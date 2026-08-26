import tkinter as tk
from tkinter import ttk
import customtkinter
import re

class OsintTab:
    def __init__(self, master_app, parent_frame):
        self.master_app = master_app
        self.parent = parent_frame
        
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(2, weight=1) # El contenedor de resultados se expande
        
        self.module_results = {}
        self.build_header()
        self.build_modules_grid()
        self.apply_role_restrictions()
        self.build_search_and_results()
        
    def apply_role_restrictions(self):
        role = self.master_app.current_user.get("role", "user")
        if role in ["user", "operador"]:
            allowed_modules = ["PPU", "RUT"]
            for code, btn in self._module_buttons.items():
                if code not in allowed_modules:
                    btn.configure(state="disabled", fg_color="#2a2d33", text_color="#5c6370")

    def build_header(self):
        header_frame = customtkinter.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        lbl_title = customtkinter.CTkLabel(
            header_frame, text="SUITE DE CONSULTAS AVANZADAS", 
            font=("Consolas", 24, "bold"), text_color="#00d9ff"
        )
        lbl_title.pack(anchor="w")
        
    def build_modules_grid(self):
        modules_container = customtkinter.CTkFrame(self.parent, fg_color="transparent")
        modules_container.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Registro de todos los botones por código de módulo
        self._module_buttons = {}  # code -> CTkButton
        self._BTN_DEFAULT  = "#1f6aa5"   # azul CTk por defecto
        self._BTN_ACTIVE   = "#00b4d8"   # cian brillante = activo
        self._BTN_HOVER_A  = "#0096c7"   # hover activo
        self._BTN_HOVER_D  = "#144870"   # hover inactivo

        # --- Inteligencia Local ---
        lbl_local = customtkinter.CTkLabel(
            modules_container,
            text="INTELIGENCIA LOCAL (CHILE) & CLIMA",
            font=("Consolas", 12, "bold"), text_color="#555555"
        )
        lbl_local.pack(anchor="w", pady=(0, 5))

        local_frame = customtkinter.CTkFrame(modules_container, fg_color="transparent")
        local_frame.pack(anchor="w", fill="x", pady=(0, 20))

        local_modules = [
            ("\U0001f697 PPU", "PPU"),
            ("\U0001faaa RUT", "RUT"),
            ("\U0001f4cd Geografía y Clima", "GeoClima"),
        ]
        for text, code in local_modules:
            btn = customtkinter.CTkButton(
                local_frame, text=text, width=130,
                fg_color=self._BTN_DEFAULT,
                hover_color=self._BTN_HOVER_D,
                command=lambda c=code: self.set_module(c)
            )
            btn.pack(side="left", padx=(0, 10))
            self._module_buttons[code] = btn

        # --- Inteligencia de Red ---
        lbl_net = customtkinter.CTkLabel(
            modules_container,
            text="INTELIGENCIA DE RED, AMENAZAS & AMBIENTE DIGITAL (12 MÓDULOS)",
            font=("Consolas", 12, "bold"), text_color="#555555"
        )
        lbl_net.pack(anchor="w", pady=(0, 5))

        net_frame = customtkinter.CTkFrame(modules_container, fg_color="transparent")
        net_frame.pack(anchor="w", fill="x")

        net_modules = [
            ("\U0001f511 Fugas de Datos", "Fugas"),
            ("\U0001f6e1 Reputación IP", "Reputacion"),
            ("\U0001f3e2 Infraestructura", "Infraestructura"),
            ("\U0001f4dc Registro WHOIS", "WHOIS"),
            ("\U0001f4cd IP Geo", "IPGeo"),
            ("\U0001f310 DNS", "DNS"),
            ("\U0001f50d Analizador Web", "Web"),
            ("\U0001f50c Puertos", "Puertos"),
            ("\U0001f578 Subdominios", "Subdominios"),
            ("\u2709 Email", "Email"),
            ("\U0001f6e4 Traceroute", "Traceroute"),
            ("\U0001f6e1 Escáner LAN", "LAN"),
        ]

        for i, (text, code) in enumerate(net_modules):
            row = i // 6
            col = i % 6
            btn = customtkinter.CTkButton(
                net_frame, text=text, width=140,
                fg_color=self._BTN_DEFAULT,
                hover_color=self._BTN_HOVER_D,
                command=lambda c=code: self.set_module(c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self._module_buttons[code] = btn
            
    def build_search_and_results(self):
        # ── CONTENEDOR PRINCIPAL ──────────────────────────────────────────
        search_container = customtkinter.CTkFrame(
            self.parent,
            fg_color="#0d1117",
            border_color="#21262d",
            border_width=1,
            corner_radius=12
        )
        search_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        search_container.grid_rowconfigure(1, weight=1)
        search_container.grid_columnconfigure(0, weight=1)

        # ── BARRA DE BÚSQUEDA ──────────────────────────────────────────────
        bar_frame = customtkinter.CTkFrame(search_container, fg_color="transparent")
        bar_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        bar_frame.grid_columnconfigure(0, weight=1)

        # Frame interior de búsqueda con fondo y borde
        entry_wrapper = customtkinter.CTkFrame(
            bar_frame,
            fg_color="#161b22",
            border_color="#30363d",
            border_width=1,
            corner_radius=8,
            height=46
        )
        entry_wrapper.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        entry_wrapper.grid_propagate(False)
        entry_wrapper.grid_columnconfigure(1, weight=1)

        # Icono lupa dentro del entry
        lbl_icon = tk.Label(
            entry_wrapper,
            text="🔍",
            bg="#161b22",
            fg="#58a6ff",
            font=("Segoe UI", 14),
            padx=10
        )
        lbl_icon.grid(row=0, column=0, sticky="w")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_typing)

        self._entry_tk = tk.Entry(
            entry_wrapper,
            textvariable=self.search_var,
            bg="#161b22",
            fg="#e6edf3",
            insertbackground="#58a6ff",
            relief="flat",
            font=("Consolas", 13),
            bd=0,
            highlightthickness=0
        )
        self._entry_tk.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 10))
        self._entry_tk.bind("<Return>", lambda e: self.ejecutar_consulta())
        self._entry_tk.bind("<FocusIn>", self._on_entry_focus_in)
        self._entry_tk.bind("<FocusOut>", self._on_entry_focus_out)

        # Placeholder label superpuesto (solución definitiva)
        self._placeholder_lbl = tk.Label(
            entry_wrapper,
            text="Seleccione un módulo...",
            bg="#161b22",
            fg="#484f58",
            font=("Consolas", 13),
            anchor="w",
            cursor="xterm"
        )
        self._placeholder_lbl.grid(row=0, column=1, sticky="ew", pady=8, padx=(0, 10))
        self._placeholder_lbl.bind("<Button-1>", lambda e: self._entry_tk.focus_set())
        self._placeholder_visible = True

        # Botón BUSCAR
        self.btn_search = tk.Button(
            bar_frame,
            text="  BUSCAR",
            bg="#238636",
            fg="#ffffff",
            activebackground="#2ea043",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
            command=self.ejecutar_consulta
        )
        self.btn_search.grid(row=0, column=1, sticky="e")

        # ── TABLA DE RESULTADOS PREMIUM ────────────────────────────────────
        self._build_results_table(search_container)

        self.active_module = None
        self.current_placeholder = "Seleccione un módulo..."
        self.set_module("WHOIS")

    def _build_results_table(self, parent):
        """Construye la tabla de resultados usando CTkScrollableFrame para soportar saltos de linea y colores."""
        self.results_container = customtkinter.CTkScrollableFrame(
            parent, fg_color="#0d1117", corner_radius=0
        )
        self.results_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        
        self.headers_frame = customtkinter.CTkFrame(self.results_container, fg_color="#161b22", corner_radius=0, height=40)
        self.headers_frame.pack(fill="x", pady=(0, 5))
        self.headers_frame.pack_propagate(False)
        
        self.rows_frame = customtkinter.CTkFrame(self.results_container, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True)
        
        self.tree = None # Para mantener compatibilidad con on_search_typing si es necesario

    def _on_entry_focus_in(self, event):
        """Oculta el placeholder al recibir foco."""
        if self._placeholder_visible:
            self._placeholder_lbl.grid_remove()
            self._placeholder_visible = False

    def _on_entry_focus_out(self, event):
        """Muestra el placeholder si el campo está vacío."""
        if not self.search_var.get():
            self._placeholder_lbl.grid()
            self._placeholder_visible = True

    # Mantener compatibilidad con código anterior que llame estos métodos
    def _clear_placeholder(self, event): pass
    def _restore_placeholder(self, event): pass

    def _set_active_button(self, active_code):
        """Resalta el botón activo y restaura todos los demás."""
        for code, btn in getattr(self, "_module_buttons", {}).items():
            if code == active_code:
                btn.configure(fg_color=self._BTN_ACTIVE, hover_color=self._BTN_HOVER_A)
            else:
                btn.configure(fg_color=self._BTN_DEFAULT, hover_color=self._BTN_HOVER_D)

    def set_module(self, module_code):
        self.active_module = module_code
        self._set_active_button(module_code)  # ← Resaltar botón activo
        
        if module_code == "LAN":
            self.btn_search.configure(text="  ESCANEAR")
        else:
            self.btn_search.configure(text="  BUSCAR")

        if module_code == "PPU":
            cols   = ("Patente", "Tipo", "Marca", "Modelo", "RUT Propietario", "Nro. Motor", "Año", "Propietario", "Riesgo", "Impacto")
            widths = (90, 80, 90, 140, 110, 120, 50, 200, 100, 220)
            placeholder = "Ingrese Patente del Vehículo  (ej. TYCC70)..."
        elif module_code == "RUT":
            cols   = ("RUT", "Nombre Completo", "Riesgo", "Impacto")
            widths = (160, 490, 100, 250)
            placeholder = "Ingrese RUT Chileno  (ej. 12.345.678-9)..."
        elif module_code == "GeoClima":
            cols   = ("Ciudad / Región", "Indicador", "Valor", "Riesgo", "Impacto")
            widths = (150, 150, 250, 100, 350)
            placeholder = "Ingrese ciudad o región  (ej. Santiago)..."
        elif module_code == "Email":
            cols   = ("Email", "Campo", "Valor", "Riesgo", "Impacto")
            widths = (200, 150, 250, 120, 280)
            placeholder = "Ingrese dirección de correo electrónico..."
        elif module_code in ("WHOIS", "Web", "Subdominios", "Reputacion"):
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Ingrese dominio o URL  (ej. anvic.cl)..."
        elif module_code == "LAN":
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Deje vacío para red local o ingrese subred (ej. 192.168.1.0/24)..."
        elif module_code in ("IPGeo", "DNS", "Infraestructura"):
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Ingrese dirección IP o dominio..."
        elif module_code == "Puertos":
            cols   = ("Puerto", "Estado", "Servicio", "Riesgo", "Impacto")
            widths = (80, 100, 370, 100, 350)
            placeholder = "Ingrese IP o dominio objetivo..."
        elif module_code == "Traceroute":
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Ingrese IP o dominio para traceroute..."
        elif module_code == "Fugas":
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Ingrese email o dominio para buscar fugas..."
        else:
            cols   = ("Parámetro", "Valor", "Detalle", "Riesgo", "Impacto")
            widths = (150, 180, 320, 100, 250)
            placeholder = "Ingrese parámetro de búsqueda..."

        # Actualizar placeholder label superpuesto
        self.current_placeholder = placeholder
        self._placeholder_lbl.configure(text=placeholder)

        # Limpiar el campo de búsqueda
        self.search_var.set("")
        # Mostrar placeholder si el entry está vacío y sin foco
        self._placeholder_lbl.grid()
        self._placeholder_visible = True

        # Reconfigurar columnas de la cabecera
        for widget in self.headers_frame.winfo_children():
            widget.destroy()
        
        self._current_widths = widths
        
        for i, col in enumerate(cols):
            lbl = customtkinter.CTkLabel(
                self.headers_frame, text=col, font=("Segoe UI", 12, "bold"), text_color="#58a6ff", anchor="w"
            )
            lbl.pack(side="left", padx=10, fill="x")
            lbl.configure(width=widths[i])

        # Limpiar tabla y cargar caché del módulo
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
            
        cached = self.module_results.get(module_code, [])
        self._render_rows(cached)

    def _render_rows(self, results):
        for idx, res in enumerate(results):
            bg_color = "#0d1117" if idx % 2 == 0 else "#111820"
            row_frame = customtkinter.CTkFrame(self.rows_frame, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", pady=1)
            
            for i, val in enumerate(res):
                width = self._current_widths[i] if i < len(self._current_widths) else 150
                text_val = str(val)
                text_color = "#c9d1d9"
                
                # Extraer circulos y aplicar colores a texto
                if "SANO" in text_val or "🟢" in text_val:
                    text_color = "#2ea043"
                    text_val = text_val.replace("🟢", "●")
                elif "PELIGROSO" in text_val or "🔴" in text_val:
                    text_color = "#f85149"
                    text_val = text_val.replace("🔴", "●")
                elif "SOSPECHOSO" in text_val or "🟡" in text_val:
                    text_color = "#d29922"
                    text_val = text_val.replace("🟡", "●")
                elif "Error" in text_val or "❌" in text_val or "⚠" in text_val:
                    text_color = "#f85149"
                    
                lbl = customtkinter.CTkLabel(
                    row_frame, text=text_val, font=("Consolas", 11), text_color=text_color,
                    anchor="w", justify="left", wraplength=width - 10
                )
                lbl.pack(side="left", padx=10, fill="y", pady=5)
                lbl.configure(width=width)

    def on_search_typing(self, *args):
        val = self.search_var.get()
        # Si el usuario empieza a escribir, asegurar que el placeholder esté oculto
        if val and self._placeholder_visible:
            self._placeholder_lbl.grid_remove()
            self._placeholder_visible = False
        elif not val and not self._entry_tk.focus_get() == self._entry_tk:
            if not self._placeholder_visible:
                self._placeholder_lbl.grid()
                self._placeholder_visible = True

        if self.active_module == "RUT":
            raw   = val
            clean = re.sub(r'[^0-9kK]', '', raw).upper()
            if len(clean) >= 2:
                body = clean[:-1]
                dv   = clean[-1]
                try:
                    formatted = "{:,}".format(int(body)).replace(",", ".") + f"-{dv}"
                    if raw != formatted:
                        self.search_var.set(formatted)
                        self._entry_tk.icursor("end")
                except ValueError:
                    pass

    def copy_to_clipboard(self, event=None):
        pass # To be implemented or omitted since it's a custom frame now

    def ejecutar_consulta(self):
        query = self.search_var.get().strip()
        
        # Permitir consultas vacías si el módulo es Escáner LAN
        if (not query or self._placeholder_visible) and self.active_module != "LAN":
            return
            
        if self._placeholder_visible:
            self.search_var.set("")
            query = ""
            self._placeholder_lbl.grid_remove()
            self._placeholder_visible = False

        # Indicador "Buscando..." en tabla
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        loading_lbl = customtkinter.CTkLabel(
            self.rows_frame, text="⏳ Consultando...", font=("Consolas", 12), text_color="#58a6ff"
        )
        loading_lbl.pack(pady=20)

        import threading
        threading.Thread(
            target=self._fetch_api_data,
            args=(self.active_module, query),
            daemon=True
        ).start()

    def _evaluate_risk(self, module, row):
        """Evalúa el riesgo de un resultado OSINT y retorna (semaforo, impacto)."""
        semaforo = "[ ⚪ N/A ]"
        impacto = "Sin análisis"
        
        if len(row) < 3:
            return semaforo, impacto
            
        param = str(row[1]).lower()
        valor = str(row[2]).lower()
        
        if "error" in param or "error" in valor or "timeout" in valor:
            return "[ 🟡 SOSPECHOSO ]", "Fallo en la consulta. Posible bloqueo, caída del servicio o rate limit."
            
        if module == "Fugas":
            if "sí" in valor or "filtrado" in param:
                return "[ 🔴 PELIGROSO ]", "Credenciales comprometidas. Riesgo crítico de acceso no autorizado. Forzar rotación de contraseñas."
            elif "no encontrado" in valor:
                return "[ 🟢 SANO ]", "No se encontraron registros en brechas de datos conocidas."
            else:
                return "[ 🟡 SOSPECHOSO ]", "Brecha histórica detectada. Verificar si la contraseña fue cambiada."
                
        elif module == "Puertos":
            puerto = str(row[0]).strip()
            puertos_criticos = ["22", "23", "3389", "445", "139"]
            puertos_web = ["80", "443", "8080", "8443"]
            if puerto in puertos_criticos and "open" in valor:
                return "[ 🔴 PELIGROSO ]", f"Puerto de gestión ({puerto}) expuesto. Vulnerable a ataques de fuerza bruta o ransomware."
            elif puerto in puertos_web and "open" in valor:
                if puerto == "80":
                    return "[ 🟡 SOSPECHOSO ]", "Puerto HTTP abierto. Posible tráfico sin cifrar."
                return "[ 🟢 SANO ]", "Puerto web estándar expuesto (Esperado)."
            elif "closed" in valor or "filtered" in valor:
                return "[ 🟢 SANO ]", "Puerto cerrado o protegido por firewall."
                
        elif module == "Email":
            if param == "disposable" and "true" in valor:
                return "[ 🔴 PELIGROSO ]", "Correo temporal/desechable detectado. Alto riesgo de fraude o cuenta falsa."
            elif param == "format" and "false" in valor:
                return "[ 🔴 PELIGROSO ]", "Formato de correo inválido."
            elif param == "dns" and "false" in valor:
                return "[ 🟡 SOSPECHOSO ]", "El dominio no tiene registros MX (no puede recibir correos)."
            elif param == "dns" and "true" in valor:
                return "[ 🟢 SANO ]", "Dominio válido con capacidad de recibir correos."
                
        elif module == "WHOIS":
            if "creation date" in param or "created" in param:
                import datetime
                import re
                match = re.search(r'\d{4}-\d{2}-\d{2}', valor)
                if match:
                    try:
                        cdate = datetime.datetime.strptime(match.group(), "%Y-%m-%d")
                        days = (datetime.datetime.now() - cdate).days
                        if days < 30:
                            return "[ 🔴 PELIGROSO ]", f"Dominio creado hace {days} días. Alto riesgo de ser infraestructura de phishing."
                        elif days < 180:
                            return "[ 🟡 SOSPECHOSO ]", f"Dominio relativamente nuevo ({days} días)."
                        else:
                            return "[ 🟢 SANO ]", "Dominio con antigüedad y reputación establecida."
                    except:
                        pass
                        
        elif module == "Reputacion":
            if "dominio compartido" in param:
                return "[ 🟡 SOSPECHOSO ]", "IP compartida con múltiples dominios. Posible hosting barato o comprometido."
                
        elif module == "Infraestructura":
            if "asn" in param:
                if "aws" in valor or "amazon" in valor or "digitalocean" in valor or "azure" in valor:
                    return "[ 🟡 SOSPECHOSO ]", "IP pertenece a un proveedor Cloud. Común en despliegues de ataque (VPS)."
                else:
                    return "[ 🟢 SANO ]", "ASN válido."
                    
        elif module == "Analizador Web":
            if "server" in param:
                return "[ ⚪ INFO ]", f"Servidor detectado: {valor}"
            elif "strict-transport-security" not in str(row).lower() and param == "headers":
                return "[ 🟡 SOSPECHOSO ]", "Falta cabecera HSTS. Riesgo de downgrade a HTTP."
                
        elif module == "DNS":
            return "[ 🟢 SANO ]", "Registro DNS válido encontrado."
            
        elif module == "LAN":
            if "activo" in valor:
                return "[ ⚪ INFO ]", "Host detectado activo en la red local."
                
        return "[ ⚪ INFO ]", "Dato nominal o informativo."

    def _fetch_api_data(self, module, query):
        import requests
        results = []
        try:
            if module == "WHOIS":
                # Consulta WHOIS directa vía socket TCP puerto 43 (protocolo nativo)
                import socket
                domain = query.lower().strip()
                # Determinar servidor WHOIS según TLD
                tld = domain.split(".")[-1].lower() if "." in domain else "com"
                whois_servers = {
                    "cl": "whois.nic.cl", "com": "whois.verisign-grs.com",
                    "net": "whois.verisign-grs.com", "org": "whois.pir.org",
                    "io": "whois.nic.io", "co": "whois.nic.co",
                    "ar": "whois.nic.ar", "pe": "whois.nic.pe",
                    "br": "whois.registro.br", "mx": "whois.mx",
                }
                server = whois_servers.get(tld, "whois.iana.org")
                try:
                    with socket.create_connection((server, 43), timeout=10) as s:
                        s.send(f"{domain}\r\n".encode())
                        raw = b""
                        while True:
                            chunk = s.recv(4096)
                            if not chunk:
                                break
                            raw += chunk
                    lines = raw.decode("utf-8", errors="replace").splitlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("%") and ":" in line:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                results.append((domain, parts[0].strip(), parts[1].strip()))
                except Exception as e_sock:
                    # Fallback RDAP IANA
                    try:
                        r2 = requests.get(f"https://rdap.iana.org/domain/{tld}", timeout=8)
                        if r2.status_code == 200:
                            d2 = r2.json()
                            results.append((domain, "WHOIS Server TLD", d2.get("port43", server)))
                            for event in d2.get("events", []):
                                results.append((domain, event.get("eventAction", ""), event.get("eventDate", "")))
                        else:
                            results.append((domain, "Error", f"Socket: {e_sock} | RDAP HTTP {r2.status_code}"))
                    except Exception as e2:
                        results.append((domain, "Error", str(e2)))
            elif module == "IPGeo":
                import socket
                target_ip = query.strip()
                if target_ip:
                    try:
                        # Si es un dominio, resolver a IP
                        target_ip = socket.gethostbyname(target_ip)
                        if target_ip != query.strip():
                            results.append(("Host", "IP Resuelta", target_ip))
                    except:
                        pass
                
                url = f"https://ipinfo.io/{target_ip}/json" if target_ip else "https://ipinfo.io/json"
                r = requests.get(url, timeout=10, headers={"Accept": "application/json"})
                
                if r.status_code == 200:
                    d = r.json()
                    if d.get("bogon"):
                        results.append((target_ip, "Red Local", "La IP ingresada es privada o reservada (bogon)."))
                    else:
                        label_map = {
                            "ip": "IP", "city": "Ciudad", "region": "Región",
                            "country": "País", "loc": "Coordenadas",
                            "org": "Organización / ASN", "postal": "Código Postal",
                            "timezone": "Zona Horaria", "hostname": "Hostname",
                            "anycast": "Anycast"
                        }
                        for k, v in d.items():
                            if k not in ("readme", "bogon") and isinstance(v, (str, int, float, bool)):
                                results.append((query or "Propia", label_map.get(k, k.capitalize()), str(v)))
                else:
                    results.append((query, "Error API", f"HTTP {r.status_code} - {r.text[:50]}"))
            elif module == "DNS":
                r = requests.get(f"https://api.hackertarget.com/dnslookup/?q={query}", timeout=10)
                lines = r.text.strip().split("\n")
                for line in lines:
                    results.append((query, "Registro DNS", line))
            elif module == "Puertos":
                # Escaneo local de puertos comunes con socket
                import socket
                COMMON_PORTS = {
                    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
                    443: "HTTPS", 445: "SMB", 3306: "MySQL",
                    3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
                    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
                }
                host = query.strip()
                # Resolver hostname a IP si es necesario
                try:
                    ip = socket.gethostbyname(host)
                    results.append(("Host", "IP resuelta", ip))
                except socket.gaierror:
                    results.append(("Error", "No se pudo resolver el host", host))
                    ip = host
                for port, svc in COMMON_PORTS.items():
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1.0)
                        ret = sock.connect_ex((ip, port))
                        sock.close()
                        estado = "ABIERTO ✓" if ret == 0 else "Cerrado"
                        results.append((str(port), estado, svc))
                    except Exception:
                        results.append((str(port), "Error", svc))
            elif module == "Web":
                r = requests.get(f"https://api.hackertarget.com/httpheaders/?q={query}", timeout=10)
                lines = r.text.strip().split("\n")
                for line in lines:
                    results.append((query, "Header HTTP", line))
            elif module == "Traceroute":
                # Traceroute local con subprocess (tracert en Windows)
                import subprocess, platform
                cmd = "tracert" if platform.system() == "Windows" else "traceroute"
                flags = ["-h", "20"] if platform.system() == "Windows" else ["-m", "20"]
                try:
                    proc = subprocess.run(
                        [cmd] + flags + [query.strip()],
                        capture_output=True, text=True, timeout=30,
                        encoding="cp850" if platform.system() == "Windows" else "utf-8"
                    )
                    output = proc.stdout or proc.stderr
                    hop = 0
                    for line in output.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        hop += 1
                        results.append((f"Salto {hop}", line[:50], line[50:] if len(line) > 50 else ""))
                except subprocess.TimeoutExpired:
                    results.append(("Timeout", "Traceroute excedió 30 seg", ""))
                except FileNotFoundError:
                    results.append(("Error", f"Comando '{cmd}' no disponible en el sistema", ""))
            elif module == "Email":
                # disify.com: API pública gratuita de validación de emails
                r = requests.get(
                    f"https://disify.com/api/email/{query}",
                    timeout=10, headers={"Accept": "application/json"}
                )
                if r.status_code == 200:
                    d = r.json()
                    label_map = {
                        "format": "Formato válido", "domain": "Dominio",
                        "disposable": "Email desechable", "dns": "Registros DNS ok",
                        "whitelist": "En lista blanca"
                    }
                    for k, v in d.items():
                        if isinstance(v, bool):
                            display = "✓ Sí" if v else "✗ No"
                        else:
                            display = str(v)
                        results.append((query, label_map.get(k, k), display))
                else:
                    results.append((query, "Error API Email", f"HTTP {r.status_code}"))
            elif module == "Subdominios":
                r = requests.get(f"https://api.hackertarget.com/hostsearch/?q={query}", timeout=10)
                lines = r.text.strip().split("\n")
                for line in lines[:20]:
                    results.append((query, "Subdominio", line))
            elif module == "Reputacion":
                r = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={query}", timeout=10)
                lines = r.text.strip().split("\n")
                for line in lines[:10]:
                    results.append((query, "Dominio Compartido", line))
            elif module == "Infraestructura":
                r = requests.get(f"https://api.hackertarget.com/aslookup/?q={query}", timeout=10)
                lines = r.text.strip().split("\n")
                for line in lines:
                    results.append((query, "ASN / BGP", line))
            elif module == "Fugas":
                # LeakCheck.io API pública (sin key para búsqueda básica por email)
                try:
                    rlc = requests.get(
                        f"https://leakcheck.io/api/public?check={query}",
                        timeout=10, headers={"User-Agent": "AnvicSentinel/2.2"}
                    )
                    if rlc.status_code == 200:
                        d = rlc.json()
                        found = d.get("found", False)
                        results.append((query, "Filtrado en brechas", "SÍ (⚠)" if found else "NO encontrado (✔)"))
                        for src in d.get("sources", [])[:10]:
                            name = src.get("name", "?") if isinstance(src, dict) else str(src)
                            date = src.get("date", "") if isinstance(src, dict) else ""
                            results.append((query, "Brecha", f"{name}  {date}".strip()))
                    else:
                        results.append((query, "LeakCheck", f"HTTP {rlc.status_code} - verifique manualmente en haveibeenpwned.com"))
                except Exception as e:
                    results.append((query, "Fugas", f"Error al consultar: {e}"))
            elif module == "LAN":
                # Escaneo real de red local con ICMP (ping sweep)
                import socket, subprocess, platform, ipaddress
                # Intentar detectar la subred local
                try:
                    local_ip = socket.gethostbyname(socket.gethostname())
                    net = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                    results.append(("Red local", "Subred escaneada", str(net)))
                except Exception:
                    net_str = query.strip() or "192.168.1.0/24"
                    try:
                        net = ipaddress.IPv4Network(net_str, strict=False)
                    except Exception:
                        results.append(("Error", "Subred inválida", net_str))
                        net = None

                if net:
                    cmd = "ping"
                    is_win = platform.system() == "Windows"
                    active_hosts = []
                    
                    # 1. Ping sweep rápido (multithreaded para no congelar 50s)
                    import concurrent.futures
                    
                    def check_host(h):
                        flags = ["-n", "1", "-w", "100"] if is_win else ["-c", "1", "-W", "1"]
                        try:
                            # Ocultar ventana de cmd en Windows
                            si = None
                            if is_win:
                                si = subprocess.STARTUPINFO()
                                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            proc = subprocess.run([cmd] + flags + [str(h)], capture_output=True, timeout=2, startupinfo=si)
                            if proc.returncode == 0:
                                return str(h)
                        except:
                            pass
                        return None
                        
                    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                        # Escanear primeros 254 hosts reales
                        hosts_to_scan = list(net.hosts())[:254]
                        futures = [executor.submit(check_host, h) for h in hosts_to_scan]
                        for f in concurrent.futures.as_completed(futures):
                            if f.result():
                                active_hosts.append(f.result())
                                
                    # 2. Obtener tabla ARP para MACs
                    mac_table = {}
                    try:
                        si = None
                        if is_win:
                            si = subprocess.STARTUPINFO()
                            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        arp_proc = subprocess.run(["arp", "-a"], capture_output=True, text=True, startupinfo=si)
                        import re
                        for line in arp_proc.stdout.splitlines():
                            parts = line.split()
                            if len(parts) >= 2:
                                ip_str = parts[0].strip()
                                mac_str = parts[1].strip()
                                if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_str):
                                    mac_table[ip_str] = mac_str
                    except:
                        pass
                        
                    # 3. Analizar puertos y armar resultados
                    for host in active_hosts:
                        mac = mac_table.get(host, "MAC oculta/desconocida")
                        try:
                            hostname = socket.gethostbyaddr(host)[0]
                        except:
                            hostname = "Sin nombre"
                            
                        # Port scan rápido
                        open_ports = []
                        for port in [80, 443, 445, 3389]:
                            try:
                                with socket.create_connection((host, port), timeout=0.2):
                                    open_ports.append(str(port))
                            except:
                                pass
                                
                        detalle = f"MAC: {mac} | Hostname: {hostname}"
                        if open_ports:
                            detalle += f" | Puertos abiertos: {', '.join(open_ports)}"
                            
                        results.append((host, "ACTIVO ✓", detalle))
                        
                    if not active_hosts:
                        results.append((str(net), "Sin respuesta", "No se detectaron hosts activos en la subred"))
            elif module == "GeoClima":
                r = requests.get(f"https://wttr.in/{query}?format=j1&lang=es", timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    condicion = d["current_condition"][0]
                    clima_desc = condicion.get("lang_es", condicion.get("weatherDesc"))[0]["value"]
                    results.append((query, "Temperatura", f"{condicion['temp_C']} °C"))
                    results.append((query, "Humedad",     f"{condicion['humidity']} %"))
                    results.append((query, "Clima",       clima_desc))
            elif module == "RUT":
                from core.scraper_rut import scraper_rut
                data = scraper_rut(query)
                results.extend(data)
            elif module == "PPU":
                from core.scraper_ppu import scraper_ppu
                data = scraper_ppu(query)
                results.extend(data)
        except Exception as e:
            results.append((query if query else "Consulta", "❌ Error", str(e)))

        if not results:
            results.append(("⚠ Sin resultados", "La consulta no devolvió información.", ""))

        processed_results = []
        for row in results:
            semaforo, impacto = self._evaluate_risk(module, row)
            processed_results.append(tuple(list(row) + [semaforo, impacto]))
            
        self.parent.after(0, self._update_tree, module, processed_results)

    def _update_tree(self, module, results):
        self.module_results[module] = results
        if self.active_module != module:
            return
            
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
            
        self._render_rows(results)

        if hasattr(self.master_app, "send_alert"):
            self.master_app.send_alert(f"✓ Consulta {module} completada", "green")

