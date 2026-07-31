# ui/components/device_card.py
"""
Tarjeta de dispositivo monitoreado (IPMonitor) para Argos Guard.
Muestra el estado en tiempo real de un equipo y dispara alertas cuando cambia.
"""

import os
import datetime
import customtkinter
import pygame
from utils.paths import get_resource_path
from config import branding as b
from config.settings import ALERT_HOUR_START, ALERT_HOUR_END


class IPMonitor(customtkinter.CTkFrame):
    """
    Widget tarjeta que representa un equipo monitoreado.
    Se actualiza desde hilos de ping_logic mediante update_status().
    """

    def __init__(
        self,
        master,
        ip: str,
        label: str,
        desconexiones_count: int = 0,
        mac: str = "Buscando MAC...",
        disconnection_timestamp=None,
    ):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=b.COLOR_CARD_BG,
            border_width=2,
            border_color="#555555",
        )

        self.ip = ip
        self.label = label
        self.status = "Verificando..."
        self.previous_status = None
        self.desconexiones_count = desconexiones_count
        self.mac = mac
        self.disconnection_timestamp = disconnection_timestamp
        self._ping_thread_active = True

        self.grid_columnconfigure(0, weight=1)
        self.bind("<Destroy>", self._mark_ping_thread_inactive, add="+")

        # Nombre del equipo
        self.label_name = customtkinter.CTkLabel(
            self, text=self.label, font=("Arial", 14, "bold"), text_color="#FFFFFF"
        )
        self.label_name.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # IP
        self.ip_label = customtkinter.CTkLabel(
            self, text=self.ip, font=("Arial", 11), text_color="#AAAAAA"
        )
        self.ip_label.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="ew")

        # MAC
        self.mac_label = customtkinter.CTkLabel(
            self, text=self.mac, font=("Arial", 10, "italic"), text_color="#888888"
        )
        self.mac_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")

        # Icono de estado
        self.status_icon_label = customtkinter.CTkLabel(
            self, text="⏳", font=("Arial", 24), text_color="#555555"
        )
        self.status_icon_label.grid(row=3, column=0, padx=10, pady=(5, 0), sticky="ew")

        # Texto de estado
        self.status_text_label = customtkinter.CTkLabel(
            self, text="Iniciando...", font=("Arial", 12, "bold"), text_color="#555555"
        )
        self.status_text_label.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

    # ─────────────────────────────────────────────
    # API pública — llamada desde hilos de ping
    # ─────────────────────────────────────────────

    def update_status(self, new_status: str, mac_address: str, latencia=None) -> None:
        """Delega la actualización de UI al hilo principal de Tkinter."""
        if not getattr(self, "_ping_thread_active", True):
            return
        try:
            self.after(0, self._update_status_ui, new_status, mac_address, latencia)
        except Exception:
            self._ping_thread_active = False

    def _mark_ping_thread_inactive(self, event=None) -> None:
        if event is None or event.widget is self:
            self._ping_thread_active = False

    # ─────────────────────────────────────────────
    # Métodos privados (UI thread)
    # ─────────────────────────────────────────────

    def _update_status_ui(
        self, new_status: str, mac_address: str, latencia=None
    ) -> None:
        """Se ejecuta SIEMPRE en el hilo principal de Tkinter."""
        if not self.winfo_exists():
            return

        self.previous_status = self.status
        self.status = new_status
        self.mac = mac_address

        # Guardar métrica en la instancia raíz de App
        self._save_metric(latencia, new_status)

        self.mac_label.configure(text=self.mac)
        self._update_visuals()
        self._check_for_alert()

    def _save_metric(self, latencia, new_status: str) -> None:
        """Sube por la jerarquía de widgets para guardar la métrica en App."""
        try:
            app = self.master
            while not isinstance(app, customtkinter.CTk) and app.master is not None:
                app = app.master
            if hasattr(app, "metricas"):
                app.metricas.agregar_medicion(self.ip, latencia, new_status)
        except Exception as e:
            print(f"[DeviceCard] Error al guardar métrica: {e}")

    def _update_visuals(self) -> None:
        """Actualiza colores e iconos según el estado del equipo."""
        visuals = {
            "Conectado": {
                "border": b.COLOR_SUCCESS,
                "icon": "👍",
                "icon_color": b.COLOR_SUCCESS,
                "text": "Conectado",
                "text_color": b.COLOR_SUCCESS,
                "mac_color": "#AAAAAA",
            },
            "Desconectado": {
                "border": b.COLOR_DANGER,
                "icon": "👎",
                "icon_color": b.COLOR_DANGER,
                "text": "Desconectado",
                "text_color": b.COLOR_DANGER,
                "mac_text": "MAC Desconocida",
                "mac_color": "#777777",
            },
        }
        v = visuals.get(self.status, {
            "border": "#555555",
            "icon": "⏳",
            "icon_color": "gray",
            "text": self.status,
            "text_color": "gray",
            "mac_color": "#777777",
        })

        self.configure(border_color=v["border"])
        self.status_icon_label.configure(text=v["icon"], text_color=v["icon_color"])
        self.status_text_label.configure(text=v["text"], text_color=v["text_color"])
        if self.status == "Desconectado":
            self.mac_label.configure(text="MAC Desconocida", text_color=v["mac_color"])
        else:
            self.mac_label.configure(text_color=v.get("mac_color", "#AAAAAA"))

    def _check_for_alert(self) -> None:
        """Detecta cambios de estado y dispara alertas visuales, sonoras y Telegram."""
        if self.previous_status is None or self.previous_status == self.status:
            return

        if self.status == "Desconectado":
            self.disconnection_timestamp = datetime.datetime.now()
            self._send_alert(
                f"¡Alerta! {self.label} está desconectado.", "red", "alerta.mp3"
            )
            self.desconexiones_count += 1
        elif self.status == "Conectado":
            self.disconnection_timestamp = None
            self._send_alert(
                f"¡Recuperado! {self.label} está en línea de nuevo.",
                "green",
                "recuperado.mp3",
            )

        self._send_telegram_alert()

    def _send_alert(self, message: str, color: str, sound_file: str) -> None:
        """Muestra Toast y reproduce sonido de alerta."""
        from ui.components.toast import ToastNotification

        try:
            app = self.master
            while not isinstance(app, customtkinter.CTk) and app.master is not None:
                app = app.master
            ToastNotification(app, f"{b.APP_NAME}: Cambio de Estado", message, color=color)
        except Exception as e:
            print(f"[DeviceCard] Error al mostrar Toast: {e}")

        try:
            sound_path = os.path.join(get_resource_path("assets"), sound_file)
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._last_sound = pygame.mixer.Sound(sound_path)
            self._last_sound.play()
        except Exception as e:
            print(f"[DeviceCard] Error al reproducir sonido: {e}")
            try:
                import winsound
                if "alerta" in sound_file:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                else:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    def _send_telegram_alert(self) -> None:
        """Envía alerta a Telegram con restricción horaria."""
        try:
            app = self.master
            while not isinstance(app, customtkinter.CTk) and app.master is not None:
                app = app.master

            if not (hasattr(app, "telegram_alerter") and app.telegram_alerter and
                    app.telegram_alerter.enabled):
                return

            current_hour = datetime.datetime.now().hour
            if not (ALERT_HOUR_START <= current_hour < ALERT_HOUR_END):
                print("[Telegram] Alerta omitida: fuera de horario laboral")
                return

            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            if self.status == "Desconectado":
                msg = (
                    f"🚨 *ALERTA - {b.APP_NAME}*\n\n"
                    f"📍 *Equipo:* {self.label}\n"
                    f"🌐 *IP:* {self.ip}\n"
                    f"⏰ *Hora:* {now_str}\n"
                    f"❌ *Estado:* DESCONECTADO"
                )
            else:
                msg = (
                    f"✅ *RECUPERADO - {b.APP_NAME}*\n\n"
                    f"📍 *Equipo:* {self.label}\n"
                    f"🌐 *IP:* {self.ip}\n"
                    f"⏰ *Hora:* {now_str}\n"
                    f"🟢 *Estado:* CONECTADO"
                )
            app.telegram_alerter.send_alert(msg)
        except Exception as e:
            print(f"[DeviceCard] Error enviando Telegram: {e}")
