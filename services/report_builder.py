"""Generador de reportes PDF corporativos para Anvic Network Sentinel."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from matplotlib.figure import Figure
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as PDFImage,
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
    osint_data: dict | None = None


def _status_color(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized == "conectado":
        return "#2E7D32"
    if normalized == "desconectado":
        return "#C62828"
    return "#6B7280"


def _paragraph_style(name: str, *, size: int, color: str, leading: int | None = None, bold: bool = False) -> ParagraphStyle:
    base = getSampleStyleSheet()["BodyText"]
    return ParagraphStyle(
        name=name,
        parent=base,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        leading=leading or (size + 3),
        textColor=colors.HexColor(color),
    )


def _build_summary_cards(ctx: ReportContext, styles: dict[str, ParagraphStyle]) -> Table:
    total_devices = len(ctx.equipos)
    online = 0
    total_disconnects = 0
    uptimes: list[float] = []

    for equipo in ctx.equipos:
        monitor = ctx.monitors.get(equipo["ip"])
        if monitor and getattr(monitor, "status", "") == "Conectado":
            online += 1
        total_disconnects += int(getattr(monitor, "desconexiones_count", 0) or 0)
        if ctx.metricas:
            uptimes.append(float(ctx.metricas.calcular_uptime(equipo["ip"])))

    avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 0.0
    offline = max(total_devices - online, 0)
    tls_mode = "Estricto" if ctx.tls_strict else "Flexible"

    cards = [
        ("Activos monitoreados", str(total_devices)),
        ("Equipos en linea", str(online)),
        ("Equipos fuera de linea", str(offline)),
        ("Uptime promedio", f"{avg_uptime:.1f}%"),
        ("Desconexiones", str(total_disconnects)),
        ("Camaras registradas", str(ctx.cameras_count)),
        ("Streams maximos", str(ctx.camera_max_streams)),
        ("Politica TLS", tls_mode),
    ]

    rows = []
    row: list = []
    for title, value in cards:
        cell = Table(
            [
                [Paragraph(title, styles["card_title"])],
                [Paragraph(value, styles["card_value"])],
            ],
            colWidths=[70 * mm],
        )
        cell.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
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

    table = Table(rows, colWidths=[74 * mm] * 4, hAlign="LEFT")
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
            Paragraph("Desconexiones", styles["table_header"]),
            Paragraph("Observacion", styles["table_header"]),
        ]
    ]

    for equipo in ctx.equipos:
        ip = equipo["ip"]
        monitor = ctx.monitors.get(ip)
        status = getattr(monitor, "status", "Desconocido") if monitor else "Desconocido"
        disconnects = int(getattr(monitor, "desconexiones_count", 0) or 0)
        uptime = float(ctx.metricas.calcular_uptime(ip)) if ctx.metricas else 0.0
        avg_lat = "N/A"
        lat_value = None
        if ctx.metricas:
            datos = ctx.metricas.obtener_datos(ip, periodo_horas=1)
            if datos and datos["latencias"]:
                latencies = [lat for lat in datos["latencias"] if lat and lat > 0]
                if latencies:
                    lat_value = sum(latencies) / len(latencies)
                    avg_lat = f"{lat_value:.1f} ms"

        if status == "Desconectado":
            observation = "Requiere atencion operativa"
        elif lat_value is not None and lat_value >= 120:
            observation = "Latencia elevada"
        else:
            observation = "Operacion estable"

        status_text = f'<font color="{_status_color(status)}"><b>{status}</b></font>'
        data.append(
            [
                Paragraph(str(equipo.get("label", "-")), styles["table_cell"]),
                Paragraph(str(ip), styles["table_cell"]),
                Paragraph(status_text, styles["table_cell"]),
                Paragraph(f"{uptime:.1f}%", styles["table_cell"]),
                Paragraph(avg_lat, styles["table_cell"]),
                Paragraph(str(disconnects), styles["table_cell"]),
                Paragraph(observation, styles["table_cell"]),
            ]
        )

    table = Table(
        data,
        colWidths=[60 * mm, 38 * mm, 28 * mm, 24 * mm, 24 * mm, 24 * mm, 52 * mm],
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
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _build_chart_image(fig: Figure, *, width: int, height: int) -> PDFImage:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    buffer.seek(0)
    return PDFImage(buffer, width=width, height=height)


def _build_visuals(ctx: ReportContext, styles: dict[str, ParagraphStyle], chart_width: float) -> list:
    if not ctx.metricas or not ctx.equipos:
        return [Paragraph("No hay datos historicos suficientes para analitica visual.", styles["muted"])]

    elements: list = []
    palette = ["#0EA5E9", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6", "#14B8A6"]
    chart_width = max(chart_width, 520)

    fig_lat = Figure(figsize=(12.2, 4.0), facecolor="white")
    ax_lat = fig_lat.add_subplot(111)
    ax_lat.set_title("Latencia historica - ultimas 24 horas", fontsize=13)
    ax_lat.grid(True, alpha=0.25)
    ax_lat.set_ylabel("Milisegundos", fontsize=10)
    ax_lat.tick_params(axis="both", labelsize=9)
    has_lat_data = False
    for index, equipo in enumerate(ctx.equipos):
        datos = ctx.metricas.obtener_datos(equipo["ip"], periodo_horas=24)
        if datos and datos["latencias"]:
            ax_lat.plot(
                range(len(datos["latencias"])),
                datos["latencias"],
                label=equipo["label"][:22],
                linewidth=1.8,
                color=palette[index % len(palette)],
            )
            has_lat_data = True
    if has_lat_data:
        ax_lat.set_xlabel("Muestras historicas", fontsize=10)
        ax_lat.legend(fontsize=8, loc="upper right", ncol=2, frameon=False)
        elements.append(Paragraph("Analitica de rendimiento", styles["section"]))
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "Curva comparativa de latencia para facilitar revision operativa, tendencias y deteccion de degradacion.",
                styles["muted"],
            )
        )
        elements.append(Spacer(1, 6))
        elements.append(_build_chart_image(fig_lat, width=chart_width, height=230))
        elements.append(Spacer(1, 14))

    heatmap_data = []
    labels = []
    for equipo in ctx.equipos:
        labels.append(equipo["label"][:20])
        datos = ctx.metricas.obtener_datos(equipo["ip"], periodo_horas=24)
        if datos and datos["estados"]:
            blocks = np.array_split(datos["estados"], 24)
            availability = [
                (sum(1 for state in block if state == 1) / len(block)) if len(block) > 0 else 0
                for block in blocks
            ]
            heatmap_data.append(availability)
        else:
            heatmap_data.append([0] * 24)

    if heatmap_data:
        fig_hm = Figure(figsize=(12.2, 4.6), facecolor="white")
        ax_hm = fig_hm.add_subplot(111)
        ax_hm.set_title("Mapa de calor de disponibilidad por hora", fontsize=13)
        ax_hm.imshow(heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
        ax_hm.set_yticks(range(len(labels)))
        ax_hm.set_yticklabels(labels, fontsize=8)
        ax_hm.set_xticks(range(0, 24, 2))
        ax_hm.set_xticklabels([f"{hour:02d}:00" for hour in range(0, 24, 2)], fontsize=8)
        ax_hm.set_xlabel("Tramo horario", fontsize=10)
        elements.append(Paragraph("Disponibilidad operacional", styles["section"]))
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "Visual de disponibilidad por equipo y franja horaria para detectar ventanas de caida y comportamiento repetitivo.",
                styles["muted"],
            )
        )
        elements.append(Spacer(1, 6))
        elements.append(_build_chart_image(fig_hm, width=chart_width, height=255))

    return elements


def build_network_report(ctx: ReportContext) -> str:
    os.makedirs(os.path.dirname(ctx.filename) or ".", exist_ok=True)
    styles = {
        "title": _paragraph_style("title", size=20, color="#0F172A", leading=24, bold=True),
        "subtitle": _paragraph_style("subtitle", size=10, color="#475569"),
        "section": _paragraph_style("section", size=13, color="#0F172A", bold=True),
        "body": _paragraph_style("body", size=9, color="#1F2937", leading=12),
        "muted": _paragraph_style("muted", size=9, color="#64748B"),
        "card_title": _paragraph_style("card_title", size=8, color="#475569"),
        "card_value": _paragraph_style("card_value", size=17, color="#0F172A", bold=True),
        "table_header": _paragraph_style("table_header", size=8, color="#FFFFFF", bold=True),
        "table_cell": _paragraph_style("table_cell", size=8, color="#1F2937"),
    }

    generated_at = datetime.now()
    doc = SimpleDocTemplate(
        ctx.filename,
        pagesize=landscape(letter),
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
    )
    elements: list = []

    title_column = [
        Paragraph(ctx.app_name, styles["title"]),
        Paragraph(ctx.tagline, styles["subtitle"]),
        Spacer(1, 2),
        Paragraph(
            (
                f"<b>Reporte ejecutivo-operacional</b><br/>"
                f"Fecha de corte: {generated_at.strftime('%d/%m/%Y %H:%M:%S')}<br/>"
                f"Generado por: {ctx.generated_by}"
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
        colWidths=[230 * mm, 24 * mm],
    )
    title_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(title_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Resumen ejecutivo", styles["section"]))
    elements.append(Spacer(1, 4))
    elements.append(_build_summary_cards(ctx, styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Alcance de supervision incorporado", styles["section"]))
    elements.append(Spacer(1, 4))
    scope_text = (
        "Disponibilidad ICMP, diagnostico HTTP/HTTPS, escaneo controlado de puertos, "
        "SNMP basico, SSH de consulta, supervision visual de camaras, politica TLS configurable "
        "y evidencia historica para soporte operacional."
    )
    elements.append(Paragraph(scope_text, styles["body"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Estado de activos monitoreados", styles["section"]))
    elements.append(Spacer(1, 4))
    elements.append(_build_devices_table(ctx, styles))
    elements.append(Spacer(1, 10))

    visuals = _build_visuals(ctx, styles, doc.width)
    if visuals:
        elements.append(PageBreak())
        elements.append(Paragraph("Analitica visual ampliada", styles["section"]))
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "Las siguientes visualizaciones se presentan en formato ampliado para facilitar analisis tecnico, revision ejecutiva y lectura en impresion o pantalla.",
                styles["body"],
            )
        )
        elements.append(Spacer(1, 10))
        elements.append(Spacer(1, 10))
        elements.extend(visuals)
        elements.append(Spacer(1, 10))

    if ctx.osint_data:
        elements.append(PageBreak())
        elements.append(Paragraph("Análisis de Inteligencia y Amenazas (OSINT)", styles["section"]))
        elements.append(Spacer(1, 4))
        
        for module_name, results in ctx.osint_data.items():
            if not results:
                continue
            elements.append(Paragraph(f"Módulo: {module_name}", styles["subheader"]))
            elements.append(Spacer(1, 4))
            
            table_data = []
            # Tratar de inferir cabeceras basados en la longitud de las filas (al menos 3)
            # En nuestro OSINT, la longitud puede variar pero sabemos que las 2 últimas son Riesgo e Impacto
            ncols = len(results[0])
            headers = ["Parámetro/Item"] * (ncols - 2) + ["Riesgo", "Impacto"] if ncols >= 2 else ["Dato"] * ncols
            table_data.append([Paragraph(h, styles["table_header"]) for h in headers])
            
            table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
            
            for row_idx, res in enumerate(results, start=1):
                row_cells = []
                for val in res:
                    val_str = str(val) if val is not None else ""
                    row_cells.append(Paragraph(val_str, styles["table_cell"]))
                table_data.append(row_cells)
                
                # Colorear celda de Riesgo si existe
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
                        
            # Ajustar anchos equitativamente
            col_width = (doc.width) / max(1, ncols)
            t = Table(table_data, colWidths=[col_width] * ncols, hAlign="LEFT")
            t.setStyle(table_style)
            elements.append(t)
            elements.append(Spacer(1, 10))

    elements.append(Paragraph("Notas de ciberseguridad y operacion", styles["section"]))
    elements.append(Spacer(1, 4))
    notes = (
        f"Este reporte refleja una operacion de red bajo politica TLS "
        f"{'estricta' if ctx.tls_strict else 'flexible controlada'}, "
        f"con {ctx.camera_max_streams} stream(s) simultaneo(s) como tope configurado "
        f"y {ctx.cameras_count} camara(s) registradas en la instalacion."
    )
    elements.append(Paragraph(notes, styles["body"]))
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            f"Documento emitido por {ctx.app_name} v{ctx.version}.",
            styles["muted"],
        )
    )

    def _decorate_page(canvas, _doc):
        canvas.setTitle(f"{ctx.app_name} - Reporte Operacional")
        canvas.setAuthor("ANVIC")
        canvas.setSubject("Reporte tecnico-operacional de monitoreo de red e instalaciones")
        canvas.setCreator(ctx.app_name)
        canvas.setKeywords("ANVIC, monitoreo, red, CCTV, soporte, ciberseguridad")
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(16 * mm, 8 * mm, 262 * mm, 8 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(16 * mm, 5 * mm, f"{ctx.app_name} v{ctx.version}")
        canvas.drawRightString(262 * mm, 5 * mm, generated_at.strftime("%d/%m/%Y %H:%M"))
        canvas.restoreState()

    doc.build(elements, onFirstPage=_decorate_page, onLaterPages=_decorate_page)
    return ctx.filename
