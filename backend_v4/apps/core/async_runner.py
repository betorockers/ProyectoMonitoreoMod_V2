"""
Argos Guard Enterprise v4.0 - AsyncIO Network Probe Runner.

Ejecuta verificaciones de conectividad concurrentes (ICMP / TCP) de alta
eficiencia para nodos y servidores monitoreados.
"""
import asyncio
import socket
import time
from typing import Dict, Any, List

class NetworkProbeRunner:
    """Ejecutor asíncrono concurentes de sondas de red."""

    @staticmethod
    async def get_mac_address(host: str) -> str:
        import platform
        import re
        if platform.system().lower() == 'windows':
            try:
                proc = await asyncio.create_subprocess_exec(
                    'arp', '-a', host,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode('cp850', errors='ignore')
                match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', output)
                if match:
                    return match.group(0).replace('-', ':').upper()
            except Exception:
                pass
        return ""

    @classmethod
    async def ping_host(cls, host: str, port: int = 80, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Realiza una prueba de latencia TCP a un host y puerto especificado.
        
        Args:
            host: Dirección IP o FQDN del objetivo.
            port: Puerto TCP a inspeccionar.
            timeout: Tiempo límite en segundos.
            
        Returns:
            Dict con estado (online/offline), latencia_ms y timestamp.
        """
        start_time = time.perf_counter()
        try:
            fut = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(fut, timeout=timeout)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            writer.close()
            await writer.wait_closed()
            mac_address = await cls.get_mac_address(host)
            return {
                "host": host,
                "port": port,
                "status": "online",
                "latency_ms": latency_ms,
                "error": None,
                "mac_address": mac_address
            }
        except (asyncio.TimeoutError, OSError, socket.error) as exc:
            # Fallback to ICMP ping (system ping)
            import platform
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
            timeout_val = '2000' if platform.system().lower() == 'windows' else '2'
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    'ping', param, '1', timeout_param, timeout_val, host,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                if proc.returncode == 0:
                    mac_address = await cls.get_mac_address(host)
                    return {
                        "host": host,
                        "port": port,
                        "status": "online",
                        "latency_ms": latency_ms,
                        "error": "TCP failed, ICMP fallback successful",
                        "mac_address": mac_address
                    }
                else:
                    return {
                        "host": host,
                        "port": port,
                        "status": "offline",
                        "latency_ms": latency_ms,
                        "error": str(exc)
                    }
            except Exception as ping_exc:
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "host": host,
                    "port": port,
                    "status": "offline",
                    "latency_ms": latency_ms,
                    "error": f"TCP err: {exc} | ICMP err: {ping_exc}"
                }

    @classmethod
    async def probe_batch(cls, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ejecuta múltiples sondas concurrentes de forma asíncrona.
        
        Args:
            targets: Lista de diccionarios con 'host' y 'port'.
            
        Returns:
            Lista de resultados de inspección de telemetría.
        """
        tasks = [
            cls.ping_host(target["host"], target.get("port", 80))
            for target in targets
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
