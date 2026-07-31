# ping_logic.py

import subprocess
import platform
import re
import time

def get_mac_address(ip):
    """
    Intenta obtener la dirección MAC para una IP dada usando el comando 'arp'.
    Es una operación que puede fallar si la IP no está en la caché ARP.
    """
    try:
        # --- CORRECCIÓN DE SEGURIDAD ---
        # Se elimina shell=True para prevenir Inyección de Comandos.
        # El comando y sus argumentos se pasan como una lista.
        command = ["arp", "-a", ip]
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        output = subprocess.check_output(
            command, startupinfo=startupinfo, text=True, stderr=subprocess.DEVNULL
        )
        # Buscar un patrón de dirección MAC en la salida.
        match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", output)
        if match:
            return match.group(0).upper().replace('-', ':')
    except Exception:
        # Si el comando falla o no se encuentra la MAC, no hacemos nada.
        pass
    return "No disponible (ARP)"

def ping_ip(ip, monitor_widget, interval):
    """
    Realiza pings a una IP en un bucle infinito y actualiza el widget de la UI.
    Se ejecuta en un hilo separado para no bloquear la aplicación.
    """
    while getattr(monitor_widget, "_ping_thread_active", True):

        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '2000', ip] # -w 2000ms timeout
        
        latencia = None
        mac_address = monitor_widget.mac # Mantener MAC si ya la tenemos

        try:
            if not monitor_widget.winfo_exists():
                break

            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            reply = subprocess.check_output(command, startupinfo=startupinfo, text=True, stderr=subprocess.DEVNULL)
            
            if "time=" in reply or "tiempo=" in reply:
                match = re.search(r"(?:time|tiempo)[=<]([\d.]+)\s*ms", reply, re.IGNORECASE)
                if match:
                    latencia = float(match.group(1))
            
            if mac_address in ["Buscando MAC...", "No disponible (ARP)", "MAC Desconocida"]:
                mac_address = get_mac_address(ip)

            monitor_widget.update_status("Conectado", mac_address, latencia)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            try:
                if monitor_widget.winfo_exists():
                    monitor_widget.update_status("Desconectado", "MAC Desconocida", None)
                else:
                    break
            except Exception:
                break
        except Exception as e:
            try:
                if "invalid command name" in str(e) or "application has been destroyed" in str(e):
                    break
                if monitor_widget.winfo_exists():
                    monitor_widget.update_status("Desconectado", "Red en reinicio", None)
                else:
                    break
            except Exception:
                break

        if not getattr(monitor_widget, "_ping_thread_active", True):
            break
        
        time.sleep(interval)
