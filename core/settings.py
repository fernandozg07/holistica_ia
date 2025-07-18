import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import sys
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

if not os.getenv('RENDER') and 'pytest' not in sys.modules:
    load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
elif not DEBUG:
    allowed_hosts_local_str = os.getenv('ALLOWED_HOSTS_LOCAL', '')
    if allowed_hosts_local_str:
        ALLOWED_HOSTS.extend(allowed_hosts_local_str.split(','))
    else:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1']
elif DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

AUTH_USER_MODEL = 'usuarios.Usuario'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'ia.apps.IaConfig',
    'usuarios.apps.UsuariosConfig',

    'crispy_forms',
    'crispy_bootstrap5',
    'corsheaders',  # ✅
    'rest_framework',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅
    'corsheaders.middleware.CorsMiddleware',       # ✅
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': [
                'crispy_forms.templatetags.crispy_forms_tags',
                'crispy_forms.templatetags.crispy_forms_field',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = 'usuarios:login_api'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# 🔐 Cookies de sessão seguros
SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = True  # ✅ obrigatório para SameSite=None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'  # ✅

# 🔐 Cookies de CSRF seguros
CSRF_COOKIE_SECURE = True  # ✅
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'None'  # ✅

# 🔐 CORS + CSRF
_CSRF_TRUSTED_ORIGINS_DEFAULT = (
    'http://localhost:3000,http://127.0.0.1:3000,'
    'http://localhost:8000,http://127.0.0.1:8000,'
    'https://mindcareia.netlify.app'
)
if RENDER_EXTERNAL_HOSTNAME:
    _CSRF_TRUSTED_ORIGINS_DEFAULT += f",https://{RENDER_EXTERNAL_HOSTNAME}"

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', _CSRF_TRUSTED_ORIGINS_DEFAULT).split(',')

CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'https://mindcareia.netlify.app,http://localhost:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True  # ✅
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',  # ✅ essencial
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

AUTHENTICATION_BACKENDS = [
    'usuarios.authentication.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

if not DEBUG:
    logger.info(f"DEBUG (final): {DEBUG}")
    logger.info(f"ALLOWED_HOSTS (final): {ALLOWED_HOSTS}")
    logger.info(f"CORS_ALLOWED_ORIGINS (final): {CORS_ALLOWED_ORIGINS}")
    logger.info(f"CSRF_TRUSTED_ORIGINS (final): {CSRF_TRUSTED_ORIGINS}")
    logging.getLogger('gunicorn.error').setLevel(logging.INFO)
    logging.getLogger('gunicorn.access').setLevel(logging.INFO)
