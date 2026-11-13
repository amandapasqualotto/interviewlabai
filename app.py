import os
import uuid
import base64
from datetime import datetime
import streamlit as st
from supabase import create_client, Client
from curadoria import PERGUNTAS_CURATORIA
from gemini_engine import get_client, avaliar_resposta_completa, stream_chat_lapidacao

# Leitura opcional de arquivos de currículo
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

ETAPA_1 = "1. Contexto da Vaga"
ETAPA_2 = "2. Painel de Simulação"
ETAPA_3 = "3. Lapidação & Feedback"

# ============================================================
# CONFIGURAÇÃO DE PÁGINA E DESIGN EDITORIAL CLEAN
# ============================================================
st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="icone.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #F8F6F0;
        color: #2C2A29;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        color: #111E16 !important;
        letter-spacing: -0.02em;
    }

    /* Containers com borda */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-color: #E6E1D7 !important;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }

    /* Botão principal */
    .stButton>button {
        background-color: #111E16;
        color: #FBF9F5;
        border: 1px solid #111E16;
        border-radius: 4px;
        padding: 0.65rem 1.4rem;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        width: 100%;
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        background-color: #233A2C;
        border-color: #233A2C;
        color: #FFFFFF;
    }

    /* Contêiner dos botões ocupa a coluna toda (para o alinhamento funcionar) */
    .st-key-btn_toggle_cad,
    .st-key-btn_voltar_login1,
    .st-key-btn_voltar_login2,
    .st-key-btn_logout,
    .st-key-btn_historico {
        width: 100% !important;
        max-width: 100% !important;
    }
    .st-key-btn_toggle_cad div[data-testid="stButton"],
    .st-key-btn_voltar_login1 div[data-testid="stButton"],
    .st-key-btn_voltar_login2 div[data-testid="stButton"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    .st-key-btn_logout div[data-testid="stButton"],
    .st-key-btn_historico div[data-testid="stButton"] {
        display: flex !important;
        justify-content: flex-end !important;
        width: 100% !important;
    }

    /* Botões secundários (cinza) */
    .st-key-btn_toggle_cad button,
    .st-key-btn_voltar_login1 button,
    .st-key-btn_voltar_login2 button {
        background-color: #E6E1D7 !important;
        color: #111E16 !important;
        border: 1px solid #DCD6CD !important;
        width: 260px !important;
        max-width: 100% !important;
    }
    .st-key-btn_historico button {
        background-color: #E6E1D7 !important;
        color: #111E16 !important;
        border: 1px solid #DCD6CD !important;
    }
    .st-key-btn_toggle_cad button:hover,
    .st-key-btn_voltar_login1 button:hover,
    .st-key-btn_voltar_login2 button:hover,
    .st-key-btn_historico button:hover {
        background-color: #DCD6CD !important;
        color: #111E16 !important;
        border-color: #C8C2B7 !important;
    }

    /* Sair da Sessão e Histórico: abaixo do nome, à direita, largura do texto */
    .st-key-btn_logout button,
    .st-key-btn_historico button {
        width: auto !important;
        padding: 0.45rem 1.1rem;
    }

    /* Link 'Esqueci minha senha' */
    .link-esqueci {
        color: #787267;
        font-size: 0.88rem;
        text-decoration: underline;
        cursor: pointer;
        transition: color 0.2s ease;
    }
    .link-esqueci:hover { color: #111E16; }

    /* Campos de entrada */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #FAFAFA;
        border: 1px solid #DCD6CD;
        border-radius: 6px;
        color: #2C2A29;
        font-size: 0.95rem;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #111E16;
        box-shadow: 0 0 0 1px #111E16;
    }

    /* Botões de exclusão (discretos, em tom rosado/vermelho suave) */
    div[class*="st-key-exc_"] button {
        background-color: #F6E7E5 !important;
        color: #8A2E2A !important;
        border: 1px solid #E8C9C5 !important;
    }
    div[class*="st-key-exc_"] button:hover {
        background-color: #F0D5D1 !important;
        border-color: #DDB3AE !important;
    }
    div[class*="st-key-sim_"] button {
        background-color: #8A2E2A !important;
        color: #FFFFFF !important;
        border: 1px solid #8A2E2A !important;
    }
    div[class*="st-key-sim_"] button:hover {
        background-color: #702420 !important;
    }
    div[class*="st-key-nao_"] button {
        background-color: #E6E1D7 !important;
        color: #111E16 !important;
        border: 1px solid #DCD6CD !important;
    }

    .ident-conectado { text-align: right; padding-top: 0.8rem; margin-bottom: 0.4rem; }

    /* ===== Versão para celular / tablet ===== */
    @media (max-width: 768px) {
        /* 16px nos campos evita o zoom automático do iPhone ao digitar */
        .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
    }
    @media (max-width: 640px) {
        .block-container { padding: 2.5rem 1rem 5rem 1rem !important; }
        h3 { font-size: 1.3rem !important; }
        .titulo-login { font-size: 2.2rem !important; }
        .kicker-login { letter-spacing: 1.5px !important; font-size: 0.68rem !important; }
        .titulo-app { font-size: 1.7rem !important; }
        .subtitulo-app { font-size: 0.8rem !important; }
        .ident-conectado { text-align: left !important; padding-top: 0.4rem !important; }
        .st-key-btn_logout div[data-testid="stButton"],
        .st-key-btn_historico div[data-testid="stButton"] { justify-content: flex-start !important; }
        /* alvos de toque maiores */
        .stButton>button { min-height: 46px; }
        div[data-testid="stRadio"] label p { font-size: 0.88rem !important; }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# UTILITÁRIOS
# ============================================================
def extrair_texto_curriculo(uploaded_file):
    if not uploaded_file:
        return ""
    nome = uploaded_file.name.lower()
    texto = ""
    try:
        if nome.endswith(".pdf") and PdfReader:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                texto += page.extract_text() or ""
        elif nome.endswith(".docx") and Document:
            doc = Document(uploaded_file)
            for p in doc.paragraphs:
                texto += p.text + "\n"
        elif nome.endswith(".txt"):
            texto = uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Erro ao ler arquivo do currículo: {e}")
    return texto


def novo_id():
    return uuid.uuid4().hex[:10]


def agora_str():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d/%m/%Y %H:%M")


@st.cache_data
def logo_base64():
    try:
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.png")
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def logo_html(tamanho):
    """Logo circular discreta; se o arquivo não existir, não mostra nada."""
    b64 = logo_base64()
    if not b64:
        return ""
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="width:{tamanho}px;height:{tamanho}px;border-radius:50%;'
        f'box-shadow:0 2px 12px rgba(120,100,90,0.18);opacity:0.95;">'
    )


def parecer_com_pergunta(pergunta, texto):
    """Garante que o parecer exibido comece com a pergunta (inclusive pareceres antigos)."""
    texto = texto or ""
    if texto.lstrip().startswith("**Pergunta:**") or not pergunta:
        return texto
    return f"**Pergunta:** {pergunta}\n\n---\n\n{texto}"


# ============================================================
# CONEXÃO COM SUPABASE & BANCO DE DADOS (COM SUPABASE AUTH + RLS)
# ============================================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Credenciais do Supabase não configuradas nos Secrets.")
        st.stop()
    return create_client(url, key)


supabase = init_supabase()

# Restaura a sessão autenticada do usuário a cada rerun para satisfazer o RLS
session_tokens = st.session_state.get("_sb_tokens")
if session_tokens:
    try:
        supabase.auth.set_session(session_tokens["access_token"], session_tokens["refresh_token"])
    except Exception:
        pass


def buscar_usuario(email):
    try:
        res = supabase.table("usuarios").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def fazer_login_supabase(email, senha):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        if res.user and res.session:
            st.session_state["_sb_tokens"] = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token
            }
            return True
    except Exception:
        pass
    return False


