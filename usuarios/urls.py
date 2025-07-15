from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, PacienteViewSet, SessaoViewSet, MensagemViewSet,
    RelatorioViewSet, NotificacaoViewSet,
    csrf_token_view, login_api, logout_api, register_api,
    buscar_pacientes_api, meu_terapeuta,
    PerfilAPIView, painel_terapeuta_api, painel_paciente_api, historico_api
)

# Adicione esta linha para definir o app_name
app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'sessoes', SessaoViewSet, basename='sessao')
router.register(r'mensagens', MensagemViewSet, basename='mensagem')
router.register(r'relatorios', RelatorioViewSet, basename='relatorio')
router.register(r'notificacoes', NotificacaoViewSet, basename='notificacao')

urlpatterns = [
    # Rotas personalizadas que devem ser diretas filhas de 'api/usuarios/'
    path('csrf/', csrf_token_view, name='csrf_token'),
    path('login/', login_api, name='login'),
    path('register/', register_api, name='register'),
    path('logout/', logout_api, name='logout'),
    path('perfil/', PerfilAPIView.as_view(), name='perfil'),
    
    # Rota para buscar pacientes - ajustada para ser direta em /api/usuarios/buscar-pacientes/
    path('buscar-pacientes/', buscar_pacientes_api, name='buscar_pacientes'),
    
    path('meu-terapeuta/', meu_terapeuta, name='meu_terapeuta'),
    path('painel-terapeuta/', painel_terapeuta_api, name='painel_terapeuta'),
    path('painel-paciente/', painel_paciente_api, name='painel_paciente'),
    path('historico/', historico_api, name='historico'),

    # Inclui as rotas geradas pelo roteador por último
    # Isso criará URLs como /api/usuarios/usuarios/, /api/usuarios/pacientes/, etc.
    path('', include(router.urls)),
]
