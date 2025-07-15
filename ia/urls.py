# ia/urls.py
from django.urls import path
from .views import responder, historico_api # Importa as views de API do app 'ia'

app_name = 'ia'

urlpatterns = [
    path('responder/', responder, name='responder'),
    path('historico/api/', historico_api, name='historico_api'),
]
