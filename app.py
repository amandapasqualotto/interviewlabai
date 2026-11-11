from pathlib import Path
import zipfile, textwrap

base = Path("/mnt/data/interview_lab_ai_atualizado")
base.mkdir(exist_ok=True)

app_py = r'''import os
import io
import streamlit as st
from google import genai
from google.genai import types

from curadoria import INSIGHTS_GERAIS, PERGUNTAS_CURATORIA

# Dependências opcionais para leitura dos currículos.
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


# ---------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODEL = "gemini-2.5-flash"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

.stApp {
    background-color: #FBF9F5;
    color: #2C2A29;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
h1, h2, h3, h4, .editorial-title {
    font-family: 'Playfair Display', serif !important;
    color: #1E3023 !important;
    font-weight: 700;
}
p, label, div, span {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.editorial-card {
    background: #F4F1EA;
    border: 1px solid #E3DED4;
    padding: 22px;
    border-radius: 4px;
    margin-bottom: 16px;
}
.small-muted { color: #6C665F; font-size: .92rem; }
.stButton > button {
    background: #1E3023;
    color: #FBF9F5;
    border: 1px solid #1E3023;
    border-radius: 2px;
    padding: .58rem 1.15rem;
    font-weight: 500;
    transition: all .2s ease;
}
.stButton > button:hover {
    background: #2C4233;
    color: white;
    border-color: #2C4233;
}
.stTextInput input, .stTextArea textarea {
    background: #FFFFFF;
    border: 1px solid #DCD6CD;
    border-radius: 2px;
    color: #2C2A29;
}
div[data-baseweb="select"] > div {
    background: #FFFFFF;
    border-color: #DCD6CD;
    border-radius: 2px;
}
hr { border-color: #E3DED4; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px dashed #CFC7BA;
    padding: 10px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding:1.3rem 0 1rem 0;">
    <p style="letter-spacing:3px; font-size:.78rem; text-transform:uppercase; color:#5A655D; margin-bottom:.5rem;">
        Atelier de Carreiras & Simulações
    </p>
    <h1 style="font-size:3rem; margin-bottom:.45rem; font-style:italic;">Interview Lab AI</h1>
    <p style="color:#6C665F; font-size:1rem; max-width:680px; margin:0 auto;">
        Estruture respostas, pratique entrevistas e desenvolva uma narrativa profissional consistente com apoio de inteligência artificial.
    </p>
</div>
<hr style="border:none; border-top:1px solid #E3DED4; margin:1.5rem 0;">
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# ESTADO DA APLICAÇÃO
# ---------------------------------------------------------------------
DEFAULTS = {
    "contexto_vaga": None,
    "curriculo_texto": "",
    "curriculo_nome": "",
    "curriculo_bytes": None,
    "linkedin_url": "",
    "etapa1_concluida": False,
    "etapa2_concluida": False,
    "pergunta_selecionada": None,
    "resposta_texto": "",
    "ultima_avaliacao": None,
    "avaliacoes": [],
    "mensagens_chat": [],
    "audio_transcrito": "",
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------------------
# GEMINI / LEITURA DE ARQUIVOS
# ---------------------------------------------------------------------
def obter_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY")


def extrair_texto_curriculo(uploaded_file):
    """Extrai texto de PDF, DOCX ou TXT sem armazenar o arquivo externamente."""
    if uploaded_file is None:
        return "", ""

    raw = uploaded_file.getvalue()
    nome = uploaded_file.name
    ext = nome.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        if PdfReader is None:
            raise RuntimeError("Instale pypdf para permitir a leitura de currículos em PDF.")
        reader = PdfReader(io.BytesIO(raw))
        texto = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == "docx":
        if Document is None:
            raise RuntimeError("Instale python-docx para permitir a leitura de currículos DOCX.")
        doc = Document(io.BytesIO(raw))
        texto = "\n".join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                texto += "\n" + " | ".join(cell.text for cell in row.cells)
    elif ext == "txt":
        texto = raw.decode("utf-8", errors="replace")
    else:
        raise RuntimeError("Formato não suportado. Anexe um arquivo PDF, DOCX ou TXT.")

    return texto.strip(), nome


def gerar_conteudo(client, prompt, pesquisar_web=False):
    """Gera conteúdo; quando solicitado, habilita a ferramenta Google Search do Gemini."""
    config = types.GenerateContentConfig(
        temperature=0.55,
        tools=[types.Tool(google_search=types.GoogleSearch())] if pesquisar_web else None,
    )
    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )
    return resposta.text or "Não foi possível gerar uma resposta textual. Tente novamente."


def contexto_completo():
    contexto = st.session_state.get("contexto_vaga") or {}
    return f"""
EMPRESA: {contexto.get('empresa', 'Não informada')}
CARGO: {contexto.get('cargo', 'Não informado')}
DESCRIÇÃO E REQUISITOS DA VAGA:
{contexto.get('descricao', 'Não informado')}

SOBRE A EMPRESA (descrição, cultura, valores, estratégia etc.):
{contexto.get('sobre_empresa', 'Não informado')}

LINK DO LINKEDIN INFORMADO PELO CANDIDATO:
{st.session_state.get('linkedin_url') or 'Não informado'}

CURRÍCULO DO CANDIDATO (texto extraído do arquivo, quando disponível):
{st.session_state.get('curriculo_texto') or 'Não anexado'}

DIRETRIZES GERAIS DA CURADORIA:
{INSIGHTS_GERAIS}
"""


def avaliar_resposta_com_gemini(client, contexto, pergunta, resposta, metadados):
    prompt = f"""
Você é um avaliador sênior de recrutamento, desenvolvimento de talentos e entrevistas.
Avalie a resposta de forma criteriosa, construtiva, específica e personalizada.

CONTEXTO DA VAGA E DO CANDIDATO:
{contexto}

PERGUNTA:
{pergunta}

TÉCNICA INDICADA PELA CURADORIA:
{metadados.get('tecnica', 'Escolha a estrutura mais adequada à pergunta.')}

O QUE A PERGUNTA BUSCA AVALIAR:
{metadados.get('expectativa', 'Avalie as competências efetivamente demonstradas.')}

DIRETRIZES DA CURADORIA:
{INSIGHTS_GERAIS}

RESPOSTA DO CANDIDATO:
{resposta}

REGRAS DE AVALIAÇÃO:
- Não force a metodologia STAR em todas as perguntas.
- Respeite a técnica indicada pela curadoria e adapte os critérios ao tipo de pergunta.
- Para perguntas comportamentais, avalie contexto, responsabilidade individual, ações concretas,
  decisões e resultados, usando STAR quando fizer sentido.
- Para perguntas de trajetória, apresentação e motivação, avalie narrativa, coerência,
  passado-presente-futuro, clareza e conexão com a oportunidade.
- Para perguntas sobre pontos fortes/fracos, avalie autenticidade, evidências e autoconhecimento.
- Para perguntas técnicas, avalie precisão, profundidade, contexto de aplicação e honestidade
  sobre o nível de domínio.
- Não invente experiências, números, resultados, competências ou fatos sobre o candidato.
- Use o currículo e as informações fornecidas para apontar conexões reais. Se faltarem dados,
  indique o que o candidato poderia acrescentar, sem fabricar conteúdo.
- Considere a vaga e a empresa para avaliar relevância e alinhamento.

FORMATO DA DEVOLUTIVA:
1. **Diagnóstico geral**: qualidade e aderência da resposta.
2. **O que funcionou**: pontos fortes específicos.
3. **O que precisa melhorar**: lacunas, generalidades, falta de evidências ou excesso de informação.
4. **Avaliação por critérios**: avalie de 1 a 5 os critérios realmente pertinentes à pergunta
   (ex.: clareza, relevância, profundidade, evidências, alinhamento, estrutura).
5. **Como fortalecer**: perguntas ou informações que ajudariam a enriquecer a resposta.
6. **Versão aprimorada**: proponha uma versão mais forte, natural e autêntica, usando somente
   fatos fornecidos. Marque entre colchetes qualquer informação que ainda precise ser preenchida.
7. **Dica para a entrevista**: uma orientação prática e objetiva.

Não atribua uma nota artificialmente alta. Seja exigente, respeitoso e didático.
"""
    return gerar_conteudo(client, prompt)


def transcrever_audio(client, audio_file):
    audio_bytes = audio_file.getvalue()
    mime_type = audio_file.type or "audio/wav"
    prompt = """
Transcreva fielmente, em português, o áudio de resposta de entrevista a seguir.
Preserve o sentido e as palavras do candidato. Não avalie nem reescreva; retorne somente a transcrição.
Se houver trechos inaudíveis, sinalize como [trecho inaudível].
"""
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    result = client.models.generate_content(
        model=MODEL,
        contents=[prompt, audio_part],
    )
    return result.text or ""


# ---------------------------------------------------------------------
# AUTENTICAÇÃO DA API
# ---------------------------------------------------------------------
api_key = obter_api_key()
if not api_key:
    st.markdown("""
    <div class="editorial-card" style="border-left:4px solid #A35C44;">
        <h3 style="margin-top:0; color:#A35C44 !important;">Configuração necessária</h3>
        <p>A chave da API do Gemini não foi encontrada.</p>
        <p>Adicione <code>GEMINI_API_KEY</code> em Settings → Secrets no Streamlit Cloud
        ou como variável de ambiente.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

client = genai.Client(api_key=api_key)


# ---------------------------------------------------------------------
# NAVEGAÇÃO PROGRESSIVA
# ---------------------------------------------------------------------
opcoes_etapas = ["1. Contexto da vaga"]
if st.session_state["etapa1_concluida"]:
    opcoes_etapas.append("2. Painel de simulação")
if st.session_state["etapa2_concluida"]:
    opcoes_etapas.append("3. Lapidação e feedback")

if "etapa_atual" not in st.session_state:
    st.session_state["etapa_atual"] = opcoes_etapas[0]
if st.session_state["etapa_atual"] not in opcoes_etapas:
    st.session_state["etapa_atual"] = opcoes_etapas[-1]

st.radio(
    "Etapas",
    options=opcoes_etapas,
    horizontal=True,
    key="etapa_atual",
    label_visibility="collapsed",
)
st.markdown("<hr style='margin-top:.5rem;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# ETAPA 1 — CONTEXTO
# ---------------------------------------------------------------------
if st.session_state["etapa_atual"] == "1. Contexto da vaga":
    st.markdown("### Defina o contexto da vaga")
    st.markdown(
        "<p class='small-muted'>Informe os dados da oportunidade para que a simulação "
        "e as recomendações sejam relevantes para o processo seletivo.</p>",
        unsafe_allow_html=True,
    )

    contexto_existente = st.session_state.get("contexto_vaga") or {}
    c1, c2 = st.columns(2, gap="large")
    with c1:
        empresa = st.text_input(
            "Nome da empresa",
            value=contexto_existente.get("empresa", ""),
            placeholder="Ex.: Banco ABC, Google, escritório...",
        )
    with c2:
        cargo = st.text_input(
            "Cargo / posição desejada",
            value=contexto_existente.get("cargo", ""),
            placeholder="Ex.: Estagiário(a), Analista, Desenvolvedor(a)...",
        )

    descricao = st.text_area(
        "Descrição e requisitos da vaga",
        value=contexto_existente.get("descricao", ""),
        placeholder="Cole a descrição da oportunidade, responsabilidades e requisitos...",
        height=150,
    )
    sobre_empresa = st.text_area(
        "Sobre a empresa — descrição, cultura, valores etc.",
        value=contexto_existente.get("sobre_empresa", ""),
        placeholder="Compartilhe o que sabe sobre a empresa, sua cultura, valores, produtos, missão e estratégia...",
        height=130,
    )

    st.markdown("#### Informações complementares (opcionais)")
    col_link, col_cv = st.columns([1, 1], gap="large")
    with col_link:
        linkedin_url = st.text_input(
            "Link do LinkedIn",
            value=st.session_state.get("linkedin_url", ""),
            placeholder="https://www.linkedin.com/in/seu-perfil/",
            help="O acesso a perfis pode ser limitado pelas configurações de privacidade do LinkedIn.",
        )
    with col_cv:
        curriculo = st.file_uploader(
            "Anexar currículo",
            type=["pdf", "docx", "txt"],
            help="Formatos aceitos: PDF, DOCX e TXT. O conteúdo será usado para personalizar as análises.",
        )

    if curriculo is not None:
        try:
            texto_cv, nome_cv = extrair_texto_curriculo(curriculo)
            st.session_state["curriculo_texto"] = texto_cv
            st.session_state["curriculo_nome"] = nome_cv
            st.session_state["curriculo_bytes"] = curriculo.getvalue()
            st.caption(f"Currículo carregado: {nome_cv}")
            if not texto_cv:
                st.warning("O arquivo foi anexado, mas não foi possível extrair texto. "
                           "Se for um PDF digitalizado, tente uma versão com texto selecionável.")
        except Exception as exc:
            st.error(f"Não foi possível ler o currículo: {exc}")

    if st.session_state.get("curriculo_nome") and curriculo is None:
        st.caption(f"Currículo já carregado nesta sessão: {st.session_state['curriculo_nome']}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Salvar contexto e avançar", type="primary"):
        if not empresa.strip() or not cargo.strip() or not descricao.strip():
            st.warning("Preencha pelo menos empresa, cargo e descrição/requisitos da vaga.")
        elif linkedin_url and not linkedin_url.startswith(("https://", "http://")):
            st.warning("Informe um link válido, começando com https:// ou http://.")
        else:
            st.session_state["contexto_vaga"] = {
                "empresa": empresa.strip(),
                "cargo": cargo.strip(),
                "descricao": descricao.strip(),
                "sobre_empresa": sobre_empresa.strip(),
            }
            st.session_state["linkedin_url"] = linkedin_url.strip()
            st.session_state["etapa1_concluida"] = True
            st.session_state["etapa_atual"] = "2. Painel de simulação"
            st.success("Contexto salvo. A etapa de simulação foi liberada.")
            st.rerun()


# ---------------------------------------------------------------------
# ETAPA 2 — SIMULAÇÃO
# ---------------------------------------------------------------------
elif st.session_state["etapa_atual"] == "2. Painel de simulação":
    st.markdown("### Simulação de pergunta e resposta")
    st.markdown(
        "<p class='small-muted'>Selecione uma pergunta da curadoria, escolha como responder "
        "e receba uma avaliação ajustada ao objetivo daquela pergunta.</p>",
        unsafe_allow_html=True,
    )

    perguntas = list(PERGUNTAS_CURATORIA.keys())
    pergunta = st.selectbox(
        "Perguntas disponíveis na curadoria",
        options=perguntas,
        index=perguntas.index(st.session_state["pergunta_selecionada"])
        if st.session_state.get("pergunta_selecionada") in perguntas else 0,
    )
    st.session_state["pergunta_selecionada"] = pergunta
    metadados = PERGUNTAS_CURATORIA[pergunta]

    with st.container(border=True):
        st.markdown("**Técnica recomendada**")
        st.write(metadados.get("tecnica", "A definir conforme a pergunta."))
        st.markdown("**O que esta pergunta busca avaliar**")
        st.write(metadados.get("expectativa", ""))

    modo_resposta = st.radio(
        "Como deseja responder?",
        ["Escrever resposta", "Gravar resposta em áudio"],
        horizontal=True,
    )

    resposta_final = ""
    if modo_resposta == "Escrever resposta":
        resposta_final = st.text_area(
            "Sua resposta",
            placeholder="Responda como se estivesse diante do recrutador. Use exemplos reais e detalhes concretos...",
            height=220,
            key="resposta_texto",
        )
    else:
        st.caption("Grave sua resposta diretamente pelo microfone do dispositivo.")
        if hasattr(st, "audio_input"):
            audio = st.audio_input("Gravar resposta")
            if audio is not None:
                st.audio(audio)
                if st.button("Transcrever áudio"):
                    with st.spinner("Transcrevendo sua resposta..."):
                        try:
                            st.session_state["audio_transcrito"] = transcrever_audio(client, audio)
                            st.success("Transcrição concluída. Revise o texto antes de avaliar.")
                        except Exception as exc:
                            st.error(f"Não foi possível transcrever o áudio: {exc}")
                if st.session_state.get("audio_transcrito"):
                    st.text_area(
                        "Transcrição para revisão",
                        key="audio_transcrito_editavel",
                        value=st.session_state["audio_transcrito"],
                        height=180,
                    )
                    resposta_final = st.session_state.get("audio_transcrito_editavel", st.session_state["audio_transcrito"])
        else:
            st.warning("A gravação de áudio exige uma versão recente do Streamlit. "
                       "Atualize com: pip install --upgrade streamlit")

    if st.button("Avaliar minha resposta", type="primary"):
        if not resposta_final.strip():
            st.warning("Escreva ou grave uma resposta antes de solicitar a avaliação.")
        else:
            with st.spinner("Analisando sua resposta em relação à pergunta e à vaga..."):
                try:
                    resultado = avaliar_resposta_com_gemini(
                        client,
                        contexto_completo(),
                        pergunta,
                        resposta_final,
                        metadados,
                    )
                    st.session_state["ultima_avaliacao"] = resultado
                    st.session_state["avaliacoes"].append({
                        "pergunta": pergunta,
                        "resposta": resposta_final,
                        "avaliacao": resultado,
                    })
                    st.session_state["etapa2_concluida"] = True
                    st.success("Avaliação concluída. A etapa de lapidação foi liberada.")
                except Exception as exc:
                    st.error(f"Erro ao avaliar a resposta: {exc}")

    if st.session_state.get("ultima_avaliacao"):
        st.markdown("---")
        st.markdown("### Parecer do avaliador")
        st.markdown(st.session_state["ultima_avaliacao"])

    if st.session_state["etapa2_concluida"]:
        st.markdown("---")
        if st.button("Avançar para lapidação e feedback"):
            st.session_state["etapa_atual"] = "3. Lapidação e feedback"
            st.rerun()


# ---------------------------------------------------------------------
# ETAPA 3 — CHAT COM PESQUISA NA WEB
# ---------------------------------------------------------------------
elif st.session_state["etapa_atual"] == "3. Lapidação e feedback":
    st.markdown("### Atelier de lapidação")
    st.markdown(
        "<p class='small-muted'>Converse com seu mentor de carreira. A IA considera seu contexto, "
        "currículo, informações da oportunidade e pode pesquisar fontes públicas na internet.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("Contexto utilizado pelo mentor", expanded=False):
        ctx = st.session_state.get("contexto_vaga") or {}
        st.write(f"**Empresa:** {ctx.get('empresa', '')}")
        st.write(f"**Cargo:** {ctx.get('cargo', '')}")
        st.write(f"**Currículo:** {st.session_state.get('curriculo_nome') or 'Não anexado'}")
        st.write(f"**LinkedIn:** {st.session_state.get('linkedin_url') or 'Não informado'}")
        st.caption("O link do LinkedIn é uma referência. O acesso ao conteúdo do perfil pode ser restrito.")

    for msg in st.session_state["mensagens_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt_usuario = st.chat_input(
        "Ex.: Como posso conectar minha experiência aos requisitos desta vaga?"
    )

    if prompt_usuario:
        st.session_state["mensagens_chat"].append({
            "role": "user",
            "content": prompt_usuario,
        })
        with st.chat_message("user"):
            st.markdown(prompt_usuario)

        historico = st.session_state["mensagens_chat"][-12:]
        historico_formatado = "\n\n".join(
            f"{'CANDIDATO' if m['role'] == 'user' else 'MENTOR'}: {m['content']}"
            for m in historico
        )

        prompt_chat = f"""
Você é o mentor de carreira do Interview Lab AI: experiente em recrutamento,
entrevistas, desenvolvimento profissional e comunicação executiva.

Use como fontes prioritárias as informações abaixo, sem inventar dados:
{contexto_completo()}

AVALIAÇÕES ANTERIORES DA SIMULAÇÃO:
{chr(10).join(
    [f"Pergunta: {a['pergunta']}\\nResposta: {a['resposta']}\\nFeedback: {a['avaliacao']}"
     for a in st.session_state['avaliacoes'][-3:]]
) or "Nenhuma avaliação anterior."}

HISTÓRICO RECENTE:
{historico_formatado}

MENSAGEM ATUAL:
{prompt_usuario}

INSTRUÇÕES:
- Personalize as respostas principalmente com base no currículo e nos dados fornecidos pelo candidato.
- Ajude a conectar experiências reais às exigências da vaga, sem criar experiências ou resultados.
- Quando a pergunta envolver a empresa, a vaga, o setor, competências exigidas ou práticas de entrevista,
  pesquise informações públicas atuais na internet usando Google Search.
- Pesquise também o que recrutadores costumam avaliar em perguntas desse tipo, priorizando fontes
  confiáveis, páginas oficiais da empresa, descrições de vagas e referências reconhecidas de carreira.
- Se o usuário fornecer um link do LinkedIn, tente localizar informações públicas indexadas associadas
  ao link ou ao nome/perfil, mas deixe claro quando não conseguir acessar ou confirmar o conteúdo.
  Nunca alegue ter lido o perfil se isso não ocorreu.
- Diferencie fatos confirmados, inferências e sugestões. Não invente dados da empresa nem atribua
  ao candidato competências não demonstradas.
- Se faltarem informações pessoais para uma resposta mais forte, faça perguntas objetivas.
- Escreva em português, com clareza, profundidade e tom profissional, sem respostas genéricas.
- Ao sugerir uma resposta de entrevista, preserve uma voz natural e autêntica.
"""
        with st.chat_message("assistant"):
            with st.spinner("Analisando o contexto e pesquisando referências públicas..."):
                try:
                    resposta_ia = gerar_conteudo(client, prompt_chat, pesquisar_web=True)
                    st.markdown(resposta_ia)
                    st.session_state["mensagens_chat"].append({
                        "role": "assistant",
                        "content": resposta_ia,
                    })
                except Exception as exc:
                    erro = f"Não foi possível consultar o mentor neste momento: {exc}"
                    st.error(erro)
                    st.session_state["mensagens_chat"].append({
                        "role": "assistant",
                        "content": erro,
                    })

    st.markdown("---")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Limpar conversa"):
            st.session_state["mensagens_chat"] = []
            st.rerun()
    with col_b:
        if st.button("Voltar à simulação"):
            st.session_state["etapa_atual"] = "2. Painel de simulação"
            st.rerun()
'''

