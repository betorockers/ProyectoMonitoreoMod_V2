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
        ubicacion: str = "",
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
        if not ubicacion:
            lbl_low = label.lower()
            if "quilicura" in lbl_low:
                ubicacion = "Quilicura"
            elif "renca" in lbl_low:
                ubicacion = "Renca"
        self.ubicacion = ubicacion

        self.status = "Verificando..."
        self.previous_status = None
        self.desconexiones_count = desconexiones_count
        self.mac = mac
        self.disconnection_timestamp = disconnection_timestamp
        self._ping_thread_active = True

        self.grid_columnconfigure(0, weight=1)
        self.bind("<Destroy>", self._mark_ping_thread_inactive, add="+")

        # Fila 0: Barra superior de locación y controles de movimiento rápido
        self.header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=6, pady=(4, 0), sticky="ew")

        badge_txt = f"📍 {self.ubicacion.upper()}" if self.ubicacion else "📍 SITIO"
        self.ubicacion_badge = customtkinter.CTkLabel(
            self.header_frame,
            text=badge_txt,
            font=("Arial", 8.5, "bold"),
            text_color="#38BDF8",
            fg_color="#1E293B",
            corner_radius=4,
            height=16,
            padx=4,
        )
        self.ubicacion_badge.pack(side="left", padx=1)

        # Controles de movimiento rápido y manija de arrastre
        self.nav_controls = customtkinter.CTkFrame(self.header_frame, fg_color="transparent")
        self.nav_controls.pack(side="right", padx=0)

        self.btn_move_left = customtkinter.CTkButton(
            self.nav_controls,
            text="◀",
            width=20,
            height=16,
            corner_radius=3,
            fg_color="#334155",
            hover_color="#0284C7",
            font=("Arial", 9, "bold"),
            command=self._mover_izquierda,
        )
        self.btn_move_left.pack(side="left", padx=1)

        self.drag_hint = customtkinter.CTkLabel(
            self.nav_controls,
            text="⠿",
            font=("Arial", 11),
            text_color="#64748B",
            cursor="fleur",
            width=14,
        )
        self.drag_hint.pack(side="left", padx=1)

        self.btn_move_right = customtkinter.CTkButton(
            self.nav_controls,
            text="▶",
            width=20,
            height=16,
            corner_radius=3,
            fg_color="#334155",
            hover_color="#0284C7",
            font=("Arial", 9, "bold"),
            command=self._mover_derecha,
        )
        self.btn_move_right.pack(side="left", padx=1)

        # Fila 1: Nombre del equipo
        self.label_name = customtkinter.CTkLabel(
            self, text=self.label, font=("Arial", 13, "bold"), text_color="#FFFFFF"
        )
        self.label_name.grid(row=1, column=0, padx=8, pady=(2, 0), sticky="ew")

        # Fila 2: IP
        self.ip_label = customtkinter.CTkLabel(
            self, text=self.ip, font=("Arial", 10), text_color="#AAAAAA"
        )
        self.ip_label.grid(row=2, column=0, padx=8, pady=(0, 1), sticky="ew")

        # Fila 3: MAC
        self.mac_label = customtkinter.CTkLabel(
            self, text=self.mac, font=("Arial", 9, "italic"), text_color="#888888"
        )
        self.mac_label.grid(row=3, column=0, padx=8, pady=(0, 3), sticky="ew")

        # Fila 4: Icono de estado
        self.status_icon_label = customtkinter.CTkLabel(
            self, text="⏳", font=("Arial", 20), text_color="#555555"
        )
        self.status_icon_label.grid(row=4, column=0, padx=8, pady=(3, 0), sticky="ew")

        # Fila 5: Texto de estado
        self.status_text_label = customtkinter.CTkLabel(
            self, text="Iniciando...", font=("Arial", 11, "bold"), text_color="#555555"
        )
        self.status_text_label.grid(row=5, column=0, padx=8, pady=(0, 6), sticky="ew")

        # Control interactivo de arrastre y selección/edición
        self._press_x = 0
        self._press_y = 0
        self._drag_started = False
        self._is_hover_target = False
        self._current_hover_target = None
        self._last_release_time = 0

        # Enlazar interacción interactiva (Click para editar / Arrastre para reubicar)
        # OJO: Los botones btn_move_left y btn_move_right NO se enlazan para permitir su click directo
        widgets_to_bind = [
            self,
            self.header_frame,
            self.ubicacion_badge,
            self.drag_hint,
            self.label_name,
            self.ip_label,
            self.mac_label,
            self.status_icon_label,
            self.status_text_label,
        ]
        for w in widgets_to_bind:
            w.bind("<ButtonPress-1>", self._on_press, add="+")
            w.bind("<B1-Motion>", self._on_motion, add="+")
            w.bind("<ButtonRelease-1>", self._on_release, add="+")

    def _mover_izquierda(self):
        top = self.winfo_toplevel()
        if hasattr(top, "mover_equipo_relativo"):
            top.mover_equipo_relativo(self.ip, -1)

    def _mover_derecha(self):
        top = self.winfo_toplevel()
        if hasattr(top, "mover_equipo_relativo"):
            top.mover_equipo_relativo(self.ip, 1)

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root
        self._drag_started = False
        self._current_hover_target = None
        return "break"

    def _on_motion(self, event):
        dx = abs(event.x_root - getattr(self, "_press_x", event.x_root))
        dy = abs(event.y_root - getattr(self, "_press_y", event.y_root))
        if dx > 8 or dy > 8:
            if not getattr(self, "_drag_started", False):
                self._drag_started = True
                self.configure(border_color="#00D9FF", border_width=3)

            top = self.winfo_toplevel()
            monitors_dict = getattr(top, "monitors", {})
            if not monitors_dict and hasattr(top, "monitor_tab"):
                monitors_dict = getattr(top.monitor_tab, "monitors", {})

            best_card = None
            min_dist = float("inf")
            mx = event.x_root
            my = event.y_root

            for ip_key, card in monitors_dict.items():
                if card is self or not card.winfo_exists():
                    continue
                try:
                    rx = card.winfo_rootx()
                    ry = card.winfo_rooty()
                    rw = card.winfo_width()
                    rh = card.winfo_height()

                    if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                        best_card = card
                        break

                    cx = rx + rw / 2
                    cy = ry + rh / 2
                    dist = ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
                    if dist < min_dist and dist < max(rw, rh):
                        min_dist = dist
                        best_card = card
                except Exception:
                    continue

            # Actualizar resaltado de tarjeta candidata
            current_target = getattr(self, "_current_hover_target", None)
            if best_card != current_target:
                if current_target is not None and current_target.winfo_exists():
                    try:
                        current_target._is_hover_target = False
                        current_target._update_visuals()
                    except Exception:
                        pass
                self._current_hover_target = best_card
                if best_card is not None and best_card.winfo_exists():
                    try:
                        best_card._is_hover_target = True
                        best_card.configure(border_color="#F59E0B", border_width=3)
                    except Exception:
                        pass

        return "break"

    def _on_release(self, event):
        top = self.winfo_toplevel()

        was_dragging = getattr(self, "_drag_started", False)
        self._drag_started = False
        self._update_visuals()

        target_card = getattr(self, "_current_hover_target", None)
        self._current_hover_target = None
        if target_card is not None and target_card.winfo_exists():
            try:
                target_card._is_hover_target = False
                target_card._update_visuals()
            except Exception:
                pass

        now = datetime.datetime.now().timestamp()
        if now - getattr(self, "_last_release_time", 0) < 0.2:
            return "break"
        self._last_release_time = now

        if was_dragging:
            if target_card is not None and target_card is not self and hasattr(top, "reordenar_equipos"):
                top.reordenar_equipos(self.ip, target_card.ip)
        else:
            if hasattr(top, "remove_entry") and top.remove_entry.winfo_exists():
                try:
                    top.remove_entry.delete(0, "end")
                    top.remove_entry.insert(0, self.ip)
                except Exception:
                    pass
            if hasattr(top, "abrir_modal_editar_equipo"):
                top.abrir_modal_editar_equipo(self.ip)

        return "break"

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

        if not getattr(self, "_drag_started", False) and not getattr(self, "_is_hover_target", False):
            self.configure(border_color=v["border"], border_width=2)
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
