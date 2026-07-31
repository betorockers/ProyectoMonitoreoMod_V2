# key_manager.py

import os
import platform
from cryptography.fernet import Fernet

# Dependencia adicional requerida: pywin32
# Instalar con: pip install pywin32
try:
    import win32crypt
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

KEY_FILENAME = "anvic_master.key"

def _get_key_path(base_path):
    return os.path.join(base_path, KEY_FILENAME)

def save_key(base_path):
    """Genera una nueva clave, la protege con DPAPI y la guarda."""
    if platform.system() != "Windows":
        raise OSError("La protección de claves con DPAPI solo está disponible en Windows.")
    if not PYWIN32_AVAILABLE:
        raise ModuleNotFoundError(
            "No se encontró 'win32crypt'. Instala 'pywin32' en este entorno para usar DPAPI."
        )

    key = Fernet.generate_key()
    # Cifra la clave usando el contexto del usuario actual y la máquina
    encrypted_key = win32crypt.CryptProtectData(key, None, None, None, None, 0)

    with open(_get_key_path(base_path), "wb") as key_file:
        key_file.write(encrypted_key)
    print("Clave maestra generada y protegida.")
    return key

def load_key(base_path):
    """Carga la clave, la desprotege con DPAPI y la retorna."""
    key_path = _get_key_path(base_path)
    if not os.path.exists(key_path):
        return save_key(base_path)

    if platform.system() != "Windows":
        raise OSError("La protección de claves con DPAPI solo está disponible en Windows.")
    if not PYWIN32_AVAILABLE:
        raise ModuleNotFoundError(
            "No se encontró 'win32crypt'. Instala 'pywin32' en este entorno para usar DPAPI."
        )

    with open(key_path, "rb") as key_file:
        encrypted_key = key_file.read()

    # Descifra la clave usando el contexto del usuario actual
    _, decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)
    return decrypted_key
