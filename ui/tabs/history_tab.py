# ui/tabs/history_tab.py
"""
Pestaña de Historial de Eventos de Argos Guard.
Renderiza gráficos de latencia, heatmap y gauges usando Matplotlib.
"""

import datetime
import tkinter as tk
import customtkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class HistoryTab:
    """Controlador de la pestaña 'Historial de Eventos'."""

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self.historial_frame = customtkinter.CTkScrollableFrame(self.frame)
        self.historial_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def inicializar(self) -> None:
        """Construye todos los widgets de historial. Debe llamarse una sola vez."""
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

        # ── Gráfico de Latencia ──────────────────────────────────────────
        self.frame_latencia = customtkinter.CTkFrame(self.graficos_frame, fg_color="#2B2B2B")
        self.frame_latencia.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(
            self.frame_latencia,
            text="📈 Latencia - Últimas 24 Horas",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)

        self.fig_latencia = Figure(figsize=(8, 3), facecolor="#2B2B2B", dpi=100)
        self.ax_latencia = self.fig_latencia.add_subplot(111)
        self.ax_latencia.set_facecolor("#2B2B2B")
        self.ax_latencia.tick_params(colors="white", labelsize=8)
        self.fig_latencia.tight_layout()

        self.canvas_latencia = FigureCanvasTkAgg(self.fig_latencia, self.frame_latencia)
        self.canvas_latencia.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # ── Gauges de Disponibilidad ─────────────────────────────────────
        self.frame_gauges = customtkinter.CTkFrame(self.graficos_frame, fg_color="transparent")
        self.frame_gauges.pack(fill="x", pady=5)
        customtkinter.CTkLabel(
            self.frame_gauges,
            text="🎯 Disponibilidad - Últimas 24 Horas",
            font=("Arial", 16, "bold"),
        ).pack(pady=2)

        self.gauges_container = customtkinter.CTkFrame(self.frame_gauges, fg_color="transparent")
        self.gauges_container.pack(fill="x", expand=True)

        # ── Heatmap ──────────────────────────────────────────────────────
        self.frame_heatmap = customtkinter.CTkFrame(self.graficos_frame, fg_color="#2B2B2B")
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
        self.canvas_heatmap.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # ── Tabla de estado ───────────────────────────────────────────────
        self.frame_tabla = customtkinter.CTkFrame(self.graficos_frame, fg_color="#2B2B2B")
        self.frame_tabla.pack(fill="both", expand=True, pady=5)
        customtkinter.CTkLabel(
            self.frame_tabla, text="📋 Estado Actual de Equipos", font=("Arial", 16, "bold")
        ).pack(pady=2)

        self.tabla_eventos = customtkinter.CTkTextbox(
            self.frame_tabla, height=150, font=("Courier New", 11)
        )
        self.tabla_eventos.pack(fill="both", expand=True, padx=10, pady=10)

        customtkinter.CTkButton(
            self.historial_frame,
            text="🔄 Actualizar Gráficos",
            command=self.actualizar_graficos,
        ).pack(pady=10)

        # Primera actualización diferida
        self.app.after(500, self.actualizar_graficos)

    def actualizar_graficos(self) -> None:
        """Redibuja todos los gráficos con datos frescos de la base de datos."""
        try:
            if not self.app.winfo_exists() or not self.historial_frame.winfo_exists():
                return
        except Exception:
            return

        metricas = getattr(self.app, "metricas", None)
        if not metricas:
            return

        colores = ["#00d9ff", "#ff6b6b", "#51cf66", "#ffd43b", "#ff6b9d", "#9775fa"]

        # ── Latencia ─────────────────────────────────────────────────────
        self.ax_latencia.clear()
        self.ax_latencia.set_facecolor("#2B2B2B")
        self.ax_latencia.grid(True, alpha=0.2, color="#555")
        self.ax_latencia.tick_params(colors="white", labelsize=8)

        for i, equipo in enumerate(self.app.equipos_a_monitorear):
            datos = metricas.obtener_datos(equipo["ip"], periodo_horas=24)
            if datos and datos["timestamps"]:
                lats = datos["latencias"]
                paso = max(1, len(lats) // 40)
                indices = list(range(0, len(lats), paso))
                self.ax_latencia.plot(
                    range(len(indices)),
                    [lats[j] for j in indices],
                    label=equipo["label"],
                    color=colores[i % len(colores)],
                    linewidth=2,
                )

        handles, labels = self.ax_latencia.get_legend_handles_labels()
        if labels:
            self.ax_latencia.legend(
                facecolor="#3B3B3B", edgecolor="#555", labelcolor="white", fontsize=8
            )
        self.canvas_latencia.draw()

        # ── Heatmap ──────────────────────────────────────────────────────
        self.ax_heatmap.clear()
        self.ax_heatmap.set_facecolor("#2B2B2B")

        heatmap_data, labels_heatmap = [], []
        for equipo in self.app.equipos_a_monitorear:
            labels_heatmap.append(equipo["label"][:20])
            datos = metricas.obtener_datos(equipo["ip"], periodo_horas=24)
            if datos and datos["estados"]:
                bloques = np.array_split(datos["estados"], 24)
                dispo = [
                    sum(1 for s in b if s == 1) / len(b) if len(b) > 0 else 0
                    for b in bloques
                ]
                heatmap_data.append(dispo)
            else:
                heatmap_data.append([0] * 24)

        if heatmap_data:
            self.ax_heatmap.imshow(heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
            self.ax_heatmap.set_yticks(range(len(labels_heatmap)))
            self.ax_heatmap.set_yticklabels(labels_heatmap, color="white", fontsize=8)
            self.ax_heatmap.set_xticks(range(0, 24, 2))
            self.ax_heatmap.set_xticklabels(
                [f"{h}h" for h in range(0, 24, 2)], color="white", fontsize=8
            )
            self.ax_heatmap.tick_params(axis="both", which="both", length=0)
        self.canvas_heatmap.draw()

        # ── Gauges ───────────────────────────────────────────────────────
        for widget in self.gauges_container.winfo_children():
            widget.destroy()

        for i in range(5):
            self.gauges_container.grid_columnconfigure(i, weight=1)

        for i, equipo in enumerate(self.app.equipos_a_monitorear):
            uptime = metricas.calcular_uptime(equipo["ip"])
            row, col = i // 5, i % 5

            g_frame = customtkinter.CTkFrame(self.gauges_container, fg_color="#2B2B2B")
            g_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            color = "#51cf66" if uptime >= 99 else "#ffd43b" if uptime >= 95 else "#ff6b6b"

            canvas_w, canvas_h = 120, 70
            canvas = tk.Canvas(
                g_frame, width=canvas_w, height=canvas_h, bg="#2B2B2B", highlightthickness=0
            )
            canvas.pack(pady=2)
            canvas.create_arc(10, 10, 110, 110, start=0, extent=180, outline="#444", width=8, style="arc")
            extent = (uptime / 100) * 180
            canvas.create_arc(10, 10, 110, 110, start=180, extent=-extent, outline=color, width=8, style="arc")
            canvas.create_text(60, 55, text=f"{uptime:.1f}%", fill="white", font=("Arial", 14, "bold"))

            customtkinter.CTkLabel(
                g_frame, text=equipo["label"][:15], font=("Arial", 10, "bold"), text_color="#AAA"
            ).pack(pady=(0, 5))

        # ── Tabla ─────────────────────────────────────────────────────────
        self.tabla_eventos.delete("0.0", "end")
        header = (
            f"┌{'─'*25}┬{'─'*12}┬{'─'*12}┬{'─'*10}┐\n"
            f"│ {'Equipo':<23} │ {'Estado':<10} │ {'Latencia':<10} │ {'Hora':<8} │\n"
            f"├{'─'*25}┼{'─'*12}┼{'─'*12}┼{'─'*10}┤\n"
        )
        self.tabla_eventos.insert("end", header)

        for ip, monitor in self.app.monitors.items():
            datos = metricas.obtener_datos(ip, periodo_horas=1)
            lat = f"{datos['latencias'][-1]:.1f}ms" if datos and datos["latencias"] else "---"
            hora = datetime.datetime.now().strftime("%H:%M:%S")
            icon = "🟢" if monitor.status == "Conectado" else "🔴"
            self.tabla_eventos.insert(
                "end",
                f"│ {icon} {monitor.label[:20]:<20} │ {monitor.status:<10} │ {lat:<10} │ {hora:<8} │\n",
            )

        self.tabla_eventos.insert("end", f"└{'─'*25}┴{'─'*12}┴{'─'*12}┴{'─'*10}┘")

        # Refrescar cada 60 segundos
        self.app.after(60000, self.actualizar_graficos)
