import os
import io
import streamlit as st
from google import genai
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

    .login-box {
        max-width: 450px;
        margin: 40px auto;
        padding: 30px;
        background: #FFFFFF;
        border: 1px solid #E3DED4;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
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
# GERENCIAMENTO DE SESSÃO & AUTENTICAÇÃO
# ============================================================
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {}  # Simulando base Supabase/Firebase

if "etapa1_concluida" not in st.session_state:
    st.session_state["etapa1_concluida"] = False
if "etapa2_concluida" not in st.session_state:
    st.session_state["etapa2_concluida"] = False

# --- TELA DE LOGIN / CADASTRO (Estilo ChatGPT / Atelier) ---
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
                if email in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][email]["senha"] == senha:
                    st.session_state["usuario_logado"] = email
                    st.success("Bem-vindo(a) de volta!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Tente novamente ou crie uma conta.")
                    
        with aba_auth2:
            novo_nome = st.text_input("Nome completo", key="cad_nome")
            novo_email = st.text_input("E-mail", key="cad_email")
            nova_senha = st.text_input("Senha", type="password", key="cad_senha")
            if st.button("Cadastrar e Acessar"):
                if novo_email in st.session_state["usuarios_db"]:
                    st.warning("Este e-mail já está cadastrado.")
                elif novo_email and nova_senha:
                    st.session_state["usuarios_db"][novo_email] = {
                        "nome": novo_nome,
                        "senha": nova_senha,
                        "historico": []
                    }
                    st.session_state["usuario_logado"] = novo_email
                    st.success("Conta criada com sucesso!")
                    st.rerun()

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
    st.markdown(f"<p style='text-align: right; padding-top: 1.5rem;'>👤 {st.session_state['usuario_logado']}</p>", unsafe_allow_html=True)
    if st.button("Sair / Logout"):
        st.session_state["usuario_logado"] = None
        st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid #E3DED4; margin: 1rem 0;'>", unsafe_allow_html=True)

# Chave API
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.warning("Chave GEMINI_API_KEY não configurada nos Secrets ou variáveis de ambiente.")
    st.stop()

client = get_client(api_key)

# ============================================================
# NAVEGAÇÃO PROGRESSIVA (SEM EMOJIS, CONDICIONAL)
# ============================================================
etapas_disponiveis = ["1. Contexto da Vaga"]
if st.session_state["etapa1_concluida"]:
    etapas_disponiveis.append("2. Painel de Simulação")
if st.session_state["etapa2_concluida"]:
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
        curriculo_texto = extrair_texto_curriculo(curriculo_file) if curriculo_file else ctx.get("curriculo_texto", "")
        
        st.session_state["contexto_vaga"] = {
            "empresa": empresa if empresa else "Empresa Alvo",
            "cargo": cargo if cargo else "Cargo Desejado",
            "descricao": descricao,
            "sobre_empresa": sobre_empresa,
            "linkedin": linkedin,
            "curriculo_texto": curriculo_texto
        }
        st.session_state["etapa1_concluida"] = True
        st.success("Contexto salvo com sucesso! Etapa 2 liberada.")
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
    
    # Exibe box discreto com expectativas técnicas
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
                st.session_state["etapa2_concluida"] = True
                
            st.markdown("---")
            st.markdown("### Parecer Técnico do Avaliador")
            st.markdown(resultado)

# ============================================================
# ETAPA 3 — LAPIDAÇÃO & FEEDBACK (CHAT COM SEARCH GROUNDING)
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
            with st.chat_message("assistant"):
                st.markdown(resposta_ia)
