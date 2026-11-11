# gemini_engine.py
import json
import os
from google import genai
from google.genai import types
from curadoria import INSIGHTS_GERAIS

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    return genai.Client(api_key=api_key)

def analisar_resposta_audio(audio_bytes: bytes, pergunta: str, dados_pergunta: dict, descritivo_vaga: str) -> dict:
    client = get_client()
    
    prompt = f"""
    {INSIGHTS_GERAIS}

    CONTEXTO DA VAGA E EMPRESA:
    {descritivo_vaga}

    PERGUNTA DA ENTREVISTA:
    "{pergunta}"

    TÉCNICA ESPERADA: {dados_pergunta['tecnica']}
    EXPECTATIVA DO RECRUTADOR: {dados_pergunta['expectativa']}

    INSTRUÇÕES:
    1. Transcreva com precisão o áudio enviado pelo candidato.
    2. Avalie a resposta considerando:
       - % de Match (0 a 100%) baseado no alinhamento com a vaga, palavras-chave e uso da técnica esperada.
       - Uso da técnica recomendada (Ex: STAR ou Storytelling).
       - Presença de palavras-chave do descritivo da vaga e fit cultural.
       - Pontos Fortes e Pontos de Melhoria.
    3. Forneça o que era esperado como resposta ideal e sugestões práticas de ajuste.

    Responda EXCLUSIVAMENTE em formato JSON com a seguinte estrutura:
    {{
      "transcricao": "Texto falado no áudio",
      "porcentagem_match": 75,
      "analise_tecnica": "Análise sobre o uso da técnica...",
      "palavras_chave_identificadas": ["termo1", "termo2"],
      "pontos_fortes": ["Ponto 1", "Ponto 2"],
      "pontos_melhoria": ["Melhoria 1", "Melhoria 2"],
      "resposta_ideal_sugerida": "Exemplo de como seria uma resposta de alto impacto"
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/wav'
            ),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

def lapidar_resposta_chat(historico_mensagens: list, contexto_vaga: str, pergunta: str, dados_pergunta: dict) -> str:
    client = get_client()
    
    system_instruction = f"""
    Você é um Coach de Entrevistas de Emprego especialista em processos de Estágio e Trainee.
    Seu objetivo é ajudar o candidato a lapidar por escrito a resposta para a pergunta: "{pergunta}".
    
    Técnica a ser aplicada: {dados_pergunta['tecnica']}
    Expectativa do recrutador: {dados_pergunta['expectativa']}
    Contexto da vaga: {contexto_vaga}
    
    {INSIGHTS_GERAIS}
    
    Dê feedbacks diretos, ajude-o a inserir palavras-chave da vaga e a estruturar um Storytelling ou modelo STAR envolvente.
    """
    
    contents = []
    for msg in historico_mensagens:
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
        
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )
    
    return response.text