# ui/tabs/history_tab.py
"""
Pestaña de Telemetría y Rendimiento de Argos Guard (anteriormente Historial Operacional).
Renderiza métricas avanzadas, KPIs de red, mapa de calor discreto (pastillas redondeadas),
gráficos de latencia con umbrales SLA y tabla de estado con barras de salud embebidas.
"""

from __future__ import annotations

import datetime
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
        self._refresh_job = None

    def inicializar(self, contenedor=None, es_popout: bool = False) -> None:
        """Construye todos los componentes de la interfaz de telemetría."""
        self.es_popout = es_popout
        self.contenedor_actual = contenedor if contenedor is not None else self.frame

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
            width=170,
            fg_color="#334155",
            button_color="#475569",
        )
        self.opt_host.set(self.filtro_host)
        self.opt_host.pack(side="left", padx=5)

        # Toggle de modo Heatmap
        self.seg_heatmap = customtkinter.CTkSegmentedButton(
            controls_frame,
            values=["Semanal (7D x 24h)", "Por Equipo (24h)"],
            command=self._on_heatmap_mode_change,
            fg_color="#334155",
            selected_color="#0284C7",
        )
        self.seg_heatmap.set(self.modo_heatmap)
        self.seg_heatmap.pack(side="left", padx=5)

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

        for idx, (kpi_id, title, val_def, color) in enumerate(kpi_defs):
            card = customtkinter.CTkFrame(self.kpi_frame, fg_color="#242427", corner_radius=8)
            card.grid(row=0, column=idx, padx=4, sticky="nsew")

            customtkinter.CTkLabel(
                card, text=title, font=("Arial", 11, "bold"), text_color="#94A3B8"
            ).pack(anchor="w", padx=12, pady=(8, 2))

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

        lbl_lat_title = customtkinter.CTkLabel(
            self.frame_latencia,
            text="📈 Comportamiento de Latencia Temporal (Umbral SLA: 100 ms)",
            font=("Arial", 14, "bold"),
            text_color="#F8FAFC",
        )
        lbl_lat_title.pack(anchor="w", padx=12, pady=(8, 2))

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

    def _on_heatmap_mode_change(self, mode: str) -> None:
        self.modo_heatmap = mode
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

        r_idx = int(round(event.ydata))
        c_idx = int(round(event.xdata))
        text = ""

        if getattr(self, "_hm_mode", "") == "Por Equipo (24h)":
            equipos_hm = getattr(self, "_hm_equipos", [])
            if 0 <= r_idx < len(equipos_hm):
                eq = equipos_hm[r_idx]
                label_completo = eq.get("label", eq.get("ip", "Dispositivo"))
                ip = eq.get("ip", "---")
                dispo_mat = getattr(self, "_hm_dispo", [])

                if 0 <= c_idx < 24 and r_idx < len(dispo_mat):
                    val = dispo_mat[r_idx][c_idx]
                    pct = int(val * 100)
                    estado = "🟢 Nominal" if pct >= 99 else "🟡 Parcial" if pct >= 70 else "🔴 Inestable/Offline"
                    text = f"🏷️ {label_completo}\n🌐 IP: {ip}\n⏰ Franja: {c_idx:02d}:00 - {c_idx:02d}:59\n📊 SLA Bloque: {pct}% ({estado})"
                else:
                    metricas = getattr(self.app, "metricas", None)
                    uptime = metricas.calcular_uptime(ip) if metricas else 100.0
                    text = f"🏷️ {label_completo}\n🌐 IP: {ip}\n🎯 SLA Global 24h: {uptime:.1f}%"

        elif getattr(self, "_hm_mode", "") == "Semanal (7D x 24h)":
            dias_hm = getattr(self, "_hm_dias", [])
            if 0 <= r_idx < len(dias_hm):
                dia_nombre = dias_hm[r_idx]
                disp_sem = getattr(self, "_hm_disp_semanal", [])
                if 0 <= c_idx < 24 and r_idx < len(disp_sem):
                    val = disp_sem[r_idx][c_idx]
                    pct = int(val * 100)
                    estado = "🟢 Nominal" if pct >= 99 else "🟡 Degradado" if pct >= 70 else "🔴 Caído"
                    text = f"📅 Día: {dia_nombre}\n⏰ Franja: {c_idx:02d}:00 - {c_idx:02d}:59\n📊 Disponibilidad: {pct}% ({estado})"
                else:
                    text = f"📅 Día: {dia_nombre}"

        if text:
            clamped_x = max(0.5, min(17.5, event.xdata))
            self.annot_hm.xy = (clamped_x, event.ydata)
            self.annot_hm.set_text(text)
            if not self.annot_hm.get_visible():
                self.annot_hm.set_visible(True)
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

    def actualizar_graficos(self) -> None:
        """Redibuja toda la telemetría con datos frescos de SQLite."""
        try:
            if not self.app.winfo_exists() or not self.telemetria_frame or not self.telemetria_frame.winfo_exists():
                return
        except Exception:
            return

        metricas = getattr(self.app, "metricas", None)
        if not metricas:
            return

        # ── A. Calcular KPIs Consolidados ──────────────────────────────────────
        total_downtime_sec = 0.0
        total_microcortes = 0
        uptimes = []
        latencias_actuales = []
        latencias_historicas = []

        equipos = getattr(self.app, "equipos_a_monitorear", [])
        if hasattr(self, "opt_host"):
            equipos_nombres = ["Todos los Equipos"] + [eq.get("label", eq.get("ip")) for eq in equipos]
            self.opt_host.configure(values=equipos_nombres)

        for eq in equipos:
            ip = eq["ip"]
            up = metricas.calcular_uptime(ip)
            uptimes.append(up)

            if hasattr(metricas, "analizar_desconexiones_y_downtime"):
                res_down = metricas.analizar_desconexiones_y_downtime(ip, periodo_horas=24)
                total_downtime_sec += res_down.get("downtime_segundos", 0.0)
                total_microcortes += res_down.get("microcortes_count", 0)

            datos_recientes = metricas.obtener_datos(ip, periodo_horas=1)
            if datos_recientes and datos_recientes["latencias"]:
                ultimas = [l for l in datos_recientes["latencias"] if l and l > 0]
                if ultimas:
                    latencias_actuales.append(ultimas[-1])

        avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 100.0
        avg_latencia = sum(latencias_actuales) / len(latencias_actuales) if latencias_actuales else 0.0

        downtime_str = (
            metricas._formatear_duracion(total_downtime_sec)
            if hasattr(metricas, "_formatear_duracion")
            else f"{int(total_downtime_sec)}s"
        )

        # Actualizar Ribbon KPI
        color_up = "#10B981" if avg_uptime >= 99.0 else "#F59E0B" if avg_uptime >= 95.0 else "#EF4444"
        self.kpi_cards["uptime"].configure(text=f"{avg_uptime:.2f}%", text_color=color_up)
        self.kpi_cards["latencia"].configure(text=f"{avg_latencia:.1f} ms")
        self.kpi_cards["microcortes"].configure(
            text=f"{total_microcortes} eventos",
            text_color="#10B981" if total_microcortes == 0 else "#F59E0B",
        )
        self.kpi_cards["downtime"].configure(
            text=downtime_str,
            text_color="#10B981" if total_downtime_sec == 0 else "#EF4444",
        )

        # ── B. Gráfico de Latencia Avanzado (Grafana Dark Theme) ───────────────
        self.ax_latencia.clear()
        self.ax_latencia.set_facecolor("#18181B")
        self.ax_latencia.grid(True, linestyle="--", alpha=0.2, color="#64748B")
        self.ax_latencia.tick_params(colors="#94A3B8", labelsize=8)

        colores = ["#00D9FF", "#38BDF8", "#10B981", "#F59E0B", "#F43F5E", "#A855F7"]

        equipos_a_dibujar = equipos
        if self.filtro_host != "Todos los Equipos":
            equipos_a_dibujar = [eq for eq in equipos if eq.get("label") == self.filtro_host or eq.get("ip") == self.filtro_host]

        for i, equipo in enumerate(equipos_a_dibujar):
            datos = metricas.obtener_datos(equipo["ip"], periodo_horas=24)
            if datos and datos["timestamps"]:
                lats = datos["latencias"]
                ts_list = datos["timestamps"]
                paso = max(1, len(lats) // 60)
                x_vals = ts_list[::paso]
                y_vals = [lats[k] if lats[k] is not None else 0 for k in range(0, len(lats), paso)]

                color_line = colores[i % len(colores)]
                self.ax_latencia.plot(
                    x_vals,
                    y_vals,
                    label=equipo["label"][:18],
                    color=color_line,
                    linewidth=1.8,
                )
                self.ax_latencia.fill_between(x_vals, y_vals, alpha=0.10, color=color_line)
                latencias_historicas.extend([y for y in y_vals if y > 0])

        # Umbral SLA a 100ms
        self.ax_latencia.axhline(
            y=100,
            color="#EF4444",
            linestyle="--",
            linewidth=1.0,
            alpha=0.7,
            label="Umbral SLA (100 ms)",
        )

        self.ax_latencia.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        self.ax_latencia.legend(
            facecolor="#27272A", edgecolor="#3F3F46", labelcolor="white", fontsize=8, loc="upper right", ncol=4
        )
        self.canvas_latencia.draw()

        # Actualizar pie de estadísticas
        if latencias_historicas:
            min_l = min(latencias_historicas)
            avg_l = sum(latencias_historicas) / len(latencias_historicas)
            max_l = max(latencias_historicas)
            p95_l = np.percentile(latencias_historicas, 95)
            ult_l = latencias_actuales[-1] if latencias_actuales else avg_l
            self.lbl_stats_latencia.configure(
                text=f"Métricas (24h):  Mín: {min_l:.1f}ms  │  Prom: {avg_l:.1f}ms  │  P95: {p95_l:.1f}ms  │  Máx: {max_l:.1f}ms  │  Actual: {ult_l:.1f}ms"
            )
        else:
            self.lbl_stats_latencia.configure(
                text="Métricas (24h):  Sin registros históricos disponibles para el período."
            )

        # ── C. Nuevo Mapa de Calor Discreto (Pastillas Redondeadas) ────────────
        self.ax_heatmap.clear()
        self.ax_heatmap.set_facecolor("#18181B")

        # Paleta discreta de 5 niveles para fondo oscuro
        colores_heat_dark = ["#26262B", "#14452F", "#1B6E44", "#229C5B", "#38D984"]

        if self.modo_heatmap == "Semanal (7D x 24h)":
            self.lbl_heatmap_title.configure(text="🗓️ Matriz Semanal de Disponibilidad (Lunes a Domingo × 24 Horas)")
            self.fig_heatmap.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.08)
            target_ip = None if self.filtro_host == "Todos los Equipos" else next((eq["ip"] for eq in equipos if eq["label"] == self.filtro_host), None)
            matriz_res = metricas.obtener_matriz_semanal(ip=target_ip)
            matriz_disp = matriz_res["disponibilidad"]
            dias_etiquetas = matriz_res["dias_etiquetas"]
            horas_etiquetas = matriz_res["horas_etiquetas"]

            nrows = len(dias_etiquetas)
            ncols = len(horas_etiquetas)
            tile_w, tile_h = 0.82, 0.72

            for r in range(nrows):
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
                        (c - tile_w / 2, nrows - 1 - r - tile_h / 2),
                        tile_w,
                        tile_h,
                        boxstyle="round,pad=0.03,rounding_size=0.18",
                        facecolor=colores_heat_dark[c_idx],
                        edgecolor="#2E2E33",
                        linewidth=0.5,
                    )
                    self.ax_heatmap.add_patch(box)

            self.ax_heatmap.set_xlim(-0.7, ncols - 0.3)
            self.ax_heatmap.set_ylim(-1.1, nrows - 0.3)
            self.ax_heatmap.xaxis.tick_top()
            self.ax_heatmap.set_xticks(range(ncols))
            self.ax_heatmap.set_xticklabels([f"{h:02d}h" for h in range(24)], fontsize=7.5, color="#94A3B8")
            self.ax_heatmap.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0)
            self.ax_heatmap.set_yticks(range(nrows))
            self.ax_heatmap.set_yticklabels(list(reversed(dias_etiquetas)), fontsize=8, fontweight="bold", color="#F8FAFC")
            self.ax_heatmap.tick_params(axis="y", left=False, length=0)

            # Metadata para hover tooltip
            self._hm_mode = "Semanal (7D x 24h)"
            self._hm_dias = list(reversed(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]))
            self._hm_disp_semanal = list(reversed(matriz_disp))

        else:
            # Modo por Equipo (24 Horas)
            self.lbl_heatmap_title.configure(text="🗓️ Matriz de Disponibilidad por Dispositivo (Últimas 24 Horas)")
            self.fig_heatmap.subplots_adjust(left=0.22, right=0.98, top=0.88, bottom=0.08)
            labels_hm = [eq["label"][:26] for eq in equipos_a_dibujar]
            nrows = len(labels_hm)
            ncols = 24
            tile_w, tile_h = 0.82, 0.72

            dispo_matriz_equipos = []
            for r, equipo in enumerate(equipos_a_dibujar):
                datos = metricas.obtener_datos(equipo["ip"], periodo_horas=24)
                if datos and datos["estados"]:
                    bloques = np.array_split(datos["estados"], 24)
                    dispo = [(sum(1 for s in b if s == 1) / len(b)) if len(b) > 0 else 0 for b in bloques]
                else:
                    dispo = [0] * 24
                dispo_matriz_equipos.append(dispo)

                for c in range(24):
                    val = dispo[c]
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
                        (c - tile_w / 2, nrows - 1 - r - tile_h / 2),
                        tile_w,
                        tile_h,
                        boxstyle="round,pad=0.03,rounding_size=0.18",
                        facecolor=colores_heat_dark[c_idx],
                        edgecolor="#2E2E33",
                        linewidth=0.5,
                    )
                    self.ax_heatmap.add_patch(box)

            self.ax_heatmap.set_xlim(-0.7, ncols - 0.3)
            self.ax_heatmap.set_ylim(-1.1, nrows - 0.3)
            self.ax_heatmap.xaxis.tick_top()
            self.ax_heatmap.set_xticks(range(ncols))
            self.ax_heatmap.set_xticklabels([f"{h:02d}h" for h in range(24)], fontsize=7.5, color="#94A3B8")
            self.ax_heatmap.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0)
            self.ax_heatmap.set_yticks(range(nrows))
            self.ax_heatmap.set_yticklabels(list(reversed(labels_hm)), fontsize=8, color="#F8FAFC")
            self.ax_heatmap.tick_params(axis="y", left=False, length=0)

            # Metadata para hover tooltip
            self._hm_mode = "Por Equipo (24h)"
            self._hm_equipos = list(reversed(equipos_a_dibujar))
            self._hm_dispo = list(reversed(dispo_matriz_equipos))

        # Leyenda de 5 pasos en el Heatmap (Ubicada limpia al pie derecho, sin colisión)
        leg_w, leg_h = 0.70, 0.32
        leg_y = -0.92
        leg_x = ncols - 6.8
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

        # Tooltip flotante interactivo para equipos y celdas
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
        self.canvas_heatmap.draw()

        # ── D. Gauges de Disponibilidad ─────────────────────────────────────────
        for widget in self.gauges_container.winfo_children():
            widget.destroy()

        cols_per_row = min(5, max(1, len(equipos_a_dibujar)))
        for i in range(cols_per_row):
            self.gauges_container.grid_columnconfigure(i, weight=1)

        for i, equipo in enumerate(equipos_a_dibujar):
            uptime = metricas.calcular_uptime(equipo["ip"])
            row, col = i // cols_per_row, i % cols_per_row

            g_frame = customtkinter.CTkFrame(self.gauges_container, fg_color="#1E1E22", corner_radius=6)
            g_frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            color_arc = "#10B981" if uptime >= 99.0 else "#F59E0B" if uptime >= 95.0 else "#EF4444"

            canvas_w, canvas_h = 120, 68
            canvas = tk.Canvas(g_frame, width=canvas_w, height=canvas_h, bg="#1E1E22", highlightthickness=0)
            canvas.pack(pady=2)

            # Arco base de fondo
            canvas.create_arc(10, 10, 110, 110, start=0, extent=180, outline="#334155", width=9, style="arc")
            # Arco medidor activo
            extent = (uptime / 100.0) * 180
            canvas.create_arc(10, 10, 110, 110, start=180, extent=-extent, outline=color_arc, width=9, style="arc")
            canvas.create_text(60, 52, text=f"{uptime:.1f}%", fill="#F8FAFC", font=("Arial", 13, "bold"))

            customtkinter.CTkLabel(
                g_frame, text=equipo["label"][:16], font=("Arial", 10, "bold"), text_color="#CBD5E1"
            ).pack(pady=(0, 4))

        # ── E. Tabla Moderna de Desglose con Barras de Salud ────────────────────
        for widget in self.tabla_container.winfo_children():
            widget.destroy()

        # Encabezado de la tabla
        header_grid = customtkinter.CTkFrame(self.tabla_container, fg_color="#0F172A", corner_radius=6)
        header_grid.pack(fill="x", pady=(0, 4))

        cols_weights = [(0, 3), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 3)]
        for c_idx, weight in cols_weights:
            header_grid.grid_columnconfigure(c_idx, weight=weight)

        headers = ["Activo / Label", "IP / Host", "Estado", "Latencia 1h", "Uptime SLA", "Microcortes", "Salud Visual"]
        for c_idx, h_text in enumerate(headers):
            customtkinter.CTkLabel(
                header_grid, text=h_text, font=("Arial", 11, "bold"), text_color="#FFFFFF"
            ).grid(row=0, column=c_idx, padx=8, pady=6, sticky="w")

        # Filas de equipos
        for row_idx, equipo in enumerate(equipos_a_dibujar):
            ip = equipo["ip"]
            monitor = self.app.monitors.get(ip)
            status = getattr(monitor, "status", "Desconectado") if monitor else "Desconectado"

            datos_h = metricas.obtener_datos(ip, periodo_horas=1)
            lat_str = f"{datos_h['latencias'][-1]:.1f} ms" if datos_h and datos_h["latencias"] and datos_h["latencias"][-1] else "---"

            uptime_val = metricas.calcular_uptime(ip)
            res_down = metricas.analizar_desconexiones_y_downtime(ip, periodo_horas=24) if hasattr(metricas, "analizar_desconexiones_y_downtime") else {}
            micro_c = res_down.get("microcortes_count", 0)
            down_str = res_down.get("downtime_str", "0s")

            row_frame = customtkinter.CTkFrame(
                self.tabla_container,
                fg_color="#1E1E22" if row_idx % 2 == 0 else "#242427",
                corner_radius=4,
            )
            row_frame.pack(fill="x", pady=2)
            for c_idx, weight in cols_weights:
                row_frame.grid_columnconfigure(c_idx, weight=weight)

            # Col 0: Label
            customtkinter.CTkLabel(
                row_frame, text=equipo["label"][:22], font=("Arial", 11, "bold"), text_color="#F8FAFC"
            ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

            # Col 1: IP
            customtkinter.CTkLabel(
                row_frame, text=ip, font=("Courier New", 10), text_color="#94A3B8"
            ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

            # Col 2: Estado
            st_color = "#10B981" if status == "Conectado" else "#EF4444"
            st_icon = "🟢" if status == "Conectado" else "🔴"
            customtkinter.CTkLabel(
                row_frame, text=f"{st_icon} {status}", font=("Arial", 11, "bold"), text_color=st_color
            ).grid(row=0, column=2, padx=8, pady=4, sticky="w")

            # Col 3: Latencia
            customtkinter.CTkLabel(
                row_frame, text=lat_str, font=("Arial", 11), text_color="#E2E8F0"
            ).grid(row=0, column=3, padx=8, pady=4, sticky="w")

            # Col 4: Uptime
            customtkinter.CTkLabel(
                row_frame, text=f"{uptime_val:.1f}%", font=("Arial", 11, "bold"), text_color=color_up
            ).grid(row=0, column=4, padx=8, pady=4, sticky="w")

            # Col 5: Microcortes & Downtime
            down_txt = f"{micro_c} cort. ({down_str})" if micro_c > 0 else "0 (0s)"
            down_col = "#F59E0B" if micro_c > 0 else "#10B981"
            customtkinter.CTkLabel(
                row_frame, text=down_txt, font=("Arial", 10), text_color=down_col
            ).grid(row=0, column=5, padx=8, pady=4, sticky="w")

            # Col 6: Barra de salud visual
            bar_w, bar_h = 100, 10
            can_bar = tk.Canvas(row_frame, width=bar_w, height=bar_h, bg="#1E1E22", highlightthickness=0)
            can_bar.grid(row=0, column=6, padx=8, pady=6, sticky="w")

            can_bar.create_rectangle(0, 0, bar_w, bar_h, fill="#334155", width=0)
            fill_w = max(2, int((uptime_val / 100.0) * bar_w))
            bar_color = "#10B981" if uptime_val >= 99.0 else "#F59E0B" if uptime_val >= 95.0 else "#EF4444"
            can_bar.create_rectangle(0, 0, fill_w, bar_h, fill=bar_color, width=0)

        # Autorefresco cada 60 segundos controlado
        if hasattr(self, "_refresh_job") and self._refresh_job:
            try:
                self.app.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = self.app.after(60000, self.actualizar_graficos)


# Alias de clase para compatibilidad total con cualquier importación previa
TelemetryTab = HistoryTab
