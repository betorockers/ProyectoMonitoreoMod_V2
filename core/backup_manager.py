# core/backup_manager.py
"""
Sistema de respaldo automático de la base de datos SQLite de Argos Guard.
Implementa rotación de archivos para optimizar espacio en disco.
"""

import shutil
import os
import datetime
import threading
from utils.paths import get_base_path
from config.settings import DB_FILENAME, MAX_BACKUPS


class BackupManager:
    """Gestiona la creación y rotación de backups de la base de datos."""

    def __init__(
        self,
        db_filename: str = DB_FILENAME,
        backup_dir: str = "backups",
        max_backups: int = MAX_BACKUPS,
    ):
        base_path = get_base_path()
        self.db_path = os.path.join(base_path, db_filename)
        self.backup_dir = os.path.join(base_path, backup_dir)
        self.max_backups = max_backups

        os.makedirs(self.backup_dir, exist_ok=True)

    def crear_backup(self) -> tuple[bool, str]:
        """
        Crea una copia de seguridad de la base de datos con timestamp.

        Returns:
            (bool, str): éxito y mensaje descriptivo.
        """
        if not os.path.exists(self.db_path):
            return False, "Base de datos aún no creada"

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_monitor_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            shutil.copy2(self.db_path, backup_path)
            print(f"[Backup] ✅ Creado: {backup_filename}")

            # Limpiar backups antiguos en background
            threading.Thread(
                target=self._limpiar_backups_antiguos, daemon=True
            ).start()

            return True, f"Backup creado: {backup_filename}"
        except Exception as e:
            print(f"[Backup] ❌ Error: {e}")
            return False, str(e)

    def _limpiar_backups_antiguos(self) -> None:
        """Mantiene solo los últimos N backups (rotación automática)."""
        try:
            archivos = sorted(
                [
                    os.path.join(self.backup_dir, f)
                    for f in os.listdir(self.backup_dir)
                    if f.startswith("backup_monitor_") and f.endswith(".db")
                ],
                key=os.path.getmtime,
            )

            if len(archivos) > self.max_backups:
                for f in archivos[: -self.max_backups]:
                    os.remove(f)
                    print(f"[Backup] 🗑️ Antiguo eliminado: {os.path.basename(f)}")
        except Exception as e:
            print(f"[Backup] Error en limpieza: {e}")
