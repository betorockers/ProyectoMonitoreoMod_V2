import os
import time

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _load_token() -> str:
    if load_dotenv is not None:
        load_dotenv(os.path.join(".secrets", "runtime", "app.env"), override=False)
        load_dotenv(override=False)
    return os.getenv("TELEGRAM_TOKEN", "").strip()


def obtener_id_telegram():
    token = _load_token()
    if not token:
        token = input("Ingrese el token del bot de Telegram: ").strip()
    if not token:
        print("No se ingreso un token de Telegram.")
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    print("Configurando bot de Telegram")
    print("Abre Telegram, busca tu bot y enviale un mensaje.")
    print("Esperando para detectar el Chat ID...")

    while True:
        try:
            response = requests.get(url, timeout=10).json()
            if response.get("ok") and response.get("result"):
                ultimo_mensaje = response["result"][-1]
                chat_id = ultimo_mensaje["message"]["chat"]["id"]
                usuario = ultimo_mensaje["message"]["from"].get("first_name", "Usuario")

                print("\n" + "=" * 50)
                print(f"Detectado mensaje de: {usuario}")
                print(f"Tu Chat ID es: {chat_id}")
                print("=" * 50)
                print("Guarda el token y este Chat ID en tu configuracion segura.")
                break
        except Exception as e:
            print(f"Esperando... ({e})")

        time.sleep(2)


if __name__ == "__main__":
    obtener_id_telegram()
