import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import sys
import logging

# Adiciona um print simples para verificar se o settings.py está sendo carregado
print("DEBUG: settings.py está sendo carregado no Render!")

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente do arquivo .env SOMENTE se não estiver em produção no Render
# Isso evita que o .env local sobrescreva as variáveis do Render, mas permite uso local.
# O Render define 'RENDER' como uma variável de ambiente em seus serviços.
# Além disso, não carrega durante a execução de testes (para evitar side effects indesejados).
if not os.getenv('RENDER') and 'pytest' not in sys.modules:
    load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- Configurações Principais ---

# Chave secreta para segurança do Django.
# EM PRODUÇÃO: A variável de ambiente DJANGO_SECRET_KEY DEVE ser definida no Render.
# EM DESENVOLVIMENTO: Será lida do .env. Se não encontrada, o Django levantará um erro,
# o que é bom para garantir que ela sempre esteja configurada.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Modo de depuração: True para desenvolvimento, False para produção.
# A variável de ambiente DEBUG deve ser 'True' ou 'False' (string).
# O padrão agora é False, o que é mais seguro para produção.
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Hosts permitidos para servir a aplicação.
# Em produção no Render, o hostname externo será adicionado.
# Em desenvolvimento, 'localhost', '127.0.0.1' e '0.0.0.0' são suficientes se DEBUG=True.
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
elif not DEBUG: # Se não for Render e estiver em modo de depuração (local)
    # Adicionado para permitir hosts locais quando DEBUG é False
    # Certifique-se de que ALLOWED_HOSTS_LOCAL está no seu .env se você for rodar com DEBUG=False localmente
    allowed_hosts_local_str = os.getenv('ALLOWED_HOSTS_LOCAL', '')
    if allowed_hosts_local_str:
        ALLOWED_HOSTS.extend(allowed_hosts_local_str.split(','))
    else:
        # Se DEBUG é False e não está no Render, e ALLOWED_HOSTS_LOCAL não está definido,
        # o Django ainda precisará de hosts permitidos.
        # Você pode adicionar um raise Exception aqui ou definir hosts padrão como 'localhost'
        # para evitar o CommandError se não quiser usar ALLOWED_HOSTS_LOCAL.
        # Para simplificar, vou adicionar 'localhost' e '127.0.0.1' como padrão se ALLOWED_HOSTS_LOCAL não for definido
        ALLOWED_HOSTS = ['localhost', '127.0.0.1']
elif DEBUG: # Se não for Render e estiver em modo de depuração (local)
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# --- Modelo de usuário personalizado ---
AUTH_USER_MODEL = 'usuarios.Usuario'

# --- Aplicações instaladas no projeto ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Necessário para servir arquivos estáticos, incluindo o admin

    # Apps do projeto
    'ia.apps.IaConfig',
    'usuarios.apps.UsuariosConfig',

    # Terceiros
    'crispy_forms',
    'crispy_bootstrap5',
    'corsheaders', # Adicionado para CORS
    'rest_framework',
    'whitenoise.runserver_nostatic', # Adicionado para Whitenoise em desenvolvimento
]

# --- Middlewares ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', # Mantenha SecurityMiddleware no topo
    'whitenoise.middleware.WhiteNoiseMiddleware', # Adicionado para Whitenoise em produção - DEVE SER O SEGUNDO
    'corsheaders.middleware.CorsMiddleware',        # Precisa vir antes de CommonMiddleware para CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- Configuração de URL raiz ---
ROOT_URLCONF = 'core.urls'

# --- Configuração de templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Adicionei o diretório 'templates' na raiz
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

# --- Configuração do servidor WSGI ---
WSGI_APPLICATION = 'core.wsgi.application'

# --- Configuração do Banco de Dados ---
# Em produção no Render, a variável de ambiente DATABASE_URL será usada.
# Em desenvolvimento, o padrão será SQLite, ou a URL do .env se fornecida.
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,   # Tempo máximo para uma conexão de banco de dados ficar aberta
        ssl_require=not DEBUG # Exige SSL para o banco de dados em produção (Render)
    )
}

