# ui/windows/login_window.py
"""
Ventanas de autenticación de Anvic Network Sentinel:
 - LoginWindow: pantalla de inicio de sesión
 - SetupWindow: configuración inicial del primer super admin
"""

import customtkinter
import os
from utils.paths import get_resource_path
from PIL import Image
from config import branding as b


def _apply_window_icon(window) -> None:
    """Aplica el icono oficial de la app a una ventana secundaria."""
    try:
        assets = get_resource_path("assets")
        icon_asset = os.path.join(assets, "img", b.ICON_FILE)
        logo_asset = os.path.join(assets, "img", b.LOGO_FILE)
        if os.path.exists(icon_asset) and icon_asset.lower().endswith(".ico"):
            window.iconbitmap(icon_asset)
            window._icon_path = icon_asset
        elif os.path.exists(icon_asset):
            img = Image.open(icon_asset)
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            window.wm_iconphoto(False, photo)
            window._icon_photo = photo
        elif os.path.exists(logo_asset):
            img = Image.open(logo_asset)
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            window.wm_iconphoto(False, photo)
            window._icon_photo = photo
    except Exception:
        pass


class LoginWindow(customtkinter.CTkToplevel):
    """Ventana de inicio de sesión."""

    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.auth = master.auth

        self.title(f"{b.APP_NAME} - Inicio de Sesión")
        self.geometry("480x700")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Centrar en pantalla
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"480x700+{(sw-480)//2}+{(sh-700)//2}")
        self.after(200, lambda: _apply_window_icon(self))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        # Logo
        try:
            logo_path = os.path.join(get_resource_path("assets"), "img", b.LOGO_FILE)
            pil_img = Image.open(logo_path)
            self.logo_image = customtkinter.CTkImage(
                light_image=pil_img, dark_image=pil_img, size=(300, 300)
            )
            customtkinter.CTkLabel(self, image=self.logo_image, text="").pack(pady=(40, 10))
        except Exception:
            customtkinter.CTkLabel(
                self, text=f"🛡️ {b.APP_NAME}", font=("Arial", 32, "bold"), text_color="#00d9ff"
            ).pack(pady=(40, 10))

        self.subtitle = customtkinter.CTkLabel(
            self, text="Inicio de Sesión", font=("Arial", 18)
        )
        self.subtitle.pack(pady=(0, 30))

        self.username_entry = customtkinter.CTkEntry(
            self, placeholder_text="Usuario", width=280, height=45, font=("Arial", 14)
        )
        self.username_entry.pack(pady=10)

        self.password_entry = customtkinter.CTkEntry(
            self, placeholder_text="Contraseña", show="*", width=280, height=45, font=("Arial", 14)
        )
        self.password_entry.pack(pady=10)

        customtkinter.CTkButton(
            self,
            text="INGRESAR",
            command=self._login,
            width=280, height=45,
            font=("Arial", 16, "bold"),
            fg_color="#00d9ff", text_color="#000000", hover_color="#00b4d8",
        ).pack(pady=(30, 10))

        self.error_label = customtkinter.CTkLabel(
            self, text="", text_color="red", font=("Arial", 12)
        )
        self.error_label.pack(pady=5)

        self.password_entry.bind("<Return>", lambda e: self._login())

    def _on_close(self) -> None:
        self.master.destroy()

    def _login(self) -> None:
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_data = self.auth.authenticate(username, password)

        if user_data:
            if user_data.get("force_change_password", False):
                self._show_change_password_ui(username)
            else:
                self.destroy()
                self.on_login_success(user_data)
        else:
            self.error_label.configure(text="Usuario o contraseña incorrectos")
            self.password_entry.delete(0, "end")

    def _show_change_password_ui(self, username: str) -> None:
        """Reemplaza el formulario de login por el de cambio de contraseña."""
        self.username_entry.pack_forget()
        self.password_entry.pack_forget()
        self.subtitle.configure(text="⚠️ Cambio de Contraseña Requerido")
        self.error_label.configure(text="")

        self.new_pass = customtkinter.CTkEntry(
            self, placeholder_text="Nueva Contraseña", show="*", width=280, height=45, font=("Arial", 14)
        )
        self.new_pass.pack(pady=10)

        self.confirm_pass = customtkinter.CTkEntry(
            self, placeholder_text="Confirmar Contraseña", show="*", width=280, height=45, font=("Arial", 14)
        )
        self.confirm_pass.pack(pady=10)

        customtkinter.CTkLabel(
            self,
            text="Mínimo 8 caracteres, 1 Mayúscula, 1 Número\ny 1 Carácter Especial (!@#$%^&*)",
            font=("Arial", 10, "italic"),
            text_color="#AAAAAA",
        ).pack(pady=5)

        customtkinter.CTkButton(
            self,
            text="ACTUALIZAR Y ENTRAR",
            command=lambda: self._perform_password_change(username),
            width=280, height=45,
            font=("Arial", 14, "bold"),
            fg_color="#ff9f1c", text_color="#000000",
        ).pack(pady=20)

    def _perform_password_change(self, username: str) -> None:
        p1, p2 = self.new_pass.get(), self.confirm_pass.get()
        if not p1 or not p2:
            self.error_label.configure(text="Los campos no pueden estar vacíos")
            return
        if p1 != p2:
            self.error_label.configure(text="Las contraseñas no coinciden")
            return
        success, msg = self.auth.change_password(username, p1)
        if success:
            user_data = self.auth.authenticate(username, p1)
            self.destroy()
            self.on_login_success(user_data)
        else:
            self.error_label.configure(text=msg)


