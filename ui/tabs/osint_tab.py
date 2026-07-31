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
        self.build_search_and_results()
        
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
        """Construye la tabla de resultados con estilo premium usando ttk.Treeview."""
        # Frame contenedor de la tabla
        table_outer = tk.Frame(parent, bg="#0d1117")
        table_outer.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        table_outer.grid_rowconfigure(1, weight=1)
        table_outer.grid_columnconfigure(0, weight=1)

        # Separador decorativo
        sep = tk.Frame(table_outer, bg="#21262d", height=1)
        sep.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 0))

        # Estilo ttk premium
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Premium.Treeview",
            background="#0d1117",
            foreground="#c9d1d9",
            rowheight=34,
            fieldbackground="#0d1117",
            borderwidth=0,
            font=("Consolas", 11)
        )
        style.configure(
            "Premium.Treeview.Heading",
            background="#161b22",
            foreground="#58a6ff",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padding=(10, 8)
        )
        style.map(
            "Premium.Treeview",
            background=[("selected", "#1f4d7a")],
            foreground=[("selected", "#e6edf3")]
        )
        style.map(
            "Premium.Treeview.Heading",
            background=[("active", "#1c2128")]
        )
        style.layout("Premium.Treeview", [
            ("Premium.Treeview.treearea", {"sticky": "nswe"})
        ])

        # ── Scrollbars elegantes oscuras ─────────────────────────────────
        # Usamos tk.Scrollbar nativo para poder aplicar colores de forma directa
        # sin depender del tema ttk que las pinta blancas en Windows.
        scrollbar_style = ttk.Style()
        for name in (
            "Dark.Vertical.TScrollbar",
            "Dark.Horizontal.TScrollbar",
        ):
            orient = "Vertical" if "Vertical" in name else "Horizontal"
            scrollbar_style.configure(
                name,
                background="#21262d",
                darkcolor="#21262d",
                lightcolor="#21262d",
                troughcolor="#0d1117",
                bordercolor="#0d1117",
                arrowcolor="#30363d",
                relief="flat",
            )
            scrollbar_style.map(
                name,
                background=[("active", "#30363d"), ("pressed", "#388bfd")],
                arrowcolor=[("active", "#58a6ff")],
            )
            scrollbar_style.layout(name, [
                (f"{orient}.Scrollbar.trough", {"sticky": "nswe", "children": [
                    (f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                ]})
            ])

        self.tree = ttk.Treeview(
            table_outer,
            style="Premium.Treeview",
            selectmode="browse"
        )

        v_scroll = ttk.Scrollbar(
            table_outer,
            orient="vertical",
            command=self.tree.yview,
            style="Dark.Vertical.TScrollbar"
        )
        h_scroll = ttk.Scrollbar(
            table_outer,
            orient="horizontal",
            command=self.tree.xview,
            style="Dark.Horizontal.TScrollbar"
        )
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        v_scroll.grid(row=1, column=1, sticky="ns",  padx=(2, 0))
        h_scroll.grid(row=2, column=0, sticky="ew",  pady=(2, 0))

        # Colores alternos de filas
        self.tree.tag_configure("odd",  background="#0d1117", foreground="#c9d1d9")
        self.tree.tag_configure("even", background="#111820", foreground="#c9d1d9")
        self.tree.tag_configure("error", background="#1f0a0a", foreground="#f85149")
        self.tree.tag_configure("ok",   background="#0a1f0a", foreground="#3fb950")

        self.tree.bind("<Control-c>", self.copy_to_clipboard)

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

        if module_code == "PPU":
            cols   = ("Patente", "Tipo", "Marca", "Modelo", "RUT Propietario", "Nro. Motor", "Año", "Propietario")
            widths = (90, 90, 100, 160, 130, 150, 60, 220)
            placeholder = "Ingrese Patente del Vehículo  (ej. TYCC70)..."
        elif module_code == "RUT":
            cols   = ("RUT", "Nombre Completo")
            widths = (160, 590)
            placeholder = "Ingrese RUT Chileno  (ej. 12.345.678-9)..."
        elif module_code == "GeoClima":
            cols   = ("Ciudad / Región", "Indicador", "Valor")
            widths = (180, 180, 390)
            placeholder = "Ingrese ciudad o región  (ej. Santiago)..."
        elif module_code == "Email":
            cols   = ("Email", "Campo", "Valor")
            widths = (240, 200, 310)
            placeholder = "Ingrese dirección de correo electrónico..."
        elif module_code in ("WHOIS", "Web", "Subdominios", "Reputacion", "LAN"):
            cols   = ("Parámetro", "Valor", "Detalle")
            widths = (170, 200, 380)
            placeholder = "Ingrese dominio o URL  (ej. anvic.cl)..."
        elif module_code in ("IPGeo", "DNS", "Infraestructura"):
            cols   = ("Parámetro", "Valor", "Detalle")
            widths = (170, 200, 380)
            placeholder = "Ingrese dirección IP o dominio..."
        elif module_code == "Puertos":
            cols   = ("Puerto", "Estado", "Servicio")
            widths = (100, 120, 530)
            placeholder = "Ingrese IP o dominio objetivo..."
        elif module_code == "Traceroute":
            cols   = ("Parámetro", "Valor", "Detalle")
            widths = (170, 200, 380)
            placeholder = "Ingrese IP o dominio para traceroute..."
        elif module_code == "Fugas":
            cols   = ("Parámetro", "Valor", "Detalle")
            widths = (170, 200, 380)
            placeholder = "Ingrese email o dominio para buscar fugas..."
        else:
            cols   = ("Parámetro", "Valor", "Detalle")
            widths = (150, 250, 350)
            placeholder = "Ingrese parámetro de búsqueda..."

        # Actualizar placeholder label superpuesto
        self.current_placeholder = placeholder
        self._placeholder_lbl.configure(text=placeholder)

        # Limpiar el campo de búsqueda
        self.search_var.set("")
        # Mostrar placeholder si el entry está vacío y sin foco
        self._placeholder_lbl.grid()
        self._placeholder_visible = True

        # Reconfigurar columnas de la tabla
        self.tree["columns"] = cols
        self.tree["show"] = "headings"
        for i, col in enumerate(cols):
            self.tree.heading(col, text=f"  {col}", anchor="w")
            self.tree.column(col, width=widths[i], anchor="w", stretch=(i == len(cols) - 1))

        # Limpiar tabla y cargar caché del módulo
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, res in enumerate(self.module_results.get(module_code, [])):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=res, tags=(tag,))

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
        selected_items = self.tree.selection()
        if selected_items:
            clipboard_text = ""
            for item in selected_items:
                values = self.tree.item(item, "values")
                clipboard_text += "\t".join(map(str, values)) + "\n"
            self.parent.clipboard_clear()
            self.parent.clipboard_append(clipboard_text.strip())
            if hasattr(self.master_app, "send_alert"):
                self.master_app.send_alert("Copiado al portapapeles ✓", "green")

    def ejecutar_consulta(self):
        query = self.search_var.get().strip()
        if not query or self._placeholder_visible:
            return

        # Indicador "Buscando..." en tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Determinar número de columnas para el placeholder de carga
        ncols = len(self.tree["columns"])
        loading_vals = ("⏳ Consultando...",) + ("",) * (ncols - 1)
        self.tree.insert("", "end", values=loading_vals, tags=("even",))

        import threading
        threading.Thread(
            target=self._fetch_api_data,
            args=(self.active_module, query),
            daemon=True
        ).start()

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
                # ipinfo.io: 50k req/mes gratis, sin key necesaria
                r = requests.get(f"https://ipinfo.io/{query}/json", timeout=10,
                                 headers={"Accept": "application/json"})
                if r.status_code == 200:
                    d = r.json()
                    label_map = {
                        "ip": "IP", "city": "Ciudad", "region": "Región",
                        "country": "País", "loc": "Coordenadas",
                        "org": "Organización / ASN", "postal": "Código Postal",
                        "timezone": "Zona Horaria", "hostname": "Hostname"
                    }
                    for k, v in d.items():
                        if k not in ("readme",) and isinstance(v, (str, int, float)):
                            results.append((query, label_map.get(k, k), str(v)))
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
                    for host in list(net.hosts())[:50]:  # Limitar a 50 hosts
                        try:
                            flags = ["-n", "1", "-w", "200"] if is_win else ["-c", "1", "-W", "1"]
                            proc = subprocess.run(
                                [cmd] + flags + [str(host)],
                                capture_output=True, timeout=3
                            )
                            if proc.returncode == 0:
                                try:
                                    hostname = socket.gethostbyaddr(str(host))[0]
                                except Exception:
                                    hostname = "Sin nombre"
                                results.append((str(host), "ACTIVO ✓", hostname))
                        except Exception:
                            pass
                    if not results or (len(results) == 1 and "escaneada" in str(results[0])):
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
            results.append((f"❌ Error", str(e), ""))

        if not results:
            results.append(("⚠ Sin resultados", "La consulta no devolvió información.", ""))

        self.parent.after(0, self._update_tree, module, results)

    def _update_tree(self, module, results):
        self.module_results[module] = results
        if self.active_module != module:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, res in enumerate(results):
            tag = "even" if idx % 2 == 0 else "odd"
            # Detectar fila de error para colorearla en rojo
            first = str(res[0]) if res else ""
            if first.startswith("❌") or first.startswith("⚠"):
                tag = "error"
            self.tree.insert("", "end", values=res, tags=(tag,))

        if hasattr(self.master_app, "send_alert"):
            self.master_app.send_alert(f"✓ Consulta {module} completada", "green")

