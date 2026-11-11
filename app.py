import streamlit as st
import os
from google import genai
from curadoria import CURADORIA_VAGAS
from gemini_engine import avaliar_resposta_com_gemini, simular_chat_lapidacao

# Configuração da página com tema minimalista e título customizado
st.set_page_config(
    page_title="Interview Lab AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILO CSS EDITORIAL / VINTAGE / MINIMALISTA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

    /* Fundo geral e tipografia base */
    .stApp {
        background-color: #FBF9F5;
        color: #2C2A29;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Títulos com a fonte editorial serifada */
    h1, h2, h3, h4, .editorial-title {
        font-family: 'Playfair Display', serif;
        color: #1E3023;
        font-weight: 700;
    }

    /* Estilização dos blocos / containers com bordas finas e fundo creme claro */
    div.stMarkdownContainer, .element-container {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Caixa de destaque estilo editorial */
    .editorial-card {
        background-color: #F4F1EA;
        border: 1px solid #E3DED4;
        padding: 24px;
        border-radius: 4px;
        margin-bottom: 20px;
    }

    /* Botões personalizados */
    .stButton>button {
        background-color: #1E3023;
        color: #FBF9F5;
        border: none;
        border-radius: 2px;
        padding: 0.6rem 1.2rem;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2C4233;
        color: #FFFFFF;
    }

    /* Inputs e Selects minimalistas */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #FFFFFF;
        border: 1px solid #DCD6CD;
        border-radius: 2px;
        color: #2C2A29;
    }

    /* Ocultar elementos padrão do Streamlit para manter clean */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO EDITORIAL ---
st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0;">
    <p style="letter-spacing: 3px; font-size: 0.85rem; text-transform: uppercase; color: #5A655D; margin-bottom: 0.5rem;">— Atelier de Carreiras & Simulações —</p>
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem; font-style: italic;">Interview Lab AI</h1>
    <p style="color: #6C665F; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
        Um espaço refinado para estruturar respostas, dominar o método STAR e lapidar a sua narrativa profissional com inteligência artificial.
    </p>
</div>
<hr style="border: none; border-top: 1px solid #E3DED4; margin: 2rem 0;">
""", unsafe_allow_html=True)

# Inicialização segura da API Key do Gemini (lendo dos Secrets ou do ambiente)
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.markdown("""
    <div class="editorial-card" style="border-left: 4px solid #A35C44;">
        <h3 style="margin-top:0; color: #A35C44;">Configuração Necessária</h3>
        <p>A chave da API do Gemini não foi detectada. Por favor, configure a chave secreta no painel do Streamlit Cloud (Secrets) ou na variável de ambiente.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

client = genai.Client(api_key=api_key)

# --- LAYOUT EM ABAS / SEÇÕES ESTILO EDITORIAL ---
aba_escolha, aba_pratica, aba_chat = st.tabs([
    "🌿 1. Contexto & Vaga", 
    "🎙️ 2. Painel de Simulação", 
    "✍️ 3. Lapidação & Feedback"
])

with aba_escolha:
    st.markdown("### Selecione ou Personalize o Contexto")
    st.markdown("<p style='color: #6C665F;'>Escolha uma das vagas curadas abaixo ou insira os detalhes da empresa dos seus sonhos.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        opcao_vaga = st.selectbox(
            "Trilhas de Vagas Disponíveis",
            ["Personalizado / Inserir Manualmente"] + list(CURADORIA_VAGAS.keys())
        )
    
    if opcao_vaga != "Personalizado / Inserir Manualmente":
        vaga_selecionada = CURADORIA_VAGAS[opcao_vaga]
        empresa = vaga_selecionada["empresa"]
        cargo = vaga_selecionada["cargo"]
        descricao = vaga_selecionada["descricao"]
        cultura = vaga_selecionada["cultura"]
    else:
        with col2:
            empresa = st.text_input("Empresa", placeholder="Ex: Banco ABC / Escritório de Advocatia")
            cargo = st.text_input("Cargo / Posição", placeholder="Ex: Pessoa Trainee Jurídico / Analista")
        
        descricao = st.text_area("Descrição e Requisitos da Vaga", placeholder="Cole aqui os principais requisitos...")
        cultura = st.text_area("Cultura e Valores da Empresa", placeholder="Ex: Foco em autonomia, inovação e rigor técnico...")

    st.session_state["contexto_vaga"] = {
        "empresa": empresa if 'empresa' in locals() else "Empresa Alvo",
        "cargo": cargo if 'cargo' in locals() else "Cargo Desejado",
        "descricao": descricao if 'descricao' in locals() else "",
        "cultura": cultura if 'cultura' in locals() else ""
    }
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Salvar Contexto e Avançar ➔"):
        st.success("Contexto gravado com sucesso! Siga para o Painel de Simulação.")

with aba_pratica:
    st.markdown("### Simulação de Pergunta & Resposta")
    st.markdown("<p style='color: #6C665F;'>Pratique sua narrativa comportamental utilizando o método STAR (Situação, Tarefa, Ação e Resultado).</p>", unsafe_allow_html=True)
    
    pergunta_pratica = st.text_input(
        "Pergunta da Entrevista",
        value="Conte sobre uma situação em que você liderou um projeto sob alta pressão e prazos curtos."
    )
    
    resposta_candidato = st.text_area(
        "Sua Resposta (ou digite/cole sua fala transcrita):",
        placeholder="Estruture sua resposta aqui...",
        height=180
    )
    
    if st.button("Avaliar com o Metodologia STAR"):
        if not resposta_candidato.strip():
            st.warning("Por favor, insira uma resposta para receber a avaliação.")
        else:
            with st.spinner("Analisando sua narrativa com critérios editoriais e corporativos..."):
                resultado_avaliacao = avaliar_resposta_com_gemini(
                    client=client,
                    contexto=st.session_state.get("contexto_vaga", {}),
                    pergunta=pergunta_pratica,
                    resposta=resposta_candidato
                )
                st.session_state["ultima_avaliacao"] = resultado_avaliacao
                
            st.markdown("---")
            st.markdown("### 📋 Parecer do Avaliador")
            st.markdown(resultado_avaliacao)

with aba_chat:
    st.markdown("### Atelier de Lapidação (Chat com IA)")
    st.markdown("<p style='color: #6C665F;'>Converse com seu mentor de carreira para refinar pontos específicos da sua fala e ganhar confiança.</p>", unsafe_allow_html=True)
    
    if "mensagens_chat" not in st.session_state:
        st.session_state["mensagens_chat"] = []
        
    for msg in st.session_state["mensagens_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    prompt_usuario = st.chat_input("Digite sua dúvida ou peça ajustes na sua resposta...")
    if prompt_usuario:
        st.session_state["mensagens_chat"].append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
            
        with  st.spinner("Tecendo ponderações..."):
            resposta_ia = simular_chat_lapidacao(client, st.session_state["mensagens_chat"])
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": resposta_ia})
            with st.chat_message("assistant"):
                st.markdown(resposta_ia)
                