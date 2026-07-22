"""
Argos Guard Enterprise v4.0 - Telemetry & Camera Models.
"""
from django.db import models

class TargetNode(models.Model):
    """Nodo o servidor objetivo de monitoreo continuo."""
    label = models.CharField(max_length=150)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=80)
    protocol = models.CharField(max_length=20, default="HTTP")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, null=True, blank=True)
    isp = models.CharField(max_length=150, null=True, blank=True)
    asn = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default="online")
    latency_ms = models.FloatField(default=0.0)
    last_check = models.DateTimeField(auto_now=True)
    last_status_change = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def is_offline_long(self):
        from django.utils import timezone
        import datetime
        if self.status == 'offline' and self.last_status_change:
            return (timezone.now() - self.last_status_change) > datetime.timedelta(minutes=5)
        return False

    def __str__(self):
        return f"{self.label} ({self.host}:{self.port})"

class CameraStream(models.Model):
    """Cámara o feed de videovigilancia IP."""
    label = models.CharField(max_length=150)
    protocol = models.CharField(max_length=30, default="RTSP") # RTSP, WebRTC, HLS, MJPEG
    endpoint = models.CharField(max_length=500)
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} [{self.protocol}]"


class MonitoringEvent(models.Model):
    """Evento de monitoreo: cambios de estado, alertas, caídas y recuperaciones."""
    EVENT_TYPES = (
        ('node_down', 'Nodo Caído'),
        ('node_up', 'Nodo Recuperado'),
        ('latency_high', 'Latencia Alta'),
        ('latency_normal', 'Latencia Normal'),
        ('packet_loss', 'Pérdida de Paquetes'),
        ('status_change', 'Cambio de Estado'),
        ('camera_offline', 'Cámara Desconectada'),
        ('camera_online', 'Cámara Reconectada'),
        ('system', 'Evento de Sistema'),
    )
    SEVERITY_CHOICES = (
        ('info', 'Informativo'),
        ('warning', 'Advertencia'),
        ('critical', 'Crítico'),
        ('resolved', 'Resuelto'),
    )
    node = models.ForeignKey(
        TargetNode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    message = models.TextField(blank=True, default='')
    details_json = models.TextField(blank=True, default='', help_text='Datos adicionales en formato JSON')
    latency_ms = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evento de Monitoreo'
        verbose_name_plural = 'Eventos de Monitoreo'

    def __str__(self):
        node_label = self.node.label if self.node else 'Sistema'
        return f"[{self.severity.upper()}] {node_label} - {self.get_event_type_display()} @ {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

