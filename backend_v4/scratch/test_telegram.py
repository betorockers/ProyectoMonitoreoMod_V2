"""
Script de prueba para validación y envío de alertas de Telegram.
"""
import os
import sys
import django

# Inicializar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import TelegramConfig

def run_test():
    print("[INFO] Iniciando prueba de alerta de Telegram...")
    
    # 1. Obtener la configuración singleton
    config = TelegramConfig.get_config()
    
    # 2. Configurar credenciales reales desde el archivo de credenciales
    config.bot_token = "8967512488:AAGIcJfbd7ui19ROj5psNb9rmqcKELTbjQY"
    config.chat_id = "8036765324"
    config.is_active = True
    config.save()
    
    print("LOG: Credenciales guardadas en BBDD:")
    print(f"   - Bot Token: {config.bot_token[:15]}... [PROTEGIDO]")
    print(f"   - Chat ID: {config.chat_id}")
    print(f"   - Estado: {'Activo' if config.is_active else 'Inactivo'}")

    # 3. Armar un mensaje de alerta con estilo cyberpunk formal
    test_msg = (
        "🤖 <b>[ARGOS GUARD SYSTEM ALERT]</b>\n"
        "----------------------------------------\n"
        "📢 <b>Prueba de Mensajería y Alertas Activa</b>\n"
        "🟢 <b>Canal de Comunicación:</b> ESTABLE\n"
        "⚙️ <b>Ecosistema:</b> v4.0.0 Enterprise\n"
        "📡 <b>Mensaje:</b> Alerta de verificación técnica del bot de Telegram iniciada con éxito.\n"
        "----------------------------------------\n"
        "<i>Argos Guard Enterprise © 2026</i>"
    )

    print("LOG: Enviando mensaje de prueba...")
    # Llamamos a send_notification. Como corre en un hilo secundario, para ver el resultado en consola
    # realizaremos también una llamada síncrona manual directa para capturar la respuesta HTTP.
    import requests
    url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
    payload = {
        "chat_id": config.chat_id,
        "text": test_msg,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=8)
        res_data = res.json()
        if res.status_code == 200 and res_data.get("ok"):
            print("LOG: Mensaje enviado con EXITO a la API de Telegram!")
            print(f"   - ID Mensaje: {res_data['result']['message_id']}")
            print(f"   - Destinatario: {res_data['result']['chat']['first_name']} (Chat ID: {res_data['result']['chat']['id']})")
        else:
            print("ERROR: Error al enviar mensaje por Telegram:")
            print(f"   - Código HTTP: {res.status_code}")
            print(f"   - Respuesta: {res_data}")
    except Exception as e:
        print(f"ERROR: Excepcion atrapada durante el envio manual: {str(e)}")

if __name__ == "__main__":
    run_test()
