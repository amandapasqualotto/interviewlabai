import io
import os
import uuid
from datetime import datetime

import streamlit as st
from pypdf import PdfReader
from docx import Document

from auth.service import sign_up, sign_in, send_password_reset, sign_out
from database.client import get_user_client
from database.repository import (
    ensure_profile, log_event, save_professional_profile, create_simulation,
    update_simulation_status, save_answer, save_chat_message, list_simulations,
    get_simulation_details, is_admin, admin_overview, admin_simulation_details,
)
from curadoria import INSIGHTS_GERAIS, PERGUNTAS_CURATORIA
from gemini_engine import get_client, avaliar_resposta, transcrever_audio, mentor_chat

st.set_page_config(page_title="Interview Lab AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
.stApp{background:#FBF9F5;color:#2C2A29;font-family:'Plus Jakarta Sans',sans-serif}
h1,h2,h3,h4{font-family:'Playfair Display',serif!important;color:#1E3023!important}
p,label,div,span{font-family:'Plus Jakarta Sans',sans-serif}
.editorial-card{background:#F4F1EA;border:1px solid #E3DED4;padding:22px;border-radius:4px;margin-bottom:16px}
.small-muted{color:#6C665F;font-size:.92rem}
.stButton>button{background:#1E3023;color:#FBF9F5;border:1px solid #1E3023;border-radius:2px;font-weight:500}
.stButton>button:hover{background:#2C4233;color:white;border-color:#2C4233}
.stTextInput input,.stTextArea textarea{background:#fff;border:1px solid #DCD6CD;border-radius:2px;color:#2C2A29}
hr{border-color:#E3DED4}#MainMenu,footer{visibility:hidden}
.block-container{padding-top:1.5rem;padding-bottom:3rem}
</style>
""", unsafe_allow_html=True)


def header(subtitle="Estruture respostas, pratique entrevistas e desenvolva uma narrativa profissional consistente com apoio de inteligência artificial."):
    st.markdown(f"""<div style='text-align:center;padding:1.2rem 0 .8rem'>
    <p style='letter-spacing:3px;font-size:.78rem;text-transform:uppercase;color:#5A655D'>— Atelier de Carreiras & Simulações —</p>
    <h1 style='font-size:2.8rem;font-style:italic;margin-bottom:.35rem'>Interview Lab AI</h1>
    <p style='color:#6C665F;max-width:650px;margin:auto'>{subtitle}</p></div><hr style='margin:1.5rem 0'>""", unsafe_allow_html=True)


def secrets_ready():
    try:
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_ANON_KEY"))
    except Exception:
        return False


def login_screen():
    header("Seu espaço pessoal de preparação profissional.")
    st.markdown("### Acesse sua conta")
    tab_login, tab_signup, tab_reset = st.tabs(["Entrar", "Criar conta", "Recuperar senha"])
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            try:
                response = sign_in(email, password)
                session = response.session
                if not session:
                    st.error("Não foi possível iniciar a sessão. Verifique e-mail e senha.")
                else:
                    st.session_state.auth_access_token = session.access_token
                    st.session_state.auth_refresh_token = session.refresh_token
                    st.session_state.auth_user = response.user
                    profile = ensure_profile(session.access_token, session.refresh_token, response.user)
                    log_event(session.access_token, session.refresh_token, "login")
                    st.session_state.profile = profile
                    st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível entrar: {exc}")
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Nome completo")
            email_new = st.text_input("E-mail", key="signup_email")
            password_new = st.text_input("Senha", type="password", help="Use pelo menos 8 caracteres.")
            password_confirm = st.text_input("Confirme a senha", type="password")
            accepted = st.checkbox("Li e concordo com a política de privacidade da plataforma.")
            create = st.form_submit_button("Criar minha conta", type="primary", use_container_width=True)
        if create:
            if not name.strip() or not email_new.strip() or len(password_new) < 8:
                st.warning("Informe nome, e-mail e uma senha com pelo menos 8 caracteres.")
            elif password_new != password_confirm:
                st.warning("As senhas não coincidem.")
            elif not accepted:
                st.warning("É necessário aceitar a política de privacidade para continuar.")
            else:
                try:
                    response = sign_up(name, email_new, password_new)
                    if response.session:
                        session = response.session
                        st.session_state.auth_access_token = session.access_token
                        st.session_state.auth_refresh_token = session.refresh_token
                        st.session_state.auth_user = response.user
                        profile = ensure_profile(session.access_token, session.refresh_token, response.user)
                        log_event(session.access_token, session.refresh_token, "signup")
                        st.session_state.profile = profile
                        st.success("Conta criada com sucesso!")
                        st.rerun()
                    else:
                        st.success("Cadastro recebido. Verifique seu e-mail para confirmar a conta e depois faça login.")
                except Exception as exc:
                    st.error(f"Não foi possível criar a conta: {exc}")
    with tab_reset:
        with st.form("reset_form"):
            reset_email = st.text_input("E-mail cadastrado")
            reset = st.form_submit_button("Enviar link de recuperação", use_container_width=True)
        if reset:
            try:
                send_password_reset(reset_email)
                st.success("Se o e-mail estiver cadastrado, você receberá as instruções de recuperação.")
            except Exception as exc:
                st.error(f"Não foi possível solicitar a recuperação: {exc}")


def get_context_text(ctx):
    return f"""
EMPRESA: {ctx.get('empresa','')}
CARGO: {ctx.get('cargo','')}
DESCRIÇÃO DA VAGA: {ctx.get('descricao','')}
SOBRE A EMPRESA: {ctx.get('sobre_empresa','')}
LINKEDIN: {ctx.get('linkedin_url','')}
CURRÍCULO: {ctx.get('curriculo_texto','')}
DIRETRIZES DA CURADORIA: {INSIGHTS_GERAIS}
"""


def extract_resume(uploaded):
    raw = uploaded.getvalue()
    ext = uploaded.name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
    elif ext == "docx":
        doc = Document(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + " | ".join(cell.text for cell in row.cells)
    else:
        text = raw.decode("utf-8", errors="replace")
    return text.strip(), raw


def save_resume_to_storage(access, refresh, uploaded, raw):
    client = get_user_client(access, refresh)
    user = client.auth.get_user().user
    safe_name = uploaded.name.replace("/", "_").replace("\\", "_")
    path = f"{user.id}/{uuid.uuid4().hex}_{safe_name}"
    mime = uploaded.type or "application/octet-stream"
    client.storage.from_("candidate-resumes").upload(path, raw, {"content-type": mime, "upsert": "true"})
    return path


def show_feedback(items):
    for item in items:
        with st.expander(f"{item.get('question','Pergunta')} · {item.get('created_at','')[:10]}", expanded=False):
            st.markdown("**Resposta**")
            st.write(item.get("answer_text", ""))
            evaluations = item.get("evaluations") or []
            if isinstance(evaluations, dict):
                evaluations = [evaluations]
            for evaluation in evaluations:
                st.markdown("**Avaliação**")
                st.markdown(evaluation.get("feedback", ""))


def candidate_app():
    access, refresh = st.session_state.auth_access_token, st.session_state.auth_refresh_token
    user = st.session_state.auth_user
    profile = st.session_state.profile
    name = profile.get("full_name") or user.email
    st.sidebar.markdown(f"### Olá, {name.split()[0]}")
    st.sidebar.caption(user.email)
    sections = ["Início", "Nova simulação", "Histórico", "Meu perfil"]
    nav_target = st.session_state.pop("nav_target", "Início")
    nav_index = sections.index(nav_target) if nav_target in sections else 0
    page = st.sidebar.radio("Navegação", sections, index=nav_index, key="candidate_navigation", label_visibility="collapsed")
    if st.sidebar.button("Sair da conta", use_container_width=True):
        log_event(access, refresh, "logout")
        try:
            sign_out(access, refresh)
        except Exception:
            pass
        for key in ["auth_access_token", "auth_refresh_token", "auth_user", "profile", "active_simulation_id", "active_context"]:
            st.session_state.pop(key, None)
        st.rerun()

    header()
    if page == "Início":
        st.markdown(f"## Bem-vinda(o), {name}.")
        sims = list_simulations(access, refresh)
        c1, c2 = st.columns(2)
        c1.metric("Simulações realizadas", len(sims))
        c2.metric("Em andamento", sum(1 for s in sims if s.get("status") == "in_progress"))
        st.markdown("### Atividades recentes")
        if sims:
            for sim in sims[:5]:
                with st.container(border=True):
                    st.markdown(f"**{sim['company']} — {sim['position']}**")
                    st.caption(f"{sim.get('created_at','')[:10]} · {sim.get('status','').replace('_',' ').title()}")
                    if st.button("Abrir simulação", key=f"open_home_{sim['id']}"):
                        st.session_state.selected_history_id = sim["id"]
                        st.session_state.nav_target = "Histórico"
                        st.rerun()
        else:
            st.info("Você ainda não criou uma simulação. Comece em ‘Nova simulação’.")

    elif page == "Meu perfil":
        st.markdown("## Meu perfil profissional")
        client = get_user_client(access, refresh)
        existing = client.table("professional_profiles").select("*").maybe_single().execute().data or {}
        with st.form("profile_form"):
            linkedin = st.text_input("Link do LinkedIn", value=existing.get("linkedin_url") or "")
            resume = st.file_uploader("Atualizar currículo", type=["pdf", "docx", "txt"])
            save = st.form_submit_button("Salvar perfil", type="primary")
        if save:
            if linkedin and not linkedin.startswith("https://"):
                st.warning("Informe o LinkedIn usando um endereço https:// válido.")
            else:
                try:
                    path, resume_name, resume_text = existing.get("resume_path"), existing.get("resume_name"), existing.get("resume_text", "")
                    if resume:
                        resume_text, raw = extract_resume(resume)
                        path = save_resume_to_storage(access, refresh, resume, raw)
                        resume_name = resume.name
                    save_professional_profile(access, refresh, linkedin, path, resume_name, resume_text)
                    st.success("Perfil atualizado.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erro ao salvar perfil: {exc}")
        if existing.get("resume_name"):
            st.caption(f"Currículo salvo: {existing['resume_name']}")

    elif page == "Nova simulação":
        st.markdown("## Contexto da vaga")
        st.caption("Preencha os dados da oportunidade. Empresa, cargo e descrição são obrigatórios.")
        client = get_user_client(access, refresh)
        professional = client.table("professional_profiles").select("*").maybe_single().execute().data or {}
        with st.form("new_simulation_form"):
            col1, col2 = st.columns(2)
            company = col1.text_input("Nome da empresa")
            position = col2.text_input("Cargo / posição desejada")
            description = st.text_area("Descrição e requisitos da vaga", height=140)
            about = st.text_area("Sobre a empresa — descrição, cultura, valores etc.", height=120)
            linkedin = st.text_input("Link do LinkedIn (opcional)", value=professional.get("linkedin_url") or "")
            use_profile_cv = st.checkbox("Utilizar o currículo salvo no meu perfil", value=bool(professional.get("resume_text")))
            resume = st.file_uploader("Ou anexar currículo para esta simulação (opcional)", type=["pdf", "docx", "txt"])
            submit = st.form_submit_button("Salvar contexto e iniciar simulação", type="primary")
        if submit:
            if not company.strip() or not position.strip() or not description.strip():
                st.warning("Preencha empresa, cargo e descrição da vaga.")
            elif linkedin and not linkedin.startswith("https://"):
                st.warning("Informe um link válido iniciado por https://.")
            else:
                try:
                    resume_text = professional.get("resume_text", "") if use_profile_cv else ""
                    resume_name = professional.get("resume_name", "") if use_profile_cv else ""
                    resume_path = professional.get("resume_path") if use_profile_cv else None
                    if resume:
                        resume_text, raw = extract_resume(resume)
                        resume_name = resume.name
                        resume_path = save_resume_to_storage(access, refresh, resume, raw)
                    context = {"empresa": company.strip(), "cargo": position.strip(), "descricao": description.strip(), "sobre_empresa": about.strip(), "linkedin_url": linkedin.strip(), "curriculo_texto": resume_text, "curriculo_nome": resume_name}
                    sim_id = create_simulation(access, refresh, context)
                    save_professional_profile(access, refresh, linkedin.strip(), resume_path, resume_name, resume_text)
                    st.session_state.active_simulation_id = sim_id
                    st.session_state.active_context = context
                    st.session_state.sim_stage = "Perguntas"
                    st.session_state.current_evaluation = None
                    st.session_state.chat_history = []
                    log_event(access, refresh, "simulation_created", {"simulation_id": sim_id})
                    st.success("Contexto salvo. Sua simulação está pronta.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível iniciar a simulação: {exc}")
        if st.session_state.get("active_simulation_id"):
            st.markdown("---")
            render_simulation(access, refresh)

    elif page == "Histórico":
        st.markdown("## Meu histórico")
        sims = list_simulations(access, refresh)
        if not sims:
            st.info("Suas simulações aparecerão aqui depois que você criar a primeira.")
        else:
            options = {f"{s['company']} — {s['position']} · {s.get('created_at','')[:10]}": s["id"] for s in sims}
            labels = list(options.keys())
            default_id = st.session_state.get("selected_history_id")
            default_index = next((i for i, label in enumerate(labels) if options[label] == default_id), 0)
            chosen = st.selectbox("Selecione uma simulação", labels, index=default_index)
            sim_id = options[chosen]
            sim, answers, messages = get_simulation_details(access, refresh, sim_id)
            st.markdown(f"### {sim['company']} — {sim['position']}")
            st.caption(f"Criada em {sim.get('created_at','')[:10]} · Status: {sim.get('status','').replace('_',' ').title()}")
            st.write(sim.get("job_description", ""))
            if answers:
                st.markdown("### Perguntas, respostas e avaliações")
                show_feedback(answers)
            if messages:
                st.markdown("### Conversas com o mentor")
                for msg in messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            if st.button("Continuar esta simulação", type="primary"):
                st.session_state.active_simulation_id = sim_id
                st.session_state.active_context = {
                    "empresa": sim["company"], "cargo": sim["position"], "descricao": sim["job_description"],
                    "sobre_empresa": sim.get("company_about", ""), "linkedin_url": sim.get("linkedin_url", ""),
                    "curriculo_nome": sim.get("resume_name", ""), "curriculo_texto": sim.get("resume_text", ""),
                }
                st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in messages]
                st.session_state.sim_stage = "Perguntas"
                st.session_state.nav_target = "Nova simulação"
                st.rerun()


def render_simulation(access, refresh):
    sim_id = st.session_state.active_simulation_id
    context = st.session_state.active_context
    st.markdown(f"### {context['empresa']} — {context['cargo']}")
    stage = st.radio("Etapas", ["Perguntas", "Mentor IA"], horizontal=True, key="sim_stage")
    if stage == "Perguntas":
        questions = list(PERGUNTAS_CURATORIA.keys())
        question = st.selectbox("Selecione uma pergunta da curadoria", questions, key="question_select")
        metadata = PERGUNTAS_CURATORIA[question]
        with st.container(border=True):
            st.markdown("**Técnica recomendada**")
            st.write(metadata.get("tecnica", "Adequada ao tipo de pergunta"))
            st.markdown("**O que a pergunta busca avaliar**")
            st.write(metadata.get("expectativa", ""))
        mode = st.radio("Como deseja responder?", ["Escrever resposta", "Gravar resposta em áudio"], horizontal=True, key="answer_mode")
        answer = ""
        if mode == "Escrever resposta":
            answer = st.text_area("Sua resposta", height=220, placeholder="Responda como se estivesse diante do recrutador. Use exemplos reais e detalhes concretos.", key="candidate_answer")
        else:
            if hasattr(st, "audio_input"):
                audio = st.audio_input("Gravar resposta")
                if audio:
                    st.audio(audio)
                    if st.button("Transcrever áudio"):
                        try:
                            with st.spinner("Transcrevendo áudio..."):
                                st.session_state.transcribed_answer = transcrever_audio(get_client(), audio)
                        except Exception as exc:
                            st.error(f"Erro na transcrição: {exc}")
                    answer = st.text_area("Revise a transcrição", value=st.session_state.get("transcribed_answer", ""), height=180, key="transcribed_answer_edit")
            else:
                st.warning("Atualize o Streamlit para uma versão que ofereça st.audio_input.")
        if st.button("Avaliar minha resposta", type="primary"):
            if not answer.strip():
                st.warning("Escreva ou grave uma resposta antes de avaliar.")
            else:
                try:
                    with st.spinner("Avaliando sua resposta de acordo com a pergunta e a vaga..."):
                        feedback = avaliar_resposta(get_client(), get_context_text(context), question, answer, metadata)
                    save_answer(access, refresh, sim_id, question, metadata.get("tecnica", ""), metadata.get("expectativa", ""), answer, "audio_transcription" if mode.startswith("Gravar") else "text", feedback)
                    st.session_state.current_evaluation = feedback
                    st.session_state.last_question = question
                    log_event(access, refresh, "answer_evaluated", {"simulation_id": sim_id})
                    st.success("Resposta avaliada e salva no seu histórico.")
                except Exception as exc:
                    st.error(f"Não foi possível avaliar a resposta: {exc}")
        if st.session_state.get("current_evaluation"):
            st.markdown("---")
            st.markdown("### Parecer do avaliador")
            st.markdown(st.session_state.current_evaluation)
            if st.button("Concluir simulação"):
                update_simulation_status(access, refresh, sim_id, "completed")
                st.success("Simulação marcada como concluída.")
    else:
        st.markdown("### Atelier de lapidação")
        st.caption("O mentor considera os dados da vaga, seu currículo, LinkedIn informado, avaliações e pesquisa pública na internet quando pertinente.")
        try:
            _, answers, saved_messages = get_simulation_details(access, refresh, sim_id)
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in saved_messages]
        except Exception:
            answers = []
        for message in st.session_state.get("chat_history", []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        prompt = st.chat_input("Peça ajuda para aprimorar sua resposta, pesquisar a empresa ou entender o que o recrutador espera...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            save_chat_message(access, refresh, sim_id, "user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)
            evaluation_text = "\n\n".join(a.get("feedback", "") for answer in answers for a in (answer.get("evaluations") or []))[-12000:]
            history_text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat_history[-10:])
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Analisando o contexto e consultando fontes públicas quando necessário..."):
                        response = mentor_chat(get_client(), get_context_text(context), st.session_state.get("last_question", ""), evaluation_text, history_text, prompt, web_search=True)
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                save_chat_message(access, refresh, sim_id, "assistant", response)
            except Exception as exc:
                st.error(f"Não foi possível consultar o mentor: {exc}")


def admin_app():
    access, refresh = st.session_state.auth_access_token, st.session_state.auth_refresh_token
    st.sidebar.markdown("### Administração")
    page = st.sidebar.radio("Painel", ["Visão geral", "Históricos dos candidatos", "Logs de acesso"])
    if st.sidebar.button("Sair da conta", use_container_width=True):
        log_event(access, refresh, "logout")
        try: sign_out(access, refresh)
        except Exception: pass
        for key in ["auth_access_token", "auth_refresh_token", "auth_user", "profile"]: st.session_state.pop(key, None)
        st.rerun()
    header("Painel administrativo — gestão e acompanhamento da plataforma.")
    try:
        users, simulations, logs = admin_overview(access, refresh)
    except Exception as exc:
        st.error(f"Não foi possível carregar o painel administrativo: {exc}")
        st.stop()
    if page == "Visão geral":
        a, b, c = st.columns(3)
        a.metric("Usuários cadastrados", len(users))
        b.metric("Simulações", len(simulations))
        c.metric("Eventos registrados", len(logs))
        st.markdown("### Usuários recentes")
        st.dataframe(users, use_container_width=True, hide_index=True)
        st.markdown("### Simulações recentes")
        st.dataframe(simulations, use_container_width=True, hide_index=True)
    elif page == "Históricos dos candidatos":
        if not simulations:
            st.info("Ainda não existem simulações cadastradas.")
        else:
            options = {f"{s['company']} — {s['position']} · {s.get('created_at','')[:10]} · {s['user_id'][:8]}": s["id"] for s in simulations}
            label = st.selectbox("Selecione uma simulação", list(options.keys()))
            sim, answers, messages = admin_simulation_details(access, refresh, options[label])
            log_event(access, refresh, "admin_viewed_simulation", {"simulation_id": options[label]})
            st.markdown(f"### {sim['company']} — {sim['position']}")
            st.caption(f"Identificador do candidato: {sim['user_id']} · {sim.get('created_at','')}")
            st.markdown("**Descrição da vaga**")
            st.write(sim.get("job_description", ""))
            st.markdown("**Sobre a empresa**")
            st.write(sim.get("company_about", ""))
            show_feedback(answers)
            if messages:
                st.markdown("### Conversas com o mentor")
                for message in messages:
                    with st.chat_message(message["role"]): st.markdown(message["content"])
    else:
        st.markdown("### Registro de acessos e atividades")
        st.dataframe(logs, use_container_width=True, hide_index=True)
        st.caption("Os logs registram eventos de autenticação e atividades relevantes; não representam gravação de tela ou monitoramento contínuo.")


# ------------------------- BOOT -------------------------
if not secrets_ready():
    header()
    st.error("Configure SUPABASE_URL e SUPABASE_ANON_KEY nos Secrets do Streamlit antes de iniciar.")
    st.code('SUPABASE_URL = "https://SEU-PROJETO.supabase.co"\nSUPABASE_ANON_KEY = "SUA_CHAVE_ANON_PUBLIC"\nGEMINI_API_KEY = "SUA_CHAVE_GEMINI"', language="toml")
    st.stop()

if not st.session_state.get("auth_access_token") or not st.session_state.get("auth_refresh_token"):
    login_screen()
    st.stop()

try:
    # Revalidates the current session on each Streamlit rerun.
    auth_client = get_user_client(st.session_state.auth_access_token, st.session_state.auth_refresh_token)
    current_user = auth_client.auth.get_user().user
    st.session_state.auth_user = current_user
    if not st.session_state.get("profile"):
        st.session_state.profile = ensure_profile(st.session_state.auth_access_token, st.session_state.auth_refresh_token, current_user)
    if is_admin(st.session_state.auth_access_token, st.session_state.auth_refresh_token):
        admin_app()
    else:
        candidate_app()
except Exception as exc:
    st.session_state.pop("auth_access_token", None)
    st.session_state.pop("auth_refresh_token", None)
    st.session_state.pop("auth_user", None)
    st.session_state.pop("profile", None)
    st.warning("Sua sessão expirou ou não pôde ser validada. Entre novamente.")
    st.rerun()
