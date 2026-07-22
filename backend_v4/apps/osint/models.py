"""
Argos Guard Enterprise v4.0 - OSINT Search History & Logs.
"""
from django.db import models

class OsintQueryLog(models.Model):
    """Registro de consultas de inteligencia efectuadas en la consola."""
    module_type = models.CharField(max_length=50) # PPU, RUT, DNS, WHOIS, IP, etc.
    query_term = models.CharField(max_length=255)
    result_json = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default="success")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.module_type}] {self.query_term} @ {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
