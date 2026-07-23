"""
Argos Guard Enterprise v4.0 - Security & Auth Views.
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
import requests
from django.conf import settings
from django.utils import timezone
from .services import generate_jwt_pair, kill_zombie_processes
from .models import UserProfile

SUPABASE_URL = "https://zzvcyrlbywnnkoigdwzz.supabase.co"
# Usamos el service_role secret o el anon key (el service role secret estaba en credenciales.txt)
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6dmN5cmxieXdubmtvaWdkd3p6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjIyNTc3NSwiZXhwIjoyMDk3ODAxNzc1fQ.z2vj0dtAtgU24MpoaFgUok2qozksPogtnlZknsfYDXE"

def setup_view(request):
    """Página de Inicialización del Sistema (Primer Uso)."""
    if User.objects.exists():
        return redirect('login')
        
    error_msg = None
    if request.method == 'POST':
        real_name = request.POST.get('real_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        serial = request.POST.get('serial', '').strip().upper()
        
        if not all([real_name, username, password, password_confirm, serial]):
            error_msg = "Todos los campos son obligatorios."
        elif password != password_confirm:
            error_msg = "Las contraseñas no coinciden."
        else:
            import hashlib
            # Validar serial contra Supabase (hasheando el serial primero)
            hashed_serial = hashlib.sha256(serial.encode('utf-8')).hexdigest()
            headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}'
            }
            try:
                res = requests.get(
                    f"{SUPABASE_URL}/rest/v1/valid_licenses?license_hash=eq.{hashed_serial}",
                    headers=headers,
                    timeout=5
                )
                data = res.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    error_msg = "Serial inválido o no reconocido."
                else:
                    license_data = data[0]
                    if not license_data.get('is_active', False):
                        error_msg = "El serial proporcionado se encuentra inactivo."
                    else:
                        # Todo correcto, crear superusuario
                        user = User.objects.create_superuser(username=username, password=password)
                        user.first_name = real_name
                        user.save()
                        UserProfile.objects.update_or_create(user=user, defaults={'role': 'super_admin'})
                        
                        # Iniciar sesión automáticamente
                        user_auth = authenticate(request, username=username, password=password)
                        login(request, user_auth)
                        return redirect('dashboard')
            except Exception as e:
                error_msg = "Error de comunicación con el servidor de licencias."

    return render(request, 'security/setup.html', {'error': error_msg})

def login_view(request):
    """Página de Login con autenticación Django real."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            return render(request, 'security/login.html', {'error': 'Por favor complete todos los campos.'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'security/login.html', {'error': 'Usuario o contraseña incorrectos.'})

    return render(request, 'security/login.html')


def logout_view(request):
    """Cierra sesión Django, elimina procesos residuales y redirige al login."""
    logout(request)
    kill_zombie_processes()
    return redirect('login')


def user_management_partial(request):
    """Fragmento parcial HTMX para Gestión de Usuarios y Configuración."""
    from apps.core.models import TelegramConfig, SlaConfig, SystemParams

    context = {
        'telegram': TelegramConfig.get_config(),
        'sla': SlaConfig.get_config(),
        'params': SystemParams.get_config(),
        'users': User.objects.select_related('profile').all(),
    }
    return render(request, 'security/partials/user_management.html', context)


@require_POST
def create_user(request):
    """Crea un nuevo usuario con perfil RBAC."""
    # Validación de Rol del Creador
    creator_role = request.user.profile.role
    
    real_name = request.POST.get('real_name', '').strip()
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    role = request.POST.get('role', 'operator')

    if creator_role == 'admin' and role != 'operator':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Error: Los administradores solo pueden crear usuarios operadores.',
            'status': 'error'
        })

    if not username or not password:
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Usuario y contraseña son obligatorios.',
            'status': 'error'
        })

    if User.objects.filter(username=username).exists():
        return render(request, 'security/partials/_config_toast.html', {
            'message': f'❌ El usuario "{username}" ya existe.',
            'status': 'error'
        })

    user = User.objects.create_user(username=username, password=password)
    user.first_name = real_name
    user.save()
    
    UserProfile.objects.update_or_create(
        user=user, 
        defaults={
            'role': role,
            'created_by': request.user
        }
    )

    response = render(request, 'security/partials/_config_toast.html', {
        'message': f'✅ Usuario "{username}" creado exitosamente con rol {role}.',
        'status': 'success'
    })
    # Forzar refresco de la tabla de usuarios via HTMX
    response['HX-Trigger'] = 'refreshUserTable'
    return response


@require_POST
def delete_user(request, user_id):
    """Elimina un usuario de la base de datos validando los roles y propiedad de creación."""
    try:
        user_to_delete = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Error: El usuario a eliminar no existe.',
            'status': 'error'
        })

    # Intentar obtener el perfil del usuario de forma segura
    try:
        profile_to_delete = user_to_delete.profile
        user_role = profile_to_delete.role
        created_by = profile_to_delete.created_by
    except Exception:
        # Fallback si no tiene perfil creado aún
        user_role = 'operator'
        created_by = None

    current_user = request.user
    try:
        current_role = current_user.profile.role
    except Exception:
        current_role = 'operator'

    # Validaciones de seguridad de eliminación
    if user_to_delete == current_user:
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Error: No puedes eliminar tu propia cuenta en sesión.',
            'status': 'error'
        })

    has_permission = False
    if current_role == 'super_admin':
        # Super Admin tiene control total, borra cualquier cuenta (incluyendo administradores y otros super admins)
        has_permission = True
    elif current_role == 'admin':
        # El administrador solo puede borrar Operadores creados por él
        if user_role == 'operator' and created_by == current_user:
            has_permission = True

    if not has_permission:
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: No tienes autorización para eliminar este usuario.',
            'status': 'error'
        })

    username = user_to_delete.username
    user_to_delete.delete()

    response = render(request, 'security/partials/_config_toast.html', {
        'message': f'🗑 Usuario "{username}" eliminado exitosamente del sistema.',
        'status': 'offline'
    })
    # Forzar refresco de la tabla de usuarios via HTMX
    response['HX-Trigger'] = 'refreshUserTable'
    return response


