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
# CONFIGURAÇÃO DE PÁGINA E DESIGN EDITORIAL CLEAN
# ============================================================
st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="🎯",
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

    /* Cartão Editorial Elevado */
    .editorial-card {
        background-color: #FFFFFF;
        border: 1px solid #E6E1D7;
        padding: 28px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        margin-bottom: 24px;
    }

    /* Estilização Botão Principal */
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

    /* Customização do Esqueci minha senha (Totalmente sem caixa, fundo ou borda) */
    div[element-id*="btn_toggle_recup"] button, 
    div[data-testid="stButton"] button:has(div:contains("Esqueci minha senha")) {
        background-color: transparent !important;
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        color: #787267 !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        text-decoration: underline !important;
        padding: 0 !important;
        margin: 0.5rem auto !important;
        display: block !important;
        width: auto !important;
    }
    div[element-id*="btn_toggle_recup"] button:hover,
    div[data-testid="stButton"] button:has(div:contains("Esqueci minha senha")):hover {
        color: #111E16 !important;
        background: transparent !important;
    }

    /* Customização do Botão Criar nova conta (Fundo cinza claro, texto escuro e centralizado) */
    div[element-id*="btn_toggle_cad"] button,
    div[data-testid="stButton"] button:has(div:contains("Criar nova conta")) {
        background-color: #E6E1D7 !important;
        color: #111E16 !important;
        border: 1px solid #DCD6CD !important;
        max-width: 280px !important;
        margin: 0 auto !important;
        display: block !important;
    }
    div[element-id*="btn_toggle_cad"] button:hover,
    div[data-testid="stButton"] button:has(div:contains("Criar nova conta")):hover {
        background-color: #DCD6CD !important;
        color: #111E16 !important;
        border-color: #C8C2B7 !important;
    }

    /* Campos de Entrada */
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
# CONEXÃO COM SUPABASE & BANCO DE DADOS
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

def atualizar_senha_usuario(email, nova_senha):
    return supabase.table("usuarios").update({"senha": nova_senha}).eq("email", email).execute()

def salvar_progresso_banco(email):
    dados_atualizados = {
        "contexto_vaga": st.session_state.get("contexto_vaga", {}),
        "avaliacoes": st.session_state.get("avaliacoes", []),
        "mensagens_chat": st.session_state.get("mensagens_chat", [])
    }
    supabase.table("usuarios").update(dados_atualizados).eq("email", email).execute()

# ============================================================
# TELA DE AUTENTICAÇÃO LIMPA E ALINHADA
# ============================================================
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

