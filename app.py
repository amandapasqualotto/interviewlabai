import os
import io
import streamlit as st
from google import genai
from google.genai import types

from curadoria import INSIGHTS_GERAIS, PERGUNTAS_CURATORIA

# Dependências para leitura dos currículos
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODEL = "gemini-2.5-flash"


# ============================================================
# IDENTIDADE VISUAL
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

.stApp {
    background-color: #FBF9F5;
    color: #2C2A29;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, h4 {
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

.small-muted {
    color: #6C665F;
    font-size: .92rem;
}

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

.stTextInput input,
.stTextArea textarea {
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

hr {
    border-color: #E3DED4;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px dashed #CFC7BA;
    padding: 10px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown("""
<div style="text-align:center; padding:1.3rem 0 1rem 0;">

    <p style="
        letter-spacing:3px;
        font-size:.78rem;
        text-transform:uppercase;
        color:#5A655D;
        margin-bottom:.5rem;
    ">
        Atelier de Carreiras & Simulações
    </p>

    <h1 style="
        font-size:3rem;
        margin-bottom:.45rem;
        font-style:italic;
    ">
        Interview Lab AI
    </h1>

    <p style="
        color:#6C665F;
        font-size:1rem;
        max-width:680px;
        margin:0 auto;
    ">
        Estruture respostas, pratique entrevistas e desenvolva
        uma narrativa profissional consistente com apoio
        de inteligência artificial.
    </p>

</div>

<hr style="
    border:none;
    border-top:1px solid #E3DED4;
    margin:1.5rem 0;
">
""", unsafe_allow_html=True)


# ============================================================
# ESTADO DA APLICAÇÃO
# ============================================================

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


# ============================================================
# GEMINI E LEITURA DE ARQUIVOS
# ============================================================

def obter_api_key():

    try:
        key = st.secrets.get("GEMINI_API_KEY")

        if key:
            return key

    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


def extrair_texto_curriculo(uploaded_file):

    if uploaded_file is None:
        return "", ""

    raw = uploaded_file.getvalue()
    nome = uploaded_file.name

    ext = nome.lower().rsplit(".", 1)[-1]

    if ext == "pdf":

        if PdfReader is None:
            raise RuntimeError(
                "Instale pypdf para permitir a leitura de currículos em PDF."
            )

        reader = PdfReader(io.BytesIO(raw))

        texto = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif ext == "docx":

        if Document is None:
            raise RuntimeError(
                "Instale python-docx para permitir a leitura de currículos DOCX."
            )

        doc = Document(io.BytesIO(raw))

        texto = "\n".join(
            p.text for p in doc.paragraphs
        )

        for table in doc.tables:

            for row in table.rows:

                texto += "\n" + " | ".join(
                    cell.text for cell in row.cells
                )

    elif ext == "txt":

        texto = raw.decode(
            "utf-8",
            errors="replace"
        )

    else:

        raise RuntimeError(
            "Formato não suportado. Anexe PDF, DOCX ou TXT."
        )

    return texto.strip(), nome


def gerar_conteudo(client, prompt, pesquisar_web=False):

    config = types.GenerateContentConfig(
        temperature=0.55,
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ] if pesquisar_web else None,
    )

    resposta = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )

    return resposta.text or (
        "Não foi possível gerar uma resposta textual. Tente novamente."
    )


# ============================================================
# CONTEXTO COMPLETO DO CANDIDATO
# ============================================================

def contexto_completo():

    contexto = st.session_state.get(
        "contexto_vaga"
    ) or {}

    return f"""

EMPRESA:
{contexto.get('empresa', 'Não informada')}

CARGO:
{contexto.get('cargo', 'Não informado')}

DESCRIÇÃO E REQUISITOS DA VAGA:
{contexto.get('descricao', 'Não informado')}

SOBRE A EMPRESA:
{contexto.get('sobre_empresa', 'Não informado')}

LINK DO LINKEDIN:
{st.session_state.get('linkedin_url') or 'Não informado'}

CURRÍCULO DO CANDIDATO:
{st.session_state.get('curriculo_texto') or 'Não anexado'}

DIRETRIZES GERAIS DA CURADORIA:
{INSIGHTS_GERAIS}

"""


# ============================================================
# AVALIAÇÃO PERSONALIZADA
# ============================================================

def avaliar_resposta_com_gemini(
    client,
    contexto,
    pergunta,
    resposta,
    metadados
):

    prompt = f"""

Você é um avaliador sênior de recrutamento,
desenvolvimento de talentos e entrevistas.

Avalie a resposta de forma criteriosa,
construtiva, específica e personalizada.

CONTEXTO DA VAGA E DO CANDIDATO:

{contexto}

PERGUNTA:

{pergunta}

TÉCNICA INDICADA PELA CURADORIA:

{metadados.get('tecnica', 'Escolha a estrutura mais adequada.')}

O QUE A PERGUNTA BUSCA AVALIAR:

{metadados.get('expectativa', '')}

DIRETRIZES DA CURADORIA:

{INSIGHTS_GERAIS}

RESPOSTA DO CANDIDATO:

{resposta}


REGRAS DE AVALIAÇÃO:

- Não force a metodologia STAR em todas as perguntas.

- Respeite a técnica indicada pela curadoria e adapte
  os critérios ao tipo de pergunta.

- Para perguntas comportamentais, avalie contexto,
  responsabilidade individual, ações concretas,
  decisões e resultados.

- Para perguntas de trajetória, apresentação e motivação,
  avalie narrativa, coerência, passado, presente e futuro.

- Para perguntas sobre pontos fortes e fracos,
  avalie autenticidade, evidências e autoconhecimento.

- Para perguntas técnicas, avalie precisão, profundidade,
  contexto de aplicação e honestidade sobre o nível de domínio.

- Não invente experiências, números, resultados,
  competências ou fatos sobre o candidato.

- Utilize o currículo e as informações fornecidas
  para apontar conexões reais.

- Considere a vaga e a empresa para avaliar
  relevância e alinhamento.


FORMATO DA DEVOLUTIVA:

1. DIAGNÓSTICO GERAL

Qualidade e aderência da resposta.

2. O QUE FUNCIONOU

Pontos fortes específicos.

3. O QUE PRECISA MELHORAR

Lacunas, generalidades, falta de evidências
ou excesso de informação.

4. AVALIAÇÃO POR CRITÉRIOS

Avalie de 1 a 5 os critérios pertinentes
àquela pergunta.

5. COMO FORTALECER

Perguntas ou informações que ajudariam
a enriquecer a resposta.

6. VERSÃO APRIMORADA

Proponha uma versão mais forte, natural e autêntica,
utilizando somente fatos fornecidos.

Marque entre colchetes informações que ainda
precisem ser preenchidas.

7. DICA PARA A ENTREVISTA

Uma orientação prática e objetiva.

Não atribua uma nota artificialmente alta.
Seja exigente, respeitoso e didático.

"""

    return gerar_conteudo(
        client,
        prompt
    )


# ============================================================
# TRANSCRIÇÃO DE ÁUDIO
# ============================================================

def transcrever_audio(client, audio_file):

    audio_bytes = audio_file.getvalue()

    mime_type = audio_file.type or "audio/wav"

    prompt = """

Transcreva fielmente, em português,
o áudio de resposta de entrevista a seguir.

Preserve o sentido e as palavras do candidato.

Não avalie nem reescreva.

Retorne somente a transcrição.

Se houver trechos inaudíveis,
sinalize como [trecho inaudível].

"""

    audio_part = types.Part.from_bytes(
        data=audio_bytes,
        mime_type=mime_type,
    )

    result = client.models.generate_content(
        model=MODEL,
        contents=[
            prompt,
            audio_part
        ],
    )

    return result.text or ""


# ============================================================
# AUTENTICAÇÃO DA API
# ============================================================

api_key = obter_api_key()

if not api_key:

    st.markdown("""
    <div class="editorial-card"
         style="border-left:4px solid #A35C44;">

        <h3 style="margin-top:0; color:#A35C44 !important;">
            Configuração necessária
        </h3>

        <p>
            A chave da API do Gemini não foi encontrada.
        </p>

        <p>
            Adicione GEMINI_API_KEY em Settings → Secrets
            no Streamlit Cloud ou como variável de ambiente.
        </p>

    </div>
    """, unsafe_allow_html=True)

    st.stop()


client = genai.Client(api_key=api_key)


# ============================================================
# NAVEGAÇÃO PROGRESSIVA
# ============================================================

opcoes_etapas = [
    "1. Contexto da vaga"
]

if st.session_state["etapa1_concluida"]:

    opcoes_etapas.append(
        "2. Painel de simulação"
    )

if st.session_state["etapa2_concluida"]:

    opcoes_etapas.append(
        "3. Lapidação e feedback"
    )


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

st.markdown(
    "<hr style='margin-top:.5rem;'>",
    unsafe_allow_html=True
)


# ============================================================
# ETAPA 1 — CONTEXTO DA VAGA
# ============================================================

if st.session_state["etapa_atual"] == "1. Contexto da vaga":

    st.markdown("### Defina o contexto da vaga")

    st.markdown(
        """
        <p class='small-muted'>
        Informe os dados da oportunidade para que a simulação
        e as recomendações sejam relevantes para o processo seletivo.
        </p>
        """,
        unsafe_allow_html=True,
    )

    contexto_existente = (
        st.session_state.get("contexto_vaga") or {}
    )

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


    st.markdown(
        "#### Informações complementares (opcionais)"
    )

    col_link, col_cv = st.columns(
        [1, 1],
        gap="large"
    )

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
            help="Formatos aceitos: PDF, DOCX e TXT.",
        )


    if curriculo is not None:

        try:

            texto_cv, nome_cv = extrair_texto_curriculo(
                curriculo
            )

            st.session_state["curriculo_texto"] = texto_cv

            st.session_state["curriculo_nome"] = nome_cv

            st.session_state["curriculo_bytes"] = (
                curriculo.getvalue()
            )

            st.caption(
                f"Currículo carregado: {nome_cv}"
            )

            if not texto_cv:

                st.warning(
                    "O arquivo foi anexado, mas não foi possível extrair texto. "
                    "Se for um PDF digitalizado, tente uma versão com texto selecionável."
                )

        except Exception as exc:

            st.error(
                f"Não foi possível ler o currículo: {exc}"
            )


    if (
        st.session_state.get("curriculo_nome")
        and curriculo is None
    ):

        st.caption(
            "Currículo já carregado nesta sessão: "
            + st.session_state["curriculo_nome"]
        )


    st.markdown("<br>", unsafe_allow_html=True)


    if st.button(
        "Salvar contexto e avançar",
        type="primary"
    ):

        if (
            not empresa.strip()
            or not cargo.strip()
            or not descricao.strip()
        ):

            st.warning(
                "Preencha pelo menos empresa, cargo e descrição/requisitos da vaga."
            )

        elif linkedin_url and not linkedin_url.startswith(
            ("https://", "http://")
        ):

            st.warning(
                "Informe um link válido, começando com https:// ou http://."
            )

        else:

            st.session_state["contexto_vaga"] = {

                "empresa": empresa.strip(),

                "cargo": cargo.strip(),

                "descricao": descricao.strip(),

                "sobre_empresa": sobre_empresa.strip(),

            }

            st.session_state["linkedin_url"] = (
                linkedin_url.strip()
            )

            st.session_state["etapa1_concluida"] = True

            st.session_state["etapa_atual"] = (
                "2. Painel de simulação"
            )

            st.success(
                "Contexto salvo. A etapa de simulação foi liberada."
            )

            st.rerun()


