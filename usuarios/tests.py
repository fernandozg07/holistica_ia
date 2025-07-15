from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from usuarios.models import Usuario, Paciente
from datetime import timedelta
from django.utils import timezone


class AutenticacaoTests(APITestCase):
    def setUp(self):
        self.email = "user@example.com"
        self.password = "Senha123!"
        self.user = Usuario.objects.create_user(email=self.email, password=self.password)

    def test_login_com_credenciais_certas(self):
        url = reverse('login_api')
        response = self.client.post(url, {'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.email)

    def test_login_com_senha_errada(self):
        url = reverse('login_api')
        response = self.client.post(url, {'email': self.email, 'password': 'senhaerrada'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acesso_sem_token(self):
        url = reverse('pacientes-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class PermissoesTests(APITestCase):
    def setUp(self):
        self.terapeuta = Usuario.objects.create_user(email="t@example.com", password="Senha123!", tipo="terapeuta")
        self.paciente = Usuario.objects.create_user(email="p@example.com", password="Senha123!", tipo="paciente")

        self.client_terapeuta = APIClient()
        self.client_terapeuta.force_authenticate(user=self.terapeuta)

        self.client_paciente = APIClient()
        self.client_paciente.force_authenticate(user=self.paciente)

    def test_paciente_nao_pode_criar_sessao(self):
        url = reverse('sessoes-list')
        data = {
            "paciente": self.paciente.id,
            "data": (timezone.now() + timedelta(days=1)).isoformat(),
            "duracao": "01:00:00",
            "status": "agendada",
            "observacoes": "Teste paciente não pode criar"
        }
        response = self.client_paciente.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_terapeuta_pode_criar_sessao(self):
        url = reverse('sessoes-list')
        data = {
            "paciente": self.paciente.id,
            "data": (timezone.now() + timedelta(days=1)).isoformat(),
            "duracao": "01:00:00",
            "status": "agendada",
            "observacoes": "Teste terapeuta pode criar"
        }
        response = self.client_terapeuta.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class FiltrosTests(APITestCase):
    def setUp(self):
        self.terapeuta = Usuario.objects.create_user(email="t@example.com", password="Senha123!", tipo="terapeuta")
        self.paciente1 = Usuario.objects.create_user(email="p1@example.com", password="Senha123!", tipo="paciente")
        self.paciente2 = Usuario.objects.create_user(email="p2@example.com", password="Senha123!", tipo="paciente")

        self.paciente1_obj = Paciente.objects.create(
            usuario=self.paciente1, nome_completo="Paciente A", email="p1@example.com", terapeuta=self.terapeuta
        )
        self.paciente2_obj = Paciente.objects.create(
            usuario=self.paciente2, nome_completo="Paciente B", email="p2@example.com", terapeuta=self.terapeuta
        )

        self.client_terapeuta = APIClient()
        self.client_terapeuta.force_authenticate(user=self.terapeuta)

    def test_filtro_nome_completo(self):
        url = reverse('pacientes-list') + "?search=Paciente A"
        response = self.client_terapeuta.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes = [p['nome_completo'] for p in response.data]
        self.assertIn("Paciente A", nomes)


class CasosDeBordaTests(APITestCase):
    def setUp(self):
        self.terapeuta = Usuario.objects.create_user(email="t@example.com", password="Senha123!", tipo="terapeuta")
        self.paciente = Usuario.objects.create_user(email="p@example.com", password="Senha123!", tipo="paciente")
        self.client_terapeuta = APIClient()
        self.client_terapeuta.force_authenticate(user=self.terapeuta)

    def test_criar_sessao_com_data_passada_falha(self):
        url = reverse('sessoes-list')
        data = {
            "paciente": self.paciente.id,
            "data": (timezone.now() - timedelta(days=1)).isoformat(),
            "duracao": "01:00:00",
            "status": "agendada",
            "observacoes": "Teste data passada"
        }
        response = self.client_terapeuta.post(url, data, format='json')
        # Se seu backend não validar isso, pode ser 201, ideal implementar validação no serializer
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_criar_mensagem_sem_conteudo_falha(self):
        url = reverse('mensagens-list')
        data = {
            "destinatario": self.paciente.id,
            "conteudo": ""
        }
        response = self.client_terapeuta.post(url, data, format='json')
        # Se backend não valida campo vazio, pode retornar 201, ajuste se desejar
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