def criar_usuario(nome, email, senha):
    # 1. Cria a conta no Supabase Auth (gera o token JWT para o RLS)
    res = supabase.auth.sign_up({"email": email, "password": senha})
    if res.user:
        if res.session:
            st.session_state["_sb_tokens"] = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token
            }
            supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
        # 2. Insere o perfil na tabela 'usuarios'
        data = {
            "email": email,
            "nome": nome,
            "contexto_vaga": {},
            "avaliacoes": [],
            "mensagens_chat": []
        }
        return supabase.table("usuarios").insert(data).execute()
    return None


def enviar_recuperacao_senha(email):
    return supabase.auth.reset_password_for_email(email)


# ============================================================
# HISTÓRICO (Etapa 1 > Etapa 2 / Etapa 3)
# ============================================================
def vaga_ativa():
    ss = st.session_state
    for v in ss.get("historico", []):
        if v["id"] == ss.get("vaga_ativa_id"):
            return v
    return None


def limpar_vaga_ativa():
    ss = st.session_state
    ss["vaga_ativa_id"] = None
    ss["contexto_vaga"] = {}
    ss["etapa1_concluida"] = False
    ss["etapa2_concluida"] = False
    ss["ultima_pergunta"] = ""
    ss["ultima_avaliacao"] = ""
    ss["ultima_avaliacao_id"] = None
    ss["conversa_ativa_id"] = None
    ss["mensagens_chat"] = []


