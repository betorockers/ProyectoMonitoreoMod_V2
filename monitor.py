# monitor.py

import customtkinter
import tkinter as tk
import threading
from ping_logic import ping_ip
import time
import subprocess
import platform
import json
import pygame
from plyer import notification
import datetime
import os
import matplotlib
import sys
import string
import secrets
import io

from tkinter import messagebox
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from metrics_manager import MetricasHistoricas
import numpy as np
from PIL import Image
from auth_manager import AuthManager
from key_manager import load_key
from network_tools_logic import is_valid_ip, is_valid_domain, run_secure_command
from cryptography.fernet import InvalidToken
from config.branding import (
    APP_NAME,
    VERSION,
    AUTHOR,
    LOGO_FILE,
    ICON_FILE,
    APP_TAGLINE,
    WINDOW_TITLE,
    REPORT_FILE_PREFIX,
)
from ui.tabs.diagnostics_tab_secure import DiagnosticsTab as ModernDiagnosticsTab
from ui.tabs.video_vigilancia_tab import VideoVigilanciaTab
from ui.tabs.osint_tab import OsintTab
from secure_config_manager import SecureConfigManager
from services.report_builder import ReportContext, build_network_report
from config.build_profile import load_build_profile
from services.telegram_alerter import TelegramAlerter
import config.settings as cfg
from licensing.license_service import LicenseService
from licensing.machine_fingerprint import get_machine_fingerprint
from ui.windows.license_activation_window import LicenseActivationWindow

# Librerías para PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image as PDFImage,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"Error al importar ReportLab: {e}")
    REPORTLAB_AVAILABLE = False

# Lista de equipos por defecto para recuperación o inicio limpio
DEFAULT_EQUIPMENT = [
    {"ip": "10.88.6.58", "label": "Totem de Entrada Quilicura"},
    {"ip": "10.88.6.60", "label": "Totem de salida Quilicura"},
    {"ip": "10.88.6.57", "label": "LPR Quilicura Entrada"},
    {"ip": "10.88.6.54", "label": "LPR Quiilicura salida"},
    {"ip": "10.88.22.59", "label": "Totem de Entrada Renca"},
    {"ip": "10.88.22.65", "label": "Totem de Salida Renca"},
    {"ip": "10.88.22.62", "label": "LPR Renca Entrada"},
    {"ip": "10.88.22.54", "label": "LPR Renca Salida"},
    {"ip": "10.88.6.56", "label": "Kiosko Quilicura"},
    {"ip": "10.88.22.63", "label": "Kiosko Renca"},

    {"ip": "8.8.8.8", "label": "Google DNS (Default)"},
    {"ip": "1.1.1.1", "label": "Cloudflare DNS (Default)"},
]

# --- GESTIÓN DE RUTAS PARA EJECUTABLE (PyInstaller) ---
def get_base_path():
    """Retorna la ruta donde está el ejecutable (para guardar configs/logs)"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    """Retorna la ruta absoluta de un recurso (para leer assets dentro del exe)"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


BASE_PATH = get_base_path()
ASSETS_PATH = get_resource_path("assets")


def apply_window_icon(window):
    """Aplica el icono oficial disponible, con fallback al logo de Anvic."""
    try:
        asset_path = os.path.join(ASSETS_PATH, "img", ICON_FILE)
        if not os.path.exists(asset_path):
            asset_path = os.path.join(ASSETS_PATH, "img", LOGO_FILE)

        if not os.path.exists(asset_path):
            return

        ext = os.path.splitext(asset_path)[1].lower()
        if ext == ".ico":
            try:
                window.iconbitmap(asset_path)
            except tk.TclError:
                pass  # Ignore "bitmap image not valid" errors on frozen builds
            window._icon_path = asset_path
        else:
            photo = tk.PhotoImage(file=asset_path)
            try:
                window.wm_iconphoto(False, photo)
            except tk.TclError:
                pass
            window._icon_photo = photo
    except Exception as e:
        print(f"Error al establecer icono: {e}")


class ToastNotification(customtkinter.CTkToplevel):
    def __init__(self, master, title, message, color="green", duration=5000):
        super().__init__(master)

        self.overrideredirect(True)  # Quitar bordes de ventana
        self.attributes("-topmost", True)  # Siempre al frente

        # Configuración de colores
        bg_color = "#1A1A1A"
        border_color = color if color != "green" else "#51cf66"
        if color == "red":
            border_color = "#ff6b6b"

        self.configure(fg_color=bg_color)

        # Dimensiones y posición (Esquina inferior derecha)
        width = 350
        height = 100
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = screen_width - width - 20
        y = screen_height - height - 60

        self.geometry(f"{width}x{height}+{x}+{y}")

        # Frame principal con borde
        self.main_frame = customtkinter.CTkFrame(
            self,
            corner_radius=10,
            border_width=2,
            border_color=border_color,
            fg_color=bg_color,
        )
        self.main_frame.pack(fill="both", expand=True)

        # Icono y Título
        icon = "🛡️" if color == "green" else "⚠️"
        self.title_label = customtkinter.CTkLabel(
            self.main_frame,
            text=f"{icon} {title}",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF",
        )
        self.title_label.pack(pady=(10, 0), padx=15, anchor="w")

        # Mensaje
        self.message_label = customtkinter.CTkLabel(
            self.main_frame,
            text=message,
            font=("Arial", 12),
            text_color="#CCCCCC",
            wraplength=300,
            justify="left",
        )
        self.message_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Barra de progreso (decorativa)
        self.progress = customtkinter.CTkProgressBar(
            self.main_frame, height=4, progress_color=border_color
        )
        self.progress.pack(fill="x", padx=15, pady=(0, 10))
        self.progress.set(1)

        # Animación de cierre
        self.after(duration, self.destroy)
        self._fade_out(duration)

    def _fade_out(self, duration):
        # Efecto simple de desvanecimiento si fuera posible, o solo cierre
        pass


class LoginWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_login_success, auth_manager):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.auth = auth_manager

        self.title(f"{APP_NAME} - Inicio de Sesión")
        self.geometry("400x550")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Centrar ventana en pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 550) // 2
        self.geometry(f"400x550+{x}+{y}")

        # Configurar icono de la ventana
        self.after(200, lambda: apply_window_icon(self))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        # Logo o Título
        try:
            logo_path = os.path.join(ASSETS_PATH, "img", LOGO_FILE)
            pil_image = Image.open(logo_path)
            self.logo_image = customtkinter.CTkImage(
                light_image=pil_image, dark_image=pil_image, size=(100, 100)
            )
            self.logo_label = customtkinter.CTkLabel(
                self, image=self.logo_image, text=""
            )
            self.logo_label.pack(pady=(40, 10))
        except:
            self.title_label = customtkinter.CTkLabel(
                self,
                text=f"🛡️ {APP_NAME}",
                font=("Arial", 32, "bold"),
                text_color="#00d9ff",
            )
            self.title_label.pack(pady=(40, 10))

        self.subtitle_label = customtkinter.CTkLabel(
            self, text="Inicio de Sesión", font=("Arial", 18)
        )
        self.subtitle_label.pack(pady=(0, 30))

        # Campos de entrada
        self.username_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Usuario",
            width=280,
            height=45,
            font=("Arial", 14),
        )
        self.username_entry.pack(pady=10)

        self.password_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Contraseña",
            show="*",
            width=280,
            height=45,
            font=("Arial", 14),
        )
        self.password_entry.pack(pady=10)

        # Botón de ingreso
        self.login_button = customtkinter.CTkButton(
            self,
            text="INGRESAR",
            command=self.login,
            width=280,
            height=45,
            font=("Arial", 16, "bold"),
            fg_color="#00d9ff",
            text_color="#000000",
            hover_color="#00b4d8",
        )
        self.login_button.pack(pady=(30, 10))

        self.error_label = customtkinter.CTkLabel(
            self, text="", text_color="red", font=("Arial", 12)
        )
        self.error_label.pack(pady=5)

        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())

    def on_close(self):
        import os
        os._exit(0)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user_data = self.auth.authenticate(username, password)
        if user_data:
            if user_data.get("force_change_password", False):
                self.show_change_password_ui(username)
            else:
                self.destroy()
                self.on_login_success(user_data)
        else:
            self.error_label.configure(text="Usuario o contraseña incorrectos")
            self.password_entry.delete(0, "end")

    def show_change_password_ui(self, username):
        # Limpiar campos de login
        self.username_entry.pack_forget()
        self.password_entry.pack_forget()
        self.login_button.pack_forget()
        self.subtitle_label.configure(text="⚠️ Cambio de Contraseña Requerido")
        self.error_label.configure(text="")

        self.new_pass_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Nueva Contraseña",
            show="*",
            width=280,
            height=45,
            font=("Arial", 14),
        )
        self.new_pass_entry.pack(pady=10)

        self.confirm_pass_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Confirmar Contraseña",
            show="*",
            width=280,
            height=45,
            font=("Arial", 14),
        )
        self.confirm_pass_entry.pack(pady=10)

        # Leyenda de requisitos de contraseña
        self.req_label = customtkinter.CTkLabel(
            self,
            text="Mínimo 8 caracteres, 1 Mayúscula, 1 Número\ny 1 Carácter Especial (!@#$%^&*)",
            font=("Arial", 10, "italic"),
            text_color="#AAAAAA",
        )
        self.req_label.pack(pady=5)

        self.change_btn = customtkinter.CTkButton(
            self,
            text="ACTUALIZAR Y ENTRAR",
            command=lambda: self.perform_password_change(username),
            width=280,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#ff9f1c",
            text_color="#000000",
        )
        self.change_btn.pack(pady=20)

    def perform_password_change(self, username):
        p1 = self.new_pass_entry.get()
        p2 = self.confirm_pass_entry.get()

        if not p1 or not p2:
            self.error_label.configure(text="Los campos no pueden estar vacíos")
            return

        if p1 != p2:
            self.error_label.configure(text="Las contraseñas no coinciden")
            return

        success, msg = self.auth.change_password(username, p1)
        if success:
            # Re-autenticar automáticamente para obtener los datos limpios
            user_data = self.auth.authenticate(username, p1)
            self.destroy()
            self.on_login_success(user_data)
        else:
            self.error_label.configure(text=msg)


class SetupWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_setup_success, auth_manager):
        super().__init__(master)
        self.on_setup_success = on_setup_success
        self.auth = auth_manager

        self.title(f"{APP_NAME} - Configuración Inicial")
        self.geometry("450x600")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Centrar ventana
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 600) // 2
        self.geometry(f"450x600+{x}+{y}")

        # Configurar icono de la ventana
        self.after(200, lambda: apply_window_icon(self))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        customtkinter.CTkLabel(
            self,
            text="🚀 Configuración Inicial",
            font=("Arial", 24, "bold"),
            text_color="#00d9ff",
        ).pack(pady=(40, 10)) # yapf: disable

        customtkinter.CTkLabel(
            self,
            text=f"Bienvenido a {APP_NAME}.\nCree su cuenta de Administrador Maestro.",
            font=("Arial", 14),
            text_color="#AAAAAA",
        ).pack(pady=(0, 20))

        self.user_entry = customtkinter.CTkEntry(
            self, placeholder_text="Usuario Maestro", width=300, height=40
        )
        self.user_entry.pack(pady=10)

        self.pass_entry = customtkinter.CTkEntry(
            self, placeholder_text="Contraseña", show="*", width=300, height=40
        )
        self.pass_entry.pack(pady=10)

        self.confirm_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Confirmar Contraseña",
            show="*",
            width=300,
            height=40,
        )
        self.confirm_entry.pack(pady=10)

        # Leyenda de requisitos de contraseña
        customtkinter.CTkLabel(
            self,
            text="Mínimo 8 caracteres, 1 Mayúscula, 1 Número\ny 1 Carácter Especial (!@#$%^&*)",
            font=("Arial", 10, "italic"),
            text_color="#AAAAAA",
        ).pack(pady=5)

        self.btn_save = customtkinter.CTkButton(
            self,
            text="FINALIZAR CONFIGURACIÓN",
            command=self.perform_setup,
            width=300,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#51cf66",
            hover_color="#40c057",
        )
        self.btn_save.pack(pady=30)

        self.error_lbl = customtkinter.CTkLabel(self, text="", text_color="#ff6b6b")
        self.error_lbl.pack(pady=5)

    def on_close(self):
        import os
        os._exit(0)

    def perform_setup(self):
        user = self.user_entry.get()
        p1 = self.pass_entry.get()
        p2 = self.confirm_entry.get()

        if not user or not p1 or not p2:
            self.error_lbl.configure(text="Todos los campos son obligatorios")
            return

        if p1 != p2:
            self.error_lbl.configure(text="Las contraseñas no coinciden")
            return

        success, msg = self.auth.create_initial_superuser(user, p1)
        if success:
            # Autenticar automáticamente
            user_data = self.auth.authenticate(user, p1)
            self.destroy()
            self.on_setup_success(user_data)
        else:
            self.error_lbl.configure(text=msg)


