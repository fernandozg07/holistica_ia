from django.db import models
from usuarios.models import Usuario # Importar o modelo Usuario do app usuarios

class Conversa(models.Model):
    # Foreign Key para o modelo Usuario, com um related_name único
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='conversas_ia' # Nome único para o acesso reverso
    )
    mensagem_usuario = models.TextField()
    resposta_ia = models.TextField()
    sentimento = models.CharField(max_length=20)
    categoria_sentimento = models.CharField(max_length=50)
    intensidade_sentimento = models.CharField(max_length=20)
    data_conversa = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversa IA"
        verbose_name_plural = "Conversas IA"
        ordering = ['-data_conversa']

    def __str__(self):
        return f"Conversa de {self.usuario.email} em {self.data_conversa.strftime('%d/%m/%Y %H:%M')}"

# Você pode ter outros modelos aqui no seu app 'ia'
# class OutroModeloIA(models.Model):
#     pass