# --- Validadores de Senha ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Configurações de Internacionalização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True # Depreciado no Django 4.0+, mas ainda funcional. Considere usar USE_TZ=True.
USE_TZ = True

# --- Configurações de Arquivos Estáticos e de Mídia ---
STATIC_URL = '/static/'
# Diretórios onde o Django vai procurar arquivos estáticos durante o desenvolvimento
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), # Crie esta pasta na raiz do seu projeto
]
# Diretório onde os arquivos estáticos serão coletados para produção pelo Whitenoise
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Configuração do storage para Whitenoise em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Configurações de arquivos de mídia (uploads de usuários)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Autenticação e Sessão ---
# Autenticação via sessão (para o admin e possível uso futuro com templates Django)
LOGIN_URL = 'usuarios:login_api' # Ajustado para o nome da sua API de login
LOGIN_REDIRECT_URL = '/' # Redireciona para a raiz após login bem-sucedido (para React)
LOGOUT_REDIRECT_URL = '/' # Redireciona para a raiz após logout

SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True
# ✅ CRÍTICO PARA iOS/Safari: Sempre False para permitir cookies cross-site
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = False
# ✅ CRÍTICO PARA iOS/Safari: Sempre 'Lax' para compatibilidade
SESSION_COOKIE_SAMESITE = 'Lax'

# --- CSRF (Cross-Site Request Forgery) ---
# ✅ CRÍTICO PARA iOS/Safari: Sempre False para permitir cookies cross-site
CSRF_COOKIE_SECURE = False
# ✅ CRÍTICO PARA iOS/Safari: Usar cookies em vez de sessões
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
# ✅ CRÍTICO PARA iOS/Safari: Sempre 'Lax' para compatibilidade
CSRF_COOKIE_SAMESITE = 'Lax'

# Adicione esta linha para informar ao Django que ele está atrás de um proxy SSL (como o Render)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# 🔐 CORS + CSRF
_CSRF_TRUSTED_ORIGINS_DEFAULT = (
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://mindcareia.netlify.app',
)
if RENDER_EXTERNAL_HOSTNAME:
    _CSRF_TRUSTED_ORIGINS_DEFAULT += (f"https://{RENDER_EXTERNAL_HOSTNAME}",) # Adiciona como tupla

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', ','.join(_CSRF_TRUSTED_ORIGINS_DEFAULT)).split(',')

_CORS_ALLOWED_ORIGINS_DEFAULT = (
    'https://mindcareia.netlify.app',
    'https://holistica-ia-backend.onrender.com', # ✅ Garante que o domínio do Render está aqui
    'http://localhost:3000',
    'http://127.0.0.1:3000',
)
# ✅ No Render, o domínio do backend é holistica-ia-backend.onrender.com
# Se o RENDER_EXTERNAL_HOSTNAME for diferente, adicione-o também.
if RENDER_EXTERNAL_HOSTNAME and f"https://{RENDER_EXTERNAL_HOSTNAME}" not in _CORS_ALLOWED_ORIGINS_DEFAULT:
    _CORS_ALLOWED_ORIGINS_DEFAULT += (f"https://{RENDER_EXTERNAL_HOSTNAME}",)

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', ','.join(_CORS_ALLOWED_ORIGINS_DEFAULT)).split(',')

# ✅ ESSENCIAL: Permite que o frontend envie e receba cookies e credenciais
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
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
    # Estas linhas de log só serão ativadas se DEBUG for False (ou seja, em produção)
    logger.info(f"DEBUG (final): {DEBUG}")
    logger.info(f"ALLOWED_HOSTS (final): {ALLOWED_HOSTS}")
    logger.info(f"CORS_ALLOWED_ORIGINS (final): {CORS_ALLOWED_ORIGINS}")
    logger.info(f"CSRF_TRUSTED_ORIGINS (final): {CSRF_TRUSTED_ORIGINS}")
    logging.getLogger('gunicorn.error').setLevel(logging.INFO)
    logging.getLogger('gunicorn.access').setLevel(logging.INFO)