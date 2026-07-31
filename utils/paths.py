# utils/paths.py
"""
Utilidades de rutas compartidas para toda la aplicación.
Centraliza la lógica de compatibilidad con PyInstaller (frozen).

FIX: Elimina la duplicación del patrón get_base_path() que existía en
     4 módulos diferentes (auth_manager, database_manager, metrics_manager, backup_manager).
"""

import os
import sys


def get_base_path() -> str:
    """
    Retorna la ruta base donde se guardan los archivos de datos y configuración.
    Compatible con ejecución normal y con binario generado por PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__ + "/.."))


def get_resource_path(relative_path: str) -> str:
    """
    Retorna la ruta absoluta de un recurso (assets, etc.).
    Cuando la app está empaquetada con PyInstaller, los recursos
    se extraen a un directorio temporal (_MEIPASS).

    Args:
        relative_path: Ruta relativa al recurso desde la raíz del proyecto.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    # En desarrollo, la raíz del proyecto es un nivel arriba de utils/
    root = os.path.dirname(os.path.abspath(__file__ + "/.."))
    return os.path.join(root, relative_path)