if not st.session_state["usuario_logado"]:
    st.markdown("""
    <div style="text-align: center; padding: 2.5rem 0 1.5rem 0;">
        <p style="letter-spacing: 3px; font-size: 0.8rem; text-transform: uppercase; color: #787267; font-weight: 600;">— Plataforma de Treinamento para Entrevista —</p>
        <h1 style="font-size: 3.2rem; font-style: italic; margin-top: 0.2rem; margin-bottom: 0;">Interview Lab AI</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col_centered = st.columns([1, 1.2, 1])[1]
    with col_centered:
        
        # MODO 1: LOGIN PRINCIPAL
        if st.session_state["auth_mode"] == "login":
            email = st.text_input("E-mail profissional", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            
            st.write("")
            if st.button("Entrar na Conta ➔", key="btn_login"):
                user = buscar_usuario(email)
                if user and user["senha"] == senha:
                    st.session_state["usuario_logado"] = email
                    st.session_state["usuario_nome"] = user["nome"]
                    st.session_state["contexto_vaga"] = user.get("contexto_vaga") or {}
                    st.session_state["avaliacoes"] = user.get("avaliacoes") or []
                    st.session_state["mensagens_chat"] = user.get("mensagens_chat") or []
                    
                    st.session_state["etapa1_concluida"] = bool(st.session_state["contexto_vaga"].get("empresa"))
                    st.session_state["etapa2_concluida"] = len(st.session_state["avaliacoes"]) > 0
                    st.session_state["etapa_selecionada"] = "1. Contexto da Vaga"
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

            # Esqueci minha senha sem caixa/fundo
            if st.button("Esqueci minha senha", key="btn_toggle_recup"):
                st.session_state["auth_mode"] = "recuperar"
                st.rerun()

            # Linha sutil de divisão e texto centralizado
            st.markdown("""
            <div style="margin: 2rem 0 1.2rem 0; text-align: center;">
                <hr style="border: none; border-top: 1px solid #E6E1D7; margin-bottom: 1.2rem;">
                <p style="font-size: 0.88rem; color: #787267; margin-bottom: 0.5rem;">Ainda não possui um acesso?</p>
            </div>
            """, unsafe_allow_html=True)

            # Botão Criar nova conta centralizado em cinza claro com texto escuro
            if st.button("Criar nova conta", key="btn_toggle_cad"):
                st.session_state["auth_mode"] = "cadastro"
                st.rerun()

        # MODO 2: CRIAR CONTA
        elif st.session_state["auth_mode"] == "cadastro":
            st.markdown("<h3 style='text-align: center; margin-bottom: 1.5rem; font-size: 1.6rem;'>Criar nova conta</h3>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome completo", key="cad_nome")
            novo_email = st.text_input("E-mail profissional", key="cad_email")
            nova_senha = st.text_input("Defina uma senha", type="password", key="cad_senha")

            st.write("")
            if st.button("Finalizar Cadastro e Acessar ➔", key="btn_cadastrar"):
                if buscar_usuario(novo_email):
                    st.warning("Este e-mail já está cadastrado.")
                elif novo_email and nova_senha and novo_nome:
                    criar_usuario(novo_nome, novo_email, nova_senha)
                    st.session_state["usuario_logado"] = novo_email
                    st.session_state["usuario_nome"] = novo_nome
                    st.session_state["etapa1_concluida"] = False
                    st.session_state["etapa2_concluida"] = False
                    st.session_state["etapa_selecionada"] = "1. Contexto da Vaga"
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

            st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
            if st.button("Voltar ao Login", key="btn_voltar_login1"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # MODO 3: REDEFINIÇÃO DIRETA DE SENHA
        elif st.session_state["auth_mode"] == "recuperar":
            st.markdown("<h3 style='text-align: center; margin-bottom: 0.5rem; font-size: 1.5rem;'>Redefinir Senha</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.88rem; color: #6B655C; margin-bottom: 1.5rem;'>Informe seu e-mail cadastrado e defina a nova senha.</p>", unsafe_allow_html=True)
            
            email_recup = st.text_input("E-mail cadastrado", key="recup_email")
            nova_senha_recup = st.text_input("Nova Senha", type="password", key="recup_nova_senha")
            confirmar_senha = st.text_input("Confirmar Nova Senha", type="password", key="recup_conf_senha")

            st.write("")
            if st.button("Atualizar Senha ➔", key="btn_confirmar_recup"):
                if not email_recup or not nova_senha_recup or not confirmar_senha:
                    st.warning("Preencha todos os campos.")
                elif nova_senha_recup != confirmar_senha:
                    st.error("As senhas digitadas não coincidem.")
                else:
                    user = buscar_usuario(email_recup)
                    if user:
                        atualizar_senha_usuario(email_recup, nova_senha_recup)
                        st.success("Senha alterada com sucesso!")
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    else:
                        st.error("Nenhuma conta encontrada com este e-mail.")

            st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
            if st.button("Voltar ao Login", key="btn_voltar_login2"):
                st.session_state["auth_mode"] = "login"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ============================================================
# CABEÇALHO & IDENTIDADE LOGADA
# ============================================================
col_head1, col_head2 = st.columns([4, 1.2])
with col_head1:
    st.markdown("""
    <div style="padding: 0.5rem 0 0.2rem 0;">
        <h1 style="font-size: 2.3rem; margin-bottom: 0px;">Interview Lab AI</h1>
        <p style="color: #787267; font-size: 0.95rem; margin-top: -4px;">Laboratório de Simulação e Lapidação Narrativa para Entrevistas Executivas.</p>
    </div>
    """, unsafe_allow_html=True)
with col_head2:
    st.markdown(f"<div style='text-align: right; padding-top: 0.8rem;'><span style='font-size: 0.85rem; color: #787267;'>Candidato Conectado</span><br><b>{st.session_state.get('usuario_nome', 'Candidato')}</b></div>", unsafe_allow_html=True)
    if st.button("Sair da Sessão", key="btn_logout"):
        st.session_state.clear()
        st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid #E6E1D7; margin: 0.8rem 0 1.5rem 0;'>", unsafe_allow_html=True)

# Validação do Cliente Gemini
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.warning("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = get_client(api_key)

# ============================================================
# GERENCIAMENTO DAS ETAPAS E PROGRESSO
# ============================================================
etapas_lista = ["1. Contexto da Vaga"]
if st.session_state.get("etapa1_concluida"):
    etapas_lista.append("2. Painel de Simulação")
if st.session_state.get("etapa2_concluida"):
    etapas_lista.append("3. Lapidação & Feedback")

if "etapa_selecionada" not in st.session_state or st.session_state["etapa_selecionada"] not in etapas_lista:
    st.session_state["etapa_selecionada"] = etapas_lista[0]

etapa_atual = st.radio(
    "Navegação por Etapas:",
    options=etapas_lista,
    index=etapas_lista.index(st.session_state["etapa_selecionada"]),
    horizontal=True,
    key="etapa_radio_main"
)

st.session_state["etapa_selecionada"] = etapa_atual

# ============================================================
# ETAPA 1 — CONTEXTO DA VAGA
# ============================================================
if st.session_state["etapa_selecionada"] == "1. Contexto da Vaga":
    st.markdown('<div class="editorial-card">', unsafe_allow_html=True)
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
            
            st.session_state["etapa_selecionada"] = "2. Painel de Simulação"
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ETAPA 2 — PAINEL DE SIMULAÇÃO
# ============================================================
elif st.session_state["etapa_selecionada"] == "2. Painel de Simulação":
    col_nav1, col_nav2 = st.columns([1.5, 4])
    with col_nav1:
        if st.button("⬅ Voltar para Contexto da Vaga", key="btn_voltar_e1"):
            st.session_state["etapa_selecionada"] = "1. Contexto da Vaga"
            st.rerun()

    st.markdown('<div class="editorial-card">', unsafe_allow_html=True)
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

    if st.button("Enviar, Avaliar e Avançar para Etapa 3 ➔", key="btn_avaliar_e2"):
        if not resposta_texto and not audio_bytes:
            st.warning("Por favor, forneça uma resposta em texto ou grave um áudio.")
        else:
            with st.spinner("Analisando alinhamento estratégico com o Gemini..."):
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
                
                st.session_state["etapa_selecionada"] = "3. Lapidação & Feedback"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("ultima_avaliacao"):
        st.markdown('<div class="editorial-card">', unsafe_allow_html=True)
        st.markdown("### Último Parecer Técnico Gerado")
        st.markdown(st.session_state["ultima_avaliacao"])
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ETAPA 3 — LAPIDAÇÃO & FEEDBACK
# ============================================================
elif st.session_state["etapa_selecionada"] == "3. Lapidação & Feedback":
    col_nav1, col_nav2 = st.columns([1.5, 4])
    with col_nav1:
        if st.button("⬅ Voltar para Simulação", key="btn_voltar_e2"):
            st.session_state["etapa_selecionada"] = "2. Painel de Simulação"
            st.rerun()

    st.markdown('<div class="editorial-card">', unsafe_allow_html=True)
    st.markdown("<h3>Etapa 3 — Atelier de Lapidação Narrativa</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B655C; font-size: 0.92rem; margin-bottom: 1.5rem;'>Converse com o mentor de inteligência para ajustar métricas, storytelling e pesquisar tendências da empresa no mercado em tempo real.</p>", unsafe_allow_html=True)
    
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
            
        with st.spinner("Buscando dados adicionais no mercado e estruturando feedback..."):
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
                
    st.markdown('</div>', unsafe_allow_html=True)
