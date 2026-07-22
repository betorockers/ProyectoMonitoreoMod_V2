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

        response = self.get_response(request)
        return response
