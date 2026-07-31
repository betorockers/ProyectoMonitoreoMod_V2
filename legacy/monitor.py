# monitor.py

import customtkinter
import tkinter as tk
import threading
from ping_logic import ping_ip
import time
from tkinter import messagebox
import platform
import json
import pygame
import datetime
import os
import matplotlib
import sys
import io

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from metrics_manager import MetricasHistoricas
import numpy as np
from PIL import Image, ImageTk
from auth_manager import AuthManager
from telegram_alerter import TelegramAlerter
import branding
from backup_manager import BackupManager
from network_tools_logic import NetworkTools

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


def apply_window_icon(window, set_as_default=False):
    """Aplica el icono oficial de Argos Guard a cualquier ventana."""
    try:
        # Rutas de iconos
        icon_path_ico = os.path.join(ASSETS_PATH, "img", "icono_argos.ico")
        icon_path_png = os.path.join(ASSETS_PATH, "img", "icono_argos.png")

        icon_loaded = False

        # 1. Intentar .ico en Windows
        if platform.system() == "Windows" and os.path.exists(icon_path_ico):
            try:
                window.iconbitmap(icon_path_ico)
                icon_loaded = True
            except Exception:
                pass  # Si falla el .ico (ej: formato inválido), intentar con PNG

        # 2. Fallback: .png (funciona en Windows también con wm_iconphoto)
        if not icon_loaded and os.path.exists(icon_path_png):
            img = Image.open(icon_path_png)
            photo = ImageTk.PhotoImage(img)
            window.wm_iconphoto(set_as_default, photo)
            window._icon_photo = photo  # Mantener referencia
    except Exception:
        pass  # Silenciar errores para evitar diálogos en producción


