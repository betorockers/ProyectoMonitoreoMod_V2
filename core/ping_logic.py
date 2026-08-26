# core/ping_logic.py
"""
Motor de red de Argos Guard (ICMP Asíncrono optimizado).
Utiliza icmplib para procesar múltiples pings en paralelo sin hilos masivos.
"""

import asyncio
import platform
import subprocess
import re
from icmplib import async_multiping

def get_mac_address(ip: str) -> str:
    """Busca la dirección MAC en la tabla ARP."""
    clean_ip = ip.strip()
    clean_ip = re.sub(r"^https?://", "", clean_ip)
    clean_ip = clean_ip.split("/")[0].split(":")[0]
    
    if platform.system().lower() == "windows":
        arp_command = ["arp", "-a", clean_ip]
        mac_pattern = r"([a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2}-[a-fA-F0-9]{2})"
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        arp_command = ["arp", clean_ip]
        mac_pattern = r"([a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2})"
        si = None

    try:
        result = subprocess.run(
            arp_command,
            capture_output=True,
            text=True,
            timeout=2,
            startupinfo=si,
        )
        match = re.search(mac_pattern, result.stdout, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace("-", ":")
        return "No disponible (ARP)"
    except Exception as e:
        return f"Error ARP: {e}"


async def _async_ping_loop(monitors_dict, ui_queue, interval_sec: int, app_instance):
    """
    Bucle asíncrono que hace multiping a todas las IPs simultáneamente.
    """
    while getattr(app_instance, "services_started", True):
        ips = list(monitors_dict.keys())
        if not ips:
            await asyncio.sleep(interval_sec)
            continue
        
        try:
            # privileged=False on Windows attempts to use the ping binary 
            # if not running as admin, which is safe and still concurrent in python.
            # If admin, it uses raw sockets natively.
            responses = await async_multiping(
                ips, 
                count=1, 
                timeout=2, 
                privileged=False
            )
            
            for host in responses:
                ip = host.address
                success = host.is_alive
                latencia = host.avg_rtt if success else None
                new_status = "Conectado" if success else "Desconectado"
                
                # Fetch MAC if alive
                mac_address = "No disponible"
                if success:
                    # MAC fetching is sync, we can offload to thread to not block async loop
                    mac_address = await asyncio.to_thread(get_mac_address, ip)
                
                monitor = monitors_dict.get(ip)
                if monitor:
                    # Send update to UI queue
                    ui_queue.put((monitor.update_status, (new_status, mac_address, latencia), {}))
                    
        except Exception as e:
            print(f"[PingEngine] Error en multiping: {e}")
            
        await asyncio.sleep(interval_sec)

def start_async_ping_loop(monitors_dict, ui_queue, interval_sec, app_instance):
    """
    Inicia el bucle de eventos asíncrono en el hilo actual (debe ser un Thread dedicado).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_ping_loop(monitors_dict, ui_queue, interval_sec, app_instance))
    finally:
        loop.close()
