"""
Argos Guard Enterprise v4.0 - System Configuration Models.

Modelos para persistir la configuración global del sistema:
Telegram, API Keys OSINT, Webhooks, SLA y Parámetros del Sistema.
"""
from django.db import models


class TelegramConfig(models.Model):
    """Configuración del Bot de Telegram para alertas de caída/recuperación."""
    bot_token = models.CharField(max_length=255, blank=True, default='')
    chat_id = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración Telegram'
        verbose_name_plural = 'Configuraciones Telegram'

    def __str__(self):
        status = '✅ Activo' if self.is_active else '❌ Inactivo'
        return f"Telegram Bot [{status}]"

    @classmethod
    def get_config(cls):
        """Retorna la configuración singleton, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def send_notification(self, message: str) -> bool:
        """Envía una alerta de red de forma asíncrona (no bloqueante) por Telegram."""
        if not self.is_active or not self.bot_token or not self.chat_id:
            return False
            
        import requests
        import threading
        
        def _send():
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            try:
                requests.post(url, json=payload, timeout=8)
            except Exception:
                pass
                
        # Ejecutar en hilo secundario para evitar latencia de red en el demonio de monitoreo
        threading.Thread(target=_send, daemon=True).start()
        return True


class ApiKeyConfig(models.Model):
    """Claves de API para servicios OSINT externos (AbuseIPDB, Shodan, HIBP)."""
    SERVICE_CHOICES = (
        ('abuseipdb', 'AbuseIPDB - Reputación de IP & Amenazas'),
        ('shodan', 'Shodan - Infraestructura Expuesta'),
        ('hibp', 'Have I Been Pwned - Auditoría de Fugas'),
    )
    service = models.CharField(max_length=30, choices=SERVICE_CHOICES, unique=True)
    api_key = models.CharField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clave de API OSINT'
        verbose_name_plural = 'Claves de API OSINT'

    def __str__(self):
        return f"{self.get_service_display()} [{'✅' if self.is_active else '❌'}]"


class WebhookConfig(models.Model):
    """Endpoints de Webhooks para notificación a plataformas externas."""
    SERVICE_CHOICES = (
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('pagerduty', 'PagerDuty'),
        ('jira', 'Jira / Atlassian'),
        ('generic', 'Webhook Genérico'),
    )
    service = models.CharField(max_length=30, choices=SERVICE_CHOICES, unique=True)
    endpoint_url = models.URLField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'

    def __str__(self):
        return f"{self.get_service_display()} [{'✅' if self.is_active else '❌'}]"


class SlaConfig(models.Model):
    """Configuración de SLA y equipo de soporte."""
    team_name = models.CharField(max_length=200, blank=True, default='')
    support_email = models.EmailField(max_length=254, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración SLA'
        verbose_name_plural = 'Configuraciones SLA'

    def __str__(self):
        return f"SLA: {self.team_name or 'Sin configurar'}"

    @classmethod
    def get_config(cls):
        """Retorna la configuración singleton, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SystemParams(models.Model):
    """Parámetros globales del sistema de monitoreo."""
    SOUND_CHOICES = (
        ('beep', 'Beep estándar'),
        ('siren', 'Sirena Táctica Cyberpunk'),
        ('mute', 'Silencioso'),
    )
    ping_interval = models.IntegerField(default=5, help_text='Intervalo de ping en segundos')
    event_retention_days = models.IntegerField(default=30, help_text='Días de retención de eventos')
    notification_sound = models.CharField(max_length=30, choices=SOUND_CHOICES, default='beep')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parámetros del Sistema'
        verbose_name_plural = 'Parámetros del Sistema'

    def __str__(self):
        return f"Params: ping={self.ping_interval}s, retención={self.event_retention_days}d"

    @classmethod
    def get_config(cls):
        """Retorna la configuración singleton, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
