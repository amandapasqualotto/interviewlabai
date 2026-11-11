"""Integração com Gemini para avaliação, transcrição e mentoria."""
import os
import streamlit as st
from google import genai
from google.genai import types
from curadoria import INSIGHTS_GERAIS

MODEL = "gemini-2.5-flash"


def get_client():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Configure GEMINI_API_KEY em Settings > Secrets do Streamlit.")
    return genai.Client(api_key=api_key)


def _generate(client, prompt, web_search=False):
    config = types.GenerateContentConfig(
        temperature=0.55,
        tools=[types.Tool(google_search=types.GoogleSearch())] if web_search else None,
    )
    result = client.models.generate_content(model=MODEL, contents=prompt, config=config)
    return result.text or "Não foi possível gerar uma resposta. Tente novamente."


def avaliar_resposta(client, contexto, pergunta, resposta, metadados):
    prompt = f"""
Você é avaliador sênior de recrutamento e desenvolvimento de talentos.
Avalie com rigor, respeito e especificidade. Não force STAR em todas as perguntas.

CONTEXTO DA VAGA E DO CANDIDATO:
{contexto}

PERGUNTA: {pergunta}
TÉCNICA DA CURADORIA: {metadados.get('tecnica', 'Adequar à pergunta')}
EXPECTATIVA DA CURADORIA: {metadados.get('expectativa', '')}
DIRETRIZES:
{INSIGHTS_GERAIS}

RESPOSTA DO CANDIDATO:
{resposta}

Faça uma avaliação adequada ao tipo de pergunta. Para perguntas comportamentais, observe contexto,
responsabilidade, ações e resultados. Para trajetória/motivação, observe narrativa e conexão entre
passado, presente e futuro. Para perguntas técnicas, observe precisão, profundidade e aplicação.
Para pontos fortes/fracos, observe autenticidade, evidências e autoconhecimento. Não invente fatos,
competências, números ou experiências. Use apenas fatos fornecidos pelo candidato.

Organize em: 1) diagnóstico geral; 2) pontos fortes; 3) pontos a melhorar; 4) avaliação dos critérios
pertinentes (notas de 1 a 5, explicadas); 5) informações que faltam; 6) versão aprimorada natural,
marcando lacunas entre colchetes; 7) dica prática para a entrevista.
Não dê nota artificialmente alta e não trate a técnica como uma lista mecânica.
"""
    return _generate(client, prompt)


def transcrever_audio(client, audio_file):
    part = types.Part.from_bytes(data=audio_file.getvalue(), mime_type=audio_file.type or "audio/wav")
    result = client.models.generate_content(
        model=MODEL,
        contents=["Transcreva fielmente em português. Não avalie nem reescreva. Retorne somente a transcrição. Sinalize trechos inaudíveis.", part],
    )
    return result.text or ""


def mentor_chat(client, contexto, pergunta_atual, avaliacoes, historico, mensagem, web_search=True):
    prompt = f"""
Você é o mentor de carreira do Interview Lab AI, especialista em recrutamento, entrevistas e desenvolvimento profissional.

Use prioritariamente o contexto e as experiências reais abaixo. Não invente informações do candidato.

CONTEXTO DO CANDIDATO, VAGA E EMPRESA:
{contexto}

PERGUNTA EM TREINAMENTO:
{pergunta_atual or 'Não há pergunta selecionada no momento.'}

AVALIAÇÕES ANTERIORES:
{avaliacoes or 'Nenhuma avaliação anterior.'}

HISTÓRICO DA CONVERSA:
{historico}

MENSAGEM ATUAL:
{mensagem}

ORIENTAÇÕES:
- Personalize usando currículo, LinkedIn (quando houver conteúdo verificável), vaga e avaliações.
- Quando pertinente, pesquise na internet informações atuais sobre empresa, setor, vaga, competências
  e expectativas comuns de recrutadores. Priorize páginas oficiais e fontes confiáveis.
- Diferencie fatos encontrados, inferências e recomendações. Nunca afirme ter acessado um LinkedIn
  privado ou uma página que não conseguiu consultar.
- Ajude a construir respostas autênticas, sem inventar experiências ou resultados.
- Se faltarem dados pessoais essenciais, faça perguntas objetivas.
- Responda em português, com profundidade e tom profissional, evitando generalidades.
"""
    return _generate(client, prompt, web_search=web_search)