def definir_vaga_ativa(vaga_id):
    ss = st.session_state
    vaga = next((v for v in ss.get("historico", []) if v["id"] == vaga_id), None)
    if vaga is None:
        limpar_vaga_ativa()
        return
    ss["vaga_ativa_id"] = vaga["id"]
    ss["contexto_vaga"] = dict(vaga["contexto"])
    ss["etapa1_concluida"] = True
    ss["etapa2_concluida"] = bool(vaga["avaliacoes"])
    ultima = vaga["avaliacoes"][-1] if vaga["avaliacoes"] else None
    ss["ultima_pergunta"] = ultima["pergunta"] if ultima else ""
    ss["ultima_avaliacao"] = ultima["avaliacao"] if ultima else ""
    ss["ultima_avaliacao_id"] = ultima["id"] if ultima else None
    conv = vaga["conversas"][-1] if vaga["conversas"] else None
    ss["conversa_ativa_id"] = conv["id"] if conv else None
    ss["mensagens_chat"] = list(conv["mensagens"]) if conv else []


def carregar_sessao(user, email):
    """Carrega os dados do usuário (migrando dados antigos para o novo formato)."""
    ss = st.session_state
    ctx = dict(user.get("contexto_vaga") or {})
    historico = ctx.pop("_historico", None)
    ativa = ctx.pop("_vaga_ativa", None)

    if historico is None:
        historico = []
        avs_db = user.get("avaliacoes") or []
        msgs_db = user.get("mensagens_chat") or []
        if ctx.get("empresa"):
            vaga = {"id": novo_id(), "data": "Anterior", "contexto": ctx, "avaliacoes": [], "conversas": []}
            for a in avs_db:
                vaga["avaliacoes"].append({
                    "id": novo_id(), "data": "Anterior",
                    "pergunta": a.get("pergunta", ""), "resposta": "",
                    "avaliacao": a.get("avaliacao", "")
                })
            if msgs_db:
                ult = vaga["avaliacoes"][-1] if vaga["avaliacoes"] else None
                vaga["conversas"].append({
                    "id": novo_id(),
                    "avaliacao_id": ult["id"] if ult else None,
                    "pergunta": ult["pergunta"] if ult else "Conversa anterior",
                    "data": "Anterior", "mensagens": msgs_db
                })
            historico.append(vaga)
            ativa = vaga["id"]

    ss["usuario_logado"] = email
    ss["usuario_nome"] = user["nome"]
    ss["historico"] = historico
    ids = [v["id"] for v in historico]
    if ativa not in ids:
        ativa = ids[-1] if ids else None
    if ativa:
        definir_vaga_ativa(ativa)
    else:
        limpar_vaga_ativa()
    ss["etapa_radio_main"] = ETAPA_1


def salvar_progresso_banco(email):
    ss = st.session_state
    ctx = dict(ss.get("contexto_vaga", {}))
    ctx["_historico"] = ss.get("historico", [])
    ctx["_vaga_ativa"] = ss.get("vaga_ativa_id")
    vaga = vaga_ativa()
    dados = {
        "contexto_vaga": ctx,
        "avaliacoes": vaga["avaliacoes"] if vaga else [],
        "mensagens_chat": ss.get("mensagens_chat", [])
    }
    try:
        supabase.table("usuarios").update(dados).eq("email", email).execute()
    except Exception as e:
        st.warning(f"Não foi possível salvar seu progresso agora: {e}")


def sincronizar_conversa():
    """Grava as mensagens do chat atual na conversa (Etapa 3) da vaga ativa."""
    ss = st.session_state
    vaga = vaga_ativa()
    if vaga is None:
        return
    conv = next((c for c in vaga["conversas"] if c["id"] == ss.get("conversa_ativa_id")), None)
    if conv is None:
        conv = {
            "id": novo_id(),
            "avaliacao_id": ss.get("ultima_avaliacao_id"),
            "pergunta": ss.get("ultima_pergunta") or "Conversa",
            "data": agora_str(),
            "mensagens": []
        }
        vaga["conversas"].append(conv)
        ss["conversa_ativa_id"] = conv["id"]
    conv["mensagens"] = list(ss.get("mensagens_chat", []))


def ir_para_etapa(nome_etapa):
    """Agenda a troca de etapa; é aplicada no próximo rerun, antes do radio ser criado."""
    st.session_state["_ir_para_etapa"] = nome_etapa
    st.rerun()


def retomar_conversa(vaga_id, conv_id):
    ss = st.session_state
    definir_vaga_ativa(vaga_id)
    vaga = vaga_ativa()
    conv = next((c for c in vaga["conversas"] if c["id"] == conv_id), None)
    if conv:
        ss["conversa_ativa_id"] = conv["id"]
        ss["mensagens_chat"] = list(conv["mensagens"])
        aval = next((a for a in vaga["avaliacoes"] if a["id"] == conv.get("avaliacao_id")), None)
        if aval:
            ss["ultima_pergunta"] = aval["pergunta"]
            ss["ultima_avaliacao"] = aval["avaliacao"]
            ss["ultima_avaliacao_id"] = aval["id"]
    salvar_progresso_banco(ss["usuario_logado"])
    ir_para_etapa(ETAPA_3)


