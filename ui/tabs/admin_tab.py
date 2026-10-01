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

        # Configuración de Red (Intervalo Ping)
        network_ping_frame = customtkinter.CTkFrame(self.scroll_frame)
        network_ping_frame.pack(fill="x", padx=20, pady=(0, 20))
        network_ping_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            network_ping_frame,
            text="⚡ Configuración de Red e Intervalo de Monitoreo",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        customtkinter.CTkLabel(
            network_ping_frame,
            text="Frecuencia con la que se comprueba el estado ICMP/Ping de cada activo en la red (segundos).",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        customtkinter.CTkLabel(network_ping_frame, text="Intervalo Ping (Segundos):").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.ping_interval_entry = customtkinter.CTkEntry(network_ping_frame, width=120)
        self.ping_interval_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.ping_interval_entry.insert(0, str(getattr(self.app, "ping_interval", 15)))

        customtkinter.CTkButton(
            network_ping_frame,
            text="Guardar Intervalo de Ping",
            command=self._guardar_intervalo_ping,
            fg_color="#0284C7",
            hover_color="#0369A1",
        ).grid(row=3, column=0, columnspan=2, pady=12)

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

        # ── Frame para Configuración de Turno Operacional ─────────────────────
        turno_frame = customtkinter.CTkFrame(self.scroll_frame)
        turno_frame.pack(fill="x", padx=20, pady=(0, 20))
        turno_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            turno_frame,
            text="⏰ Configuración de Turno Operacional (Telemetría Adaptativa)",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        customtkinter.CTkLabel(
            turno_frame,
            text="Define el rango horario del turno. Al seleccionar 'Semanal (7D x Turno)' o 'Por Equipo (Turno)' en Telemetría, todas las métricas, gauges, latencia y mapa de calor se adaptarán a esta franja horaria.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        horas_disponibles = [f"{h:02d}:00" for h in range(24)]

        customtkinter.CTkLabel(turno_frame, text="Hora Inicio Turno:").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.turno_inicio_option = customtkinter.CTkOptionMenu(
            turno_frame,
            values=horas_disponibles,
            width=140,
            command=self._on_turno_hours_changed,
        )
        self.turno_inicio_option.set(getattr(self.app, "turno_inicio", "07:00"))
        self.turno_inicio_option.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        customtkinter.CTkLabel(turno_frame, text="Hora Fin Turno:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.turno_fin_option = customtkinter.CTkOptionMenu(
            turno_frame,
            values=horas_disponibles,
            width=140,
            command=self._on_turno_hours_changed,
        )
        self.turno_fin_option.set(getattr(self.app, "turno_fin", "18:00"))
        self.turno_fin_option.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.lbl_turno_resumen = customtkinter.CTkLabel(
            turno_frame,
            text="",
            font=("Arial", 11, "italic"),
            text_color="#38BDF8",
        )
        self.lbl_turno_resumen.grid(row=4, column=0, columnspan=2, padx=10, pady=4, sticky="w")
        self._actualizar_resumen_turno_label()

        self.btn_guardar_turno = customtkinter.CTkButton(
            turno_frame,
            text="Guardar Configuración de Turno",
            command=self._guardar_turno,
            fg_color="#0284C7",
            hover_color="#0369A1",
        )
        self.btn_guardar_turno.grid(row=5, column=0, columnspan=2, pady=12)

        # ── Frame para Parámetros de Reporte Ejecutivo SLA (Fortune 500) ─────────────
        report_frame = customtkinter.CTkFrame(self.scroll_frame)
        report_frame.pack(fill="x", padx=20, pady=(0, 20))
        report_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            report_frame,
            text="📑 Configuración del Reporte Ejecutivo SLA (Fortune 500)",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        customtkinter.CTkLabel(
            report_frame,
            text="Personaliza la identidad corporativa y directrices del reporte formal PDF. Define si se incluye la supervisión de CCTV o si se prioriza el análisis puro de infraestructura de red y SLA.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        customtkinter.CTkLabel(report_frame, text="Empresa / Cliente:").grid(
            row=2, column=0, padx=10, pady=5, sticky="e"
        )
        self.report_empresa_entry = customtkinter.CTkEntry(report_frame, width=280, placeholder_text="Ej: Anvic Seguridad Integral")
        self.report_empresa_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.report_empresa_entry.insert(0, getattr(self.app, "empresa_cliente", "Anvic Seguridad Integral"))

        customtkinter.CTkLabel(report_frame, text="Sitio / Planta / Faena:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.report_sitio_entry = customtkinter.CTkEntry(report_frame, width=280, placeholder_text="Ej: Planta Quilicura - Renca")
        self.report_sitio_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.report_sitio_entry.insert(0, getattr(self.app, "sitio_planta", "Planta Quilicura - Renca"))

        customtkinter.CTkLabel(report_frame, text="SLA Objetivo (%):").grid(
            row=4, column=0, padx=10, pady=5, sticky="e"
        )
        self.report_sla_entry = customtkinter.CTkEntry(report_frame, width=120, placeholder_text="Ej: 99.5")
        self.report_sla_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        self.report_sla_entry.insert(0, str(getattr(self.app, "sla_objetivo", 99.5)))

        self.report_incluir_cctv_switch = customtkinter.CTkSwitch(
            report_frame,
            text="Incluir Supervisión CCTV / Cámaras en Reporte PDF",
        )
        self.report_incluir_cctv_switch.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")
        if getattr(self.app, "incluir_cctv_en_reporte", False):
            self.report_incluir_cctv_switch.select()
        else:
            self.report_incluir_cctv_switch.deselect()

        customtkinter.CTkLabel(
            report_frame,
            text="Si está desactivado, el reporte omitirá los apartados de CCTV y destacará en su lugar la meta de SLA Contractual y el dictamen técnico de red.",
            text_color="#9aa0a6",
            justify="left",
            wraplength=640,
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        self.btn_guardar_reporte_config = customtkinter.CTkButton(
            report_frame,
            text="Guardar Parámetros de Reporte",
            command=self._guardar_reporte_config,
            fg_color="#059669",
            hover_color="#047857",
        )
        self.btn_guardar_reporte_config.grid(row=7, column=0, columnspan=2, pady=12)

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

    def _actualizar_resumen_turno_label(self) -> None:
        try:
            ini = self.turno_inicio_option.get() if hasattr(self, "turno_inicio_option") else getattr(self.app, "turno_inicio", "07:00")
            fin = self.turno_fin_option.get() if hasattr(self, "turno_fin_option") else getattr(self.app, "turno_fin", "18:00")
            h_ini = int(ini.split(":")[0])
            h_fin = int(fin.split(":")[0])
            duracion = (h_fin - h_ini) if h_ini <= h_fin else (24 - h_ini + h_fin)
            tipo = "Diurno" if h_ini <= h_fin else "Nocturno / Cruza Medianoche"
            if hasattr(self, "lbl_turno_resumen"):
                self.lbl_turno_resumen.configure(
                    text=f"📊 Cobertura del Turno: {duracion} horas ({ini} a {fin}) • Modalidad: {tipo}"
                )
        except Exception:
            pass

    def _on_turno_hours_changed(self, _choice=None) -> None:
        self._actualizar_resumen_turno_label()

    def _guardar_turno(self) -> None:
        ini = self.turno_inicio_option.get()
        fin = self.turno_fin_option.get()
        if hasattr(self.app, "save_turno_runtime_settings"):
            self.app.save_turno_runtime_settings(ini, fin, nombre="Turno Operativo")
        else:
            self.app.turno_inicio = ini
            self.app.turno_fin = fin
            if hasattr(self.app, "monitor_tab"):
                self.app.monitor_tab.guardar_equipos()
            elif hasattr(self.app, "guardar_equipos"):
                self.app.guardar_equipos()
        ToastNotification(
            self.app,
            "Turno Operacional",
            f"Configuración guardada exitosamente: {ini} a {fin}.\nTelemetría adaptada a este turno.",
            color="green",
        )

    def _actualizar_lista_usuarios(self) -> None:
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        users = self.app.auth.get_all_users(self.app.current_user["role"])
        for i, user in enumerate(users):
            password_str = user.get("password_plain", "Oculta (Antigua)")
            full_name = (user.get("full_name") or "").strip() or user.get("username", "")
            role_fmt = user.get("role", "").replace("_", " ").title()
            info = f"{full_name} • {role_fmt} - Pass: {password_str}"
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
                current_user_role=self.app.current_user["role"],
                old_username=user["username"],
                new_username=nu,
                new_password=np,
                new_fullname=nf,
                new_role=nr
            )
            if success:
                if self.app.current_user and self.app.current_user.get("username") == user["username"]:
                    self.app.current_user["username"] = nu
                    self.app.current_user["full_name"] = nf
                    if np:
                        self.app.current_user["password_plain"] = np
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

    def _guardar_reporte_config(self) -> None:
        empresa = self.report_empresa_entry.get().strip()
        sitio = self.report_sitio_entry.get().strip()
        try:
            sla_val = float(self.report_sla_entry.get().replace(",", "."))
            if not (0.0 <= sla_val <= 100.0):
                raise ValueError()
        except ValueError:
            ToastNotification(
                self.app, "Error", "El SLA objetivo debe ser un porcentaje numérico válido entre 0 y 100.", color="red"
            )
            return

        incluir_cctv = bool(self.report_incluir_cctv_switch.get())

        if hasattr(self.app, "save_reporte_runtime_settings"):
            self.app.save_reporte_runtime_settings(empresa, sitio, sla_val, incluir_cctv)
            ToastNotification(
                self.app,
                "Parámetros Guardados",
                "Configuración de Reporte Ejecutivo actualizada exitosamente.",
                color="green",
            )

    def _guardar_intervalo_ping(self) -> None:
        try:
            val = int(self.ping_interval_entry.get().strip())
            if val < 1:
                val = 1
                self.ping_interval_entry.delete(0, "end")
                self.ping_interval_entry.insert(0, "1")
            self.app.ping_interval = val
            if hasattr(self.app, "monitor_tab"):
                self.app.monitor_tab.guardar_equipos()
            elif hasattr(self.app, "guardar_equipos"):
                self.app.guardar_equipos()
            ToastNotification(
                self.app,
                "Configuración Guardada",
                f"Intervalo de ping actualizado a {val} segundos.",
                color="green",
            )
        except ValueError:
            ToastNotification(
                self.app,
                "Error",
                "El intervalo de ping debe ser un número entero mayor o igual a 1.",
                color="red",
            )
