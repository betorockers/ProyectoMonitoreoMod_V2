# ping_logic.py

import subprocess
import platform
import time
import re


def get_mac_address(ip):
    """Busca la MAC address en la tabla ARP después de un ping exitoso."""
    # Comando ARP - diferente sintaxis en Windows vs Linux
    if platform.system().lower() == "windows":
        arp_command = ["arp", "-a", ip]
        mac_pattern = r"([a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
    else:  # Linux/macOS
        arp_command = ["arp", ip]
        mac_pattern = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"

    # Configuración para ocultar la ventana de consola en Windows
    startupinfo = None
    if platform.system().lower() == "windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        result = subprocess.run(
            arp_command,
            capture_output=True,
            text=True,
            timeout=5,
            startupinfo=startupinfo,
        )

        match = re.search(mac_pattern, result.stdout, re.IGNORECASE)

        if match:
            mac = match.group(1).upper().replace("-", ":")
            return mac
        else:
            return "No disponible (ARP)"

    except Exception as e:
        # En caso de error (ej: permisos, o equipo fuera de la red local)
        return f"Error ARP: {e}"


def ping_ip(ip, monitor, interval_sec):
    # Parámetros de ping por plataforma
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"

    # Comando de ping: 1 paquete, timeout de 1 segundo
    command = ["ping", param, "1", timeout_param, "1000", ip]

    # Configuración para ocultar la ventana de consola en Windows
    startupinfo = None
    if platform.system().lower() == "windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    while True:
        try:
            # Se pasa startupinfo para evitar parpadeo de consola
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=2,
                startupinfo=startupinfo,
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
                    # Buscar "tiempo=XXms" o "time=XXms"
                    match = re.search(r"tiempo[=<](\d+)", result.stdout, re.IGNORECASE)
                    if not match:
                        match = re.search(
                            r"time[=<](\d+)", result.stdout, re.IGNORECASE
                        )
                    if match:
                        latencia = float(match.group(1))
                else:
                    # Linux/Mac: buscar "time=XX.X ms"
                    match = re.search(r"time=([\d.]+)", result.stdout, re.IGNORECASE)
                    if match:
                        latencia = float(match.group(1))
            except:
                pass

        # Verificar si el widget aún existe antes de intentar actualizarlo
        # Esto evita errores si se recarga la lista de equipos
        try:
            if not monitor.winfo_exists():
                break
        except:
            break

        monitor.update_status(new_status, mac_address, latencia)

        time.sleep(interval_sec)
