# config/settings.py
"""
Configuracion centralizada de la aplicacion.
Carga secretos desde rutas locales ignoradas por Git antes de revisar .env.
"""

import os
from pathlib import Path


def _load_local_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    root = Path(__file__).resolve().parent.parent
    preferred_secret_env = root / ".secrets" / "runtime" / "app.env"
    fallback_env = root / ".env"

    if preferred_secret_env.exists():
        load_dotenv(preferred_secret_env, override=False)
    if fallback_env.exists():
        load_dotenv(fallback_env, override=False)


_load_local_env()

# --- Telegram ---
# La aplicacion comercial no lleva credenciales precargadas:
# el administrador las define desde la pestaña de configuracion.
TELEGRAM_TOKEN_DEFAULT: str = ""
TELEGRAM_CHAT_ID_DEFAULT: str = ""

# --- Monitoreo ---
DEFAULT_PING_INTERVAL: int = 15
MIN_PING_INTERVAL: int = 1
MAX_MONITOR_COLUMNS: int = 4

# --- Backups ---
MAX_BACKUPS: int = 30
DB_FILENAME: str = "argos_guard.db"

# --- Scheduler de tareas automáticas ---
SCHEDULER_TIMES = [
    (11, 0),
    (14, 30),
    (16, 55),
]
BACKUP_HOUR: int = 16
BACKUP_MINUTE: int = 55

# --- Restricción horaria Telegram ---
ALERT_HOUR_START: int = 9
ALERT_HOUR_END: int = 17

# --- Historial y Métricas ---
MONTHLY_AVAILABILITY_FILE: str = "disponibilidad_mensual.json"
HISTORIAL_LOG_FILE: str = "historial_log.txt"
EQUIPOS_CONFIG_FILE: str = "equipos_guardados.json"
SERVICES_WHITELIST_FILE: str = "services_whitelist.json"

# --- Turnos Operacionales ---
DEFAULT_TURNO_INICIO: str = "07:00"
DEFAULT_TURNO_FIN: str = "18:00"
DEFAULT_TURNO_NOMBRE: str = "Turno Operativo"

