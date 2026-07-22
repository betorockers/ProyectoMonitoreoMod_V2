from django.apps import AppConfig

class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'

    def ready(self):
        import os
        import sys
        # Iniciar daemon únicamente en el proceso worker de Django (no en el reloader/padre).
        # En desarrollo: RUN_MAIN='true' identifica el proceso hijo que ejecuta la app.
        # En producción (gunicorn/waitress): RUN_MAIN no existe, el daemon debe arrancar.
        # Nunca iniciar en contexto de comando de gestión (manage.py migrate, etc.).
        running_server = (
            os.environ.get('RUN_MAIN') == 'true' or
            not any(cmd in sys.argv for cmd in ['test', 'migrate', 'makemigrations', 'collectstatic', 'shell'])
        )
        if running_server:
            from apps.monitoring.daemon import start_daemon
            start_daemon()
