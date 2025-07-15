from rest_framework import serializers
from .models import Conversa # Importa o modelo Conversa do próprio app 'ia'
from usuarios.models import Usuario # Importa o modelo Usuario do app 'usuarios'


# Re-incluir UsuarioSerializer aqui ou importá-lo de usuarios.serializers
# Se o UsuarioSerializer já estiver definido em usuarios.serializers,
# a melhor prática é importá-lo de lá para evitar duplicação.
# Por simplicidade e para garantir que este arquivo seja autônomo para o contexto de IA,
# vou defini-lo aqui, mas considere a importação se já existir em outro lugar.
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
    Lida com a serialização de interações de conversa entre o usuário e a IA.
    """
    # Campo 'usuario' para leitura, que retorna o objeto completo do usuário.
    usuario = UsuarioSerializer(read_only=True)

    # Campo 'usuario_id' para escrita, que permite enviar apenas o ID do usuário.
    # 'write_only=True' significa que este campo é usado para entrada de dados,
    # mas não é incluído na saída serializada.
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), # Permite qualquer usuário existente
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