curadoria_py = r'''# curadoria.py
# Banco de perguntas e critérios de avaliação do Interview Lab AI.

INSIGHTS_GERAIS = """
DIRETRIZES DE AVALIAÇÃO DE RESPOSTAS EM ENTREVISTAS:
1. Alinhamento com a Vaga: Conectar exemplos aos valores da empresa e utilizar palavras-chave presentes no descritivo da vaga.
2. Estruturação Técnica e Storytelling: Perguntas comportamentais devem seguir STAR; perguntas de trajetória/visão pessoal devem usar Storytelling (Passado, Presente e Futuro com aprendizados marcantes).
3. Objetividade e Clareza: Evitar rodeios mantendo detalhes concretos (métricas, aprendizados, impactos).
4. Postura e Tom: Demonstrar autoconhecimento, inteligência emocional e capacidade de aprendizagem contínua.
"""

PERGUNTAS_CURATORIA = {
    "Descreva uma situação em que você precisou se adaptar rapidamente a uma nova demanda ou contexto": {
        "tecnica": "STAR (Situação, Tarefa, Ação e Resultado)",
        "expectativa": "Avalia flexibilidade, resiliência e agilidade de aprendizado. Espera-se que o candidato mostre como manteve a calma, reorganizou prioridades e gerou resultado rápido."
    },
    "Conte sobre uma situação em que você identificou uma oportunidade de melhoria ou um problema e tomou a iniciativa para resolvê-lo ou propor uma solução.": {
        "tecnica": "STAR",
        "expectativa": "Avalia proatividade, senso de dono (ownership) e visão crítica. Espera-se que o candidato não tenha apenas apontado o problema, mas liderado/executado a solução."
    },
    "Como você busca aprender e se desenvolver em novas áreas ou com novas ferramentas? Dê um exemplo de algo que você aprendeu recentemente por iniciativa própria.": {
        "tecnica": "Exemplo Prático + Aplicação",
        "expectativa": "Avalia Lifelong Learning e curiosidade. Espera-se demonstrar métodos de estudo autônomos (cursos, projetos, testes) e o impacto prático do que foi aprendido."
    },
    "Descreva uma situação em que você precisou colaborar com outras pessoas para alcançar um objetivo. Como foi sua participação e qual foi o resultado?": {
        "tecnica": "STAR",
        "expectativa": "Avalia trabalho em equipe, empatia e inteligência interpessoal. Espera-se foco no papel do candidato sem anular a contribuição do grupo."
    },
    "Para começar, conte-me sobre sua trajetória profissional e formação. Quanto tempo de experiência você tem na área, quais foram suas principais responsabilidades e atividades em cada cargo": {
        "tecnica": "Pitch Pessoal (Passado, Presente e Futuro)",
        "expectativa": "Resumo cronológico e estratégico. Espera-se destaque aos marcos mais relevantes e conexões diretas entre o histórico e o momento atual/objetivo da vaga."
    },
    "Descreva uma situação em que você precisou explicar algo complexo para alguém que não tinha conhecimento técnico. Como você adaptou sua comunicação?": {
        "tecnica": "STAR (Foco em Didática)",
        "expectativa": "Avalia comunicação adaptável e empatia. Espera-se o uso de analogias, escuta ativa e verificação de entendimento do interlocutor."
    },
    "Conte uma vez em que você precisou 'trocar o pneu com o carro em movimento' — ou seja, manter algo funcionando enquanto tentava melhorar o processo. O que você priorizou em cada etapa para não deixar a peteca cair?": {
        "tecnica": "STAR (Foco em Priorização e Gestão de Risco)",
        "expectativa": "Avalia gestão sob pressão, triagem de tarefas críticas e capacidade de otimização contínua."
    },
    "Relate uma ocasião em que algo não saiu como o planejado ou em que você cometeu um erro em um projeto. Como você reagiu no momento, o que aprendeu com essa experiência e o que mudou na sua forma de trabalhar depois disso?": {
        "tecnica": "STAR (Foco na Reação, Aprendizado e Prevenção)",
        "expectativa": "Avalia maturidade, autorresponsabilidade e inteligência emocional. Não busque culpar terceiros; foque no aprendizado e na mudança de processo."
    },
    "Você mencionou que aprendeu com a experiência e que teve um fio condutor para resolver problemas semelhantes no futuro. Poderia compartilhar um exemplo específico de como você aplicou esse aprendizado em uma situação posterior?": {
        "tecnica": "STAR (Foco na Aplicação Prática da Lição Aprendida)",
        "expectativa": "Demonstrar a evolução e maturidade profissional após uma falha ou aprendizado prévio."
    },
    "Como a Inteligência Artificial faz parte da sua rotina atual? Como você a utiliza para resolver problemas cotidianos sem perder a visão crítica do resultado? Consegue nos dar algum exemplo mais concreto?": {
        "tecnica": "Uso Prático + Pensamento Crítico",
        "expectativa": "Avalia afinidade tecnológica e critério. O candidato deve citar ferramentas e ressaltar a checagem de fatos/supervisão humana."
    },
    "Conte sobre uma vez em que você discordou da opinião de um colega ou líder em um trabalho em grupo. Como você defendeu suas ideias e como chegaram a um consenso?": {
        "tecnica": "STAR (Foco em Negociação e Argumentação Baseada em Dados)",
        "expectativa": "Avalia diplomacia, escuta e capacidade de construir consensos focando no objetivo do projeto."
    },
    "Como você acredita que suas habilidades e interesses se alinham a essa missão e como você gostaria de contribuir para gerar impacto?": {
        "tecnica": "Conexão de Valores e Competências",
        "expectativa": "Demonstrar pesquisa prévia sobre a empresa, alinhando propósitos pessoais aos objetivos organizacionais."
    },
    "Porque vc é o melhor candidato para esse cargo?": {
        "tecnica": "Value Pitch (Diferencial Competitivo)",
        "expectativa": "Conexão direta entre hard/soft skills do candidato e as dores/necessidades imediatas descritas na vaga."
    },
    "Porque a nossa empresa?": {
        "tecnica": "Storytelling de Conexão de Propósito",
        "expectativa": "Contar o ponto de contato em que sua história cruzou com a missão, produto ou cultura da empresa, mostrando pesquisa prévia."
    },
    "Conte sobre uma vez em que você teve múltiplas entregas simultâneas. Como você organizou seu tempo e garantiu que todas fossem cumpridas?": {
        "tecnica": "STAR (Foco em Metodologia de Organização)",
        "expectativa": "Citar métodos reais de priorização (Matriz de Eisenhower, listas, Notion, Kanban) e alinhamento de prazos."
    },
    "Fale sobre uma habilidade que você aprendeu recentemente por conta própria. O que te motivou e como foi o processo?": {
        "tecnica": "Motivação + Processo + Resultado",
        "expectativa": "Autonomia e curiosidade intelectiva. Mostrar o caminho percorrido do zero à aplicação prática."
    },
    "Me conte sobre você": {
        "tecnica": "Storytelling: Passado, Presente e Futuro (Elevator Pitch)",
        "expectativa": "Construir uma narrativa fluida (máx. 2 min) ligando a origem do seu interesse na área, momentos-chave da sua trajetória, sua atuação atual e por que esta oportunidade é o próximo passo natural."
    },
    "Onde você se vê daqui a 5 anos?": {
        "tecnica": "Storytelling de Visão e Conectividade",
        "expectativa": "Pintar uma imagem clara da sua evolução profissional alinhada aos desafios e à trilha de crescimento da empresa."
    },
    "Como você lida com pressão ou prazos apertados?": {
        "tecnica": "Estratégia de Controle + Exemplo STAR curto",
        "expectativa": "Inteligência emocional, foco em resolução de problemas e comunicação antecipada de riscos."
    },
    "Como você lida com equipes ou colaboração em grupo?": {
        "tecnica": "Estilo de Trabalho + Exemplo Prático",
        "expectativa": "Demonstrar adaptabilidade, boa comunicação, respeito à diversidade de opiniões e foco em metas coletivas."
    },
    "Você tem alguma pergunta?": {
        "tecnica": "Perguntas Estratégicas sobre o Negócio/Cultura",
        "expectativa": "Demonstrar interesse genuíno fazendo 2 a 3 perguntas sobre a rotina da área, desafios do setor ou cultura do time."
    },
    "Quais são seus pontos fortes": {
        "tecnica": "Fortaleza + Exemplo de Aplicação",
        "expectativa": "Citar 2 a 3 fortalezas relevantes para a vaga acompanhadas de breves evidências práticas."
    },
    "Quais são seus pontos fracos?": {
        "tecnica": "Storytelling de Vulnerabilidade + Plano de Ação",
        "expectativa": "Narrar um momento real de dificuldade sem clichês, mostrando a tomada de consciência e o método prático adotado para superá-lo."
    },
    "Com quais ferramentas, frameworks ou tecnologias você tem mais experiência?": {
        "tecnica": "Objetiva + Nível de Proficiência + Contexto de Uso",
        "expectativa": "Listar tecnologias pertinentes informando contexto de aplicação em projetos reais."
    },
    "Que legado você espera deixar nesta organização?": {
        "tecnica": "Visão de Impacto a Longo Prazo",
        "expectativa": "Demonstrar vontade de construir soluções duradouras, melhorar processos ou impactar positivamente a cultura do time."
    },
    "Você teve oportunidade de liderar um projeto? Conte-nos como foi o processo.": {
        "tecnica": "STAR (Foco em Gestão de Projeto e Pessoas)",
        "expectativa": "Demonstrar planejamento, delegação de tarefas, acompanhamento de métricas e contorno de imprevistos."
    },
    "Voce teve oportunidade de exercer liderança? Conte essa experiencia.": {
        "tecnica": "STAR (Foco em Liderança Situacional/Informal)",
        "expectativa": "Mesmo sem cargo formal, demonstrar iniciativa para guiar, apoiar ou destravar colegas em prol de um objetivo comum."
    }
}
'''

