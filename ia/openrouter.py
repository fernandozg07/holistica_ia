import requests

# ⛔ ATENÇÃO: Chave colocada direto no código (somente se você quiser isso mesmo)
API_KEY = "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"

def gerar_resposta_openrouter(mensagem):
    if not API_KEY:
        print("⚠️ AVISO: OPENROUTER_API_KEY não configurada!")
        return fallback_resposta(mensagem)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",  # pode ajustar com o domínio real
        "X-Title": "Assistente Terapeuta",
    }

    payload = {
        "model": "openai/gpt-4o",  # ✅ modelo correto da OpenRouter
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
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"❌ Erro da IA ({response.status_code}): {response.text}")
            return fallback_resposta(mensagem)
    except Exception as e:
        print(f"🌐 Erro de conexão com IA: {str(e)}")
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
