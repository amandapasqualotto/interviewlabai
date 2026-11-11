import streamlit as st
import os
from google import genai

# --- FUNÇÕES DE INTEGRAÇÃO COM GEMINI ---
def avaliar_resposta_com_gemini(client, contexto, pergunta, resposta):
    prompt = f"""
    Você é um selecionador sênior de carreiras avaliando um candidato para a vaga:
    Empresa: {contexto.get('empresa')}
    Cargo: {contexto.get('cargo')}
    Descrição: {contexto.get('descricao')}
    Cultura: {contexto.get('cultura')}

    Pergunta feita: {pergunta}
    Resposta fornecida pelo candidato: {resposta}

    Avalie a resposta utilizando a Metodologia STAR (Situação, Tarefa, Ação, Resultado).
    Forneça um feedback construtivo, elegante, pontuando os acertos, lacunas e sugerindo uma versão aprimorada da resposta.
    """
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    return response.text

def simular_chat_lapidacao(client, historico_mensagens):
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=historico_mensagens
    )
    return response.text

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

# Inicialização segura da API Key do Gemini
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
        <p>A chave da API do Gemini não foi detectada nos Secrets do Streamlit Cloud.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

client = genai.Client(api_key=api_key)

# --- LAYOUT EM ABAS EDITORIAL ---
aba_escolha, aba_pratica, aba_chat = st.tabs([
    "🌿 1. Contexto da Vaga", 
    "🎙️ 2. Painel de Simulação", 
    "✍️ 3. Lapidação & Feedback"
])

with aba_escolha:
    st.markdown("### Defina o Contexto da Vaga")
    st.markdown("<p style='color: #6C665F;'>Insira os detalhes da empresa, cargo e requisitos para personalizar a simulação de entrevista.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        empresa = st.text_input("Nome da Empresa Alvo", placeholder="Ex: Google, Banco ABC, Escritório...")
    with col2:
        cargo = st.text_input("Cargo / Posição Desejada", placeholder="Ex: Product Manager, Advogado(a), Desenvolvedor(a)...")
        
    descricao = st.text_area("Descrição e Requisitos da Vaga", placeholder="Cole aqui os principais requisitos técnicos ou responsabilidades exigidas pela vaga...")
    cultura = st.text_area("Cultura e Valores da Empresa (Opcional)", placeholder="Ex: Foco em inovação, autonomia, trabalho em equipe, rigor técnico...")

    st.session_state["contexto_vaga"] = {
        "empresa": empresa if empresa else "Empresa Alvo",
        "cargo": cargo if cargo else "Cargo Desejado",
        "descricao": descricao,
        "cultura": cultura
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
        "Sua Resposta:",
        placeholder="Estruture sua resposta aqui...",
        height=180
    )
    
    if st.button("Avaliar com a Metodologia STAR"):
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
            
        with st.spinner("Tecendo ponderações..."):
            contents = []
            for m in st.session_state["mensagens_chat"]:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
                
            resposta_ia = simular_chat_lapidacao(client, contents)
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": resposta_ia})
            with st.chat_message("assistant"):
                st.markdown(resposta_ia)
