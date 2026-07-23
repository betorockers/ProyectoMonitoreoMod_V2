"""
Argos Guard Enterprise v4.0 - Telemetry Background Daemon
"""
import threading
import asyncio
import time
import queue
from django.utils import timezone
from apps.core.async_runner import NetworkProbeRunner

# Cola en memoria para pasar notificaciones Toast del demonio a las vistas
toast_queue = queue.Queue(maxsize=100)

class TelemetryDaemon(threading.Thread):
    def __init__(self, interval_seconds=2.0):
        super().__init__(daemon=True)
        self.interval = interval_seconds
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        """Bucle síncrono que corre en su propio hilo."""
        # Importaciones locales para evitar problemas circulares o de carga prematura de Django
        from apps.monitoring.models import TargetNode, MonitoringEvent

        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:
                # 1. Obtener nodos (Síncrono - Seguro en el hilo)
                nodes = list(TargetNode.objects.all())
                
                if nodes:
                    # 2. Preparar targets
                    targets = [{"host": node.host, "port": node.port, "id": node.id} for node in nodes]
                    
                    # 3. Ejecutar probe_batch asíncronamente en un loop dedicado a la tarea de red
                    results = asyncio.run(NetworkProbeRunner.probe_batch(targets))
                    
                    # 4. Procesar resultados y registrar eventos (Síncrono - Seguro)
                    for node in nodes:
                        for res in results:
                            if isinstance(res, dict) and res.get("host") == node.host:
                                new_status = res.get("status")
                                
                                # Si hubo cambio de estado
                                if node.status != new_status:
                                    node.last_status_change = timezone.now()
                                    
                                    # Cargar configuración de Telegram para alertas móviles
                                    try:
                                        from apps.core.models import TelegramConfig
                                        telegram = TelegramConfig.get_config()
                                    except Exception:
                                        telegram = None

                                    if new_status == "offline":
                                        MonitoringEvent.objects.create(
                                            node=node,
                                            event_type='node_down',
                                            severity='critical',
                                            message=f'Nodo {node.label} ({node.host}) ha perdido conectividad.'
                                        )
                                        try:
                                            toast_queue.put_nowait({
                                                'message': f'⚠️ Alerta: Nodo {node.label} está OFFLINE',
                                                'status': 'offline',
                                                'node_id': node.id
                                            })
                                        except queue.Full:
                                            pass

                                        # Alerta de Telegram
                                        if telegram:
                                            now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
                                            msg = (
                                                f"🚨 <b>ALERTA DE CAÍDA - ARGOS GUARD</b> 🚨\n\n"
                                                f"<b>Equipo:</b> {node.label}\n"
                                                f"<b>Host:</b> {node.host}\n"
                                                f"<b>Estado:</b> 🔴 <b>OFFLINE</b>\n"
                                                f"<b>Hora:</b> {now_str}"
                                            )
                                            telegram.send_notification(msg)

                                    elif new_status == "online":
                                        MonitoringEvent.objects.create(
                                            node=node,
                                            event_type='node_up',
                                            severity='resolved',
                                            message=f'Nodo {node.label} ({node.host}) ha recuperado conectividad.'
                                        )
                                        try:
                                            toast_queue.put_nowait({
                                                'message': f'✅ Recuperado: Nodo {node.label} está ONLINE',
                                                'status': 'online',
                                                'node_id': node.id
                                            })
                                        except queue.Full:
                                            pass

                                        # Alerta de Telegram
                                        if telegram:
                                            now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
                                            msg = (
                                                f"✅ <b>RECUPERACIÓN DE RED - ARGOS GUARD</b> ✅\n\n"
                                                f"<b>Equipo:</b> {node.label}\n"
                                                f"<b>Host:</b> {node.host}\n"
                                                f"<b>Estado:</b> 🟢 <b>ONLINE</b>\n"
                                                f"<b>Latencia:</b> {res.get('latency_ms', 0.0)} ms\n"
                                                f"<b>Hora:</b> {now_str}"
                                            )
                                            telegram.send_notification(msg)
                                
                                if res.get("mac_address"):
                                    node.mac_address = res.get("mac_address")
                                    
                                node.status = new_status
                                node.latency_ms = res.get("latency_ms", 0.0)
                                node.save(update_fields=['status', 'latency_ms', 'last_check', 'last_status_change', 'mac_address'])
                                break
            except Exception as e:
                # Evitamos que caiga el hilo completo ante errores de base de datos temporales
                print(f"[TelemetryDaemon Error] {e}")

            # 5. Esperar el resto del intervalo antes del siguiente ciclo
            elapsed = time.time() - start_time
            sleep_time = max(0.1, self.interval - elapsed)
            time.sleep(sleep_time)

# Instancia global del demonio
_telemetry_daemon = None
_daemon_started = False  # Lock global: garantiza que el daemon arranca exactamente una vez.

def start_daemon():
    global _telemetry_daemon, _daemon_started
    # Lock de módulo: si ya arrancó en este proceso, no crear otra instancia.
    if _daemon_started:
        return
    if _telemetry_daemon is None or not _telemetry_daemon.is_alive():
        _telemetry_daemon = TelemetryDaemon(interval_seconds=2.0)
        _telemetry_daemon.start()
        _daemon_started = True
