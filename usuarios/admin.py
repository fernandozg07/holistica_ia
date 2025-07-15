from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Paciente

class UsuarioAdmin(UserAdmin):
    # Campos a serem exibidos na lista do painel de administração para Usuario
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'is_staff')
    # Campos para filtragem na lista
    list_filter = ('tipo', 'is_staff')
    # Campos a serem exibidos no formulário de edição/criação de Usuario
    # Adiciona campos personalizados do modelo Usuario aos fieldsets padrão do UserAdmin
    fieldsets = UserAdmin.fieldsets + (
        ('Dados Adicionais', {'fields': ('tipo', 'telefone', 'data_nascimento', 'foto_perfil', 'especialidade', 'crp')}),
    )

class PacienteAdmin(admin.ModelAdmin):
    # Método customizado para obter o email do usuário associado ao Paciente
    def get_usuario_email(self, obj):
        # Tenta retornar o email do Usuario associado, se existir
        return obj.usuario.email if obj.usuario else None
    get_usuario_email.short_description = 'Email do Usuário' # Nome da coluna no admin

    # Campos a serem exibidos na lista do painel de administração para Paciente
    # 'get_usuario_email' é o método customizado que criamos
    # 'nome_completo' é um campo direto do modelo Paciente
    # 'terapeuta' é a ForeignKey para o Usuario Terapeuta
    # 'telefone' é um campo direto do modelo Paciente
    # 'idade' é uma propriedade calculada no modelo Paciente
    list_display = ('nome_completo', 'terapeuta', 'get_usuario_email', 'telefone', 'idade')
    # Campos para filtragem na lista
    list_filter = ('terapeuta',)
    # Campos para busca. Note que 'usuario__email' é usado para buscar pelo email do Usuario associado.
    search_fields = ('nome_completo', 'usuario__email', 'telefone')
    # Campos que serão exibidos como campos de seleção de ID bruto (melhor para muitos objetos)
    raw_id_fields = ('terapeuta', 'usuario')

# Registra os modelos no painel de administração com suas classes Admin personalizadas
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Paciente, PacienteAdmin)
