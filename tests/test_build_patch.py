#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el sistema industrial de parches (build_patch.py).
Valida cálculo de hashes, sugerencia de versiones, generación de manifiestos
y protección estricta de bases de datos y configuraciones sensibles.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from build_patch import (
    calcular_sha256,
    sugerir_siguiente_version,
    obtener_version_actual,
    preparar_staging_parche,
    PROTECTED_DATA_FILES,
)


def test_sugerir_siguiente_version():
    assert sugerir_siguiente_version("2.2.3") == "2.2.4"
    assert sugerir_siguiente_version("1.0.0") == "1.0.1"
    assert sugerir_siguiente_version("3.1") == "3.1.1"


def test_calcular_sha256():
    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("ANVIC_NETWORK_SENTINEL_PATCH_TEST_HASH")
        tf.flush()
        tf_path = Path(tf.name)

    try:
        digest = calcular_sha256(tf_path)
        assert len(digest) == 64
        assert isinstance(digest, str)
    finally:
        if tf_path.exists():
            tf_path.unlink()


def test_archivos_protegidos_definidos():
    """Garantiza que la lista de exclusión sagrada contiene los artefactos de datos del cliente."""
    assert "anvic_monitor.db" in PROTECTED_DATA_FILES
    assert "equipos_guardados.json.enc" in PROTECTED_DATA_FILES
    assert "users.json.enc" in PROTECTED_DATA_FILES
    assert "anvic_master.key" in PROTECTED_DATA_FILES


def test_obtener_version_actual():
    """Verifica lectura de la versión desde config/branding.py."""
    ver = obtener_version_actual()
    assert isinstance(ver, str)
    assert len(ver.split(".")) >= 2
