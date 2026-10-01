import os
import sqlite3
import datetime
from services.report_builder import ReportContext, build_network_report
from metrics_manager import MetricasHistoricas


def test_report_builder_cctv_toggle_false(tmp_path):
    pdf_path = str(tmp_path / "report_no_cctv.pdf")
    ctx = ReportContext(
        filename=pdf_path,
        app_name="Anvic Network Sentinel",
        version="2.2.6",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Ingeniero NOC • Administrador",
        equipos=[
            {"ip": "10.88.22.54", "label": "LPR Quilicura Entrada"},
            {"ip": "10.88.6.56", "label": "Kiosko Quilicura"},
        ],
        monitors={},
        metricas=None,
        tls_strict=True,
        cameras_count=2,
        camera_max_streams=1,
        empresa_cliente="Cliente Corporativo Top-Tier",
        sitio_planta="Planta Industrial Central",
        sla_objetivo=99.8,
        incluir_cctv=False,
        periodo_evaluado="Últimas 24 Horas",
    )
    result = build_network_report(ctx)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 1000


def test_report_builder_cctv_toggle_true(tmp_path):
    pdf_path = str(tmp_path / "report_with_cctv.pdf")
    ctx = ReportContext(
        filename=pdf_path,
        app_name="Anvic Network Sentinel",
        version="2.2.6",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Ingeniero NOC • Administrador",
        equipos=[
            {"ip": "10.88.22.54", "label": "LPR Quilicura Entrada"},
        ],
        monitors={},
        metricas=None,
        tls_strict=True,
        cameras_count=5,
        camera_max_streams=2,
        empresa_cliente="Cliente Corporativo Top-Tier",
        sitio_planta="Planta Industrial Central",
        sla_objetivo=99.5,
        incluir_cctv=True,
        periodo_evaluado="Turno Operativo (07:00 - 18:00)",
    )
    result = build_network_report(ctx)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 1000


def test_offline_timeline_and_exact_seconds_preservation(tmp_path):
    # Crear BD temporal para simular caída previa a la apertura de turno
    db_file = str(tmp_path / "test_timeline.db")
    metricas = MetricasHistoricas(db_path=db_file)

    now = datetime.datetime.now()
    # Caída que comenzó hace 3 horas (03:00) y el turno abre a las 07:00 (hace 1 hora)
    ts_falla_inicio = now - datetime.timedelta(hours=3, minutes=14, seconds=22)
    ts_recuperacion = now - datetime.timedelta(minutes=10, seconds=5)

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Estado ONLINE antes de la falla
    c.execute(
        "INSERT INTO mediciones (timestamp, ip, latencia, estado) VALUES (?, ?, ?, ?)",
        ((ts_falla_inicio - datetime.timedelta(seconds=15)).strftime("%Y-%m-%d %H:%M:%S"), "10.88.6.56", 20.0, 1),
    )
    # Segundo exacto de la falla (OFFLINE)
    c.execute(
        "INSERT INTO mediciones (timestamp, ip, latencia, estado) VALUES (?, ?, ?, ?)",
        (ts_falla_inicio.strftime("%Y-%m-%d %H:%M:%S"), "10.88.6.56", 0.0, 0),
    )
    # Durante la falla sigue OFFLINE
    c.execute(
        "INSERT INTO mediciones (timestamp, ip, latencia, estado) VALUES (?, ?, ?, ?)",
        ((ts_falla_inicio + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), "10.88.6.56", 0.0, 0),
    )
    # Recuperación
    c.execute(
        "INSERT INTO mediciones (timestamp, ip, latencia, estado) VALUES (?, ?, ?, ?)",
        (ts_recuperacion.strftime("%Y-%m-%d %H:%M:%S"), "10.88.6.56", 25.0, 1),
    )
    conn.commit()
    conn.close()

    equipos = [{"ip": "10.88.6.56", "label": "Kiosko Quilicura"}]
    timeline = metricas.obtener_timeline_incidencias(equipos, periodo_horas=24)

    assert len(timeline) >= 1
    incidencia = timeline[0]
    assert incidencia["activo"] == "Kiosko Quilicura"
    assert incidencia["ip"] == "10.88.6.56"
    assert ts_falla_inicio.strftime("%H:%M:%S") in incidencia["inicio_str"]
    assert ts_recuperacion.strftime("%H:%M:%S") in incidencia["fin_str"]
    assert "h" in incidencia["duracion_str"] or "m" in incidencia["duracion_str"]
    assert "duracion_periodo_str" in incidencia
    metricas.close()