class SetupWindow(customtkinter.CTkToplevel):
    """Ventana de configuración inicial (primer arranque)."""

    def __init__(self, master, on_setup_success):
        super().__init__(master)
        self.on_setup_success = on_setup_success
        self.auth = master.auth

        self.title(f"{b.APP_NAME} - Configuración Inicial")
        self.geometry("450x600")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"450x600+{(sw-450)//2}+{(sh-600)//2}")
        self.after(200, lambda: _apply_window_icon(self))

        customtkinter.CTkLabel(
            self, text="🚀 Configuración Inicial", font=("Arial", 24, "bold"), text_color="#00d9ff"
        ).pack(pady=(40, 10))

        customtkinter.CTkLabel(
            self,
            text=f"Bienvenido a {b.APP_NAME}.\nCree su cuenta de Administrador Maestro.",
            font=("Arial", 14), text_color="#AAAAAA",
        ).pack(pady=(0, 20))

        self.fullname_entry = customtkinter.CTkEntry(
            self, placeholder_text="Nombre Real / Operador (Opcional)", width=300, height=40
        )
        self.fullname_entry.pack(pady=6)

        self.user_entry = customtkinter.CTkEntry(
            self, placeholder_text="Usuario Maestro (Login)", width=300, height=40
        )
        self.user_entry.pack(pady=6)

        self.pass_entry = customtkinter.CTkEntry(
            self, placeholder_text="Contraseña", show="*", width=300, height=40
        )
        self.pass_entry.pack(pady=6)

        self.confirm_entry = customtkinter.CTkEntry(
            self, placeholder_text="Confirmar Contraseña", show="*", width=300, height=40
        )
        self.confirm_entry.pack(pady=6)

        customtkinter.CTkLabel(
            self,
            text="Mínimo 8 caracteres, 1 Mayúscula, 1 Número\ny 1 Carácter Especial (!@#$%^&*)",
            font=("Arial", 10, "italic"), text_color="#AAAAAA",
        ).pack(pady=5)

        customtkinter.CTkButton(
            self,
            text="FINALIZAR CONFIGURACIÓN",
            command=self._perform_setup,
            width=300, height=45,
            font=("Arial", 14, "bold"),
            fg_color="#51cf66", hover_color="#40c057",
        ).pack(pady=20)

        self.error_lbl = customtkinter.CTkLabel(self, text="", text_color="#ff6b6b")
        self.error_lbl.pack(pady=5)

    def _on_close(self) -> None:
        self.master.destroy()

    def _perform_setup(self) -> None:
        fullname = self.fullname_entry.get().strip() or "Administrador Maestro"
        user = self.user_entry.get().strip()
        p1, p2 = self.pass_entry.get(), self.confirm_entry.get()

        if not user or not p1 or not p2:
            self.error_lbl.configure(text="Todos los campos marcados son obligatorios")
            return
        if p1 != p2:
            self.error_lbl.configure(text="Las contraseñas no coinciden")
            return

        success, msg = self.auth.create_initial_superuser(user, p1, full_name=fullname)
        if success:
            user_data = self.auth.authenticate(user, p1)
            self.destroy()
            self.on_setup_success(user_data)
        else:
            self.error_lbl.configure(text=msg)
