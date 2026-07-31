# network_tools_logic.py

import subprocess
import platform
import re

def is_valid_ip(ip):
    """Valida si un string es una dirección IPv4 válida."""
    pattern = re.compile(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    return pattern.match(ip)

def is_valid_domain(domain):
    """Valida si un string es un nombre de dominio sintácticamente válido."""
    pattern = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$")
    return pattern.match(domain)

def run_secure_command(command_list):
    """
    Ejecuta un comando de forma segura, sin shell, y retorna la salida.
    command_list: Una lista de strings, ej: ["ping", "8.8.8.8"]
    """
    try:
        # shell=False es el default y es crucial para la seguridad
        # STARTUPINFO es para evitar que se abra una ventana de consola en Windows
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=False, # No lanzar excepción si el comando falla (ej. ping a IP caída)
            startupinfo=startupinfo,
            encoding='cp850', # Codificación común para consolas de Windows
            errors='ignore'
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        return f"Error: El comando '{command_list[0]}' no fue encontrado. Asegúrese de que esté en el PATH del sistema."
    except Exception as e:
        return f"Error inesperado al ejecutar el comando: {e}"

# Ejemplo de cómo se usaría para un ping manual
# def ping_manual(target_ip):
#     if not is_valid_ip(target_ip):
#         return "Error: Dirección IP inválida."
#     command = ["ping", "-n", "4", target_ip] if platform.system() == "Windows" else ["ping", "-c", "4", target_ip]
#     return run_secure_command(command)