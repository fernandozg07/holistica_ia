from django.test import TestCase
from .views import processar_mensagem

class SentimentoTestCase(TestCase):
    def test_sentimento_positivo(self):
        mensagem = "Estou muito feliz hoje!"  # Mensagem com sentimento positivo
        resposta_ia, sentimento = processar_mensagem(mensagem)
        self.assertEqual(sentimento, "Positivo")

    def test_sentimento_negativo(self):
        mensagem = "Eu estou tão triste."  # Mensagem com sentimento negativo
        resposta_ia, sentimento = processar_mensagem(mensagem)
        self.assertEqual(sentimento, "Negativo")

    def test_sentimento_neutro(self):
        mensagem = "Eu gosto de caminhar no parque."  # Mensagem neutra
        resposta_ia, sentimento = processar_mensagem(mensagem)
        self.assertEqual(sentimento, "Neutro")
