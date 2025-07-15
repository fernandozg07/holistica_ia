import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Define o diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente do arquivo .env
# Isso garantirá que as variáveis do .env sejam carregadas localmente.
# Em produção no Render, as variáveis de ambiente serão definidas diretamente lá.
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- Configurações Principais ---

# Chave secreta para segurança do Django.
# EM PRODUÇÃO: A variável de ambiente DJANGO_SECRET_KEY DEVE ser definida no Render.
# EM DESENVOLVIMENTO: Será lida do .env. A chave 'sua-chave-secreta-para-dev' é um fallback,
# mas você deve ter uma chave real e forte no seu .env para desenvolvimento também.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'sua-chave-secreta-para-dev') # Use uma chave forte para dev!

# Modo de depuração: True para desenvolvimento, False para produção.
# A variável de ambiente DEBUG deve ser 'True' ou 'False' (string).
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Hosts permitidos para servir a aplicação.
# EM PRODUÇÃO: A variável de ambiente ALLOWED_HOSTS deve conter os domínios do Render.
# Em desenvolvimento: 'localhost,127.0.0.1,0.0.0.0' são suficientes.
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')
# Adiciona o hostname do Render dinamicamente em produção
if not DEBUG and 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])


# Modelo de usuário personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Aplicações instaladas no projeto
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
    'corsheaders',
    'rest_framework',
]

# Middlewares
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Precisa vir antes de CommonMiddleware para CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuração de URL raiz
ROOT_URLCONF = 'core.urls'

# Configuração de templates
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

# Configuração do servidor WSGI
WSGI_APPLICATION = 'core.wsgi.application'

# --- Configuração do Banco de Dados ---
# Em produção no Render, a variável de ambiente DATABASE_URL será usada.
# Em desenvolvimento, o padrão será SQLite.
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,  # Tempo máximo para uma conexão de banco de dados ficar aberta
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
# Diretório onde os arquivos estáticos serão coletados para produção
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

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
SESSION_COOKIE_SECURE = not DEBUG  # True em produção HTTPS, False em desenvolvimento HTTP
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# --- CSRF (Cross-Site Request Forgery) ---
CSRF_COOKIE_SECURE = not DEBUG  # True em produção HTTPS, False em desenvolvimento HTTP
CSRF_USE_SESSIONS = False # False se o token CSRF for enviado via cookie e não via sessão
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
# EM PRODUÇÃO: A variável de ambiente CSRF_TRUSTED_ORIGINS deve conter os domínios do seu frontend.
# Em desenvolvimento: os padrões para localhost são definidos.
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000').split(',')

# --- CORS (Cross-Origin Resource Sharing) ---
# As origens permitidas para CORS serão as mesmas das origens confiáveis para CSRF.
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
CORS_ALLOW_CREDENTIALS = True # Permite que credenciais (cookies, headers de autorização) sejam incluídas

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken', # Essencial para o CSRF com React
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# --- Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', # Para autenticação baseada em sessão (admin, CSRF)
        'rest_framework.authentication.BasicAuthentication', # Opcional, para testes ou APIs simples
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Padrão: exige autenticação para todas as views de API
    ],
}

# --- Email ---
# Configuração para desenvolvimento: imprime emails no console.
# Em produção, você configuraria um serviço de email real.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# --- Backends de Autenticação Personalizados ---
AUTHENTICATION_BACKENDS = [
    'usuarios.authentication.EmailBackend', # Seu backend personalizado para autenticar por email
    'django.contrib.auth.backends.ModelBackend', # Backend padrão do Django
]

# --- OpenRouter API Key ---
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')