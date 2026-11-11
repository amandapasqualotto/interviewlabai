# gemini_engine.py
import json
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
    Avalia a resposta do candidato (seja via áudio ou texto) considerando
    a técnica recomendada e expectativas específicas de curadoria.
    """
    prompt = f"""
    {INSIGHTS_GERAIS}

    CONTEXTO DA VAGA E EMPRESA:
    Empresa: {contexto.get('empresa')}
    Cargo: {contexto.get('cargo')}
    Descrição da Vaga: {contexto.get('descricao')}
    Sobre a Empresa: {contexto.get('sobre_empresa')}
    Perfil LinkedIn do Candidato: {contexto.get('linkedin', 'Não informado')}
    Texto do Currículo: {contexto.get('curriculo_texto', 'Não informado')}

    PERGUNTA DA ENTREVISTA SELECIONADA:
    "{pergunta}"

    TÉCNICA ESPERADA PARA ESTA PERGUNTA: {dados_pergunta.get('tecnica')}
    EXPECTATIVA DO RECRUTADOR: {dados_pergunta.get('expectativa')}

    INSTRUÇÕES DE AVALIAÇÃO:
    1. Se houver áudio, transcreva-o primeiro na íntegra.
    2. Avalie o alinhamento da resposta do candidato com os requisitos da vaga, o perfil do candidato (se fornecido) e a expectativa técnica da pergunta.
    3. Retorne um feedback completo estruturado com:
       - Transcrição (se aplicável)
       - Pontuação de Alinhamento (0 a 100%)
       - Análise Técnica da Estrutura da Resposta
       - Pontos Fortes
       - Lacunas e Oportunidades de Melhoria
       - Reescrita Ideal Sugerida (de alto impacto)
    """

    contents = []
    if audio_bytes:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))
    
    if resposta_texto:
        contents.append(f"\nRESPOSTA ESCRITA DO CANDIDATO:\n{resposta_texto}")

    contents.append(prompt)

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    return response.text

def simular_chat_lapidacao_com_busca(client, historico_mensagens: list, contexto_vaga: dict, pergunta: str, parecer_anterior: str):
    """
    Chat interativo que utiliza a busca na web (Google Search Grounding) para complementar
    as informações da empresa, vaga e melhores práticas do mercado.
    """
    system_instruction = f"""
    Você é um mentor sênior de carreiras e recrutador de elite.
    Seu objetivo é ajudar o candidato a lapidar a resposta para a pergunta: "{pergunta}".

    DADOS DO CANDIDATO E DA VAGA:
    - Empresa: {contexto_vaga.get('empresa')}
    - Cargo: {contexto_vaga.get('cargo')}
    - Descrição: {contexto_vaga.get('descricao')}
    - Sobre a Empresa: {contexto_vaga.get('sobre_empresa')}
    - LinkedIn: {contexto_vaga.get('linkedin')}
    - Resumo do Currículo: {contexto_vaga.get('curriculo_texto')}
    - Último parecer de avaliação: {parecer_anterior}

    DIRETRIZES:
    1. As informações fornecidas acima são suas referências principais.
    2. Você DEVE realizar buscas na web se precisar validar novidades sobre a empresa, tendências da área, requisitos de mercado ou cultura organizacional.
    3. Dê feedbacks elegantes, práticos e construa a melhor narrativa profissional possível com o candidato.
    """

    contents = []
    for msg in historico_mensagens:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Ativa busca integrada no Google (Google Search Grounding)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[{"google_search": {}}]
        )
    )
    return response.text
