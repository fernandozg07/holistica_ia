import json
from datetime import date, timedelta
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Usuario, Paciente, Sessao, Mensagem, Relatorio, Notificacao
# Importa o modelo Conversa do app 'ia' para uso nos dashboards
from ia.models import Conversa
from django.utils import timezone
from django.middleware.csrf import get_token # Importar get_token para CSRF
import uuid # Para gerar username único, se necessário

from .serializers import (
    UsuarioSerializer,
    PacienteSerializer,
    SessaoSerializer,
    MensagemSerializer,
    RelatorioSerializer,
    ConversaSerializer,
    NotificacaoSerializer,
)

User = get_user_model()

# --- Funções de Autenticação e CSRF ---

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """
    Retorna o CSRF token no corpo da resposta para que o frontend possa acessá-lo.
    O token também é definido como um cookie pelo Django.
    """
    token = get_token(request)
    return JsonResponse({'csrftoken': token})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Endpoint de login para o frontend React.
    Autentica o utilizador e retorna os dados do utilizador autenticado.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'detail': 'Email e palavra-passe são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, email=email, password=password)
    if user and user.is_active:
        login(request, user)
        return Response({'user': UsuarioSerializer(user).data})

    return Response({'detail': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Endpoint de registo para o frontend React.
    Cria um novo utilizador e, se for paciente, cria também o perfil de paciente.
    """
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # MELHORIA: Cria o perfil de Paciente com nome completo do request.data
        if user.tipo == 'paciente':
            nome_completo_paciente = request.data.get('first_name', '') + ' ' + request.data.get('last_name', '')
            Paciente.objects.create(
                usuario=user,
                nome_completo=nome_completo_paciente.strip(),
                # Você pode adicionar outros campos do Paciente aqui se vierem no request.data
                telefone=request.data.get('telefone', ''),
                data_nascimento=request.data.get('data_nascimento', None),
                endereco=request.data.get('endereco', ''),
                cep=request.data.get('cep', ''),
            )
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Endpoint de logout para o frontend React.
    Remove o utilizador da sessão.
    """
    logout(request)
    return Response({"detail": "Logout realizado com sucesso."})


# --- ViewSets para Modelos ---

class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar e recuperar detalhes de utilizadores.
    Apenas leitura, para proteger dados sensíveis.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']


class PacienteViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de pacientes.
    Permite que terapeutas criem/gerenciem os seus pacientes
    e pacientes visualizem os seus próprios dados de paciente.
    """
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome_completo', 'usuario__email']

    def get_queryset(self):
        user = self.request.user
        if user.tipo == 'terapeuta':
            return Paciente.objects.filter(terapeuta=user)
        elif user.tipo == 'paciente':
            paciente_perfil = Paciente.objects.filter(usuario=user).first()
            if paciente_perfil:
                return Paciente.objects.filter(usuario=user)
            return Paciente.objects.none()
        elif user.is_superuser:
            return Paciente.objects.all()
        return Paciente.objects.none()

    def perform_create(self, serializer):
        """
        Lógica aprimorada para criar ou associar um perfil de Paciente.
        Lida com cenários onde o Usuario já existe ou não.
        Apenas terapeutas e superutilizadores podem criar/associar pacientes.
        """
        user = self.request.user
        if user.tipo != 'terapeuta' and not user.is_superuser:
            raise PermissionDenied("Apenas terapeutas e superutilizadores podem criar pacientes.")

        email_data = self.request.data.get('email')
        nome_completo_data = self.request.data.get('nome_completo')
        data_nascimento_data = self.request.data.get('data_nascimento')
        telefone_data = self.request.data.get('telefone', '')
        endereco_data = self.request.data.get('endereco', '')
        cep_data = self.request.data.get('cep', '')

        if not email_data:
            raise ValidationError({"email": "O email é obrigatório para criar um novo paciente."})
        if not nome_completo_data:
            raise ValidationError({"nome_completo": "O nome completo é obrigatório para criar um novo paciente."})

        if data_nascimento_data:
            try:
                date.fromisoformat(data_nascimento_data)
            except ValueError:
                raise ValidationError({"data_nascimento": "Formato de data inválido. Use YYYY-MM-DD."})

        first_name = nome_completo_data.split(' ')[0] if nome_completo_data else ''
        last_name = ' '.join(nome_completo_data.split(' ')[1:]) if nome_completo_data else ''

        usuario_paciente = None
        existing_paciente_profile = None

        try:
            usuario_paciente = Usuario.objects.get(email=email_data)
            
            if usuario_paciente.tipo != 'paciente':
                raise ValidationError({"email": "Já existe um utilizador com este email que não é um paciente. Por favor, utilize um email diferente."})

            existing_paciente_profile = Paciente.objects.filter(usuario=usuario_paciente).first()

            if existing_paciente_profile:
                if existing_paciente_profile.terapeuta == user:
                    raise ValidationError({"email": "Este utilizador já é seu paciente."})
                elif existing_paciente_profile.terapeuta and not user.is_superuser:
                    raise ValidationError({"email": "Este utilizador já é paciente de outro terapeuta."})
                # Se o perfil existe mas não tem terapeuta, ou se o superusuário está a atribuir
                # O perfil existente será atualizado abaixo.
            else:
                # Se o usuário existe mas não tem perfil de paciente, cria um novo perfil de paciente
                existing_paciente_profile = Paciente.objects.create(
                    usuario=usuario_paciente,
                    nome_completo=nome_completo_data,
                    telefone=telefone_data,
                    data_nascimento=data_nascimento_data,
                    endereco=endereco_data,
                    cep=cep_data,
                    terapeuta=None # Será atribuído abaixo
                )

        except Usuario.DoesNotExist:
            # Se o usuário não existe, cria um novo Usuario
            username_to_use = email_data.split('@')[0]
            if Usuario.objects.filter(username=username_to_use).exists():
                username_to_use = f"{username_to_use}_{uuid.uuid4().hex[:8]}"

            usuario_paciente = Usuario.objects.create_user(
                email=email_data,
                username=username_to_use,
                first_name=first_name,
                last_name=last_name,
                tipo='paciente',
                is_active=True,
                password=User.objects.make_random_password(),
                data_nascimento=data_nascimento_data
            )
        
        terapeuta_para_paciente = None
        if user.tipo == 'terapeuta':
            terapeuta_para_paciente = user
        elif user.is_superuser:
            terapeuta_id_from_payload = serializer.validated_data.get('terapeuta')
            if terapeuta_id_from_payload:
                terapeuta_para_paciente = terapeuta_id_from_payload
            else:
                # Se superusuário não especifica terapeuta, e o paciente já tem um, mantém o existente
                if existing_paciente_profile and existing_paciente_profile.terapeuta:
                    terapeuta_para_paciente = existing_paciente_profile.terapeuta
                # Caso contrário, o terapeuta será None (se o campo permitir)

        if existing_paciente_profile:
            # Atualiza o perfil de paciente existente
            existing_paciente_profile.terapeuta = terapeuta_para_paciente
            existing_paciente_profile.nome_completo = nome_completo_data
            existing_paciente_profile.telefone = telefone_data
            existing_paciente_profile.data_nascimento = data_nascimento_data
            existing_paciente_profile.endereco = endereco_data
            existing_paciente_profile.cep = cep_data
            existing_paciente_profile.save()
            serializer.instance = existing_paciente_profile # Define a instância para o serializer retornar
        else:
            # Salva o novo perfil de paciente (se o usuário não existia ou existia sem perfil de paciente)
            serializer.save(terapeuta=terapeuta_para_paciente, usuario=usuario_paciente)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if user.tipo == 'terapeuta' and instance.terapeuta != user and not user.is_superuser:
            raise PermissionDenied("Não tem permissão para atualizar este paciente.")
        elif user.tipo == 'paciente' and instance.usuario != user and not user.is_superuser:
            raise PermissionDenied("Não tem permissão para atualizar este paciente.")
        elif not user.is_superuser and user.tipo not in ['terapeuta', 'paciente']:
             raise PermissionDenied("Não tem permissão para atualizar este paciente.")
        
        if 'usuario' in serializer.validated_data and serializer.validated_data['usuario'] != instance.usuario:
            raise ValidationError({"usuario": "Não é permitido alterar o utilizador associado a um paciente."})

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        
        is_therapist_of_patient = user.tipo == 'terapeuta' and instance.terapeuta == user
        is_superuser = user.is_superuser

        if is_therapist_of_patient or is_superuser:
            instance.delete()
        else:
            raise PermissionDenied("Você não tem permissão para deletar este paciente.")


class SessaoViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de sessões.
    Terapeutas gerenciam as suas sessões.
    Pacientes podem ver e deletar as suas próprias sessões.
    """
    serializer_class = SessaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['data']
    ordering = ['-data']

    def get_queryset(self):
        """
        Filtra sessões com base no tipo de utilizador autenticado.
        """
        user = self.request.user
        if user.tipo == 'terapeuta':
            return Sessao.objects.filter(terapeuta=user)
        elif user.tipo == 'paciente':
            paciente_perfil = Paciente.objects.filter(usuario=user).first()
            if paciente_perfil:
                return Sessao.objects.filter(paciente=paciente_perfil)
            return Sessao.objects.none()
        elif user.is_superuser: # Superusuários podem ver todas as sessões
            return Sessao.objects.all()
        return Sessao.objects.none()

    def perform_create(self, serializer):
        """
        Associa o terapeuta ou paciente autenticado à sessão.
        Cria notificações para o terapeuta e o paciente.
        """
        user = self.request.user
        session_instance = None

        try:
            if user.tipo == 'terapeuta':
                paciente_id = self.request.data.get('paciente_id')
                if not paciente_id:
                    raise ValidationError({"paciente_id": "O ID do paciente é obrigatório para terapeutas."})
                try:
                    paciente_obj = Paciente.objects.get(pk=paciente_id)
                except Paciente.DoesNotExist:
                    raise ValidationError({"paciente_id": "Paciente inválido ou não encontrado."})
                
                if paciente_obj.terapeuta != user:
                    raise PermissionDenied("Não tem permissão para agendar sessões para este paciente.")
                
                session_instance = serializer.save(terapeuta=user, paciente=paciente_obj)

            elif user.tipo == 'paciente':
                paciente_perfil = Paciente.objects.filter(usuario=user).first()
                if not paciente_perfil:
                    raise PermissionDenied("Não tem um perfil de paciente associado.")
                
                if not paciente_perfil.terapeuta:
                    raise ValidationError("Precisa ter um terapeuta associado para agendar uma sessão.")
                
                session_instance = serializer.save(paciente=paciente_perfil, terapeuta=paciente_perfil.terapeuta)
            
            elif user.is_superuser: # Superusuários podem criar sessões para qualquer terapeuta/paciente
                # Superusuários devem fornecer 'terapeuta_id' e 'paciente_id' no request.data
                terapeuta_id = self.request.data.get('terapeuta_id')
                paciente_id = self.request.data.get('paciente_id')
                if not terapeuta_id or not paciente_id:
                    raise ValidationError({"detail": "Para superutilizadores, 'terapeuta_id' e 'paciente_id' são obrigatórios."})
                
                terapeuta_obj = Usuario.objects.get(pk=terapeuta_id, tipo='terapeuta')
                paciente_obj = Paciente.objects.get(pk=paciente_id)

                if paciente_obj.terapeuta != terapeuta_obj:
                    raise ValidationError({"detail": "O paciente não está associado ao terapeuta fornecido."})

                session_instance = serializer.save(terapeuta=terapeuta_obj, paciente=paciente_obj)

            else:
                raise PermissionDenied("Acesso negado. Apenas terapeutas, pacientes e superutilizadores podem criar sessões.")

            # --- Lógica de Notificação para Sessão Criada ---
            if session_instance:
                # Notificação para o Paciente
                Notificacao.objects.create(
                    usuario=session_instance.paciente.usuario,
                    tipo='sessao',
                    assunto='Sessão Agendada!',
                    conteudo=f'A sua sessão com {session_instance.terapeuta.get_full_name()} foi agendada para {session_instance.data.strftime("%d/%m/%Y às %H:%M")}.',
                    link=f'/sessoes/{session_instance.id}/editar',
                    lida=False,
                    # data_criacao=timezone.now() # REMOVIDO: O modelo Notificacao já define auto_now_add=True ou default=timezone.now
                )
                print(f"Notificação de sessão criada para o paciente: {session_instance.paciente.usuario.username}")

                # Notificação para o Terapeuta
                Notificacao.objects.create(
                    usuario=session_instance.terapeuta,
                    tipo='sessao',
                    assunto='Nova Sessão Agendada!',
                    conteudo=f'Você agendou uma nova sessão com {session_instance.paciente.nome_completo} para {session_instance.data.strftime("%d/%m/%Y às %H:%M")}.',
                    link=f'/sessoes/{session_instance.id}/editar',
                    lida=False,
                    # data_criacao=timezone.now() # REMOVIDO: O modelo Notificacao já define auto_now_add=True ou default=timezone.now
                )
                print(f"Notificação de sessão criada para o terapeuta: {session_instance.terapeuta.username}")

        except Exception as e:
            print(f"ERRO ao criar sessão ou notificação de sessão: {e}")
            raise # Re-raise a exceção para que o DRF a trate

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user
        old_status = instance.status

        try:
            # Permite a atualização se for o terapeuta responsável, o próprio paciente ou um superutilizador
            if user.tipo == 'terapeuta' and instance.terapeuta == user:
                session_instance = serializer.save()
            elif user.tipo == 'paciente' and instance.paciente.usuario == user:
                session_instance = serializer.save()
            elif user.is_superuser: # Superutilizadores podem atualizar qualquer sessão
                session_instance = serializer.save()
            else:
                raise PermissionDenied("Não tem permissão para atualizar esta sessão.")

            # --- Lógica de Notificação para Sessão Atualizada ---
            if session_instance:
                update_message = "atualizada"
                if session_instance.status != old_status:
                    update_message = f"teve o seu status alterado para '{session_instance.status}'"
                
                # Notificação para o Paciente
                Notificacao.objects.create(
                    usuario=session_instance.paciente.usuario,
                    tipo='sessao',
                    assunto=f'Sessão {update_message.capitalize()}!',
                    conteudo=f'A sua sessão com {session_instance.terapeuta.get_full_name()} em {session_instance.data.strftime("%d/%m/%Y às %H:%M")} foi {update_message}.',
                    link=f'/sessoes/{session_instance.id}/editar',
                    lida=False,
                    # data_criacao=timezone.now() # REMOVIDO: O modelo Notificacao já define auto_now_add=True ou default=timezone.now
                )
                print(f"Notificação de sessão atualizada para o paciente: {session_instance.paciente.usuario.username}")

                # Notificação para o Terapeuta
                Notificacao.objects.create(
                    usuario=session_instance.terapeuta,
                    tipo='sessao',
                    assunto=f'Sessão {update_message.capitalize()}!',
                    conteudo=f'A sessão com {session_instance.paciente.nome_completo} em {session_instance.data.strftime("%d/%m/%Y às %H:%M")} foi {update_message}.',
                    link=f'/sessoes/{session_instance.id}/editar',
                    lida=False,
                    # data_criacao=timezone.now() # REMOVIDO: O modelo Notificacao já define auto_now_add=True ou default=timezone.now
                )
                print(f"Notificação de sessão atualizada para o terapeuta: {session_instance.terapeuta.username}")

        except Exception as e:
            print(f"ERRO ao atualizar sessão ou notificação de sessão: {e}")
            raise # Re-raise a exceção para que o DRF a trate

    def perform_destroy(self, instance):
        """
        Permite a exclusão de uma sessão pelo terapeuta responsável,
        pelo paciente que agendou a sessão, ou por um superutilizador.
        """
        user = self.request.user

        is_therapist_of_session = user.tipo == 'terapeuta' and instance.terapeuta == user
        is_patient_of_session = user.tipo == 'paciente' and instance.paciente.usuario == user
        is_superuser = user.is_superuser

        if is_therapist_of_session or is_patient_of_session or is_superuser:
            instance.delete()
        else:
            raise PermissionDenied("Não tem permissão para deletar esta sessão.")


class MensagemViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de mensagens.
    Permite que utilizadores (terapeutas e pacientes) visualizem as suas mensagens.
    """
    serializer_class = MensagemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-data_envio']

    def get_queryset(self):
        """
        Filtra mensagens enviadas ou recebidas pelo utilizador autenticado.
        Superutilizadores podem ver todas as mensagens.
        """
        user = self.request.user
        if user.is_superuser:
            return Mensagem.objects.all()
        return Mensagem.objects.filter(Q(remetente=user) | Q(destinatario=user)).distinct()

    def perform_create(self, serializer):
        print("Iniciando perform_create para Mensagem.")
        try:
            message_instance = serializer.save()
            print(f"Mensagem salva com ID: {message_instance.id}")

            destinatario_notificacao = message_instance.destinatario
            remetente_nome = message_instance.remetente.get_full_name()

            print(f"Destinatário da notificação: {destinatario_notificacao.username} (ID: {destinatario_notificacao.id})")
            print(f"Remetente da mensagem: {remetente_nome}")

            notificacao_instance = Notificacao.objects.create(
                usuario=destinatario_notificacao,
                tipo='mensagem',
                assunto=f'Nova Mensagem de {remetente_nome}',
                conteudo=f'Você recebeu uma nova mensagem de {remetente_nome} com o assunto: "{message_instance.assunto}".',
                link=f'/mensagens/{message_instance.id}',
                lida=False,
                # data_criacao=timezone.now() # REMOVIDO: O modelo Notificacao já define auto_now_add=True ou default=timezone.now
            )
            print(f"Notificação criada com sucesso para o utilizador {destinatario_notificacao.username}. ID da notificação: {notificacao_instance.id}")

        except Exception as e:
            print(f"ERRO ao criar notificação de mensagem: {e}")
            raise

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        if instance.remetente != user and not user.is_superuser:
            raise PermissionDenied("Não tem permissão para atualizar esta mensagem.")
        
        if not user.is_superuser:
            if 'remetente' in serializer.validated_data and serializer.validated_data['remetente'] != instance.remetente:
                raise PermissionDenied("Não é permitido alterar o remetente da mensagem.")
            if 'destinatario' in serializer.validated_data and serializer.validated_data['destinatario'] != instance.destinatario:
                raise PermissionDenied("Não é permitido alterar o destinatário da mensagem.")
        
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.remetente != user and not user.is_superuser:
            raise PermissionDenied("Não tem permissão para deletar esta mensagem.")
        instance.delete()


class RelatorioViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de relatórios.
    Terapeutas gerenciam os seus relatórios.
    Pacientes podem ver relatórios relacionados a eles.
    """
    serializer_class = RelatorioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['data_criacao']
    ordering = ['-data_criacao']
    search_fields = ['titulo', 'conteudo']

    def get_queryset(self):
        """
        Filtra relatórios com base no tipo de utilizador autenticado.
        Superutilizadores podem ver todos os relatórios.
        """
        user = self.request.user
        if user.tipo == 'terapeuta':
            return Relatorio.objects.filter(terapeuta=user)
        elif user.tipo == 'paciente':
            paciente_perfil = Paciente.objects.filter(usuario=user).first()
            if paciente_perfil:
                return Relatorio.objects.filter(paciente=paciente_perfil)
            return Relatorio.objects.none()
        elif user.is_superuser:
            return Relatorio.objects.all()
        return Relatorio.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.tipo != 'terapeuta' and not user.is_superuser:
            raise PermissionDenied("Apenas terapeutas e superutilizadores podem criar relatórios.")

        paciente_obj = serializer.validated_data.get('paciente')

        if not paciente_obj:
            raise ValidationError({"paciente_id": "O ID do paciente é obrigatório para criar um relatório."})

        if paciente_obj.terapeuta != user and not user.is_superuser:
            raise PermissionDenied("Não tem permissão para criar relatórios para este paciente.")

        serializer.save(terapeuta=user, paciente=paciente_obj)

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        if (user.tipo == 'terapeuta' and instance.terapeuta == user) or user.is_superuser:
            serializer.save()
        elif user.tipo == 'paciente':
            raise PermissionDenied("Pacientes não podem atualizar relatórios.")
        else:
            raise PermissionDenied("Não tem permissão para atualizar este relatório.")

    def perform_destroy(self, instance):
        user = self.request.user
        if (user.tipo == 'terapeuta' and instance.terapeuta == user) or user.is_superuser:
            instance.delete()
        elif user.tipo == 'paciente':
            raise PermissionDenied("Pacientes não podem deletar relatórios.")
        else:
            raise PermissionDenied("Não tem permissão para deletar este relatório.")


# --- Views Específicas ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_pacientes_api(request):
    """
    API para terapeutas buscarem os seus pacientes por termo de pesquisa.
    Retorna IDs e nomes completos.
    """
    user = request.user
    if user.tipo != 'terapeuta' and not user.is_superuser:
        return Response({'detail': 'Acesso negado. Apenas terapeutas e administradores podem buscar pacientes.'}, status=status.HTTP_403_FORBIDDEN)

    termo = request.GET.get('search', '')
    
    if user.tipo == 'terapeuta':
        pacientes_queryset = Paciente.objects.filter(terapeuta=user)
    elif user.is_superuser:
        pacientes_queryset = Paciente.objects.all()
    else:
        pacientes_queryset = Paciente.objects.none()

    pacientes = pacientes_queryset.filter(
        nome_completo__icontains=termo
    ).values('pk', 'nome_completo', 'usuario__id', 'usuario__first_name', 'usuario__last_name')[:10]
    
    formatted_pacientes = []
    for p in pacientes:
        formatted_pacientes.append({
            'id': p['pk'],
            'nome_completo': p['nome_completo'],
            'usuario_id': p['usuario__id'],
            'usuario_nome_completo': f"{p['usuario__first_name']} {p['usuario__last_name']}".strip()
        })

    return Response(formatted_pacientes)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meu_terapeuta(request):
    """
    API para pacientes buscarem as informações do seu terapeuta principal.
    Apenas pacientes autenticados podem aceder.
    """
    user = request.user
    if user.tipo != 'paciente' and not user.is_superuser:
        return Response({'detail': 'Acesso negado. Apenas pacientes podem buscar o seu terapeuta.'}, status=status.HTTP_403_FORBIDDEN)

    paciente_perfil = Paciente.objects.filter(usuario=user).first()
    if not paciente_perfil:
        return Response({'detail': 'Perfil de paciente não encontrado para este utilizador.'}, status=status.HTTP_404_NOT_FOUND)

    if not paciente_perfil.terapeuta:
        return Response({'detail': 'Nenhum terapeuta associado a este paciente.'}, status=status.HTTP_404_NOT_FOUND)

    terapeuta_data = UsuarioSerializer(paciente_perfil.terapeuta).data
    return Response(terapeuta_data, status=status.HTTP_200_OK)


class PerfilAPIView(APIView):
    """
    API para visualizar e atualizar o perfil do utilizador autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Views de Painel (APIs) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def painel_terapeuta_api(request):
    """
    API para obter dados do painel do terapeuta.
    Retorna os dados do terapeuta autenticado e uma lista dos seus pacientes.
    Apenas terapeutas e superutilizadores podem aceder.
    """
    user = request.user
    if user.tipo != 'terapeuta' and not user.is_superuser:
        return Response({'detail': 'Acesso negado. Apenas terapeutas e administradores podem aceder a este painel.'}, status=status.HTTP_403_FORBIDDEN)

    terapeuta_data = UsuarioSerializer(user).data
    
    if user.tipo == 'terapeuta':
        total_pacientes = Paciente.objects.filter(terapeuta=user).count()
        pacientes_do_terapeuta_usuario_ids = Paciente.objects.filter(terapeuta=user).values_list('usuario__id', flat=True)
    elif user.is_superuser:
        total_pacientes = Paciente.objects.all().count()
        pacientes_do_terapeuta_usuario_ids = Paciente.objects.all().values_list('usuario__id', flat=True)
    else:
        total_pacientes = 0
        pacientes_do_terapeuta_usuario_ids = []

    hoje = date.today()
    conversas_hoje = Conversa.objects.filter(
        usuario__id__in=pacientes_do_terapeuta_usuario_ids,
        data_conversa__date=hoje
    ).count()

    if user.tipo == 'terapeuta':
        sessoes_pendentes = Sessao.objects.filter(
            terapeuta=user,
            data__date__gte=hoje,
            status='agendada'
        ).count()
    elif user.is_superuser:
        sessoes_pendentes = Sessao.objects.filter(
            data__date__gte=hoje,
            status='agendada'
        ).count()
    else:
        sessoes_pendentes = 0

    alertas_urgentes = 0 # Esta lógica pode ser expandida com base nas suas necessidades

    pacientes_ativos_data = []
    if user.tipo == 'terapeuta':
        pacientes_ativos_queryset = Paciente.objects.filter(terapeuta=user)
    elif user.is_superuser:
        pacientes_ativos_queryset = Paciente.objects.all()
    else:
        pacientes_ativos_queryset = Paciente.objects.none()

    for paciente_perfil in pacientes_ativos_queryset:
        ultima_conversa = Conversa.objects.filter(usuario=paciente_perfil.usuario).order_by('-data_conversa').first()
        if ultima_conversa:
            pacientes_ativos_data.append({
                'id': paciente_perfil.pk,
                'nome': paciente_perfil.nome_completo,
                'ultimaConversa': ultima_conversa.data_conversa.isoformat(),
                'sentimento': ultima_conversa.sentimento
            })
    
    notificacoes_terapeuta = Notificacao.objects.filter(usuario=user).order_by('-data_criacao')[:5]
    alertas_data = NotificacaoSerializer(notificacoes_terapeuta, many=True).data

    return Response({
        'terapeuta': terapeuta_data,
        'totalPacientes': total_pacientes,
        'conversasHoje': conversas_hoje,
        'sessoesPendentes': sessoes_pendentes,
        'alertasUrgentes': alertas_urgentes,
        'pacientesAtivos': pacientes_ativos_data,
        'alertas': alertas_data,
        'detail': 'Dados do painel do terapeuta retornados com sucesso.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def painel_paciente_api(request):
    """
    API para obter dados do painel do paciente.
    Retorna os dados do paciente autenticado e as suas sessões.
    Apenas pacientes e superutilizadores podem aceder.
    """
    user = request.user
    if user.tipo != 'paciente' and not user.is_superuser:
        return Response({'detail': 'Acesso negado. Apenas pacientes e administradores podem aceder a este painel.'}, status=status.HTTP_403_FORBIDDEN)

    paciente_perfil = Paciente.objects.filter(usuario=user).first()
    if not paciente_perfil:
        return Response({'detail': 'Perfil de paciente não encontrado para este utilizador.'}, status=status.HTTP_404_NOT_FOUND)

    paciente_data = PacienteSerializer(paciente_perfil).data
    
    sessoes = Sessao.objects.filter(paciente=paciente_perfil).order_by('-data')
    sessoes_data = SessaoSerializer(sessoes, many=True).data

    # --- LÓGICA PARA O DASHBOARD DO PACIENTE ---
    total_conversas = Conversa.objects.filter(usuario=user).count()
    
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    conversas_essa_semana = Conversa.objects.filter(
        usuario=user,
        data_conversa__date__gte=inicio_semana,
        data_conversa__date__lte=hoje
    ).count()

    ultima_conversa_sentimento = Conversa.objects.filter(usuario=user).order_by('-data_conversa').first()
    sentimento_medio = ultima_conversa_sentimento.sentimento if ultima_conversa_sentimento else 'N/A'
    
    proxima_sessao = Sessao.objects.filter(paciente=paciente_perfil, data__date__gte=hoje).order_by('data').first()
    proxima_sessao_data = proxima_sessao.data.isoformat() if proxima_sessao else None

    return Response({
        'paciente_perfil': paciente_data,
        'totalConversas': total_conversas,
        'conversasEssaSemana': conversas_essa_semana,
        'sentimentoMedio': sentimento_medio,
        'proximaSessao': proxima_sessao_data,
        'sessoes': sessoes_data,
        'detail': 'Dados do painel do paciente retornados com sucesso.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historico_api(request):
    """
    Esta view foi movida para ia/views.py para centralizar a lógica de IA.
    Retorna 404 Not Found ou, se preferir, uma Response informando a mudança.
    """
    return Response({'detail': 'Esta API de histórico está agora na app IA.'}, status=status.HTTP_404_NOT_FOUND)


class NotificacaoViewSet(viewsets.ModelViewSet):
    """
    API para CRUD de notificações.
    Permite que utilizadores (terapeutas e pacientes) visualizem e gerenciem as suas notificações.
    A criação de notificações será geralmente feita internamente pelo sistema.
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['data_criacao', 'lida']
    ordering = ['-data_criacao'] # Notificações mais recentes primeiro por padrão

    def get_queryset(self):
        """
        Filtra notificações para o utilizador autenticado.
        Superusuários podem ver todas as notificações.
        """
        user = self.request.user
        if user.is_superuser:
            return Notificacao.objects.all()
        return Notificacao.objects.filter(usuario=user)

    def perform_create(self, serializer):
        """
        A criação de notificações deve ser restrita e geralmente feita pelo sistema.
        Para permitir a criação via API (apenas para superutilizadores, por exemplo),
        você pode adicionar uma verificação aqui.
        """
        user = self.request.user
        if not user.is_superuser: # Apenas superutilizadores podem criar notificações diretamente via API
            raise PermissionDenied("Apenas administradores podem criar notificações diretamente via API.")
        
        # Se o usuário não for explicitamente fornecido no payload, use o usuário autenticado
        if 'usuario' not in serializer.validated_data and 'usuario_id' not in self.request.data:
            serializer.validated_data['usuario'] = user
        
        # O campo data_criacao é auto_now_add=True ou default=timezone.now no modelo,
        # então não precisamos passá-lo explicitamente aqui.
        serializer.save()

    def perform_update(self, serializer):
        """
        Permite que o utilizador marque as suas próprias notificações como lidas.
        Terapeutas podem marcar notificações dos seus pacientes como lidas.
        Outras alterações devem ser restritas.
        """
        instance = self.get_object()
        user = self.request.user

        # Verifica se o usuário logado é o proprietário da notificação OU um superusuário
        is_owner_or_superuser = (instance.usuario == user) or user.is_superuser

        # Verifica se o usuário logado é um terapeuta e a notificação pertence a um de seus pacientes
        is_therapist_of_patient_notification = False
        if user.tipo == 'terapeuta':
            # Verifica se o usuário da notificação é um paciente do terapeuta logado
            if Paciente.objects.filter(usuario=instance.usuario, terapeuta=user).exists():
                is_therapist_of_patient_notification = True

        # Permissão para atualizar: ou é o dono/superuser, ou é terapeuta do paciente da notificação
        if not (is_owner_or_superuser or is_therapist_of_patient_notification):
            raise PermissionDenied("Você não tem permissão para atualizar esta notificação.")
        
        # Se o usuário não é superusuário nem terapeuta do paciente, permite apenas a mudança do campo 'lida'
        # Se outros campos forem enviados, levanta um erro de permissão.
        if not user.is_superuser and not is_therapist_of_patient_notification:
            if set(serializer.validated_data.keys()) - {'lida'}:
                raise PermissionDenied("Você só pode marcar notificações como lidas.")

        serializer.save()

    def perform_destroy(self, instance):
        """
        Permite que o utilizador delete as suas próprias notificações.
        Superusuários também podem deletar qualquer notificação.
        """
        user = self.request.user
        if instance.usuario != user and not user.is_superuser:
            raise PermissionDenied("Você não tem permissão para deletar esta notificação.")
        instance.delete()