requirements = """streamlit>=1.40.0
google-genai>=1.0.0
pypdf>=5.0.0
python-docx>=1.1.2
"""

readme = """# Interview Lab AI — versão atualizada

## Arquivos
- `app.py`: aplicação Streamlit.
- `curadoria.py`: perguntas e diretrizes da curadoria.
- `requirements.txt`: dependências.

## Instalação local
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Configure a chave do Gemini como variável de ambiente `GEMINI_API_KEY` ou nos Secrets do Streamlit Cloud:

```toml
GEMINI_API_KEY = "SUA_CHAVE"
```

Execute:
```bash
streamlit run app.py
```

## Publicação no Streamlit Community Cloud
1. Envie `app.py`, `curadoria.py` e `requirements.txt` para o mesmo repositório GitHub.
2. No Streamlit Community Cloud, conecte o repositório e selecione `app.py`.
3. Em **App settings → Secrets**, adicione `GEMINI_API_KEY = "SUA_CHAVE"`.
4. Reinicie o app.

## Fluxo
1. Contexto da vaga: empresa, cargo e descrição são obrigatórios; informações sobre a empresa, currículo e LinkedIn são opcionais.
2. Simulação: as perguntas são carregadas de `PERGUNTAS_CURATORIA`. O candidato pode escrever ou gravar áudio; o áudio é transcrito pelo Gemini antes da avaliação.
3. Lapidação: chat com contexto do candidato e pesquisa pública via Google Search do Gemini.

## Observações importantes
- O áudio depende de navegador/dispositivo com microfone e de uma versão compatível do Streamlit.
- O currículo é processado em memória durante a sessão. Não há banco de dados nem armazenamento permanente implementado neste exemplo.
- O LinkedIn pode bloquear acessos automatizados. O sistema não garante leitura do perfil; use o currículo e as informações preenchidas como fonte principal.
- A pesquisa na internet é feita pela ferramenta Google Search disponibilizada ao modelo Gemini. Confirme informações importantes nas fontes originais.
- A etapa 2 é considerada concluída após a primeira avaliação bem-sucedida. A etapa 3 então é liberada.
"""

(base / "app.py").write_text(app_py, encoding="utf-8")
(base / "curadoria.py").write_text(curadoria_py, encoding="utf-8")
(base / "requirements.txt").write_text(requirements, encoding="utf-8")
(base / "README.md").write_text(readme, encoding="utf-8")

zip_path = Path("/mnt/data/interview_lab_ai_atualizado.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in base.iterdir():
        z.write(p, arcname=f"interview_lab_ai_atualizado/{p.name}")

print(f"Projeto criado: {zip_path}")
print(f"Arquivos: {[p.name for p in base.iterdir()]}")
