# gemini_engine.py
import os
from google import genai
from google.genai import types
from curadoria import INSIGHTS_GERAIS

def get_client(api_key: str = None):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave GEMINI_API_KEY não encontrada.")
    return genai.Client(api_key=key)

def avaliar_resposta_completa(client, contexto: dict, pergunta: str, dados_pergunta: dict, resposta_texto: str = None, audio_bytes: bytes = None, audio_mime: str = "audio/wav"):
    """
    Avalia a resposta do candidato (áudio ou texto) utilizando
    a estrutura nativa de partes da biblioteca google-genai.
    """
    if not contexto:
        contexto = {}
    if not dados_pergunta:
        dados_pergunta = {}

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

    # Se houver áudio, adiciona os bytes no formato exigido
    if audio_bytes and isinstance(audio_bytes, bytes) and len(audio_bytes) > 0:
        parts.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))

    # Adiciona a instrução de texto
    parts.append(types.Part.from_text(text=prompt_texto))

    # Tenta primeiro com gemini-2.0-flash e faz fallback para gemini-1.5-flash
    erros = []
    for model_name in ['gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=parts
            )
            if response and response.text:
                return response.text
        except Exception as e:
            erros.append(f"{model_name}: {str(e)}")
            continue

    return f"Erro ao comunicar com a API do Gemini. Detalhes: {' | '.join(erros)}"

def simular_chat_lapidacao_com_busca(client, historico_mensagens: list, contexto_vaga: dict, pergunta: str, parecer_anterior: str):
    """
    Chat interativo que utiliza busca na web (Google Search Grounding) para complementar
    as informações da empresa e vaga.
    """
    if not contexto_vaga:
        contexto_vaga = {}

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
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=str(texto))]
                )
            )

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[{"google_search": {}}]
            )
        )
        return response.text
    except Exception as e:
        return f"Erro no chat de lapidação: {str(e)}"