def test_report_adaptive_telemetry_modes(tmp_path):
    # Probar generación de reportes con los modos adaptativos: Semanal Turno y Por Equipo Turno
    db_file = str(tmp_path / "test_modes.db")
    metricas = MetricasHistoricas(db_path=db_file)
    equipos = [
        {"ip": "10.88.6.56", "label": "Kiosko Quilicura"},
        {"ip": "10.88.6.58", "label": "Totem Entrada"},
    ]

    # Generar en modo Semanal Turno
    pdf_turno = str(tmp_path / "report_turno.pdf")
    ctx_turno = ReportContext(
        filename=pdf_turno,
        app_name="Anvic Network Sentinel",
        version="2.2.7",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Ingeniero NOC",
        equipos=equipos,
        monitors={},
        metricas=metricas,
        tls_strict=True,
        cameras_count=0,
        camera_max_streams=1,
        modo_telemetria="Semanal (7D x Turno)",
        filtro_host="Todos los Equipos",
        turno_inicio="07:00",
        turno_fin="18:00",
        periodo_evaluado="Turno 07:00 a 18:00",
    )
    res_turno = build_network_report(ctx_turno)
    assert os.path.exists(res_turno)
    assert os.path.getsize(res_turno) > 1000

    # Generar en modo Por Equipo Turno
    pdf_eq_turno = str(tmp_path / "report_eq_turno.pdf")
    ctx_eq = ReportContext(
        filename=pdf_eq_turno,
        app_name="Anvic Network Sentinel",
        version="2.2.7",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Ingeniero NOC",
        equipos=equipos,
        monitors={},
        metricas=metricas,
        tls_strict=True,
        cameras_count=0,
        camera_max_streams=1,
        modo_telemetria="Por Equipo (Turno)",
        filtro_host="Todos los Equipos",
        turno_inicio="07:00",
        turno_fin="18:00",
        periodo_evaluado="Turno 07:00 a 18:00",
    )
    res_eq = build_network_report(ctx_eq)
    assert os.path.exists(res_eq)
    assert os.path.getsize(res_eq) > 1000

    metricas.close()


def test_report_layout_page_count_and_keep_together(tmp_path):
    import re
    db_file = str(tmp_path / "test_pages.db")
    metricas = MetricasHistoricas(db_path=db_file)
    equipos = [
        {"ip": f"10.88.6.{50+i}", "label": f"Equipo {i}", "ubicacion": "Quilicura" if i < 5 else "Renca"}
        for i in range(10)
    ]
    for eq in equipos:
        metricas.agregar_medicion(eq["ip"], 14.2, "Conectado")

    pdf_file = str(tmp_path / "report_3pages_check.pdf")
    ctx = ReportContext(
        filename=pdf_file,
        app_name="Anvic Network Sentinel",
        version="2.2.8",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Omar Toledo • Super Admin",
        equipos=equipos,
        monitors={},
        metricas=metricas,
        tls_strict=True,
        cameras_count=0,
        camera_max_streams=1,
        modo_telemetria="Por Equipo (Turno)",
        filtro_host="Todos los Equipos",
        turno_inicio="07:00",
        turno_fin="18:00",
        periodo_evaluado="Turno 07:00 a 18:00",
    )
    res = build_network_report(ctx)
    assert os.path.exists(res)

    with open(res, "rb") as f:
        pdf_bytes = f.read()

    pages = re.findall(rb"/Type\s*/Page\b", pdf_bytes)
    # Debe ser exactamente 3 páginas ejecutivas sin hojas huérfanas
    assert len(pages) == 3, f"Se esperaban exactamente 3 páginas pero se generaron {len(pages)}"

    metricas.close()


def test_report_layout_many_devices_separate_pages(tmp_path):
    """Verifica que con más de 10 equipos (>10), el heatmap pase elegantemente a su propia hoja generando 4 páginas."""
    import re
    db_file = str(tmp_path / "test_pages_15.db")
    metricas = MetricasHistoricas(db_path=db_file)
    equipos = [
        {"ip": f"10.88.6.{40+i}", "label": f"Equipo Rack {i}", "ubicacion": "Planta Norte" if i < 8 else "Planta Sur"}
        for i in range(15)
    ]
    for eq in equipos:
        metricas.agregar_medicion(eq["ip"], 12.5, "Conectado")

    pdf_file = str(tmp_path / "report_4pages_check.pdf")
    ctx = ReportContext(
        filename=pdf_file,
        app_name="Anvic Network Sentinel",
        version="2.2.9",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Omar Toledo • Super Admin",
        equipos=equipos,
        monitors={},
        metricas=metricas,
        tls_strict=True,
        cameras_count=0,
        camera_max_streams=1,
        modo_telemetria="Por Equipo (Turno)",
        filtro_host="Todos los Equipos",
        turno_inicio="07:00",
        turno_fin="18:00",
        periodo_evaluado="Turno 07:00 a 18:00",
    )
    res = build_network_report(ctx)
    assert os.path.exists(res)

    with open(res, "rb") as f:
        pdf_bytes = f.read()

    pages = re.findall(rb"/Type\s*/Page\b", pdf_bytes)
    # Debe ser exactamente 4 páginas (P1: Resumen/Tabla, P2: Latencia, P3: Heatmap 15 equipos, P4: Dictamen/Firmas)
    assert len(pages) == 4, f"Se esperaban exactamente 4 páginas pero se generaron {len(pages)}"

    metricas.close()