# ============================================================
# ETAPA 2 — SIMULAÇÃO
# ============================================================

elif st.session_state["etapa_atual"] == "2. Painel de simulação":

    st.markdown(
        "### Simulação de pergunta e resposta"
    )

    st.markdown(
        """
        <p class='small-muted'>
        Selecione uma pergunta da curadoria, escolha como responder
        e receba uma avaliação ajustada ao objetivo daquela pergunta.
        </p>
        """,
        unsafe_allow_html=True,
    )


    perguntas = list(
        PERGUNTAS_CURATORIA.keys()
    )


    pergunta = st.selectbox(
        "Perguntas disponíveis na curadoria",

        options=perguntas,

        index=(
            perguntas.index(
                st.session_state["pergunta_selecionada"]
            )
            if st.session_state.get("pergunta_selecionada") in perguntas
            else 0
        ),
    )


    st.session_state["pergunta_selecionada"] = pergunta

    metadados = PERGUNTAS_CURATORIA[pergunta]


    with st.container(border=True):

        st.markdown("**Técnica recomendada**")

        st.write(
            metadados.get(
                "tecnica",
                "A definir conforme a pergunta."
            )
        )

        st.markdown(
            "**O que esta pergunta busca avaliar**"
        )

        st.write(
            metadados.get("expectativa", "")
        )


    modo_resposta = st.radio(
        "Como deseja responder?",

        [
            "Escrever resposta",
            "Gravar resposta em áudio"
        ],

        horizontal=True,
    )


    resposta_final = ""


    # --------------------------------------------------------
    # RESPOSTA ESCRITA
    # --------------------------------------------------------

    if modo_resposta == "Escrever resposta":

        resposta_final = st.text_area(
            "Sua resposta",

            placeholder=(
                "Responda como se estivesse diante do recrutador. "
                "Use exemplos reais e detalhes concretos..."
            ),

            height=220,

            key="resposta_texto",
        )


    # --------------------------------------------------------
    # RESPOSTA EM ÁUDIO
    # --------------------------------------------------------

    else:

        st.caption(
            "Grave sua resposta diretamente pelo microfone do dispositivo."
        )

        if hasattr(st, "audio_input"):

            audio = st.audio_input(
                "Gravar resposta"
            )

            if audio is not None:

                st.audio(audio)

                if st.button("Transcrever áudio"):

                    with st.spinner(
                        "Transcrevendo sua resposta..."
                    ):

                        try:

                            st.session_state["audio_transcrito"] = (
                                transcrever_audio(
                                    client,
                                    audio
                                )
                            )

                            st.success(
                                "Transcrição concluída. Revise o texto antes de avaliar."
                            )

                        except Exception as exc:

                            st.error(
                                f"Não foi possível transcrever o áudio: {exc}"
                            )


                if st.session_state.get("audio_transcrito"):

                    resposta_final = st.text_area(
                        "Transcrição para revisão",

                        value=st.session_state["audio_transcrito"],

                        height=180,

                        key="audio_transcrito_editavel",
                    )

        else:

            st.warning(
                "A gravação de áudio exige uma versão recente do Streamlit. "
                "Atualize com: pip install --upgrade streamlit"
            )


    # --------------------------------------------------------
    # AVALIAÇÃO
    # --------------------------------------------------------

    if st.button(
        "Avaliar minha resposta",
        type="primary"
    ):

        if not resposta_final.strip():

            st.warning(
                "Escreva ou grave uma resposta antes de solicitar a avaliação."
            )

        else:

            with st.spinner(
                "Analisando sua resposta em relação à pergunta e à vaga..."
            ):

                try:

                    resultado = avaliar_resposta_com_gemini(
                        client=client,

                        contexto=contexto_completo(),

                        pergunta=pergunta,

                        resposta=resposta_final,

                        metadados=metadados,
                    )


                    st.session_state["ultima_avaliacao"] = (
                        resultado
                    )


                    st.session_state["avaliacoes"].append({

                        "pergunta": pergunta,

                        "resposta": resposta_final,

                        "avaliacao": resultado,

                    })


                    st.session_state["etapa2_concluida"] = True


                    st.success(
                        "Avaliação concluída. A etapa de lapidação foi liberada."
                    )


                except Exception as exc:

                    st.error(
                        f"Erro ao avaliar a resposta: {exc}"
                    )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if st.session_state.get("ultima_avaliacao"):

        st.markdown("---")

        st.markdown(
            "### Parecer do avaliador"
        )

        st.markdown(
            st.session_state["ultima_avaliacao"]
        )


    # --------------------------------------------------------
    # AVANÇAR PARA ETAPA 3
    # --------------------------------------------------------

    if st.session_state["etapa2_concluida"]:

        st.markdown("---")

        if st.button(
            "Avançar para lapidação e feedback"
        ):

            st.session_state["etapa_atual"] = (
                "3. Lapidação e feedback"
            )

            st.rerun()


