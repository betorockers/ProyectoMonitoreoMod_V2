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
                ubicacion=equipo.get("ubicacion", ""),
            )
            monitor.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
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

    def reordenar_equipos(self, ip_origen: str, ip_destino: str) -> None:
        """Reordena tarjetas al arrastrar y soltar a 60 FPS."""
        idx_origen = next((i for i, eq in enumerate(self.app.equipos_a_monitorear) if eq.get("ip") == ip_origen), None)
        idx_destino = next((i for i, eq in enumerate(self.app.equipos_a_monitorear) if eq.get("ip") == ip_destino), None)
        if idx_origen is not None and idx_destino is not None and idx_origen != idx_destino:
            item = self.app.equipos_a_monitorear.pop(idx_origen)
            self.app.equipos_a_monitorear.insert(idx_destino, item)
            self.reorganizar_grid_monitores()
            self._programar_guardado_silencioso()

    def mover_equipo_relativo(self, ip: str, delta: int) -> None:
        """Mueve un equipo hacia la izquierda (-1) o derecha (+1) en la cuadrícula de forma fluida."""
        idx = next((i for i, eq in enumerate(self.app.equipos_a_monitorear) if eq.get("ip") == ip), None)
        if idx is None:
            return
        nuevo_idx = max(0, min(len(self.app.equipos_a_monitorear) - 1, idx + delta))
        if nuevo_idx != idx:
            item = self.app.equipos_a_monitorear.pop(idx)
            self.app.equipos_a_monitorear.insert(nuevo_idx, item)
            self.reorganizar_grid_monitores()
            self._programar_guardado_silencioso()

    def reorganizar_grid_monitores(self) -> None:
        """Reorganiza visualmente el grid de tarjetas sin parpadeos."""
        for idx, eq in enumerate(self.app.equipos_a_monitorear):
            ip = eq.get("ip")
            if ip in self.monitors:
                row = idx // MAX_MONITOR_COLUMNS
                col = idx % MAX_MONITOR_COLUMNS
                self.monitors[ip].grid(row=row, column=col, padx=7, pady=7, sticky="nsew")

    def _programar_guardado_silencioso(self) -> None:
        """Debounce de guardado a disco para mantener 60 FPS durante reordenamiento."""
        if hasattr(self, "_save_timer_id") and self._save_timer_id is not None:
            try:
                self.after_cancel(self._save_timer_id)
            except Exception:
                pass
        self._save_timer_id = self.after(1200, self._guardar_equipos_silencioso)

    def _guardar_equipos_silencioso(self) -> None:
        """Persiste la configuración de equipos cifrada en disco sin bloquear la interfaz."""
        self._save_timer_id = None
        try:
            self.guardar_equipos()
        except Exception as e:
            print(f"Error guardando equipos silenciosamente: {e}")

    def agregar_equipo(self) -> None:
        ip = self.app.sidebar.ip_entry.get().strip()
        etiqueta = self.app.sidebar.etiqueta_entry.get().strip()
        ubicacion = self.app.sidebar.ubicacion_entry.get().strip() if hasattr(self.app.sidebar, "ubicacion_entry") else ""
        if ip and etiqueta:
            if not ubicacion:
                lbl_low = etiqueta.lower()
                if "quilicura" in lbl_low:
                    ubicacion = "Quilicura"
                elif "renca" in lbl_low:
                    ubicacion = "Renca"
            self.app.equipos_a_monitorear.append({
                "ip": ip,
                "label": etiqueta,
                "ubicacion": ubicacion,
                "desconexiones_count": 0,
                "mac_address": "Buscando MAC...",
                "disconnection_timestamp": None,
            })
            self.create_monitors()
            self.guardar_equipos()
            self.app.sidebar.ip_entry.delete(0, "end")
            self.app.sidebar.etiqueta_entry.delete(0, "end")
            if hasattr(self.app.sidebar, "ubicacion_entry"):
                self.app.sidebar.ubicacion_entry.delete(0, "end")

    def remover_equipo(self) -> None:
        ip_a_remover = self.app.sidebar.remove_entry.get().strip()
        if ip_a_remover:
            nueva_lista = [
                eq for eq in self.app.equipos_a_monitorear if eq["ip"] != ip_a_remover
            ]
            if len(nueva_lista) < len(self.app.equipos_a_monitorear):
                self.app.equipos_a_monitorear = nueva_lista
                self.create_monitors()
                self.guardar_equipos()
                self.app.sidebar.remove_entry.delete(0, "end")

    def guardar_equipos(self) -> None:
        try:
            lista_guardar = []
            for equipo in self.app.equipos_a_monitorear:
                ip = equipo["ip"]
                eq = equipo.copy()
                eq["ubicacion"] = equipo.get("ubicacion", "")
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
                "turno_settings": {
                    "inicio": getattr(self.app, "turno_inicio", "07:00"),
                    "fin": getattr(self.app, "turno_fin", "18:00"),
                    "nombre": getattr(self.app, "turno_nombre", "Turno Operativo"),
                },
                "reporte_settings": {
                    "empresa_cliente": getattr(self.app, "empresa_cliente", "Anvic Seguridad Integral"),
                    "sitio_planta": getattr(self.app, "sitio_planta", "Planta Quilicura - Renca"),
                    "sla_objetivo": getattr(self.app, "sla_objetivo", 99.5),
                    "incluir_cctv": getattr(self.app, "incluir_cctv_en_reporte", False),
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
