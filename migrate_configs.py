# migrate_configs.py

import os
import json
import sys

def migrate_file(config_manager, base_path, filename):
    plain_path = os.path.join(base_path, filename)
    encrypted_path = f"{plain_path}.enc"

    if os.path.exists(encrypted_path):
        print(f"✅ '{filename}.enc' ya existe. No se necesita migración.")
        return

    if not os.path.exists(plain_path):
        print(f"ℹ️ No se encontró '{filename}'. No hay nada que migrar.")
        return

    print(f"⏳ Migrando '{filename}' a formato cifrado...")
    try:
        with open(plain_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config_manager.save(data, plain_path)
        
        # Renombrar el archivo viejo para evitar cargarlo por error
        os.rename(plain_path, f"{plain_path}.bak")
        print(f"✔️ ¡Éxito! '{filename}' fue cifrado. El original fue renombrado a '{filename}.bak'.")

    except Exception as e:
        print(f"❌ Error durante la migración de '{filename}': {e}")

if __name__ == "__main__":
    print("Iniciando script de migración de configuración de Argos Guard...")
    
    try:
        # Revertimos a importación directa, ya que los módulos de seguridad
        # parecen estar en la raíz del proyecto junto a este script.
        from key_manager import load_key
        from secure_config_manager import SecureConfigManager
        from utils.paths import get_base_path # Usamos la utilidad centralizada
    except ImportError as e:
        print(f"❌ Error de importación: {e}. Asegúrate de que los archivos 'key_manager.py', 'secure_config_manager.py' y la carpeta 'utils/' existan en la raíz del proyecto.")
        exit()

    BASE_PATH = get_base_path()
    
    master_key = load_key(BASE_PATH)
    secure_config = SecureConfigManager(master_key)

    migrate_file(secure_config, BASE_PATH, "users.json")
    migrate_file(secure_config, BASE_PATH, "equipos_guardados.json")
    
    print("\nMigración completada. Ahora puedes ejecutar la aplicación principal.")