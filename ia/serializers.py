from rest_framework import serializers
from .models import Conversa # Importa o modelo Conversa do próprio app 'ia'
from usuarios.models import Usuario # Importa o modelo Usuario do app 'usuarios'
# from usuarios.serializers import UsuarioSerializer as BaseUsuarioSerializer # ✅ Melhor prática: importar se já existe

# ✅ NOTA: Se UsuarioSerializer já estiver definido em 'usuarios.serializers',
# é melhor importá-lo de lá para evitar duplicação e manter um único ponto de verdade.
# Por exemplo: from usuarios.serializers import UsuarioSerializer
# Para este contexto, mantemos a definição local para clareza.
class UsuarioSerializer(serializers.ModelSerializer):
    idade = serializers.ReadOnlyField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'tipo',
            'telefone', 'data_nascimento', 'cpf', 'endereco', 'cep',
            'foto_perfil', 'especialidade', 'crp',
            'criado_em', 'atualizado_em', 'idade'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'idade']


class ConversaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Conversa.
    Lida com a serialização de interações de conversa entre o utilizador e a IA.
    """
    # Campo 'usuario' para leitura, que retorna o objeto completo do utilizador.
    usuario = UsuarioSerializer(read_only=True)

    # Campo 'usuario_id' para escrita, que permite enviar apenas o ID do utilizador.
    # 'write_only=True' significa que este campo é usado para entrada de dados,
    # mas não é incluído na saída serializada.
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), # Permite qualquer utilizador existente
        source='usuario', # Mapeia para o campo 'usuario' do modelo Conversa
        write_only=True
    )

    class Meta:
        model = Conversa
        fields = [
            'id', 'usuario', 'usuario_id', 'mensagem_usuario', 'resposta_ia',
            'sentimento', 'categoria_sentimento', 'intensidade_sentimento',
            'data_conversa'
        ]
        # Campos que são apenas para leitura.
        # 'data_conversa' é auto_now_add, então é gerado automaticamente.
        read_only_fields = ['id', 'data_conversa', 'usuario']