@require_POST
def save_telegram(request):
    """Guarda configuración de Telegram Bot."""
    if request.user.profile.role != 'super_admin':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: Solo el Super Administrador puede modificar la configuración de Telegram.',
            'status': 'error'
        })

    from apps.core.models import TelegramConfig
    config = TelegramConfig.get_config()
    config.bot_token = request.POST.get('bot_token', '').strip()
    config.chat_id = request.POST.get('chat_id', '').strip()
    config.is_active = bool(config.bot_token and config.chat_id)
    config.save()

    return render(request, 'security/partials/_config_toast.html', {
        'message': '✅ Credenciales de Telegram guardadas correctamente.',
        'status': 'success'
    })


@require_POST
def save_api_key(request):
    """Guarda una clave de API OSINT."""
    if request.user.profile.role != 'super_admin':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: Solo el Super Administrador puede guardar claves de API OSINT.',
            'status': 'error'
        })

    from apps.core.models import ApiKeyConfig
    service = request.POST.get('service', '').strip()
    api_key = request.POST.get('api_key', '').strip()

    if service not in ('abuseipdb', 'shodan', 'hibp'):
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Servicio no reconocido.',
            'status': 'error'
        })

    obj, _ = ApiKeyConfig.objects.update_or_create(
        service=service,
        defaults={'api_key': api_key, 'is_active': bool(api_key)}
    )

    labels = {'abuseipdb': 'AbuseIPDB', 'shodan': 'Shodan', 'hibp': 'Have I Been Pwned'}
    return render(request, 'security/partials/_config_toast.html', {
        'message': f'✅ API Key de {labels.get(service, service)} guardada.',
        'status': 'success'
    })


@require_POST
def save_webhook(request):
    """Guarda un endpoint de Webhook."""
    if request.user.profile.role != 'super_admin':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: Solo el Super Administrador puede configurar Webhooks.',
            'status': 'error'
        })

    from apps.core.models import WebhookConfig
    service = request.POST.get('service', '').strip()
    endpoint_url = request.POST.get('endpoint_url', '').strip()

    if service not in ('slack', 'teams', 'pagerduty', 'jira', 'generic'):
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Servicio webhook no reconocido.',
            'status': 'error'
        })

    obj, _ = WebhookConfig.objects.update_or_create(
        service=service,
        defaults={'endpoint_url': endpoint_url, 'is_active': bool(endpoint_url)}
    )

    labels = {'slack': 'Slack', 'teams': 'Microsoft Teams', 'pagerduty': 'PagerDuty', 'jira': 'Jira', 'generic': 'Webhook Genérico'}
    return render(request, 'security/partials/_config_toast.html', {
        'message': f'✅ Webhook de {labels.get(service, service)} guardado.',
        'status': 'success'
    })


@require_POST
def save_sla(request):
    """Guarda configuración de SLA & Equipo."""
    if request.user.profile.role != 'super_admin':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: Solo el Super Administrador puede configurar SLA y Equipo.',
            'status': 'error'
        })

    from apps.core.models import SlaConfig
    config = SlaConfig.get_config()
    config.team_name = request.POST.get('team_name', '').strip()
    config.support_email = request.POST.get('support_email', '').strip()
    config.save()

    return render(request, 'security/partials/_config_toast.html', {
        'message': '✅ Configuración SLA & Equipo guardada.',
        'status': 'success'
    })


@require_POST
def save_system_params(request):
    """Guarda parámetros del sistema."""
    if request.user.profile.role != 'super_admin':
        return render(request, 'security/partials/_config_toast.html', {
            'message': '❌ Permiso Denegado: Solo el Super Administrador puede modificar los parámetros del sistema.',
            'status': 'error'
        })

    from apps.core.models import SystemParams
    config = SystemParams.get_config()
    try:
        config.ping_interval = int(request.POST.get('ping_interval', 5))
    except (ValueError, TypeError):
        config.ping_interval = 5
    try:
        config.event_retention_days = int(request.POST.get('event_retention_days', 30))
    except (ValueError, TypeError):
        config.event_retention_days = 30
    config.notification_sound = request.POST.get('notification_sound', 'beep')
    config.save()

    return render(request, 'security/partials/_config_toast.html', {
        'message': '✅ Parámetros del sistema guardados.',
        'status': 'success'
    })


def shutdown_system(request):
    """Mata todos los procesos del kiosko (backend y GUI) inmediatamente para no dejar zombies."""
    import os
    import threading
    
    def kill_all():
        os._exit(0)
        
    t = threading.Timer(0.5, kill_all)
    t.start()
    
    return JsonResponse({"status": "shutting_down", "message": "Apagando sistema..."})
