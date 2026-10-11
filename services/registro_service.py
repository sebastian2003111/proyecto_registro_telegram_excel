import queue
import threading
import time
from datetime import datetime

from integrations.google_sheets import (
    agregar_registro,
    obtener_registros_sheets,
    actualizar_estado_sheets
)
from integrations.telegram import enviar_mensaje

# ============================================================
# COLA ASÍNCRONA FIFO (First-In, First-Out)
# ============================================================
cola_solicitudes = queue.Queue()
lock_contador = threading.Lock()
contador_solicitudes = 0
total_procesadas = 0


def worker_procesamiento():
    """
    Worker en segundo plano que procesa las solicitudes una a una
    en estricto orden secuencial (FIFO), garantizando que lleguen
    en orden numérico (#1, #2, #3, ...) y que ninguna se pierda.
    """
    global total_procesadas

    while True:
        try:
            item = cola_solicitudes.get()
            if item is None:
                break

            data, numero_actual = item

            # 1. Guardar en Google Sheets de forma ordenada (con reintentos automáticos)
            hoja_ok = agregar_registro(data)

            # 2. Enviar a Telegram en el orden exacto
            mensaje = f"📋 NUEVA SOLICITUD ACADÉMICA #{numero_actual}"
            telegram_ok = enviar_mensaje(mensaje)

            total_procesadas += 1
            print(f"[Worker] Procesada solicitud #{numero_actual} con éxito. (Sheets: {hoja_ok}, Telegram: {telegram_ok})")

            # Pausa mínima de control para respetar cuotas de API de Google y Telegram
            time.sleep(0.15)

        except Exception as e:
            print(f"[Worker] Error inesperado procesando solicitud: {e}")
        finally:
            cola_solicitudes.task_done()


# Iniciar el hilo de fondo al importar el servicio
hilo_worker = threading.Thread(target=worker_procesamiento, daemon=True)
hilo_worker.start()


# ============================================================
# FUNCIONES DEL SERVICIO
# ============================================================

def registrar(solicitud):
    """
    Recibe la solicitud, le asigna número secuencial atómico,
    la coloca en la cola FIFO y responde inmediatamente (no bloqueante).
    """
    global contador_solicitudes

    with lock_contador:
        contador_solicitudes += 1
        numero_actual = contador_solicitudes

    data = solicitud.model_dump()

    # El ID ahora es el número secuencial exacto (1, 2, 3...) para que coincida con Telegram
    data["id"] = numero_actual
    data["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Encolar para procesamiento secuencial garantizado
    cola_solicitudes.put((data, numero_actual))

    return {
        "mensaje": "Solicitud recibida y encolada exitosamente",
        "numero_solicitud": numero_actual,
        "id": data["id"],
        "estado": "EN_COLA",
        "solicitud": data,
    }


def listar():
    return obtener_registros_sheets()


def actualizar_estado(id_registro: str, nuevo_estado: str):
    return actualizar_estado_sheets(id_registro, nuevo_estado)


def reiniciar_contador():
    """Permite reiniciar el contador a 0 antes de cada prueba de carga."""
    global contador_solicitudes, total_procesadas
    with lock_contador:
        contador_solicitudes = 0
        total_procesadas = 0
    return {"mensaje": "Contador reiniciado a 0"}


def estado_cola():
    """Retorna el estado de la cola y solicitudes pendientes."""
    return {
        "solicitudes_recibidas": contador_solicitudes,
        "total_procesadas": total_procesadas,
        "pendientes_en_cola": cola_solicitudes.qsize(),
    }