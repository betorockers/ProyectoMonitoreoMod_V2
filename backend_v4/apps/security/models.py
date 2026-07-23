"""
Argos Guard Enterprise v4.0 - RBAC & Security Audit Models.
"""
from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = (
    ('super_admin', 'Super Administrator'),
    ('admin', 'Administrator'),
    ('operator', 'Operator'),
    ('reader', 'Reader / Auditor'),
)

class UserProfile(models.Model):
    """Perfil extendido de usuario con RBAC y MFA."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='operator')
    totp_secret = models.CharField(max_length=64, null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_profiles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} [{self.role}]"
