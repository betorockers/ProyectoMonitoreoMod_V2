# tests/test_auth_and_security.py
"""
Suite de pruebas unitarias para AuthManager, SecureConfigManager y ReportBuilder.
Valida la seguridad por diseño, jerarquía de roles y formato de presentación de usuarios.
"""

import os
import tempfile
import pytest
from key_manager import load_key
from secure_config_manager import SecureConfigManager
from auth_manager import AuthManager
from services.report_builder import ReportContext, build_network_report


@pytest.fixture
def temp_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        master_key = load_key(tmpdir)
        sc = SecureConfigManager(master_key)
        auth = AuthManager(sc, tmpdir)
        yield tmpdir, master_key, sc, auth


def test_password_complexity(temp_env):
    tmpdir, _, _, auth = temp_env

    # Demasiado corta (< 8)
    ok, msg = auth._validate_password("Short1!")
    assert not ok
    assert "8 caracteres" in msg

    # Sin mayúscula
    ok, msg = auth._validate_password("lowercase1!")
    assert not ok
    assert "mayúscula" in msg

    # Sin minúscula
    ok, msg = auth._validate_password("UPPERCASE1!")
    assert not ok
    assert "minúscula" in msg

    # Sin número
    ok, msg = auth._validate_password("NoNumbers!")
    assert not ok
    assert "número" in msg

    # Sin carácter especial
    ok, msg = auth._validate_password("NoSpecial123")
    assert not ok
    assert "carácter especial" in msg

    # Contraseña robusta válida
    ok, msg = auth._validate_password("Complex@Pass123")
    assert ok
    assert msg == ""


def test_role_hierarchy_and_permissions(temp_env):
    tmpdir, _, _, auth = temp_env

    # Crear super_admin inicial
    ok, msg = auth.create_initial_superuser("admin_boss", "Complex@Pass123", "Omar Toledo")
    assert ok

    # Intentar crear otro super_admin (debe fallar)
    ok, msg = auth.create_initial_superuser("another_boss", "Complex@Pass123", "Otro")
    assert not ok

    # super_admin crea un operador (rol user)
    ok, msg = auth.add_user("operator1", "SimplePass", "user", "Juan Pérez", "super_admin")
    assert ok

    # super_admin crea un admin
    ok, msg = auth.add_user("sub_admin", "SimplePass", "admin", "Pedro Admin", "super_admin")
    assert ok

    # admin intenta crear otro admin (debe ser denegado según políticas)
    ok, msg = auth.add_user("admin2", "SimplePass", "admin", "Admin Invalido", "admin")
    assert not ok
    assert "Un admin no puede crear otro admin" in msg

    # Usuario con rol 'user' intenta eliminar o agregar (permiso denegado)
    ok, msg = auth.add_user("hacker", "SimplePass", "admin", "Hacker", "user")
    assert not ok

    ok, msg = auth.delete_user("sub_admin", "user")
    assert not ok
    assert "super_admin" in msg

    # super_admin elimina al operador
    ok, msg = auth.delete_user("operator1", "super_admin")
    assert ok


def test_update_user_superuser_self_and_roles(temp_env):
    """Valida que el super_admin pueda actualizar su nombre y contraseña sin ser bloqueado."""
    tmpdir, _, _, auth = temp_env

    # 1. Crear super_admin BetoDev
    ok, msg = auth.create_initial_superuser("BetoDev", "Complex@Pass123", "Beto Developer")
    assert ok

    # 2. Actualizar nombre completo a 'Omar Toledo' y nueva contraseña '@B3t0R0ck3rs'
    ok, msg = auth.update_user(
        current_user_role="super_admin",
        old_username="BetoDev",
        new_username="BetoDev",
        new_password="@B3t0R0ck3rs",
        new_fullname="Omar Toledo",
        new_role="super_admin",
    )
    assert ok, f"Fallo al actualizar super_admin: {msg}"
    assert "exitosamente" in msg

    # Verificar que los datos en memoria y disco se hayan actualizado
    user = auth.users["BetoDev"]
    assert user["full_name"] == "Omar Toledo"
    assert user["password_plain"] == "@B3t0R0ck3rs"

    # Verificar autenticación con nueva contraseña
    auth_res = auth.authenticate("BetoDev", "@B3t0R0ck3rs")
    assert auth_res is not None
    assert auth_res["full_name"] == "Omar Toledo"

    # 3. Validar llamada simplificada de 4 argumentos: update_user(username, new_pwd, new_fname, role)
    ok_legacy, msg_legacy = auth.update_user("BetoDev", "@B3t0R0ck3rs", "Omar Toledo Staff", "super_admin")
    assert ok_legacy
    assert auth.users["BetoDev"]["full_name"] == "Omar Toledo Staff"

    # 4. Validar que un operador no pueda actualizar usuarios
    ok_denied, msg_denied = auth.update_user(
        current_user_role="operator",
        old_username="BetoDev",
        new_fullname="Intruso",
    )
    assert not ok_denied
    assert "Permiso denegado" in msg_denied



def test_user_display_formatting_top_tier(temp_env):
    tmpdir, _, _, auth = temp_env

    # Validar que el formato no incluya '@' ni usernames redundantes
    user_data = {
        "username": "BetoDev",
        "full_name": "Omar Toledo",
        "role": "super_admin",
    }
    full_name = (user_data.get("full_name") or "").strip()
    role_label = user_data.get("role", "Operador").replace("_", " ").title()
    user_display = f"{full_name} • {role_label}"

    assert user_display == "Omar Toledo • Super Admin"
    assert "@" not in user_display
    assert "BetoDev" not in user_display


def test_report_builder_with_dynamic_user(temp_env):
    tmpdir, _, _, _ = temp_env
    pdf_path = os.path.join(tmpdir, "test_report.pdf")

    ctx = ReportContext(
        filename=pdf_path,
        app_name="Anvic Network Sentinel",
        version="2.2.3",
        tagline="Plataforma de Supervisión Industrial",
        logo_path="",
        generated_by="Omar Toledo • Super Admin",
        equipos=[
            {"ip": "10.88.22.54", "label": "LPR Renca Salida"},
            {"ip": "10.88.6.58", "label": "Totem Entrada"},
        ],
        monitors={},
        metricas=None,
        tls_strict=True,
        cameras_count=2,
        camera_max_streams=1,
        osint_data=None,
    )

    build_network_report(ctx)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000
