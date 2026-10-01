# ui/tabs/history_tab.py
"""
Pestaña de Telemetría y Rendimiento de Argos Guard (anteriormente Historial Operacional).
Renderiza métricas avanzadas, KPIs de red, mapa de calor discreto (pastillas redondeadas),
gráficos de latencia con umbrales SLA y tabla de estado con barras de salud embebidas.
"""

from __future__ import annotations

import datetime
import threading
import tkinter as tk
import customtkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyBboxPatch
import matplotlib.dates as mdates
import numpy as np
from config.branding import APP_NAME


class HistoryTab:
    """Controlador de la pestaña 'Telemetría' de Argos Guard con soporte para desacople multimonitor."""

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self.contenedor_actual = tab_frame
        self.popout_window = None
        self.es_popout = False
        self.telemetria_frame = None

        self.filtro_host = "Todos los Equipos"
        self.modo_heatmap = "Semanal (7D x 24h)"
        self.opt_semanal = None
        self.opt_equipo = None
        self.seg_heatmap = None
        self._refresh_job = None
        self._worker_busy = False
        self._pending_refresh = False
        self._gauges_pool = {}
        self._table_rows_pool = {}

    def inicializar(self, contenedor=None, es_popout: bool = False) -> None:
        """Construye todos los componentes de la interfaz de telemetría."""
        self.es_popout = es_popout
        self.contenedor_actual = contenedor if contenedor is not None else self.frame
        self._gauges_pool = {}
        self._table_rows_pool = {}

        for w in self.contenedor_actual.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        self.telemetria_frame = customtkinter.CTkScrollableFrame(self.contenedor_actual, fg_color="#18181B")
        self.telemetria_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # ── 1. Barra Superior de Título y Controles ────────────────────────────
        header_frame = customtkinter.CTkFrame(self.telemetria_frame, fg_color="#242427", corner_radius=8)
        header_frame.pack(fill="x", padx=10, pady=(10, 8))

        title_sub_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        title_sub_frame.pack(side="left", padx=12, pady=10)

        titulo_texto = "📡 Telemetría de Red [Monitor Secundario]" if es_popout else "📡 Telemetría de Red & Rendimiento Operacional"
        customtkinter.CTkLabel(
            title_sub_frame,
            text=titulo_texto,
            font=("Arial", 18, "bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w")

        self.lbl_subtitulo = customtkinter.CTkLabel(
            title_sub_frame,
            text="Supervisión en tiempo real de latencia, SLA de disponibilidad y microcortes de enlace",
            font=("Arial", 11),
            text_color="#94A3B8",
        )
        self.lbl_subtitulo.pack(anchor="w")

        # Controles a la derecha
        controls_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right", padx=12, pady=10)

        # Botón Desacoplar / Reacoplar
        if not es_popout:
            self.btn_popout = customtkinter.CTkButton(
                controls_frame,
                text="⧉ Desacoplar",
                width=110,
                font=("Arial", 12, "bold"),
                fg_color="#0D9488",
                hover_color="#0F766E",
                command=self.desacoplar_pantalla,
            )
            self.btn_popout.pack(side="left", padx=5)
        else:
            self.btn_popout = customtkinter.CTkButton(
                controls_frame,
                text="📥 Reacoplar",
                width=110,
                font=("Arial", 12, "bold"),
                fg_color="#D97706",
                hover_color="#B45309",
                command=self.reacoplar_pantalla,
            )
            self.btn_popout.pack(side="left", padx=5)

        # Dropdown de hosts
        equipos_nombres = ["Todos los Equipos"] + [eq.get("label", eq.get("ip")) for eq in getattr(self.app, "equipos_a_monitorear", [])]
        self.opt_host = customtkinter.CTkOptionMenu(
            controls_frame,
            values=equipos_nombres,
            command=self._on_host_change,
            width=165,
            fg_color="#334155",
            button_color="#475569",
        )
        self.opt_host.set(self.filtro_host)
        self.opt_host.pack(side="left", padx=5)

        # Selector Semanal (Dropdown con opciones 24h / Turno)
        semanal_opciones = ["Semanal (7D x 24h)", "Semanal (7D x Turno)"]
        self.opt_semanal = customtkinter.CTkOptionMenu(
            controls_frame,
            values=semanal_opciones,
            command=self._on_semanal_change,
            width=175,
            fg_color="#0284C7" if "Semanal" in self.modo_heatmap else "#334155",
            button_color="#0369A1" if "Semanal" in self.modo_heatmap else "#475569",
        )
        if "Semanal" in self.modo_heatmap:
            self.opt_semanal.set(self.modo_heatmap)
        else:
            self.opt_semanal.set("Semanal (7D x 24h)")
        self.opt_semanal.pack(side="left", padx=5)

        # Selector Por Equipo (Dropdown con opciones 24h / Turno)
        equipo_opciones = ["Por Equipo (24h)", "Por Equipo (Turno)"]
        self.opt_equipo = customtkinter.CTkOptionMenu(
            controls_frame,
            values=equipo_opciones,
            command=self._on_equipo_change,
            width=170,
            fg_color="#0284C7" if "Por Equipo" in self.modo_heatmap else "#334155",
            button_color="#0369A1" if "Por Equipo" in self.modo_heatmap else "#475569",
        )
        if "Por Equipo" in self.modo_heatmap:
            self.opt_equipo.set(self.modo_heatmap)
        else:
            self.opt_equipo.set("Por Equipo (24h)")
        self.opt_equipo.pack(side="left", padx=5)

        # Botón Refrescar
        customtkinter.CTkButton(
            controls_frame,
            text="🔄 Actualizar",
            width=100,
            font=("Arial", 12, "bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.actualizar_graficos,
        ).pack(side="left", padx=5)

        # ── 2. Ribbon de Tarjetas KPI (Big Stats) ──────────────────────────────
        self.kpi_frame = customtkinter.CTkFrame(self.telemetria_frame, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=10, pady=5)
        for i in range(4):
            self.kpi_frame.grid_columnconfigure(i, weight=1)

        self.kpi_cards = {}
        kpi_defs = [
            ("uptime", "SLA Global (24h)", "100.0%", "#10B981"),
            ("latencia", "Latencia Media", "0.0 ms", "#00D9FF"),
            ("microcortes", "Microcortes Detectados", "0 eventos", "#F59E0B"),
            ("downtime", "Downtime Total", "0s", "#EF4444"),
        ]

        self.kpi_title_labels = {}
        for idx, (kpi_id, title, val_def, color) in enumerate(kpi_defs):
            card = customtkinter.CTkFrame(self.kpi_frame, fg_color="#242427", corner_radius=8)
            card.grid(row=0, column=idx, padx=4, sticky="nsew")

            lbl_title = customtkinter.CTkLabel(
                card, text=title, font=("Arial", 11, "bold"), text_color="#94A3B8"
            )
            lbl_title.pack(anchor="w", padx=12, pady=(8, 2))
            self.kpi_title_labels[kpi_id] = lbl_title

            val_lbl = customtkinter.CTkLabel(
                card, text=val_def, font=("Arial", 20, "bold"), text_color=color
            )
            val_lbl.pack(anchor="w", padx=12, pady=(0, 8))
            self.kpi_cards[kpi_id] = val_lbl

        # ── 3. Gráficos Principales ────────────────────────────────────────────
        self.graficos_frame = customtkinter.CTkFrame(self.telemetria_frame, fg_color="transparent")
        self.graficos_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Panel Latencia con Umbrales SLA y Panel de Estadísticas
        self.frame_latencia = customtkinter.CTkFrame(self.graficos_frame, fg_color="#242427", corner_radius=8)
        self.frame_latencia.pack(fill="both", expand=True, pady=6)

        self.lbl_lat_title = customtkinter.CTkLabel(
            self.frame_latencia,
            text="📈 Comportamiento de Latencia Temporal (Umbral SLA: 100 ms)",
            font=("Arial", 14, "bold"),
            text_color="#F8FAFC",
        )
        self.lbl_lat_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.fig_latencia = Figure(figsize=(8, 2.7), facecolor="#242427", dpi=100)
        self.ax_latencia = self.fig_latencia.add_subplot(111)
        self.ax_latencia.set_facecolor("#18181B")
        self.fig_latencia.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.18)

        self.canvas_latencia = FigureCanvasTkAgg(self.fig_latencia, self.frame_latencia)
        self.canvas_latencia.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=4)

        # Barra inferior de estadísticas del gráfico
        self.lbl_stats_latencia = customtkinter.CTkLabel(
            self.frame_latencia,
            text="Métricas: Mín: --- │ Prom: --- │ P95: --- │ Máx: --- │ Actual: ---",
            font=("Courier New", 11),
            text_color="#94A3B8",
        )
        self.lbl_stats_latencia.pack(anchor="w", padx=12, pady=(0, 6))

        # Panel Heatmap Moderno (Pastillas Redondeadas)
        self.frame_heatmap = customtkinter.CTkFrame(self.graficos_frame, fg_color="#242427", corner_radius=8)
        self.frame_heatmap.pack(fill="both", expand=True, pady=6)

        hm_header_box = customtkinter.CTkFrame(self.frame_heatmap, fg_color="transparent")
        hm_header_box.pack(fill="x", padx=12, pady=(8, 2))

        self.lbl_heatmap_title = customtkinter.CTkLabel(
            hm_header_box,
            text="🗓️ Matriz de Disponibilidad (Mapa de Calor Discreto)",
            font=("Arial", 14, "bold"),
            text_color="#F8FAFC",
        )
        self.lbl_heatmap_title.pack(side="left")

        self.lbl_heatmap_rango = customtkinter.CTkLabel(
            hm_header_box,
            text="Últimos 7 Días",
            font=("Arial", 11),
            text_color="#38BDF8",
        )
        self.lbl_heatmap_rango.pack(side="right")

        self.fig_heatmap = Figure(figsize=(8, 3.2), facecolor="#242427", dpi=100)
        self.ax_heatmap = self.fig_heatmap.add_subplot(111)
        self.ax_heatmap.set_facecolor("#18181B")
        self.fig_heatmap.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.08)

        self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, self.frame_heatmap)
        self.canvas_heatmap.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=4)
        self.canvas_heatmap.mpl_connect("motion_notify_event", self._on_heatmap_hover)

        # ── 4. Matriz de Gauges (Estilo Grafana Datacenter) ────────────────────
        self.frame_gauges = customtkinter.CTkFrame(self.graficos_frame, fg_color="#242427", corner_radius=8)
        self.frame_gauges.pack(fill="x", pady=6)

        customtkinter.CTkLabel(
            self.frame_gauges,
            text="🎯 Disponibilidad y SLA por Dispositivo (Gauges)",
            font=("Arial", 14, "bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.gauges_container = customtkinter.CTkFrame(self.frame_gauges, fg_color="transparent")
        self.gauges_container.pack(fill="x", expand=True, padx=10, pady=(0, 10))

        # ── 5. Tabla de Desglose con Barras de Salud Embebidas ───────────────────
        self.frame_tabla = customtkinter.CTkFrame(self.graficos_frame, fg_color="#242427", corner_radius=8)
        self.frame_tabla.pack(fill="both", expand=True, pady=6)

        customtkinter.CTkLabel(
            self.frame_tabla,
            text="📋 Telemetría Detallada & Diagnóstico por Nodo",
            font=("Arial", 14, "bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.tabla_container = customtkinter.CTkFrame(self.frame_tabla, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Primera actualización
        self.app.after(500, self.actualizar_graficos)

    def _on_host_change(self, selected_host: str) -> None:
        self.filtro_host = selected_host
        self.actualizar_graficos()

    def _on_semanal_change(self, mode: str) -> None:
        self.modo_heatmap = mode
        self._actualizar_estilo_selectores()
        self.actualizar_graficos()

    def _on_equipo_change(self, mode: str) -> None:
        self.modo_heatmap = mode
        self._actualizar_estilo_selectores()
        self.actualizar_graficos()

    def _actualizar_estilo_selectores(self) -> None:
        """Sincroniza visualmente los colores de los dropdowns activo (#0284C7) vs inactivo (#334155)."""
        es_semanal = "Semanal" in self.modo_heatmap
        if hasattr(self, "opt_semanal") and self.opt_semanal and self.opt_semanal.winfo_exists():
            self.opt_semanal.configure(
                fg_color="#0284C7" if es_semanal else "#334155",
                button_color="#0369A1" if es_semanal else "#475569",
            )
        if hasattr(self, "opt_equipo") and self.opt_equipo and self.opt_equipo.winfo_exists():
            self.opt_equipo.configure(
                fg_color="#334155" if es_semanal else "#0284C7",
                button_color="#475569" if es_semanal else "#0369A1",
            )

    def _on_heatmap_mode_change(self, mode: str) -> None:
        """Compatibilidad regresiva para cambios de modo directos."""
        self.modo_heatmap = mode
        if "Semanal" in mode:
            if hasattr(self, "opt_semanal") and self.opt_semanal and self.opt_semanal.winfo_exists():
                self.opt_semanal.set(mode)
        elif "Por Equipo" in mode:
            if hasattr(self, "opt_equipo") and self.opt_equipo and self.opt_equipo.winfo_exists():
                self.opt_equipo.set(mode)
        self._actualizar_estilo_selectores()
        self.actualizar_graficos()

    def _on_heatmap_hover(self, event):
        """Muestra un tooltip flotante interactivo con el nombre completo del equipo, IP y SLA."""
        if not hasattr(self, "annot_hm") or not self.annot_hm:
            return

        if event.inaxes != self.ax_heatmap or event.ydata is None or event.xdata is None:
            if self.annot_hm.get_visible():
                self.annot_hm.set_visible(False)
                self.canvas_heatmap.draw_idle()
            return

        nrows = getattr(self, "_hm_nrows", len(getattr(self, "_hm_dispo", [])))
        ncols = getattr(self, "_hm_ncols", len(getattr(self, "_hm_horas_turno", [])))
        if nrows == 0 or ncols == 0:
            return

        # Despejar el índice de fila r (dado y_pos = (nrows - 1) - r => r = (nrows - 1) - y_pos)
        r_idx = int(round((nrows - 1) - event.ydata))
        c_idx = int(round(event.xdata))

        if r_idx < 0 or r_idx >= nrows or c_idx < 0 or c_idx >= ncols:
            if self.annot_hm.get_visible():
                self.annot_hm.set_visible(False)
                self.canvas_heatmap.draw_idle()
            return

        text = ""
        horas_turno = getattr(self, "_hm_horas_turno", list(range(24)))
        hora_real = horas_turno[c_idx] if 0 <= c_idx < len(horas_turno) else c_idx
        hm_mode = getattr(self, "_hm_mode", "")

        if "Por Equipo" in hm_mode:
            equipos_hm = getattr(self, "_hm_equipos", [])
            if 0 <= r_idx < len(equipos_hm):
                eq = equipos_hm[r_idx]
                label_completo = eq.get("label", eq.get("ip", "Dispositivo"))
                ip = eq.get("ip", "---")
                dispo_mat = getattr(self, "_hm_dispo", [])

                if 0 <= c_idx < len(horas_turno) and r_idx < len(dispo_mat):
                    val = dispo_mat[r_idx][c_idx]
                    pct = int(round(val * 100))
                    if pct == 0:
                        estado = "⚪ Sin Registros / Inactivo"
                    elif pct >= 99:
                        estado = "🟢 Nominal"
                    elif pct >= 70:
                        estado = "🟡 Parcial"
                    else:
                        estado = "🔴 Inestable/Offline"
                    text = f"🏷️ {label_completo}\n🌐 IP: {ip}\n⏰ Franja: {hora_real:02d}:00 - {hora_real:02d}:59\n📊 SLA Bloque: {pct}% ({estado})"
                else:
                    text = f"🏷️ {label_completo}\n🌐 IP: {ip}"

        elif "Semanal" in hm_mode:
            dias_hm = getattr(self, "_hm_dias", [])
            if 0 <= r_idx < len(dias_hm):
                dia_nombre = dias_hm[r_idx]
                disp_sem = getattr(self, "_hm_dispo", [])
                if 0 <= c_idx < len(horas_turno) and r_idx < len(disp_sem):
                    val = disp_sem[r_idx][c_idx]
                    pct = int(round(val * 100))
                    if pct == 0:
                        estado = "⚪ Sin Registros / Inactivo"
                    elif pct >= 99:
                        estado = "🟢 Nominal"
                    elif pct >= 70:
                        estado = "🟡 Degradado"
                    else:
                        estado = "🔴 Caído"
                    text = f"📅 Día: {dia_nombre}\n⏰ Franja: {hora_real:02d}:00 - {hora_real:02d}:59\n📊 Disponibilidad: {pct}% ({estado})"
                else:
                    text = f"📅 Día: {dia_nombre}"

        if text:
            max_limit = max(0.5, len(horas_turno) - 2.5)
            clamped_x = max(0.5, min(max_limit, event.xdata))
            self.annot_hm.xy = (clamped_x, event.ydata)
            self.annot_hm.set_text(text)
            if not self.annot_hm.get_visible():
                self.annot_hm.set_visible(True)
            self.canvas_heatmap.draw_idle()
        else:
            if self.annot_hm.get_visible():
                self.annot_hm.set_visible(False)
                self.canvas_heatmap.draw_idle()

    def desacoplar_pantalla(self) -> None:
        """Abre la telemetría en una ventana Toplevel independiente para monitores secundarios."""
        # 1. Limpiar la pestaña incrustada y mostrar un placeholder elegante
        for w in self.frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        placeholder = customtkinter.CTkFrame(self.frame, fg_color="#18181B", corner_radius=12)
        placeholder.pack(expand=True, fill="both", padx=20, pady=20)

        center_card = customtkinter.CTkFrame(placeholder, fg_color="#242427", corner_radius=12)
        center_card.place(relx=0.5, rely=0.5, anchor="center")

        customtkinter.CTkLabel(
            center_card,
            text="🖥️ Telemetría Desacoplada en Monitor Secundario",
            font=("Arial", 18, "bold"),
            text_color="#38BDF8",
        ).pack(padx=30, pady=(25, 8))

        customtkinter.CTkLabel(
            center_card,
            text="El panel de telemetría y rendimiento operacional está activo en su propia ventana dedicada.\nPuede moverla a una pantalla secundaria, proyectores de pared (NOC) o mantenerla en pantalla completa.",
            font=("Arial", 12),
            text_color="#94A3B8",
            justify="center",
        ).pack(padx=30, pady=(0, 20))

        customtkinter.CTkButton(
            center_card,
            text="📥 Reacoplar Panel a esta Pestaña",
            font=("Arial", 13, "bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            height=38,
            command=self.reacoplar_pantalla,
        ).pack(padx=30, pady=(0, 25))

        # 2. Crear la ventana Toplevel secundaria
        self.popout_window = customtkinter.CTkToplevel(self.app)
        self.popout_window.title(f"{APP_NAME} - Telemetría de Red y Rendimiento [Monitor Secundario]")
        self.popout_window.geometry("1240x820")
        self.popout_window.minsize(900, 600)
        self.popout_window.protocol("WM_DELETE_WINDOW", self.reacoplar_pantalla)

        # 3. Construir e inicializar la interfaz dentro de la ventana secundaria
        self.inicializar(contenedor=self.popout_window, es_popout=True)
        self.actualizar_graficos()

    def reacoplar_pantalla(self) -> None:
        """Cierra la ventana externa y vuelve a montar la telemetría dentro de la pestaña original."""
        if self.popout_window and self.popout_window.winfo_exists():
            try:
                self.popout_window.destroy()
            except Exception:
                pass
        self.popout_window = None

        self.inicializar(contenedor=self.frame, es_popout=False)
        self.actualizar_graficos()

    def actualizar_graficos(self, forzar: bool = False) -> None:
        """
        Dispara la actualización asíncrona de telemetría sin bloquear el hilo principal.
        Utiliza un worker daemon en segundo plano para cálculo en lotes ultra optimizado.
        """
        try:
            if not self.app.winfo_exists() or not self.telemetria_frame or not self.telemetria_frame.winfo_exists():
                return
        except Exception:
            return

        if getattr(self, "_worker_busy", False):
            self._pending_refresh = True
            return

        self._worker_busy = True
        t = threading.Thread(target=self._async_fetch_telemetry, daemon=True)
        t.start()

    def _async_fetch_telemetry(self) -> None:
        """Worker en segundo plano: recolecta y procesa métricas en RAM sin saturar la UI."""
        try:
            metricas = getattr(self.app, "metricas", None)
            if not metricas:
                self._worker_busy = False
                return

            equipos = getattr(self.app, "equipos_a_monitorear", [])
            turno_ini = getattr(self.app, "turno_inicio", "07:00")
            turno_fin = getattr(self.app, "turno_fin", "18:00")
            filtro = self.filtro_host
            modo = self.modo_heatmap

            monitors = getattr(self.app, "monitors", {})
            monitors_status = {ip: getattr(m, "status", "Desconectado") for ip, m in monitors.items()}

            payload = metricas.obtener_telemetria_completa(
                equipos=equipos,
                filtro_host=filtro,
                modo=modo,
                turno_inicio=turno_ini,
                turno_fin=turno_fin,
                monitors_status=monitors_status,
            )

            # Notificar al hilo principal de la UI para renderizado rápido
            self.app.after(0, self._render_telemetry_ui, payload)
        except Exception as e:
            print(f"[TelemetryTab] Error en worker asíncrono: {e}")
            self._worker_busy = False

    def _render_telemetry_ui(self, payload: dict) -> None:
        """Renderiza los datos procesados en la UI sin congelar la ventana ni destruir widgets."""
        self._worker_busy = False
        if getattr(self, "_pending_refresh", False):
            self._pending_refresh = False
            self.app.after(50, self.actualizar_graficos)

        try:
            if not self.app.winfo_exists() or not self.telemetria_frame or not self.telemetria_frame.winfo_exists():
                return
        except Exception:
            return

        equipos = getattr(self.app, "equipos_a_monitorear", [])
        if hasattr(self, "opt_host"):
            equipos_nombres = ["Todos los Equipos"] + [eq.get("label", eq.get("ip")) for eq in equipos]
            self.opt_host.configure(values=equipos_nombres)

        # ── 1. Actualizar Subtítulo & Insignia de Turno ───────────────────────
        if payload.get("es_turno", False):
            badge_txt = f"🕒 Turno Operacional: {payload['turno_inicio']} a {payload['turno_fin']} • Supervisión Adaptada"
            self.lbl_subtitulo.configure(text=badge_txt, text_color="#38BDF8")
        else:
            self.lbl_subtitulo.configure(
                text="Supervisión en tiempo real de latencia, SLA de disponibilidad y microcortes de enlace (24h / 7 Días)",
                text_color="#94A3B8",
            )

        # ── 2. Actualizar Ribbon KPI ──────────────────────────────────────────
        if "uptime" in getattr(self, "kpi_title_labels", {}):
            self.kpi_title_labels["uptime"].configure(text=payload.get("kpi_uptime_title", "SLA Global (24h)"))

        kpis = payload["kpis"]
        avg_uptime = kpis["uptime"]
        color_up = "#10B981" if avg_uptime >= 99.0 else "#F59E0B" if avg_uptime >= 95.0 else "#EF4444"
        self.kpi_cards["uptime"].configure(text=f"{avg_uptime:.2f}%", text_color=color_up)
        self.kpi_cards["latencia"].configure(text=f"{kpis['latencia']:.1f} ms")
        self.kpi_cards["microcortes"].configure(
            text=f"{kpis['microcortes']} eventos",
            text_color="#10B981" if kpis["microcortes"] == 0 else "#F59E0B",
        )
        self.kpi_cards["downtime"].configure(
            text=kpis["downtime"],
            text_color="#10B981" if kpis["downtime_sec"] == 0 else "#EF4444",
        )

        # ── 3. Gráfico de Latencia Avanzado (Grafana Dark Theme) ───────────────
        if hasattr(self, "lbl_lat_title") and self.lbl_lat_title:
            self.lbl_lat_title.configure(text=payload.get("latencia_title", "📈 Comportamiento de Latencia Temporal"))

        self.ax_latencia.clear()
        self.ax_latencia.set_facecolor("#18181B")
        self.ax_latencia.grid(True, linestyle="--", alpha=0.2, color="#64748B")
        self.ax_latencia.tick_params(colors="#94A3B8", labelsize=8)

        colores = ["#00D9FF", "#38BDF8", "#10B981", "#F59E0B", "#F43F5E", "#A855F7"]
        for i, serie in enumerate(payload["serie_latencia"]):
            color_line = colores[i % len(colores)]
            if serie.get("x_vals") and serie.get("y_vals"):
                self.ax_latencia.plot(
                    serie["x_vals"],
                    serie["y_vals"],
                    label=serie["label"],
                    color=color_line,
                    linewidth=1.8,
                )
                self.ax_latencia.fill_between(serie["x_vals"], serie["y_vals"], alpha=0.10, color=color_line)

        self.ax_latencia.axhline(
            y=100,
            color="#EF4444",
            linestyle="--",
            linewidth=1.0,
            alpha=0.7,
            label="Umbral SLA (100 ms)",
        )

        # Fijar ventana horizontal de tiempo adaptada al turno o 24h
        min_x = payload.get("latencia_min_x")
        max_x = payload.get("latencia_max_x")
        if min_x and max_x:
            self.ax_latencia.set_xlim(min_x, max_x)

        self.ax_latencia.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        self.ax_latencia.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=12))
        self.ax_latencia.legend(
            facecolor="#27272A", edgecolor="#3F3F46", labelcolor="white", fontsize=8, loc="upper right", ncol=4
        )
        self.canvas_latencia.draw_idle()
        self.lbl_stats_latencia.configure(text=payload["stats_text"])

        # ── 4. Mapa de Calor Discreto (Pastillas Redondeadas) ─────────────────
        hm = payload["heatmap_data"]
        self.lbl_heatmap_title.configure(text=hm["title"])
        self.lbl_heatmap_rango.configure(text=hm["rango_subtitulo"])

        self.ax_heatmap.clear()
        self.ax_heatmap.set_facecolor("#18181B")

        colores_heat_dark = ["#26262B", "#14452F", "#1B6E44", "#229C5B", "#38D984"]
        nrows = hm["nrows"]
        ncols = hm["ncols"]
        tile_w, tile_h = 0.82, 0.72

        if "Semanal" in hm["mode"]:
            self.fig_heatmap.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.08)
        else:
            self.fig_heatmap.subplots_adjust(left=0.22, right=0.98, top=0.88, bottom=0.08)

        matriz_disp = hm["matriz_disp"]
        for r in range(nrows):
            y_pos = (nrows - 1) - r
            for c in range(ncols):
                val = matriz_disp[r][c]
                if val <= 0.01:
                    c_idx = 0
                elif val < 0.70:
                    c_idx = 1
                elif val < 0.90:
                    c_idx = 2
                elif val < 0.99:
                    c_idx = 3
                else:
                    c_idx = 4

                box = FancyBboxPatch(
                    (c - tile_w / 2, y_pos - tile_h / 2),
                    tile_w,
                    tile_h,
                    boxstyle="round,pad=0.03,rounding_size=0.18",
                    facecolor=colores_heat_dark[c_idx],
                    edgecolor="#2E2E33",
                    linewidth=0.5,
                )
                self.ax_heatmap.add_patch(box)

        self.ax_heatmap.set_xlim(-0.7, max(0.5, ncols - 0.3))
        self.ax_heatmap.set_ylim(-1.1, max(0.5, nrows - 0.3))
        self.ax_heatmap.xaxis.tick_top()
        self.ax_heatmap.set_xticks(range(ncols))
        self.ax_heatmap.set_xticklabels(hm["col_labels"], fontsize=7.5, color="#94A3B8")
        self.ax_heatmap.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0)

        # Configuración exacta de Y: cada fila r tiene su tick en y_pos = (nrows - 1) - r
        # Para r=0 (arriba): y_pos = nrows - 1 -> etiqueta hm["row_labels"][0]
        # Para r=nrows-1 (abajo): y_pos = 0 -> etiqueta hm["row_labels"][nrows - 1]
        self.ax_heatmap.set_yticks([(nrows - 1) - r for r in range(nrows)])
        self.ax_heatmap.set_yticklabels(
            hm["row_labels"],
            fontsize=8,
            color="#F8FAFC",
            fontweight="bold" if "Semanal" in hm["mode"] else "normal",
        )
        self.ax_heatmap.tick_params(axis="y", left=False, length=0)

        # Leyenda de 5 pasos en el Heatmap
        leg_w, leg_h = 0.70, 0.32
        leg_y = -0.92
        leg_x = max(0.5, ncols - 6.8)
        self.ax_heatmap.text(leg_x - 0.4, leg_y + leg_h / 2, "Menos", fontsize=7.5, color="#94A3B8", ha="right", va="center")
        for i, col in enumerate(colores_heat_dark):
            p = FancyBboxPatch(
                (leg_x + (i * 0.85), leg_y),
                leg_w,
                leg_h,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                facecolor=col,
                edgecolor="#3F3F46",
                linewidth=0.4,
            )
            self.ax_heatmap.add_patch(p)
        self.ax_heatmap.text(leg_x + (len(colores_heat_dark) * 0.85) + 0.3, leg_y + leg_h / 2, "Más", fontsize=7.5, color="#94A3B8", ha="left", va="center")

        # Metadatos para hover tooltip
        self._hm_mode = hm["mode"]
        self._hm_horas_turno = hm["horas_turno"]
        self._hm_dias = hm["row_labels"]
        self._hm_equipos = hm.get("equipos_lista", [])
        self._hm_dispo = matriz_disp
        self._hm_nrows = nrows
        self._hm_ncols = ncols

        self.annot_hm = self.ax_heatmap.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="#1E293B", ec="#0284C7", lw=1.2),
            color="#F8FAFC",
            fontsize=8.5,
            fontfamily="sans-serif",
            zorder=200,
        )
        self.annot_hm.set_visible(False)
        for spine in self.ax_heatmap.spines.values():
            spine.set_visible(False)
        self.ax_heatmap.tick_params(axis="both", which="both", length=0)
        self.canvas_heatmap.draw_idle()

        # ── 5. Gauges de Disponibilidad (Widget Pooling / Zero Destroy) ───────
        if not hasattr(self, "_gauges_pool"):
            self._gauges_pool = {}

        current_gauge_ips = [g["ip"] for g in payload["gauges_data"]]
        cached_gauge_ips = list(self._gauges_pool.keys())

        if current_gauge_ips != cached_gauge_ips:
            for widget in self.gauges_container.winfo_children():
                widget.destroy()
            self._gauges_pool = {}

            cols_per_row = min(5, max(1, len(current_gauge_ips)))
            for i in range(cols_per_row):
                self.gauges_container.grid_columnconfigure(i, weight=1)

            for i, g in enumerate(payload["gauges_data"]):
                ip = g["ip"]
                row, col = i // cols_per_row, i % cols_per_row
                g_frame = customtkinter.CTkFrame(self.gauges_container, fg_color="#1E1E22", corner_radius=6)
                g_frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

                ubi_txt = f"📍 {g.get('ubicacion', '').upper()}" if g.get("ubicacion") else "📍 SITIO"
                lbl_ubi = customtkinter.CTkLabel(
                    g_frame,
                    text=ubi_txt,
                    font=("Arial", 8, "bold"),
                    text_color="#38BDF8",
                    fg_color="#0F172A",
                    corner_radius=4,
                    height=16,
                )
                lbl_ubi.pack(anchor="nw", padx=6, pady=(4, 0))

                canvas = tk.Canvas(g_frame, width=120, height=68, bg="#1E1E22", highlightthickness=0)
                canvas.pack(pady=2)

                canvas.create_arc(10, 10, 110, 110, start=0, extent=180, outline="#334155", width=9, style="arc")
                arc_act = canvas.create_arc(10, 10, 110, 110, start=180, extent=0, outline="#10B981", width=9, style="arc")
                text_pct = canvas.create_text(60, 52, text="0.0%", fill="#F8FAFC", font=("Arial", 13, "bold"))

                lbl_title = customtkinter.CTkLabel(
                    g_frame, text=g["label"], font=("Arial", 10, "bold"), text_color="#CBD5E1"
                )
                lbl_title.pack(pady=(0, 4))

                self._gauges_pool[ip] = {
                    "canvas": canvas,
                    "arc_act": arc_act,
                    "text_pct": text_pct,
                    "lbl_title": lbl_title,
                    "lbl_ubi": lbl_ubi,
                }

        for g in payload["gauges_data"]:
            ip = g["ip"]
            up = g["uptime"]
            item = self._gauges_pool.get(ip)
            if item:
                color_arc = "#10B981" if up >= 99.0 else "#F59E0B" if up >= 95.0 else "#EF4444"
                extent = (up / 100.0) * 180
                item["canvas"].itemconfig(item["arc_act"], extent=-extent, outline=color_arc)
                item["canvas"].itemconfig(item["text_pct"], text=f"{up:.1f}%")
                item["lbl_title"].configure(text=g["label"])
                if "lbl_ubi" in item:
                    ubi_txt = f"📍 {g.get('ubicacion', '').upper()}" if g.get("ubicacion") else "📍 SITIO"
                    item["lbl_ubi"].configure(text=ubi_txt)

        # ── 6. Tabla Moderna de Desglose (Widget Pooling) ─────────────────────
        if not hasattr(self, "_table_rows_pool"):
            self._table_rows_pool = {}

        current_table_ips = [t["ip"] for t in payload["tabla_data"]]
        cached_table_ips = list(self._table_rows_pool.keys())
        cols_weights = [(0, 3), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 3)]

        if current_table_ips != cached_table_ips:
            for widget in self.tabla_container.winfo_children():
                widget.destroy()
            self._table_rows_pool = {}

            header_grid = customtkinter.CTkFrame(self.tabla_container, fg_color="#0F172A", corner_radius=6)
            header_grid.pack(fill="x", pady=(0, 4))
            for c_idx, weight in cols_weights:
                header_grid.grid_columnconfigure(c_idx, weight=weight)

            headers = ["Activo / Label", "IP / Host", "Estado", "Latencia", "Uptime SLA", "Microcortes", "Salud Visual"]
            for c_idx, h_text in enumerate(headers):
                customtkinter.CTkLabel(
                    header_grid, text=h_text, font=("Arial", 11, "bold"), text_color="#FFFFFF"
                ).grid(row=0, column=c_idx, padx=8, pady=6, sticky="w")

            for row_idx, t in enumerate(payload["tabla_data"]):
                ip = t["ip"]
                row_frame = customtkinter.CTkFrame(
                    self.tabla_container,
                    fg_color="#1E1E22" if row_idx % 2 == 0 else "#242427",
                    corner_radius=4,
                )
                row_frame.pack(fill="x", pady=2)
                for c_idx, weight in cols_weights:
                    row_frame.grid_columnconfigure(c_idx, weight=weight)

                lbl_lbl = customtkinter.CTkLabel(row_frame, text=t["label"], font=("Arial", 11, "bold"), text_color="#F8FAFC")
                lbl_lbl.grid(row=0, column=0, padx=8, pady=4, sticky="w")

                lbl_ip = customtkinter.CTkLabel(row_frame, text=ip, font=("Courier New", 10), text_color="#94A3B8")
                lbl_ip.grid(row=0, column=1, padx=8, pady=4, sticky="w")

                lbl_st = customtkinter.CTkLabel(row_frame, text=t["status"], font=("Arial", 11, "bold"))
                lbl_st.grid(row=0, column=2, padx=8, pady=4, sticky="w")

                lbl_lat = customtkinter.CTkLabel(row_frame, text=t["lat_str"], font=("Arial", 11), text_color="#E2E8F0")
                lbl_lat.grid(row=0, column=3, padx=8, pady=4, sticky="w")

                lbl_up = customtkinter.CTkLabel(row_frame, text=f"{t['uptime_val']:.1f}%", font=("Arial", 11, "bold"))
                lbl_up.grid(row=0, column=4, padx=8, pady=4, sticky="w")

                lbl_down = customtkinter.CTkLabel(row_frame, text=t["down_str"], font=("Arial", 10))
                lbl_down.grid(row=0, column=5, padx=8, pady=4, sticky="w")

                can_bar = tk.Canvas(row_frame, width=100, height=10, bg="#1E1E22", highlightthickness=0)
                can_bar.grid(row=0, column=6, padx=8, pady=6, sticky="w")
                can_bar.create_rectangle(0, 0, 100, 10, fill="#334155", width=0)
                rect_bar = can_bar.create_rectangle(0, 0, 100, 10, fill="#10B981", width=0)

                self._table_rows_pool[ip] = {
                    "lbl_lbl": lbl_lbl,
                    "lbl_ip": lbl_ip,
                    "lbl_st": lbl_st,
                    "lbl_lat": lbl_lat,
                    "lbl_up": lbl_up,
                    "lbl_down": lbl_down,
                    "can_bar": can_bar,
                    "rect_bar": rect_bar,
                }

        for t in payload["tabla_data"]:
            ip = t["ip"]
            row_item = self._table_rows_pool.get(ip)
            if row_item:
                row_item["lbl_lbl"].configure(text=t["label"])
                row_item["lbl_ip"].configure(text=ip)

                st = t["status"]
                st_col = "#10B981" if st == "Conectado" else "#EF4444"
                st_ico = "🟢" if st == "Conectado" else "🔴"
                row_item["lbl_st"].configure(text=f"{st_ico} {st}", text_color=st_col)
                row_item["lbl_lat"].configure(text=t["lat_str"])

                up_v = t["uptime_val"]
                up_col = "#10B981" if up_v >= 99.0 else "#F59E0B" if up_v >= 95.0 else "#EF4444"
                row_item["lbl_up"].configure(text=f"{up_v:.1f}%", text_color=up_col)

                mc = t["micro_c"]
                down_s = t["down_str"]
                down_txt = f"{mc} cort. ({down_s})" if mc > 0 else f"0 ({down_s})"
                down_col = "#F59E0B" if mc > 0 else "#10B981"
                row_item["lbl_down"].configure(text=down_txt, text_color=down_col)

                fill_w = max(2, int((up_v / 100.0) * 100))
                row_item["can_bar"].coords(row_item["rect_bar"], 0, 0, fill_w, 10)
                row_item["can_bar"].itemconfig(row_item["rect_bar"], fill=up_col)

        # ── 7. Autorefresco Dinámico de Alta Frecuencia (15 segundos) ────────
        if hasattr(self, "_refresh_job") and self._refresh_job:
            try:
                self.app.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = self.app.after(15000, self.actualizar_graficos)


# Alias de clase para compatibilidad total con cualquier importación previa
TelemetryTab = HistoryTab
