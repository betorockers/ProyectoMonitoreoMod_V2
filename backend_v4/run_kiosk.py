"""
Argos Guard Enterprise v4.0 - PyQt6 QWebEngine Kiosk Runner.

Servidor monolítico Django embebido dentro de un contenedor Kiosko Full-Screen
con supresión de consola y manejo estricto de excepciones nativas (MessageBoxW).
"""
import sys
import os
import time
import socket
import secrets
import threading
import traceback
import ctypes
from pathlib import Path

# Activar supresión de consola en subprocesos Windows
if os.name == 'nt':
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

from apps.core.path_resolver import PathResolver

resolver = PathResolver()

def log_msg(msg: str):
    """Escribe logs de diagnóstico en AppData."""
    try:
        log_file = resolver.get_app_data_path("kiosk_engine.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def get_free_port() -> int:
    """Busca un puerto libre dinámico en 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        return s.getsockname()[1]

def run_django_server(port: int):
    """Ejecuta el servidor WSGI de Django en el hilo secundario con soporte de archivos estáticos."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from django.core.wsgi import get_wsgi_application
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from wsgiref.simple_server import make_server

    try:
        app = StaticFilesHandler(get_wsgi_application())
        
        # Purgar sesiones antiguas de Django para garantizar inicio en limpio
        try:
            from django.contrib.sessions.models import Session
            Session.objects.all().delete()
            log_msg("Sesiones de Django purgadas con éxito al arrancar el servidor.")
        except Exception as e:
            log_msg(f"Advertencia al purgar sesiones: {e}")

        httpd = make_server('127.0.0.1', port, app)
        log_msg(f"Servidor Django iniciado exitosamente en http://127.0.0.1:{port}/")
        httpd.serve_forever()
    except Exception as e:
        log_msg(f"ERROR en Servidor Django: {traceback.format_exc()}")

def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Realiza una espera activa en bucle para confirmar que el puerto esté abierto."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except (OSError, socket.error):
            time.sleep(0.1)
    return False

def kill_zombie_processes():
    """Destruye procesos huérfanos de ejecuciones previas del Kiosko."""
    if os.name == 'nt':
        import subprocess
        current_pid = os.getpid()
        try:
            # Eliminar otros python.exe corriendo run_kiosk.py
            cmd = 'wmic process where "name=\'python.exe\' and commandline like \'%run_kiosk%\'" get processid'
            output = subprocess.check_output(cmd, shell=True, text=True)
            for line in output.splitlines():
                line = line.strip()
                if line.isdigit():
                    pid = int(line)
                    if pid != current_pid:
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Eliminar subprocesos zombis de WebEngine (es seguro en un kiosko dedicado)
            subprocess.run("taskkill /F /IM QtWebEngineProcess.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log_msg(f"Advertencia al limpiar zombies: {e}")

def main():
    """Entrypoint principal del ejecutable Kiosko Desktop."""
    log_msg("1. Iniciando contenedor Kiosko v4.0")
    kill_zombie_processes()

    port = get_free_port()
    server_thread = threading.Thread(target=run_django_server, args=(port,), daemon=True)
    server_thread.start()

    log_msg(f"2. Esperando confirmación de socket en puerto {port}...")
    if not wait_for_server(port, timeout=12.0):
        log_msg("CRITICAL: El servidor Django no respondió a tiempo.")
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, "Error crítico de inicialización:\n\nEl servidor interno de Argos Guard no pudo iniciar en el tiempo límite.", "Error Fatal - Argos Guard v4.0", 0x10)
        sys.exit(1)

    url = f"http://127.0.0.1:{port}/"

    # PyQt6 GUI Setup
    from PyQt6.QtCore import QUrl
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    from PyQt6.QtGui import QIcon, QColor

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Argos Guard Enterprise v4.0")

    icon_path = resolver.get_path("static", "icono_argos.ico")
    if icon_path.exists():
        qt_app.setWindowIcon(QIcon(str(icon_path)))

    window = QMainWindow()
    window.setWindowTitle("Argos Guard Enterprise v4.0")
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    # Use off-the-record profile so sessions are NEVER persistent across restarts
    profile = QWebEngineProfile("", window)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
    
    browser = QWebEngineView()
    page = QWebEnginePage(profile, browser)
    # Prevenir el "flash blanco" inicial asignando el fondo oscuro del sistema
    page.setBackgroundColor(QColor("#050d12"))
    browser.setPage(page)
    
    # Intercept logout to close the application completely
    def handle_url_change(qurl):
        url_str = qurl.toString()
        if "/security/logout" in url_str:
            window.close()
            QApplication.instance().quit()
            
    browser.urlChanged.connect(handle_url_change)

    # ─── Interceptor de Descargas ─────────────────────────────────────────────
    # Redirige automáticamente toda descarga (JSON, PDF, SQLite) a la carpeta
    # "Descargas" del usuario host de Windows, sin intervención del usuario.
    from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest

    downloads_dir = str(Path.home() / "Downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    def on_download_requested(download: QWebEngineDownloadRequest):
        download.setDownloadDirectory(downloads_dir)
        # Conservar el filename sugerido por el servidor (Content-Disposition)
        download.accept()
        log_msg(f"Descarga iniciada: {download.suggestedFileName()} → {downloads_dir}")

    profile.downloadRequested.connect(on_download_requested)
    # ─────────────────────────────────────────────────────────────────────────

    browser.setUrl(QUrl(url))

    window.setCentralWidget(browser)
    window.showFullScreen()


    log_msg("3. Lanzando Bucle Kiosko GUI Full-Screen")
    qt_app.exec()
    
    # Destrucción forzada inmediata para evitar procesos zombies
    log_msg("4. Kiosko cerrado. Destruyendo subprocesos.")
    os._exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err_msg = traceback.format_exc()
        log_msg(f"FATAL EXCEPTION: {err_msg}")
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, f"Error no controlado en Argos Guard Enterprise v4.0:\n\n{err_msg}", "Error Fatal - Argos Guard v4.0", 0x10)
        os._exit(1)
