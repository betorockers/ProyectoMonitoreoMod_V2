# tests/test_telemetry_turnos.py
import datetime
import tempfile
import pytest
from metrics_manager import (
    MetricasHistoricas,
    _parse_hora_str,
    dentro_de_turno,
    obtener_horas_turno,
)


def test_parse_hora_str():
    assert _parse_hora_str("07:00") == (7, 0)
    assert _parse_hora_str("18:30") == (18, 30)
    assert _parse_hora_str("23:59") == (23, 59)
    assert _parse_hora_str("00:00") == (0, 0)
    assert _parse_hora_str("7") == (7, 0)
    assert _parse_hora_str("invalid") == (7, 0)


def test_dentro_de_turno_diurno():
    # Turno de 07:00 a 18:00
    t_dentro_1 = datetime.time(7, 0)
    t_dentro_2 = datetime.time(12, 30)
    t_dentro_3 = datetime.time(18, 0)
    t_fuera_1 = datetime.time(6, 59)
    t_fuera_2 = datetime.time(18, 1)
    t_fuera_3 = datetime.time(23, 0)

    assert dentro_de_turno(t_dentro_1, "07:00", "18:00") is True
    assert dentro_de_turno(t_dentro_2, "07:00", "18:00") is True
    assert dentro_de_turno(t_dentro_3, "07:00", "18:00") is True
    assert dentro_de_turno(t_fuera_1, "07:00", "18:00") is False
    assert dentro_de_turno(t_fuera_2, "07:00", "18:00") is False
    assert dentro_de_turno(t_fuera_3, "07:00", "18:00") is False


def test_dentro_de_turno_nocturno():
    # Turno nocturno que cruza medianoche: 22:00 a 06:00
    t_dentro_1 = datetime.time(22, 0)
    t_dentro_2 = datetime.time(23, 59)
    t_dentro_3 = datetime.time(2, 30)
    t_dentro_4 = datetime.time(6, 0)
    t_fuera_1 = datetime.time(6, 1)
    t_fuera_2 = datetime.time(12, 0)
    t_fuera_3 = datetime.time(21, 59)

    assert dentro_de_turno(t_dentro_1, "22:00", "06:00") is True
    assert dentro_de_turno(t_dentro_2, "22:00", "06:00") is True
    assert dentro_de_turno(t_dentro_3, "22:00", "06:00") is True
    assert dentro_de_turno(t_dentro_4, "22:00", "06:00") is True
    assert dentro_de_turno(t_fuera_1, "22:00", "06:00") is False
    assert dentro_de_turno(t_fuera_2, "22:00", "06:00") is False
    assert dentro_de_turno(t_fuera_3, "22:00", "06:00") is False


def test_obtener_horas_turno():
    horas_diurnas = obtener_horas_turno("07:00", "12:00")
    assert horas_diurnas == [7, 8, 9, 10, 11, 12]

    horas_nocturnas = obtener_horas_turno("22:00", "02:00")
    assert horas_nocturnas == [22, 23, 0, 1, 2]


