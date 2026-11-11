# gemini_engine.py
import os
from google import genai
from google.genai import types
from curadoria import INSIGHTS_GERAIS

# Modelos tentados em ordem. Pode sobrescrever com a variável/secret GEMINI_MODEL.
MODELOS_PREFERIDOS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
]


def get_client(api_key: str = None):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave GEMINI_API_KEY não encontrada.")
    return genai.Client(api_key=key)


def _descobrir_modelos(client):
    """Consulta a API e devolve modelos 'flash' que suportam generateContent."""
    try:
        nomes = []
        for m in client.models.list():
            acoes = getattr(m, "supported_actions", None) or []
            nome = (getattr(m, "name", "") or "").replace("models/", "")
            if "generateContent" in acoes and "flash" in nome:
                if any(x in nome for x in ("image", "tts", "live", "audio", "embedding")):
                    continue
                nomes.append(nome)
        return sorted(set(nomes), reverse=True)
    except Exception:
        return []


def _lista_modelos(client):
    ordem = []
    override = os.getenv("GEMINI_MODEL")
    if override:
        ordem.append(override)
    ordem.extend(MODELOS_PREFERIDOS)
    # Descobre modelos disponíveis só se necessário (evita chamada extra a cada vez)
    return ordem


def _gerar(client, contents, config=None):
    """Tenta gerar conteúdo percorrendo modelos. Retorna (texto, erros)."""
    erros = []
    tentados = set()

    def tentar(model_name):
        if model_name in tentados:
            return None
        tentados.add(model_name)
        try:
            kwargs = {"model": model_name, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            resp = client.models.generate_content(**kwargs)
            if resp and resp.text:
                return resp.text
            erros.append(f"{model_name}: resposta vazia")
        except Exception as e:
            erros.append(f"{model_name}: {e}")
        return None

    for nome in _lista_modelos(client):
        texto = tentar(nome)
        if texto:
            return texto, erros

    # Último recurso: pergunta à API quais modelos existem
    for nome in _descobrir_modelos(client):
        texto = tentar(nome)
        if texto:
            return texto, erros

    return None, erros


def avaliar_resposta_completa(client, contexto: dict, pergunta: str, dados_pergunta: dict,
                              resposta_texto: str = None, audio_bytes: bytes = None,
                              audio_mime: str = "audio/wav"):
    """Avalia a resposta do candidato (áudio ou texto)."""
    contexto = contexto or {}
    dados_pergunta = dados_pergunta or {}

    prompt_texto = f"""
    {INSIGHTS_GERAIS}

    CONTEXTO DA VAGA E EMPRESA:
    Empresa: {contexto.get('empresa', 'Não informada')}
    Cargo: {contexto.get('cargo', 'Não informado')}
    Descrição da Vaga: {contexto.get('descricao', 'Não informada')}
    Sobre a Empresa: {contexto.get('sobre_empresa', 'Não informada')}
    Perfil LinkedIn do Candidato: {contexto.get('linkedin', 'Não informado')}
    Texto do Currículo: {contexto.get('curriculo_texto', 'Não informado')}

    PERGUNTA DA ENTREVISTA SELECIONADA:
    "{pergunta}"

    TÉCNICA ESPERADA PARA ESTA PERGUNTA: {dados_pergunta.get('tecnica', 'STAR')}
    EXPECTATIVA DO RECRUTADOR: {dados_pergunta.get('expectativa', 'Avaliação geral')}

    INSTRUÇÕES DE AVALIAÇÃO:
    1. Se houver áudio anexado, transcreva-o primeiro na íntegra.
    2. Avalie o alinhamento da resposta do candidato com os requisitos da vaga e a expectativa técnica da pergunta.
    3. Retorne um parecer claro e estruturado contendo:
       - Transcrição (se aplicável)
       - Diagnóstico Geral e % de Alinhamento (0 a 100%)
       - Análise Técnica da Estrutura da Resposta
       - Pontos Fortes
       - Lacunas e Oportunidades de Melhoria
       - Reescrita Sugerida de Alto Impacto
    """

    if resposta_texto and str(resposta_texto).strip():
        prompt_texto += f"\n\nRESPOSTA ESCRITA DO CANDIDATO:\n{str(resposta_texto).strip()}"

    parts = []
    if audio_bytes and isinstance(audio_bytes, bytes) and len(audio_bytes) > 0:
        parts.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))
    parts.append(types.Part.from_text(text=prompt_texto))

    texto, erros = _gerar(client, parts)
    if texto:
        return texto

    return "Não foi possível obter resposta da API do Gemini. Detalhes do erro:\n\n" + "\n\n".join(erros)


def simular_chat_lapidacao_com_busca(client, historico_mensagens: list, contexto_vaga: dict,
                                     pergunta: str, parecer_anterior: str):
    """Chat de lapidação, com Google Search quando disponível."""
    contexto_vaga = contexto_vaga or {}

    system_instruction = f"""
    Você é um mentor sênior de carreiras e recrutador de elite.
    Seu objetivo é ajudar o candidato a lapidar a resposta para a pergunta: "{pergunta}".

    DADOS DO CANDIDATO E DA VAGA:
    - Empresa: {contexto_vaga.get('empresa', 'Não informada')}
    - Cargo: {contexto_vaga.get('cargo', 'Não informado')}
    - Descrição: {contexto_vaga.get('descricao', 'Não informada')}
    - Sobre a Empresa: {contexto_vaga.get('sobre_empresa', 'Não informada')}
    - LinkedIn: {contexto_vaga.get('linkedin', 'Não informado')}
    - Resumo do Currículo: {contexto_vaga.get('curriculo_texto', 'Não informado')}
    - Último parecer de avaliação: {parecer_anterior}

    DIRETRIZES:
    1. As informações fornecidas acima são suas referências principais.
    2. Você pode realizar buscas na web se precisar validar novidades sobre a empresa, tendências ou requisitos.
    3. Dê feedbacks elegantes, práticos e construa a melhor narrativa profissional possível com o candidato.
    """

    contents = []
    for msg in historico_mensagens:
        role = "user" if msg.get("role") == "user" else "model"
        texto = msg.get("content", "")
        if str(texto).strip():
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=str(texto))]))

    # 1ª tentativa: com busca na web
    config_busca = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    texto, erros_busca = _gerar(client, contents, config_busca)
    if texto:
        return texto

    # 2ª tentativa: sem ferramenta de busca
    config_simples = types.GenerateContentConfig(system_instruction=system_instruction)
    texto, erros_simples = _gerar(client, contents, config_simples)
    if texto:
        return texto

    detalhes = "\n\n".join(erros_simples or erros_busca)
    return "Não foi possível gerar a resposta do chat no momento. Detalhes:\n\n" + detalhes
