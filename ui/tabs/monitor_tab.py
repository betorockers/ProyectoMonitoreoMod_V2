# ui/tabs/monitor_tab.py
"""
Pestaña de Monitoreo Activo de Argos Guard.
Gestiona la cuadrícula de tarjetas de dispositivos y el panel lateral de control.
"""

import os
import threading
import customtkinter
from tkinter import messagebox

from ui.components.device_card import IPMonitor
from ui.components.toast import ToastNotification
from core.ping_logic import ping_ip
from utils.paths import get_base_path, get_resource_path
from config import branding as b
from config.settings import (
    DEFAULT_PING_INTERVAL,
    MIN_PING_INTERVAL,
    MAX_MONITOR_COLUMNS,
    EQUIPOS_CONFIG_FILE,
)
from PIL import Image


class MonitorTab:
    """
    Controlador de la pestaña 'Monitoreo Activo'.
    Recibe la instancia de App para acceder a servicios compartidos (metricas, telegram_alerter).
    """

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self.monitors: dict[str, IPMonitor] = {}
        self._setup_scrollable_frame()

    def _setup_scrollable_frame(self) -> None:
        self.monitor_frame = customtkinter.CTkScrollableFrame(self.frame)
        self.monitor_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def create_monitors(self) -> None:
        """Destruye las tarjetas existentes y recrea el grid completo."""
        print(f"[MonitorTab] Creando monitores para {len(self.app.equipos_a_monitorear)} equipos...")

        # Leer intervalo del entry del sidebar
        try:
            val = self.app.sidebar.ping_interval_entry.get()
            if val:
                new_interval = max(int(val), MIN_PING_INTERVAL)
                self.app.ping_interval = new_interval
        except (ValueError, AttributeError):
            pass

        for widget in self.monitor_frame.winfo_children():
            widget.destroy()

        self.monitors = {}
        row, col = 0, 0

        for i in range(MAX_MONITOR_COLUMNS):
            self.monitor_frame.grid_columnconfigure(i, weight=1, pad=10)

        for equipo in self.app.equipos_a_monitorear:
            monitor = IPMonitor(
                self.monitor_frame,
                equipo["ip"],
                equipo["label"],
                desconexiones_count=equipo.get("desconexiones_count", 0),
                mac=equipo.get("mac_address", "Buscando MAC..."),
                disconnection_timestamp=equipo.get("disconnection_timestamp"),
            )
            monitor.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.monitors[equipo["ip"]] = monitor

            threading.Thread(
                target=ping_ip,
                args=(equipo["ip"], monitor, self.app.ping_interval),
                daemon=True,
            ).start()

            col += 1
            if col >= MAX_MONITOR_COLUMNS:
                col, row = 0, row + 1

        # Sincronizar referencia en App
        self.app.monitors = self.monitors

    def agregar_equipo(self) -> None:
        ip = self.app.sidebar.ip_entry.get()
        etiqueta = self.app.sidebar.etiqueta_entry.get()
        if ip and etiqueta:
            self.app.equipos_a_monitorear.append({
                "ip": ip,
                "label": etiqueta,
                "desconexiones_count": 0,
                "mac_address": "Buscando MAC...",
                "disconnection_timestamp": None,
            })
            self.create_monitors()
            self.app.sidebar.ip_entry.delete(0, "end")
            self.app.sidebar.etiqueta_entry.delete(0, "end")

    def remover_equipo(self) -> None:
        ip_a_remover = self.app.sidebar.remove_entry.get()
        if ip_a_remover:
            nueva_lista = [
                eq for eq in self.app.equipos_a_monitorear if eq["ip"] != ip_a_remover
            ]
            if len(nueva_lista) < len(self.app.equipos_a_monitorear):
                self.app.equipos_a_monitorear = nueva_lista
                self.create_monitors()
                self.app.sidebar.remove_entry.delete(0, "end")

    def guardar_equipos(self) -> None:
        try:
            new_interval = max(int(self.app.sidebar.ping_interval_entry.get()), MIN_PING_INTERVAL)
            self.app.ping_interval = new_interval

            lista_guardar = []
            for equipo in self.app.equipos_a_monitorear:
                ip = equipo["ip"]
                eq = equipo.copy()
                if ip in self.monitors:
                    m = self.monitors[ip]
                    eq["desconexiones_count"] = m.desconexiones_count
                    eq["mac_address"] = m.mac
                    eq["disconnection_timestamp"] = (
                        m.disconnection_timestamp.isoformat()
                        if m.disconnection_timestamp else None
                    )
                lista_guardar.append(eq)

            plain_cameras = []
            for camera in getattr(self.app, "cameras_config", []):
                camera_copy = camera.copy()
                camera_copy.pop("password", None)
                plain_cameras.append(camera_copy)

            data = {
                "intervalo_ping": self.app.ping_interval,
                "equipos": lista_guardar,
                "telegram": {
                    "configured": bool(self.app.telegram_alerter.token and self.app.telegram_alerter.chat_id),
                },
                "cameras": plain_cameras,
                "camera_settings": {
                    "max_streams": getattr(self.app, "camera_max_streams", 1),
                    "snapshot_interval": getattr(self.app, "camera_snapshot_interval", 2),
                    "verify_tls_certificates": getattr(self.app, "verify_tls_certificates", True),
                    "enable_external_geolocation": getattr(self.app, "enable_external_geolocation", False),
                    "verify_ssh_host_key": getattr(self.app, "verify_ssh_host_key", True),
                    "ssh_trust_on_first_use": getattr(self.app, "ssh_trust_on_first_use", False),
                },
            }
            path = os.path.join(get_base_path(), EQUIPOS_CONFIG_FILE)
            self.app.secure_config.save(data, path)

            if hasattr(self.app, "_save_sensitive_runtime_settings"):
                self.app._save_sensitive_runtime_settings()

            if hasattr(self.app, "metricas"):
                self.app.metricas.registrar_disponibilidad_diaria()
        except Exception as e:
            print(f"[MonitorTab] Error al guardar: {e}")

    def cargar_equipos(self) -> None:
        self.app.cargar_configuracion_inicial()
        try:
            self.app.sidebar.ping_interval_entry.delete(0, "end")
            self.app.sidebar.ping_interval_entry.insert(0, str(self.app.ping_interval))
        except Exception:
            pass
        self.create_monitors()