def test_obtener_telemetria_completa_batch(monkeypatch):
    """Prueba que el motor unificado de telemetría procesa los 4 modos sin errores y adapta las métricas al turno."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("metrics_manager.get_base_path", lambda: tmpdir)
        mm = MetricasHistoricas()

        # Insertar registros para dos equipos
        now = datetime.datetime.now()
        # Generar estampas: algunas a las 09:00 (en turno diurno 07-18) y otras a las 23:00 (fuera de turno)
        ts_turno_1 = now.replace(hour=9, minute=15, second=0, microsecond=0)
        ts_turno_2 = now.replace(hour=10, minute=30, second=0, microsecond=0)
        ts_fuera = now.replace(hour=23, minute=0, second=0, microsecond=0)

        cursor = mm.conn.cursor()
        for ip, lats in [("192.168.1.10", [12.5, 14.2, 90.0]), ("192.168.1.20", [20.0, 0.0, 22.0])]:
            cursor.execute("INSERT INTO mediciones (ip, timestamp, latencia, estado) VALUES (?, ?, ?, ?)", (ip, ts_turno_1, lats[0], 1))
            cursor.execute("INSERT INTO mediciones (ip, timestamp, latencia, estado) VALUES (?, ?, ?, ?)", (ip, ts_turno_2, lats[1], 1 if lats[1] > 0 else 0))
            cursor.execute("INSERT INTO mediciones (ip, timestamp, latencia, estado) VALUES (?, ?, ?, ?)", (ip, ts_fuera, lats[2], 1))
        mm.conn.commit()

        equipos = [
            {"ip": "192.168.1.10", "label": "Switch Core"},
            {"ip": "192.168.1.20", "label": "Router Border"},
        ]
        monitors_status = {"192.168.1.10": "Conectado", "192.168.1.20": "Desconectado"}

        # 1. Probar modo 24h
        res_24h = mm.obtener_telemetria_completa(
            equipos,
            filtro_host="Todos los Equipos",
            modo="Semanal (7D x 24h)",
            turno_inicio="07:00",
            turno_fin="18:00",
            monitors_status=monitors_status,
        )
        assert res_24h["es_turno"] is False
        assert "uptime" in res_24h["kpis"]
        assert len(res_24h["gauges_data"]) == 2
        assert len(res_24h["tabla_data"]) == 2
        assert res_24h["heatmap_data"]["ncols"] == 24

        # 2. Probar modo Turno Semanal
        res_turno_sem = mm.obtener_telemetria_completa(
            equipos,
            filtro_host="Todos los Equipos",
            modo="Semanal (7D x Turno)",
            turno_inicio="07:00",
            turno_fin="18:00",
            monitors_status=monitors_status,
        )
        assert res_turno_sem["es_turno"] is True
        assert res_turno_sem["heatmap_data"]["ncols"] == len(obtener_horas_turno("07:00", "18:00"))

        # 3. Probar modo Por Equipo (Turno) y correspondencia 1:1 de equipos
        res_turno_eq = mm.obtener_telemetria_completa(
            equipos,
            filtro_host="Todos los Equipos",
            modo="Por Equipo (Turno)",
            turno_inicio="07:00",
            turno_fin="18:00",
            monitors_status=monitors_status,
        )
        assert res_turno_eq["es_turno"] is True
        assert res_turno_eq["heatmap_data"]["nrows"] == 2
        assert res_turno_eq["heatmap_data"]["ncols"] == len(obtener_horas_turno("07:00", "18:00"))
        # Verificación estricta de orden 1:1: el equipo en índice 0 debe ser Switch Core y en 1 Router Border (sin efecto espejo)
        assert res_turno_eq["heatmap_data"]["row_labels"][0] == "Switch Core"
        assert res_turno_eq["heatmap_data"]["row_labels"][1] == "Router Border"
        assert res_turno_eq["heatmap_data"]["equipos_lista"][0]["ip"] == "192.168.1.10"
        assert res_turno_eq["heatmap_data"]["equipos_lista"][1]["ip"] == "192.168.1.20"
        assert "Turno 07:00 a 18:00" in res_turno_eq["latencia_title"]
        assert res_turno_eq["kpi_uptime_title"] == "SLA Turno (07:00-18:00)"
        assert res_turno_eq["latencia_min_x"] <= res_turno_eq["latencia_max_x"]

        # 4. Probar modo Por Equipo (24h)
        res_eq_24h = mm.obtener_telemetria_completa(
            equipos,
            filtro_host="Todos los Equipos",
            modo="Por Equipo (24h)",
            turno_inicio="07:00",
            turno_fin="18:00",
            monitors_status=monitors_status,
        )
        assert res_eq_24h["es_turno"] is False
        assert res_eq_24h["heatmap_data"]["ncols"] == 24
        assert res_eq_24h["heatmap_data"]["nrows"] == 2
        assert res_eq_24h["heatmap_data"]["row_labels"][0] == "Switch Core"
        assert res_eq_24h["heatmap_data"]["row_labels"][1] == "Router Border"
        assert "Últimas 24 Horas" in res_eq_24h["latencia_title"]
        assert res_eq_24h["kpi_uptime_title"] == "SLA Global (24h)"

        mm.close()
