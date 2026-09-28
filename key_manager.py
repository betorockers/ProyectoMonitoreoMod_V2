# key_manager.py

import os
import platform
import ctypes
from ctypes import wintypes
from cryptography.fernet import Fernet

# Intento de carga de win32crypt (pywin32) con fallback a DPAPI nativo (ctypes / Crypt32.dll)
try:
    import win32crypt
    PYWIN32_AVAILABLE = True
except ImportError:
    win32crypt = None
    PYWIN32_AVAILABLE = False

KEY_FILENAME = "anvic_master.key"


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char))
    ]


def _ctypes_dpapi_protect(data: bytes) -> bytes:
    """Cifra datos usando DPAPI nativo de Windows (Crypt32.dll) sin dependencias externas."""
    CryptProtectData = ctypes.windll.crypt32.CryptProtectData
    CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),
        wintypes.LPCWSTR,
        ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(DATA_BLOB)
    ]
    CryptProtectData.restype = wintypes.BOOL

    LocalFree = ctypes.windll.kernel32.LocalFree
    LocalFree.argtypes = [ctypes.c_void_p]

    in_blob = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)))
    out_blob = DATA_BLOB()

    if not CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        LocalFree(out_blob.pbData)


def _ctypes_dpapi_unprotect(data: bytes) -> bytes:
    """Descifra datos usando DPAPI nativo de Windows (Crypt32.dll) sin dependencias externas."""
    CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
    CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(DATA_BLOB)
    ]
    CryptUnprotectData.restype = wintypes.BOOL

    LocalFree = ctypes.windll.kernel32.LocalFree
    LocalFree.argtypes = [ctypes.c_void_p]

    in_blob = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)))
    out_blob = DATA_BLOB()

    if not CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        LocalFree(out_blob.pbData)


def _dpapi_protect(data: bytes) -> bytes:
    """Cifra datos usando win32crypt si está presente, o DPAPI nativo vía ctypes."""
    if PYWIN32_AVAILABLE and win32crypt is not None:
        try:
            return win32crypt.CryptProtectData(data, None, None, None, None, 0)
        except Exception:
            pass
    return _ctypes_dpapi_protect(data)


def _dpapi_unprotect(data: bytes) -> bytes:
    """Descifra datos usando win32crypt si está presente, o DPAPI nativo vía ctypes."""
    if PYWIN32_AVAILABLE and win32crypt is not None:
        try:
            _, decrypted = win32crypt.CryptUnprotectData(data, None, None, None, 0)
            return decrypted
        except Exception:
            pass
    return _ctypes_dpapi_unprotect(data)


def _get_key_path(base_path: str) -> str:
    return os.path.join(base_path, KEY_FILENAME)


def save_key(base_path: str) -> bytes:
    """Genera una nueva clave, la protege con DPAPI y la guarda en disco."""
    if platform.system() != "Windows":
        raise OSError("La protección de claves con DPAPI solo está disponible en Windows.")

    key = Fernet.generate_key()
    encrypted_key = _dpapi_protect(key)

    with open(_get_key_path(base_path), "wb") as key_file:
        key_file.write(encrypted_key)
    print("Clave maestra generada y protegida con DPAPI.")
    return key


def load_key(base_path: str) -> bytes:
    """Carga la clave, la desprotege con DPAPI y la retorna."""
    key_path = _get_key_path(base_path)
    if not os.path.exists(key_path):
        return save_key(base_path)

    if platform.system() != "Windows":
        raise OSError("La protección de claves con DPAPI solo está disponible en Windows.")

    with open(key_path, "rb") as key_file:
        encrypted_key = key_file.read()

    return _dpapi_unprotect(encrypted_key)