class ToastNotification(customtkinter.CTkToplevel):
    def __init__(self, master, title, message, color="green", duration=5000):
        super().__init__(master)
        self.after(200, lambda: apply_window_icon(self))

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
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.auth = master.auth

        self.title("Argos Guard - Inicio de Sesión")
        self.geometry("480x700")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Centrar ventana en pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 480) // 2
        y = (screen_height - 700) // 2
        self.geometry(f"480x700+{x}+{y}")

        # Configurar icono de la ventana
        self.after(200, lambda: apply_window_icon(self))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        # Logo o Título
        try:
            logo_path = os.path.join(ASSETS_PATH, "img", "logoargosguard.png")
            pil_image = Image.open(logo_path)
            self.logo_image = customtkinter.CTkImage(
                light_image=pil_image, dark_image=pil_image, size=(300, 300)
            )
            self.logo_label = customtkinter.CTkLabel(
                self, image=self.logo_image, text=""
            )
            self.logo_label.pack(pady=(40, 10))
        except:
            self.title_label = customtkinter.CTkLabel(
                self,
                text="🛡️ ARGOS GUARD",
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
        self.master.destroy()

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
    def __init__(self, master, on_setup_success):
        super().__init__(master)
        self.on_setup_success = on_setup_success
        self.auth = master.auth

        self.title("Argos Guard - Configuración Inicial")
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
        ).pack(pady=(40, 10))

        customtkinter.CTkLabel(
            self,
            text="Bienvenido a Argos Guard.\nCree su cuenta de Administrador Maestro.",
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
        self.master.destroy()

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


class TelegramConfigWindow(customtkinter.CTkToplevel):
    def __init__(self, master, current_token, current_chat_id, on_save):
        super().__init__(master)
        self.on_save = on_save
        self.title("Configuración Telegram")
        self.geometry("400x350")
        self.resizable(False, False)

        # Centrar
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 350) // 2
        self.geometry(f"400x350+{x}+{y}")

        self.after(200, lambda: apply_window_icon(self))

        customtkinter.CTkLabel(
            self, text="🤖 Configuración de Alertas", font=("Arial", 16, "bold")
        ).pack(pady=20)

        self.token_entry = customtkinter.CTkEntry(
            self, placeholder_text="Bot Token", width=300
        )
        self.token_entry.pack(pady=10)
        if current_token:
            self.token_entry.insert(0, current_token)

        self.chat_id_entry = customtkinter.CTkEntry(
            self, placeholder_text="Chat ID", width=300
        )
        self.chat_id_entry.pack(pady=10)
        if current_chat_id:
            self.chat_id_entry.insert(0, current_chat_id)

        customtkinter.CTkLabel(
            self,
            text="Para obtener estos datos, crea un bot con @BotFather\ny obtén tu ID con @userinfobot",
            font=("Arial", 10),
            text_color="gray",
        ).pack(pady=5)

        self.btn_save = customtkinter.CTkButton(
            self,
            text="Guardar y Probar",
            command=self.save_config,
            fg_color="#00d9ff",
            text_color="black",
        )
        self.btn_save.pack(pady=20)

        self.btn_disable = customtkinter.CTkButton(
            self,
            text="Desactivar Alertas",
            command=self.disable_alerts,
            fg_color="#ff6b6b",
        )
        self.btn_disable.pack(pady=5)

    def save_config(self):
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()

        if not token or not chat_id:
            ToastNotification(
                self.master, "Error", "Token y Chat ID son requeridos", color="red"
            )
            return

        self.on_save(token, chat_id)
        ToastNotification(
            self.master,
            "Guardado",
            "Configuración actualizada. Enviando prueba...",
            color="green",
        )
        self.destroy()

    def disable_alerts(self):
        self.on_save("", "")
        ToastNotification(
            self.master,
            "Desactivado",
            "Alertas de Telegram desactivadas",
            color="yellow",
        )
        self.destroy()


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

        # Campo para rastrear la fecha y hora exacta de la desconexión
        self.disconnection_timestamp = disconnection_timestamp

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
        try:
            if self.winfo_exists():
                self.after(0, self._update_status_ui, new_status, mac_address, latencia)
        except:
            pass

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
                self.send_alert(
                    f"¡Alerta! {self.label} está desconectado.", "red", "alerta.mp3"
                )
                self.desconexiones_count += 1
            elif self.status == "Conectado":
                self.disconnection_timestamp = None
                self.send_alert(
                    f"¡Recuperado! {self.label} está en línea de nuevo.",
                    "green",
                    "recuperado.mp3",
                )

            # --- Alerta Telegram ---
            try:
                app = self.master
                while not isinstance(app, customtkinter.CTk) and app.master is not None:
                    app = app.master

                if (
                    hasattr(app, "telegram_alerter")
                    and app.telegram_alerter
                    and app.telegram_alerter.enabled
                ):
                    # Restricción de horario: 9 AM a 5 PM (17:00)
                    current_hour = datetime.datetime.now().hour
                    if 9 <= current_hour < 17:
                        if self.status == "Desconectado":
                            msg = f"🚨 *ALERTA - {branding.APP_NAME}*\n\n📍 *Equipo:* {self.label}\n🌐 *IP:* {self.ip}\n⏰ *Hora:* {datetime.datetime.now().strftime('%H:%M:%S')}\n❌ *Estado:* DESCONECTADO"
                            app.telegram_alerter.send_alert(msg)
                        elif self.status == "Conectado":
                            msg = f"✅ *RECUPERADO - {branding.APP_NAME}*\n\n📍 *Equipo:* {self.label}\n🌐 *IP:* {self.ip}\n⏰ *Hora:* {datetime.datetime.now().strftime('%H:%M:%S')}\n🟢 *Estado:* CONECTADO"
                            app.telegram_alerter.send_alert(msg)
                    else:
                        print(
                            "Alerta Telegram omitida: Fuera de horario laboral (09:00 - 17:00)"
                        )
            except Exception as e:
                print(f"Error enviando telegram: {e}")

    def send_alert(self, message, color, sound_file):
        # Notificación personalizada tipo Toast
        try:
            app = self.master
            while not isinstance(app, customtkinter.CTk) and app.master is not None:
                app = app.master

            title = "Argos Guard: Cambio de Estado"
            ToastNotification(app, title, message, color=color)
        except Exception as e:
            print(f"Error al mostrar Toast: {e}")

        try:
            sound_path = get_resource_path(os.path.join("assets", sound_file))
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._last_sound = pygame.mixer.Sound(sound_path)
            self._last_sound.play()
        except Exception as e:
            print(f"Error al reproducir el sonido: {e}")
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
        self.after(200, lambda: apply_window_icon(self, set_as_default=True))

        self.withdraw()  # Iniciar oculto
        self.equipos_a_monitorear = equipos_a_monitorear
        self.current_user = None
        self.auth = AuthManager()
        self.services_started = False

        # Inicializar Alerter con defaults de branding
        self.telegram_alerter = TelegramAlerter(
            branding.TELEGRAM_TOKEN_DEFAULT, branding.TELEGRAM_CHAT_ID_DEFAULT
        )

        # Inicializar Gestor de Backups
        self.backup_manager = BackupManager()

        try:
            # Inicialización explícita para mayor compatibilidad
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            print(f"Error al inicializar el mezclador de Pygame: {e}")

        self.show_login()

    def show_login(self):
        # Limpiar ventana principal y ocultarla
        for widget in self.winfo_children():
            widget.destroy()
        self.withdraw()

        # Si no hay usuarios registrados, mostrar Setup
        if not self.auth.users:
            self.setup_window = SetupWindow(self, self.on_login_success)
            self.setup_window.attributes("-topmost", True)
        else:
            self.login_window = LoginWindow(self, self.on_login_success)
            self.login_window.attributes("-topmost", True)

    def on_login_success(self, user_data):
        self.current_user = user_data
        self.deiconify()  # Mostrar ventana principal
        self.after(200, lambda: apply_window_icon(self, set_as_default=True))
        self.setup_main_ui()

    def setup_main_ui(self):
        # Título personalizado solicitado por el usuario
        self.title(
            f"{branding.APP_NAME} v{branding.VERSION} | Usuario: {self.current_user['full_name']} ({self.current_user['role']}) | {branding.POWERED_BY}"
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.ping_interval = 15

        # Horarios de tareas automáticas (Logs y Backups)
        self.scheduler_times = [
            datetime.time(11, 0, 0),
            datetime.time(14, 30, 0),
            datetime.time(16, 55, 0),
        ]
        self.log_executed_today = {t.isoformat(): False for t in self.scheduler_times}

        # Cargar configuración pero NO sobrescribir si ya tenemos equipos de main.py
        self.cargar_configuracion_inicial()

        # Crear sistema de pestañas
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.tab_monitoreo = self.tabview.add("Monitoreo Activo")
        self.tab_historial = self.tabview.add("Historial de Eventos")

        if self.current_user["role"] in ["super_admin", "admin"]:
            self.tab_usuarios = self.tabview.add("Gestión de Usuarios")
            self.setup_user_management_tab()

            # --- FASE 1: Pestaña de Diagnóstico ---
            self.tab_diagnostico = self.tabview.add("Diagnóstico")
            self.setup_diagnostics_tab()

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

        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        self.footer_frame.grid_columnconfigure(2, weight=1)

        self.clock_label = customtkinter.CTkLabel(
            self.footer_frame, text="", font=("Arial", 12, "bold"), text_color="#00d9ff"
        )
        self.clock_label.grid(row=0, column=0, padx=20, pady=2, sticky="w")

        leyenda_label = customtkinter.CTkLabel(
            self.footer_frame,
            text="Argos Guard: El pulso de tu red bajo nuestra mirada.",
            font=("Arial", 12, "bold"),
            text_color="#FFFFFF",
        )
        leyenda_label.grid(row=0, column=1, padx=10, pady=2, sticky="ew")

        nombre_label = customtkinter.CTkLabel(
            self.footer_frame,
            text="Desarrollado por Omar Toledo",
            font=("Arial", 12, "italic"),
            text_color="#999999",
        )
        nombre_label.grid(row=0, column=2, padx=10, pady=2, sticky="e")

        # Iniciar reloj
        self.update_clock()

        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=1, rowspan=3, sticky="nsew")

        # Mejora de Logo 75x75 (Ajuste de espacio solicitado por el usuario)
        try:
            logo_path = os.path.join(ASSETS_PATH, "img", "logoargosguard.png")
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
            self.sidebar_frame, text="Dirección IP:", font=("Arial", 12)
        )
        self.ip_label.grid(row=4, column=0, padx=10, pady=(5, 0), sticky="w")
        self.ip_entry = customtkinter.CTkEntry(
            self.sidebar_frame, placeholder_text="ej. 192.168.1.1"
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

        self.backup_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Crear Backup DB",
            command=self.realizar_backup_manual,
            fg_color="#e67e22",
        )
        self.backup_button.grid(row=15, column=0, padx=10, pady=5)

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

        self.telegram_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Configurar Telegram",
            command=self.open_telegram_config,
            fg_color="#3B8ED0",
        )
        self.telegram_button.grid(row=15, column=0, padx=10, pady=5)

        self.logout_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Cerrar Sesión",
            command=self.show_login,
            fg_color="#ff6b6b",
            hover_color="#fa5252",
        )
        self.logout_button.grid(row=15, column=0, padx=10, pady=10)
        self.logout_button.grid(row=16, column=0, padx=10, pady=10)

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
            self.telegram_button.configure(state="disabled")
            self.backup_button.configure(state="disabled")

        self.monitors = {}
        # Prioridad 1: Crear tarjetas e iniciar pings de inmediato
        self.create_monitors()

        # Prioridad 2: Iniciar servicios de fondo (solo una vez)
        if not self.services_started:
            self.iniciar_scheduler_log()
            self.services_started = True

        # Prioridad 3: Cargar historial y gráficos con un ligero retraso para no bloquear la UI inicial
        self.after(500, self.inicializar_historial)

    # --- INICIO: Métodos para Pestaña de Diagnóstico ---
    # Estos métodos corresponden a las Fases 1 y 2 del plan de trabajo.

    def setup_diagnostics_tab(self):
        """Configura la pestaña de Herramientas de Diagnóstico (Fase 1)"""
        # Layout de 2 columnas
        self.tab_diagnostico.grid_columnconfigure(0, weight=1)
        self.tab_diagnostico.grid_columnconfigure(1, weight=1)
        self.tab_diagnostico.grid_rowconfigure(0, weight=0)  # Fila fija
        self.tab_diagnostico.grid_rowconfigure(1, weight=1)
        self.tab_diagnostico.grid_rowconfigure(2, weight=1)

        # --- MÓDULO A: Información Local ---
        self.frame_info_local = customtkinter.CTkFrame(
            self.tab_diagnostico, corner_radius=10
        )
        self.frame_info_local.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        customtkinter.CTkLabel(
            self.frame_info_local,
            text="💻 Información del Sistema Local",
            font=("Arial", 16, "bold"),
            text_color="#00d9ff",
        ).pack(pady=(15, 10))

        # Contenedor de datos
        self.info_container = customtkinter.CTkFrame(
            self.frame_info_local, fg_color="transparent"
        )
        self.info_container.pack(fill="both", expand=True, padx=15)

        # Variables para actualizar etiquetas
        self.lbl_hostname = customtkinter.CTkLabel(
            self.info_container, text="Host: Cargando...", anchor="w"
        )
        self.lbl_hostname.pack(fill="x", pady=2)

        self.lbl_ip = customtkinter.CTkLabel(
            self.info_container,
            text="IP: Cargando...",
            anchor="w",
            font=("Arial", 12, "bold"),
        )
        self.lbl_ip.pack(fill="x", pady=2)

        self.lbl_mac = customtkinter.CTkLabel(
            self.info_container, text="MAC: Cargando...", anchor="w"
        )
        self.lbl_mac.pack(fill="x", pady=2)

        self.lbl_gateway = customtkinter.CTkLabel(
            self.info_container, text="Gateway: Cargando...", anchor="w"
        )
        self.lbl_gateway.pack(fill="x", pady=2)

        self.lbl_dns = customtkinter.CTkLabel(
            self.info_container, text="DNS: Cargando...", anchor="w"
        )
        self.lbl_dns.pack(fill="x", pady=2)

        customtkinter.CTkButton(
            self.frame_info_local,
            text="🔄 Actualizar Info",
            command=self.refresh_local_info,
            height=30,
        ).pack(pady=15)

        # --- MÓDULO B: Herramientas de Reparación ---
        self.frame_tools = customtkinter.CTkFrame(
            self.tab_diagnostico, corner_radius=10
        )
        self.frame_tools.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        customtkinter.CTkLabel(
            self.frame_tools,
            text="🛠️ Herramientas de Reparación",
            font=("Arial", 16, "bold"),
            text_color="#ff9f1c",
        ).pack(pady=(15, 10))

        customtkinter.CTkLabel(
            self.frame_tools,
            text="Acciones rápidas para solucionar problemas de red.\nÚselas con precaución.",
            font=("Arial", 11),
            text_color="gray",
        ).pack(pady=(0, 15))

        # Botones de acción
        btn_flush = customtkinter.CTkButton(
            self.frame_tools,
            text="🧹 Limpiar Caché DNS (Flush)",
            command=lambda: self.run_maintenance_tool("flushdns"),
            fg_color="#2B2B2B",
            border_width=1,
            border_color="#555",
            hover_color="#333",
        )
        btn_flush.pack(fill="x", padx=20, pady=8)

        btn_renew = customtkinter.CTkButton(
            self.frame_tools,
            text="🔄 Renovar Dirección IP",
            command=lambda: self.run_maintenance_tool("renew"),
            fg_color="#2B2B2B",
            border_width=1,
            border_color="#555",
            hover_color="#333",
        )
        btn_renew.pack(fill="x", padx=20, pady=8)

        btn_release = customtkinter.CTkButton(
            self.frame_tools,
            text="⚠️ Liberar IP (Desconectar)",
            command=lambda: self.run_maintenance_tool("release"),
            fg_color="#3a1c1c",
            border_width=1,
            border_color="#ff6b6b",
            hover_color="#5c2b2b",
            text_color="#ff6b6b",
        )
        btn_release.pack(fill="x", padx=20, pady=8)

        # Cargar info inicial
        self.after(1000, self.refresh_local_info)

        # --- MÓDULO C: Diagnóstico Remoto ---
        self.frame_remote_diag = customtkinter.CTkFrame(
            self.tab_diagnostico, corner_radius=10
        )
        self.frame_remote_diag.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew"
        )
        self.frame_remote_diag.grid_columnconfigure(0, weight=1)
        self.frame_remote_diag.grid_rowconfigure(2, weight=1)

        customtkinter.CTkLabel(
            self.frame_remote_diag,
            text="🔎 Diagnóstico Remoto",
            font=("Arial", 16, "bold"),
            text_color="#51cf66",
        ).grid(row=0, column=0, pady=(15, 10))

        # Input y botones
        controls_frame = customtkinter.CTkFrame(
            self.frame_remote_diag, fg_color="transparent"
        )
        controls_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew", columnspan=1)
        controls_frame.grid_columnconfigure(0, weight=1)

        self.diag_target_entry = customtkinter.CTkEntry(
            controls_frame, placeholder_text="IP o Dominio (ej: 8.8.8.8 o google.com)"
        )
        self.diag_target_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_controls_frame = customtkinter.CTkFrame(
            controls_frame, fg_color="transparent"
        )
        btn_controls_frame.grid(row=0, column=1)

        self.btn_ping = customtkinter.CTkButton(
            btn_controls_frame,
            text="Ping",
            width=80,
            command=lambda: self.run_diagnostic_tool("ping"),
        )
        self.btn_ping.pack(side="left", padx=5)

        self.btn_tracert = customtkinter.CTkButton(
            btn_controls_frame,
            text="Tracert",
            width=80,
            command=lambda: self.run_diagnostic_tool("tracert"),
        )
        self.btn_tracert.pack(side="left", padx=5)

        self.btn_nslookup = customtkinter.CTkButton(
            btn_controls_frame,
            text="NSLookup",
            width=80,
            command=lambda: self.run_diagnostic_tool("nslookup"),
        )
        self.btn_nslookup.pack(side="left", padx=5)

        self.btn_stop_diag = customtkinter.CTkButton(
            btn_controls_frame,
            text="Detener",
            width=80,
            fg_color="#ff6b6b",
            command=self.stop_diagnostic_tool,
            state="disabled",
        )
        self.btn_stop_diag.pack(side="left", padx=5)

        # Consola de salida
        self.diag_console = customtkinter.CTkTextbox(
            self.frame_remote_diag, font=("Courier New", 12), wrap="none"
        )
        self.diag_console.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        self.diag_console.configure(state="disabled")

        self.active_diag_process = None

        # --- MÓDULO D: Auditoría Avanzada ---
        self.frame_audit = customtkinter.CTkFrame(
            self.tab_diagnostico, corner_radius=10
        )
        self.frame_audit.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_audit.grid_rowconfigure(1, weight=1)
        self.frame_audit.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            self.frame_audit,
            text="🔬 Auditoría Avanzada",
            font=("Arial", 16, "bold"),
            text_color="#a5d8ff",
        ).grid(row=0, column=0, pady=(15, 10))

        self.audit_tabs = customtkinter.CTkTabview(self.frame_audit, fg_color="#2B2B2B")
        self.audit_tabs.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_arp = self.audit_tabs.add("Tabla ARP")
        self.tab_netstat = self.audit_tabs.add("Netstat")

        # Contenido Tab ARP
        self.tab_arp.grid_columnconfigure(0, weight=1)
        self.tab_arp.grid_rowconfigure(1, weight=1)
        customtkinter.CTkButton(
            self.tab_arp, text="Mostrar Tabla ARP Local", command=self.display_arp_table
        ).grid(row=0, column=0, pady=10)
        self.arp_console = customtkinter.CTkTextbox(
            self.tab_arp, font=("Courier New", 11), wrap="none", state="disabled"
        )
        self.arp_console.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Contenido Tab Netstat
        self.tab_netstat.grid_columnconfigure(0, weight=1)
        self.tab_netstat.grid_rowconfigure(1, weight=1)
        netstat_controls = customtkinter.CTkFrame(
            self.tab_netstat, fg_color="transparent"
        )
        netstat_controls.grid(row=0, column=0, pady=5, sticky="ew")
        customtkinter.CTkButton(
            netstat_controls,
            text="Mostrar Conexiones Activas",
            command=self.display_netstat,
        ).pack(side="left", padx=10)
        self.netstat_filter_entry = customtkinter.CTkEntry(
            netstat_controls, placeholder_text="Filtrar por IP, puerto o estado..."
        )
        self.netstat_filter_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.netstat_console = customtkinter.CTkTextbox(
            self.tab_netstat, font=("Courier New", 11), wrap="none", state="disabled"
        )
        self.netstat_console.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # --- MÓDULO E: Gestión de Servicios ---
        self.frame_services = customtkinter.CTkFrame(
            self.tab_diagnostico, corner_radius=10
        )
        self.frame_services.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.frame_services.grid_rowconfigure(1, weight=1)
        self.frame_services.grid_columnconfigure(0, weight=1)

        service_header = customtkinter.CTkFrame(
            self.frame_services, fg_color="transparent"
        )
        service_header.grid(row=0, column=0, sticky="ew", pady=(15, 10), padx=10)
        customtkinter.CTkLabel(
            service_header,
            text="⚙️ Gestor de Servicios (Whitelist)",
            font=("Arial", 16, "bold"),
            text_color="#fcc419",
        ).pack(side="left")
        customtkinter.CTkButton(
            service_header,
            text="🔄",
            width=30,
            command=self.refresh_all_services_status,
        ).pack(side="right")

        self.services_container = customtkinter.CTkScrollableFrame(
            self.frame_services, label_text="Servicios Permitidos"
        )
        self.services_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.service_widgets = {}
        self.load_service_manager()

    def refresh_local_info(self):
        """Actualiza la tarjeta de información local en un hilo separado"""

        def _fetch():
            info = NetworkTools.get_local_info()
            self.after(0, lambda: self._update_info_labels(info))

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_info_labels(self, info):
        self.lbl_hostname.configure(text=f"🖥️ Hostname:  {info['hostname']}")
        self.lbl_ip.configure(text=f"🌐 IP Local:    {info['ip']}")
        self.lbl_mac.configure(text=f"🆔 MAC Addr:    {info['mac']}")
        self.lbl_gateway.configure(text=f"🚪 Gateway:     {info['gateway']}")
        dns_str = ", ".join(info["dns"]) if info["dns"] else "No detectado"
        self.lbl_dns.configure(text=f"🌍 DNS:         {dns_str}")

    def run_maintenance_tool(self, tool_type):
        """Ejecuta herramientas de mantenimiento con confirmación y feedback"""

        # 1. Confirmación de Seguridad (UX Pattern)
        msgs = {
            "flushdns": "¿Desea limpiar la caché de resolución de nombres (DNS)?",
            "renew": "Esto desconectará momentáneamente la red mientras se negocia una nueva IP.\n¿Continuar?",
            "release": "⚠️ ADVERTENCIA: Esto dejará al equipo SIN CONEXIÓN a la red.\n¿Está seguro?",
        }

        if not messagebox.askyesno(
            "Confirmar Acción", msgs.get(tool_type, "¿Ejecutar?")
        ):
            return

        # 2. Ejecución en Hilo (Para no congelar UI)
        ToastNotification(
            self,
            "Ejecutando...",
            "Por favor espere mientras se aplica la configuración.",
            color="blue",
        )

        def _run():
            success, output = NetworkTools.execute_maintenance(tool_type)
            self.after(
                0, lambda: self._on_maintenance_complete(success, output, tool_type)
            )

        threading.Thread(target=_run, daemon=True).start()

    def _on_maintenance_complete(self, success, output, tool_type):
        if success:
            ToastNotification(
                self,
                "Éxito",
                f"Comando '{tool_type}' ejecutado correctamente.",
                color="green",
            )
            # Si cambiamos IP, refrescar info
            if tool_type in ["renew", "release"]:
                self.after(2000, self.refresh_local_info)
        else:
            # Mostrar error truncado si es muy largo
            err_msg = output[:100] + "..." if len(output) > 100 else output
            ToastNotification(
                self, "Error", f"Fallo al ejecutar: {err_msg}", color="red"
            )

    def display_arp_table(self):
        """Obtiene y muestra la tabla ARP en su consola."""
        self.arp_console.configure(state="normal")
        self.arp_console.delete("1.0", "end")

        success, data = NetworkTools.get_arp_table()
        if success:
            header = f"{'Dirección IP':<25}{'Dirección MAC':<20}{'Tipo'}\n"
            separator = f"{'-' * 25}{'-' * 20}{'-' * 10}\n"
            self.arp_console.insert("end", header + separator)
            for entry in data:
                line = f"{entry['ip']:<25}{entry['mac']:<20}{entry['type']}\n"
                self.arp_console.insert("end", line)
        else:
            self.arp_console.insert("end", f"Error al obtener la tabla ARP:\n{data}")

        self.arp_console.configure(state="disabled")

    def display_netstat(self):
        """Obtiene y muestra las conexiones de red (netstat)."""
        self.netstat_console.configure(state="normal")
        self.netstat_console.delete("1.0", "end")

        success, data = NetworkTools.get_netstat()
        if success:
            header = f"{'Proto':<8}{'Dirección Local':<25}{'Dirección Remota':<25}{'Estado'}\n"
            separator = f"{'-' * 8}{'-' * 25}{'-' * 25}{'-' * 15}\n"
            self.netstat_console.insert("end", header + separator)

            filter_text = self.netstat_filter_entry.get().lower()

            for conn in data:
                line = f"{conn['proto']:<8}{conn['local_addr']:<25}{conn['foreign_addr']:<25}{conn['state']}\n"
                if not filter_text or filter_text in line.lower():
                    self.netstat_console.insert("end", line)
        else:
            self.netstat_console.insert("end", f"Error al obtener netstat:\n{data}")

        self.netstat_console.configure(state="disabled")

    def load_service_manager(self):
        """Carga los servicios desde el whitelist y los muestra en la UI."""
        try:
            whitelist_path = os.path.join(BASE_PATH, "services_whitelist.json")
            with open(whitelist_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for service in data.get("services", []):
                name = service["name"]
                desc = service.get("description", name)

                frame = customtkinter.CTkFrame(
                    self.services_container, fg_color="transparent"
                )
                frame.pack(fill="x", pady=2, padx=5)

                label = customtkinter.CTkLabel(
                    frame, text=f"{name}", font=("Arial", 12, "bold"), anchor="w"
                )
                label.pack(side="left", fill="x", expand=True)

                status_label = customtkinter.CTkLabel(
                    frame, text="Cargando...", width=80, text_color="gray"
                )
                status_label.pack(side="left", padx=5)

                btn_start = customtkinter.CTkButton(
                    frame,
                    text="▶",
                    width=30,
                    command=lambda n=name: self.run_service_action(n, "start"),
                )
                btn_start.pack(side="left")

                btn_stop = customtkinter.CTkButton(
                    frame,
                    text="■",
                    width=30,
                    fg_color="#ff6b6b",
                    command=lambda n=name: self.run_service_action(n, "stop"),
                )
                btn_stop.pack(side="left", padx=5)

                self.service_widgets[name] = {
                    "status_label": status_label,
                    "start_btn": btn_start,
                    "stop_btn": btn_stop,
                }

            self.after(500, self.refresh_all_services_status)

        except FileNotFoundError:
            customtkinter.CTkLabel(
                self.services_container, text="services_whitelist.json no encontrado."
            ).pack()
        except Exception as e:
            customtkinter.CTkLabel(
                self.services_container, text=f"Error al cargar: {e}"
            ).pack()

    def refresh_all_services_status(self):
        """Actualiza el estado de todos los servicios en la lista."""
        for service_name, widgets in self.service_widgets.items():
            widgets["status_label"].configure(text="...", text_color="gray")
            threading.Thread(
                target=self._fetch_service_status, args=(service_name,), daemon=True
            ).start()

    def _fetch_service_status(self, service_name):
        success, state = NetworkTools.get_service_status(service_name)
        if not success:
            state = "Error"
        self.after(0, self._update_service_status_ui, service_name, state)

    def _update_service_status_ui(self, service_name, state):
        widgets = self.service_widgets.get(service_name)
        if not widgets:
            return

        color = "gray"
        if state == "Corriendo":
            color = "#51cf66"
        elif state == "Detenido":
            color = "#ff6b6b"
        elif state == "No existe":
            color = "#ff9f1c"

        widgets["status_label"].configure(text=state, text_color=color)

    def run_service_action(self, service_name, action):
        if not messagebox.askyesno(
            "Confirmar Acción",
            f"¿Está seguro que desea '{action}' el servicio '{service_name}'?",
        ):
            return

        ToastNotification(
            self,
            "Ejecutando...",
            f"Intentando {action} el servicio {service_name}...",
            color="blue",
        )

        def _run():
            success, msg = NetworkTools.manage_service(service_name, action)
            self.after(
                0,
                lambda: ToastNotification(
                    self, "Resultado", msg, color="green" if success else "red"
                ),
            )
            self.after(2000, lambda: self._fetch_service_status(service_name))

        threading.Thread(target=_run, daemon=True).start()

    def run_diagnostic_tool(self, tool_type):
        if self.active_diag_process:
            ToastNotification(
                self,
                "Proceso en Ejecución",
                "Ya hay una herramienta de diagnóstico activa.",
                color="yellow",
            )
            return

        target = self.diag_target_entry.get().strip()
        if not target:
            ToastNotification(
                self,
                "Entrada Vacía",
                "Por favor, ingrese una IP o dominio.",
                color="red",
            )
            return

        # UI state: running
        self.diag_console.configure(state="normal")
        self.diag_console.delete("1.0", "end")
        self.diag_console.insert(
            "end", f"--- Ejecutando {tool_type.upper()} en {target} ---\n\n"
        )
        self.diag_console.configure(state="disabled")

        self.btn_ping.configure(state="disabled")
        self.btn_tracert.configure(state="disabled")
        self.btn_nslookup.configure(state="disabled")
        self.btn_stop_diag.configure(state="normal")

        NetworkTools.run_diagnostic(tool_type, target, self.diagnostic_callback)

    def stop_diagnostic_tool(self):
        if self.active_diag_process:
            NetworkTools.stop_diagnostic(self.active_diag_process)
            self.active_diag_process = None
            self._insert_to_console("\n--- Proceso detenido por el usuario ---\n")
            self._on_diagnostic_complete()

    def diagnostic_callback(self, data, proc=None):
        if proc:
            self.active_diag_process = proc
            return

        if data == "PROCESS_FINISHED":
            self.after(0, self._on_diagnostic_complete)
        elif data is not None:
            self.after(0, self._insert_to_console, data)

    def _insert_to_console(self, text):
        self.diag_console.configure(state="normal")
        self.diag_console.insert("end", text)
        self.diag_console.see("end")
        self.diag_console.configure(state="disabled")

    def _on_diagnostic_complete(self):
        self.active_diag_process = None
        self.btn_ping.configure(state="normal")
        self.btn_tracert.configure(state="normal")
        self.btn_nslookup.configure(state="normal")
        self.btn_stop_diag.configure(state="disabled")
        ToastNotification(
            self,
            "Finalizado",
            "La herramienta de diagnóstico ha terminado.",
            color="blue",
        )

    def setup_user_management_tab(self):
        # Frame para agregar usuarios
        self.add_user_frame = customtkinter.CTkFrame(self.tab_usuarios)
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

        # Lista de usuarios
        self.user_list_frame = customtkinter.CTkScrollableFrame(
            self.tab_usuarios, label_text="Usuarios Existentes"
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
            ToastNotification(
                self, "Error", "Las contraseñas no coinciden", color="red"
            )
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

    def actualizar_lista_usuarios(self):
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        users = self.auth.get_all_users(self.current_user["role"])
        for i, user in enumerate(users):
            user_info = (
                f"{user['full_name']} ({user['username']}) - Rol: {user['role']}"
            )
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

    def open_telegram_config(self):
        TelegramConfigWindow(
            self,
            self.telegram_alerter.token,
            self.telegram_alerter.chat_id,
            self.save_telegram_config,
        )

    def save_telegram_config(self, token, chat_id):
        self.telegram_alerter.update_credentials(token, chat_id)
        if token and chat_id:
            self.telegram_alerter.test_message()
        self.guardar_equipos()  # Guardar en JSON

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
        try:
            config_path = os.path.join(BASE_PATH, "equipos_guardados.json")
            with open(config_path, "r") as file:
                data = json.load(file)
                equipos_guardados = data.get("equipos", [])

                # Si el archivo de configuración existe y tiene equipos, SIEMPRE tiene prioridad.
                if equipos_guardados:
                    self.equipos_a_monitorear = equipos_guardados
                    print(
                        f"Configuración cargada: {len(self.equipos_a_monitorear)} equipos desde JSON."
                    )

                self.ping_interval = data.get("intervalo_ping", 15)
                if self.ping_interval < 1:
                    self.ping_interval = 1

                for equipo in self.equipos_a_monitorear:
                    ts_str = equipo.get("disconnection_timestamp")
                    if ts_str:
                        try:
                            equipo["disconnection_timestamp"] = (
                                datetime.datetime.fromisoformat(ts_str)
                            )
                        except:
                            equipo["disconnection_timestamp"] = None
                    else:
                        equipo["disconnection_timestamp"] = None

                # Cargar config de Telegram
                tg_config = data.get("telegram", {})
                token = tg_config.get("token", "")
                chat_id = tg_config.get("chat_id", "")

                # Si no hay config guardada, usar defaults de branding
                if not token:
                    token = branding.TELEGRAM_TOKEN_DEFAULT
                if not chat_id:
                    chat_id = branding.TELEGRAM_CHAT_ID_DEFAULT

                self.telegram_alerter.update_credentials(token, chat_id)

            print("Configuración inicial procesada.")
        except FileNotFoundError:
            print(
                "Archivo de configuración no encontrado. Usando equipos por defecto de main.py."
            )
        except Exception as e:
            print(f"Error al cargar la configuración inicial: {e}")

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
                daemon=True,
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
                "telegram": {
                    "token": self.telegram_alerter.token,
                    "chat_id": self.telegram_alerter.chat_id,
                },
            }
            config_path = os.path.join(BASE_PATH, "equipos_guardados.json")
            with open(config_path, "w") as file:
                json.dump(data_to_save, file, indent=4)

            # Guardar también las métricas históricas y el registro diario
            if hasattr(self, "metricas"):
                self.metricas.registrar_disponibilidad_diaria()
        except Exception as e:
            print(f"Error al guardar: {e}")

    def cargar_equipos(self):
        try:
            self.cargar_configuracion_inicial()
            self.ping_interval_entry.delete(0, "end")
            self.ping_interval_entry.insert(0, str(self.ping_interval))
            self.create_monitors()
        except Exception as e:
            print(f"Error al cargar: {e}")

    def realizar_backup_manual(self):
        success, msg = self.backup_manager.crear_backup()
        if success:
            ToastNotification(self, "Backup Exitoso", msg, color="green")
        else:
            ToastNotification(self, "Error Backup", msg, color="red")

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

                        # Si es el horario de cierre (16:55), hacer backup
                        if scheduled_time.hour == 16 and scheduled_time.minute == 55:
                            self.backup_manager.crear_backup()

                        self.log_executed_today[time_key] = True
                time.sleep(30)

        threading.Thread(target=scheduler_thread, daemon=True).start()

    def generar_reporte(self):
        if not REPORTLAB_AVAILABLE:
            ToastNotification(
                self,
                "Error",
                "Librería PDF no encontrada. Reinstale la aplicación.",
                color="red",
            )
            return

        filename_only = f"Reporte_ArgosGuard_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        filename = os.path.join(BASE_PATH, filename_only)

        try:
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            elements = []
            styles = getSampleStyleSheet()

            # --- Encabezado con Logo ---
            logo_path = os.path.join(ASSETS_PATH, "img", "logoargosguard.png")
            if os.path.exists(logo_path):
                # Logo a la derecha, Título a la izquierda (usando tabla invisible)
                im = PDFImage(logo_path, width=50, height=50)
                im.hAlign = "RIGHT"

                title_text = Paragraph(
                    f"<b>Reporte de Estado de Red - Argos Guard</b><br/><font size=10>Generado por: {self.current_user['full_name']}</font>",
                    styles["Title"],
                )

                header_data = [[title_text, im]]
                header_table = Table(header_data, colWidths=[500, 100])
                header_table.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                elements.append(header_table)
            else:
                elements.append(
                    Paragraph("Reporte de Estado de Red - Argos Guard", styles["Title"])
                )

            elements.append(Spacer(1, 20))
            elements.append(
                Paragraph(
                    f"Fecha de Corte: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 20))

            # --- Tabla de Datos ---
            data = [
                [
                    "Equipo / Etiqueta",
                    "Dirección IP",
                    "Estado Actual",
                    "Uptime (30d)",
                    "Latencia (Avg)",
                    "Desconexiones",
                ]
            ]

            for equipo in self.equipos_a_monitorear:
                ip = equipo["ip"]
                monitor = self.monitors.get(ip)

                # Obtener datos reales
                estado = monitor.status if monitor else "Desconocido"
                desconexiones = monitor.desconexiones_count if monitor else 0

                # Calcular métricas desde metrics_manager
                uptime = self.metricas.calcular_uptime(ip)
                datos_hist = self.metricas.obtener_datos(ip, periodo_horas=1)
                if datos_hist and datos_hist["latencias"]:
                    # Filtrar ceros o Nones para promedio
                    lats = [l for l in datos_hist["latencias"] if l > 0]
                    avg_lat = f"{sum(lats) / len(lats):.1f} ms" if lats else "N/A"
                else:
                    avg_lat = "N/A"

                data.append(
                    [
                        equipo["label"],
                        ip,
                        estado,
                        f"{uptime:.1f}%",
                        avg_lat,
                        str(desconexiones),
                    ]
                )

            # Estilo de Tabla
            t = Table(data, colWidths=[200, 100, 100, 80, 100, 100])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(t)

            # --- SECCIÓN VISUAL (Gráficos) ---
            elements.append(Spacer(1, 20))
            elements.append(
                Paragraph(
                    "<b>Análisis Visual de Rendimiento (Últimas 24h)</b>",
                    styles["Heading2"],
                )
            )
            elements.append(Spacer(1, 10))

            # 1. Generar Gráfico de Latencia para el PDF
            fig_lat = Figure(figsize=(10, 3), facecolor="white")
            ax_lat = fig_lat.add_subplot(111)
            ax_lat.set_title(
                "Histórico de Latencia (ms) - Horario Laboral (09:00 - 17:00)",
                fontsize=10,
            )
            ax_lat.grid(True, alpha=0.3)
            colores = ["#007bff", "#dc3545", "#28a745", "#ffc107", "#6f42c1", "#e83e8c"]

            has_lat_data = False
            for i, equipo in enumerate(self.equipos_a_monitorear):
                datos = self.metricas.obtener_datos(equipo["ip"], periodo_horas=24)
                if datos and len(datos["timestamps"]) > 0:
                    # Usar un índice simple para el eje X en el PDF
                    ax_lat.plot(
                        range(len(datos["latencias"])),
                        datos["latencias"],
                        label=equipo["label"],
                        color=colores[i % len(colores)],
                        linewidth=1,
                    )
                    has_lat_data = True

            if has_lat_data:
                ax_lat.legend(fontsize=7, loc="upper right")
                img_buffer_lat = io.BytesIO()
                fig_lat.savefig(
                    img_buffer_lat, format="png", bbox_inches="tight", dpi=150
                )
                img_buffer_lat.seek(0)
                elements.append(PDFImage(img_buffer_lat, width=500, height=150))

            elements.append(Spacer(1, 20))

            # 2. Generar Heatmap para el PDF
            elements.append(
                Paragraph(
                    "<b>Mapa de Calor de Disponibilidad (Bloques Horarios)</b>",
                    styles["Heading2"],
                )
            )
            elements.append(Spacer(1, 10))

            fig_hm = Figure(figsize=(10, 3), facecolor="white")
            ax_hm = fig_hm.add_subplot(111)

            heatmap_data = []
            labels_hm = []
            for equipo in self.equipos_a_monitorear:
                labels_hm.append(equipo["label"][:20])
                datos = self.metricas.obtener_datos(equipo["ip"], periodo_horas=24)
                if datos and datos["estados"]:
                    bloques = np.array_split(datos["estados"], 24)
                    dispo_bloques = [
                        sum(1 for s in b if s == 1) / len(b) if len(b) > 0 else 0
                        for b in bloques
                    ]
                    heatmap_data.append(dispo_bloques)
                else:
                    heatmap_data.append([0] * 24)

            if heatmap_data:
                im_hm = ax_hm.imshow(
                    heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1
                )
                ax_hm.set_yticks(range(len(labels_hm)))
                ax_hm.set_yticklabels(labels_hm, fontsize=7)
                ax_hm.set_xticks(range(0, 24, 2))
                ax_hm.set_xticklabels([f"{h}h" for h in range(0, 24, 2)], fontsize=7)

                img_buffer_hm = io.BytesIO()
                fig_hm.savefig(
                    img_buffer_hm, format="png", bbox_inches="tight", dpi=150
                )
                img_buffer_hm.seek(0)
                elements.append(PDFImage(img_buffer_hm, width=500, height=150))

            elements.append(Spacer(1, 20))

            # Footer
            elements.append(Spacer(1, 30))
            elements.append(
                Paragraph(
                    "Documento generado automáticamente por Argos Guard v2.0 | Horario Laboral: 09:00 - 17:00",
                    styles["Italic"],
                )
            )

            doc.build(elements)
            ToastNotification(
                self,
                "Reporte PDF",
                f"Generado exitosamente:\n{filename}",
                color="green",
            )

            # Intentar abrir el PDF automáticamente (Windows)
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
                self.ax_latencia.plot(
                    [i for i in range(len(indices))],
                    [latencias[j] for j in indices],
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
