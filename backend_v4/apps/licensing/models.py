"""
Argos Guard Enterprise v4.0 - HWID & Licensing Models.
"""
from django.db import models

class SystemLicense(models.Model):
    """Licencia Enterprise de sistema vinculada a HWID."""
    serial_key = models.CharField(max_length=100, unique=True)
    hwid = models.CharField(max_length=255)
    tier = models.CharField(max_length=50, default="ENTERPRISE")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tier}] {self.serial_key} -> {self.hwid}"
