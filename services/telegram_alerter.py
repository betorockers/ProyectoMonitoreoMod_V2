# services/telegram_alerter.py
"""
Cliente Telegram Bot para alertas de Argos Guard.

FIX H-14: Desacoplado de `branding`. El método test_message() ahora recibe
           el texto como parámetro en lugar de construirlo con import de branding.
"""

import requests
import threading


class TelegramAlerter:
    """Envía alertas a un canal de Telegram en hilos separados para no bloquear la UI."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.enabled = bool(token and chat_id)

    # ─────────────────────────────────────────────
    # Métodos privados
    # ─────────────────────────────────────────────

    def _send(self, message: str) -> None:
        """Envía el mensaje HTTP a la API de Telegram."""
        if not self.enabled:
            return
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
            }
            # Timeout corto para no colgar hilos si no hay internet
            requests.post(self.base_url, json=payload, timeout=10)
        except Exception as e:
            print(f"[Telegram] Error al enviar alerta: {e}")

    # ─────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────

    def send_alert(self, message: str) -> None:
        """Envía el mensaje en un hilo separado para no congelar la UI."""
        if self.enabled:
            threading.Thread(
                target=self._send, args=(message,), daemon=True
            ).start()

    def update_credentials(self, token: str, chat_id: str) -> None:
        """Actualiza las credenciales del bot en caliente."""
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.enabled = bool(token and chat_id)

    def test_message(self, app_name: str = "Anvic Network Sentinel", version: str = "2.2.1") -> None:
        """
        Envía un mensaje de prueba.
        FIX H-14: Recibe datos de texto como parámetros, no importa branding directamente.
        """
        msg = (
            f"🔔 *Prueba de Notificación*\n\n"
            f"El sistema *{app_name} v{version}* está conectado correctamente con Telegram."
        )
        self.send_alert(msg)
