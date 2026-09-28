import sys
import os
import time
import pytest
import threading

# Añadir el directorio raíz al path para que los imports locales funcionen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitor import App
from auth_manager import AuthManager

@pytest.fixture(scope="module")
def app():
    """Fixture que inicializa la aplicación (sin mainloop) para pruebas E2E."""
    # Evitamos inicializar pygame mixer si falla en CI
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    
    test_app = App([])
    test_app.update() # Forzar renderizado inicial
    
    yield test_app
    
    # Teardown
    test_app.destroy()

def test_01_login_flow(app):
    """Prueba E2E de inicialización de la UI Principal."""
    # Bypasseamos el Login/Setup directamente para probar la UI Principal
    mock_user = {"username": "BetoDev", "role": "super_admin", "full_name": "Beto Rock"}
    app.on_login_success(mock_user)
    app.update() # Forzamos el renderizado de la UI principal
    
    # Verificamos que la UI principal se desplegó correctamente
    assert hasattr(app, "tabview"), "La vista de pestañas (Tabview) no se cargó tras el login simulado."
    assert app.current_user["username"] == "BetoDev"

def test_02_operacion_tab(app):
    """Prueba E2E de añadir equipo en la pestaña de monitoreo."""
    # Ir a la pestaña de Operación
    app.tabview.set("Operacion en Vivo")
    app.update()
    
    # Ingresar datos en los campos
    app.ip_entry.insert(0, "127.0.0.1")
    app.etiqueta_entry.insert(0, "E2E Test Host")
    
    # Simular pulsar el botón
    app.add_button.invoke()
    app.update()
    
    # Verificar que el monitor se creó en el diccionario de monitores
    assert "127.0.0.1" in app.monitors, "El host 127.0.0.1 no se añadió a los monitores activos."
    
def test_03_admin_tab(app):
    """Prueba E2E de la pestaña Administración (Crear usuario simulado)."""
    # Ir a la pestaña de Administración
    app.tabview.set("Administracion")
    app.update()
    
    app.new_username_entry.insert(0, "test_e2e_user")
    app.new_fullname_entry.insert(0, "Test E2E User")
    app.new_password_entry.insert(0, "SuperSecret123!")
    app.confirm_password_entry.insert(0, "SuperSecret123!")
    app.new_role_option.set("user")
    
    # Simular clic de añadir
    app.create_user_button.invoke()
    app.update()
    
    # Verificamos que se haya añadido en la instancia auth (users)
    users = app.auth.users
    assert "test_e2e_user" in users, "El usuario E2E no fue guardado en el archivo encriptado."

def test_04_cctv_tab(app):
    """Prueba E2E de la pestaña de Video Vigilancia (CCTV)."""
    app.tabview.set("Video Vigilancia")
    app.update()
    
    cctv_tab = app.video_vigilancia_controller
    # Añadir credenciales falsas RTSP
    cctv_tab.entry_nombre.insert(0, "Cámara E2E")
    cctv_tab.entry_url.insert(0, "rtsp://1.1.1.1/stream")
    cctv_tab.btn_guardar.invoke()
    app.update()
    
    # Verificar si la lista de cámaras se actualizó
    assert any(c.get("nombre") == "Cámara E2E" for c in cctv_tab.cameras), "La cámara no se añadió correctamente a la base de datos local CCTV."
