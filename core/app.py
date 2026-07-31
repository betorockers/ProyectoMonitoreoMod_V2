# core/app.py
"""
Clase App principal de Argos Guard — Orquestador de la Aplicación.

Responsabilidades:
  - Inicializar servicios compartidos (Auth, Metricas, Telegram, Backup, Pygame)
  - Gestionar el ciclo de vida de la autenticación (Login / Setup)
  - Construir la ventana principal y el sidebar
  - Delegar la lógica de UI a los módulos de tabs y componentes
  - Ejecutar el scheduler de tareas automáticas
"""

import os
import sys
import json
import time
import platform
import datetime
import threading
import io
import customtkinter
import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import InvalidToken

# ---------- Intentar imports opcionales ----------
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image as PDFImage
    from matplotlib.figure import Figure
    import numpy as np
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------- Módulos propios ----------
from config import branding as b
from config import settings as cfg
from config.settings import (
    DEFAULT_PING_INTERVAL, EQUIPOS_CONFIG_FILE,
    SCHEDULER_TIMES, BACKUP_HOUR, BACKUP_MINUTE,
    HISTORIAL_LOG_FILE,
)
from utils.paths import get_base_path, get_resource_path
from key_manager import load_key
from secure_config_manager import SecureConfigManager
from auth.auth_manager import AuthManager
from database.metrics_manager import MetricasHistoricas
from services.telegram_alerter import TelegramAlerter
from core.backup_manager import BackupManager
from ui.components.toast import ToastNotification
from ui.windows.login_window import LoginWindow, SetupWindow
from ui.windows.telegram_config import TelegramConfigWindow
from ui.tabs.monitor_tab import MonitorTab
from ui.tabs.history_tab import HistoryTab
from ui.tabs.diagnostics_tab_secure import DiagnosticsTab
from ui.tabs.cameras_tab import CamerasTab
from ui.tabs.admin_tab import AdminTab
from services.report_builder import ReportContext, build_network_report


ASSETS_PATH = get_resource_path("assets")
BASE_PATH = get_base_path()


