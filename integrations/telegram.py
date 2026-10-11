import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def enviar_mensaje(mensaje: str, max_reintentos: int = 10) -> bool:
    """
    Envía un mensaje a Telegram con manejo de límites de tasa (Rate Limiting 429)
    y reintentos automáticos para asegurar el 100% de entregas.
    """
    if not TOKEN or not CHAT_ID:
        print("[Telegram] Falta TOKEN o CHAT_ID en .env")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    for intento in range(max_reintentos):
        try:
            r = requests.post(
                url,
                json={"chat_id": CHAT_ID, "text": mensaje},
                timeout=10
            )

            # Si Telegram nos pide esperar por límite de velocidad (Rate Limit)
            if r.status_code == 429:
                try:
                    retry_after = r.json().get("parameters", {}).get("retry_after", 2)
                except Exception:
                    retry_after = 2
                print(f"[Telegram] Rate limit 429. Esperando {retry_after}s antes de reintentar...")
                time.sleep(retry_after)
                continue

            r.raise_for_status()
            return True

        except requests.RequestException as e:
            print(f"[Telegram] Intento {intento + 1}/{max_reintentos} falló: {e}")
            time.sleep(1)

    print("[Telegram] CRÍTICO: No se pudo enviar el mensaje tras todos los reintentos.")
    return False