# ============================================================
# ETAPA 3 — LAPIDAÇÃO E FEEDBACK
# ============================================================

elif st.session_state["etapa_atual"] == "3. Lapidação e feedback":

    st.markdown(
        "### Atelier de lapidação"
    )

    st.markdown(
        """
        <p class='small-muted'>
        Converse com seu mentor de carreira. A IA considera seu contexto,
        currículo, informações da oportunidade e pode pesquisar
        fontes públicas na internet.
        </p>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # CONTEXTO UTILIZADO
    # --------------------------------------------------------

    with st.expander(
        "Contexto utilizado pelo mentor",
        expanded=False
    ):

        ctx = (
            st.session_state.get("contexto_vaga") or {}
        )

        st.write(
            f"**Empresa:** {ctx.get('empresa', '')}"
        )

        st.write(
            f"**Cargo:** {ctx.get('cargo', '')}"
        )

        st.write(
            "**Currículo:** "
            + (
                st.session_state.get("curriculo_nome")
                or "Não anexado"
            )
        )

        st.write(
            "**LinkedIn:** "
            + (
                st.session_state.get("linkedin_url")
                or "Não informado"
            )
        )

        st.caption(
            "O link do LinkedIn é uma referência. "
            "O acesso ao conteúdo do perfil pode ser restrito."
        )


    # --------------------------------------------------------
    # HISTÓRICO DO CHAT
    # --------------------------------------------------------

    for msg in st.session_state["mensagens_chat"]:

        with st.chat_message(msg["role"]):

            st.markdown(
                msg["content"]
            )


    prompt_usuario = st.chat_input(
        "Ex.: Como posso conectar minha experiência aos requisitos desta vaga?"
    )


    # --------------------------------------------------------
    # RESPOSTA DO MENTOR
    # --------------------------------------------------------

    if prompt_usuario:

        st.session_state["mensagens_chat"].append({

            "role": "user",

            "content": prompt_usuario,

        })


        with st.chat_message("user"):

            st.markdown(
                prompt_usuario
            )


        historico = (
            st.session_state["mensagens_chat"][-12:]
        )


        historico_formatado = "\n\n".join(

            f"{'CANDIDATO' if m['role'] == 'user' else 'MENTOR'}: {m['content']}"

            for m in historico

        )


        avaliacoes_anteriores = "\n\n".join(

            [
                f"""
Pergunta: {a['pergunta']}

Resposta: {a['resposta']}

Feedback: {a['avaliacao']}
"""
                for a in st.session_state["avaliacoes"][-3:]
            ]

        ) or "Nenhuma avaliação anterior."


        prompt_chat = f"""

Você é o mentor de carreira do Interview Lab AI.

Você possui experiência em recrutamento,
entrevistas, desenvolvimento profissional
e comunicação executiva.

Use como fontes prioritárias as informações abaixo,
sem inventar dados.

CONTEXTO DO CANDIDATO E DA VAGA:

{contexto_completo()}


AVALIAÇÕES ANTERIORES DA SIMULAÇÃO:

{avaliacoes_anteriores}


HISTÓRICO RECENTE:

{historico_formatado}


MENSAGEM ATUAL:

{prompt_usuario}


INSTRUÇÕES:

1. PERSONALIZAÇÃO

Personalize suas respostas principalmente com base
no currículo e nos dados fornecidos pelo candidato.

Ajude a conectar experiências reais às exigências
da vaga, sem criar experiências ou resultados.


2. PESQUISA NA INTERNET

Quando a pergunta envolver a empresa, a vaga,
o setor, competências exigidas ou práticas de entrevista,
pesquise informações públicas atuais na internet
usando Google Search.

Pesquise também o que recrutadores costumam avaliar
em perguntas desse tipo.

Priorize fontes confiáveis, páginas oficiais da empresa,
descrições de vagas e referências reconhecidas de carreira.


3. LINKEDIN

Se o usuário fornecer um link do LinkedIn,
tente localizar informações públicas indexadas
associadas ao link ou ao perfil.

Deixe claro quando não conseguir acessar
ou confirmar o conteúdo.

Nunca alegue ter lido o perfil se isso não ocorreu.


4. CONFIABILIDADE

Diferencie fatos confirmados, inferências e sugestões.

Não invente dados da empresa.

Não atribua ao candidato competências
que não foram demonstradas.


5. DESENVOLVIMENTO PROFISSIONAL

Se faltarem informações pessoais para uma resposta
mais forte, faça perguntas objetivas.

Ajude o candidato a desenvolver respostas
mais claras, estratégicas e autênticas.


6. COMUNICAÇÃO

Escreva em português, com clareza,
profundidade e tom profissional.

Evite respostas genéricas.

Ao sugerir uma resposta de entrevista,
preserve uma voz natural e autêntica.

"""


        with st.chat_message("assistant"):

            with st.spinner(
                "Analisando o contexto e pesquisando referências públicas..."
            ):

                try:

                    resposta_ia = gerar_conteudo(
                        client,
                        prompt_chat,
                        pesquisar_web=True
                    )


                    st.markdown(
                        resposta_ia
                    )


                    st.session_state["mensagens_chat"].append({

                        "role": "assistant",

                        "content": resposta_ia,

                    })


                except Exception as exc:

                    erro = (
                        "Não foi possível consultar o mentor neste momento: "
                        + str(exc)
                    )

                    st.error(
                        erro
                    )


                    st.session_state["mensagens_chat"].append({

                        "role": "assistant",

                        "content": erro,

                    })


    # --------------------------------------------------------
    # CONTROLES DO CHAT
    # --------------------------------------------------------

    st.markdown("---")

    col_a, col_b = st.columns(
        [1, 1]
    )

    with col_a:

        if st.button(
            "Limpar conversa"
        ):

            st.session_state["mensagens_chat"] = []

            st.rerun()


    with col_b:

        if st.button(
            "Voltar à simulação"
        ):

            st.session_state["etapa_atual"] = (
                "2. Painel de simulação"
            )

            st.rerun()
