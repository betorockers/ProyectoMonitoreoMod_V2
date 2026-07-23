"""
Argos Guard Enterprise v4.0 - Django Master Settings.
"""
import os
import sys
from pathlib import Path
from apps.core.path_resolver import PathResolver

resolver = PathResolver()
BASE_DIR = resolver.base_dir

SECRET_KEY = os.environ.get(
    "ARGOS_SECRET_KEY",
    # Solo para desarrollo local. En producción siempre inyectar ARGOS_SECRET_KEY.
    "django-insecure-argos-v4-dev-only-replace-in-production-2026"
)

# En producción (ejecutable compilado) DEBUG siempre es False.
# Para activar DEBUG en desarrollo: $env:ARGOS_DEBUG="1"
DEBUG = os.environ.get("ARGOS_DEBUG", "0") == "1"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps Modulares v4.0
    'apps.core',
    'apps.monitoring',
    'apps.osint',
    'apps.security',
    'apps.licensing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.security.middleware.FirstRunMiddleware',
    'apps.security.middleware.RoleAccessMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Motor de Base de Datos SQLite (preparado para capa SQLCipher AES-256)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': resolver.db_path,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = resolver.get_app_data_path('static_root')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
