from __future__ import annotations

import base64
import json
import os
import winreg

try:
    import win32crypt
except ImportError:  # pragma: no cover
    win32crypt = None

try:
    from key_manager import _dpapi_protect, _dpapi_unprotect
except ImportError:  # pragma: no cover
    _dpapi_protect = None
    _dpapi_unprotect = None

from config.licensing import LICENSE_REGISTRY_ROOT


class LicenseStorage:
    def __init__(self, registry_root: str = LICENSE_REGISTRY_ROOT):
        self.registry_root = registry_root

    def _ensure_key(self):
        return winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_root)

    def _set_string(self, name: str, value: str) -> None:
        with self._ensure_key() as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def _get_string(self, name: str) -> str | None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_root) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except OSError:
            return None

    def _delete_value(self, name: str) -> None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_root, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except OSError:
            return

    def _protect(self, raw: bytes) -> str:
        if _dpapi_protect is not None:
            try:
                return base64.b64encode(_dpapi_protect(raw)).decode("ascii")
            except Exception:
                pass
        if win32crypt is not None:
            try:
                protected = win32crypt.CryptProtectData(raw, None, None, None, None, 0)
                return base64.b64encode(protected).decode("ascii")
            except Exception:
                pass
        return base64.b64encode(raw).decode("ascii")

    def _unprotect(self, value: str) -> bytes | None:
        if not value:
            return None
        raw = base64.b64decode(value.encode("ascii"))
        if _dpapi_unprotect is not None:
            try:
                return _dpapi_unprotect(raw)
            except Exception:
                pass
        if win32crypt is not None:
            try:
                _, unprotected = win32crypt.CryptUnprotectData(raw, None, None, None, 0)
                return unprotected
            except Exception:
                pass
        return raw

    def save_activation(self, data: dict) -> None:
        self._set_string("ActivationBlob", self._protect(json.dumps(data, separators=(",", ":")).encode("utf-8")))

    def load_activation(self) -> dict | None:
        raw = self._unprotect(self._get_string("ActivationBlob") or "")
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def clear_activation(self) -> None:
        self._delete_value("ActivationBlob")

    def save_pending_serial(self, serial: str) -> None:
        self._set_string("PendingSerial", serial.strip())

    def load_pending_serial(self) -> str | None:
        return self._get_string("PendingSerial")

    def clear_pending_serial(self) -> None:
        self._delete_value("PendingSerial")

    def save_marker(self, name: str, value: str) -> None:
        self._set_string(name, value)

    def load_marker(self, name: str) -> str | None:
        return self._get_string(name)
