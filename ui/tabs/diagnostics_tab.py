# ui/tabs/diagnostics_tab.py
"""
Pestaña de Diagnóstico de Argos Guard (Rediseño UI/UX Nivel Dios).
Organizada mediante Sub-pestañas para mejorar la armonía visual y usabilidad.
"""

import json
import os
import threading
import customtkinter
from tkinter import messagebox

from services.network_tools import NetworkTools
from ui.components.toast import ToastNotification
from utils.paths import get_base_path
from config.settings import SERVICES_WHITELIST_FILE


class DiagnosticsTab:
    """Controlador de la pestaña 'Diagnóstico' optimizado con CTkTabview interno."""

    DEFAULT_SYSTEM_SERVICES = [
        {
            "name": "Spooler",
            "display_name": "Cola de impresion",
            "description": "Servicio de Cola de Impresion",
        },
        {
            "name": "w32time",
            "display_name": "Hora de Windows",
            "description": "Servicio de Hora de Windows",
        },
        {
            "name": "BITS",
            "display_name": "Transferencia inteligente",
            "description": "Servicio de Transferencia Inteligente en Segundo Plano",
        },
        {
            "name": "WinDefend",
            "display_name": "Microsoft Defender",
            "description": "Antivirus de Microsoft Defender",
        },
    ]

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self.active_diag_process = None
        self.service_widgets: dict = {}
        self.monitored_target_map: dict[str, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # ── Contenedor de Sub-pestañas ───────────────────────────────────
        self.sub_tabs = customtkinter.CTkTabview(self.frame, fg_color="transparent")
        self.sub_tabs.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        tab_local = self.sub_tabs.add("Estado del Puesto")
        tab_network = self.sub_tabs.add("Red e Instalaciones")

        self._build_local_panel(tab_local)
        self._build_network_panel(tab_network)

        # Actualizar info local al iniciar
        self.app.after(1000, self._refresh_local_info)

    # ─────────────────────────────────────────────────────────────────────
    # PANEL 1: CONTROL LOCAL (Sistema, Servicios, Reparación)
    # ─────────────────────────────────────────────────────────────────────
    def _build_local_panel(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        # 1.1 Info del Sistema
        self._build_local_info_card(master, row=0, col=0)
        # 1.2 Herramientas de Reparación
        self._build_repair_tools_card(master, row=0, col=1)
        # 1.3 Gestor de Servicios (Abajo)
        self._build_services_card(master, row=1, col=0, columnspan=2)

    def _build_local_info_card(self, master, row, col) -> None:
        frame = customtkinter.CTkFrame(master)
        frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        customtkinter.CTkLabel(
            frame, text="Resumen del Host",
            font=("Arial", 16, "bold"), text_color="#00d9ff"
        ).pack(pady=(15, 10))

        container = customtkinter.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20)

        self.lbl_hostname = customtkinter.CTkLabel(container, text="Host: ...", anchor="w")
        self.lbl_hostname.pack(fill="x", pady=2)
        self.lbl_ip = customtkinter.CTkLabel(container, text="IP: ...", anchor="w", font=("Arial", 13, "bold"))
        self.lbl_ip.pack(fill="x", pady=2)
        self.lbl_mac = customtkinter.CTkLabel(container, text="MAC: ...", anchor="w")
        self.lbl_mac.pack(fill="x", pady=2)
        self.lbl_gateway = customtkinter.CTkLabel(container, text="Gateway: ...", anchor="w")
        self.lbl_gateway.pack(fill="x", pady=2)
        self.lbl_dns = customtkinter.CTkLabel(container, text="DNS: ...", anchor="w")
        self.lbl_dns.pack(fill="x", pady=2)

        customtkinter.CTkButton(
            frame, text="Actualizar", height=28, width=100, 
            command=self._refresh_local_info
        ).pack(pady=15)

    def _build_repair_tools_card(self, master, row, col) -> None:
        frame = customtkinter.CTkFrame(master)
        frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        customtkinter.CTkLabel(
            frame, text="Recuperacion Tecnica",
            font=("Arial", 16, "bold"), text_color="#ff9f1c"
        ).pack(pady=(15, 10))

        btn_cfg = [
            ("🧹 Limpiar Caché DNS", "flushdns", "#2B2B2B"),
            ("🔄 Renovar IP Local", "renew", "#2B2B2B"),
            ("⚠️ Desconectar IP", "release", "#3a1c1c"),
        ]
        for txt, cmd, color in btn_cfg:
            customtkinter.CTkButton(
                frame, text=txt, fg_color=color, height=32,
                command=lambda c=cmd: self._run_maintenance(c)
            ).pack(fill="x", padx=30, pady=8)

    def _build_services_card(self, master, row, col, columnspan=1) -> None:
        frame = customtkinter.CTkFrame(master)
        frame.grid(row=row, column=col, columnspan=columnspan, padx=15, pady=15, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        header = customtkinter.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        customtkinter.CTkLabel(header, text="Servicios del Sistema", font=("Arial", 16, "bold")).pack(side="left")
        customtkinter.CTkButton(header, text="🔄", width=30, height=30, command=self._refresh_all_services).pack(side="right")

        add_frame = customtkinter.CTkFrame(frame, fg_color="#262626")
        add_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        add_frame.grid_columnconfigure(0, weight=2)
        add_frame.grid_columnconfigure(1, weight=2)
        add_frame.grid_columnconfigure(2, weight=3)

        self.service_name_entry = customtkinter.CTkEntry(
            add_frame,
            placeholder_text="Nombre real del servicio Windows",
        )
        self.service_name_entry.grid(row=0, column=0, padx=(10, 6), pady=10, sticky="ew")

        self.service_display_entry = customtkinter.CTkEntry(
            add_frame,
            placeholder_text="Nombre visible (opcional)",
        )
        self.service_display_entry.grid(row=0, column=1, padx=6, pady=10, sticky="ew")

        self.service_description_entry = customtkinter.CTkEntry(
            add_frame,
            placeholder_text="Descripcion (opcional)",
        )
        self.service_description_entry.grid(row=0, column=2, padx=6, pady=10, sticky="ew")

        customtkinter.CTkButton(
            add_frame,
            text="Agregar servicio",
            width=130,
            command=self._add_service_entry,
        ).grid(row=0, column=3, padx=(6, 10), pady=10)

        customtkinter.CTkLabel(
            add_frame,
            text="Mantén la base por defecto y agrega servicios del cliente o de la instalación manualmente.",
            text_color="#B8BDC7",
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="ew")

        self.services_container = customtkinter.CTkScrollableFrame(frame, height=180)
        self.services_container.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self._load_services()

    # ─────────────────────────────────────────────────────────────────────
    # PANEL 2: ANÁLISIS DE RED (Diag, ARP, Netstat)
    # ─────────────────────────────────────────────────────────────────────
    def _build_network_panel(self, master) -> None:
        master.grid_columnconfigure(0, weight=3) # Consola
        master.grid_columnconfigure(1, weight=1) # Auditoría
        master.grid_rowconfigure(0, weight=1)

        # 2.1 Consola de Diagnóstico Avanzado
        self._build_diag_console(master)
        # 2.2 Panel Lateral de Auditoría (ARP/Netstat)
        self._build_audit_sidebar(master)

    def _build_diag_console(self, master) -> None:
        frame = customtkinter.CTkFrame(master)
        frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(7, weight=1)

        customtkinter.CTkLabel(
            frame, text="Resumen de Red",
            font=("Arial", 16, "bold"), text_color="#51cf66"
        ).grid(row=0, column=0, pady=15)

        picker = customtkinter.CTkFrame(frame, fg_color="transparent")
        picker.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")

        customtkinter.CTkLabel(
            picker, text="Equipo monitoreado:", font=("Arial", 12, "bold")
        ).pack(side="left", padx=(0, 10))

        self.monitored_target_option = customtkinter.CTkOptionMenu(
            picker,
            values=["Sin equipos cargados"],
            width=280,
        )
        self.monitored_target_option.pack(side="left", fill="x", expand=True, padx=(0, 8))

        customtkinter.CTkButton(
            picker, text="Usar", width=70, command=self._apply_selected_target
        ).pack(side="left", padx=(0, 6))

        customtkinter.CTkButton(
            picker, text="Refrescar", width=90, command=self._refresh_monitored_targets
        ).pack(side="left")

        controls = customtkinter.CTkFrame(frame, fg_color="transparent")
        controls.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.diag_target_entry = customtkinter.CTkEntry(
            controls, placeholder_text="IP, dominio o URL"
        )
        self.diag_target_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.diag_ports_entry = customtkinter.CTkEntry(
            controls, width=170, placeholder_text="Puertos (80,443,554)"
        )
        self.diag_ports_entry.pack(side="left", padx=(0, 10))
        self.diag_ports_entry.insert(0, "80,443,554,8000")

        self.diag_action_buttons = []

        for tool in ["Ping", "Tracert", "Lookup"]:
            btn = customtkinter.CTkButton(
                controls, text=tool, width=70,
                command=lambda t=tool.lower(): self._run_diag(t)
            )
            btn.pack(side="left", padx=3)
            setattr(self, f"btn_{tool.lower()}", btn)
            self.diag_action_buttons.append(btn)

        utility_controls = customtkinter.CTkFrame(frame, fg_color="transparent")
        utility_controls.grid(row=3, column=0, padx=20, pady=(0, 2), sticky="ew")

        self.btn_http = customtkinter.CTkButton(
            utility_controls, text="HTTP", width=70, command=lambda: self._run_http_check("http")
        )
        self.btn_http.pack(side="left", padx=(0, 6))
        self.diag_action_buttons.append(self.btn_http)

        self.btn_https = customtkinter.CTkButton(
            utility_controls, text="HTTPS", width=70, command=lambda: self._run_http_check("https")
        )
        self.btn_https.pack(side="left", padx=6)
        self.diag_action_buttons.append(self.btn_https)

        self.btn_ports = customtkinter.CTkButton(
            utility_controls, text="Puertos", width=80, command=self._run_port_scan
        )
        self.btn_ports.pack(side="left", padx=6)
        self.diag_action_buttons.append(self.btn_ports)

        self.btn_stop = customtkinter.CTkButton(
            utility_controls,
            text="Detener prueba activa",
            width=170,
            fg_color="#c92a2a",
            hover_color="#a61e1e",
            state="disabled",
            command=self._stop_diag,
        )
        self.btn_stop.pack(side="left", padx=(12, 6))

        self.btn_copy = customtkinter.CTkButton(
            utility_controls, text="Copiar", width=80, fg_color="#495057",
            command=self._copy_console
        )
        self.btn_copy.pack(side="left", padx=(6, 0))

        customtkinter.CTkLabel(
            frame,
            text="El boton rojo se activa cuando hay un Ping, Tracert o Lookup en curso.",
            text_color="#ff8787",
            anchor="w",
        ).grid(row=4, column=0, padx=22, pady=(0, 5), sticky="ew")

        snmp_controls = customtkinter.CTkFrame(frame, fg_color="transparent")
        snmp_controls.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")

        self.diag_snmp_community_entry = customtkinter.CTkEntry(
            snmp_controls, width=140, placeholder_text="Community SNMP"
        )
        self.diag_snmp_community_entry.pack(side="left", padx=(0, 10))
        self.diag_snmp_community_entry.insert(0, "public")

        self.diag_snmp_oid_entry = customtkinter.CTkEntry(
            snmp_controls, placeholder_text="OID o alias (sysName, sysDescr, sysUpTime...)"
        )
        self.diag_snmp_oid_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.diag_snmp_oid_entry.insert(0, "sysName")

        self.btn_snmp = customtkinter.CTkButton(
            snmp_controls, text="SNMP", width=80, command=self._run_snmp_check
        )
        self.btn_snmp.pack(side="left")
        self.diag_action_buttons.append(self.btn_snmp)

        ssh_controls = customtkinter.CTkFrame(frame, fg_color="transparent")
        ssh_controls.grid(row=6, column=0, padx=20, pady=(0, 5), sticky="ew")

        self.diag_ssh_user_entry = customtkinter.CTkEntry(
            ssh_controls, width=130, placeholder_text="Usuario SSH"
        )
        self.diag_ssh_user_entry.pack(side="left", padx=(0, 10))

        self.diag_ssh_password_entry = customtkinter.CTkEntry(
            ssh_controls, width=140, placeholder_text="Contrasena SSH", show="*"
        )
        self.diag_ssh_password_entry.pack(side="left", padx=(0, 10))

        self.diag_ssh_command_entry = customtkinter.CTkEntry(
            ssh_controls, placeholder_text="Comando SSH"
        )
        self.diag_ssh_command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.diag_ssh_command_entry.insert(0, "hostname")

        self.btn_ssh = customtkinter.CTkButton(
            ssh_controls, text="SSH", width=80, command=self._run_ssh_check
        )
        self.btn_ssh.pack(side="left")
        self.diag_action_buttons.append(self.btn_ssh)

        self.diag_console = customtkinter.CTkTextbox(frame, font=("Courier New", 12), wrap="none")
        self.diag_console.grid(row=7, column=0, padx=20, pady=15, sticky="nsew")
        self.diag_console.configure(state="disabled")
        self._refresh_monitored_targets()

    def _build_audit_sidebar(self, master) -> None:
        frame = customtkinter.CTkFrame(master, width=300)
        frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(frame, text="Auditoria Tecnica", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=15)

        sub_audit = customtkinter.CTkTabview(frame, fg_color="#222")
        sub_audit.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        tab_arp = sub_audit.add("Inventario ARP")
        tab_net = sub_audit.add("Sesiones de Red")

        # ARP Tab
        tab_arp.grid_rowconfigure(1, weight=1)
        tab_arp.grid_columnconfigure(0, weight=1)
        customtkinter.CTkButton(tab_arp, text="Actualizar ARP", command=self._display_arp).grid(row=0, column=0, pady=10)
        self.arp_console = customtkinter.CTkTextbox(tab_arp, font=("Courier New", 11), state="disabled", wrap="none")
        self.arp_console.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Netstat Tab
        tab_net.grid_rowconfigure(1, weight=1)
        tab_net.grid_columnconfigure(0, weight=1)
        customtkinter.CTkButton(tab_net, text="Actualizar Sesiones", command=self._display_netstat).grid(row=0, column=0, pady=10)
        self.netstat_console = customtkinter.CTkTextbox(tab_net, font=("Courier New", 11), state="disabled", wrap="none")
        self.netstat_console.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    # ─────────────────────────────────────────────────────────────────────
    # Lógica de Soporte (Mantenida del original pero adaptada)
    # ─────────────────────────────────────────────────────────────────────

    def _refresh_local_info(self) -> None:
        def _fetch():
            info = NetworkTools.get_local_info()
            self.app.after(0, lambda: self._update_info_labels(info))
        threading.Thread(target=_fetch, daemon=True).start()

    def _update_info_labels(self, info: dict) -> None:
        self.lbl_hostname.configure(text=f"🖥️ Host: {info['hostname']}")
        self.lbl_ip.configure(text=f"🌐 IP:   {info['ip']}")
        self.lbl_mac.configure(text=f"🆔 MAC:  {info['mac']}")
        self.lbl_gateway.configure(text=f"🚪 GW:   {info['gateway']}")
        dns_str = ", ".join(info["dns"]) if info["dns"] else "No detectado"
        self.lbl_dns.configure(text=f"🌍 DNS:  {dns_str}")

    def _run_maintenance(self, tool_type: str) -> None:
        msgs = {"flushdns": "¿Limpiar caché DNS?", "renew": "¿Renovar IP?", "release": "¡Esto cortará la red! ¿Seguro?"}
        if not messagebox.askyesno("Confirmar", msgs.get(tool_type, "¿Ejecutar?")): return
        ToastNotification(self.app, "Ejecutando...", "Espere...", color="blue")
        threading.Thread(target=lambda: self._on_maintenance_done(*NetworkTools.execute_maintenance(tool_type), tool_type), daemon=True).start()

    def _on_maintenance_done(self, success, output, tool_type) -> None:
        color = "green" if success else "red"
        msg = f"{tool_type} completado." if success else f"Error: {output[:50]}"
        self.app.after(0, lambda: ToastNotification(self.app, "Resultado", msg, color=color))
        if success and tool_type in ["renew", "release"]: self.app.after(2000, self._refresh_local_info)

    def _run_diag(self, tool: str) -> None:
        if self.active_diag_process: return
        target = self.diag_target_entry.get().strip()
        if not target: return
        self._reset_console(f">>> ANALIZANDO: {target} [{tool.upper()}]\n\n")
        self._set_diag_buttons_state("disabled")
        self.btn_stop.configure(state="normal")
        NetworkTools.run_diagnostic(
            tool if tool != "lookup" else "nslookup",
            target,
            self._diag_callback,
            enable_geolocation=bool(getattr(self.app, "enable_external_geolocation", False)),
        )

    def _diag_callback(self, data, proc=None) -> None:
        if proc: self.active_diag_process = proc
        elif data == "PROCESS_FINISHED": self.app.after(0, self._on_diag_complete)
        elif data: self.app.after(0, self._insert_console, data)

    def _insert_console(self, text) -> None:
        self.diag_console.configure(state="normal")
        self.diag_console.insert("end", text)
        self.diag_console.see("end")
        self.diag_console.configure(state="disabled")

    def _on_diag_complete(self) -> None:
        self.active_diag_process = None
        self._set_diag_buttons_state("normal")
        self.btn_stop.configure(state="disabled")

    def _stop_diag(self) -> None:
        if self.active_diag_process:
            NetworkTools.stop_diagnostic(self.active_diag_process)
            self._insert_console("\n!!! ANÁLISIS DETENIDO POR USUARIO !!!\n")
            self._on_diag_complete()

    def _set_diag_buttons_state(self, state: str) -> None:
        for button in getattr(self, "diag_action_buttons", []):
            button.configure(state=state)

    def _reset_console(self, header: str) -> None:
        self.diag_console.configure(state="normal")
        self.diag_console.delete("1.0", "end")
        self.diag_console.insert("end", header)
        self.diag_console.configure(state="disabled")

    def _run_http_check(self, scheme: str) -> None:
        if self.active_diag_process:
            return
        target = self.diag_target_entry.get().strip()
        if not target:
            return

        self._reset_console(f">>> CHEQUEO {scheme.upper()}: {target}\n\n")
        self._set_diag_buttons_state("disabled")
        self.btn_stop.configure(state="disabled")

        def _worker():
            ok, data = NetworkTools.check_http_endpoint(
                target,
                scheme=scheme,
                timeout=5,
                verify_tls=getattr(self.app, "verify_tls_certificates", False),
            )
            self.app.after(0, lambda: self._on_http_check_complete(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_http_check_complete(self, ok: bool, data: dict) -> None:
        if ok:
            lines = [
                f"URL final: {data.get('url', '-')}\n",
                f"Estado HTTP: {data.get('status_code', '-')}\n",
                f"Tiempo: {data.get('elapsed_ms', '-')} ms\n",
                f"Servidor: {data.get('server') or 'No informado'}\n",
                f"Contenido: {data.get('content_type') or 'No informado'}\n",
            ]
            title = data.get("title")
            if title:
                lines.append(f"Titulo: {title}\n")
            self._insert_console("".join(lines))
        else:
            self._insert_console(
                f"Error en chequeo {data.get('url', '')}:\n{data.get('error', 'Sin detalle')}\n"
            )

        self._set_diag_buttons_state("normal")

    def _run_port_scan(self) -> None:
        if self.active_diag_process:
            return
        target = self.diag_target_entry.get().strip()
        port_spec = self.diag_ports_entry.get().strip()
        if not target or not port_spec:
            return

        self._reset_console(
            f">>> ESCANEO CONTROLADO: {target}\nPuertos: {port_spec}\n\n"
        )
        self._set_diag_buttons_state("disabled")
        self.btn_stop.configure(state="disabled")

        def _worker():
            ok, data = NetworkTools.scan_ports(
                target,
                port_spec,
                timeout=1.0,
                max_ports=16,
            )
            self.app.after(0, lambda: self._on_port_scan_complete(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_port_scan_complete(self, ok: bool, data) -> None:
        if ok:
            open_count = sum(1 for entry in data if entry["open"])
            header = f"Puertos revisados: {len(data)} | Abiertos: {open_count}\n\n"
            lines = [header]
            for entry in data:
                state = "ABIERTO" if entry["open"] else "cerrado"
                service = f" ({entry['service']})" if entry["service"] else ""
                lines.append(
                    f"{entry['port']:>5}  {state:<8}  {entry['latency_ms']:>6} ms{service}\n"
                )
            self._insert_console("".join(lines))
        else:
            self._insert_console(f"Error de escaneo:\n{data}\n")

        self._set_diag_buttons_state("normal")

    def _run_snmp_check(self) -> None:
        if self.active_diag_process:
            return
        target = self.diag_target_entry.get().strip()
        community = self.diag_snmp_community_entry.get().strip() or "public"
        oid = self.diag_snmp_oid_entry.get().strip() or "sysName"
        if not target:
            return

        self._reset_console(
            f">>> CHEQUEO SNMP: {target}\nCommunity: {community}\nOID: {oid}\n\n"
        )
        self._set_diag_buttons_state("disabled")
        self.btn_stop.configure(state="disabled")

        def _worker():
            ok, data = NetworkTools.snmp_get(
                target,
                community=community,
                oid=oid,
                port=161,
                timeout=2,
                retries=0,
            )
            self.app.after(0, lambda: self._on_snmp_complete(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_snmp_complete(self, ok: bool, data: dict) -> None:
        if ok:
            lines = [
                f"Host: {data.get('host', '-')}\n",
                f"OID consultado: {data.get('oid', '-')}\n",
                f"Community: {data.get('community', '-')}\n\n",
            ]
            for entry in data.get("entries", []):
                lines.append(f"{entry['oid']} = {entry['value']}\n")
            self._insert_console("".join(lines))
        else:
            self._insert_console(
                f"Error SNMP para {data.get('host', '')}:\n{data.get('error', 'Sin detalle')}\n"
            )

        self._set_diag_buttons_state("normal")

    def _run_ssh_check(self) -> None:
        if self.active_diag_process:
            return
        target = self.diag_target_entry.get().strip()
        username = self.diag_ssh_user_entry.get().strip()
        password = self.diag_ssh_password_entry.get()
        command = self.diag_ssh_command_entry.get().strip() or "hostname"
        if not target:
            return

        self._reset_console(
            f">>> CHEQUEO SSH: {target}\nUsuario: {username or '-'}\nComando: {command}\n\n"
        )
        self._set_diag_buttons_state("disabled")
        self.btn_stop.configure(state="disabled")

        def _worker():
            ok, data = NetworkTools.ssh_run_command(
                target,
                username=username,
                password=password,
                command=command,
                port=22,
                timeout=5,
                verify_host_key=bool(getattr(self.app, "verify_ssh_host_key", True)),
                trust_on_first_use=bool(getattr(self.app, "ssh_trust_on_first_use", False)),
                known_hosts_path=getattr(self.app, "ssh_known_hosts_path", ""),
            )
            self.app.after(0, lambda: self._on_ssh_complete(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ssh_complete(self, ok: bool, data: dict) -> None:
        if ok:
            lines = [
                f"Host: {data.get('host', '-')}\n",
                f"Puerto: {data.get('port', '-')}\n",
                f"Usuario: {data.get('username', '-')}\n",
                f"Comando: {data.get('command', '-')}\n",
                f"Modo host key: {data.get('host_key_mode', '-')}\n",
                f"Exit status: {data.get('exit_status', '-')}\n\n",
            ]
            if data.get("host_key_type"):
                lines.append(f"Host key: {data.get('host_key_type')} | {data.get('host_key_fingerprint', '-')}\n\n")
            stdout_text = data.get("stdout") or "(sin salida stdout)"
            stderr_text = data.get("stderr") or ""
            lines.append("STDOUT:\n")
            lines.append(f"{stdout_text}\n")
            if stderr_text:
                lines.append("\nSTDERR:\n")
                lines.append(f"{stderr_text}\n")
            self._insert_console("".join(lines))
        else:
            self._insert_console(
                f"Error SSH para {data.get('host', '')}:\n{data.get('error', 'Sin detalle')}\n"
            )

        self._set_diag_buttons_state("normal")

    def _refresh_monitored_targets(self) -> None:
        equipos = getattr(self.app, "equipos_a_monitorear", [])
        self.monitored_target_map = {
            f"{eq['label']} [{eq['ip']}]": eq["ip"] for eq in equipos
        }
        values = list(self.monitored_target_map.keys()) or ["Sin equipos cargados"]
        self.monitored_target_option.configure(values=values)
        self.monitored_target_option.set(values[0])

    def _apply_selected_target(self) -> None:
        selection = self.monitored_target_option.get()
        ip = self.monitored_target_map.get(selection)
        if not ip:
            return
        self.diag_target_entry.delete(0, "end")
        self.diag_target_entry.insert(0, ip)

    def _copy_console(self) -> None:
        content = self.diag_console.get("1.0", "end").strip()
        if not content:
            ToastNotification(self.app, "Diagnóstico", "No hay salida para copiar", color="yellow")
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(content)
        ToastNotification(self.app, "Diagnóstico", "Salida copiada al portapapeles", color="green")

    def _display_arp(self) -> None:
        self.arp_console.configure(state="normal"); self.arp_console.delete("1.0", "end")
        success, data = NetworkTools.get_arp_table()
        if success:
            for e in data: self.arp_console.insert("end", f"{e['ip']:<15} {e['mac']}\n")
        self.arp_console.configure(state="disabled")

    def _display_netstat(self) -> None:
        self.netstat_console.configure(state="normal"); self.netstat_console.delete("1.0", "end")
        success, data = NetworkTools.get_netstat()
        if success:
            for c in data: self.netstat_console.insert("end", f"{c['proto']:<5} {c['foreign_addr']}\n")
        self.netstat_console.configure(state="disabled")

    def _services_config_path(self) -> str:
        return os.path.join(get_base_path(), SERVICES_WHITELIST_FILE)

    def _read_services_config(self) -> dict:
        path = self._services_config_path()
        if not os.path.exists(path):
            return {"services": [dict(service) for service in self.DEFAULT_SYSTEM_SERVICES]}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            services = [self._normalize_service_entry(item) for item in data.get("services", [])]
            if not services:
                services = [dict(service) for service in self.DEFAULT_SYSTEM_SERVICES]
            return {"services": services}
        except Exception:
            return {"services": [dict(service) for service in self.DEFAULT_SYSTEM_SERVICES]}

    def _write_services_config(self, data: dict) -> None:
        with open(self._services_config_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    @staticmethod
    def _normalize_service_entry(entry: dict) -> dict:
        service_name = (entry.get("name") or "").strip()
        return {
            "name": service_name,
            "display_name": (entry.get("display_name") or service_name).strip(),
            "description": (entry.get("description") or "").strip(),
        }

    def _add_service_entry(self) -> None:
        service_name = self.service_name_entry.get().strip()
        display_name = self.service_display_entry.get().strip() or service_name
        description = self.service_description_entry.get().strip()

        if not service_name:
            ToastNotification(
                self.app,
                "Servicios del Sistema",
                "Debes ingresar el nombre real del servicio Windows.",
                color="yellow",
            )
            return

        data = self._read_services_config()
        existing = {item.get("name", "").strip().lower() for item in data.get("services", [])}
        if service_name.lower() in existing:
            ToastNotification(
                self.app,
                "Servicios del Sistema",
                "Ese servicio ya esta registrado.",
                color="yellow",
            )
            return

        data["services"].append(
            {
                "name": service_name,
                "display_name": display_name,
                "description": description,
            }
        )
        self._write_services_config(data)

        self.service_name_entry.delete(0, "end")
        self.service_display_entry.delete(0, "end")
        self.service_description_entry.delete(0, "end")
        self._load_services()

        ToastNotification(
            self.app,
            "Servicios del Sistema",
            f"Servicio '{display_name}' agregado correctamente.",
            color="green",
        )

    def _remove_service_entry(self, service_name: str) -> None:
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Deseas quitar '{service_name}' de la lista de Servicios del Sistema?",
        ):
            return

        data = self._read_services_config()
        data["services"] = [
            item for item in data.get("services", [])
            if item.get("name", "").strip().lower() != service_name.strip().lower()
        ]
        self._write_services_config(data)
        self._load_services()
        ToastNotification(
            self.app,
            "Servicios del Sistema",
            f"Servicio '{service_name}' eliminado de la lista.",
            color="green",
        )

    def _load_services(self) -> None:
        try:
            data = self._read_services_config()
            for s in data.get("services", []):
                name = s["name"]
                row = customtkinter.CTkFrame(self.services_container, fg_color="transparent")
                row.pack(fill="x", pady=2)
                customtkinter.CTkLabel(row, text=name, font=("Arial", 12, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
                status_lbl = customtkinter.CTkLabel(row, text="...", width=70)
                status_lbl.pack(side="left", padx=5)
                customtkinter.CTkButton(row, text="▶", width=30, command=lambda n=name: self._svc_act(n, "start")).pack(side="left")
                customtkinter.CTkButton(row, text="■", width=30, fg_color="#ff6b6b", command=lambda n=name: self._svc_act(n, "stop")).pack(side="left", padx=5)
                self.service_widgets[name] = {"status_label": status_lbl}
            self.app.after(500, self._refresh_all_services)
        except Exception: pass

    def _refresh_all_services(self) -> None:
        for name in self.service_widgets:
            threading.Thread(target=self._fetch_svc_status, args=(name,), daemon=True).start()

    def _fetch_svc_status(self, name) -> None:
        _, state = NetworkTools.get_service_status(name)
        self.app.after(0, lambda: self.service_widgets[name]["status_label"].configure(
            text=state, text_color={"Corriendo": "#51cf66", "Detenido": "#ff6b6b"}.get(state, "gray")
        ))

    def _svc_act(self, name, action) -> None:
        if not messagebox.askyesno("Confirmar", f"¿{action} '{name}'?"): return
        def _run():
            NetworkTools.manage_service(name, action)
            self.app.after(2000, lambda: self._fetch_svc_status(name))
        threading.Thread(target=_run, daemon=True).start()
