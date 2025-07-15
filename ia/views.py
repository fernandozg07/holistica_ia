import json
from django.db.models import Q # Adicionado para filtros complexos (se necessário)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Conversa # Importa o modelo Conversa
from .serializers import ConversaSerializer # Importa o serializer ConversaSerializer
from .openrouter import gerar_resposta_openrouter # Importa a função de resposta da IA

# Importa o modelo Usuario do app 'usuarios' para vincular conversas
from usuarios.models import Usuario


# === FUNÇÕES AUXILIARES ===
def detectar_sentimento_manual(mensagem):
    """
    Detecta o sentimento, categoria e intensidade de uma mensagem.
    """
    mensagem = mensagem.lower()
    negativas = ["triste", "cansado", "ansioso", "deprimido", "estressado", "exausto", "preocupado"]
    positivas = ["feliz", "bem", "animado", "ótimo", "grato", "leve", "tranquilo"]

    if any(p in mensagem for p in negativas):
        sentimento = "Negativo"
        categoria = "Emocional"
    elif any(p in mensagem for p in positivas):
        sentimento = "Positivo"
        categoria = "Bem-estar"
    else:
        sentimento = "Neutro"
        categoria = "Geral"

    if "muito" in mensagem or "demais" in mensagem:
        intensidade = "Alta"
    elif "um pouco" in mensagem:
        intensidade = "Média"
    else:
        intensidade = "Baixa"

    return sentimento, categoria, intensidade


# === VIEWS DE API ===

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Protege o endpoint da IA, exigindo autenticação
def responder(request):
    """
    Endpoint de API para o chat com a IA.
    Recebe a mensagem do usuário via POST (JSON), gera uma resposta da IA,
    detecta o sentimento e salva a conversa no banco de dados.
    Retorna a resposta da IA e os dados de sentimento em JSON.
    """
    mensagem_usuario = request.data.get("mensagem_usuario")

    if not mensagem_usuario:
        return Response({"erro": "Nenhuma mensagem fornecida"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        resposta_ia = gerar_resposta_openrouter(mensagem_usuario)
        sentimento, categoria, intensidade = detectar_sentimento_manual(mensagem_usuario)

        # Cria um novo registro de conversa no banco de dados, associando ao usuário logado
        Conversa.objects.create(
            usuario=request.user, # Associa a conversa ao usuário logado
            mensagem_usuario=mensagem_usuario,
            resposta_ia=resposta_ia,
            sentimento=sentimento,
            categoria_sentimento=categoria,
            intensidade_sentimento=intensidade
        )

        # Retorna a resposta em formato JSON
        return Response({
            "resposta": resposta_ia,
            "sentimento": sentimento,
            "categoria": categoria,
            "intensidade": intensidade
        })

    except Exception as e:
        # Captura qualquer erro durante o processamento (ex: erro na API da IA)
        return Response({"erro": f"Erro ao processar: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historico_api(request):
    """
    API REST que retorna o histórico de conversas com a IA do usuário logado.
    Retorna as últimas 50 conversas.
    """
    # Filtra as conversas APENAS do usuário logado
    historico = Conversa.objects.filter(usuario=request.user).order_by('-data_conversa')[:50]

    # Serializa o queryset de conversas usando o ConversaSerializer
    serializer = ConversaSerializer(historico, many=True)
    return Response(serializer.data)
