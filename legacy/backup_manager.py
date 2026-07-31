import shutil
import os
import datetime
import sys
import threading

class BackupManager:
    def __init__(self, db_filename="argos_guard.db", backup_dir="backups", max_backups=30):
        # Determinar ruta base
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.db_path = os.path.join(self.base_path, db_filename)
        self.backup_dir = os.path.join(self.base_path, backup_dir)
        self.max_backups = max_backups
        
        # Crear carpeta de backups si no existe
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def crear_backup(self):
        """Crea una copia de seguridad de la base de datos con timestamp."""
        if not os.path.exists(self.db_path):
            # Si no existe la DB, no es necesariamente un error crítico al inicio
            return False, "Base de datos aún no creada"

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_monitor_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copiar archivo (shutil.copy2 preserva metadatos)
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Backup creado exitosamente: {backup_filename}")
            
            # Limpiar backups antiguos en un hilo separado
            threading.Thread(target=self._limpiar_backups_antiguos, daemon=True).start()
            
            return True, f"Backup creado: {backup_filename}"
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False, str(e)

    def _limpiar_backups_antiguos(self):
        """Mantiene solo los últimos N backups."""
        try:
            archivos = [
                os.path.join(self.backup_dir, f) 
                for f in os.listdir(self.backup_dir) 
                if f.startswith("backup_monitor_") and f.endswith(".db")
            ]
            
            # Ordenar por fecha de modificación (más reciente al final)
            archivos.sort(key=os.path.getmtime)
            
            # Si hay más archivos que el límite, borrar los más viejos
            if len(archivos) > self.max_backups:
                archivos_a_borrar = archivos[:-self.max_backups]
                for f in archivos_a_borrar:
                    os.remove(f)
                    print(f"🗑️ Backup antiguo eliminado: {os.path.basename(f)}")
        except Exception as e:
            print(f"Error limpiando backups antiguos: {e}")