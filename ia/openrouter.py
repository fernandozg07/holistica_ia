import requests
import os # Importa o módulo os para acessar variáveis de ambiente

# ✅ CORREÇÃO: Lê a chave da API da variável de ambiente
# A variável de ambiente OPENROUTER_API_KEY DEVE estar configurada no Render!
API_KEY = os.getenv('OPENROUTER_API_KEY')

def gerar_resposta_openrouter(mensagem):
    # Verifica se a chave da API está configurada
    if not API_KEY:
        print("⚠️ AVISO: OPENROUTER_API_KEY não configurada! Usando resposta de fallback.")
        return fallback_resposta(mensagem)

    url = "https://openrouter.ai/api/v1/chat/completions"

    # ✅ CORREÇÃO: HTTP-Referer deve ser o domínio real do seu frontend no Netlify
    # Use o domínio HTTPS do Netlify.
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mindcareia.netlify.app",  # ✅ CORREÇÃO AQUI!
        "X-Title": "Assistente Terapeuta",
    }

    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um terapeuta virtual empático que ajuda o usuário "
                    "com saúde mental, respondendo de forma acolhedora, respeitosa e leve. "
                    "Foque em escutar e apoiar emocionalmente, sem julgamentos."
                )
            },
            {"role": "user", "content": mensagem}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        # Verifica se a resposta da API foi bem-sucedida (código 2xx)
        response.raise_for_status() # Levanta um HTTPError para respostas 4xx/5xx

        data = response.json()
        # Verifica se a estrutura da resposta contém o conteúdo esperado
        if "choices" in data and len(data["choices"]) > 0 and "message" in data["choices"][0]:
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"❌ Erro: Resposta inesperada da IA: {data}")
            return fallback_resposta(mensagem)

    except requests.exceptions.RequestException as e:
        # Captura erros de requisição (conexão, timeouts, 4xx/5xx)
        print(f"🌐 Erro de conexão ou HTTP com IA: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta de erro da IA: {e.response.text}")
        return fallback_resposta(mensagem)
    except Exception as e:
        # Captura outros erros inesperados
        print(f"🐛 Erro inesperado ao processar resposta da IA: {str(e)}")
        return fallback_resposta(mensagem)


def fallback_resposta(mensagem):
    mensagem = mensagem.lower() if isinstance(mensagem, str) else ""

    if "oi" in mensagem or "olá" in mensagem:
        return "Olá! Como posso te ajudar hoje?"
    elif "respiração" in mensagem:
        return "Tente: inspire 4s, segure 4s, expire 4s. Isso ajuda a acalmar a mente."
    elif "ansioso" in mensagem or "preocupado" in mensagem:
        return "A ansiedade pode ser difícil. Você quer me contar o que está sentindo?"
    else:
        return "Desculpe, não consegui entender direito. Pode reformular, por favor?"