def excluir_vaga(vaga_id):
    ss = st.session_state
    ss["historico"] = [v for v in ss.get("historico", []) if v["id"] != vaga_id]
    era_ativa = ss.get("vaga_ativa_id") == vaga_id
    if era_ativa:
        restante = ss["historico"]
        if restante:
            definir_vaga_ativa(restante[-1]["id"])
        else:
            limpar_vaga_ativa()
    ss.pop("hist_vaga_sel", None)
    salvar_progresso_banco(ss["usuario_logado"])
    return era_ativa


def excluir_avaliacao(vaga_id, aval_id):
    ss = st.session_state
    vaga = next((v for v in ss.get("historico", []) if v["id"] == vaga_id), None)
    if vaga is None:
        return False
    vaga["avaliacoes"] = [a for a in vaga["avaliacoes"] if a["id"] != aval_id]
    afeta = False
    if ss.get("vaga_ativa_id") == vaga_id:
        ss["etapa2_concluida"] = bool(vaga["avaliacoes"])
        if ss.get("ultima_avaliacao_id") == aval_id:
            ult = vaga["avaliacoes"][-1] if vaga["avaliacoes"] else None
            ss["ultima_pergunta"] = ult["pergunta"] if ult else ""
            ss["ultima_avaliacao"] = ult["avaliacao"] if ult else ""
            ss["ultima_avaliacao_id"] = ult["id"] if ult else None
            ss["conversa_ativa_id"] = None
            ss["mensagens_chat"] = []
            afeta = True
    salvar_progresso_banco(ss["usuario_logado"])
    return afeta


def excluir_conversa(vaga_id, conv_id):
    ss = st.session_state
    vaga = next((v for v in ss.get("historico", []) if v["id"] == vaga_id), None)
    if vaga is None:
        return False
    vaga["conversas"] = [c for c in vaga["conversas"] if c["id"] != conv_id]
    afeta = ss.get("vaga_ativa_id") == vaga_id and ss.get("conversa_ativa_id") == conv_id
    if afeta:
        ss["conversa_ativa_id"] = None
        ss["mensagens_chat"] = []
    salvar_progresso_banco(ss["usuario_logado"])
    return afeta


def botao_excluir(chave, aviso, acao):
    """Exclusão em dois passos (Excluir -> Sim, excluir / Cancelar). Use só dentro do diálogo."""
    ss = st.session_state
    if ss.get("_exc_pendente") == chave:
        st.warning(aviso)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sim, excluir", key=f"sim_{chave}"):
                afeta = acao()
                ss["_exc_pendente"] = None
                if afeta:
                    st.rerun()  # muda algo na tela principal: fecha o histórico e atualiza
                else:
                    st.rerun(scope="fragment")  # mantém o histórico aberto
        with c2:
            if st.button("Cancelar", key=f"nao_{chave}"):
                ss["_exc_pendente"] = None
                st.rerun(scope="fragment")
    else:
        if st.button("Excluir", key=f"exc_{chave}"):
            ss["_exc_pendente"] = chave
            st.rerun(scope="fragment")


