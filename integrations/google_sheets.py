import os
import time
from pathlib import Path
from threading import Lock

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
GOOGLE_WORKSHEET_NAME = os.getenv("GOOGLE_WORKSHEET_NAME", "Registros")

CREDENTIALS_PATH = BASE_DIR / GOOGLE_CREDENTIALS_FILE

CACHE_TTL = 30

_cache_registros = None
_cache_expira = 0.0
_cache_lock = Lock()

# Instancia persistente para no reconectar en cada solicitud y evitar cuota de lectura
_hoja_instancia = None
_hoja_lock = Lock()


def _obtener_hoja(forzar_reconnect=False):
    """
    Obtiene la hoja de Google Sheets reutilizando la conexión existente
    para ahorrar cuota de peticiones a la API.
    """
    global _hoja_instancia

    if _hoja_instancia is not None and not forzar_reconnect:
        return _hoja_instancia

    with _hoja_lock:
        if _hoja_instancia is not None and not forzar_reconnect:
            return _hoja_instancia

        if not GOOGLE_SHEET_ID:
            raise ValueError("Falta GOOGLE_SHEET_ID en el archivo .env")

        if not CREDENTIALS_PATH.is_file():
            raise FileNotFoundError(f"No se encontró el archivo de credenciales: {CREDENTIALS_PATH}")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credenciales = Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=scopes
        )
        cliente = gspread.authorize(credenciales)
        documento = cliente.open_by_key(GOOGLE_SHEET_ID)
        _hoja_instancia = documento.worksheet(GOOGLE_WORKSHEET_NAME)
        return _hoja_instancia


def agregar_registro(data: dict, max_reintentos: int = 10) -> bool:
    """
    Guarda una solicitud en Google Sheets con reintentos y retroceso exponencial
    para garantizar que NUNCA se pierda un registro por límites de cuota (429).
    """
    for intento in range(max_reintentos):
        try:
            hoja = _obtener_hoja()
            fila = [
                str(data["id"]),
                data["estudiante"],
                data["tipo"],
                data["descripcion"],
                data["estado"],
                data["fecha"],
            ]
            hoja.append_row(fila, value_input_option="USER_ENTERED")

            # Invalidar la caché de lectura
            global _cache_registros, _cache_expira
            with _cache_lock:
                _cache_registros = None
                _cache_expira = 0.0

            return True

        except Exception as error:
            error_str = str(error)
            print(f"[Google Sheets] Intento {intento + 1}/{max_reintentos} falló: {type(error).__name__}: {error}")

            if "429" in error_str or "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                espera = min(2 * (intento + 1), 8)
                print(f"[Google Sheets] Cuota 429 detectada. Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
            else:
                # Si falló la sesión o token, forzar reconexión
                _obtener_hoja(forzar_reconnect=True)
                time.sleep(1)

    print("[Google Sheets] CRÍTICO: No se pudo guardar la fila tras todos los reintentos.")
    return False


def obtener_registros_sheets():
    global _cache_registros, _cache_expira

    with _cache_lock:
        ahora = time.monotonic()
        if _cache_registros is not None and ahora < _cache_expira:
            return _cache_registros

        try:
            hoja = _obtener_hoja()
            registros = hoja.get_all_records()
            _cache_registros = registros
            _cache_expira = time.monotonic() + CACHE_TTL
            return registros
        except Exception as error:
            print(f"Error al consultar Google Sheets: {type(error).__name__}: {error}")
            return []


def actualizar_estado_sheets(id_registro: str, nuevo_estado: str) -> bool:
    try:
        hoja = _obtener_hoja()
        columna_ids = hoja.col_values(1)

        fila_encontrada = -1
        for i, val in enumerate(columna_ids):
            if str(val) == str(id_registro):
                fila_encontrada = i + 1
                break

        if fila_encontrada == -1:
            return False

        hoja.update_cell(fila_encontrada, 5, nuevo_estado)

        global _cache_registros, _cache_expira
        with _cache_lock:
            _cache_registros = None
            _cache_expira = 0.0

        return True
    except Exception as error:
        print(f"Error al actualizar en Google Sheets: {type(error).__name__}: {error}")
        return False
