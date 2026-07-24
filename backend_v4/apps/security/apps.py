import os
from django.apps import AppConfig

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.security'
    path = os.path.dirname(os.path.abspath(__file__))
