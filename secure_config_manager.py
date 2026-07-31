# secure_config_manager.py

import json
from cryptography.fernet import Fernet
import os

class SecureConfigManager:
    def __init__(self, key):
        self.fernet = Fernet(key)

    def _get_encrypted_path(self, filepath):
        """Añade .enc a la ruta del archivo para la versión cifrada."""
        return f"{filepath}.enc"

    def save(self, data, filepath):
        """Cifra los datos y los guarda en un archivo .enc."""
        try:
            json_data = json.dumps(data, indent=4).encode('utf-8')
            encrypted_data = self.fernet.encrypt(json_data)
            
            encrypted_filepath = self._get_encrypted_path(filepath)
            with open(encrypted_filepath, "wb") as file:
                file.write(encrypted_data)
        except Exception as e:
            print(f"Error al guardar configuración segura en {filepath}: {e}")

    def load(self, filepath):
        """Carga un archivo .enc, lo descifra y retorna los datos."""
        encrypted_filepath = self._get_encrypted_path(filepath)
        if not os.path.exists(encrypted_filepath):
            return None # El archivo no existe, retorna None

        with open(encrypted_filepath, "rb") as file:
            encrypted_data = file.read()

        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))