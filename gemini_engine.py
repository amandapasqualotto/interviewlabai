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

# Tempo máximo (segundos) de cada chamada à API. Evita o "pensando para sempre".
TIMEOUT_SEGUNDOS = 30

# Guarda o último modelo que funcionou para não testar os outros toda vez.
_MODELO_OK = None


def get_client(api_key: str = None):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave GEMINI_API_KEY não encontrada.")
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=TIMEOUT_SEGUNDOS * 1000),  # milissegundos
    )


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


def _ordem_modelos():
    ordem = []
    if _MODELO_OK:
        ordem.append(_MODELO_OK)
    override = os.getenv("GEMINI_MODEL")
    if override:
        ordem.append(override)
    ordem.extend(MODELOS_PREFERIDOS)
    vistos, final = set(), []
    for m in ordem:
        if m not in vistos:
            vistos.add(m)
            final.append(m)
    return final


def _config_rapida(config, model_name):
    """Reduz o 'pensamento' do modelo para responder em segundos."""
    try:
        if model_name.startswith("gemini-2.5"):
            tc = types.ThinkingConfig(thinking_budget=0)
        else:
            tc = types.ThinkingConfig(thinking_level="low")
    except Exception:
        return config
    base = config if config is not None else types.GenerateContentConfig()
    try:
        return base.model_copy(update={"thinking_config": tc})
    except Exception:
        return config


def _gerar(client, contents, config=None):
    """Tenta gerar conteúdo percorrendo modelos. Retorna (texto, erros)."""
    global _MODELO_OK
    erros = []
    tentados = set()

    def tentar(model_name):
        global _MODELO_OK
        if model_name in tentados:
            return None
        tentados.add(model_name)
        for cfg in (_config_rapida(config, model_name), config):
            try:
                kwargs = {"model": model_name, "contents": contents}
                if cfg is not None:
                    kwargs["config"] = cfg
                resp = client.models.generate_content(**kwargs)
                if resp and resp.text:
                    _MODELO_OK = model_name
                    return resp.text
                erros.append(f"{model_name}: resposta vazia")
                return None
            except Exception as e:
                msg = str(e)
                erros.append(f"{model_name}: {msg}")
                # Só repete sem a config de 'thinking' se o erro for sobre isso
                if "thinking" not in msg.lower():
                    return None
        return None

    for nome in _ordem_modelos():
        texto = tentar(nome)
        if texto:
            return texto, erros

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
    3. Seja direto e conciso. Retorne um parecer estruturado contendo:
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


def _montar_chat(historico_mensagens, contexto_vaga, pergunta, parecer_anterior):
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
    2. Use busca na web só se for realmente necessário (novidades da empresa, tendências).
    3. Dê feedbacks elegantes, práticos e objetivos e construa a melhor narrativa profissional possível com o candidato.
    """
    contents = []
    for msg in historico_mensagens:
        role = "user" if msg.get("role") == "user" else "model"
        texto = msg.get("content", "")
        if str(texto).strip():
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=str(texto))]))
    return system_instruction, contents


def stream_chat_lapidacao(client, historico_mensagens: list, contexto_vaga: dict,
                          pergunta: str, parecer_anterior: str):
    """
    Gerador que devolve o texto aos poucos (streaming), então a resposta
    começa a aparecer em poucos segundos. Use com st.write_stream().
    """
    global _MODELO_OK
    system_instruction, contents = _montar_chat(historico_mensagens, contexto_vaga, pergunta, parecer_anterior)

    config_busca = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    config_simples = types.GenerateContentConfig(system_instruction=system_instruction)

    erros = []
    tentados = set()
    modelos = _ordem_modelos()

    # Primeiro tenta SEM busca (mais rápido); a busca fica como segunda opção
    for usar_busca in (False, True):
        base = config_busca if usar_busca else config_simples
        for nome in modelos:
            chave = (nome, usar_busca)
            if chave in tentados:
                continue
            tentados.add(chave)
            for cfg in (_config_rapida(base, nome), base):
                emitiu = False
                try:
                    for chunk in client.models.generate_content_stream(
                        model=nome, contents=contents, config=cfg
                    ):
                        if chunk and chunk.text:
                            emitiu = True
                            yield chunk.text
                    if emitiu:
                        _MODELO_OK = nome
                        return
                    erros.append(f"{nome}: resposta vazia")
                    break
                except Exception as e:
                    if emitiu:
                        # Já mostrou parte do texto; encerra sem repetir
                        return
                    msg = str(e)
                    erros.append(f"{nome}: {msg}")
                    if "thinking" not in msg.lower():
                        break

    yield "Não foi possível gerar a resposta do chat no momento. Detalhes:\n\n" + "\n\n".join(erros)


def simular_chat_lapidacao_com_busca(client, historico_mensagens: list, contexto_vaga: dict,
                                     pergunta: str, parecer_anterior: str):
    """Versão sem streaming (mantida por compatibilidade)."""
    return "".join(stream_chat_lapidacao(client, historico_mensagens, contexto_vaga, pergunta, parecer_anterior))
