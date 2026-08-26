# core/process_manager.py
import atexit
import psutil
import logging
import os

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Gestor centralizado de procesos para evitar zombies (WebDrivers, pings, etc.).
    Registra procesos al iniciar y asegura su terminación limpia en atexit.
    """
    _webdrivers = []
    _pids = []

    @classmethod
    def register_webdriver(cls, driver):
        if driver not in cls._webdrivers:
            cls._webdrivers.append(driver)

    @classmethod
    def register_pid(cls, pid):
        if pid not in cls._pids and pid != os.getpid():
            cls._pids.append(pid)

    @classmethod
    def cleanup(cls):
        """Finaliza ordenadamente todos los procesos registrados."""
        print("[ProcessManager] Iniciando limpieza de recursos...")
        
        # 1. Cerrar WebDrivers de forma elegante
        for driver in cls._webdrivers:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error cerrando WebDriver: {e}")
        cls._webdrivers.clear()

        # 2. Matar procesos huérfanos registrados
        for pid in cls._pids:
            try:
                proc = psutil.Process(pid)
                # Terminar hijos
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logger.error(f"Error matando proceso {pid}: {e}")
        cls._pids.clear()
        print("[ProcessManager] Limpieza completada.")

# Registrar la limpieza al salir
atexit.register(ProcessManager.cleanup)
