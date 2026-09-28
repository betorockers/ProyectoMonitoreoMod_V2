import os
import tempfile
import pytest
from cryptography.fernet import Fernet
import key_manager
from licensing.license_storage import LicenseStorage


def test_key_manager_save_and_load_native():
    with tempfile.TemporaryDirectory() as tmpdir:
        key = key_manager.save_key(tmpdir)
        assert isinstance(key, bytes)
        assert len(key) == 44  # Fernet key standard base64 len

        # Verify key file was created on disk
        key_file = os.path.join(tmpdir, key_manager.KEY_FILENAME)
        assert os.path.exists(key_file)

        # Reload key
        loaded = key_manager.load_key(tmpdir)
        assert loaded == key

        # Verify encryption functionality
        cipher = Fernet(loaded)
        msg = b"Sensitive test payload for Anvic Network Sentinel"
        token = cipher.encrypt(msg)
        assert cipher.decrypt(token) == msg


def test_key_manager_ctypes_fallback_without_pywin32(monkeypatch):
    """Verifica que si pywin32 / win32crypt no existe, DPAPI nativo vía ctypes funciona 100%."""
    monkeypatch.setattr(key_manager, "PYWIN32_AVAILABLE", False)
    monkeypatch.setattr(key_manager, "win32crypt", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        key = key_manager.save_key(tmpdir)
        assert isinstance(key, bytes)
        assert len(key) == 44

        loaded = key_manager.load_key(tmpdir)
        assert loaded == key

        cipher = Fernet(loaded)
        msg = b"Payload without win32crypt"
        assert cipher.decrypt(cipher.encrypt(msg)) == msg


def test_license_storage_dpapi_without_pywin32(monkeypatch):
    """Verifica que license storage proteja y desproteja datos sin win32crypt."""
    storage = LicenseStorage(registry_root="Software\\AnvicTestDPAPI")
    raw = b'{"license_id": "TEST-123", "active": true}'

    # Test with win32crypt disabled
    monkeypatch.setattr("licensing.license_storage.win32crypt", None)
    protected = storage._protect(raw)
    assert protected is not None
    unprotected = storage._unprotect(protected)
    assert unprotected == raw
