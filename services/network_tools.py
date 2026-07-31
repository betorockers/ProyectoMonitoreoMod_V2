# services/network_tools.py
"""
Módulo de lógica para herramientas de diagnóstico y gestión de red.
Encapsula llamadas a subprocess con parsing de resultados.

Solo contiene lógica de red pura — sin dependencias de UI.
"""

import hashlib
import os
import subprocess
import platform
import re
import socket
import threading
import time
import warnings
from urllib.parse import urlparse


class _TrustOnFirstUsePolicy:
    """Policy compatible con Paramiko para registrar la primera huella si se permite TOFU."""

    def __init__(self, known_hosts_path: str, trust_on_first_use: bool):
        self.known_hosts_path = known_hosts_path
        self.trust_on_first_use = trust_on_first_use

    def missing_host_key(self, client, hostname, key):
        if not self.trust_on_first_use:
            raise Exception(
                "La huella SSH del host no es conocida. "
                "Valide la clave del servidor o habilite confianza inicial controlada (TOFU)."
            )

        host_keys = client.get_host_keys()
        host_keys.add(hostname, key.get_name(), key)
        directory = os.path.dirname(self.known_hosts_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        host_keys.save(self.known_hosts_path)


def _ssh_fingerprint_sha256(key) -> str:
    digest = hashlib.sha256(key.asbytes()).digest()
    import base64

    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


class NetworkTools:
    """
    Herramientas de diagnóstico y gestión del sistema de red.
    Todos los métodos son estáticos (stateless) para facilitar testing.
    """

    SNMP_OID_PRESETS = {
        "sysdescr": "1.3.6.1.2.1.1.1.0",
        "sysobjectid": "1.3.6.1.2.1.1.2.0",
        "sysuptime": "1.3.6.1.2.1.1.3.0",
        "syscontact": "1.3.6.1.2.1.1.4.0",
        "sysname": "1.3.6.1.2.1.1.5.0",
        "syslocation": "1.3.6.1.2.1.1.6.0",
    }

    @staticmethod
    def _get_startupinfo():
        """Retorna StartupInfo para ocultar ventanas de consola en Windows."""
        if platform.system() == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return si
        return None

    @staticmethod
    def get_local_info() -> dict:
        """
        Obtiene información detallada de la interfaz de red activa.

        Returns:
            dict con hostname, ip, mac, gateway y dns.
        """
        info = {
            "hostname": platform.node(),
            "ip": "Desconocido",
            "mac": "No detectada",
            "gateway": "No detectada",
            "dns": [],
        }

        # IP local activa mediante socket (más fiable que parsear ipconfig)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            info["ip"] = "127.0.0.1"

        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["ipconfig", "/all"],
                    capture_output=True,
                    text=True,
                    startupinfo=NetworkTools._get_startupinfo(),
                )
                output = result.stdout
                adapters = re.split(r"adapter|adaptador", output, flags=re.IGNORECASE)

                target_section = next(
                    (s for s in adapters if info["ip"] in s), None
                )
                if target_section:
                    mac_match = re.search(
                        r"([0-9A-Fa-f]{2}-){5}([0-9A-Fa-f]{2})", target_section
                    )
                    if mac_match:
                        info["mac"] = mac_match.group(0)

                    gw_match = re.search(
                        r"(?:Gateway|enlace).*?:\s*((?:\d{1,3}\.){3}\d{1,3})",
                        target_section,
                        re.IGNORECASE,
                    )
                    if gw_match:
                        info["gateway"] = gw_match.group(1)

                    dns_match = re.search(
                        r"(?:DNS Servers|Servidores DNS).*?:",
                        target_section,
                        re.IGNORECASE,
                    )
                    if dns_match:
                        dns_chunk = target_section[dns_match.end():]
                        dns_ips = re.findall(r"((?:\d{1,3}\.){3}\d{1,3})", dns_chunk)
                        info["dns"] = dns_ips[:2]
            except Exception as e:
                print(f"[NetworkTools] Error parseando ipconfig: {e}")

        return info

    @staticmethod
    def execute_maintenance(command_type: str) -> tuple[bool, str]:
        """
        Ejecuta comandos de mantenimiento de red.

        Args:
            command_type: 'release' | 'renew' | 'flushdns'
        """
        cmd_map = {
            "release": ["ipconfig", "/release"],
            "renew": ["ipconfig", "/renew"],
            "flushdns": ["ipconfig", "/flushdns"],
        }
        if command_type not in cmd_map:
            return False, "Comando no válido"

        try:
            result = subprocess.run(
                cmd_map[command_type],
                capture_output=True,
                text=True,
                startupinfo=NetworkTools._get_startupinfo(),
                timeout=30,
            )
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "El comando excedió el tiempo de espera."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def normalize_url(target: str, scheme: str = "http") -> str:
        """Normaliza un host o URL a una URL completa."""
        cleaned = target.strip()
        if not cleaned:
            return ""
        if "://" in cleaned:
            return cleaned
        return f"{scheme}://{cleaned}"

    @staticmethod
    def extract_host(target: str) -> str:
        """Extrae el host desde una IP, dominio o URL completa."""
        cleaned = target.strip()
        if not cleaned:
            return ""
        if "://" in cleaned:
            parsed = urlparse(cleaned)
            return parsed.hostname or ""
        return cleaned.split("/")[0]

    @staticmethod
    def parse_ports(port_spec: str | list[int], max_ports: int = 16) -> list[int]:
        """
        Parsea una lista de puertos o rangos acotados.
        Soporta formatos como '80,443,554-556'.
        """
        if isinstance(port_spec, list):
            ports = [int(p) for p in port_spec]
        else:
            ports = []
            tokens = [token.strip() for token in str(port_spec).split(",") if token.strip()]
            for token in tokens:
                if "-" in token:
                    start, end = token.split("-", 1)
                    start_port, end_port = int(start), int(end)
                    if start_port > end_port:
                        start_port, end_port = end_port, start_port
                    ports.extend(range(start_port, end_port + 1))
                else:
                    ports.append(int(token))

        normalized = []
        for port in ports:
            if 1 <= int(port) <= 65535 and int(port) not in normalized:
                normalized.append(int(port))

        return normalized[:max_ports]

    @staticmethod
    def resolve_snmp_oid(oid_or_alias: str) -> str:
        """Resuelve un alias SNMP conocido o devuelve el OID informado."""
        cleaned = oid_or_alias.strip()
        if not cleaned:
            return ""
        return NetworkTools.SNMP_OID_PRESETS.get(cleaned.lower(), cleaned)

    @staticmethod
    def safe_requests_get(requests_module, url: str, *, verify_tls: bool = True, **kwargs):
        """
        Ejecuta requests.get y suprime solo InsecureRequestWarning cuando
        explicitamente se desactiva la validacion TLS.
        """
        if verify_tls:
            return requests_module.get(url, verify=True, **kwargs)

        try:
            from urllib3.exceptions import InsecureRequestWarning
        except Exception:
            InsecureRequestWarning = Warning

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            return requests_module.get(url, verify=False, **kwargs)

    @staticmethod
    def snmp_get(
        target: str,
        community: str = "public",
        oid: str = "sysName",
        port: int = 161,
        timeout: int = 2,
        retries: int = 0,
    ) -> tuple[bool, dict]:
        """Realiza una consulta SNMP v2c puntual y devuelve un resumen simple."""
        host = NetworkTools.extract_host(target)
        resolved_oid = NetworkTools.resolve_snmp_oid(oid)
        if not host:
            return False, {"error": "Host no válido", "host": "", "oid": resolved_oid}
        if not resolved_oid:
            return False, {"error": "OID no válido", "host": host, "oid": ""}

        try:
            from pysnmp.hlapi import (
                CommunityData,
                ContextData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                getCmd,
            )
        except ModuleNotFoundError:
            return False, {
                "host": host,
                "oid": resolved_oid,
                "error": "Dependencia 'pysnmp' no disponible en este entorno.",
            }

        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=1),
                UdpTransportTarget((host, int(port)), timeout=timeout, retries=retries),
                ContextData(),
                ObjectType(ObjectIdentity(resolved_oid)),
            )
            error_indication, error_status, error_index, var_binds = next(iterator)
        except Exception as e:
            return False, {
                "host": host,
                "oid": resolved_oid,
                "error": str(e),
            }

        if error_indication:
            return False, {
                "host": host,
                "oid": resolved_oid,
                "error": str(error_indication),
            }

        if error_status:
            position = int(error_index) if error_index else "?"
            return False, {
                "host": host,
                "oid": resolved_oid,
                "error": f"{error_status.prettyPrint()} en índice {position}",
            }

        entries = []
        for name, value in var_binds:
            entries.append(
                {
                    "oid": str(name),
                    "value": str(value),
                }
            )

        if not entries:
            return False, {
                "host": host,
                "oid": resolved_oid,
                "error": "Sin respuesta SNMP.",
            }

        return True, {
            "host": host,
            "community": community,
            "oid": resolved_oid,
            "entries": entries,
        }

    @staticmethod
    def ssh_run_command(
        target: str,
        username: str,
        password: str,
        command: str = "hostname",
        port: int = 22,
        timeout: int = 5,
        verify_host_key: bool = True,
        trust_on_first_use: bool = False,
        known_hosts_path: str = "",
    ) -> tuple[bool, dict]:
        """Ejecuta un comando SSH puntual y devuelve un resumen simple."""
        host = NetworkTools.extract_host(target)
        if not host:
            return False, {"error": "Host no valido", "host": "", "command": command}
        if not username.strip():
            return False, {"error": "Usuario SSH requerido", "host": host, "command": command}
        if not password:
            return False, {"error": "Contrasena SSH requerida", "host": host, "command": command}
        if not command.strip():
            return False, {"error": "Comando SSH requerido", "host": host, "command": ""}

        try:
            import paramiko
        except ModuleNotFoundError:
            return False, {
                "host": host,
                "command": command,
                "error": "Dependencia 'paramiko' no disponible en este entorno.",
            }

        client = None
        try:
            client = paramiko.SSHClient()
            if verify_host_key:
                try:
                    client.load_system_host_keys()
                except Exception:
                    pass
                if known_hosts_path and os.path.exists(known_hosts_path):
                    try:
                        client.load_host_keys(known_hosts_path)
                    except Exception:
                        pass
                client.set_missing_host_key_policy(
                    _TrustOnFirstUsePolicy(
                        known_hosts_path=known_hosts_path,
                        trust_on_first_use=trust_on_first_use,
                    )
                )
            else:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=int(port),
                username=username,
                password=password,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            remote_key = None
            transport = getattr(client, "get_transport", lambda: None)()
            if transport is not None:
                try:
                    remote_key = transport.get_remote_server_key()
                except Exception:
                    remote_key = None
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8", errors="replace").strip()
            stderr_text = stderr.read().decode("utf-8", errors="replace").strip()

            payload = {
                "host": host,
                "port": int(port),
                "username": username,
                "command": command,
                "exit_status": exit_status,
                "stdout": stdout_text,
                "stderr": stderr_text,
            }
            if remote_key is not None:
                payload["host_key_type"] = remote_key.get_name()
                payload["host_key_fingerprint"] = _ssh_fingerprint_sha256(remote_key)
            payload["host_key_mode"] = (
                "strict"
                if verify_host_key and not trust_on_first_use
                else "tofu"
                if verify_host_key and trust_on_first_use
                else "insecure"
            )
            return True, payload
        except Exception as e:
            return False, {
                "host": host,
                "command": command,
                "error": str(e),
            }
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

    @staticmethod
    def check_http_endpoint(
        target: str,
        scheme: str = "http",
        timeout: int = 5,
        verify_tls: bool = False,
    ) -> tuple[bool, dict]:
        """Realiza un chequeo HTTP/HTTPS simple y retorna un resumen útil."""
        url = NetworkTools.normalize_url(target, scheme=scheme)
        if not url:
            return False, {"error": "Destino vacío", "url": ""}

        try:
            import requests
        except ModuleNotFoundError:
            return False, {
                "url": url,
                "error": "Dependencia 'requests' no disponible en este entorno.",
            }

        started = time.perf_counter()
        try:
            response = NetworkTools.safe_requests_get(
                requests,
                url,
                timeout=timeout,
                verify_tls=verify_tls,
                allow_redirects=True,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            return True, {
                "url": response.url,
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed_ms, 1),
                "server": response.headers.get("Server", ""),
                "content_type": response.headers.get("Content-Type", ""),
                "title": title,
            }
        except requests.RequestException as e:
            return False, {
                "url": url,
                "error": str(e),
            }

    @staticmethod
    def scan_ports(
        target: str,
        port_spec: str | list[int],
        timeout: float = 1.0,
        max_ports: int = 16,
    ) -> tuple[bool, list[dict] | str]:
        """
        Escanea un conjunto acotado de puertos contra un host.
        El escaneo es deliberadamente limitado para no desbordar el host ni la red.
        """
        host = NetworkTools.extract_host(target)
        if not host:
            return False, "Host no válido"

        try:
            ports = NetworkTools.parse_ports(port_spec, max_ports=max_ports)
        except ValueError:
            return False, "Formato de puertos inválido"

        if not ports:
            return False, "No se definieron puertos válidos"

        results = []
        for port in ports:
            started = time.perf_counter()
            is_open = False
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    is_open = True
            except OSError:
                is_open = False

            elapsed_ms = (time.perf_counter() - started) * 1000
            try:
                service = socket.getservbyport(port)
            except OSError:
                service = ""

            results.append(
                {
                    "port": port,
                    "open": is_open,
                    "latency_ms": round(elapsed_ms, 1),
                    "service": service,
                }
            )

        return True, results

    @staticmethod
    def get_ip_geolocation(ip: str, enabled: bool = False) -> str:
        """
        Obtiene la geolocalización de una IP pública.
        Utiliza la API gratuita de ip-api.com.
        """
        if not enabled:
            return ""

        # Evitar geolocalizar IPs privadas o reservadas
        private_patterns = [
            r"^10\.", r"^172\.(1[6-9]|2[0-9]|3[10])\.", r"^192\.168\.", r"^127\.", r"^169\.254\."
        ]
        if any(re.match(p, ip) for p in private_patterns) or ip == "localhost":
            return ""

        try:
            import requests
            url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    country = data.get("country", "")
                    city = data.get("city", "")
                    isp = data.get("isp", "")
                    return f" [{country}, {city} - {isp}]"
        except Exception:
            pass
        return ""

    @staticmethod
    def run_diagnostic(tool_type: str, target: str, callback, enable_geolocation: bool = False) -> None:
        """
        Ejecuta una herramienta de diagnóstico en un hilo separado.
        Llama al callback con la salida en tiempo real.
        """
        cmd_map = {
            "ping": ["ping", "-t", target],
            "tracert": ["tracert", "-d", target], # -d para no resolver nombres y ser más rápido
            "nslookup": ["nslookup", target],
        }
        if platform.system() != "Windows":
            cmd_map["ping"] = ["ping", target]
            cmd_map["tracert"] = ["traceroute", "-n", target]

        command = cmd_map.get(tool_type)
        if not command:
            callback("Herramienta no válida.")
            callback("PROCESS_FINISHED")
            return

        def _worker():
            proc = None
            geo_cache = {}
            try:
                startupinfo = NetworkTools._get_startupinfo()
                creationflags = (
                    subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )

                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    errors="replace",
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
                callback(None, proc=proc)

                for line in iter(proc.stdout.readline, ""):
                    if not line:
                        break
                    
                    # Geolocalización en caliente para Tracert
                    if tool_type == "tracert" and enable_geolocation:
                        ip_match = re.search(r"((?:\d{1,3}\.){3}\d{1,3})", line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if ip not in geo_cache:
                                geo_cache[ip] = NetworkTools.get_ip_geolocation(ip, enabled=enable_geolocation)
                            line = line.rstrip() + geo_cache[ip] + "\n"
                    
                    callback(line)

                proc.stdout.close()
                proc.wait()
            except FileNotFoundError:
                callback(
                    f"Error: El comando '{command[0]}' no se encontró."
                )
            except Exception as e:
                callback(f"Error inesperado: {e}")
            finally:
                callback("PROCESS_FINISHED")

        threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    def stop_diagnostic(process) -> None:
        """Detiene un proceso de diagnostico en ejecucion."""
        if process:
            try:
                process.terminate()
                wait_fn = getattr(process, "wait", None)
                if callable(wait_fn):
                    try:
                        wait_fn(timeout=2)
                    except subprocess.TimeoutExpired:
                        kill_fn = getattr(process, "kill", None)
                        if callable(kill_fn):
                            kill_fn()
            except Exception as e:
                print(f"[NetworkTools] Error al terminar proceso: {e}")

    @staticmethod
    def get_arp_table() -> tuple[bool, list | str]:
        """Ejecuta 'arp -a' y parsea la salida."""
        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                startupinfo=NetworkTools._get_startupinfo(),
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0
                ),
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                return False, f"Error ejecutando arp: {result.stderr}"

            pattern = re.compile(
                r"\s*((?:\d{1,3}\.){3}\d{1,3})\s+((?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2})\s+(\w+)"
            )
            entries = [
                {"ip": m.group(1), "mac": m.group(2), "type": m.group(3)}
                for line in result.stdout.splitlines()
                if (m := pattern.search(line))
            ]
            return True, entries
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_netstat() -> tuple[bool, list | str]:
        """Ejecuta 'netstat -an' y parsea las conexiones de red."""
        try:
            result = subprocess.run(
                ["netstat", "-an"],
                capture_output=True,
                text=True,
                startupinfo=NetworkTools._get_startupinfo(),
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0
                ),
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                return False, f"Error ejecutando netstat: {result.stderr}"

            pattern = re.compile(r"^\s*(TCP|UDP)\s+(\S+)\s+(\S+)\s*(\S*)?\s*$")
            connections = [
                {
                    "proto": m.group(1),
                    "local_addr": m.group(2),
                    "foreign_addr": m.group(3),
                    "state": m.group(4) if m.group(4) else "N/A",
                }
                for line in result.stdout.splitlines()
                if (m := pattern.match(line))
            ]
            return True, connections
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_service_status(service_name: str) -> tuple[bool, str]:
        """Consulta el estado de un servicio de Windows."""
        try:
            result = subprocess.run(
                ["sc", "query", f'"{service_name}"'],
                capture_output=True,
                text=True,
                startupinfo=NetworkTools._get_startupinfo(),
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0
                ),
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout
            if "1060" in output:
                return True, "No existe"
            if "RUNNING" in output:
                return True, "Corriendo"
            if "STOPPED" in output:
                return True, "Detenido"
            return True, "Desconocido"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def manage_service(service_name: str, action: str) -> tuple[bool, str]:
        """Inicia o detiene un servicio de Windows. action: 'start' | 'stop'."""
        if action not in ["start", "stop"]:
            return False, "Acción no válida. Use 'start' o 'stop'."

        try:
            result = subprocess.run(
                ["net", action, f'"{service_name}"'],
                capture_output=True,
                text=True,
                startupinfo=NetworkTools._get_startupinfo(),
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0
                ),
                timeout=20,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0 or (action == "start" and result.returncode == 2):
                return True, result.stdout if result.stdout else "Comando ejecutado."
            error_msg = result.stderr if result.stderr else result.stdout
            return False, f"Error (código {result.returncode}): {error_msg.strip()}"
        except subprocess.TimeoutExpired:
            return False, "El comando excedió el tiempo de espera."
        except Exception as e:
            return False, str(e)
