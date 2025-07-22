from rest_framework import serializers
from .models import Usuario, Paciente, Sessao, Mensagem, Relatorio, Notificacao
from ia.models import Conversa # Importação correta do modelo Conversa

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Usuario.
    Inclui um campo de leitura 'idade' que é uma propriedade calculada no modelo.
    Adiciona 'password' como campo de escrita para registo e atualização.
    """
    idade = serializers.ReadOnlyField()  # Propriedade calculada no model
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}) # Adicionado para registo/atualização

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'tipo',
            'telefone', 'data_nascimento', 'cpf', 'endereco', 'cep',
            'foto_perfil', 'especialidade', 'crp',
            'criado_em', 'atualizado_em', 'idade', 'password' # Incluir 'password'
        ]
        # Campos que são apenas para leitura e não podem ser modificados via API
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'idade']

    def create(self, validated_data):
        # Extrai a palavra-passe para hash
        password = validated_data.pop('password', None)
        user = Usuario.objects.create(**validated_data)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        # Extrai a palavra-passe para hash durante a atualização
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Paciente.
    Lida com a serialização e desserialização de perfis de pacientes.
    """
    # O ID do paciente é o mesmo do ID do usuário associado (devido a primary_key=True no OneToOneField)
    # Exponha-o explicitamente para clareza na API.
    id = serializers.ReadOnlyField(source='usuario.id')

    # A propriedade 'idade' é calculada no modelo Paciente
    idade = serializers.ReadOnlyField()

    # O campo 'terapeuta' é um objeto aninhado para leitura, contendo os detalhes do Terapeuta.
    # Ele refere-se ao modelo Usuario, que representa o terapeuta.
    terapeuta = UsuarioSerializer(read_only=True)

    # 'terapeuta_id' é um campo de escrita que mapeia para a ForeignKey 'terapeuta' no modelo.
    # 'write_only=True' significa que este campo é usado apenas para enviar dados para a API,
    # não sendo incluído na resposta da API.
    # 'required=False' permite que o backend defina o terapeuta para pacientes.
    terapeuta_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo='terapeuta'), # Garante que apenas IDs de terapeutas sejam válidos
        source='terapeuta',  # Mapeia para o campo 'terapeuta' do modelo
        write_only=True,
        required=False
    )

    # 'usuario' é um objeto aninhado para leitura, contendo os detalhes do Usuario principal.
    usuario = UsuarioSerializer(read_only=True)

    # O email do paciente agora vem do modelo Usuario associado
    email = serializers.ReadOnlyField(source='usuario.email')

    # Adicionando nome_completo do utilizador associado para ser usado no frontend para o campo de seleção
    usuario_nome_completo = serializers.ReadOnlyField(source='usuario.get_full_name')
    usuario_id = serializers.ReadOnlyField(source='usuario.id') # ID do utilizador associado ao paciente


    class Meta:
        model = Paciente
        fields = [
            'id', # Agora explicitamente incluído e mapeado para usuario.id
            'usuario', # Inclui os detalhes completos do utilizador associado
            'email', # O email agora é um ReadOnlyField que busca do utilizador associado
            'usuario_nome_completo', # Adicionado para frontend
            'usuario_id',            # Adicionado para frontend

            'nome_completo', 'telefone', 'data_nascimento',
            'endereco', 'cep', 'historico_medico', 'alergias', 'medicamentos',
            'emergencia_nome', 'emergencia_telefone',
            'criado_em', 'atualizado_em', 'idade',
            'terapeuta', 'terapeuta_id',
        ]
        read_only_fields = [
            'id', # Adicionado 'id' aqui também, pois é um campo de leitura
            'criado_em', 'atualizado_em', 'idade', 'terapeuta', 'usuario',
            'email', 'usuario_nome_completo', 'usuario_id'
        ]


class SessaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Sessao.
    Lida com a serialização e desserialização de sessões.
    """
    terapeuta = UsuarioSerializer(read_only=True)
    paciente = PacienteSerializer(read_only=True)

    terapeuta_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo='terapeuta'),
        source='terapeuta',
        write_only=True,
        required=False
    )
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(),
        source='paciente',
        write_only=True,
        required=False
    )
    # ✅ CORREÇÃO: duracao_timedelta agora é apenas um ReadOnlyField que expõe a propriedade do modelo.
    duracao_timedelta = serializers.ReadOnlyField() 

    class Meta:
        model = Sessao
        fields = [
            'id', 'terapeuta', 'terapeuta_id',
            'paciente', 'paciente_id',
            'data', 'duracao', 'duracao_timedelta',
            'status', 'observacoes', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'duracao_timedelta', 'terapeuta', 'paciente']


class MensagemSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Mensagem.
    Lida com a serialização e desserialização de mensagens.
    """
    remetente = UsuarioSerializer(read_only=True)
    destinatario = UsuarioSerializer(read_only=True)

    remetente_nome = serializers.CharField(source='remetente.get_full_name', read_only=True)
    destinatario_nome = serializers.CharField(source='destinatario.get_full_name', read_only=True)

    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='destinatario',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Mensagem
        fields = [
            'id', 'remetente', 'destinatario',
            'assunto', 'conteudo', 'data_envio', 'lida',
            'destinatario_id',
            'remetente_nome', 'destinatario_nome'
        ]
        read_only_fields = ['id', 'data_envio', 'lida', 'remetente', 'destinatario', 'remetente_nome', 'destinatario_nome']

    def create(self, validated_data):
        remetente = self.context['request'].user
        validated_data['remetente'] = remetente

        destinatario = validated_data.get('destinatario')  

        if remetente.tipo == 'terapeuta':
            if not destinatario:
                raise serializers.ValidationError({"destinatario_id": "O ID do destinatário é obrigatório para terapeutas."})
            if not Paciente.objects.filter(usuario=destinatario, terapeuta=remetente).exists():
                raise serializers.ValidationError({"destinatario_id": "Não tem permissão para enviar mensagens para este paciente."})

        elif remetente.tipo == 'paciente':
            try:
                paciente_perfil = Paciente.objects.get(usuario=remetente)
            except Paciente.DoesNotExist:
                raise serializers.ValidationError({"detail": "Perfil de paciente não encontrado para o utilizador logado."})
            
            if not paciente_perfil.terapeuta:
                raise serializers.ValidationError({"detail": "Você precisa ter um terapeuta principal associado para enviar mensagens."})
            
            validated_data['destinatario'] = paciente_perfil.terapeuta
            
            if destinatario and destinatario != paciente_perfil.terapeuta:
                raise serializers.ValidationError({"destinatario_id": "Pacientes só podem enviar mensagens para o seu terapeuta associado."})

        else:
            raise serializers.ValidationError({"detail": "Tipo de utilizador não autorizado a enviar mensagens."})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'remetente' in validated_data:
            raise serializers.ValidationError({"remetente": "Não é permitido alterar o remetente de uma mensagem existente."})
        if 'destinatario' in validated_data:
            raise serializers.ValidationError({"destinatario": "Não é permitido alterar o destinatário de uma mensagem existente."})
        
        return super().update(instance, validated_data)


class ConversaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Conversa (do app 'ia').
    Lida com a serialização e desserialização de conversas com a IA.
    """
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )

    class Meta:
        model = Conversa
        fields = [
            'id', 'usuario', 'usuario_id', 'mensagem_usuario', 'resposta_ia',
            'sentimento', 'categoria_sentimento', 'intensidade_sentimento',
            'data_conversa'
        ]
        read_only_fields = ['id', 'data_conversa', 'usuario']


class RelatorioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Relatorio.
    Lida com a serialização e desserialização de relatórios.
    """
    terapeuta = UsuarioSerializer(read_only=True)
    paciente = PacienteSerializer(read_only=True)

    terapeuta_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo='terapeuta'),
        source='terapeuta',
        write_only=True,
        required=False
    )
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(),
        source='paciente',
        write_only=True,
        required=False
    )

    class Meta:
        model = Relatorio
        fields = [
            'id', 'terapeuta', 'terapeuta_id',
            'paciente', 'paciente_id',
            'titulo', 'conteudo', 'data_criacao'
        ]
        read_only_fields = ['id', 'data_criacao', 'terapeuta', 'paciente']


class NotificacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Notificacao.
    Inclui o utilizador associado para leitura.
    """
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Notificacao
        fields = [
            'id', 'usuario', 'tipo', 'assunto', 'conteudo', 'link', 'lida', 'data_criacao'
        ]
        read_only_fields = ['id', 'usuario', 'data_criacao']
