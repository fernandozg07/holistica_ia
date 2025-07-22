from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from datetime import date, timedelta # ✅ Importado timedelta aqui
from django.conf import settings
from django.utils import timezone

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_CHOICES = [
        ('paciente', 'Paciente'),
        ('terapeuta', 'Terapeuta'),
        ('admin', 'Administrador'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    first_name = models.CharField('Nome', max_length=150, blank=True)
    last_name = models.CharField('Sobrenome', max_length=150, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='paciente')

    telefone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Número inválido")]
    )
    data_nascimento = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, blank=True, default='')
    endereco = models.CharField(max_length=255, blank=True)
    cep = models.CharField(max_length=9, blank=True, default='')
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)

    especialidade = models.CharField(max_length=255, blank=True, default='')
    crp = models.CharField('CRP', max_length=20, blank=True, default='')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.get_tipo_display()})"

    def get_full_name(self):
        """Retorna o nome completo do utilizador."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Retorna o primeiro nome do utilizador."""
        return self.first_name

    @property
    def idade(self):
        if self.data_nascimento:
            today = date.today()
            born = self.data_nascimento
            idade = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            return idade
        return None


class Paciente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True, # Mantemos primary_key=True aqui
        related_name='perfil_paciente', 
        limit_choices_to={'tipo': 'paciente'}
    )
    # ✅ NOTA: Os campos 'telefone', 'data_nascimento', 'endereco', 'cep'
    # já existem no modelo Usuario. Se a intenção é que esses dados sejam
    # sempre os mesmos para o Usuario e o Paciente associado, eles são
    # redundantes aqui. Você pode removê-los e acessá-los via 'paciente.usuario.telefone'
    # no serializer ou template. Se eles podem ter valores diferentes, mantenha-os.
    nome_completo = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True, default='')
    data_nascimento = models.DateField(null=True, blank=True)
    endereco = models.CharField(max_length=255, blank=True, default='')
    cep = models.CharField(max_length=9, blank=True, default='')

    historico_medico = models.TextField(blank=True, default='')
    alergias = models.TextField(blank=True, default='')
    medicamentos = models.TextField(blank=True, default='')
    emergencia_nome = models.CharField(max_length=255, blank=True, default='')
    emergencia_telefone = models.CharField(max_length=20, blank=True, default='')

    terapeuta = models.ForeignKey(
        Usuario, # Terapeuta é um Usuario com tipo='terapeuta'
        limit_choices_to={'tipo': 'terapeuta'},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pacientes_associados_terapeuta'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    @property
    def idade(self):
        # Esta propriedade agora verifica o data_nascimento do próprio Paciente primeiro
        # e, se não, usa o do Usuario associado.
        if self.data_nascimento:
            today = date.today()
            born = self.data_nascimento
            idade = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            return idade
        elif self.usuario and self.usuario.data_nascimento:
            today = date.today()
            born = self.usuario.data_nascimento
            idade = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            return idade
        return None

    def __str__(self):
        return self.nome_completo or (self.usuario.get_full_name() if self.usuario else "Paciente sem nome")


class Sessao(models.Model):
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    terapeuta = models.ForeignKey(
        Usuario, # Terapeuta ainda é o modelo Usuario com tipo='terapeuta'
        limit_choices_to={'tipo': 'terapeuta'},
        on_delete=models.CASCADE,
        related_name='sessoes_como_terapeuta'
    )
    paciente = models.ForeignKey(
        Paciente, # Agora referencia o modelo Paciente, não Usuario
        on_delete=models.CASCADE,
        related_name='sessoes_do_paciente'
    )

    data = models.DateTimeField()
    duracao = models.DurationField(help_text="Duração da sessão")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='agendada')
    observacoes = models.TextField(blank=True, default='')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sessão"
        verbose_name_plural = "Sessões"
        ordering = ['data']

    @property
    def duracao_timedelta(self):
        # ✅ timedelta já importado no topo do arquivo
        return timedelta(minutes=self.duracao)

    def __str__(self):
        paciente_nome = self.paciente.nome_completo if self.paciente else "Paciente Desconhecido"
        terapeuta_nome = self.terapeuta.get_full_name() if self.terapeuta else "Terapeuta Desconhecido"
        return f"Sessão {paciente_nome} com {terapeuta_nome} em {self.data.strftime('%d/%m/%Y %H:%M')}"


class Mensagem(models.Model):
    remetente = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='mensagens_enviadas'
    )
    destinatario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='mensagens_recebidas'
    )
    assunto = models.CharField(max_length=255, blank=True)
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['-data_envio']

    def __str__(self):
        return f"De: {self.remetente.email} para: {self.destinatario.email} - Assunto: {self.assunto[:50]}"

# Continuar com Relatorio aqui se ele estiver no mesmo arquivo
class Relatorio(models.Model):
    terapeuta = models.ForeignKey(
        Usuario,
        limit_choices_to={'tipo': 'terapeuta'},
        on_delete=models.CASCADE,
        related_name='relatorios_criados'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='relatorios_recebidos'
    )
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Relatório de {self.terapeuta.get_full_name()} para {self.paciente.nome_completo} - {self.titulo}"
    

class Notificacao(models.Model):
    """
    Modelo para armazenar notificações do sistema.
    Pode ser associado a um utilizador específico.
    """
    TIPO_CHOICES = [
        ('geral', 'Geral'),
        ('sessao', 'Sessão'),
        ('mensagem', 'Mensagem'),
        ('alerta', 'Alerta'),
        ('sistema', 'Sistema'),
    ]

    # O utilizador que receberá a notificação
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        verbose_name='Utilizador'
    )
    
    # Tipo da notificação (para categorização e ícones no frontend)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='geral',
        verbose_name='Tipo'
    )

    # Assunto ou título breve da notificação
    assunto = models.CharField(
        max_length=255,
        verbose_name='Assunto'
    )
    
    # Conteúdo completo da notificação
    conteudo = models.TextField(
        verbose_name='Conteúdo'
    )
    
    # URL opcional para onde a notificação deve levar o utilizador
    link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Link'
    )
    
    # Se a notificação já foi lida pelo utilizador
    lida = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    
    # Data e hora em que a notificação foi criada
    data_criacao = models.DateTimeField(
        default=timezone.now,
        verbose_name='Data de Criação'
    )

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_criacao'] # Notificações mais recentes primeiro

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.assunto} para {self.usuario.email}"
