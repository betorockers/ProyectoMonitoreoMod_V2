"""
Argos Guard Enterprise v4.0 - PathResolver Singleton.

Provee resolución dinámica de rutas de archivos para assets estáticos,
plantillas y base de datos local cifrada, soportando ejecución directa
y empaquetado Nuitka C++ / PyInstaller.
"""
import os
import sys
from pathlib import Path

class PathResolver:
    """Singleton para la resolución dinámica de rutas relativas y absolutas."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathResolver, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializa las rutas base detectando si la app está compilada."""
        if getattr(sys, 'frozen', False) or '__compiled__' in globals():
            # Ejecución compilada (Nuitka / PyInstaller)
            self.base_dir = Path(sys.executable).parent.resolve()
        else:
            # Ejecución interpretada Python
            self.base_dir = Path(__file__).parent.parent.parent.resolve()

        # Directorio seguro en AppData para la base de datos local y logs
        app_data_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
        self.app_data_dir = Path(app_data_base) / "ArgosGuardEnterpriseV4"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.app_data_dir / "argos_guard_v4.db"
        self.log_dir = self.app_data_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, *relative_parts: str) -> Path:
        """Retorna una ruta absoluta uniendo partes relativas al directorio base."""
        return self.base_dir.joinpath(*relative_parts).resolve()

    def get_app_data_path(self, *relative_parts: str) -> Path:
        """Retorna una ruta absoluta dentro del directorio seguro AppData."""
        return self.app_data_dir.joinpath(*relative_parts).resolve()
