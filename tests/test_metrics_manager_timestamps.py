import datetime
import tempfile
import pytest
from metrics_manager import MetricasHistoricas, _parse_timestamp


def test_parse_timestamp_formats():
    # ISO con T y microsegundos (el formato reportado en el crash del usuario)
    ts_t = "2026-09-25T16:19:24.860481"
    dt = _parse_timestamp(ts_t)
    assert isinstance(dt, datetime.datetime)
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 25
    assert dt.hour == 16
    assert dt.minute == 19
    assert dt.second == 24
    assert dt.microsecond == 860481

    # Formato clásico con espacio y microsegundos
    ts_space = "2026-09-25 16:19:24.860481"
    dt2 = _parse_timestamp(ts_space)
    assert dt2 == dt

    # Formato sin microsegundos
    ts_no_micro = "2026-09-25 16:19:24"
    dt3 = _parse_timestamp(ts_no_micro)
    assert isinstance(dt3, datetime.datetime)
    assert dt3.second == 24

    # Instancia nativa
    now = datetime.datetime.now()
    assert _parse_timestamp(now) is now


def test_metrics_manager_handles_iso_timestamps_in_db(monkeypatch):
    """Simula registros en la base de datos con formato ISO 'T' y valida que obtener_datos y análisis no crasheen."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("metrics_manager.get_base_path", lambda: tmpdir)
        mm = MetricasHistoricas()
        try:
            # Insertar mediciones artificiales con formato ISO con 'T'
            cursor = mm.conn.cursor()
            iso_ts = "2026-09-25T16:19:24.860481"
            cursor.execute("""
                INSERT INTO mediciones (ip, timestamp, latencia, estado)
                VALUES (?, ?, ?, ?)
            """, ("192.168.1.1", iso_ts, 15.4, 1))
            
            # Una medición de corte
            iso_ts_down = "2026-09-25T16:19:30.123456"
            cursor.execute("""
                INSERT INTO mediciones (ip, timestamp, latencia, estado)
                VALUES (?, ?, ?, ?)
            """, ("192.168.1.1", iso_ts_down, 0.0, 0))
            
            # Medición de recuperación
            iso_ts_up = "2026-09-25T16:19:35.654321"
            cursor.execute("""
                INSERT INTO mediciones (ip, timestamp, latencia, estado)
                VALUES (?, ?, ?, ?)
            """, ("192.168.1.1", iso_ts_up, 18.2, 1))
            mm.conn.commit()

            # Validar obtener_datos
            datos = mm.obtener_datos("192.168.1.1", periodo_horas=24 * 365)
            assert len(datos["timestamps"]) == 3
            for t in datos["timestamps"]:
                assert isinstance(t, datetime.datetime)

            # Validar analizar_desconexiones_y_downtime (lo que usa el reporte PDF)
            analisis = mm.analizar_desconexiones_y_downtime("192.168.1.1", periodo_horas=24 * 365)
            assert analisis["total_desconexiones"] == 1
            assert analisis["microcortes_count"] == 1

            # Validar matriz semanal
            matriz = mm.obtener_matriz_semanal("192.168.1.1", dias=365)
            assert len(matriz["disponibilidad"]) == 7
        finally:
            mm.conn.close()
