"""
Django settings for ats2626 project.

Configurado para funcionar con PostgreSQL en producción (Render)
y SQLite o PostgreSQL en desarrollo local.
"""

from pathlib import Path
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS acepta lista separada por comas: "localhost,127.0.0.1,.onrender.com"
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if h.strip()]

# Render inyecta RENDER_EXTERNAL_HOSTNAME con el dominio exacto del servicio
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ─────────────────────────────────────────
# APLICACIONES
# ─────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reclutamiento',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Debe ir justo después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ats2626.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'reclutamiento' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'reclutamiento.context_processors.perfil_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'ats2626.wsgi.application'


# ─────────────────────────────────────────
# BASE DE DATOS (PostgreSQL en prod / SQLite en local)
# ─────────────────────────────────────────

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ─────────────────────────────────────────
# VALIDACIÓN DE CONTRASEÑAS
# ─────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────
# INTERNACIONALIZACIÓN
# ─────────────────────────────────────────

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────
# ARCHIVOS ESTÁTICOS (WhiteNoise para producción)
# ─────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise sirve y comprime estáticos sin necesidad de nginx/CDN
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos de media (hojas de vida subidas)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ─────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# ─────────────────────────────────────────
# MENSAJES DE DJANGO (etiquetas Bootstrap)
# ─────────────────────────────────────────

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}


# ─────────────────────────────────────────
# SEGURIDAD ADICIONAL EN PRODUCCIÓN
# ─────────────────────────────────────────

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# ─────────────────────────────────────────
# CORREO ELECTRÓNICO (SMTP)
# ─────────────────────────────────────────
# Configura las variables EMAIL_* en Render o en .env local
# Para Gmail: activa "Contraseñas de aplicación" en tu cuenta Google

EMAIL_BACKEND   = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST      = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT      = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS   = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='ATS Recluta <no-reply@atsrecluta.com>')
SERVER_EMAIL        = DEFAULT_FROM_EMAIL

# URL base del sitio (para links en correos)
SITE_URL = config('SITE_URL', default='https://ats2026.onrender.com')


# ─────────────────────────────────────────
# OTROS
# ─────────────────────────────────────────

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
