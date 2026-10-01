"""Generador de reportes PDF corporativos y ejecutivos para Anvic Network Sentinel."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as PDFImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass
class ReportContext:
    filename: str
    app_name: str
    version: str
    tagline: str
    logo_path: str
    generated_by: str
    equipos: list[dict]
    monitors: dict
    metricas: object | None
    tls_strict: bool
    cameras_count: int
    camera_max_streams: int
    empresa_cliente: str = "Anvic Seguridad Integral"
    sitio_planta: str = "Planta Quilicura - Renca"
    sla_objetivo: float = 99.5
    incluir_cctv: bool = False
    periodo_evaluado: str = "Últimas 24 Horas"
    osint_data: dict | None = None
    modo_telemetria: str = "Semanal (7D x 24h)"
    filtro_host: str = "Todos los Equipos"
    turno_inicio: str = "07:00"
    turno_fin: str = "18:00"


def _status_color(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized == "conectado":
        return "#15803D"
    if normalized == "desconectado":
        return "#DC2626"
    return "#64748B"


def _paragraph_style(
    name: str,
    *,
    size: int,
    color: str,
    leading: int | None = None,
    bold: bool = False,
    alignment: int = 0,
    keepWithNext: bool = False,
) -> ParagraphStyle:
    base = getSampleStyleSheet()["BodyText"]
    return ParagraphStyle(
        name=name,
        parent=base,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        leading=leading or (size + 3),
        textColor=colors.HexColor(color),
        alignment=alignment,
        keepWithNext=keepWithNext,
    )


def _build_summary_cards(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> Table:
    total_devices = len(ctx.equipos)
    online = 0
    total_disconnects = 0
    total_microcortes = 0
    total_downtime_sec = 0.0
    max_downtime_sec = 0.0
    uptimes_periodo: list[float] = []

    rango_ini = None
    rango_fin = None
    periodo_horas = 24
    now_dt = datetime.now()
    modo = getattr(ctx, "modo_telemetria", "Semanal (7D x 24h)")
    if "Turno" in modo:
        from metrics_manager import obtener_rango_turno_reciente
        t_ini = getattr(ctx, "turno_inicio", "07:00")
        t_fin = getattr(ctx, "turno_fin", "18:00")
        shift_start, shift_end = obtener_rango_turno_reciente(t_ini, t_fin, now_dt)
        rango_ini = shift_start
        rango_fin = min(now_dt, shift_end)
    elif "Semanal" in modo:
        periodo_horas = 168

    for equipo in ctx.equipos:
        ip = equipo["ip"]
        monitor = ctx.monitors.get(ip)
        if monitor and getattr(monitor, "status", "") == "Conectado":
            online += 1
        total_disconnects += int(getattr(monitor, "desconexiones_count", 0) or 0)

        if ctx.metricas:
            if hasattr(ctx.metricas, "analizar_desconexiones_y_downtime"):
                analisis = ctx.metricas.analizar_desconexiones_y_downtime(
                    ip,
                    periodo_horas=periodo_horas,
                    rango_inicio=rango_ini,
                    rango_fin=rango_fin,
                )
                total_microcortes += analisis.get("microcortes_count", 0)
                dt_dev = analisis.get("downtime_segundos", 0.0)
                total_downtime_sec += dt_dev
                if dt_dev > max_downtime_sec:
                    max_downtime_sec = dt_dev
                uptimes_periodo.append(analisis.get("uptime_periodo", 100.0))
            else:
                uptimes_periodo.append(float(ctx.metricas.calcular_uptime(ip)))

    avg_uptime = sum(uptimes_periodo) / len(uptimes_periodo) if uptimes_periodo else 100.0
    offline = max(total_devices - online, 0)
    tls_mode = "Estricto" if ctx.tls_strict else "Flexible"

    fmt_dur = (
        ctx.metricas._formatear_duracion
        if ctx.metricas and hasattr(ctx.metricas, "_formatear_duracion")
        else lambda s: f"{int(s)}s"
    )

    if total_downtime_sec <= 0:
        downtime_display = "0s <font size=7.5 color='#16A34A'><b>(100% Operativo)</b></font>"
    else:
        avg_dt = total_downtime_sec / total_devices if total_devices > 0 else 0.0
        downtime_display = (
            f"<b>{fmt_dur(avg_dt)}</b> <font size=7.5 color='#64748B'>prom</font><br/>"
            f"<font size=7.5 color='#64748B'>Máx: </font><font size=8 color='#DC2626'><b>{fmt_dur(max_downtime_sec)}</b></font>"
        )

    cumplimiento_tag = " (Cumplido)" if avg_uptime >= ctx.sla_objetivo else " (Incumplido)"
    uptime_display = f"{avg_uptime:.1f}%{cumplimiento_tag}"

    cards = [
        ("Activos monitoreados", str(total_devices)),
        ("Equipos en línea", str(online)),
        ("Equipos fuera de línea", str(offline)),
        (f"SLA Uptime ({ctx.periodo_evaluado})", uptime_display),
        ("Microcortes detectados", str(total_microcortes)),
        (f"Downtime Red ({ctx.periodo_evaluado})", downtime_display),
    ]

    if ctx.incluir_cctv:
        cards.append(("Supervisión CCTV", f"{ctx.cameras_count} Cám. ({ctx.camera_max_streams} St)"))
    else:
        cards.append(("SLA Meta Contractual", f"{ctx.sla_objetivo:.1f}%"))

    cards.append(("Política TLS", tls_mode))

    rows = []
    row: list = []
    for title, value in cards:
        cell = Table(
            [
                [Paragraph(title, styles["card_title"])],
                [Paragraph(value, styles["card_value"])],
            ],
            colWidths=[59 * mm],
        )
        cell.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        row.append(cell)
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        while len(row) < 4:
            row.append("")
        rows.append(row)

    table = Table(rows, colWidths=[61.5 * mm] * 4, hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return table


def _build_devices_table(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [
            Paragraph("Activo", styles["table_header"]),
            Paragraph("IP / Host", styles["table_header"]),
            Paragraph("Estado", styles["table_header"]),
            Paragraph("Uptime 30d", styles["table_header"]),
            Paragraph("Latencia 1h", styles["table_header"]),
            Paragraph("Microcortes", styles["table_header"]),
            Paragraph(f"Downtime ({ctx.periodo_evaluado})", styles["table_header"]),
            Paragraph("Diagnóstico Operacional", styles["table_header"]),
        ]
    ]

    rango_ini = None
    rango_fin = None
    periodo_horas = 24
    now_dt = datetime.now()
    modo = getattr(ctx, "modo_telemetria", "Semanal (7D x 24h)")
    if "Turno" in modo:
        from metrics_manager import obtener_rango_turno_reciente
        t_ini = getattr(ctx, "turno_inicio", "07:00")
        t_fin = getattr(ctx, "turno_fin", "18:00")
        shift_start, shift_end = obtener_rango_turno_reciente(t_ini, t_fin, now_dt)
        rango_ini = shift_start
        rango_fin = min(now_dt, shift_end)
    elif "Semanal" in modo:
        periodo_horas = 168

    for equipo in ctx.equipos:
        ip = equipo["ip"]
        monitor = ctx.monitors.get(ip)
        status = getattr(monitor, "status", "Desconocido") if monitor else "Desconocido"
        uptime = float(ctx.metricas.calcular_uptime(ip)) if ctx.metricas else 0.0

        avg_lat = "N/A"
        lat_value = None
        microcortes_count = 0
        downtime_str = "0s"

        if ctx.metricas:
            datos = ctx.metricas.obtener_datos(ip, periodo_horas=1)
            if datos and datos["latencias"]:
                latencies = [lat for lat in datos["latencias"] if lat and lat > 0]
                if latencies:
                    lat_value = sum(latencies) / len(latencies)
                    avg_lat = f"{lat_value:.1f} ms"

            if hasattr(ctx.metricas, "analizar_desconexiones_y_downtime"):
                analisis = ctx.metricas.analizar_desconexiones_y_downtime(
                    ip,
                    periodo_horas=periodo_horas,
                    rango_inicio=rango_ini,
                    rango_fin=rango_fin,
                )
                microcortes_count = analisis.get("microcortes_count", 0)
                downtime_str = analisis.get("downtime_str", "0s")

        if status == "Desconectado":
            observation = "<font color='#DC2626'><b>Fuera de servicio (Atención inmediata)</b></font>"
        elif microcortes_count > 0:
            observation = f"<font color='#D97706'>Inestabilidad leve ({microcortes_count} eventos)</font>"
        elif lat_value is not None and lat_value >= 100:
            observation = "<font color='#D97706'>Latencia elevada (> 100ms)</font>"
        else:
            observation = "<font color='#16A34A'>Operación nominal estable</font>"

        status_bullet = "●"
        status_color_hex = _status_color(status)
        status_text = f"<font color='{status_color_hex}'><b>{status_bullet} {status}</b></font>"
        
        # Color del downtime
        dt_color = "#DC2626" if downtime_str != "0s" else "#16A34A"
        dt_text = f"<font color='{dt_color}'><b>{downtime_str}</b></font>"

        data.append(
            [
                Paragraph(str(equipo.get("label", "-")), styles["table_cell_bold"]),
                Paragraph(str(ip), styles["table_cell_mono"]),
                Paragraph(status_text, styles["table_cell"]),
                Paragraph(f"{uptime:.1f}%", styles["table_cell"]),
                Paragraph(avg_lat, styles["table_cell"]),
                Paragraph(str(microcortes_count), styles["table_cell"]),
                Paragraph(dt_text, styles["table_cell"]),
                Paragraph(observation, styles["table_cell"]),
            ]
        )

    row_pad = 1.8 if len(ctx.equipos) > 10 else 3.5
    table = Table(
        data,
        colWidths=[48 * mm, 25 * mm, 28 * mm, 20 * mm, 21 * mm, 21 * mm, 24 * mm, 59 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), row_pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), row_pad),
            ]
        )
    )
    return table


def _build_chart_image(fig: Figure, *, width: int, height: int) -> PDFImage:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=180)
    buffer.seek(0)
    return PDFImage(buffer, width=width, height=height)


def _build_visuals(ctx: ReportContext, styles: dict[str, ParagraphStyle], chart_width: float) -> list:
    if not ctx.metricas or not ctx.equipos:
        return [Paragraph("No hay datos históricos suficientes para analítica visual.", styles["muted"])]

    elements: list = []
    palette = ["#0284C7", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0D9488", "#E11D48", "#2563EB"]
    chart_width = max(chart_width, 520)

    # 1. Obtener telemetría completa unificada del motor analítico
    payload = None
    if hasattr(ctx.metricas, "obtener_telemetria_completa"):
        payload = ctx.metricas.obtener_telemetria_completa(
            equipos=ctx.equipos,
            filtro_host=getattr(ctx, "filtro_host", "Todos los Equipos"),
            modo=getattr(ctx, "modo_telemetria", "Semanal (7D x 24h)"),
            turno_inicio=getattr(ctx, "turno_inicio", "07:00"),
            turno_fin=getattr(ctx, "turno_fin", "18:00"),
        )

    # 2. Extraer o armar datos de Heatmap primero para determinar el layout dinámico
    hm = payload.get("heatmap_data") if payload else None
    if not hm and hasattr(ctx.metricas, "obtener_matriz_semanal"):
        matriz_info = ctx.metricas.obtener_matriz_semanal()
        if matriz_info:
            hm = {
                "mode": "Semanal (7D x 24h)",
                "title": "Matriz Semanal de Disponibilidad (Lunes a Domingo × 24 Horas)",
                "rango_subtitulo": "Últimos 7 Días • Monitoreo continuo 24 horas",
                "ncols": 24,
                "nrows": 7,
                "col_labels": matriz_info["horas_etiquetas"],
                "row_labels": matriz_info["dias_etiquetas"],
                "matriz_disp": matriz_info["disponibilidad"],
            }

    # Determinación dinámica de distribución ejecutiva:
    # Si el heatmap por equipos tiene más de 10 activos (nrows > 10),
    # no deben forzarse en la misma hoja para no comprometer la legibilidad de cada fila.
    # En ese caso, Latencia toma la Hoja 2 con altura generosa y Heatmap pasa a la Hoja 3 con altura completa.
    # Si son 10 equipos o menos (o modo semanal de 7 días), comparten dinámicamente la Hoja 2
    # con proporciones balanceadas y espacio de aire entre ellos.
    nrows = hm.get("nrows", 0) if hm else 0
    is_by_equipment = "Por Equipo" in hm.get("mode", "") if hm else False
    separate_pages = is_by_equipment and (nrows > 10)

    # ── 1. Gráfico de Latencia Avanzado (Adaptado al modo activo) ─────────
    fig_lat_h = 3.6 if separate_pages else 2.65
    lat_height = 220 if separate_pages else 155

    fig_lat = Figure(figsize=(12.0, fig_lat_h), facecolor="white", dpi=100)
    ax_lat = fig_lat.add_subplot(111)
    ax_lat.set_facecolor("#FAFAFA")
    ax_lat.grid(True, linestyle="--", alpha=0.35, color="#94A3B8")
    ax_lat.set_ylabel("Latencia (ms)", fontsize=9, fontweight="bold", color="#1E293B")
    ax_lat.tick_params(axis="both", labelsize=8, colors="#475569")

    has_lat_data = False
    all_latencies = []

    if payload and payload.get("serie_latencia"):
        for i, serie in enumerate(payload["serie_latencia"]):
            color = palette[i % len(palette)]
            x_vals = serie.get("x_vals", [])
            y_vals = serie.get("y_vals", [])
            if x_vals and y_vals:
                ax_lat.plot(x_vals, y_vals, label=serie["label"][:20], linewidth=1.5, color=color)
                ax_lat.fill_between(x_vals, y_vals, alpha=0.08, color=color)
                has_lat_data = True
                all_latencies.extend([y for y in y_vals if y > 0])

        if payload.get("latencia_min_x") and payload.get("latencia_max_x"):
            ax_lat.set_xlim(payload["latencia_min_x"], payload["latencia_max_x"])

        lat_title = payload.get("latencia_title", "Telemetría de Latencia & Rendimiento Temporal")
        stats_bar = payload.get("stats_text", "")
    else:
        # Fallback a consulta directa de 24h
        for index, equipo in enumerate(ctx.equipos):
            datos = ctx.metricas.obtener_datos(equipo["ip"], periodo_horas=24)
            if datos and datos["latencias"] and datos["timestamps"]:
                ts_list = datos["timestamps"]
                lats = datos["latencias"]
                color = palette[index % len(palette)]
                step = max(1, len(lats) // 60)
                x_vals = ts_list[::step]
                y_vals = [lats[k] if lats[k] is not None else 0 for k in range(0, len(lats), step)]
                ax_lat.plot(x_vals, y_vals, label=equipo["label"][:20], linewidth=1.5, color=color)
                ax_lat.fill_between(x_vals, y_vals, alpha=0.08, color=color)
                has_lat_data = True
                all_latencies.extend([y for y in y_vals if y > 0])

        lat_title = f"Telemetría de Latencia & Rendimiento Temporal ({ctx.periodo_evaluado})"
        min_l = min(all_latencies) if all_latencies else 0.0
        avg_l = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
        max_l = max(all_latencies) if all_latencies else 0.0
        p95_l = np.percentile(all_latencies, 95) if all_latencies else 0.0
        stats_bar = (
            f"Métricas ({ctx.periodo_evaluado}):  Mín: {min_l:.1f}ms  │  Prom: {avg_l:.1f}ms  "
            f"│  P95: {p95_l:.1f}ms  │  Máx: {max_l:.1f}ms"
        )

    lat_items: list = []
    if has_lat_data:
        ax_lat.axhline(y=100, color="#DC2626", linestyle="--", linewidth=1.1, label="Límite SLA Advertencia (100 ms)", alpha=0.8)
        modo = getattr(ctx, "modo_telemetria", "")
        if "Semanal" in modo:
            ax_lat.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
        else:
            ax_lat.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

        ax_lat.legend(
            fontsize=7.5 if separate_pages else 7.0,
            loc="upper right",
            ncol=4,
            frameon=True,
            facecolor="white",
            edgecolor="#CBD5E1",
        )
        fig_lat.autofmt_xdate(rotation=0, ha="center")
        fig_lat.tight_layout()

        lat_items = [
            Paragraph(lat_title, styles["section"]),
            Spacer(1, 2),
            Paragraph(f"<b>{stats_bar}</b>", styles["muted_highlight"]),
            Spacer(1, 4),
            _build_chart_image(fig_lat, width=chart_width, height=lat_height),
        ]

    # ── 2. Mapa de Calor Discreto (Pastillas Redondeadas Dinámico) ─────────
    hm_items: list = []
    if hm:
        matriz_disp = hm["matriz_disp"]
        row_labels = hm["row_labels"]
        col_labels = hm["col_labels"]
        nrows = hm["nrows"]
        ncols = hm["ncols"]

        if separate_pages:
            fig_hm_h = min(7.5, max(4.0, 0.28 * nrows + 1.2))
            hm_height = min(430, max(260, int(19 * nrows + 60)))
            ytick_font = 8.5 if nrows <= 12 else (8.0 if nrows <= 16 else 7.2)
            top_margin = 0.91
            bottom_margin = 0.08
        else:
            fig_hm_h = max(2.8, min(3.8, 0.24 * nrows + 1.3)) if is_by_equipment else 2.9
            hm_height = min(228, max(170, int(18 * nrows + 48))) if is_by_equipment else 180
            ytick_font = 8.5
            top_margin = 0.88
            bottom_margin = 0.10

        fig_hm = Figure(figsize=(12.0, fig_hm_h), facecolor="white", dpi=100)
        ax_hm = fig_hm.add_subplot(111)
        ax_hm.set_facecolor("#FAFAFA")

        colores_escala = ["#F1F5F9", "#C8E6C9", "#81C784", "#2E7D32", "#0B3C26"]
        tile_w = 0.82
        tile_h = 0.72

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

                color_box = colores_escala[c_idx]
                box = FancyBboxPatch(
                    (c - tile_w / 2, nrows - 1 - r - tile_h / 2),
                    tile_w,
                    tile_h,
                    boxstyle="round,pad=0.03,rounding_size=0.18",
                    facecolor=color_box,
                    edgecolor="#E2E8F0",
                    linewidth=0.5,
                )
                ax_hm.add_patch(box)

        ax_hm.set_xlim(-0.7, max(0.5, ncols - 0.3))
        ax_hm.set_ylim(-1.25, max(0.5, nrows - 0.3))
        ax_hm.xaxis.tick_top()
        ax_hm.set_xticks(range(ncols))
        ax_hm.set_xticklabels(col_labels, fontsize=7.5, color="#475569")
        ax_hm.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0)
        ax_hm.set_yticks(range(nrows))
        ax_hm.set_yticklabels(list(reversed(row_labels)), fontsize=ytick_font, fontweight="bold", color="#1E293B")
        ax_hm.tick_params(axis="y", left=False, length=0)

        for spine in ax_hm.spines.values():
            spine.set_visible(False)

        # Leyenda de escala
        legend_start_x = max(0.0, ncols - 6.8)
        leg_w, leg_h = 0.70, 0.32
        legend_y = -0.92
        ax_hm.text(legend_start_x - 0.4, legend_y + leg_h / 2, "Menos", fontsize=7.5, color="#64748B", ha="right", va="center")
        for i, col in enumerate(colores_escala):
            patch_leg = FancyBboxPatch(
                (legend_start_x + (i * 0.85), legend_y),
                leg_w,
                leg_h,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                facecolor=col,
                edgecolor="#CBD5E1",
                linewidth=0.4,
            )
            ax_hm.add_patch(patch_leg)
        ax_hm.text(legend_start_x + (len(colores_escala) * 0.85) + 0.3, legend_y + leg_h / 2, "Más", fontsize=7.5, color="#64748B", ha="left", va="center")

        left_margin = 0.20 if is_by_equipment else 0.06
        fig_hm.subplots_adjust(left=left_margin, right=0.98, top=top_margin, bottom=bottom_margin)

        hm_items = [
            Paragraph(hm.get("title", "Matriz de Disponibilidad (Mapa de Calor Discreto)"), styles["section"]),
            Spacer(1, 2),
            Paragraph(
                hm.get("rango_subtitulo", "Mapeo de disponibilidad operacional adaptado al perfil temporal de supervisión."),
                styles["muted"],
            ),
            Spacer(1, 4),
            _build_chart_image(fig_hm, width=chart_width, height=hm_height),
        ]

    # ── Ensamblado de Flujo Visual con Control de Paginación y Aire Ejecutivo ───
    if lat_items and hm_items:
        if separate_pages:
            elements.append(KeepTogether(lat_items))
            elements.append(PageBreak())
            elements.append(KeepTogether(hm_items))
        else:
            elements.append(KeepTogether(lat_items))
            elements.append(Spacer(1, 14))  # Espacio de aire limpio entre ambos gráficos
            elements.append(KeepTogether(hm_items))
    elif lat_items:
        elements.append(KeepTogether(lat_items))
    elif hm_items:
        elements.append(KeepTogether(hm_items))

    return elements


def _build_dynamic_intelligence_capsule(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> Table:
    """Construye la cápsula de dictamen técnico y recomendaciones según el comportamiento diario."""
    if not ctx.metricas or not hasattr(ctx.metricas, "evaluar_estabilidad_global"):
        return Table([[Paragraph("Evaluación heurística no disponible.", styles["muted"])]])

    modo = getattr(ctx, "modo_telemetria", "")
    periodo_horas = 168 if "Semanal" in modo else 24
    evaluacion = ctx.metricas.evaluar_estabilidad_global(ctx.equipos, periodo_horas=periodo_horas)

    estado = evaluacion["estado"]
    badge_texto = evaluacion["badge"]
    color_banner = evaluacion["color_hex"]
    diagnostico = evaluacion["diagnostico"]
    causa_raiz = evaluacion["causa_raiz"]
    recomendaciones = evaluacion["recomendaciones"]

    # Color de fondo según severidad
    bg_banner = "#DCFCE7" if estado == "ESTABLE" else "#FEF3C7" if estado == "DEGRADADA_INTERMITENTE" else "#FEE2E2"

    banner_p = Paragraph(f"<b>{badge_texto}</b>", styles["capsule_badge"])

    content_cells = [
        [
            Paragraph("<b>1. Diagnóstico Operacional:</b>", styles["capsule_subhead"]),
            Paragraph(diagnostico, styles["capsule_body"]),
        ],
        [
            Paragraph("<b>2. Causa Raíz Probable:</b>", styles["capsule_subhead"]),
            Paragraph(causa_raiz, styles["capsule_body"]),
        ],
        [
            Paragraph("<b>3. Recomendaciones Técnicas:</b>", styles["capsule_subhead"]),
            Paragraph("<br/>".join([f"• {r}" for r in recomendaciones]), styles["capsule_body"]),
        ],
    ]

    inner_table = Table(content_cells, colWidths=[68 * mm, 174 * mm])
    inner_table.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    card_data = [
        [banner_p],
        [inner_table],
    ]

    capsule = Table(card_data, colWidths=[246 * mm], hAlign="LEFT")
    capsule.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(bg_banner)),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor(color_banner)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(color_banner)),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return capsule


def _build_timeline_table(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> list:
    """Construye la tabla de auditoría cronológica de caídas mayores con segundo exacto."""
    if not ctx.metricas or not hasattr(ctx.metricas, "obtener_timeline_incidencias"):
        return []

    modo = getattr(ctx, "modo_telemetria", "24h")
    turno_ini = getattr(ctx, "turno_inicio", "07:00")
    turno_fin = getattr(ctx, "turno_fin", "18:00")

    timeline = ctx.metricas.obtener_timeline_incidencias(
        ctx.equipos,
        periodo_horas=24,
        modo=modo,
        turno_inicio=turno_ini,
        turno_fin=turno_fin,
    )
    if not timeline:
        return []

    data = [
        [
            Paragraph("Activo Afectado", styles["table_header"]),
            Paragraph("IP / Host", styles["table_header"]),
            Paragraph("Inicio de Falla", styles["table_header"]),
            Paragraph("Hora Término", styles["table_header"]),
            Paragraph("Impacto en Período", styles["table_header"]),
            Paragraph("Duración Total Falla", styles["table_header"]),
            Paragraph("Severidad / Estado", styles["table_header"]),
        ]
    ]

    for item in timeline[:6]:
        sev_color = "#DC2626" if "Crítico" in item["severidad"] or item.get("en_curso") else "#D97706"
        sev_text = f"<font color='{sev_color}'><b>{item['severidad']}</b></font>"

        dur_per_text = f"<font color='#DC2626'><b>{item.get('duracion_periodo_str', item['duracion_str'])}</b></font>"
        dur_tot_text = f"<font color='#64748B'><b>{item.get('duracion_str', item['duracion_str'])}</b></font>"

        data.append(
            [
                Paragraph(item["activo"], styles["table_cell_bold"]),
                Paragraph(item["ip"], styles["table_cell_mono"]),
                Paragraph(item["inicio_str"], styles["table_cell"]),
                Paragraph(item["fin_str"], styles["table_cell"]),
                Paragraph(dur_per_text, styles["table_cell"]),
                Paragraph(dur_tot_text, styles["table_cell"]),
                Paragraph(sev_text, styles["table_cell"]),
            ]
        )

    t = Table(
        data,
        colWidths=[45 * mm, 25 * mm, 32 * mm, 36 * mm, 32 * mm, 36 * mm, 40 * mm],
        repeatRows=1,
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    t_block = [
        Paragraph("Registro Cronológico de Eventos Críticos & Caídas Significativas", styles["section"]),
        Spacer(1, 2),
        Paragraph(
            "Detalle segundo a segundo de desconexiones registradas en base de datos. "
            "Se audita el impacto efectivo dentro del período evaluado y la duración total de la contingencia "
            "preservada sin reinicios arbitrarios al abrir turnos.",
            styles["muted"],
        ),
        Spacer(1, 4),
        t,
    ]
    return [KeepTogether(t_block), Spacer(1, 6)]


def _build_signatures_table(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> Table:
    """Genera el bloque formal de firmas de conformidad técnica y recepción cliente."""
    emisor_content = [
        Paragraph("<b>EMITIDO Y CERTIFICADO POR:</b>", styles["capsule_subhead"]),
        Spacer(1, 10),
        Paragraph("____________________________________________", styles["body"]),
        Paragraph(f"<b>{ctx.generated_by}</b>", styles["body"]),
        Paragraph("Ingeniería de Redes & Monitoreo NOC", styles["muted"]),
        Paragraph(f"Suite {ctx.app_name} {ctx.version}", styles["muted"]),
    ]
    cliente_content = [
        Paragraph("<b>CONFORMIDAD DE RECEPCIÓN (CLIENTE):</b>", styles["capsule_subhead"]),
        Spacer(1, 10),
        Paragraph("____________________________________________", styles["body"]),
        Paragraph("<b>Firma y Timbre Autorizado</b>", styles["body"]),
        Paragraph(f"Entidad: <b>{ctx.empresa_cliente}</b>", styles["muted"]),
        Paragraph(f"Sitio / Planta: <b>{ctx.sitio_planta}</b>", styles["muted"]),
    ]

    table = Table(
        [[emisor_content, cliente_content]],
        colWidths=[120 * mm, 120 * mm],
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (0, 0), 0.8, colors.HexColor("#CBD5E1")),
                ("BOX", (1, 0), (1, 0), 0.8, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def build_network_report(ctx: ReportContext) -> str:
    os.makedirs(os.path.dirname(ctx.filename) or ".", exist_ok=True)
    styles = {
        "title": _paragraph_style("title", size=20, color="#0F172A", leading=24, bold=True),
        "subtitle": _paragraph_style("subtitle", size=10, color="#475569"),
        "section": _paragraph_style("section", size=11, color="#0F172A", bold=True, keepWithNext=True),
        "subheader": _paragraph_style("subheader", size=9.5, color="#1E293B", bold=True, keepWithNext=True),
        "body": _paragraph_style("body", size=8.5, color="#1F2937", leading=12),
        "muted": _paragraph_style("muted", size=8, color="#64748B", leading=11),
        "muted_highlight": _paragraph_style("muted_highlight", size=8, color="#0F172A", leading=11),
        "card_title": _paragraph_style("card_title", size=7.5, color="#64748B"),
        "card_value": _paragraph_style("card_value", size=13, color="#0F172A", bold=True, leading=15),
        "table_header": _paragraph_style("table_header", size=7.5, color="#FFFFFF", bold=True),
        "table_cell": _paragraph_style("table_cell", size=7.5, color="#1F2937"),
        "table_cell_bold": _paragraph_style("table_cell_bold", size=7.5, color="#0F172A", bold=True),
        "table_cell_mono": _paragraph_style("table_cell_mono", size=7.5, color="#334155"),
        "capsule_badge": _paragraph_style("capsule_badge", size=9.5, color="#0F172A", bold=True),
        "capsule_subhead": _paragraph_style("capsule_subhead", size=8.5, color="#0F172A", bold=True),
        "capsule_body": _paragraph_style("capsule_body", size=8, color="#334155", leading=11),
    }

    generated_at = datetime.now()
    doc = SimpleDocTemplate(
        ctx.filename,
        pagesize=landscape(letter),
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    elements: list = []

    # ── Cabecera Principal con Logo y Datos Empresariales Fortune 500 ─────────────
    title_column = [
        Paragraph(ctx.app_name, styles["title"]),
        Paragraph(ctx.tagline, styles["subtitle"]),
        Spacer(1, 2),
        Paragraph(
            (
                f"<b>Reporte Ejecutivo-Operacional de Telemetría</b><br/>"
                f"Empresa / Cliente: <b>{ctx.empresa_cliente}</b> &nbsp;│&nbsp; Sitio / Faena: <b>{ctx.sitio_planta}</b><br/>"
                f"Período Evaluado: <b>{ctx.periodo_evaluado}</b> &nbsp;│&nbsp; Fecha de corte: <b>{generated_at.strftime('%d/%m/%Y %H:%M:%S')}</b><br/>"
                f"Generado por: <b>{ctx.generated_by}</b>"
            ),
            styles["body"],
        ),
    ]
    title_table = Table(
        [
            [
                title_column,
                PDFImage(ctx.logo_path, width=22 * mm, height=22 * mm)
                if ctx.logo_path and os.path.exists(ctx.logo_path)
                else "",
            ]
        ],
        colWidths=[222 * mm, 24 * mm],
    )
    title_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(title_table)
    elements.append(Spacer(1, 6))

    # ── Resumen Ejecutivo ─────────────────────────────────────────────────────────
    elements.append(Paragraph("Resumen Ejecutivo de Infraestructura", styles["section"]))
    elements.append(Spacer(1, 3))
    elements.append(_build_summary_cards(ctx, styles))
    elements.append(Spacer(1, 7))

    # ── Tabla de Activos Monitoreados ─────────────────────────────────────────────
    elements.append(Paragraph("Inventario y Estado de Activos Monitoreados", styles["section"]))
    elements.append(Spacer(1, 3))
    elements.append(_build_devices_table(ctx, styles))

    # ── Página 2: Analítica Visual de Telemetría ───────────────────────────────────
    visuals = _build_visuals(ctx, styles, doc.width)
    if visuals:
        elements.append(PageBreak())
        elements.extend(visuals)

    # ── Página 3: Cápsula Dinámica de Inteligencia & Recomendaciones ───────────────
    elements.append(PageBreak())
    capsule_items = [
        Paragraph("Dictamen de Estabilidad & Análisis de Inteligencia Operacional", styles["section"]),
        Spacer(1, 2),
        Paragraph(
            "Conclusiones y diagnóstico heurístico generado por el motor de telemetría de Argos Guard, "
            "evaluando fluctuaciones de señal, microcortes y salud integral de enlaces.",
            styles["muted"],
        ),
        Spacer(1, 4),
        _build_dynamic_intelligence_capsule(ctx, styles),
    ]
    elements.append(KeepTogether(capsule_items))
    elements.append(Spacer(1, 6))

    # ── Timeline Cronológico de Incidencias Críticas ──────────────────────────────
    timeline_elements = _build_timeline_table(ctx, styles)
    if timeline_elements:
        elements.extend(timeline_elements)

    # ── Sección OSINT (si existen datos) ──────────────────────────────────────────
    if ctx.osint_data:
        elements.append(Paragraph("Análisis de Inteligencia y Amenazas (OSINT)", styles["section"]))
        elements.append(Spacer(1, 3))

        for module_name, results in ctx.osint_data.items():
            if not results:
                continue
            elements.append(Paragraph(f"Módulo: {module_name}", styles["subheader"]))
            elements.append(Spacer(1, 2))

            table_data = []
            ncols = len(results[0])
            headers = ["Parámetro/Item"] * (ncols - 2) + ["Riesgo", "Impacto"] if ncols >= 2 else ["Dato"] * ncols
            table_data.append([Paragraph(h, styles["table_header"]) for h in headers])

            table_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ("TOPPADDING", (0, 0), (-1, 0), 4),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )

            for row_idx, res in enumerate(results, start=1):
                row_cells = []
                for val in res:
                    val_str = str(val) if val is not None else ""
                    row_cells.append(Paragraph(val_str, styles["table_cell"]))
                table_data.append(row_cells)

                if len(res) >= 2:
                    riesgo_val = str(res[-2])
                    bg_color = None
                    if "🔴" in riesgo_val:
                        bg_color = colors.HexColor("#FEE2E2")
                    elif "🟡" in riesgo_val:
                        bg_color = colors.HexColor("#FEF3C7")
                    elif "🟢" in riesgo_val:
                        bg_color = colors.HexColor("#DCFCE7")

                    if bg_color:
                        col_idx = len(res) - 2
                        table_style.add("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), bg_color)

            col_width = (doc.width) / max(1, ncols)
            t = Table(table_data, colWidths=[col_width] * ncols, hAlign="LEFT")
            t.setStyle(table_style)
            elements.append(t)
            elements.append(Spacer(1, 8))

    # ── Notas Finales y Certificación ─────────────────────────────────────────────
    if ctx.incluir_cctv:
        notes = (
            f"Este documento refleja la telemetría operacional bajo política TLS "
            f"{'estricta' if ctx.tls_strict else 'flexible controlada'}, con {ctx.camera_max_streams} stream(s) "
            f"simultáneo(s) y {ctx.cameras_count} cámara(s) registradas. "
            f"Emitido y validado digitalmente por la suite <b>{ctx.app_name} {ctx.version}</b>."
        )
    else:
        notes = (
            f"Este documento refleja la telemetría operacional bajo política TLS "
            f"{'estricta' if ctx.tls_strict else 'flexible controlada'}, auditando disponibilidad, "
            f"latencia temporal y cumplimiento de SLA de red. Supervisión CCTV no requerida para este perfil. "
            f"Emitido y validado digitalmente por la suite <b>{ctx.app_name} {ctx.version}</b>."
        )

    signatures_block = [
        Paragraph("Notas de Cumplimiento & Certificación de Emisión", styles["section"]),
        Spacer(1, 2),
        Paragraph(notes, styles["body"]),
        Spacer(1, 4),
        _build_signatures_table(ctx, styles),
    ]
    elements.append(KeepTogether(signatures_block))
    elements.append(Spacer(1, 4))

    def _decorate_page(canvas, _doc):
        canvas.setTitle(f"{ctx.app_name} - Reporte de Telemetría")
        canvas.setAuthor("ANVIC SECURITY")
        canvas.setSubject("Reporte técnico-operacional de telemetría de red")
        canvas.setCreator(ctx.app_name)
        canvas.setKeywords("ANVIC, telemetria, red, CCTV, ciberseguridad, reporte")
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(16 * mm, 8 * mm, 262 * mm, 8 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        ver_str = ctx.version if ctx.version.startswith("v") else f"v{ctx.version}"
        canvas.drawString(16 * mm, 5 * mm, f"{ctx.app_name} {ver_str} • {ctx.empresa_cliente} • {ctx.sitio_planta}")
        canvas.drawRightString(262 * mm, 5 * mm, generated_at.strftime("%d/%m/%Y %H:%M"))
        canvas.restoreState()

    doc.build(elements, onFirstPage=_decorate_page, onLaterPages=_decorate_page)
    return ctx.filename