@st.dialog("Histórico", width="large")
def dialog_historico():
    historico = st.session_state.get("historico", [])
    if not historico:
        st.info("Seu histórico aparecerá aqui assim que você salvar a primeira vaga na Etapa 1.")
        return

    mapa = {v["id"]: v for v in historico}
    ids = [v["id"] for v in reversed(historico)]
    ativa = st.session_state.get("vaga_ativa_id")

    def rotulo(i):
        c = mapa[i]["contexto"]
        txt = f"{c.get('empresa', '?')} — {c.get('cargo', '?')} · {mapa[i].get('data', '')}"
        return txt + ("  (ativa)" if i == ativa else "")

    idx = ids.index(ativa) if ativa in ids else 0
    escolhido = st.selectbox("Vaga (histórico da Etapa 1)", ids, index=idx, format_func=rotulo, key="hist_vaga_sel")
    vaga = mapa[escolhido]

    avs = vaga["avaliacoes"]
    convs = [c for c in vaga["conversas"] if c.get("mensagens")]

    tab1, tab2, tab3 = st.tabs([
        "Etapa 1 — Contexto",
        f"Etapa 2 — Pareceres ({len(avs)})",
        f"Etapa 3 — Conversas ({len(convs)})",
    ])

    with tab1:
        c = vaga["contexto"]
        st.markdown(f"**Empresa:** {c.get('empresa', '')}")
        st.markdown(f"**Cargo:** {c.get('cargo', '')}")
        if c.get("linkedin"):
            st.markdown(f"**LinkedIn:** {c['linkedin']}")
        st.markdown("**Descrição & requisitos da vaga**")
        st.write(c.get("descricao", ""))
        if c.get("sobre_empresa"):
            st.markdown("**Sobre a empresa & cultura**")
            st.write(c["sobre_empresa"])
        if escolhido != ativa:
            if st.button("Usar esta vaga e ir para a Etapa 2", key=f"usar_{escolhido}"):
                definir_vaga_ativa(escolhido)
                salvar_progresso_banco(st.session_state["usuario_logado"])
                ir_para_etapa(ETAPA_2)
        else:
            st.caption("Esta é a vaga ativa no momento.")
        botao_excluir(
            f"vaga_{escolhido}",
            "Excluir esta vaga apaga também todos os pareceres e conversas dela. Essa ação não pode ser desfeita.",
            lambda: excluir_vaga(escolhido),
        )

    with tab2:
        if not avs:
            st.caption("Nenhum parecer gerado para esta vaga ainda.")
        for a in reversed(avs):
            with st.expander(f"{a.get('data', '')} · {a.get('pergunta', '')[:80]}"):
                if a.get("resposta"):
                    st.markdown("**Sua resposta**")
                    st.write(a["resposta"])
                st.markdown("**Parecer**")
                st.markdown(parecer_com_pergunta(a.get("pergunta"), a.get("avaliacao", "")))
                botao_excluir(
                    f"aval_{a['id']}",
                    "Excluir este parecer? Essa ação não pode ser desfeita.",
                    lambda aid=a["id"]: excluir_avaliacao(escolhido, aid),
                )

    with tab3:
        if not convs:
            st.caption("Nenhuma conversa com o mentor para esta vaga ainda.")
        for cv in reversed(convs):
            n = len(cv["mensagens"])
            with st.expander(f"{cv.get('data', '')} · {cv.get('pergunta', '')[:80]} ({n} msgs)"):
                for m in cv["mensagens"]:
                    with st.chat_message(m["role"]):
                        st.markdown(m["content"])
                if st.button("Retomar esta conversa", key=f"ret_{cv['id']}"):
                    retomar_conversa(escolhido, cv["id"])
                botao_excluir(
                    f"conv_{cv['id']}",
                    "Excluir esta conversa? Essa ação não pode ser desfeita.",
                    lambda cid=cv["id"]: excluir_conversa(escolhido, cid),
                )


# ============================================================
# TELA DE AUTENTICAÇÃO
# ============================================================
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