class IPMonitor(customtkinter.CTkFrame):
    def __init__(
        self,
        master,
        ip,
        label,
        desconexiones_count=0,
        mac="Buscando MAC...",
        disconnection_timestamp=None,
    ):
        super().__init__(
            master,
            corner_radius=10,
            fg_color="#2B2B2B",
            border_width=2,
            border_color="#555555",
        )

        self.ip = ip
        self.label = label
        self.status = "Verificando..."
        self.previous_status = None
        self.desconexiones_count = desconexiones_count
        self.mac = mac
        self._ping_thread_active = True

        # Campo para rastrear la fecha y hora exacta de la desconexión
        self.disconnection_timestamp = disconnection_timestamp
        self.critical_telegram_sent = False
        self.bind("<Destroy>", self._mark_ping_thread_inactive, add="+")

        self.grid_columnconfigure(0, weight=1)

        # Diseño de tarjeta compacto y centrado
        self.label_name = customtkinter.CTkLabel(
            self, text=self.label, font=("Arial", 14, "bold"), text_color="#FFFFFF"
        )
        self.label_name.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # Fila 1: IP
        self.ip_label = customtkinter.CTkLabel(
            self, text=self.ip, font=("Arial", 11), text_color="#AAAAAA"
        )
        self.ip_label.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="ew")

        # Fila 2: MAC
        self.mac_label = customtkinter.CTkLabel(
            self, text=self.mac, font=("Arial", 10, "italic"), text_color="#888888"
        )
        self.mac_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")

        # Fila 3: Icono de Status (Cargando inicialmente)
        self.status_icon_label = customtkinter.CTkLabel(
            self, text="⏳", font=("Arial", 24), text_color="#555555"
        )
        self.status_icon_label.grid(row=3, column=0, padx=10, pady=(5, 0), sticky="ew")

        # Fila 4: Texto de Status
        self.status_text_label = customtkinter.CTkLabel(
            self, text="Iniciando...", font=("Arial", 12, "bold"), text_color="#555555"
        )
        self.status_text_label.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

    def update_status(self, new_status, mac_address, latencia=None):
        # Delegar la actualización de la UI al hilo principal de Tkinter
        if not getattr(self, "_ping_thread_active", True):
            return
        try:
            self.after(0, self._update_status_ui, new_status, mac_address, latencia)
        except Exception:
            self._ping_thread_active = False

    def _mark_ping_thread_inactive(self, event=None):
        if event is None or event.widget is self:
            self._ping_thread_active = False

    def _update_status_ui(self, new_status, mac_address, latencia=None):
        # Esta función se ejecuta SIEMPRE en el hilo principal
        if not self.winfo_exists():
            return

        self.previous_status = self.status
        self.status = new_status
        self.mac = mac_address

        # Guardar métrica en la instancia de App
        try:
            app = self.master
            while not isinstance(app, customtkinter.CTk) and app.master is not None:
                app = app.master

            if hasattr(app, "metricas"):
                app.metricas.agregar_medicion(self.ip, latencia, new_status)
        except Exception as e:
            print(f"Error al guardar métrica: {e}")

        self.mac_label.configure(text=self.mac)
        self.update_visuals()
        self.check_for_alert()

    def update_visuals(self):
        if self.status == "Conectado":
            self.configure(border_color="green")
            self.status_icon_label.configure(text="👍", text_color="green")
            self.status_text_label.configure(text="Conectado", text_color="green")
            self.mac_label.configure(text_color="#AAAAAA")
        elif self.status == "Desconectado":
            self.configure(border_color="red")
            self.status_icon_label.configure(text="👎", text_color="red")
            self.status_text_label.configure(text="Desconectado", text_color="red")
            self.mac_label.configure(text="MAC Desconocida", text_color="#777777")
        else:
            self.configure(border_color="#555555")
            self.status_icon_label.configure(text="⏳", text_color="gray")
            self.status_text_label.configure(text=self.status, text_color="gray")
            self.mac_label.configure(text_color="#777777")

    def check_for_alert(self):
        if self.previous_status is not None and self.previous_status != self.status:
            if self.status == "Desconectado":
                self.disconnection_timestamp = datetime.datetime.now()
                self.critical_telegram_sent = False
                self.send_alert(
                    f"¡Alerta! {self.label} está desconectado.", "red", "alerta.mp3"
                )
                self.send_telegram_alert("down")
                self.desconexiones_count += 1
            elif self.status == "Conectado":
                downtime_minutes = None
                if self.disconnection_timestamp:
                    downtime_minutes = max(
                        1,
                        int((datetime.datetime.now() - self.disconnection_timestamp).total_seconds() // 60),
                    )
                self.disconnection_timestamp = None
                self.critical_telegram_sent = False
                self.send_alert(
                    f"¡Recuperado! {self.label} está en línea de nuevo.",
                    "green",
                    "recuperado.mp3",
                )

                self.send_telegram_alert("recovery", downtime_minutes=downtime_minutes)
        elif (
            self.status == "Desconectado"
            and self.disconnection_timestamp
            and not self.critical_telegram_sent
        ):
            elapsed_seconds = (datetime.datetime.now() - self.disconnection_timestamp).total_seconds()
            if elapsed_seconds >= 300:
                self.critical_telegram_sent = True
                self.send_telegram_alert(
                    "critical",
                    downtime_minutes=max(5, int(elapsed_seconds // 60)),
                )

    def send_alert(self, message, color, sound_file):
        # Obtener la instancia principal de la app para acceder a sus propiedades
        app = self.master
        while not isinstance(app, customtkinter.CTk) and app.master is not None:
            app = app.master

        if hasattr(app, "send_alert"):
            app.send_alert(message, color, sound_file)

    def send_telegram_alert(self, alert_type, downtime_minutes=None):
        app = self.master
        while not isinstance(app, customtkinter.CTk) and app.master is not None:
            app = app.master

        if hasattr(app, "send_telegram_status_alert"):
            app.send_telegram_status_alert(
                self.label,
                self.ip,
                alert_type,
                downtime_minutes=downtime_minutes,
            )


class App(customtkinter.CTk):
    def __init__(self, equipos_a_monitorear):
        super().__init__()


        # Centrar ventana principal
        width = 1366
        height = 768
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        # Configurar icono de la ventana
        self.after(200, lambda: apply_window_icon(self))


        self.withdraw()  # Iniciar oculto
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.equipos_a_monitorear = equipos_a_monitorear
        self.current_user = None
        self.services_started = False
        self.build_profile = load_build_profile()

        # --- INICIALIZACIÓN DE SEGURIDAD ---
        # Cargar o generar la clave maestra de cifrado
        self.master_key = load_key(BASE_PATH)
        self.secure_config = SecureConfigManager(self.master_key)
        self.cameras_config = []
        self.camera_max_streams = 1
        self.camera_snapshot_interval = 2
        self.verify_tls_certificates = True
        self.enable_external_geolocation = False
        self.verify_ssh_host_key = True
        self.ssh_trust_on_first_use = False
        self.ssh_known_hosts_path = os.path.join(BASE_PATH, "ssh_known_hosts")
        self.active_camera_streams = 0
        self.telegram_installation_name = ""
        self.telegram_notification_title = "Notificacion enviada desde"
        # Crear una única instancia de AuthManager con el gestor seguro
        self.auth = AuthManager(self.secure_config, BASE_PATH)
        self.telegram_alerter = TelegramAlerter(
            cfg.TELEGRAM_TOKEN_DEFAULT,
            cfg.TELEGRAM_CHAT_ID_DEFAULT,
        )
        self.license_service = LicenseService()
        self.license_state = None

        # --- INICIALIZACIÓN DE AUDIO ROBUSTA ---
        self.audio_enabled = self._initialize_audio()

        self.bootstrap_license_flow()

    def _initialize_audio(self):
        """
        Intenta inicializar el sistema de audio de Pygame probando varios drivers.
        Retorna True si tiene éxito, False en caso contrario.
        """
        # Para sistemas no-Windows, usar el método estándar.
        if platform.system() == "Windows":
            # Lógica de fallback de drivers para Windows, usando el método correcto con os.environ
            drivers = ['wasapi', 'directsound', 'winmm']
            for driver in drivers:
                try:
                    # Establecer la variable de entorno de SDL ANTES de inicializar el mixer
                    os.environ['SDL_AUDIODRIVER'] = driver
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    
                    # Si tiene éxito, imprimir y salir del bucle
                    print(f"[OK] Sistema de audio inicializado con éxito usando el driver: '{driver}'")
                    
                    # Limpiar la variable de entorno para no afectar otros procesos
                    if 'SDL_AUDIODRIVER' in os.environ:
                        del os.environ['SDL_AUDIODRIVER']
                    return True
                except Exception as e:
                    print(f"[INFO] Falló la inicialización con el driver '{driver}': {e}")
                    # Es importante llamar a quit() para limpiar antes del siguiente intento
                    pygame.mixer.quit()

        # Si todos los drivers fallan (o no es Windows), intentar una última vez sin especificar ninguno
        try:
            if 'SDL_AUDIODRIVER' in os.environ:
                del os.environ['SDL_AUDIODRIVER']
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("[OK] Sistema de audio inicializado con éxito (driver por defecto de Pygame).")
            return True
        except Exception as e:
            print(f"[ERROR] ERROR CRÍTICO: No se pudo inicializar el sistema de audio. Último error: {e}")
            return False

    def bootstrap_license_flow(self):
        if not self.build_profile.require_license_activation:
            self.license_state = None
            self.enter_demo_mode()
            return

        pending_state = self.license_service.consume_pending_serial()
        self.license_state = pending_state or self.license_service.get_state()
        if self.license_state.valid:
            self.show_login()
        else:
            self.show_license_activation(self.license_state.message)

    def send_alert(self, message, color="green", sound_file=None):
        """Metodo global para enviar notificaciones tipo Toast y sonidos."""
        try:
            title = f"{APP_NAME}: Notificación"
            ToastNotification(self, title, message, color=color)
        except Exception as e:
            print(f"Error al mostrar Toast: {e}")

        if sound_file and hasattr(self, "audio_enabled") and self.audio_enabled:
            try:
                sound_path = os.path.join(ASSETS_PATH, sound_file)
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self._last_sound = pygame.mixer.Sound(sound_path)
                self._last_sound.play()
            except Exception as e:
                print(f"Error al reproducir el sonido: {e}")
                try:
                    import winsound
                    if "alerta" in sound_file:
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass

    def enter_demo_mode(self):
        self.current_user = {
            "username": "demo",
            "role": "demo",
        }
        self.deiconify()
        self.setup_main_ui()

    def show_license_activation(self, message=""):
        for widget in self.winfo_children():
            widget.destroy()
        self.withdraw()
        self.license_window = LicenseActivationWindow(
            self,
            self.handle_license_activation,
            lambda: __import__('os')._exit(0),
            get_machine_fingerprint(),
            message or "Ingrese un serial valido para continuar.",
        )
        self.license_window.attributes("-topmost", True)
        self.license_window.after(200, lambda: apply_window_icon(self.license_window))

    def open_license_management_dialog(self):
        self.license_window = LicenseActivationWindow(
            self,
            self.handle_license_activation,
            lambda: self.license_window.destroy(),
            get_machine_fingerprint(),
            self.license_service.get_state().message,
        )
        self.license_window.after(200, lambda: apply_window_icon(self.license_window))

    def handle_license_activation(self, serial):
        if not serial.strip():
            if hasattr(self, "license_window"):
                self.license_window.message_label.configure(
                    text="Debe ingresar un serial firmado para continuar.",
                    text_color="#ff6b6b",
                )
            ToastNotification(self, "Licencia", "Debe ingresar un serial valido.", color="red")
            return

        state = self.license_service.activate_serial(serial)
        self.license_state = state
        if state.valid:
            if hasattr(self, "license_window") and self.license_window.winfo_exists():
                self.license_window.destroy()
            ToastNotification(self, "Licencia", "Licencia activada correctamente.", color="green")
            if self.current_user:
                self.refresh_license_summary_ui()
            else:
                self.show_login()
        else:
            if hasattr(self, "license_window") and self.license_window.winfo_exists():
                self.license_window.message_label.configure(text=state.message, text_color="#ff6b6b")
            ToastNotification(self, "Licencia", state.message, color="red")

    def refresh_license_summary_ui(self):
        if self.build_profile.require_license_activation:
            self.license_state = self.license_service.get_state()
        summary = self.get_effective_license_summary()
        if hasattr(self, "license_summary_labels"):
            for key, label in self.license_summary_labels.items():
                label.configure(text=self._format_license_summary_value(key, summary.get(key, "-")))
        self.title(self._build_window_title(summary))

    def get_effective_license_summary(self) -> dict:
        if not self.build_profile.require_license_activation:
            return {
                "valid": True,
                "status": "demo",
                "message": "Compilacion demo con funciones basicas.",
                "edition": "DEMO",
                "license_type": "DEMO",
                "license_id": "DEMO-BUILD",
                "expires_at": "-",
                "customer_name": "ANVIC",
                "bound_machine": get_machine_fingerprint(),
            }
        return self.license_service.get_summary()

    @staticmethod
    def _build_license_banner_text(summary: dict) -> str:
        edition_map = {"STANDARD": "Standard", "ADVANCED": "Advanced", "PRO": "Pro"}
        type_map = {"TRIAL": "Trial", "ANNUAL": "Anual", "PERPETUAL": "Perpetua"}
        status = summary.get("status", "missing")
        if status == "demo":
            return "Modo Demo"
        edition = edition_map.get(str(summary.get("edition", "-")).upper(), str(summary.get("edition", "-")))
        license_type = type_map.get(
            str(summary.get("license_type", "-")).upper(),
            str(summary.get("license_type", "-")),
        )
        if status == "valid":
            return f"Licencia activa: {edition} {license_type}"
        if status == "expired":
            return f"Licencia vencida: {edition} {license_type}"
        return "Licencia no activa"

    @staticmethod
    def _build_license_banner_color(summary: dict) -> str:
        status = summary.get("status", "missing")
        if status == "demo":
            return "#4dabf7"
        if status == "valid":
            return "#51cf66"
        if status == "expired":
            return "#ff922b"
        return "#ff6b6b"

    def _build_window_title(self, summary: dict | None = None) -> str:
        summary = summary or self.get_effective_license_summary()
        title = WINDOW_TITLE
        if self.build_profile.window_title_suffix:
            title = f"{title} [{self.build_profile.window_title_suffix}]"
        return f"{title} | {self._build_license_banner_text(summary)}"

    @staticmethod
    def _format_license_summary_value(key: str, value) -> str:
        if value in (None, "", "-"):
            return "No aplica" if key == "expires_at" else "-"

        if key == "status":
            status_map = {
                "demo": "Demo",
                "valid": "Valido",
                "expired": "Vencido",
                "missing": "Sin licencia",
                "invalid": "Invalido",
                "mismatch": "No coincide con este equipo",
                "clock_tamper": "Fecha del sistema inconsistente",
            }
            return status_map.get(str(value).lower(), str(value).capitalize())

        if key == "edition":
            edition_map = {
                "DEMO": "Demo",
                "STANDARD": "Standard",
                "ADVANCED": "Advanced",
                "PRO": "Pro",
            }
            return edition_map.get(str(value).upper(), str(value))

        if key == "license_type":
            type_map = {
                "DEMO": "Demo",
                "TRIAL": "Trial",
                "ANNUAL": "Anual",
                "PERPETUAL": "Perpetua",
            }
            return type_map.get(str(value).upper(), str(value))

        if key == "expires_at":
            try:
                expiry = datetime.datetime.fromisoformat(str(value))
                return expiry.strftime("%d-%m-%Y")
            except ValueError:
                return str(value)

        return str(value)

    def _build_telegram_origin_text(self) -> str:
        title = (self.telegram_notification_title or "Notificacion enviada desde").strip()
        installation = (self.telegram_installation_name or "").strip()
        if installation:
            return f"{title} {installation}"
        return title

    def _build_telegram_message(self, label, ip, alert_type, downtime_minutes=None):
        origin = self._build_telegram_origin_text()
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        lines = [origin, ""]

        if alert_type == "down":
            lines.extend(
                [
                    "Estado detectado: EQUIPO DESCONECTADO",
                    f"Equipo: {label}",
                    f"IP: {ip}",
                    f"Hora: {timestamp}",
                ]
            )
        elif alert_type == "recovery":
            lines.extend(
                [
                    "Estado detectado: EQUIPO RECUPERADO",
                    f"Equipo: {label}",
                    f"IP: {ip}",
                    f"Hora: {timestamp}",
                ]
            )
            if downtime_minutes:
                lines.append(f"Tiempo estimado fuera de linea: {downtime_minutes} minuto(s)")
        elif alert_type == "critical":
            lines.extend(
                [
                    "ALERTA DE GRAVEDAD: EQUIPO SIGUE DESCONECTADO",
                    f"Equipo: {label}",
                    f"IP: {ip}",
                    f"Hora: {timestamp}",
                    f"Tiempo caido: {downtime_minutes or 5} minuto(s) o mas",
                ]
            )
        else:
            lines.extend([f"Equipo: {label}", f"IP: {ip}", f"Hora: {timestamp}"])

        return "\n".join(lines)

    def send_telegram_status_alert(self, label, ip, alert_type, downtime_minutes=None):
        if not hasattr(self, "telegram_alerter") or not self.telegram_alerter.enabled:
            return

        try:
            message = self._build_telegram_message(
                label,
                ip,
                alert_type,
                downtime_minutes=downtime_minutes,
            )
            self.telegram_alerter.send_alert(message)
        except Exception as e:
            print(f"[Telegram] Error al preparar alerta: {e}")

    def save_telegram_runtime_settings(self, token, chat_id, installation_name, notification_title, send_test=False):
        self.telegram_installation_name = installation_name.strip()
        self.telegram_notification_title = (
            notification_title.strip() or "Notificacion enviada desde"
        )
        self.telegram_alerter.update_credentials(token.strip(), chat_id.strip())
        self.guardar_equipos()

        if send_test and self.telegram_alerter.enabled:
            self.telegram_alerter.send_alert(
                self._build_telegram_message(
                    "Prueba de Telegram",
                    "N/A",
                    "test",
                )
            )

    def on_closing(self):
        """Hard kill of the app and all background threads to avoid zombies"""
        import os
        os._exit(0)

    def show_login(self):
        # Detener hilos y procesos en segundo plano
        if hasattr(self, 'monitors'):
            for monitor in self.monitors.values():
                monitor._ping_thread_active = False
        
        if hasattr(self, 'video_vigilancia_controller'):
            self.video_vigilancia_controller.is_playing = False
            self.video_vigilancia_controller.is_recording = False

        # Limpiar ventana principal y ocultarla
        for widget in self.winfo_children():
            widget.destroy()
        self.withdraw()
        
        # Resetear recursos clave
        self.monitors = {}
        self.services_started = False

        # Si no hay usuarios registrados, mostrar Setup
        if not self.auth.users:
            self.setup_window = SetupWindow(self, self.on_login_success, self.auth)
            self.setup_window.attributes("-topmost", True)
        else:
            self.login_window = LoginWindow(self, self.on_login_success, self.auth)
            self.login_window.attributes("-topmost", True)

    def on_login_success(self, user_data):
        self.current_user = user_data
        self.deiconify()  # Mostrar ventana principal
        self.setup_main_ui()

    def setup_main_ui(self):
        # Título personalizado solicitado por el usuario
        self.title(self._build_window_title())


        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.ping_interval = 15

        self.scheduler_times = [datetime.time(11, 0, 0), datetime.time(14, 30, 0)]
        self.log_executed_today = {t.isoformat(): False for t in self.scheduler_times}

        # Cargar configuración pero NO sobrescribir si ya tenemos equipos de main.py
        self.cargar_configuracion_inicial()

        # Crear sistema de pestañas
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.tab_monitoreo = self.tabview.add("Operacion en Vivo")
        self.tab_historial = self.tabview.add("Historial Operacional")

        if self.build_profile.enable_visual_supervision:
            self.tab_camaras = self.tabview.add("Video Vigilancia")
            self.video_vigilancia_controller = VideoVigilanciaTab(self, self.tab_camaras)

        if (
            self.build_profile.enable_support_center
            and self.build_profile.enable_administration
            and self.current_user["role"] in ["super_admin", "admin"]
        ):
            self.tab_diagnostico = self.tabview.add("Servicios OSINT")
            self.osint_controller = OsintTab(self, self.tab_diagnostico)
            
            self.tab_usuarios = self.tabview.add("Administracion")
            self.setup_user_management_tab()
        self.refresh_license_summary_ui()

        self.monitor_frame = customtkinter.CTkScrollableFrame(self.tab_monitoreo)
        self.monitor_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.historial_frame = customtkinter.CTkScrollableFrame(self.tab_historial)
        self.historial_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=0)
        self.button_frame.grid_columnconfigure(2, weight=1)

        self.refresh_button = customtkinter.CTkButton(
            self.button_frame,
            text="Recargar",
            font=("Arial", 14, "bold"),
            command=self.create_monitors,
        )
        self.refresh_button.grid(row=0, column=1, padx=10, pady=5)

        self.footer_frame = customtkinter.CTkFrame(self, height=40, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, sticky="ew")

        self.footer_frame.grid_columnconfigure(0, weight=0)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_columnconfigure(2, weight=1)
        self.footer_frame.grid_columnconfigure(3, weight=0)

        # Indicador de estado de audio
        audio_icon = "🔊" if self.audio_enabled else "🔇"
        audio_color = "#51cf66" if self.audio_enabled else "#ff6b6b"
        self.audio_status_label = customtkinter.CTkLabel(
            self.footer_frame, text=audio_icon, font=("Arial", 14), text_color=audio_color
        )
        self.audio_status_label.grid(row=0, column=0, padx=(20, 5), pady=2, sticky="w")

        self.clock_label = customtkinter.CTkLabel(
            self.footer_frame, text="", font=("Arial", 12, "bold"), text_color="#00d9ff"
        )
        self.clock_label.grid(row=0, column=1, padx=0, pady=2, sticky="w")

        leyenda_label = customtkinter.CTkLabel(
            self.footer_frame,
            text=f"{APP_NAME}: {APP_TAGLINE}",
            font=("Arial", 12, "bold"),
            text_color="#FFFFFF",
        )
        leyenda_label.grid(row=0, column=2, padx=10, pady=2, sticky="ew")

        nombre_label = customtkinter.CTkLabel(
            self.footer_frame,
            text=f"Desarrollado por {AUTHOR}",
            font=("Arial", 12, "italic"),
            text_color="#999999",
        )
        nombre_label.grid(row=0, column=3, padx=20, pady=2, sticky="e")

        # Iniciar reloj
        self.update_clock()

        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=1, rowspan=3, sticky="nsew")

        # Mejora de Logo 75x75 (Ajuste de espacio solicitado por el usuario)
        try:
            logo_path = os.path.join(ASSETS_PATH, "img", LOGO_FILE)
            pil_image = Image.open(logo_path)
            # Calcular dimensiones manteniendo el aspecto dentro de un cuadro de 75x75
            orig_w, orig_h = pil_image.size
            ratio = min(75 / orig_w, 75 / orig_h)
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)

            self.logo_image = customtkinter.CTkImage(
                light_image=pil_image, dark_image=pil_image, size=(new_w, new_h)
            )
            self.logo_label = customtkinter.CTkLabel(
                self.sidebar_frame, image=self.logo_image, text=""
            )
            self.logo_label.grid(row=0, column=0, padx=10, pady=10)

            # Título del panel debajo del logo
            self.sidebar_title = customtkinter.CTkLabel(
                self.sidebar_frame, text="Panel de Control", font=("Arial", 16, "bold")
            )
            self.sidebar_title.grid(row=1, column=0, padx=10, pady=(0, 10))
        except Exception as e:
            print(f"Error al cargar el logo: {e}")
            self.sidebar_title = customtkinter.CTkLabel(
                self.sidebar_frame, text="Panel de Control", font=("Arial", 16, "bold")
            )
            self.sidebar_title.grid(row=0, column=0, padx=10, pady=10)

        self.sidebar_frame.grid_rowconfigure(14, weight=1)

        # Fila 2 en adelante para los controles
        self.interval_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Intervalo Ping (Segundos):", font=("Arial", 12)
        )
        self.interval_label.grid(row=2, column=0, padx=10, pady=(5, 0), sticky="w")

        self.ping_interval_entry = customtkinter.CTkEntry(
            self.sidebar_frame, placeholder_text="ej. 1, 5, 30", justify="center"
        )
        self.ping_interval_entry.grid(row=3, column=0, padx=10, pady=2, sticky="ew")
        self.ping_interval_entry.insert(0, str(self.ping_interval))

        self.ip_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="IP, URL o Dominio:", font=("Arial", 12)
        )
        self.ip_label.grid(row=4, column=0, padx=10, pady=(5, 0), sticky="w")
        self.ip_entry = customtkinter.CTkEntry(
            self.sidebar_frame, placeholder_text="ej. 192.168.1.1 o web.cl"
        )
        self.ip_entry.grid(row=5, column=0, padx=10, pady=2, sticky="ew")

        self.etiqueta_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Etiqueta:", font=("Arial", 12)
        )
        self.etiqueta_label.grid(row=6, column=0, padx=10, pady=(5, 0), sticky="w")
        self.etiqueta_entry = customtkinter.CTkEntry(
            self.sidebar_frame, placeholder_text="ej. Servidor Principal"
        )
        self.etiqueta_entry.grid(row=7, column=0, padx=10, pady=2, sticky="ew")

        self.add_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Agregar Equipo", command=self.agregar_equipo
        )
        self.add_button.grid(row=8, column=0, padx=10, pady=10)

        self.remove_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Eliminar Equipo (por IP):", font=("Arial", 12)
        )
        self.remove_label.grid(row=9, column=0, padx=10, pady=(5, 0), sticky="w")

        self.remove_entry = customtkinter.CTkEntry(
            self.sidebar_frame, placeholder_text="ej. 192.168.1.1"
        )
        self.remove_entry.grid(row=10, column=0, padx=10, pady=2, sticky="ew")

        self.remove_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Eliminar Equipo", command=self.remover_equipo
        )
        self.remove_button.grid(row=11, column=0, padx=10, pady=10)

        self.save_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Guardar Configuración",
            command=self.guardar_equipos,
        )
        self.save_button.grid(row=12, column=0, padx=10, pady=5)

        self.load_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Cargar Configuración", command=self.cargar_equipos
        )
        self.load_button.grid(row=13, column=0, padx=10, pady=5)

        self.report_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Generar Reporte", command=self.generar_reporte
        )
        self.report_button.grid(row=14, column=0, padx=10, pady=10)

        self.logout_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Cerrar Sesión",
            command=self.show_login,
            fg_color="#ff6b6b",
            hover_color="#fa5252",
        )
        self.logout_button.grid(row=15, column=0, padx=10, pady=10)

        # Restricciones de Rol
        if self.current_user["role"] == "user":
            self.add_button.configure(state="disabled")
            self.remove_button.configure(state="disabled")
            self.save_button.configure(state="disabled")
            self.load_button.configure(state="disabled")
            self.report_button.configure(state="disabled")
            self.ping_interval_entry.configure(state="disabled")
            self.ip_entry.configure(state="disabled")
            self.etiqueta_entry.configure(state="disabled")
            self.remove_entry.configure(state="disabled")
            if hasattr(self, "camera_settings_save_button"):
                self.camera_settings_save_button.configure(state="disabled")
                self.camera_max_streams_entry.configure(state="disabled")
                self.camera_snapshot_interval_entry.configure(state="disabled")
                self.verify_tls_switch.configure(state="disabled")

        self.monitors = {}
        # Prioridad 1: Crear tarjetas e iniciar pings de inmediato
        self.create_monitors()

        # Prioridad 2: Iniciar servicios de fondo (solo una vez)
        if not self.services_started:
            self.iniciar_scheduler_log()
            self.services_started = True

        # Prioridad 3: Cargar historial y gráficos con un ligero retraso para no bloquear la UI inicial
        self.after(500, self.inicializar_historial)

    def setup_user_management_tab(self):
        self.admin_scroll_frame = customtkinter.CTkScrollableFrame(self.tab_usuarios)
        self.admin_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame para agregar usuarios
        self.add_user_frame = customtkinter.CTkFrame(self.admin_scroll_frame)
        self.add_user_frame.pack(fill="x", padx=20, pady=20)

        customtkinter.CTkLabel(
            self.add_user_frame,
            text="Agregar Nuevo Usuario",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=10)

        customtkinter.CTkLabel(self.add_user_frame, text="Usuario:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.new_username_entry = customtkinter.CTkEntry(self.add_user_frame)
        self.new_username_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(self.add_user_frame, text="Nombre Completo:").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.new_fullname_entry = customtkinter.CTkEntry(self.add_user_frame)
        self.new_fullname_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(self.add_user_frame, text="Contraseña:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.new_password_entry = customtkinter.CTkEntry(self.add_user_frame, show="*")
        self.new_password_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(self.add_user_frame, text="Confirmar Clave:").grid(
            row=4, column=0, padx=10, pady=5, sticky="e"
        )
        self.confirm_password_entry = customtkinter.CTkEntry(
            self.add_user_frame, show="*"
        )
        self.confirm_password_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(self.add_user_frame, text="Rol:").grid(
            row=5, column=0, padx=10, pady=5, sticky="e"
        )
        roles = ["user"]
        if self.current_user["role"] == "super_admin":
            roles.append("admin")

        self.new_role_option = customtkinter.CTkOptionMenu(
            self.add_user_frame, values=roles
        )
        self.new_role_option.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        self.create_user_button = customtkinter.CTkButton(
            self.add_user_frame, text="Crear Usuario", command=self.crear_usuario
        )
        self.create_user_button.grid(row=6, column=0, columnspan=2, pady=20)

        self.telegram_frame = customtkinter.CTkFrame(self.admin_scroll_frame)
        self.telegram_frame.pack(fill="x", padx=20, pady=(0, 20))

        customtkinter.CTkLabel(
            self.telegram_frame,
            text="Notificaciones Telegram",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")

        customtkinter.CTkLabel(self.telegram_frame, text="Bot Token:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.telegram_token_entry = customtkinter.CTkEntry(self.telegram_frame, width=360)
        self.telegram_token_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.telegram_token_entry.insert(0, getattr(self.telegram_alerter, "token", ""))

        customtkinter.CTkLabel(self.telegram_frame, text="Chat ID:").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.telegram_chat_id_entry = customtkinter.CTkEntry(self.telegram_frame, width=360)
        self.telegram_chat_id_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.telegram_chat_id_entry.insert(0, getattr(self.telegram_alerter, "chat_id", ""))

        customtkinter.CTkLabel(self.telegram_frame, text="Instalacion:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.telegram_installation_entry = customtkinter.CTkEntry(self.telegram_frame, width=360)
        self.telegram_installation_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.telegram_installation_entry.insert(0, getattr(self, "telegram_installation_name", ""))

        customtkinter.CTkLabel(self.telegram_frame, text="Titulo base:").grid(
            row=4, column=0, padx=10, pady=5, sticky="e"
        )
        self.telegram_title_entry = customtkinter.CTkEntry(self.telegram_frame, width=360)
        self.telegram_title_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        self.telegram_title_entry.insert(
            0,
            getattr(self, "telegram_notification_title", "Notificacion enviada desde"),
        )

        customtkinter.CTkLabel(
            self.telegram_frame,
            text="Ejemplo: si el titulo base es 'Notificacion enviada desde' y la instalacion es 'CIAL', cada alerta comenzara con 'Notificacion enviada desde CIAL'. Tambien se enviara una alerta critica si un equipo sigue caido por mas de 5 minutos.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.telegram_save_button = customtkinter.CTkButton(
            self.telegram_frame,
            text="Guardar y probar Telegram",
            command=self.guardar_config_telegram,
        )
        self.telegram_save_button.grid(row=6, column=0, columnspan=2, pady=12)

        self.camera_settings_frame = customtkinter.CTkFrame(self.admin_scroll_frame)
        self.camera_settings_frame.pack(fill="x", padx=20, pady=(0, 20))

        customtkinter.CTkLabel(
            self.camera_settings_frame, text="Configuracion de Streaming", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        customtkinter.CTkLabel(self.camera_settings_frame, text="Maximo de streams:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.camera_max_streams_entry = customtkinter.CTkEntry(self.camera_settings_frame)
        self.camera_max_streams_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.camera_max_streams_entry.insert(0, str(getattr(self, "camera_max_streams", 1)))

        customtkinter.CTkLabel(self.camera_settings_frame, text="Intervalo snapshot (seg):").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.camera_snapshot_interval_entry = customtkinter.CTkEntry(self.camera_settings_frame)
        self.camera_snapshot_interval_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.camera_snapshot_interval_entry.insert(0, str(getattr(self, "camera_snapshot_interval", 2)))

        self.verify_tls_switch = customtkinter.CTkSwitch(
            self.camera_settings_frame,
            text="Modo TLS estricto (desactivalo para usar verify=False)",
        )
        self.verify_tls_switch.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")
        if getattr(self, "verify_tls_certificates", False):
            self.verify_tls_switch.select()
        else:
            self.verify_tls_switch.deselect()

        customtkinter.CTkLabel(
            self.camera_settings_frame,
            text="Si lo desactivas, Sentinel permitira certificados autofirmados o invalidos en HTTPS para camaras, NVR y paneles legacy.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.external_geolocation_switch = customtkinter.CTkSwitch(
            self.camera_settings_frame,
            text="Permitir geolocalizacion externa en Tracert",
        )
        self.external_geolocation_switch.grid(row=5, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        if getattr(self, "enable_external_geolocation", False):
            self.external_geolocation_switch.select()
        else:
            self.external_geolocation_switch.deselect()

        customtkinter.CTkLabel(
            self.camera_settings_frame,
            text="Cuando esta opcion esta activa, los saltos publicos de Tracert se enriquecen consultando un servicio externo. Se recomienda dejarla desactivada por defecto.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.verify_ssh_host_key_switch = customtkinter.CTkSwitch(
            self.camera_settings_frame,
            text="Validar huella SSH del host",
        )
        self.verify_ssh_host_key_switch.grid(row=7, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        if getattr(self, "verify_ssh_host_key", True):
            self.verify_ssh_host_key_switch.select()
        else:
            self.verify_ssh_host_key_switch.deselect()

        self.ssh_tofu_switch = customtkinter.CTkSwitch(
            self.camera_settings_frame,
            text="Permitir confianza inicial SSH (TOFU)",
        )
        self.ssh_tofu_switch.grid(row=8, column=0, columnspan=2, padx=10, pady=(2, 4), sticky="w")
        if getattr(self, "ssh_trust_on_first_use", False):
            self.ssh_tofu_switch.select()
        else:
            self.ssh_tofu_switch.deselect()

        customtkinter.CTkLabel(
            self.camera_settings_frame,
            text="Con validacion SSH activa, Sentinel solo aceptara servidores conocidos. TOFU permite registrar la primera huella automaticamente y exigirla en conexiones futuras.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.camera_settings_save_button = customtkinter.CTkButton(
            self.camera_settings_frame, text="Guardar streaming, TLS y red", command=self.guardar_config_streaming
        )
        self.camera_settings_save_button.grid(row=10, column=0, columnspan=2, pady=15)

        self.license_frame = customtkinter.CTkFrame(self.admin_scroll_frame)
        self.license_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.license_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            self.license_frame, text="Licenciamiento", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        self.license_summary_labels = {}
        license_rows = [
            ("status", "Estado"),
            ("edition", "Edicion"),
            ("license_type", "Tipo"),
            ("license_id", "ID de licencia"),
            ("expires_at", "Vence"),
            ("bound_machine", "Huella equipo"),
        ]
        for row_index, (key, title) in enumerate(license_rows, start=1):
            customtkinter.CTkLabel(self.license_frame, text=f"{title}:").grid(
                row=row_index, column=0, padx=10, pady=4, sticky="e"
            )
            value_label = customtkinter.CTkLabel(
                self.license_frame,
                text="-",
                anchor="w",
                justify="left",
                wraplength=360,
                text_color="#DDDDDD",
            )
            value_label.grid(row=row_index, column=1, padx=10, pady=4, sticky="ew")
            self.license_summary_labels[key] = value_label

        self.license_manage_button = customtkinter.CTkButton(
            self.license_frame,
            text="Actualizar licencia",
            command=self.open_license_management_dialog,
        )
        self.license_manage_button.grid(row=len(license_rows) + 1, column=0, columnspan=2, padx=10, pady=15)
        self.refresh_license_summary_ui()

        # Lista de usuarios
        self.user_list_frame = customtkinter.CTkScrollableFrame(
            self.admin_scroll_frame, label_text="Usuarios Existentes"
        )
        self.user_list_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.actualizar_lista_usuarios()

    def crear_usuario(self):
        username = self.new_username_entry.get()
        fullname = self.new_fullname_entry.get()
        p1 = self.new_password_entry.get()
        p2 = self.confirm_password_entry.get()
        role = self.new_role_option.get()

        if not username or not fullname or not p1 or not p2:
            ToastNotification(
                self, "Error", "Todos los campos son obligatorios", color="red"
            )
            return

        if p1 != p2:
            ToastNotification(self, "Error", "Las contraseñas no coinciden", color="red")
            return

        success, message = self.auth.add_user(
            username, p1, role, fullname, self.current_user["role"]
        )
        if success:
            ToastNotification(self, "Éxito", message, color="green")
            self.new_username_entry.delete(0, "end")
            self.new_fullname_entry.delete(0, "end")
            self.new_password_entry.delete(0, "end")
            self.confirm_password_entry.delete(0, "end")
            self.actualizar_lista_usuarios()
        else:
            ToastNotification(self, "Error", message, color="red")

    def guardar_config_telegram(self):
        token = self.telegram_token_entry.get().strip()
        chat_id = self.telegram_chat_id_entry.get().strip()
        installation_name = self.telegram_installation_entry.get().strip()
        notification_title = self.telegram_title_entry.get().strip()

        if (token and not chat_id) or (chat_id and not token):
            ToastNotification(
                self,
                "Error",
                "Debes ingresar Token y Chat ID, o dejar ambos vacios para desactivar Telegram.",
                color="red",
            )
            return

        self.save_telegram_runtime_settings(
            token,
            chat_id,
            installation_name,
            notification_title,
            send_test=bool(token and chat_id),
        )

        if token and chat_id:
            ToastNotification(
                self,
                "Telegram",
                "Configuracion guardada y prueba enviada correctamente.",
                color="green",
            )
        else:
            ToastNotification(
                self,
                "Telegram",
                "Notificaciones de Telegram desactivadas.",
                color="green",
            )

    def guardar_config_streaming(self):
        try:
            max_streams = max(int(self.camera_max_streams_entry.get()), 1)
            snapshot_interval = max(int(self.camera_snapshot_interval_entry.get()), 1)
        except ValueError:
            ToastNotification(self, "Error", "Los valores de streaming deben ser numericos", color="red")
            return

        verify_tls_certificates = bool(self.verify_tls_switch.get())
        enable_external_geolocation = bool(self.external_geolocation_switch.get())
        verify_ssh_host_key = bool(self.verify_ssh_host_key_switch.get())
        ssh_trust_on_first_use = bool(self.ssh_tofu_switch.get())
        self.save_camera_runtime_settings(
            max_streams,
            snapshot_interval,
            verify_tls_certificates=verify_tls_certificates,
            enable_external_geolocation=enable_external_geolocation,
            verify_ssh_host_key=verify_ssh_host_key,
            ssh_trust_on_first_use=ssh_trust_on_first_use,
        )
        mode = "estricto" if verify_tls_certificates else "flexible/autofirmado"
        geo = "activa" if enable_external_geolocation else "desactivada"
        ssh_mode = (
            "estricto"
            if verify_ssh_host_key and not ssh_trust_on_first_use
            else "tofu"
            if verify_ssh_host_key and ssh_trust_on_first_use
            else "sin validacion"
        )
        ToastNotification(self, "Streaming", f"Configuracion actualizada. TLS: {mode} | Geo externa: {geo} | SSH: {ssh_mode}", color="green")

    def actualizar_lista_usuarios(self):
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        users = self.auth.get_all_users(self.current_user["role"])
        for i, user in enumerate(users):
            user_info = f"{user['full_name']} ({user['username']}) - Rol: {user['role']}"
            customtkinter.CTkLabel(self.user_list_frame, text=user_info).grid(
                row=i, column=0, padx=10, pady=5, sticky="w"
            )

            if (
                self.current_user["role"] == "super_admin"
                and user["username"] != self.current_user["username"]
            ):
                btn_delete = customtkinter.CTkButton(
                    self.user_list_frame,
                    text="Eliminar",
                    width=60,
                    fg_color="#ff6b6b",
                    command=lambda u=user["username"]: self.eliminar_usuario(u),
                )
                btn_delete.grid(row=i, column=1, padx=10, pady=5)

    def eliminar_usuario(self, username):
        success, message = self.auth.delete_user(username, self.current_user["role"])
        if success:
            ToastNotification(self, "Éxito", message, color="green")
            self.actualizar_lista_usuarios()
        else:
            ToastNotification(self, "Error", message, color="red")

    def setup_diagnostics_tab(self):
        """Inicializa la pestaña de diagnóstico moderna reutilizable."""
        self.diagnostics_tab_controller = ModernDiagnosticsTab(self, self.tab_diagnostico)

    def run_diagnostic_tool(self, tool):
        target = self.diag_target_entry.get().strip()
        if not target:
            ToastNotification(self, "Error", "El campo de IP o Dominio no puede estar vacío.", color="red")
            return

        if not is_valid_ip(target) and not is_valid_domain(target):
            ToastNotification(self, "Error", "La entrada no es una IP o dominio válido.", color="red")
            return
        
        self.ping_button.configure(state="disabled")
        self.tracert_button.configure(state="disabled")
        self.nslookup_button.configure(state="disabled")
        if hasattr(self, "release_button"):
            self.release_button.configure(state="disabled")
            self.renew_button.configure(state="disabled")
            self.flush_button.configure(state="disabled")


        self.diag_output_textbox.configure(state="normal")
        self.diag_output_textbox.delete("1.0", "end")
        self.diag_output_textbox.insert("end", f"Ejecutando {tool} en {target}...\n\n")
        self.diag_output_textbox.configure(state="disabled")

        thread = threading.Thread(target=self._diagnostic_worker, args=(tool, target), daemon=True)
        thread.start()

    def _diagnostic_worker(self, tool, target):
        command = []
        if tool == "ping":
            param = "-n" if platform.system() == "Windows" else "-c"
            command = ["ping", param, "4", target]
        elif tool == "tracert":
            command = ["tracert", target] if platform.system() == "Windows" else ["traceroute", target]
        elif tool == "nslookup":
            command = ["nslookup", target]
        
        output = run_secure_command(command)
        self.after(0, self._update_diagnostic_output, output)

    def _update_diagnostic_output(self, output):
        self.diag_output_textbox.configure(state="normal")
        self.diag_output_textbox.insert("end", output)
        self.diag_output_textbox.insert("end", "\n\n--- Diagnóstico finalizado ---")
        self.diag_output_textbox.configure(state="disabled")

        self.ping_button.configure(state="normal")
        self.tracert_button.configure(state="normal")
        self.nslookup_button.configure(state="normal")
        if hasattr(self, "release_button"):
            self.release_button.configure(state="normal")
            self.renew_button.configure(state="normal")
            self.flush_button.configure(state="normal")

    def run_maintenance_tool(self, tool):
        # Confirmation dialog
        confirmation = messagebox.askyesno(
            "Confirmación de Acción",
            f"¿Está seguro de que desea ejecutar 'ipconfig /{tool}'?\n"
            "Esta acción puede interrumpir temporalmente su conectividad de red.",
            icon='warning'
        )
        if not confirmation:
            return

        self.diag_output_textbox.configure(state="normal")
        self.diag_output_textbox.delete("1.0", "end")
        self.diag_output_textbox.insert("end", f"Ejecutando ipconfig /{tool}...\n\n")
        self.diag_output_textbox.configure(state="disabled")
        
        # Disable all buttons
        self.ping_button.configure(state="disabled")
        self.tracert_button.configure(state="disabled")
        self.nslookup_button.configure(state="disabled")
        self.release_button.configure(state="disabled")
        self.renew_button.configure(state="disabled")
        self.flush_button.configure(state="disabled")

        thread = threading.Thread(target=self._maintenance_worker, args=(tool,), daemon=True)
        thread.start()

    def _maintenance_worker(self, tool):
        command = ["ipconfig", f"/{tool}"]
        output = run_secure_command(command)
        self.after(0, self._update_maintenance_output, tool, output)

    def _update_maintenance_output(self, tool, output):
        self.diag_output_textbox.configure(state="normal")
        self.diag_output_textbox.insert("end", output)
        self.diag_output_textbox.insert("end", f"\n\n--- Mantenimiento 'ipconfig /{tool}' finalizado ---")
        self.diag_output_textbox.configure(state="disabled")

        # Re-enable all buttons
        self.ping_button.configure(state="normal")
        self.tracert_button.configure(state="normal")
        self.nslookup_button.configure(state="normal")
        self.release_button.configure(state="normal")
        self.renew_button.configure(state="normal")
        self.flush_button.configure(state="normal")
        
        ToastNotification(self, "Mantenimiento", "Comando ejecutado con éxito.", color="green")

    def update_clock(self):
        """Actualiza el reloj del footer cada segundo"""
        try:
            if not hasattr(self, "clock_label") or not self.clock_label.winfo_exists():
                return

            ahora = datetime.datetime.now().strftime("%H:%M:%S")
            fecha = datetime.datetime.now().strftime("%d/%m/%Y")
            self.clock_label.configure(text=f"{fecha} | {ahora}")
            self.after(1000, self.update_clock)
        except Exception:
            pass

    def cargar_configuracion_inicial(self):
        config_path = os.path.join(BASE_PATH, "equipos_guardados.json")
        try:
            data = self.secure_config.load(config_path)

            if not data:
                print("Archivo de configuración no encontrado. Usando equipos por defecto.")
                if not self.equipos_a_monitorear:
                    self.equipos_a_monitorear = self._get_initial_equipment_seed()
                return

            equipos_guardados = data.get("equipos", [])
            if equipos_guardados:
                self.equipos_a_monitorear = equipos_guardados
                print(f"Configuración cargada: {len(self.equipos_a_monitorear)} equipos desde archivo.")

            self.cameras_config = data.get("cameras", [])
            telegram_settings = data.get("telegram", {})
            self.telegram_installation_name = telegram_settings.get("installation_name", "")
            self.telegram_notification_title = telegram_settings.get(
                "notification_title",
                "Notificacion enviada desde",
            )
            token = telegram_settings.get("token") or cfg.TELEGRAM_TOKEN_DEFAULT
            chat_id = telegram_settings.get("chat_id") or cfg.TELEGRAM_CHAT_ID_DEFAULT
            self.telegram_alerter.update_credentials(token, chat_id)
            camera_settings = data.get("camera_settings", {})
            self.camera_max_streams = max(int(camera_settings.get("max_streams", 1)), 1)
            self.camera_snapshot_interval = max(int(camera_settings.get("snapshot_interval", 2)), 1)
            self.verify_tls_certificates = bool(camera_settings.get("verify_tls_certificates", True))
            self.enable_external_geolocation = bool(camera_settings.get("enable_external_geolocation", False))
            self.verify_ssh_host_key = bool(camera_settings.get("verify_ssh_host_key", True))
            self.ssh_trust_on_first_use = bool(camera_settings.get("ssh_trust_on_first_use", False))

            self.ping_interval = data.get("intervalo_ping", 15)
            if self.ping_interval < 1: self.ping_interval = 1

            for equipo in self.equipos_a_monitorear:
                ts_str = equipo.get("disconnection_timestamp")
                if ts_str:
                    try: equipo["disconnection_timestamp"] = datetime.datetime.fromisoformat(ts_str)
                    except: equipo["disconnection_timestamp"] = None
                else: equipo["disconnection_timestamp"] = None
            print("Configuración inicial segura procesada.")
        except InvalidToken:
            print("[!] ADVERTENCIA: La clave de cifrado ha cambiado o el archivo de equipos está corrupto.")
            print("[!] Se cargarán los equipos por defecto.")
            try:
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                encrypted_path = self.secure_config._get_encrypted_path(config_path)
                backup_path = f"{encrypted_path}.corrupt.{ts}"
                os.rename(encrypted_path, backup_path)
                print(f"[i] Se ha guardado una copia del archivo de equipos inválido en: {backup_path}")
            except Exception as e:
                print(f"[!] No se pudo renombrar el archivo de equipos corrupto: {e}")
            self.equipos_a_monitorear = self._get_initial_equipment_seed()
        except Exception as e:
            print(f"Error al cargar la configuración inicial: {e}")

    def _get_initial_equipment_seed(self):
        if self.build_profile.preload_default_equipment:
            return [d.copy() for d in DEFAULT_EQUIPMENT]
        return []

    def create_monitors(self):
        print(f"Creando monitores para {len(self.equipos_a_monitorear)} equipos...")
        try:
            val = self.ping_interval_entry.get()
            if val:
                new_interval = int(val)
                if new_interval < 1:
                    new_interval = 1
                    self.ping_interval_entry.delete(0, "end")
                    self.ping_interval_entry.insert(0, str(new_interval))
                self.ping_interval = new_interval
        except (ValueError, AttributeError):
            pass

        for widget in self.monitor_frame.winfo_children():
            widget.destroy()

        if not self.equipos_a_monitorear:
            customtkinter.CTkLabel(
                self.monitor_frame,
                text="No hay equipos registrados en esta compilacion. Agregue equipos manualmente para comenzar a monitorear.",
                font=("Arial", 16, "bold"),
                text_color="#CCCCCC",
                wraplength=720,
                justify="center",
            ).pack(expand=True, pady=40)
            self.monitors = {}
            return

        self.monitors = {}
        row = 0
        col = 0

        # Calcular columnas basadas en el ancho (aproximación para responsividad)
        max_cols = 4

        for i in range(max_cols):
            self.monitor_frame.grid_columnconfigure(i, weight=1, pad=10)

        for equipo in self.equipos_a_monitorear:
            desconexiones = equipo.get("desconexiones_count", 0)
            mac_address = equipo.get("mac_address", "Buscando MAC...")
            disconnection_ts = equipo.get("disconnection_timestamp")

            monitor = IPMonitor(
                self.monitor_frame,
                equipo["ip"],
                equipo["label"],
                desconexiones_count=desconexiones,
                mac=mac_address,
                disconnection_timestamp=disconnection_ts,
            )
            monitor.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            self.monitors[equipo["ip"]] = monitor

            thread = threading.Thread(
                target=ping_ip,
                args=(equipo["ip"], monitor, self.ping_interval),
            )
            thread.start()

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def agregar_equipo(self):
        ip = self.ip_entry.get()
        etiqueta = self.etiqueta_entry.get()
        if ip and etiqueta:
            nuevo_equipo = {
                "ip": ip,
                "label": etiqueta,
                "desconexiones_count": 0,
                "mac_address": "Buscando MAC...",
                "disconnection_timestamp": None,
            }
            self.equipos_a_monitorear.append(nuevo_equipo)
            self.create_monitors()
            if hasattr(self, "cameras_tab_controller"):
                self.cameras_tab_controller._refresh_camera_list()
            self.ip_entry.delete(0, "end")
            self.etiqueta_entry.delete(0, "end")

    def remover_equipo(self):
        ip_a_remover = self.remove_entry.get()
        if ip_a_remover:
            nueva_lista = [
                equipo
                for equipo in self.equipos_a_monitorear
                if equipo["ip"] != ip_a_remover
            ]
            if len(nueva_lista) < len(self.equipos_a_monitorear):
                self.equipos_a_monitorear = nueva_lista
                self.create_monitors()
                self.remove_entry.delete(0, "end")

    def guardar_equipos(self):
        try:
            new_interval = int(self.ping_interval_entry.get())
            if new_interval < 1:
                new_interval = 1
            self.ping_interval = new_interval
            lista_para_guardar = []
            for equipo in self.equipos_a_monitorear:
                ip = equipo["ip"]
                equipo_a_guardar = equipo.copy()
                if ip in self.monitors:
                    monitor = self.monitors[ip]
                    equipo_a_guardar["desconexiones_count"] = (
                        monitor.desconexiones_count
                    )
                    equipo_a_guardar["mac_address"] = monitor.mac
                    if monitor.disconnection_timestamp:
                        equipo_a_guardar["disconnection_timestamp"] = (
                            monitor.disconnection_timestamp.isoformat()
                        )
                    else:
                        equipo_a_guardar["disconnection_timestamp"] = None
                lista_para_guardar.append(equipo_a_guardar)
            data_to_save = {
                "intervalo_ping": self.ping_interval,
                "equipos": lista_para_guardar,
                "cameras": getattr(self, "cameras_config", []),
                "telegram": {
                    "token": getattr(self.telegram_alerter, "token", ""),
                    "chat_id": getattr(self.telegram_alerter, "chat_id", ""),
                    "installation_name": getattr(self, "telegram_installation_name", ""),
                    "notification_title": getattr(
                        self,
                        "telegram_notification_title",
                        "Notificacion enviada desde",
                    ),
                },
                "camera_settings": {
                    "max_streams": getattr(self, "camera_max_streams", 1),
                    "snapshot_interval": getattr(self, "camera_snapshot_interval", 2),
                    "verify_tls_certificates": getattr(self, "verify_tls_certificates", True),
                    "enable_external_geolocation": getattr(self, "enable_external_geolocation", False),
                    "verify_ssh_host_key": getattr(self, "verify_ssh_host_key", True),
                    "ssh_trust_on_first_use": getattr(self, "ssh_trust_on_first_use", False),
                },
            }
            config_path = os.path.join(BASE_PATH, "equipos_guardados.json") # Path base
            self.secure_config.save(data_to_save, config_path)
            # Guardar también las métricas históricas y el registro diario
            if hasattr(self, "metricas"):
                self.metricas.guardar_en_disco()
                self.metricas.registrar_disponibilidad_diaria()
        except Exception as e:
            print(f"Error al guardar: {e}")

    def cargar_equipos(self):
        try:
            self.cargar_configuracion_inicial()
            self.ping_interval_entry.delete(0, "end")
            self.ping_interval_entry.insert(0, str(self.ping_interval))
            self.create_monitors()
            if hasattr(self, "cameras_tab_controller"):
                self.cameras_tab_controller._refresh_camera_list()
        except Exception as e:
            print(f"Error al cargar: {e}")

    def save_camera_runtime_settings(
        self,
        max_streams,
        snapshot_interval,
        verify_tls_certificates=None,
        enable_external_geolocation=None,
        verify_ssh_host_key=None,
        ssh_trust_on_first_use=None,
    ):
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
        self.guardar_equipos()
        if hasattr(self, "cameras_tab_controller"):
            self.cameras_tab_controller._refresh_stream_status()

    def try_acquire_camera_stream(self):
        if self.active_camera_streams >= self.camera_max_streams:
            return False
        self.active_camera_streams += 1
        return True

    def release_camera_stream(self):
        self.active_camera_streams = max(self.active_camera_streams - 1, 0)

    def generar_log_historial(self):
        log_filename = os.path.join(BASE_PATH, "historial_log.txt")
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_filename, "a") as file:
                file.write("=" * 60 + "\n")
                file.write(f"--- LOG DE ESTADO AUTOMÁTICO: {current_time_str} ---\n")
                for equipo in self.equipos_a_monitorear:
                    ip = equipo["ip"]
                    label = equipo["label"]
                    monitor = self.monitors.get(ip)
                    if monitor:
                        log_entry = f"[{current_time_str}] Equipo: {label} ({ip}) - Estado: {monitor.status} - MAC: {monitor.mac}"
                        if (
                            monitor.status == "Desconectado"
                            and monitor.disconnection_timestamp
                        ):
                            duration = (
                                datetime.datetime.now()
                                - monitor.disconnection_timestamp
                            )
                            log_entry += f" - Desconectado desde: {monitor.disconnection_timestamp.strftime('%H:%M:%S')}"
                        file.write(log_entry + "\n")
                file.write("-" * 60 + "\n\n")
        except Exception as e:
            print(f"Error al generar log: {e}")

    def iniciar_scheduler_log(self):
        def scheduler_thread():
            last_check_day = datetime.date.today()
            while True:
                now = datetime.datetime.now()
                current_date = now.date()
                current_time = now.time()
                if current_date > last_check_day:
                    self.log_executed_today = {
                        t.isoformat(): False for t in self.scheduler_times
                    }
                    last_check_day = current_date
                for scheduled_time in self.scheduler_times:
                    time_key = scheduled_time.isoformat()
                    is_time_to_run = (
                        (current_time >= scheduled_time)
                        and (current_time.hour == scheduled_time.hour)
                        and (current_time.minute == scheduled_time.minute)
                    )
                    if is_time_to_run and not self.log_executed_today[time_key]:
                        self.generar_log_historial()
                        if hasattr(self, "metricas"):
                            self.metricas.registrar_disponibilidad_diaria()
                        self.log_executed_today[time_key] = True
                time.sleep(30)

        threading.Thread(target=scheduler_thread, daemon=True).start()

    def generar_reporte(self):
        if not REPORTLAB_AVAILABLE:
            ToastNotification(
                self,
                "Error",
                "Libreria PDF no encontrada. Reinstale la aplicacion.",
                color="red",
            )
            return

        filename_only = f"{REPORT_FILE_PREFIX}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        filename = os.path.join(BASE_PATH, filename_only)

        try:
            build_network_report(
                ReportContext(
                    filename=filename,
                    app_name=APP_NAME,
                    version=VERSION,
                    tagline=APP_TAGLINE,
                    logo_path=os.path.join(ASSETS_PATH, "img", LOGO_FILE),
                    generated_by=self.current_user["full_name"],
                    equipos=self.equipos_a_monitorear,
                    monitors=self.monitors,
                    metricas=getattr(self, "metricas", None),
                    tls_strict=bool(getattr(self, "verify_tls_certificates", False)),
                    cameras_count=len(getattr(self, "cameras_config", [])),
                    camera_max_streams=int(getattr(self, "camera_max_streams", 1)),
                )
            )
            ToastNotification(
                self,
                "Reporte PDF",
                f"Generado exitosamente:\n{filename}",
                color="green",
            )

            if platform.system() == "Windows":
                os.startfile(filename)

        except Exception as e:
            print(f"Error PDF: {e}")
            ToastNotification(
                self, "Error PDF", f"No se pudo generar el reporte: {e}", color="red"
            )

    def inicializar_historial(self):
        self.metricas = MetricasHistoricas()
        titulo = customtkinter.CTkLabel(
            self.historial_frame,
            text="📊 Historial y Análisis de Equipos",
            font=("Arial", 20, "bold"),
        )
        titulo.pack(pady=(10, 20))
        self.graficos_frame = customtkinter.CTkFrame(
            self.historial_frame, fg_color="transparent"
        )
        self.graficos_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_latencia = customtkinter.CTkFrame(
            self.graficos_frame, fg_color="#2B2B2B"
        )
        self.frame_latencia.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(
            self.frame_latencia,
            text="📈 Latencia - Últimas 24 Horas",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)

        # Ajustar tamaño de figura para ser más responsiva
        self.fig_latencia = Figure(figsize=(8, 3), facecolor="#2B2B2B", dpi=100)
        self.ax_latencia = self.fig_latencia.add_subplot(111)
        self.ax_latencia.set_facecolor("#2B2B2B")
        self.ax_latencia.tick_params(colors="white", labelsize=8)
        self.fig_latencia.tight_layout()

        self.canvas_latencia = FigureCanvasTkAgg(self.fig_latencia, self.frame_latencia)
        self.canvas_latencia.get_tk_widget().pack(
            fill="both", expand=True, padx=5, pady=5
        )

        self.frame_gauges = customtkinter.CTkFrame(
            self.graficos_frame, fg_color="transparent"
        )
        self.frame_gauges.pack(fill="x", pady=5)
        customtkinter.CTkLabel(
            self.frame_gauges,
            text="🎯 Disponibilidad - Últimas 24 Horas",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)

        self.gauges_container = customtkinter.CTkFrame(
            self.frame_gauges, fg_color="transparent"
        )
        self.gauges_container.pack(fill="x", expand=True)

        # Mejora 1.5: Heatmap de Disponibilidad
        self.frame_heatmap = customtkinter.CTkFrame(
            self.graficos_frame, fg_color="#2B2B2B"
        )
        self.frame_heatmap.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(
            self.frame_heatmap,
            text="🗓️ Mapa de Calor - Disponibilidad (24h)",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)

        self.fig_heatmap = Figure(figsize=(8, 2.5), facecolor="#2B2B2B", dpi=100)
        self.ax_heatmap = self.fig_heatmap.add_subplot(111)
        self.ax_heatmap.set_facecolor("#2B2B2B")
        self.fig_heatmap.subplots_adjust(left=0.25, bottom=0.2)
        self.fig_heatmap.tight_layout()

        self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, self.frame_heatmap)
        self.canvas_heatmap.get_tk_widget().pack(
            fill="both", expand=True, padx=5, pady=5
        )

        self.frame_tabla = customtkinter.CTkFrame(
            self.graficos_frame, fg_color="#2B2B2B"
        )
        self.frame_tabla.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(
            self.frame_tabla,
            text="📋 Estado Actual de Equipos",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)
        self.tabla_eventos = customtkinter.CTkTextbox(
            self.frame_tabla, height=150, font=("Courier New", 11)
        )
        self.tabla_eventos.pack(fill="both", expand=True, padx=10, pady=10)

        self.btn_actualizar = customtkinter.CTkButton(
            self.historial_frame,
            text="🔄 Actualizar Gráficos",
            command=self.actualizar_graficos,
        )
        self.btn_actualizar.pack(pady=10)

        # Primera actualización de gráficos diferida
        self.after(500, self.actualizar_graficos)

    def actualizar_graficos(self):
        # --- BLINDAJE ANTI-CRASH ---
        # Si la ventana o los widgets de historial ya no existen, detener la ejecución.
        try:
            if not self.winfo_exists() or not self.historial_frame.winfo_exists():
                return
        except Exception:
            return

        self.ax_latencia.clear()
        self.ax_latencia.set_facecolor("#2B2B2B")
        self.ax_latencia.grid(True, alpha=0.2, color="#555")
        self.ax_latencia.tick_params(colors="white", labelsize=8)
        colores = ["#00d9ff", "#ff6b6b", "#51cf66", "#ffd43b", "#ff6b9d", "#9775fa"]
        for i, equipo in enumerate(self.equipos_a_monitorear):
            ip = equipo["ip"]
            datos = self.metricas.obtener_datos(ip, periodo_horas=24)
            if datos and len(datos["timestamps"]) > 0:
                latencias = datos["latencias"]
                paso = max(1, len(latencias) // 40)
                indices = range(0, len(latencias), paso)
                # Reemplazar None con 0 para evitar crasheos (TypeError)
                y_values = [latencias[j] if latencias[j] is not None else 0 for j in indices]
                self.ax_latencia.plot(
                    [k for k in range(len(indices))],
                    y_values,
                    label=equipo["label"],
                    color=colores[i % len(colores)],
                    linewidth=2,
                )

        # Validación de leyenda para evitar UserWarning
        handles, labels = self.ax_latencia.get_legend_handles_labels()
        if labels:
            self.ax_latencia.legend(
                facecolor="#3B3B3B", edgecolor="#555", labelcolor="white", fontsize=8
            )

        self.canvas_latencia.draw()

        # Mejora 1.5: Lógica del Heatmap
        self.ax_heatmap.clear()
        self.ax_heatmap.set_facecolor("#2B2B2B")

        heatmap_data = []
        labels_heatmap = []
        for equipo in self.equipos_a_monitorear:
            ip = equipo["ip"]
            labels_heatmap.append(equipo["label"][:20])  # Más caracteres para etiquetas
            datos = self.metricas.obtener_datos(ip, periodo_horas=24)
            if datos and datos["estados"]:
                bloques = np.array_split(datos["estados"], 24)
                dispo_bloques = []
                for b in bloques:
                    if len(b) > 0:
                        online_count = sum(
                            1 for s in b if s == 1
                        )  # Corregido: s es int (1 o 0)
                        dispo_bloques.append(online_count / len(b))
                    else:
                        dispo_bloques.append(0)
                heatmap_data.append(dispo_bloques)
            else:
                heatmap_data.append([0] * 24)

        if heatmap_data:
            im = self.ax_heatmap.imshow(
                heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1
            )
            self.ax_heatmap.set_yticks(range(len(labels_heatmap)))
            self.ax_heatmap.set_yticklabels(labels_heatmap, color="white", fontsize=8)
            self.ax_heatmap.set_xticks(range(0, 24, 2))
            self.ax_heatmap.set_xticklabels(
                [f"{h}h" for h in range(0, 24, 2)], color="white", fontsize=8
            )
            self.ax_heatmap.tick_params(axis="both", which="both", length=0)

        self.canvas_heatmap.draw()

        for widget in self.gauges_container.winfo_children():
            widget.destroy()

        # Configurar grid para gauges (máximo 5 por fila)
        for i in range(5):
            self.gauges_container.grid_columnconfigure(i, weight=1)

        for i, equipo in enumerate(self.equipos_a_monitorear):
            uptime = self.metricas.calcular_uptime(equipo["ip"])

            row = i // 5
            col = i % 5

            g_frame = customtkinter.CTkFrame(self.gauges_container, fg_color="#2B2B2B")
            g_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            color = (
                "#51cf66" if uptime >= 99 else "#ffd43b" if uptime >= 95 else "#ff6b6b"
            )

            # Dibujar Semicírculo (Gauge)
            canvas_w, canvas_h = 120, 70
            canvas = tk.Canvas(
                g_frame,
                width=canvas_w,
                height=canvas_h,
                bg="#2B2B2B",
                highlightthickness=0,
            )
            canvas.pack(pady=2)

            # Fondo del arco (gris)
            canvas.create_arc(
                10,
                10,
                110,
                110,
                start=0,
                extent=180,
                outline="#444",
                width=8,
                style="arc",
            )
            # Arco de progreso
            extent = (uptime / 100) * 180
            canvas.create_arc(
                10,
                10,
                110,
                110,
                start=180,
                extent=-extent,
                outline=color,
                width=8,
                style="arc",
            )

            # Texto de porcentaje al centro
            canvas.create_text(
                60, 55, text=f"{uptime:.1f}%", fill="white", font=("Arial", 14, "bold")
            )

            customtkinter.CTkLabel(
                g_frame,
                text=equipo["label"][:15],
                font=("Arial", 10, "bold"),
                text_color="#AAA",
            ).pack(pady=(0, 5))

        # Mejora 1.6: Tabla de Eventos Pro
        self.tabla_eventos.delete("0.0", "end")
        header = f"┌{'─' * 25}┬{'─' * 12}┬{'─' * 12}┬{'─' * 10}┐\n"
        header += (
            f"│ {'Equipo':<23} │ {'Estado':<10} │ {'Latencia':<10} │ {'Hora':<8} │\n"
        )
        header += f"├{'─' * 25}┼{'─' * 12}┼{'─' * 12}┼{'─' * 10}┤\n"
        self.tabla_eventos.insert("end", header)

        for ip, monitor in self.monitors.items():
            datos = self.metricas.obtener_datos(ip, periodo_horas=1)
            lat = (
                f"{datos['latencias'][-1]:.1f}ms"
                if datos and datos["latencias"]
                else "---"
            )
            hora = datetime.datetime.now().strftime("%H:%M:%S")
            status_icon = "🟢" if monitor.status == "Conectado" else "🔴"

            row = f"│ {status_icon} {monitor.label[:20]:<20} │ {monitor.status:<10} │ {lat:<10} │ {hora:<8} │\n"
            self.tabla_eventos.insert("end", row)

        footer = f"└{'─' * 25}┴{'─' * 12}┴{'─' * 12}┴{'─' * 10}┘"
        self.tabla_eventos.insert("end", footer)

        self.after(60000, self.actualizar_graficos)


if __name__ == "__main__":
    # IPs de ejemplo por si se ejecuta monitor.py directamente
    ips_ejemplo = [
        {"ip": "8.8.8.8", "label": "Google Primario"},
        {"ip": "1.1.1.1", "label": "Cloudflare"},
    ]
    app = App(ips_ejemplo)
    app.mainloop()
