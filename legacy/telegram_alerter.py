import requests
import threading
import branding

class TelegramAlerter:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.enabled = bool(token and chat_id)

    def _send(self, message):
        if not self.enabled:
            return
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            # Timeout corto para no colgar hilos si no hay internet
            requests.post(self.base_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Error enviando alerta Telegram: {e}")

    def send_alert(self, message):
        """Envía el mensaje en un hilo separado para no congelar la UI"""
        if self.enabled:
            threading.Thread(target=self._send, args=(message,), daemon=True).start()

    def update_credentials(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.enabled = bool(token and chat_id)
        
    def test_message(self):
        self.send_alert(f"🔔 *Prueba de Notificación*\n\nEl sistema {branding.APP_NAME} v{branding.VERSION} está conectado correctamente con Telegram.")