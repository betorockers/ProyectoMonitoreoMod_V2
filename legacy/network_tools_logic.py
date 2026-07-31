import subprocess
import platform
import re
import socket
import threading

class NetworkTools:
    """
    Módulo de lógica para herramientas de red y diagnóstico del sistema.
    Encapsula llamadas a subprocess y parseo de salida.
    """

    @staticmethod
    def get_local_info():
        """
        Obtiene información detallada de la interfaz de red activa.
        Retorna un diccionario con hostname, ip, mac, gateway y dns.
        """
        info = {
            "hostname": platform.node(),
            "ip": "Desconocido",
            "mac": "No detectada",
            "gateway": "No detectada",
            "dns": []
        }
        
        # 1. Obtener IP Local activa mediante socket (más fiable que ipconfig para saber cuál es la activa)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # No se conecta realmente, solo determina la ruta de salida
            s.connect(("8.8.8.8", 80))
            info["ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            info["ip"] = "127.0.0.1"

        # 2. Parsear ipconfig /all (Windows) para obtener el resto de datos
        if platform.system() == "Windows":
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                # Ejecutar ipconfig /all
                result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, startupinfo=startupinfo)
                output = result.stdout
                
                # Estrategia: Buscar la sección del adaptador que tiene nuestra IP
                # Dividimos por "adapter" o "adaptador" para procesar por bloques
                adapters = re.split(r"adapter|adaptador", output, flags=re.IGNORECASE)
                
                target_section = None
                for section in adapters:
                    if info["ip"] in section:
                        target_section = section
                        break
                
                if target_section:
                    # Extraer MAC (Physical Address)
                    mac_match = re.search(r"([0-9A-Fa-f]{2}-){5}([0-9A-Fa-f]{2})", target_section)
                    if mac_match:
                        info["mac"] = mac_match.group(0)
                    
                    # Extraer Gateway
                    # Busca patrones como "Default Gateway . . . : 192.168.1.1"
                    gateway_match = re.search(r"(?:Gateway|enlace).*?:\s*((?:\d{1,3}\.){3}\d{1,3})", target_section, re.IGNORECASE)
                    if gateway_match:
                        info["gateway"] = gateway_match.group(1)
                        
                    # Extraer DNS Servers
                    # Busca la sección de DNS y extrae todas las IPs que encuentre ahí
                    dns_header_match = re.search(r"(?:DNS Servers|Servidores DNS).*?:", target_section, re.IGNORECASE)
                    if dns_header_match:
                        # Tomamos el texto desde donde dice DNS hasta el final de la sección o doble salto de línea
                        start_idx = dns_header_match.end()
                        dns_chunk = target_section[start_idx:]
                        # Extraemos las primeras IPs que aparezcan (suelen venir en lista)
                        dns_ips = re.findall(r"((?:\d{1,3}\.){3}\d{1,3})", dns_chunk)
                        # Filtramos para no tomar la IP propia o gateway si se colaron, aunque el regex es simple
                        info["dns"] = dns_ips[:2] # Nos quedamos con los 2 primeros

            except Exception as e:
                print(f"Error parseando ipconfig: {e}")
                
        return info

    @staticmethod
    def execute_maintenance(command_type):
        """
        Ejecuta comandos de mantenimiento de red.
        command_type: 'release', 'renew', 'flushdns'
        """
        cmd_map = {
            "release": ["ipconfig", "/release"],
            "renew": ["ipconfig", "/renew"],
            "flushdns": ["ipconfig", "/flushdns"]
        }
        
        if command_type not in cmd_map:
            return False, "Comando no válido"

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Timeout generoso para renew que puede tardar
            result = subprocess.run(cmd_map[command_type], capture_output=True, text=True, startupinfo=startupinfo, timeout=30)
            
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "El comando excedió el tiempo de espera."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def run_diagnostic(tool_type, target, callback):
        """
        Ejecuta una herramienta de diagnóstico (ping, tracert, nslookup) en un hilo separado.
        Llama al callback con la salida en tiempo real.
        """
        cmd_map = {
            'ping': ['ping', '-t', target], # -t para ping continuo en Windows
            'tracert': ['tracert', target],
            'nslookup': ['nslookup', target]
        }
        
        if platform.system() != "Windows":
            # Adaptar comandos para Linux/macOS si es necesario
            cmd_map['ping'] = ['ping', target]
            cmd_map['tracert'] = ['traceroute', target]

        command = cmd_map.get(tool_type)
        if not command:
            callback("Herramienta no válida.")
            callback("PROCESS_FINISHED")
            return

        def _worker():
            proc = None
            try:
                # Configuración específica para Windows (ocultar ventana)
                startupinfo = None
                creationflags = 0
                
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    creationflags = subprocess.CREATE_NO_WINDOW
                
                # Usamos Popen para leer la salida en tiempo real
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1, # Line buffered para respuesta inmediata
                    errors='replace',
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                
                # Pasamos el proceso al callback para que pueda ser detenido
                callback(None, proc=proc)

                # Leemos línea por línea
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    callback(line)
                
                proc.stdout.close()
                proc.wait()

            except FileNotFoundError:
                callback(f"Error: El comando '{command[0]}' no se encontró. ¿Está instalado y en el PATH del sistema?")
            except Exception as e:
                callback(f"Error inesperado: {e}")
            finally:
                callback("PROCESS_FINISHED")

        threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    def stop_diagnostic(process):
        """Detiene un proceso de diagnóstico en ejecución."""
        if process:
            try:
                process.terminate()
            except Exception as e:
                print(f"Error al terminar el proceso: {e}")

    @staticmethod
    def get_arp_table():
        """Ejecuta 'arp -a' y parsea la salida para obtener la tabla ARP."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                return False, f"Error ejecutando arp: {result.stderr}"

            output = result.stdout
            entries = []
            # Regex para capturar IP, MAC y tipo. Flexible con espacios.
            pattern = re.compile(r"\s*((?:\d{1,3}\.){3}\d{1,3})\s+((?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2})\s+(\w+)")
            
            for line in output.splitlines():
                match = pattern.search(line)
                if match:
                    entries.append({
                        "ip": match.group(1),
                        "mac": match.group(2),
                        "type": match.group(3)
                    })
            
            return True, entries
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_netstat():
        """Ejecuta 'netstat -an' y parsea la salida."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(["netstat", "-an"], capture_output=True, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                return False, f"Error ejecutando netstat: {result.stderr}"

            output = result.stdout
            connections = []
            # Regex para capturar Proto, Local, Remote, State
            pattern = re.compile(r"^\s*(TCP|UDP)\s+(\S+)\s+(\S+)\s*(\S*)?\s*$")
            
            for line in output.splitlines():
                match = pattern.match(line)
                if match:
                    connections.append({
                        "proto": match.group(1),
                        "local_addr": match.group(2),
                        "foreign_addr": match.group(3),
                        "state": match.group(4) if match.group(4) else "N/A"
                    })
            
            return True, connections
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_service_status(service_name):
        """Consulta el estado de un servicio de Windows. Retorna (éxito, estado_str)."""
        command = ["sc", "query", f'"{service_name}"']
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW, check=False, encoding='utf-8', errors='replace')
            
            output = result.stdout
            if "1060" in output: # Código de error para servicio no existente
                return True, "No existe"

            if "RUNNING" in output:
                return True, "Corriendo"
            elif "STOPPED" in output:
                return True, "Detenido"
            else:
                return True, "Desconocido"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def manage_service(service_name, action):
        """Inicia o detiene un servicio de Windows. action: 'start' o 'stop'."""
        if action not in ["start", "stop"]:
            return False, "Acción no válida. Use 'start' o 'stop'."
        
        command = ["net", action, f'"{service_name}"']
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20, encoding='utf-8', errors='replace')
            
            if result.returncode == 0 or (action == 'start' and result.returncode == 2):
                return True, result.stdout if result.stdout else "Comando ejecutado."
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"Error (código {result.returncode}): {error_msg.strip()}"

        except subprocess.TimeoutExpired:
            return False, "El comando excedió el tiempo de espera."
        except Exception as e:
            return False, str(e)