class Sidebar:
    """Panel lateral de control con entradas y botones de acción."""

    def __init__(self, master, app):
        self.app = app
        self.frame = customtkinter.CTkFrame(master, width=200, corner_radius=0)
        self.frame.grid(row=0, column=1, rowspan=3, sticky="nsew")

        self._build_logo()
        self._build_controls()
        self.frame.grid_rowconfigure(14, weight=1)

    def _build_logo(self) -> None:
        if not PIL_AVAILABLE:
            self._add_text_logo()
            return
        try:
            logo_path = os.path.join(ASSETS_PATH, "img", b.LOGO_FILE)
            pil_img = Image.open(logo_path)
            orig_w, orig_h = pil_img.size
            ratio = min(75 / orig_w, 75 / orig_h)
            size = (int(orig_w * ratio), int(orig_h * ratio))
            self.logo_image = customtkinter.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            customtkinter.CTkLabel(self.frame, image=self.logo_image, text="").grid(
                row=0, column=0, padx=10, pady=10
            )
            customtkinter.CTkLabel(
                self.frame, text="Panel de Control", font=("Arial", 16, "bold")
            ).grid(row=1, column=0, padx=10, pady=(0, 10))
        except Exception:
            self._add_text_logo()

    def _add_text_logo(self) -> None:
        customtkinter.CTkLabel(
            self.frame, text="Panel de Control", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, padx=10, pady=10)

    def _build_controls(self) -> None:
        app = self.app
        frame = self.frame

        customtkinter.CTkLabel(frame, text="Intervalo Ping (Segundos):", font=("Arial", 12)).grid(
            row=2, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.ping_interval_entry = customtkinter.CTkEntry(
            frame, placeholder_text="ej. 1, 5, 30", justify="center"
        )
        self.ping_interval_entry.grid(row=3, column=0, padx=10, pady=2, sticky="ew")
        self.ping_interval_entry.insert(0, str(app.ping_interval))

        customtkinter.CTkLabel(frame, text="Dirección IP:", font=("Arial", 12)).grid(
            row=4, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.ip_entry = customtkinter.CTkEntry(frame, placeholder_text="ej. 192.168.1.1")
        self.ip_entry.grid(row=5, column=0, padx=10, pady=2, sticky="ew")

        customtkinter.CTkLabel(frame, text="Etiqueta:", font=("Arial", 12)).grid(
            row=6, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.etiqueta_entry = customtkinter.CTkEntry(frame, placeholder_text="ej. Servidor Principal")
        self.etiqueta_entry.grid(row=7, column=0, padx=10, pady=2, sticky="ew")

        self.add_button = customtkinter.CTkButton(
            frame, text="Agregar Equipo", command=lambda: app.monitor_tab.agregar_equipo()
        )
        self.add_button.grid(row=8, column=0, padx=10, pady=10)

        customtkinter.CTkLabel(frame, text="Eliminar Equipo (por IP):", font=("Arial", 12)).grid(
            row=9, column=0, padx=10, pady=(5, 0), sticky="w"
        )
        self.remove_entry = customtkinter.CTkEntry(frame, placeholder_text="ej. 192.168.1.1")
        self.remove_entry.grid(row=10, column=0, padx=10, pady=2, sticky="ew")

        self.remove_button = customtkinter.CTkButton(
            frame, text="Eliminar Equipo", command=lambda: app.monitor_tab.remover_equipo()
        )
        self.remove_button.grid(row=11, column=0, padx=10, pady=10)

        self.save_button = customtkinter.CTkButton(
            frame, text="Guardar Configuración", command=lambda: app.monitor_tab.guardar_equipos()
        )
        self.save_button.grid(row=12, column=0, padx=10, pady=5)

        self.load_button = customtkinter.CTkButton(
            frame, text="Cargar Configuración", command=lambda: app.monitor_tab.cargar_equipos()
        )
        self.load_button.grid(row=13, column=0, padx=10, pady=5)

        self.report_button = customtkinter.CTkButton(
            frame, text="Generar Reporte", command=app.generar_reporte
        )
        self.report_button.grid(row=14, column=0, padx=10, pady=10)

        self.backup_button = customtkinter.CTkButton(
            frame, text="Crear Backup DB", command=app.realizar_backup_manual, fg_color="#e67e22"
        )
        self.backup_button.grid(row=15, column=0, padx=10, pady=5)

        self.telegram_button = customtkinter.CTkButton(
            frame, text="Configurar Telegram", command=app.open_telegram_config, fg_color="#3B8ED0"
        )
        self.telegram_button.grid(row=15, column=0, padx=10, pady=5)

        self.logout_button = customtkinter.CTkButton(
            frame, text="Cerrar Sesión", command=app.show_login, fg_color="#ff6b6b", hover_color="#fa5252"
        )
        self.logout_button.grid(row=16, column=0, padx=10, pady=10)

    def apply_role_restrictions(self, role: str) -> None:
        """Deshabilita controles según el rol del usuario."""
        if role == "user":
            for btn in (self.add_button, self.remove_button, self.save_button,
                        self.load_button, self.report_button, self.telegram_button, self.backup_button):
                btn.configure(state="disabled")
            for entry in (self.ping_interval_entry, self.ip_entry,
                          self.etiqueta_entry, self.remove_entry):
                entry.configure(state="disabled")


class App(customtkinter.CTk):
    """
    Ventana principal de Argos Guard.
    Orquesta todos los servicios y módulos de la aplicación.
    """

    def __init__(self, equipos_iniciales: list[dict] = None):
        super().__init__()

        self.equipos_a_monitorear: list[dict] = equipos_iniciales or []
        self.current_user: dict | None = None
        self.ping_interval: int = DEFAULT_PING_INTERVAL
        self.monitors: dict = {}
        self.cameras_config: list[dict] = []
        self.camera_max_streams: int = 1
        self.camera_snapshot_interval: int = 2
        self.verify_tls_certificates: bool = True
        self.enable_external_geolocation: bool = False
        self.verify_ssh_host_key: bool = True
        self.ssh_trust_on_first_use: bool = False
        self.active_camera_streams: int = 0
        self.services_started: bool = False
        self._icon_path: str | None = None
        self.master_key = load_key(BASE_PATH)
        self.secure_config = SecureConfigManager(self.master_key)
        self.ssh_known_hosts_path = os.path.join(BASE_PATH, "ssh_known_hosts")

        # ── Servicios core ────────────────────────────────────────────────
        self.auth = AuthManager(self.secure_config, BASE_PATH)
        self.telegram_alerter = TelegramAlerter(
            cfg.TELEGRAM_TOKEN_DEFAULT, cfg.TELEGRAM_CHAT_ID_DEFAULT
        )
        self.backup_manager = BackupManager()

        # ── Son ───────────────────────────────────────────────────────────
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        # ── Ventana base (oculta hasta login) ────────────────────────────
        self.withdraw()
        self._apply_icon()

        # ── Scheduler de tiempos para las tareas automáticas ─────────────
        self.scheduler_times = [
            datetime.time(*t) for t in SCHEDULER_TIMES
        ]
        self.log_executed_today = {t.isoformat(): False for t in self.scheduler_times}

        # ── Flujo de autenticación ────────────────────────────────────────
        self.show_login()

    # ─────────────────────────────────────────────
    # Autenticación
    # ─────────────────────────────────────────────

    def show_login(self) -> None:
        """Muestra Login o Setup según si existen usuarios."""
        self.withdraw()
        for widget in self.winfo_children():
            widget.destroy()

        if not self.auth.users:
            SetupWindow(self, self.on_login_success)
        else:
            LoginWindow(self, self.on_login_success)

    def on_login_success(self, user_data: dict) -> None:
        """Callback tras autenticación exitosa. Construye la UI principal."""
        self.current_user = user_data
        self.deiconify()
        self._setup_main_window()

    # ─────────────────────────────────────────────
    # Configuración ventana principal
    # ─────────────────────────────────────────────

    def _setup_main_window(self) -> None:
        self.title(b.WINDOW_TITLE)
        self.geometry("1450x900")
        customtkinter.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        self.cargar_configuracion_inicial()

        # ── Tabs ──────────────────────────────────────────────────────────
        tabview = customtkinter.CTkTabview(self)
        tabview.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        tab_monitoreo = tabview.add("Operacion en Vivo")
        tab_historial = tabview.add("Historial Operacional")
        tab_camaras = tabview.add("Supervision Visual")

        # Instanciar controladores de tabs
        self.monitor_tab = MonitorTab(self, tab_monitoreo)
        self.history_tab = HistoryTab(self, tab_historial)
        self.cameras_tab = CamerasTab(self, tab_camaras)

        if self.current_user["role"] in ["super_admin", "admin"]:
            tab_usuarios = tabview.add("Administracion")
            tab_diag = tabview.add("Centro de Soporte")
            self.admin_tab = AdminTab(self, tab_usuarios)
            self.diag_tab = DiagnosticsTab(self, tab_diag)

        # ── Footer ────────────────────────────────────────────────────────
        self._build_footer()

        # ── Botón Recargar ────────────────────────────────────────────────
        btn_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        btn_frame.grid_columnconfigure((0, 2), weight=1)
        btn_frame.grid_columnconfigure(1, weight=0)
        customtkinter.CTkButton(
            btn_frame, text="Recargar", font=("Arial", 14, "bold"),
            command=self.monitor_tab.create_monitors
        ).grid(row=0, column=1, padx=10, pady=5)

        # ── Sidebar ───────────────────────────────────────────────────────
        self.sidebar = Sidebar(self, self)
        self.sidebar.apply_role_restrictions(self.current_user["role"])

        # ── Iniciar monitores y servicios ─────────────────────────────────
        self.monitor_tab.create_monitors()

        if not self.services_started:
            self._iniciar_scheduler_log()
            self.services_started = True

        self.after(500, self._inicializar_historial)

    def _build_footer(self) -> None:
        footer = customtkinter.CTkFrame(self, height=40, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure((0, 1, 2), weight=1)

        self.clock_label = customtkinter.CTkLabel(
            footer, text="", font=("Arial", 12, "bold"), text_color="#00d9ff"
        )
        self.clock_label.grid(row=0, column=0, padx=20, pady=2, sticky="w")

        customtkinter.CTkLabel(
            footer, text=f"{b.APP_NAME}: {b.APP_TAGLINE}",
            font=("Arial", 12, "bold"), text_color="#FFFFFF"
        ).grid(row=0, column=1, padx=10, pady=2, sticky="ew")

        customtkinter.CTkLabel(
            footer, text="Desarrollado por Omar Toledo",
            font=("Arial", 12, "italic"), text_color="#999999"
        ).grid(row=0, column=2, padx=10, pady=2, sticky="e")

        self._update_clock()

    def _update_clock(self) -> None:
        try:
            if not self.clock_label.winfo_exists():
                return
            ahora = datetime.datetime.now()
            self.clock_label.configure(
                text=f"{ahora.strftime('%d/%m/%Y')} | {ahora.strftime('%H:%M:%S')}"
            )
            self.after(1000, self._update_clock)
        except Exception:
            pass

    def _apply_icon(self) -> None:
        try:
            icon_asset = os.path.join(ASSETS_PATH, "img", b.ICON_FILE)
            logo_asset = os.path.join(ASSETS_PATH, "img", b.LOGO_FILE)
            if os.path.exists(icon_asset) and icon_asset.lower().endswith(".ico"):
                self.iconbitmap(icon_asset)
                self._icon_path = icon_asset
            elif os.path.exists(icon_asset) and PIL_AVAILABLE:
                from PIL import ImageTk

                img = Image.open(icon_asset)
                photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(False, photo)
                self._icon_photo = photo
            elif os.path.exists(logo_asset) and PIL_AVAILABLE:
                from PIL import ImageTk

                img = Image.open(logo_asset)
                photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(False, photo)
                self._icon_photo = photo
        except Exception:
            pass

    # ─────────────────────────────────────────────
    # Configuración
    # ─────────────────────────────────────────────

    def _sensitive_settings_path(self) -> str:
        return os.path.join(BASE_PATH, "runtime_sensitive_settings.json")

    def _load_sensitive_runtime_settings(self) -> dict:
        try:
            return self.secure_config.load(self._sensitive_settings_path()) or {}
        except Exception:
            return {}

    def _save_sensitive_runtime_settings(self) -> None:
        camera_passwords = {}
        for camera in getattr(self, "cameras_config", []):
            name = camera.get("name", "").strip()
            password = camera.get("password", "")
            if name and password:
                camera_passwords[name] = password

        payload = {
            "telegram": {
                "token": getattr(self.telegram_alerter, "token", ""),
                "chat_id": getattr(self.telegram_alerter, "chat_id", ""),
            },
            "camera_passwords": camera_passwords,
        }
        self.secure_config.save(payload, self._sensitive_settings_path())

    @staticmethod
    def _merge_camera_passwords(cameras: list[dict], sensitive_data: dict) -> list[dict]:
        password_map = sensitive_data.get("camera_passwords", {})
        merged = []
        for camera in cameras:
            camera_copy = camera.copy()
            name = camera_copy.get("name", "").strip()
            if name and name in password_map:
                camera_copy["password"] = password_map[name]
            merged.append(camera_copy)
        return merged

    def cargar_configuracion_inicial(self) -> None:
        try:
            path = os.path.join(BASE_PATH, EQUIPOS_CONFIG_FILE)
            data = self.secure_config.load(path)
            if not data:
                raise FileNotFoundError(path)

            equipos_guardados = data.get("equipos", [])
            if equipos_guardados:
                self.equipos_a_monitorear = equipos_guardados

            self.cameras_config = data.get("cameras", [])
            camera_settings = data.get("camera_settings", {})
            self.camera_max_streams = max(int(camera_settings.get("max_streams", 1)), 1)
            self.camera_snapshot_interval = max(int(camera_settings.get("snapshot_interval", 2)), 1)
            self.verify_tls_certificates = bool(camera_settings.get("verify_tls_certificates", True))
            self.enable_external_geolocation = bool(camera_settings.get("enable_external_geolocation", False))
            self.verify_ssh_host_key = bool(camera_settings.get("verify_ssh_host_key", True))
            self.ssh_trust_on_first_use = bool(camera_settings.get("ssh_trust_on_first_use", False))

            self.ping_interval = max(data.get("intervalo_ping", DEFAULT_PING_INTERVAL), 1)

            for eq in self.equipos_a_monitorear:
                ts_str = eq.get("disconnection_timestamp")
                if ts_str:
                    try:
                        eq["disconnection_timestamp"] = datetime.datetime.fromisoformat(ts_str)
                    except Exception:
                        eq["disconnection_timestamp"] = None

            sensitive_data = self._load_sensitive_runtime_settings()
            self.cameras_config = self._merge_camera_passwords(self.cameras_config, sensitive_data)

            tg_cfg = sensitive_data.get("telegram", {}) or data.get("telegram", {})
            token = tg_cfg.get("token") or cfg.TELEGRAM_TOKEN_DEFAULT
            chat_id = tg_cfg.get("chat_id") or cfg.TELEGRAM_CHAT_ID_DEFAULT
            self.telegram_alerter.update_credentials(token, chat_id)

            print("[App] Configuración cargada.")
        except FileNotFoundError:
            print("[App] Sin archivo de configuración. Usando valores por defecto.")
        except InvalidToken:
            print("[App] La configuracion cifrada no pudo descifrarse. Se conservara una copia corrupta y se usaran valores por defecto.")
            try:
                encrypted_path = self.secure_config._get_encrypted_path(path)
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = f"{encrypted_path}.corrupt.{ts}"
                os.rename(encrypted_path, backup_path)
                print(f"[App] Copia de resguardo creada en: {backup_path}")
            except Exception as backup_error:
                print(f"[App] No se pudo resguardar la configuracion corrupta: {backup_error}")
        except Exception as e:
            print(f"[App] Error al cargar configuración: {e}")

    # ─────────────────────────────────────────────
    # Historial y Scheduler
    # ─────────────────────────────────────────────

    def _inicializar_historial(self) -> None:
        self.metricas = MetricasHistoricas()
        self.history_tab.inicializar()

    def _iniciar_scheduler_log(self) -> None:
        def _scheduler():
            last_check_day = datetime.date.today()
            while True:
                now = datetime.datetime.now()
                current_date = now.date()
                current_time = now.time()

                if current_date > last_check_day:
                    self.log_executed_today = {t.isoformat(): False for t in self.scheduler_times}
                    last_check_day = current_date

                for sched_time in self.scheduler_times:
                    key = sched_time.isoformat()
                    if (
                        current_time >= sched_time
                        and current_time.hour == sched_time.hour
                        and current_time.minute == sched_time.minute
                        and not self.log_executed_today[key]
                    ):
                        self._generar_log_historial()
                        if hasattr(self, "metricas"):
                            self.metricas.registrar_disponibilidad_diaria()
                        if sched_time.hour == BACKUP_HOUR and sched_time.minute == BACKUP_MINUTE:
                            self.backup_manager.crear_backup()
                        self.log_executed_today[key] = True

                time.sleep(30)

        threading.Thread(target=_scheduler, daemon=True).start()

    def _generar_log_historial(self) -> None:
        log_path = os.path.join(BASE_PATH, HISTORIAL_LOG_FILE)
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"--- LOG DE ESTADO AUTOMÁTICO: {current_time_str} ---\n")
                for equipo in self.equipos_a_monitorear:
                    ip = equipo["ip"]
                    monitor = self.monitors.get(ip)
                    if monitor:
                        entry = (
                            f"[{current_time_str}] Equipo: {equipo['label']} ({ip}) "
                            f"- Estado: {monitor.status} - MAC: {monitor.mac}"
                        )
                        f.write(entry + "\n")
                f.write("-" * 60 + "\n\n")
        except Exception as e:
            print(f"[App] Error al generar log: {e}")

    # ─────────────────────────────────────────────
    # Acciones de sidebar (delegadas desde Sidebar)
    # ─────────────────────────────────────────────

    def realizar_backup_manual(self) -> None:
        success, msg = self.backup_manager.crear_backup()
        ToastNotification(self, "Backup" if success else "Error Backup", msg, color="green" if success else "red")

    def open_telegram_config(self) -> None:
        TelegramConfigWindow(
            self,
            self.telegram_alerter.token,
            self.telegram_alerter.chat_id,
            self._save_telegram_config,
        )

    def _save_telegram_config(self, token: str, chat_id: str) -> None:
        self.telegram_alerter.update_credentials(token, chat_id)
        self._save_sensitive_runtime_settings()
        if token and chat_id:
            self.telegram_alerter.test_message(b.APP_NAME, b.VERSION)
        if hasattr(self, "monitor_tab"):
            self.monitor_tab.guardar_equipos()

    def save_camera_runtime_settings(
        self,
        max_streams: int,
        snapshot_interval: int,
        verify_tls_certificates: bool | None = None,
        enable_external_geolocation: bool | None = None,
        verify_ssh_host_key: bool | None = None,
        ssh_trust_on_first_use: bool | None = None,
    ) -> None:
        self.camera_max_streams = max(int(max_streams), 1)
        self.camera_snapshot_interval = max(int(snapshot_interval), 1)
        if verify_tls_certificates is not None:
            self.verify_tls_certificates = bool(verify_tls_certificates)
        if enable_external_geolocation is not None:
            self.enable_external_geolocation = bool(enable_external_geolocation)
        if verify_ssh_host_key is not None:
            self.verify_ssh_host_key = bool(verify_ssh_host_key)
        if ssh_trust_on_first_use is not None:
            self.ssh_trust_on_first_use = bool(ssh_trust_on_first_use)
        if hasattr(self, "monitor_tab"):
            self.monitor_tab.guardar_equipos()
        if hasattr(self, "cameras_tab"):
            self.cameras_tab._refresh_stream_status()

    def try_acquire_camera_stream(self) -> bool:
        if self.active_camera_streams >= self.camera_max_streams:
            return False
        self.active_camera_streams += 1
        return True

    def release_camera_stream(self) -> None:
        self.active_camera_streams = max(self.active_camera_streams - 1, 0)

    # ─────────────────────────────────────────────
    # Generación de Reporte PDF
    # ─────────────────────────────────────────────

    def generar_reporte(self) -> None:
        if not REPORTLAB_AVAILABLE:
            ToastNotification(self, "Error", "Libreria PDF no disponible.", color="red")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(BASE_PATH, f"{b.REPORT_FILE_PREFIX}_{timestamp}.pdf")

        try:
            build_network_report(
                ReportContext(
                    filename=filename,
                    app_name=b.APP_NAME,
                    version=b.VERSION,
                    tagline=b.APP_TAGLINE,
                    logo_path=os.path.join(ASSETS_PATH, "img", b.LOGO_FILE),
                    generated_by=self.current_user["full_name"],
                    equipos=self.equipos_a_monitorear,
                    monitors=self.monitors,
                    metricas=getattr(self, "metricas", None),
                    tls_strict=bool(getattr(self, "verify_tls_certificates", False)),
                    cameras_count=len(getattr(self, "cameras_config", [])),
                    camera_max_streams=int(getattr(self, "camera_max_streams", 1)),
                )
            )
            ToastNotification(self, "Reporte PDF", f"Generado: {filename}", color="green")
            if platform.system() == "Windows":
                os.startfile(filename)
        except Exception as e:
            print(f"[App] Error PDF: {e}")
            ToastNotification(self, "Error PDF", str(e), color="red")