if not st.session_state["usuario_logado"]:
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0 1.5rem 0;">
        <div style="margin-bottom: 1.1rem;">{logo_html(88)}</div>
        <p class="kicker-login" style="letter-spacing: 3px; font-size: 0.8rem; text-transform: uppercase; color: #787267; font-weight: 600;">— Plataforma de Treinamento para Entrevista —</p>
        <h1 class="titulo-login" style="font-size: 3.2rem; font-style: italic; margin-top: 0.2rem; margin-bottom: 0;">Interview Lab AI</h1>
    </div>
    """, unsafe_allow_html=True)

    col_centered = st.columns([1, 1.2, 1])[1]
    with col_centered:

        # MODO 1: LOGIN
        if st.session_state["auth_mode"] == "login":
            email = st.text_input("E-mail profissional", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")

            st.write("")
            if st.button("Entrar na Conta ➔", key="btn_login"):
                if fazer_login_supabase(email, senha):
                    user = buscar_usuario(email)
                    if user:
                        carregar_sessao(user, email)
                        st.rerun()
                    else:
                        st.error("Perfil de usuário não encontrado na base.")
                else:
                    st.error("E-mail ou senha incorretos.")

            st.markdown("""
            <div style="text-align: center; margin-top: 0.8rem;">
                <a href="?recuperar=true" target="_self" class="link-esqueci">Esqueci minha senha</a>
            </div>
            """, unsafe_allow_html=True)

            if st.query_params.get("recuperar") == "true":
                st.query_params.clear()
                st.session_state["auth_mode"] = "recuperar"
                st.rerun()

            st.markdown("""
            <div style="margin: 2rem 0 0.5rem 0; text-align: center;">
                <hr style="border: none; border-top: 1px solid #E6E1D7; margin-bottom: 1.5rem;">
                <p style="font-size: 0.88rem; color: #787267; margin-bottom: 0.4rem;">Ainda não possui um acesso?</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Criar nova conta", key="btn_toggle_cad"):
                st.session_state["auth_mode"] = "cadastro"
                st.rerun()

        # MODO 2: CRIAR CONTA
        elif st.session_state["auth_mode"] == "cadastro":
            st.markdown("<h3 style='text-align: center; margin-bottom: 1.5rem; font-size: 1.6rem;'>Criar nova conta</h3>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome completo", key="cad_nome")
            novo_email = st.text_input("E-mail profissional", key="cad_email")
            nova_senha = st.text_input("Defina uma senha (mín. 6 caracteres)", type="password", key="cad_senha")

            st.write("")
            if st.button("Finalizar Cadastro e Acessar ➔", key="btn_cadastrar"):
                if novo_email and nova_senha and novo_nome:
                    if len(nova_senha) < 6:
                        st.warning("A senha deve ter pelo menos 6 caracteres.")
                    else:
                        try:
                            criar_usuario(novo_nome, novo_email, nova_senha)
                            st.session_state["usuario_logado"] = novo_email
                            st.session_state["usuario_nome"] = novo_nome
                            st.session_state["historico"] = []
                            limpar_vaga_ativa()
                            st.session_state["etapa_radio_main"] = ETAPA_1
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Não foi possível criar a conta (verifique se o e-mail já existe): {e}")
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

            st.write("")
            if st.button("Voltar ao Login", key="btn_voltar_login1"):
                st.session_state["auth_mode"] = "login"
                st.rerun()

        # MODO 3: REDEFINIR SENHA
        elif st.session_state["auth_mode"] == "recuperar":
            st.markdown("<h3 style='text-align: center; margin-bottom: 0.5rem; font-size: 1.5rem;'>Recuperar Senha</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.88rem; color: #6B655C; margin-bottom: 1.5rem;'>Informe seu e-mail cadastrado para receber o link de redefinição.</p>", unsafe_allow_html=True)

            email_recup = st.text_input("E-mail cadastrado", key="recup_email")

            st.write("")
            if st.button("Enviar Link de Recuperação ➔", key="btn_confirmar_recup"):
                if not email_recup:
                    st.warning("Informe seu e-mail.")
                else:
                    try:
                        enviar_recuperacao_senha(email_recup)
                        st.success("Se o e-mail estiver cadastrado, enviamos um link de redefinição para sua caixa de entrada.")
                    except Exception as e:
                        st.error(f"Erro ao solicitar recuperação: {e}")

            st.write("")
            if st.button("Voltar ao Login", key="btn_voltar_login2"):
                st.session_state["auth_mode"] = "login"
                st.rerun()

    st.stop()

