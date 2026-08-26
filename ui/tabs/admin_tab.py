# ui/tabs/admin_tab.py
"""
Pestana de Gestion de Usuarios de Argos Guard.
Solo visible para roles 'admin' y 'super_admin'.
"""

import customtkinter
from ui.components.toast import ToastNotification


class AdminTab:
    """Controlador de la pestana 'Gestion de Usuarios'."""

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self._build_ui()

    def _build_ui(self) -> None:
        self.scroll_frame = customtkinter.CTkScrollableFrame(self.frame)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        add_frame = customtkinter.CTkFrame(self.scroll_frame)
        add_frame.pack(fill="x", padx=20, pady=20)

        customtkinter.CTkLabel(
            add_frame, text="Agregar Nuevo Usuario", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        fields = [
            ("Usuario:", "new_username_entry"),
            ("Nombre Completo:", "new_fullname_entry"),
        ]
        for i, (label, attr) in enumerate(fields, start=1):
            customtkinter.CTkLabel(add_frame, text=label).grid(
                row=i, column=0, padx=10, pady=5, sticky="e"
            )
            entry = customtkinter.CTkEntry(add_frame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            setattr(self, attr, entry)

        customtkinter.CTkLabel(add_frame, text="Contrasena:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.new_password_entry = customtkinter.CTkEntry(add_frame, show="*", placeholder_text="Mínimo 8 caracteres")
        self.new_password_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(add_frame, text="Confirmar Clave:").grid(
            row=4, column=0, padx=10, pady=5, sticky="e"
        )
        self.confirm_password_entry = customtkinter.CTkEntry(add_frame, show="*", placeholder_text="Repita su contraseña")
        self.confirm_password_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(add_frame, text="Rol:").grid(
            row=5, column=0, padx=10, pady=5, sticky="e"
        )
        roles = ["user"]
        if self.app.current_user["role"] == "super_admin":
            roles.append("admin")
        self.new_role_option = customtkinter.CTkOptionMenu(add_frame, values=roles)
        self.new_role_option.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkButton(
            add_frame, text="Crear Usuario", command=self._crear_usuario
        ).grid(row=6, column=0, columnspan=2, pady=20)

        streaming_frame = customtkinter.CTkFrame(self.scroll_frame)
        streaming_frame.pack(fill="x", padx=20, pady=(0, 20))

        customtkinter.CTkLabel(
            streaming_frame, text="Configuracion de Streaming y TLS", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        customtkinter.CTkLabel(streaming_frame, text="Maximo de streams:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.camera_max_streams_entry = customtkinter.CTkEntry(streaming_frame, placeholder_text="Ej: 4")
        self.camera_max_streams_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.camera_max_streams_entry.insert(0, str(getattr(self.app, "camera_max_streams", 1)))

        customtkinter.CTkLabel(streaming_frame, text="Intervalo snapshot (seg):").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.camera_snapshot_interval_entry = customtkinter.CTkEntry(streaming_frame, placeholder_text="Ej: 2")
        self.camera_snapshot_interval_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.camera_snapshot_interval_entry.insert(0, str(getattr(self.app, "camera_snapshot_interval", 2)))

        self.verify_tls_switch = customtkinter.CTkSwitch(
            streaming_frame,
            text="Modo TLS estricto (desactivalo para usar verify=False)",
        )
        self.verify_tls_switch.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")
        if getattr(self.app, "verify_tls_certificates", False):
            self.verify_tls_switch.select()
        else:
            self.verify_tls_switch.deselect()

        customtkinter.CTkLabel(
            streaming_frame,
            text="Si lo desactivas, Sentinel permitira certificados autofirmados o invalidos en HTTPS para camaras, NVR y paneles legacy.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.external_geolocation_switch = customtkinter.CTkSwitch(
            streaming_frame,
            text="Permitir geolocalizacion externa en Tracert",
        )
        self.external_geolocation_switch.grid(row=5, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        if getattr(self.app, "enable_external_geolocation", False):
            self.external_geolocation_switch.select()
        else:
            self.external_geolocation_switch.deselect()

        customtkinter.CTkLabel(
            streaming_frame,
            text="Cuando esta opcion esta activa, los saltos publicos de Tracert se enriquecen consultando un servicio externo. Se recomienda dejarla desactivada por defecto.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.verify_ssh_host_key_switch = customtkinter.CTkSwitch(
            streaming_frame,
            text="Validar huella SSH del host",
        )
        self.verify_ssh_host_key_switch.grid(row=7, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        if getattr(self.app, "verify_ssh_host_key", True):
            self.verify_ssh_host_key_switch.select()
        else:
            self.verify_ssh_host_key_switch.deselect()

        self.ssh_tofu_switch = customtkinter.CTkSwitch(
            streaming_frame,
            text="Permitir confianza inicial SSH (TOFU)",
        )
        self.ssh_tofu_switch.grid(row=8, column=0, columnspan=2, padx=10, pady=(2, 4), sticky="w")
        if getattr(self.app, "ssh_trust_on_first_use", False):
            self.ssh_tofu_switch.select()
        else:
            self.ssh_tofu_switch.deselect()

        customtkinter.CTkLabel(
            streaming_frame,
            text="Con validacion SSH activa, Sentinel solo aceptara servidores conocidos. TOFU permite registrar la primera huella automaticamente y exigirla en conexiones futuras.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.camera_settings_save_button = customtkinter.CTkButton(
            streaming_frame, text="Guardar streaming, TLS y red", command=self._guardar_streaming
        )
        self.camera_settings_save_button.grid(row=10, column=0, columnspan=2, pady=12)

        self.user_list_frame = customtkinter.CTkScrollableFrame(
            self.scroll_frame, label_text="Usuarios Existentes"
        )
        self.user_list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self._actualizar_lista_usuarios()

    def _crear_usuario(self) -> None:
        username = self.new_username_entry.get()
        fullname = self.new_fullname_entry.get()
        p1 = self.new_password_entry.get()
        p2 = self.confirm_password_entry.get()
        role = self.new_role_option.get()

        if not username or not fullname or not p1 or not p2:
            ToastNotification(self.app, "Error", "Todos los campos son obligatorios", color="red")
            return
        if p1 != p2:
            ToastNotification(self.app, "Error", "Las contrasenas no coinciden", color="red")
            return

        success, msg = self.app.auth.add_user(
            username, p1, role, fullname, self.app.current_user["role"]
        )
        if success:
            ToastNotification(self.app, "Exito", msg, color="green")
            for entry in (
                self.new_username_entry,
                self.new_fullname_entry,
                self.new_password_entry,
                self.confirm_password_entry,
            ):
                entry.delete(0, "end")
            self._actualizar_lista_usuarios()
        else:
            ToastNotification(self.app, "Error", msg, color="red")

    def _guardar_streaming(self) -> None:
        try:
            max_streams = max(int(self.camera_max_streams_entry.get()), 1)
            snapshot_interval = max(int(self.camera_snapshot_interval_entry.get()), 1)
        except ValueError:
            ToastNotification(self.app, "Error", "Los valores de streaming deben ser numericos", color="red")
            return

        verify_tls_certificates = bool(self.verify_tls_switch.get())
        enable_external_geolocation = bool(self.external_geolocation_switch.get())
        verify_ssh_host_key = bool(self.verify_ssh_host_key_switch.get())
        ssh_trust_on_first_use = bool(self.ssh_tofu_switch.get())
        self.app.save_camera_runtime_settings(
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
        ToastNotification(
            self.app,
            "Streaming",
            f"Configuracion actualizada. TLS: {mode} | Geo externa: {geo} | SSH: {ssh_mode}",
            color="green",
        )

    def _actualizar_lista_usuarios(self) -> None:
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        users = self.app.auth.get_all_users(self.app.current_user["role"])
        for i, user in enumerate(users):
            password_str = user.get("password_plain", "Oculta (Antigua)")
            info = f"{user['full_name']} ({user['username']}) - Rol: {user['role']} - Pass: {password_str}"
            customtkinter.CTkLabel(
                self.user_list_frame, text=info
            ).grid(row=i, column=0, padx=10, pady=5, sticky="w")

            if (
                self.app.current_user["role"] == "super_admin"
                and user["username"] != self.app.current_user["username"]
            ):
                btns_frame = customtkinter.CTkFrame(self.user_list_frame, fg_color="transparent")
                btns_frame.grid(row=i, column=1, padx=10, pady=5)
                
                customtkinter.CTkButton(
                    btns_frame,
                    text="Editar",
                    width=60,
                    fg_color="#005b96",
                    command=lambda u=user: self._editar_usuario_ui(u),
                ).pack(side="left", padx=5)

                customtkinter.CTkButton(
                    btns_frame,
                    text="Eliminar",
                    width=60,
                    fg_color="#ff6b6b",
                    command=lambda u=user["username"]: self._eliminar_usuario(u),
                ).pack(side="left")

    def _editar_usuario_ui(self, user: dict) -> None:
        edit_win = customtkinter.CTkToplevel(self.app)
        edit_win.title(f"Editar Usuario: {user['username']}")
        edit_win.geometry("400x450")
        edit_win.grab_set()

        customtkinter.CTkLabel(edit_win, text="Nuevo Username (Opcional):").pack(pady=(10, 0))
        entry_username = customtkinter.CTkEntry(edit_win, width=300, placeholder_text="Nombre de usuario")
        entry_username.insert(0, user["username"])
        entry_username.pack(pady=5)

        customtkinter.CTkLabel(edit_win, text="Nuevo Nombre Completo:").pack(pady=(10, 0))
        entry_fullname = customtkinter.CTkEntry(edit_win, width=300, placeholder_text="Nombre Completo")
        entry_fullname.insert(0, user["full_name"])
        entry_fullname.pack(pady=5)

        customtkinter.CTkLabel(edit_win, text="Nueva Contraseña (Deje vacío si no cambia):").pack(pady=(10, 0))
        entry_password = customtkinter.CTkEntry(edit_win, width=300, placeholder_text="Nueva contraseña (opcional)")
        if "password_plain" in user:
            entry_password.insert(0, user["password_plain"])
        entry_password.pack(pady=5)

        customtkinter.CTkLabel(edit_win, text="Rol:").pack(pady=(10, 0))
        role_var = customtkinter.StringVar(value=user["role"])
        role_menu = customtkinter.CTkOptionMenu(edit_win, values=["operador", "admin", "super_admin"], variable=role_var)
        role_menu.pack(pady=5)

        def save_edit():
            nu = entry_username.get().strip()
            nf = entry_fullname.get().strip()
            np = entry_password.get().strip()
            nr = role_var.get()
            
            if not nu or not nf:
                ToastNotification(self.app, "Error", "Username y Fullname no pueden estar vacíos.", color="red")
                return
                
            success, msg = self.app.auth.update_user(
                self.app.current_user["role"],
                user["username"], nu, np, nf, nr
            )
            if success:
                ToastNotification(self.app, "Exito", msg, color="green")
                self._actualizar_lista_usuarios()
                edit_win.destroy()
            else:
                ToastNotification(self.app, "Error", msg, color="red")

        customtkinter.CTkButton(edit_win, text="Guardar Cambios", command=save_edit).pack(pady=20)

    def _eliminar_usuario(self, username: str) -> None:
        success, msg = self.app.auth.delete_user(username, self.app.current_user["role"])
        if success:
            ToastNotification(self.app, "Exito", msg, color="green")
            self._actualizar_lista_usuarios()
        else:
            ToastNotification(self.app, "Error", msg, color="red")
