import os
import io
import streamlit as st
from google import genai
from supabase import create_client, Client
from curadoria import PERGUNTAS_CURATORIA
from gemini_engine import get_client, avaliar_resposta_completa, simular_chat_lapidacao_com_busca

# Leitura opcional de arquivos de currículo
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

# ============================================================
# CONFIGURAÇÃO DE PÁGINA E CSS EDITORIAL
# ============================================================
st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

    .stApp {
        background-color: #FBF9F5;
        color: #2C2A29;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    h1, h2, h3, h4, .editorial-title {
        font-family: 'Playfair Display', serif;
        color: #1E3023;
        font-weight: 700;
    }

    .editorial-card {
        background-color: #F4F1EA;
        border: 1px solid #E3DED4;
        padding: 24px;
        border-radius: 4px;
        margin-bottom: 20px;
    }

    .stButton>button {
        background-color: #1E3023;
        color: #FBF9F5;
        border: none;
        border-radius: 2px;
        padding: 0.6rem 1.2rem;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 500;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2C4233;
        color: #FFFFFF;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #FFFFFF;
        border: 1px solid #DCD6CD;
        border-radius: 2px;
        color: #2C2A29;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Helper para ler arquivo de currículo
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

# ============================================================
# CONEXÃO COM SUPABASE & BANC0 DE DADOS
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

def buscar_usuario(email):
    try:
        res = supabase.table("usuarios").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def criar_usuario(nome, email, senha):
    data = {"email": email, "nome": nome, "senha": senha}
    return supabase.table("usuarios").insert(data).execute()

def salvar_progresso_banco(email):
    dados_atualizados = {
        "contexto_vaga": st.session_state.get("contexto_vaga", {}),
        "avaliacoes": st.session_state.get("avaliacoes", []),
        "mensagens_chat": st.session_state.get("mensagens_chat", [])
    }
    supabase.table("usuarios").update(dados_atualizados).eq("email", email).execute()

# ============================================================
# TELA DE LOGIN / CADASTRO (AUTENTICAÇÃO)
# ============================================================
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if not st.session_state["usuario_logado"]:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <p style="letter-spacing: 3px; font-size: 0.85rem; text-transform: uppercase; color: #5A655D;">— Atelier de Carreiras & Simulações —</p>
        <h1 style="font-size: 2.8rem; font-style: italic;">Interview Lab AI</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col_centered = st.columns([1, 2, 1])[1]
    with col_centered:
        aba_auth1, aba_auth2 = st.tabs(["Entrar na minha conta", "Criar nova conta"])
        
        with aba_auth1:
            email = st.text_input("E-mail", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            if st.button("Entrar na minha conta ➔"):
                user = buscar_usuario(email)
                if user and user["senha"] == senha:
                    st.session_state["usuario_logado"] = email
                    st.session_state["usuario_nome"] = user["nome"]
                    # Restaura histórico do banco de dados
                    st.session_state["contexto_vaga"] = user.get("contexto_vaga") or {}
                    st.session_state["avaliacoes"] = user.get("avaliacoes") or []
                    st.session_state["mensagens_chat"] = user.get("mensagens_chat") or []
                    
                    st.session_state["etapa1_concluida"] = bool(st.session_state["contexto_vaga"].get("empresa"))
                    st.session_state["etapa2_concluida"] = len(st.session_state["avaliacoes"]) > 0
                    
                    st.success(f"Bem-vindo(a) de volta, {user['nome']}!")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
                    
        with aba_auth2:
            novo_nome = st.text_input("Nome completo", key="cad_nome")
            novo_email = st.text_input("E-mail", key="cad_email")
            nova_senha = st.text_input("Senha", type="password", key="cad_senha")
            if st.button("Cadastrar e Acessar"):
                if buscar_usuario(novo_email):
                    st.warning("Este e-mail já está cadastrado.")
                elif novo_email and nova_senha and novo_nome:
                    criar_usuario(novo_nome, novo_email, nova_senha)
                    st.session_state["usuario_logado"] = novo_email
                    st.session_state["usuario_nome"] = novo_nome
                    st.session_state["etapa1_concluida"] = False
                    st.session_state["etapa2_concluida"] = False
                    st.success("Conta criada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos.")

    st.stop()

# ============================================================
# CABEÇALHO DA APLICAÇÃO LOGADA
# ============================================================
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown("""
    <div style="padding: 1rem 0 0.5rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">Interview Lab AI</h1>
        <p style="color: #6C665F; font-size: 0.95rem;">Um espaço refinado para estruturar respostas e lapidar sua narrativa profissional.</p>
    </div>
    """, unsafe_allow_html=True)
with col_head2:
    st.markdown(f"<p style='text-align: right; padding-top: 1.5rem;'>👤 <b>{st.session_state.get('usuario_nome', 'Candidato')}</b></p>", unsafe_allow_html=True)
    if st.button("Sair / Logout"):
        st.session_state.clear()
        st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid #E3DED4; margin: 1rem 0;'>", unsafe_allow_html=True)

# Chave API Gemini
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.warning("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = get_client(api_key)

# ============================================================
# NAVEGAÇÃO PROGRESSIVA (SEM EMOJIS, DESBLOQUEIO CONDICIONAL)
# ============================================================
etapas_disponiveis = ["1. Contexto da Vaga"]
if st.session_state.get("etapa1_concluida"):
    etapas_disponiveis.append("2. Painel de Simulação")
if st.session_state.get("etapa2_concluida"):
    etapas_disponiveis.append("3. Lapidação & Feedback")

etapa_selecionada = st.radio(
    "Etapas de Preparação:",
    options=etapas_disponiveis,
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)

# ============================================================
# ETAPA 1 — CONTEXTO DA VAGA
# ============================================================
if etapa_selecionada == "1. Contexto da Vaga":
    st.markdown("### Defina o Contexto da Vaga")
    st.markdown("<p style='color: #6C665F;'>Insira os detalhes da empresa, cargo e suas informações opcionais de perfil.</p>", unsafe_allow_html=True)
    
    ctx = st.session_state.get("contexto_vaga", {})
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        empresa = st.text_input("Nome da Empresa Alvo", value=ctx.get("empresa", ""), placeholder="Ex: Google, Banco ABC...")
        linkedin = st.text_input("Link do LinkedIn (Opcional)", value=ctx.get("linkedin", ""), placeholder="Ex: https://linkedin.com/in/seu-perfil")
    with col2:
        cargo = st.text_input("Cargo / Posição Desejada", value=ctx.get("cargo", ""), placeholder="Ex: Product Manager, Analista...")
        curriculo_file = st.file_uploader("Anexar Currículo (Opcional - PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    descricao = st.text_area("Descrição e Requisitos da Vaga", value=ctx.get("descricao", ""), placeholder="Cole os requisitos exigidos pela vaga...")
    sobre_empresa = st.text_area("Sobre a empresa (descrição, cultura, valores, etc)", value=ctx.get("sobre_empresa", ""), placeholder="Ex: Foco em inovação, autonomia, foco em clientes...")

    if st.button("Salvar Contexto e Avançar ➔"):
        if not empresa or not cargo or not descricao:
            st.warning("Preencha pelo menos Nome da Empresa, Cargo e Descrição da vaga.")
        else:
            curriculo_texto = extrair_texto_curriculo(curriculo_file) if curriculo_file else ctx.get("curriculo_texto", "")
            
            st.session_state["contexto_vaga"] = {
                "empresa": empresa,
                "cargo": cargo,
                "descricao": descricao,
                "sobre_empresa": sobre_empresa,
                "linkedin": linkedin,
                "curriculo_texto": curriculo_texto
            }
            st.session_state["etapa1_concluida"] = True
            salvar_progresso_banco(st.session_state["usuario_logado"])
            st.success("Contexto salvo no banco de dados! Etapa 2 liberada.")
            st.rerun()

# ============================================================
# ETAPA 2 — PAINEL DE SIMULAÇÃO
# ============================================================
elif etapa_selecionada == "2. Painel de Simulação":
    st.markdown("### Simulação de Pergunta & Resposta")
    st.markdown("<p style='color: #6C665F;'>Escolha uma pergunta da curadoria e responda por texto ou gravando um áudio.</p>", unsafe_allow_html=True)
    
    lista_perguntas = list(PERGUNTAS_CURATORIA.keys())
    pergunta_selecionada = st.selectbox("Selecione a pergunta para simular:", options=lista_perguntas)
    
    dados_pergunta = PERGUNTAS_CURATORIA[pergunta_selecionada]
    
    st.markdown(f"""
    <div class="editorial-card" style="padding: 14px; margin-top: 10px;">
        <small><b>Técnica Sugerida:</b> {dados_pergunta['tecnica']}</small><br>
        <small><b>Expectativa do Avaliador:</b> {dados_pergunta['expectativa']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    tipo_resposta = st.radio("Formato da Resposta:", ["Texto", "Áudio"], horizontal=True)
    
    resposta_texto = None
    audio_bytes = None
    
    if tipo_resposta == "Texto":
        resposta_texto = st.text_area("Sua Resposta:", placeholder="Estruture sua resposta...", height=180)
    else:
        st.markdown("<label>Grave sua resposta em áudio:</label>", unsafe_allow_html=True)
        audio_input = st.audio_input("Clique para gravar")
        if audio_input:
            audio_bytes = audio_input.read()

    if st.button("Enviar e Avaliar Resposta ➔"):
        if not resposta_texto and not audio_bytes:
            st.warning("Por favor, digite a resposta ou grave um áudio para prosseguir.")
        else:
            with st.spinner("Analisando com critérios de curadoria e inteligência de mercado..."):
                resultado = avaliar_resposta_completa(
                    client=client,
                    contexto=st.session_state.get("contexto_vaga", {}),
                    pergunta=pergunta_selecionada,
                    dados_pergunta=dados_pergunta,
                    resposta_texto=resposta_texto,
                    audio_bytes=audio_bytes
                )
                
                st.session_state["ultima_pergunta"] = pergunta_selecionada
                st.session_state["ultima_avaliacao"] = resultado
                
                if "avaliacoes" not in st.session_state:
                    st.session_state["avaliacoes"] = []
                st.session_state["avaliacoes"].append({
                    "pergunta": pergunta_selecionada,
                    "avaliacao": resultado
                })
                
                st.session_state["etapa2_concluida"] = True
                salvar_progresso_banco(st.session_state["usuario_logado"])
                
            st.markdown("---")
            st.markdown("### Parecer Técnico do Avaliador")
            st.markdown(resultado)

# ============================================================
# ETAPA 3 — LAPIDAÇÃO & FEEDBACK
# ============================================================
elif etapa_selecionada == "3. Lapidação & Feedback":
    st.markdown("### Atelier de Lapidação (Chat com IA)")
    st.markdown("<p style='color: #6C665F;'>Refine pontos específicos, solicite reescritas e tire dúvidas com pesquisa em tempo real na web.</p>", unsafe_allow_html=True)
    
    if "mensagens_chat" not in st.session_state:
        st.session_state["mensagens_chat"] = []
        
    for msg in st.session_state["mensagens_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    prompt_usuario = st.chat_input("Ex: Como posso resumir essa resposta para caber em 2 minutos?")
    if prompt_usuario:
        st.session_state["mensagens_chat"].append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
            
        with st.spinner("Pesquisando dados adicionais na web e lapidando resposta..."):
            resposta_ia = simular_chat_lapidacao_com_busca(
                client=client,
                historico_mensagens=st.session_state["mensagens_chat"],
                contexto_vaga=st.session_state.get("contexto_vaga", {}),
                pergunta=st.session_state.get("ultima_pergunta", "Pergunta Comportamental"),
                parecer_anterior=st.session_state.get("ultima_avaliacao", "")
            )
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": resposta_ia})
            salvar_progresso_banco(st.session_state["usuario_logado"])
            with st.chat_message("assistant"):
                st.markdown(resposta_ia)