# ============================================================
# CABEÇALHO & IDENTIDADE LOGADA
# ============================================================
col_head1, col_head2 = st.columns([4, 1.4])
with col_head1:
    st.markdown(f"""
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 16px; padding: 0.5rem 0 0.2rem 0;">
        {logo_html(60)}
        <div>
            <h1 class="titulo-app" style="font-size: 2.3rem; margin-bottom: 0px;">Interview Lab AI</h1>
            <p class="subtitulo-app" style="color: #787267; font-size: 0.95rem; margin-top: -4px;">Laboratório de Simulação e Lapidação Narrativa para Entrevistas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_head2:
    st.markdown(
        f"<div class='ident-conectado'>"
        f"<span style='font-size: 0.85rem; color: #787267;'>Candidato Conectado</span><br>"
        f"<b>{st.session_state.get('usuario_nome', 'Candidato')}</b></div>",
        unsafe_allow_html=True
    )
    if st.button("Sair da Sessão", key="btn_logout"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.rerun()
    if st.button("Histórico", key="btn_historico"):
        st.session_state["_exc_pendente"] = None
        dialog_historico()

st.markdown("<hr style='border: none; border-top: 1px solid #E6E1D7; margin: 0.8rem 0 1.5rem 0;'>", unsafe_allow_html=True)

# Validação do Cliente Gemini
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.warning("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = get_client(api_key)

# ============================================================
# GERENCIAMENTO DAS ETAPAS (navegação automática)
# ============================================================
etapas_lista = [ETAPA_1]
if st.session_state.get("etapa1_concluida"):
    etapas_lista.append(ETAPA_2)
if st.session_state.get("etapa2_concluida"):
    etapas_lista.append(ETAPA_3)

destino = st.session_state.pop("_ir_para_etapa", None)
if destino in etapas_lista:
    st.session_state["etapa_radio_main"] = destino

if st.session_state.get("etapa_radio_main") not in etapas_lista:
    st.session_state["etapa_radio_main"] = etapas_lista[0]

etapa_atual = st.radio(
    "Navegação por Etapas:",
    options=etapas_lista,
    horizontal=True,
    key="etapa_radio_main"
)

# ============================================================
# ETAPA 1 — CONTEXTO DA VAGA
# ============================================================
if etapa_atual == ETAPA_1:
    st.markdown("<h3>Etapa 1 — Contexto da Vaga & Perfil</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B655C; font-size: 0.92rem; margin-bottom: 1.5rem;'>Insira os detalhes estratégicos do cargo pretendido. A IA utilizará esses dados para personalizar a avaliação.</p>", unsafe_allow_html=True)

    ctx = st.session_state.get("contexto_vaga", {})

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        empresa = st.text_input("Empresa Alvo", value=ctx.get("empresa", ""), placeholder="Ex: Google, Itaú, Ambev...")
        linkedin = st.text_input("Perfil do LinkedIn (Opcional)", value=ctx.get("linkedin", ""), placeholder="https://linkedin.com/in/seu-perfil")
    with col2:
        cargo = st.text_input("Cargo Desejado", value=ctx.get("cargo", ""), placeholder="Ex: Gerente de Produto, Tech Lead...")
        curriculo_file = st.file_uploader("Upload de Currículo (PDF, DOCX)", type=["pdf", "docx", "txt"])

    descricao = st.text_area("Descrição & Requisitos da Vaga", value=ctx.get("descricao", ""), height=120, placeholder="Cole aqui os principais requisitos e responsabilidades do anúncio...")
    sobre_empresa = st.text_area("Sobre a Empresa & Cultura (Opcional)", value=ctx.get("sobre_empresa", ""), height=90, placeholder="Valores, momento de mercado, novos projetos...")

    if st.button("Salvar Contexto e Avançar para Etapa 2 ➔", key="btn_salvar_e1"):
        if not empresa or not cargo or not descricao:
            st.warning("Preencha pelo menos a Empresa, Cargo e Descrição da Vaga.")
        else:
            curriculo_texto = extrair_texto_curriculo(curriculo_file) if curriculo_file else ctx.get("curriculo_texto", "")
            novo_ctx = {
                "empresa": empresa,
                "cargo": cargo,
                "descricao": descricao,
                "sobre_empresa": sobre_empresa,
                "linkedin": linkedin,
                "curriculo_texto": curriculo_texto
            }

            vaga = vaga_ativa()
            mesma_vaga = (
                vaga is not None
                and vaga["contexto"].get("empresa", "").strip().lower() == empresa.strip().lower()
                and vaga["contexto"].get("cargo", "").strip().lower() == cargo.strip().lower()
            )
            if mesma_vaga:
                # Mesma empresa e cargo: só atualiza os dados (mantém pareceres e conversas)
                vaga["contexto"] = novo_ctx
                st.session_state["contexto_vaga"] = novo_ctx
            else:
                # Vaga nova: cria um novo registro no histórico
                nova = {"id": novo_id(), "data": agora_str(), "contexto": novo_ctx, "avaliacoes": [], "conversas": []}
                st.session_state.setdefault("historico", []).append(nova)
                definir_vaga_ativa(nova["id"])

            salvar_progresso_banco(st.session_state["usuario_logado"])
            ir_para_etapa(ETAPA_2)

# ============================================================
# ETAPA 2 — PAINEL DE SIMULAÇÃO
# ============================================================
elif etapa_atual == ETAPA_2:
    col_nav1, _ = st.columns([1.5, 4])
    with col_nav1:
        if st.button("⬅ Voltar para Contexto da Vaga", key="btn_voltar_e1"):
            ir_para_etapa(ETAPA_1)

    st.markdown("<h3>Etapa 2 — Simulação & Avaliação Técnica</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B655C; font-size: 0.92rem; margin-bottom: 1.5rem;'>Selecione uma pergunta técnica ou comportamental e responda via texto ou áudio.</p>", unsafe_allow_html=True)

    lista_perguntas = list(PERGUNTAS_CURATORIA.keys())
    pergunta_selecionada = st.selectbox("Escolha a Pergunta para Simular:", options=lista_perguntas)
    dados_pergunta = PERGUNTAS_CURATORIA[pergunta_selecionada]

    st.markdown(f"""
    <div style="background-color: #FAFAFA; border: 1px solid #E6E1D7; padding: 14px 18px; border-radius: 6px; margin: 10px 0 20px 0;">
        <span style="font-size: 0.85rem; color: #111E16; font-weight: 700;">METODOLOGIA SUGERIDA:</span> <span style="font-size: 0.88rem; color: #4A453E;">{dados_pergunta['tecnica']}</span><br>
        <span style="font-size: 0.85rem; color: #111E16; font-weight: 700;">FOCO DO AVALIADOR:</span> <span style="font-size: 0.88rem; color: #4A453E;">{dados_pergunta['expectativa']}</span>
    </div>
    """, unsafe_allow_html=True)

    tipo_resposta = st.radio("Formato da Resposta:", ["Texto", "Áudio"], horizontal=True, key="tipo_resp_radio")

    resposta_texto = None
    audio_bytes = None

    if tipo_resposta == "Texto":
        resposta_texto = st.text_area("Sua Resposta:", placeholder="Desenvolva sua resposta utilizando a técnica sugerida...", height=180)
    else:
        st.markdown("<label style='font-size: 0.9rem; font-weight: 600;'>Grave a sua resposta:</label>", unsafe_allow_html=True)
        audio_input = st.audio_input("Gravador de voz")
        if audio_input:
            audio_bytes = audio_input.read()

    if st.button("Enviar e Avaliar ➔", key="btn_avaliar_e2"):
        if not resposta_texto and not audio_bytes:
            st.warning("Por favor, forneça uma resposta em texto ou grave um áudio.")
        else:
            with st.spinner("Analisando alinhamento estratégico"):
                resultado = avaliar_resposta_completa(
                    client=client,
                    contexto=st.session_state.get("contexto_vaga", {}),
                    pergunta=pergunta_selecionada,
                    dados_pergunta=dados_pergunta,
                    resposta_texto=resposta_texto,
                    audio_bytes=audio_bytes
                )

            if resultado.startswith("Não foi possível obter resposta"):
                # Falhas não entram no histórico
                st.error(resultado)
            else:
                # A pergunta vai dentro do parecer (de propósito), para copiar/imprimir completo
                resultado = f"**Pergunta:** {pergunta_selecionada}\n\n---\n\n{resultado}"

                vaga = vaga_ativa()
                aval = {
                    "id": novo_id(),
                    "data": agora_str(),
                    "pergunta": pergunta_selecionada,
                    "resposta": (resposta_texto or "").strip() or "[Resposta enviada em áudio]",
                    "avaliacao": resultado
                }
                if vaga is not None:
                    vaga["avaliacoes"].append(aval)

                st.session_state["ultima_pergunta"] = pergunta_selecionada
                st.session_state["ultima_avaliacao"] = resultado
                st.session_state["ultima_avaliacao_id"] = aval["id"]
                # Um novo parecer abre uma conversa nova na Etapa 3 (a anterior fica no histórico)
                st.session_state["conversa_ativa_id"] = None
                st.session_state["mensagens_chat"] = []
                st.session_state["etapa2_concluida"] = True
                salvar_progresso_banco(st.session_state["usuario_logado"])
                st.rerun()

    if st.session_state.get("ultima_avaliacao"):
        with st.container(border=True):
            st.markdown("### Último Parecer Técnico Gerado")
            st.markdown(parecer_com_pergunta(st.session_state.get("ultima_pergunta"), st.session_state["ultima_avaliacao"]))

        if st.button("Avançar para Etapa 3 ➔", key="btn_avancar_e3"):
            ir_para_etapa(ETAPA_3)

# ============================================================
# ETAPA 3 — LAPIDAÇÃO & FEEDBACK
# ============================================================
elif etapa_atual == ETAPA_3:
    col_nav1, _ = st.columns([1.5, 4])
    with col_nav1:
        if st.button("⬅ Voltar para Simulação", key="btn_voltar_e2"):
            ir_para_etapa(ETAPA_2)

    st.markdown("<h3>Etapa 3 — Atelier de Lapidação Narrativa</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B655C; font-size: 0.92rem; margin-bottom: 1.5rem;'>Converse com o mentor de inteligência para ajustar métricas, storytelling e pesquisar tendências da empresa no mercado em tempo real.</p>", unsafe_allow_html=True)

    if st.session_state.get("ultima_pergunta"):
        st.caption(f"Conversando sobre: {st.session_state['ultima_pergunta']}")

    if "mensagens_chat" not in st.session_state:
        st.session_state["mensagens_chat"] = []

    for msg in st.session_state["mensagens_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt_usuario = st.chat_input("Ex: Como posso destacar minha experiência com liderança nessa resposta?")
    if prompt_usuario:
        st.session_state["mensagens_chat"].append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user"):
            st.markdown(prompt_usuario)

        with st.chat_message("assistant"):
            resposta_ia = st.write_stream(
                stream_chat_lapidacao(
                    client=client,
                    historico_mensagens=st.session_state["mensagens_chat"],
                    contexto_vaga=st.session_state.get("contexto_vaga", {}),
                    pergunta=st.session_state.get("ultima_pergunta", "Pergunta Comportamental"),
                    parecer_anterior=st.session_state.get("ultima_avaliacao", "")
                )
            )

        if str(resposta_ia).startswith("Não foi possível gerar a resposta do chat"):
            # Falha: não salva, para você poder tentar de novo
            st.session_state["mensagens_chat"].pop()
        else:
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": resposta_ia})
            sincronizar_conversa()
            salvar_progresso_banco(st.session_state["usuario_logado"])
