# core/ping_logic.py
"""
Motor de red de Argos Guard: ejecución de pings ICMP y resolución ARP.
"""

import subprocess
import platform
import time
import re


def _get_startupinfo():
    """Retorna StartupInfo para ocultar ventanas de consola en Windows."""
    if platform.system().lower() == "windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def get_mac_address(ip: str) -> str:
    """Busca la dirección MAC en la tabla ARP después de un ping exitoso."""
    clean_ip = ip.strip()
    clean_ip = re.sub(r"^https?://", "", clean_ip)
    clean_ip = clean_ip.split("/")[0].split(":")[0]
    
    if platform.system().lower() == "windows":
        arp_command = ["arp", "-a", clean_ip]
        mac_pattern = r"([a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
    else:
        arp_command = ["arp", clean_ip]
        mac_pattern = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"

    try:
        result = subprocess.run(
            arp_command,
            capture_output=True,
            text=True,
            timeout=5,
            startupinfo=_get_startupinfo(),
        )
        match = re.search(mac_pattern, result.stdout, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace("-", ":")
        return "No disponible (ARP)"
    except Exception as e:
        return f"Error ARP: {e}"


def ping_ip(ip: str, monitor, interval_sec: int) -> None:
    """
    Loop de monitoreo para una IP. Ejecuta en un hilo daemon.

    Args:
        ip: Dirección IP a monitorear.
        monitor: Instancia de IPMonitor (ui.components.device_card).
        interval_sec: Segundos entre cada ping.
    """
    clean_ip = ip.strip()
    clean_ip = re.sub(r"^https?://", "", clean_ip)
    clean_ip = clean_ip.split("/")[0].split(":")[0]

    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    command = ["ping", param, "1", timeout_param, "1000", clean_ip]
    si = _get_startupinfo()

    while getattr(monitor, "_ping_thread_active", True):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=2,
                startupinfo=si,
            )
            success = result.returncode == 0
        except subprocess.TimeoutExpired:
            success = False
        except Exception:
            success = False

        new_status = "Conectado" if success else "Desconectado"
        mac_address = "No disponible"
        latencia = None

        if success:
            mac_address = get_mac_address(ip)
            try:
                if platform.system().lower() == "windows":
                    match = re.search(r"(?:time|tiempo)[=<]([\d.]+)", result.stdout, re.IGNORECASE)
                else:
                    match = re.search(r"time=([\d.]+)", result.stdout, re.IGNORECASE)
                if match:
                    latencia = float(match.group(1))
            except Exception:  # FIX H-13: bare except → except Exception
                pass

        try:
            monitor.update_status(new_status, mac_address, latencia)
        except Exception:
            break

        if not getattr(monitor, "_ping_thread_active", True):
            break
        time.sleep(interval_sec)
