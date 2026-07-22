"""
Argos Guard Enterprise v4.0 - Security, JWT & Process Control Services.

Nota: El hashing de contraseñas está delegado al sistema de auth nativo de Django
(PBKDF2/Argon2 vía AUTH_PASSWORD_HASHERS). Las funciones de JWT son
utilizadas en flows futuros de API stateless.
"""
import os
import subprocess
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def generate_jwt_pair(username: str, role: str) -> dict:
    """Genera par de tokens JWT (Access Token 30m, Refresh Token 7d)."""
    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=30)
    }
    refresh_payload = {
        "sub": username,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7)
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def kill_zombie_processes():
    """Extermina procesos zombie de Chrome, ChromeDriver o subprocesos colgados."""
    try:
        if os.name == 'nt':
            for proc in ["chrome.exe", "chromedriver.exe"]:
                subprocess.call(
                    ["taskkill", "/F", "/IM", proc],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        else:
            subprocess.call(["pkill", "-9", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call(["pkill", "-9", "-f", "chromedriver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
