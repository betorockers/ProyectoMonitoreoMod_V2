import pytest
import os
import tempfile
from metrics_manager import MetricasHistoricas
from unittest.mock import MagicMock

def test_gauges_telemetry_includes_location():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_anvic.db")
        manager = MetricasHistoricas(db_path=db_path)
        
        equipos = [
            {"ip": "10.88.6.60", "label": "Totem de salida Quilicura"},
            {"ip": "10.88.22.65", "label": "Totem de Salida Renca"},
            {"ip": "192.168.1.50", "label": "Camara Patio", "ubicacion": "Sucursal Norte"},
        ]
        
        telemetria = manager.obtener_telemetria_completa(equipos, modo="Semanal (7D x 24h)")
        gauges = telemetria.get("gauges_data", [])
        manager.cerrar()
        
        assert len(gauges) == 3
        
        # Test inferencia automática para Quilicura
        g_quilicura = next((g for g in gauges if g["ip"] == "10.88.6.60"), None)
        assert g_quilicura is not None
        assert g_quilicura["ubicacion"] == "Quilicura"
        
        # Test inferencia automática para Renca
        g_renca = next((g for g in gauges if g["ip"] == "10.88.22.65"), None)
        assert g_renca is not None
        assert g_renca["ubicacion"] == "Renca"
        
        # Test ubicación explícita respetada
        g_sucursal = next((g for g in gauges if g["ip"] == "192.168.1.50"), None)
        assert g_sucursal is not None
        assert g_sucursal["ubicacion"] == "Sucursal Norte"


def test_reordenar_equipos_logic():
    equipos = [
        {"ip": "10.88.6.58", "label": "Totem de Entrada Quilicura", "ubicacion": "Quilicura"},
        {"ip": "10.88.6.60", "label": "Totem de salida Quilicura", "ubicacion": "Quilicura"},
        {"ip": "10.88.22.59", "label": "Totem de Entrada Renca", "ubicacion": "Renca"},
    ]
    
    # Simular swap/reubicación
    ip_origen = "10.88.22.59"
    ip_destino = "10.88.6.58"
    
    idx_origen = next((i for i, eq in enumerate(equipos) if eq.get("ip") == ip_origen), None)
    idx_destino = next((i for i, eq in enumerate(equipos) if eq.get("ip") == ip_destino), None)
    
    assert idx_origen == 2
    assert idx_destino == 0
    
    item = equipos.pop(idx_origen)
    equipos.insert(idx_destino, item)
    
    # Ahora el Totem de Entrada Renca debe ser el primero
    assert equipos[0]["ip"] == "10.88.22.59"
    assert equipos[1]["ip"] == "10.88.6.58"
    assert equipos[2]["ip"] == "10.88.6.60"


def test_guardar_equipos_preserves_location():
    equipos = [
        {"ip": "10.88.6.58", "label": "Totem Entrada", "ubicacion": "Planta 1"},
        {"ip": "10.88.6.60", "label": "Totem Salida", "ubicacion": "Planta 2"},
    ]
    
    lista_para_guardar = []
    for eq in equipos:
        eq_copy = eq.copy()
        eq_copy["ubicacion"] = eq.get("ubicacion", "")
        lista_para_guardar.append(eq_copy)
        
    assert lista_para_guardar[0]["ubicacion"] == "Planta 1"
    assert lista_para_guardar[1]["ubicacion"] == "Planta 2"
