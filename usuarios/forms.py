from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Paciente, Sessao, Mensagem
from datetime import timedelta

Usuario = get_user_model()

class TerapeutaSignupForm(UserCreationForm):
    crp = forms.CharField(
        label='CRP',
        max_length=20,
        required=True,
        help_text='Número de registro no conselho de psicologia'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'cpf', 'crp',
            'data_nascimento', 'telefone', 'especialidade'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'terapeuta'
        if commit:
            user.save()
        return user

class PacienteSignupForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'cpf', 'data_nascimento',
            'telefone'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'paciente'
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': True})

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nome_completo', 'email', 'telefone', 'data_nascimento',
            'endereco', 'cep', 'historico_medico', 'alergias',
            'medicamentos', 'emergencia_nome', 'emergencia_telefone'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'historico_medico': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'alergias': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control'
            }),
            'medicamentos': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control'
            }),
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'email', 'telefone',
            'data_nascimento', 'endereco', 'cep', 'foto_perfil',
            'especialidade', 'crp'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

class PasswordChangeCustomForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class SessaoForm(forms.ModelForm):
    DURACAO_CHOICES = [
        (30, '30 minutos'),
        (50, '50 minutos'),
        (60, '1 hora'),
    ]

    duracao = forms.ChoiceField(
        choices=DURACAO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Duração (minutos)"
    )

    class Meta:
        model = Sessao
        fields = ['paciente', 'data', 'duracao', 'observacoes']
        widgets = {
            'data': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # 'duracao' não precisa widget aqui pois sobrescrevemos acima
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user.tipo == 'terapeuta':
            self.fields['paciente'].queryset = user.meus_pacientes.all()
            self.fields['paciente'].widget.attrs.update({'class': 'form-control'})
        else:
            # Pacientes só podem criar sessões para si mesmos
            self.fields['paciente'].queryset = Usuario.objects.filter(pk=user.pk)
            self.fields['paciente'].initial = user
            self.fields['paciente'].widget = forms.HiddenInput()

class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['destinatario', 'assunto', 'conteudo']
        widgets = {
            'destinatario': forms.Select(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'conteudo': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control'
            }),
        }

def __init__(self, user, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['paciente'].queryset = user.meus_pacientes.all()
