from __future__ import annotations

import hashlib
import os
import platform
import uuid
import winreg


def _read_machine_guid() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except OSError:
        return "unknown-machine-guid"


def get_machine_fingerprint() -> str:
    source = "|".join(
        [
            _read_machine_guid(),
            os.environ.get("COMPUTERNAME", "unknown-computer"),
            platform.system(),
            platform.release(),
            platform.machine(),
            hex(uuid.getnode()),
        ]
    )
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest().upper()
    return digest[:32]
