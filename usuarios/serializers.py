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
        # 'password' é write_only, então não precisa estar em read_only_fields.
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
    # A propriedade 'idade' é calculada no modelo Paciente
    idade = serializers.ReadOnlyField()

    # O campo 'terapeuta' é um objeto aninhado para leitura, contendo os detalhes do Terapeuta.
    # Ele refere-se ao modelo Usuario, que representa o o terapeuta.
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
            # Removido 'id' daqui, pois não é um campo válido para o modelo Paciente
            # O ID do paciente é o mesmo do usuario associado, acessível via 'usuario_id' ou 'pk'
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
        # Campos que são apenas para leitura.
        # 'usuario' é read-only porque é um OneToOneField e é gerido no perform_create da ViewSet.
        # 'terapeuta' é read-only porque 'terapeuta_id' é usado para escrita.
        read_only_fields = [
            'criado_em', 'atualizado_em', 'idade', 'terapeuta', 'usuario',
            'email', 'usuario_nome_completo', 'usuario_id'
        ]


class SessaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Sessao.
    Lida com a serialização e desserialização de sessões.
    """
    # Campos 'terapeuta' e 'paciente' são objetos aninhados para leitura.
    # 'terapeuta' é um Usuario, 'paciente' é um Paciente.
    terapeuta = UsuarioSerializer(read_only=True)
    paciente = PacienteSerializer(read_only=True) # Agora referencia PacienteSerializer

    # 'terapeuta_id' e 'paciente_id' são campos de escrita para associar os IDs.
    # 'required=False' é usado aqui porque a lógica de obrigatoriedade e inferência
    # é tratada no método `perform_create` da ViewSet, com base no tipo de utilizador.
    terapeuta_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo='terapeuta'),
        source='terapeuta',
        write_only=True,
        required=False
    )
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(), # Queryset agora filtra objetos Paciente
        source='paciente',
        write_only=True,
        required=False
    )
    duracao_timedelta = serializers.ReadOnlyField() # Propriedade calculada no model

    class Meta:
        model = Sessao
        fields = [
            'id', 'terapeuta', 'terapeuta_id',
            'paciente', 'paciente_id',
            'data', 'duracao', 'duracao_timedelta',
            'status', 'observacoes', 'criado_em', 'atualizado_em'
        ]
        # Campos que são apenas para leitura.
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'duracao_timedelta', 'terapeuta', 'paciente']


class MensagemSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Mensagem.
    Lida com a serialização e desserialização de mensagens.
    """
    # Campos 'remetente' e 'destinatario' são objetos aninhados para leitura.
    remetente = UsuarioSerializer(read_only=True)
    destinatario = UsuarioSerializer(read_only=True)

    # Campos de nome para facilitar a exibição no frontend (leitura)
    remetente_nome = serializers.CharField(source='remetente.get_full_name', read_only=True)
    destinatario_nome = serializers.CharField(source='destinatario.get_full_name', read_only=True)

    # 'destinatario_id' é um campo de escrita.
    # É 'required=False' AQUI NO SERIALIZER porque a validação de obrigatoriedade
    # e a lógica de inferência (para pacientes) serão tratadas no método 'create' do serializer.
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
            'destinatario_id', # Incluir no fields para escrita
            'remetente_nome', 'destinatario_nome' # Incluir no fields para leitura
        ]
        # Campos que são apenas para leitura (os que são definidos na view ou criados automaticamente)
        # 'destinatario_id' é write_only, então não precisa estar em read_only_fields.
        read_only_fields = ['id', 'data_envio', 'lida', 'remetente', 'destinatario', 'remetente_nome', 'destinatario_nome']

    def create(self, validated_data):
        # O remetente é o utilizador autenticado, passado via contexto da requisição
        remetente = self.context['request'].user
        validated_data['remetente'] = remetente

        # Pega o objeto Usuario se foi mapeado via destinatario_id
        destinatario = validated_data.get('destinatario') 

        if remetente.tipo == 'terapeuta':
            if not destinatario: # Se o terapeuta não forneceu um destinatario_id válido
                raise serializers.ValidationError({"destinatario_id": "O ID do destinatário é obrigatório para terapeutas."})
            # Validação: Terapeuta só pode enviar para os seus pacientes
            if not Paciente.objects.filter(usuario=destinatario, terapeuta=remetente).exists():
                raise serializers.ValidationError({"destinatario_id": "Não tem permissão para enviar mensagens para este paciente."})

        elif remetente.tipo == 'paciente':
            try:
                paciente_perfil = Paciente.objects.get(usuario=remetente)
            except Paciente.DoesNotExist:
                raise serializers.ValidationError({"detail": "Perfil de paciente não encontrado para o utilizador logado."})
            
            if not paciente_perfil.terapeuta:
                raise serializers.ValidationError({"detail": "Você precisa ter um terapeuta principal associado para enviar mensagens."})
            
            # O destinatário do paciente é sempre o seu terapeuta principal
            validated_data['destinatario'] = paciente_perfil.terapeuta
            
            # Se por acaso o paciente enviou um 'destinatario_id' no payload,
            # precisamos garantir que ele seja o terapeuta correto.
            if destinatario and destinatario != paciente_perfil.terapeuta:
                raise serializers.ValidationError({"destinatario_id": "Pacientes só podem enviar mensagens para o seu terapeuta associado."})

        else:
            raise serializers.ValidationError({"detail": "Tipo de utilizador não autorizado a enviar mensagens."})

        # Chama o método create original do ModelSerializer.
        # Agora 'remetente' e 'destinatario' já estão em validated_data.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Impedir mudança de remetente ou destinatário em updates
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
    # O campo 'usuario' é um objeto aninhado para leitura.
    usuario = UsuarioSerializer(read_only=True)
    # 'usuario_id' é um campo de escrita para associar o ID do utilizador.
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
        # Campos que são apenas para leitura.
        # 'data_conversa' é auto_now_add, então é gerado automaticamente.
        read_only_fields = ['id', 'data_conversa', 'usuario']


class RelatorioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Relatorio.
    Lida com a serialização e desserialização de relatórios.
    """
    # Campos 'terapeuta' e 'paciente' são objetos aninhados para leitura.
    # 'terapeuta' é um Usuario, 'paciente' é um Paciente.
    terapeuta = UsuarioSerializer(read_only=True)
    paciente = PacienteSerializer(read_only=True) # Agora referencia PacienteSerializer

    # 'terapeuta_id' e 'paciente_id' são campos de escrita para associar os IDs.
    terapeuta_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(tipo='terapeuta'),
        source='terapeuta',
        write_only=True,
        required=False
    )
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(), # Queryset agora filtra objetos Paciente
        source='paciente',
        write_only=True,
        required=False # A validação de obrigatoriedade é feita no perform_create da ViewSet
    )

    class Meta:
        model = Relatorio
        fields = [
            'id', 'terapeuta', 'terapeuta_id',
            'paciente', 'paciente_id',
            'titulo', 'conteudo', 'data_criacao'
        ]
        # Campos que são apenas para leitura.
        read_only_fields = ['id', 'data_criacao', 'terapeuta', 'paciente']


class NotificacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Notificacao.
    Inclui o utilizador associado para leitura.
    """
    usuario = UsuarioSerializer(read_only=True) # Para mostrar os detalhes do utilizador

    class Meta:
        model = Notificacao
        fields = [
            'id', 'usuario', 'tipo', 'assunto', 'conteudo', 'link', 'lida', 'data_criacao'
        ]
        read_only_fields = ['id', 'usuario', 'data_criacao'] # O utilizador e a data são definidos no backend
