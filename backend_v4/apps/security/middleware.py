from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User

class FirstRunMiddleware:
    """
    Argos Guard Enterprise v4.0 - First Run Middleware.
    
    Intercepta todas las solicitudes web. Si no existen usuarios en la base de datos,
    redirige forzosamente a la pantalla de Setup (Inicialización).
    Si ya hay usuarios, bloquea el acceso a la pantalla de Setup.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # Ignorar recursos estáticos o multimedia para que la interfaz cargue correctamente
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)
            
        try:
            has_users = User.objects.exists()
        except Exception:
            # Si hay error (ej. migraciones pendientes), dejar pasar por si es un comando CLI,
            # pero en runtime normal esto asumirá no hay usuarios.
            has_users = False

        setup_url = reverse('setup')
        login_url = reverse('login')

        if not has_users:
            # Si no hay usuarios y no estamos en la página de setup, redirigir a setup
            if path != setup_url:
                return redirect(setup_url)
        else:
            # Si hay usuarios y tratamos de acceder a setup, redirigir al login
            if path == setup_url:
                return redirect(login_url)

        return self.get_response(request)


class RoleAccessMiddleware:
    """
    Middleware de Control de Acceso Basado en Roles (RBAC).
    Garantiza restricciones duras a nivel de backend para los roles 'admin' y 'operator'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import HttpResponseForbidden
        
        path = request.path_info
        user = request.user

        # Ignorar recursos estáticos o multimedia
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Si el usuario no está autenticado, ignorar (los decoradores se encargan)
        if not user.is_authenticated:
            return self.get_response(request)

        try:
            role = user.profile.role
        except Exception:
            role = 'operator'

        # 1. RESTRICCIONES PARA EL ROL OPERADOR
        if role == 'operator':
            # Solo puede ver Monitoreo Activo, Historial Eventos y Video Vigilancia.
            # En OSINT solo puede acceder a RUT y PPU.
            # No puede ver Mapa Táctico, ni Configuración.
            forbidden_prefixes = [
                '/partial/map/',      # Mapa Táctico
                '/config/',           # Configuración
                '/partial/users/',    # Configuración de usuarios
            ]
            for prefix in forbidden_prefixes:
                if path.startswith(prefix):
                    return HttpResponseForbidden("❌ Acceso Restringido: Tu rol de Operador no tiene permisos para esta sección.")

            # Restricciones dentro de OSINT
            if path.startswith('/osint/'):
                allowed_osint_paths = [
                    '/osint/',
                    '/osint/rut/',
                    '/osint/ppu/',
                ]
                if path not in allowed_osint_paths:
                    return HttpResponseForbidden("❌ Acceso Restringido: En OSINT tu rol de Operador solo puede consultar RUT y PPU.")

            # Restricciones en acciones de Monitoreo/Cámaras
            forbidden_actions = [
                '/node/add/',
                '/node/remove/',
                '/import-nodes/',
                '/camera/add/',
                '/camera/remove/',
            ]
            for action in forbidden_actions:
                if path.startswith(action):
                    return HttpResponseForbidden("❌ Acceso Restringido: Tu rol de Operador no puede agregar ni eliminar activos.")

        # 2. RESTRICCIONES PARA EL ROL ADMINISTRADOR
        elif role == 'admin':
            # El administrador tiene acceso a las pestañas, pero NO puede guardar configuraciones globales de notificaciones, SLA, params o webhooks
            forbidden_config_endpoints = [
                '/config/telegram/',
                '/config/api-key/',
                '/config/webhook/',
                '/config/sla/',
                '/config/params/',
            ]
            for endpoint in forbidden_config_endpoints:
                if path.startswith(endpoint):
                    return HttpResponseForbidden("❌ Acceso Restringido: Como Administrador no tienes permisos para modificar configuraciones globales del sistema.")

            # Tampoco puede eliminar equipos, nodos, cámaras ni descargar la base de datos de respaldo
            forbidden_admin_actions = [
                '/node/remove/',
                '/camera/remove/',
                '/export/backup/',
            ]
            for action in forbidden_admin_actions:
                if path.startswith(action):
                    return HttpResponseForbidden("❌ Acceso Restringido: Como Administrador no tienes autorización para eliminar activos o descargar respaldos de base de datos.")

        return self.get_response(request)
