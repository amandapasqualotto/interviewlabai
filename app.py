# app.py
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from curadoria import PERGUNTAS_CURATORIA
from gemini_engine import analisar_resposta_audio, lapidar_resposta_chat

st.set_page_config(page_title="Interview Coach IA", page_icon="🎯", layout="wide")

st.title("🎯 Simulator & Coach de Entrevistas com IA")
st.markdown("Treine suas respostas gravando áudio ou lapidando o texto com nossa curadoria de perguntas.")

# BLOCO 1: ENTRADA DE DADOS DA VAGA
st.header("1. Contexto da Vaga e Empresa")
vaga_info = st.text_area(
    "Cole aqui o descritivo da vaga, requisitos, sobre a empresa e valores:",
    height=150,
    placeholder="Ex: Empresa X busca estagiário de tecnologia proativo, com conhecimento em Python, comunicação clara e alinhado aos valores de inovação e diversidade..."
)

st.divider()

# BLOCO 2: PAINEL DE SIMULAÇÃO (ÁUDIO)
st.header("2. Painel de Simulação (Áudio)")

pergunta_selecionada = st.selectbox(
    "Escolha uma pergunta da curadoria para treinar:",
    options=list(PERGUNTAS_CURATORIA.keys())
)

dados_pergunta = PERGUNTAS_CURATORIA[pergunta_selecionada]

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info(f"**Técnica Recomendada:** {dados_pergunta['tecnica']}")
with col_info2:
    st.warning(f"**O que o Recrutador Espera:** {dados_pergunta['expectativa']}")

st.markdown("#### Grave sua Resposta:")
audio_bytes = audio_recorder(text="Clique para gravar", recording_color="#e8b62c", neutral_color="#6aa36f")

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    
    if st.button("🚀 Analisar Resposta com IA"):
        if not vaga_info.strip():
            st.error("Por favor, preencha as informações da vaga no Bloco 1 antes de analisar.")
        else:
            with st.spinner("Analisando áudio, transcrição e aderência técnica..."):
                try:
                    resultado = analisar_resposta_audio(
                        audio_bytes=audio_bytes,
                        pergunta=pergunta_selecionada,
                        dados_pergunta=dados_pergunta,
                        descritivo_vaga=vaga_info
                    )
                    
                    st.success("Análise concluída!")
                    
                    metric_col, text_col = st.columns([1, 3])
                    with metric_col:
                        st.metric(
                            label="Match da Resposta", 
                            value=f"{resultado['porcentagem_match']}%"
                        )
                    
                    with text_col:
                        st.markdown(f"**Transcrição:** *\"{resultado['transcricao']}\"*")
                    
                    st.subheader("Parecer Técnico")
                    st.write(f"**Análise da Técnica:** {resultado['analise_tecnica']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**✅ Pontos Fortes:**")
                        for pf in resultado.get("pontos_fortes", []):
                            st.write(f"- {pf}")
                    with c2:
                        st.markdown("**⚠️ O que pode melhorar:**")
                        for pm in resultado.get("pontos_melhoria", []):
                            st.write(f"- {pm}")
                            
                    with st.expander("💡 Resposta Ideal Sugerida pela IA"):
                        st.write(resultado.get("resposta_ideal_sugerida", ""))
                        
                except Exception as e:
                    st.error(f"Erro ao processar áudio: {str(e)}")

st.divider()

# BLOCO 3: OFICINA DE RESPOSTAS (CHAT)
st.header("3. Oficina de Respostas (Chat de Lapidação)")
st.caption("Escreva o rascunho da sua resposta abaixo e receba orientações da IA para ajustá-la passo a passo.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Digite sua resposta ou rascunho para ajustarmos..."):
    if not vaga_info.strip():
        st.error("Preencha as informações da vaga no Bloco 1 antes de usar a oficina.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Lapidando resposta..."):
                resposta_ia = lapidar_resposta_chat(
                    historico_mensagens=st.session_state.messages,
                    contexto_vaga=vaga_info,
                    pergunta=pergunta_selecionada,
                    dados_pergunta=dados_pergunta
                )
                st.markdown(resposta_ia)
        
        st.session_state.messages.append({"role": "assistant", "content": resposta_ia})