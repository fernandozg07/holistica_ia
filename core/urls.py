# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importe a view csrf_token_view do aplicativo usuarios
from usuarios.views import csrf_token_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Endpoint para o CSRF token, deve ser acessível publicamente
    path('api/csrf/', csrf_token_view, name='csrf_token'),

    # Inclua as URLs do aplicativo 'usuarios' sob o prefixo 'api/usuarios/'
    # Garanta que este include venha ANTES de includes mais genéricos se houver
    path('api/usuarios/', include('usuarios.urls', namespace='usuarios')),

    # Inclua as URLs do aplicativo 'ia' sob o prefixo 'api/ia/'
    path('api/ia/', include('ia.urls', namespace='ia')),

    # Caso você queira servir o seu aplicativo React a partir do Django
    # Geralmente, em produção, um servidor web (Nginx/Apache) serve os arquivos estáticos do React.
    # Em desenvolvimento, você pode ter um proxy ou deixar o Vite/React servir.
    # path('', TemplateView.as_view(template_name='index.html')), # Se você tiver um index.html na raiz

    # Se você tiver outras URLs de API que não se encaixam nos apps acima
    # path('api/', include('algum_outro_app.urls')),
]

# Apenas para servir arquivos de mídia e estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

