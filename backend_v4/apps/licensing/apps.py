import os
from django.apps import AppConfig

class LicensingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.licensing'
    path = os.path.dirname(os.path.abspath(__file__))
