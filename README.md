<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:111E16,50:233A2C,100:C98B8B&height=220&section=header&text=Interview%20Lab%20AI&fontSize=48&fontColor=F8F6F0&animation=fadeIn&fontAlignY=38&desc=Interview%20simulation%20%C3%97%20Gemini%20%C3%97%20Narrative%20refinement&descAlignY=58&descSize=18" width="100%" alt="banner"/>

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=3500&pause=900&color=B8955A&center=true&vCenter=true&width=780&lines=Treine+suas+respostas+de+entrevista+com+IA;Interview+practice+powered+by+Generative+AI;STAR+method+%7C+Feedback+personalizado+por+vaga;Python+%C2%B7+Streamlit+%C2%B7+Gemini+%C2%B7+Supabase" alt="Typing SVG" />
</a>

<br/><br/>

### <a href="#english">🇺🇸 English</a> &nbsp;|&nbsp; <a href="#portugues">🇧🇷 Português</a>

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-233A2C?style=for-the-badge&logo=python&logoColor=white&labelColor=111E16)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-C98B8B?style=for-the-badge&logo=streamlit&logoColor=white&labelColor=111E16)
![Gemini](https://img.shields.io/badge/Google%20Gemini-API-233A2C?style=for-the-badge&logo=googlegemini&logoColor=white&labelColor=111E16)
![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-B8955A?style=for-the-badge&logo=supabase&logoColor=white&labelColor=111E16)

<br/>

<img src="icone.png" width="170" alt="Interview Lab AI logo"/>

<br/><br/>

### 🌿 [**Open the live app / Abrir o app**](https://interviewlabai.streamlit.app)

</div>

<br/>

<!-- ======================================================== -->
<!-- ======================= ENGLISH ======================== -->
<!-- ======================================================== -->

<a id="english"></a>

# 🇺🇸 English

## 🌿 About the project

> *"Many candidates get cut in the very first interview round, the one with an AI or an HR screener, simply because nobody taught them how to answer."*

While applying to several internships and trainee programs, I noticed the same pattern: the **opening stage of
the selection process** (AI interviews and HR screenings) repeats a **small set of frequent questions**, and this
is exactly where many people are eliminated.

So I curated those questions and built **Interview Lab AI**, a tool to **practice with the real job description
in hand**:

- 📋 Paste the **job posting**, company description and culture, and upload your **résumé**
- 🎯 Pick one of **27 curated interview questions**
- 🎙️ Answer by **text or audio**, recorded right in the browser
- 🧠 Receive a **technical evaluation** based on the expected answer, the suggested technique (such as **STAR**) and the job context
- 💬 Refine your answer in a **chat with an AI mentor** until it gets close to the ideal

<br/>

## 🧭 How it was built

<div align="center">

<table>
<tr>
<td align="center" width="20%">🔍<br/><b>Observation</b><br/><sub>My own selection processes</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🗂️<br/><b>Curation</b><br/><sub>27 questions · technique · evaluator focus</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🧪<br/><b>Prototype</b><br/><sub>Prompts in Google Colab</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🖥️<br/><b>Streamlit app</b><br/><sub>3 steps · audio · chat</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🔐<br/><b>Accounts</b><br/><sub>Supabase · history</sub></td>
</tr>
</table>

</div>

The questions and the evaluator's expectations come from my own experience in selection processes. I designed the
product (flow, curation, visual identity and evaluation criteria), tested each version and brought the errors back,
using **Claude (Anthropic)** as a coding copilot.

**Real problems solved along the way:**

| Problem | Solution |
|---|---|
| Hard-coded Gemini model names returned *404* for my API key | The app **asks the API which "flash" models the key can use**, tries them in order and remembers the last one that worked |
| Evaluations taking too long to come back | The model's **"thinking" budget is reduced** on Gemini 2.5 models, so feedback arrives in seconds |
| The mentor's answer appeared only at the end | The refinement chat uses **streaming**, writing the answer as it is generated |
| Feedback too generic | Every prompt carries the **job posting, culture, résumé, technique and evaluator focus** |
| Progress lost when the page reloaded | Jobs, evaluations and chats are **saved per account** in Supabase and can be resumed |

<br/>

## 🛠️ Tech Stack

<table>
<tr>
<td width="50%" valign="top">

### 💻 Application
<img src="https://img.shields.io/badge/Python-111E16?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit-C98B8B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/HTML5-233A2C?style=for-the-badge&logo=html5&logoColor=white"/>
<img src="https://img.shields.io/badge/CSS3-B8955A?style=for-the-badge&logo=css3&logoColor=white"/>

</td>
<td width="50%" valign="top">

### 🤖 AI
<img src="https://img.shields.io/badge/Gemini%20API-233A2C?style=for-the-badge&logo=googlegemini&logoColor=white"/>
<img src="https://img.shields.io/badge/Google%20Search%20Grounding-B8955A?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/Prompt%20Engineering-C98B8B?style=for-the-badge&logoColor=white"/>
<img src="https://img.shields.io/badge/Audio%20Understanding-111E16?style=for-the-badge&logoColor=white"/>

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🗄️ Data & Auth
<img src="https://img.shields.io/badge/Supabase%20Auth-233A2C?style=for-the-badge&logo=supabase&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-111E16?style=for-the-badge&logo=postgresql&logoColor=white"/>
<img src="https://img.shields.io/badge/Row%20Level%20Security-B8955A?style=for-the-badge&logoColor=white"/>

</td>
<td width="50%" valign="top">

### 🧰 Tools
<img src="https://img.shields.io/badge/GitHub-111E16?style=for-the-badge&logo=github&logoColor=white"/>
<img src="https://img.shields.io/badge/Google%20Colab-B8955A?style=for-the-badge&logo=googlecolab&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit%20Cloud-C98B8B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/Claude%20(copilot)-233A2C?style=for-the-badge&logo=anthropic&logoColor=white"/>

</td>
</tr>
</table>

<br/>

## ✨ Features

| Feature | What it does |
|---|---|
| 🏢 **Job context** | Stores company, role, job description, culture and your résumé (PDF, DOCX or TXT) to personalize every evaluation |
| 🗂️ **Curated questions** | Each question comes with the **suggested methodology** and the **evaluator's focus** (what the recruiter is really looking for) |
| 🎙️ **Text or audio answers** | Type your answer or record it directly in the browser |
| 📝 **AI evaluation report** | Feedback aligned with the company's values and the keywords of the job posting |
| 🪄 **Narrative atelier** | Streaming chat with a mentor that can **search the web** for company trends |
| 🕘 **Full history** | Every job, evaluation and conversation is saved and can be resumed or deleted |
| 🔐 **Login and password recovery** | Each candidate has a private account and progress |
| 📱 **Responsive design** | Editorial, clean layout that also works on mobile |

<br/>

## 🔄 How it works

<div align="center">

<table>
<tr>
<td align="center" width="30%">📋<br/><b>Step 1</b><br/><sub>Job context</sub></td>
<td align="center">➜</td>
<td align="center" width="30%">🎙️<br/><b>Step 2</b><br/><sub>Simulation panel</sub></td>
<td align="center">➜</td>
<td align="center" width="30%">🪄<br/><b>Step 3</b><br/><sub>Refinement and feedback</sub></td>
</tr>
</table>

</div>

1. **Job context:** paste the job posting, company information and upload your résumé.
2. **Simulation panel:** choose a question, answer by text or audio and receive the evaluation.
3. **Refinement:** chat with the mentor to improve your answer using the evaluation as a base.

> Evaluations and conversations are linked to the **job** you registered, so you can prepare for several selection processes in parallel.

<br/>

## 🧩 Architecture

| Layer | File | What it does |
|---|---|---|
| 🖥️ Interface | `app.py` | Login, the 3 steps, history dialog and the editorial visual identity (custom CSS) |
| 🧠 AI engine | `gemini_engine.py` | Gemini client, model discovery and fallback, evaluation (text and audio) and chat streaming |
| 🗂️ Curation | `curadoria.py` | 27 questions with technique and evaluator focus, plus the general evaluation guidelines |
| 🗄️ Data | Supabase | Accounts (Auth) and the `usuarios` table with jobs, evaluations and chats |

<br/>

## 🚀 Getting started

Requires **Python 3.10+**, a free key from [Google AI Studio](https://aistudio.google.com/apikey) and a
[Supabase](https://supabase.com/) project with a `usuarios` table.

```bash
git clone https://github.com/amandapasqualotto/InterviewLabAI.git
cd InterviewLabAI
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Keys go in `.streamlit/secrets.toml` (or environment variables):

```toml
GEMINI_API_KEY = "your-gemini-key"
SUPABASE_URL   = "https://your-project.supabase.co"
SUPABASE_KEY   = "your-anon-key"
```

<br/>

## 📫 Author

<div align="center">

**Amanda Pasqualotto**, IT and Law student, passionate about Generative AI, Product and UX/UI.

<a href="https://www.linkedin.com/in/amanda-pasqualotto-b14ab6327/"><img src="https://img.shields.io/badge/LinkedIn-233A2C?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
<a href="mailto:amandapasqualotto.pf@gmail.com"><img src="https://img.shields.io/badge/Email-C98B8B?style=for-the-badge&logo=gmail&logoColor=white"/></a>
<a href="https://github.com/amandapasqualotto"><img src="https://img.shields.io/badge/GitHub-111E16?style=for-the-badge&logo=github&logoColor=white"/></a>

<br/><br/>

<a href="#portugues">🇧🇷 Ler em Português</a> &nbsp;|&nbsp; <a href="#english">⬆️ Back to top</a>

</div>

<br/>

---

<br/>

<!-- ======================================================== -->
<!-- ====================== PORTUGUÊS ======================= -->
<!-- ======================================================== -->

<a id="portugues"></a>

# 🇧🇷 Português

## 🌿 Sobre o projeto

> *"Muita gente é eliminada logo na primeira etapa, a entrevista com IA ou com o RH, simplesmente porque ninguém ensinou como responder."*

Ao me inscrever em diversos processos seletivos de estágio e trainee, percebi um padrão: a **fase inicial da
seleção** (entrevistas com IA e triagem com RH) repete um **conjunto pequeno de perguntas frequentes**, e é
justamente aí que muitos candidatos "rodam".

Por isso, fiz uma curadoria dessas perguntas e criei o **Interview Lab AI**, uma ferramenta para **treinar com a
vaga real em mãos**:

- 📋 Cole a **vaga**, a descrição da empresa e a cultura, e envie seu **currículo**
- 🎯 Escolha uma das **27 perguntas curadas** de entrevista
- 🎙️ Responda por **texto ou áudio**, gravado direto no navegador
- 🧠 Receba uma **avaliação técnica** com base na resposta esperada, na técnica sugerida (como o **STAR**) e no contexto da vaga
- 💬 Refine sua resposta em um **chat com um mentor de IA** até chegar perto do ideal

<br/>

## 🧭 Como foi construído

<div align="center">

<table>
<tr>
<td align="center" width="20%">🔍<br/><b>Observação</b><br/><sub>Meus próprios processos seletivos</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🗂️<br/><b>Curadoria</b><br/><sub>27 perguntas · técnica · foco do avaliador</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🧪<br/><b>Protótipo</b><br/><sub>Prompts no Google Colab</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🖥️<br/><b>App Streamlit</b><br/><sub>3 etapas · áudio · chat</sub></td>
<td align="center">➜</td>
<td align="center" width="20%">🔐<br/><b>Contas</b><br/><sub>Supabase · histórico</sub></td>
</tr>
</table>

</div>

As perguntas e as expectativas do avaliador vêm da minha própria experiência em processos seletivos. Eu desenhei o
produto (fluxo, curadoria, identidade visual e critérios de avaliação), testei cada versão e trouxe os erros de
volta, usando o **Claude (Anthropic)** como copiloto de código.

**Problemas reais que resolvi no caminho:**

| Problema | Solução |
|---|---|
| Nomes fixos de modelo do Gemini davam *404* para a minha chave | O app **pergunta à API quais modelos "flash" a chave pode usar**, testa em ordem e guarda o último que funcionou |
| Pareceres demorando demais | O **"pensamento" do modelo é reduzido** nos modelos Gemini 2.5, e o feedback chega em segundos |
| A resposta do mentor só aparecia no final | O chat de lapidação usa **streaming**, escrevendo a resposta enquanto ela é gerada |
| Feedback genérico demais | Todo prompt leva a **vaga, a cultura, o currículo, a técnica e o foco do avaliador** |
| Progresso perdido ao recarregar a página | Vagas, pareceres e conversas ficam **salvos por conta** no Supabase e podem ser retomados |

<br/>

## 🛠️ Tecnologias

<table>
<tr>
<td width="50%" valign="top">

### 💻 Aplicação
<img src="https://img.shields.io/badge/Python-111E16?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit-C98B8B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/HTML5-233A2C?style=for-the-badge&logo=html5&logoColor=white"/>
<img src="https://img.shields.io/badge/CSS3-B8955A?style=for-the-badge&logo=css3&logoColor=white"/>

</td>
<td width="50%" valign="top">

### 🤖 IA
<img src="https://img.shields.io/badge/Gemini%20API-233A2C?style=for-the-badge&logo=googlegemini&logoColor=white"/>
<img src="https://img.shields.io/badge/Google%20Search%20Grounding-B8955A?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/Engenharia%20de%20Prompt-C98B8B?style=for-the-badge&logoColor=white"/>
<img src="https://img.shields.io/badge/Entendimento%20de%20%C3%81udio-111E16?style=for-the-badge&logoColor=white"/>

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🗄️ Dados e Autenticação
<img src="https://img.shields.io/badge/Supabase%20Auth-233A2C?style=for-the-badge&logo=supabase&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-111E16?style=for-the-badge&logo=postgresql&logoColor=white"/>
<img src="https://img.shields.io/badge/Row%20Level%20Security-B8955A?style=for-the-badge&logoColor=white"/>

</td>
<td width="50%" valign="top">

### 🧰 Ferramentas
<img src="https://img.shields.io/badge/GitHub-111E16?style=for-the-badge&logo=github&logoColor=white"/>
<img src="https://img.shields.io/badge/Google%20Colab-B8955A?style=for-the-badge&logo=googlecolab&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit%20Cloud-C98B8B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/Claude%20(copiloto)-233A2C?style=for-the-badge&logo=anthropic&logoColor=white"/>

</td>
</tr>
</table>

| Biblioteca | Uso |
|---|---|
| `streamlit` | Interface web, estado de sessão, gravação de áudio e diálogos |
| `google-genai` | API do Gemini: avaliação das respostas (texto e áudio) e chat com streaming |
| `supabase` | Contas de usuário e armazenamento do histórico |
| `pypdf` | Leitura do currículo (PDF) |
| `python-docx` | Leitura do currículo (DOCX) |

<br/>

## ✨ Funcionalidades

| Funcionalidade | O que faz |
|---|---|
| 🏢 **Contexto da vaga** | Guarda empresa, cargo, descrição, cultura e seu currículo (PDF, DOCX ou TXT) para personalizar cada avaliação |
| 🗂️ **Perguntas curadas** | Cada pergunta traz a **metodologia sugerida** e o **foco do avaliador** (o que o recrutador realmente busca) |
| 🎙️ **Resposta em texto ou áudio** | Digite a resposta ou grave direto no navegador |
| 📝 **Parecer da IA** | Feedback alinhado aos valores da empresa e às palavras-chave da vaga |
| 🪄 **Atelier de lapidação** | Chat com streaming e um mentor que pode **pesquisar na web** tendências da empresa |
| 🕘 **Histórico completo** | Cada vaga, parecer e conversa fica salvo, podendo ser retomado ou excluído |
| 🔐 **Login e recuperação de senha** | Cada candidato tem conta e progresso privados |
| 📱 **Design responsivo** | Layout editorial e limpo que também funciona no celular |

<br/>

## 🔄 Como funciona

<div align="center">

<table>
<tr>
<td align="center" width="30%">📋<br/><b>Etapa 1</b><br/><sub>Contexto da vaga</sub></td>
<td align="center">➜</td>
<td align="center" width="30%">🎙️<br/><b>Etapa 2</b><br/><sub>Painel de simulação</sub></td>
<td align="center">➜</td>
<td align="center" width="30%">🪄<br/><b>Etapa 3</b><br/><sub>Lapidação e feedback</sub></td>
</tr>
</table>

</div>

1. **Contexto da vaga:** cole o anúncio, as informações da empresa e envie seu currículo.
2. **Painel de simulação:** escolha uma pergunta, responda por texto ou áudio e receba a avaliação.
3. **Lapidação:** converse com o mentor para melhorar a resposta, usando o parecer como base.

> Pareceres e conversas ficam vinculados à **vaga** cadastrada, então dá para se preparar para vários processos seletivos ao mesmo tempo.

<br/>

## 🧩 Arquitetura

| Camada | Arquivo | O que faz |
|---|---|---|
| 🖥️ Interface | `app.py` | Login, as 3 etapas, histórico e a identidade visual editorial (CSS próprio) |
| 🧠 Motor de IA | `gemini_engine.py` | Cliente Gemini, descoberta e troca de modelos, avaliação (texto e áudio) e streaming do chat |
| 🗂️ Curadoria | `curadoria.py` | 27 perguntas com técnica e foco do avaliador, mais as diretrizes gerais de avaliação |
| 🗄️ Dados | Supabase | Contas (Auth) e a tabela `usuarios` com vagas, pareceres e conversas |

<br/>

## 🚀 Como rodar

Pré-requisitos: **Python 3.10+**, uma chave gratuita do [Google AI Studio](https://aistudio.google.com/apikey) e
um projeto no [Supabase](https://supabase.com/) com a tabela `usuarios`.

```bash
git clone https://github.com/amandapasqualotto/InterviewLabAI.git
cd InterviewLabAI
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

As chaves ficam em `.streamlit/secrets.toml` (ou em variáveis de ambiente):

```toml
GEMINI_API_KEY = "sua-chave-do-gemini"
SUPABASE_URL   = "https://seu-projeto.supabase.co"
SUPABASE_KEY   = "sua-anon-key"
```

<br/>

## 📫 Autora

<div align="center">

**Amanda Pasqualotto**, estudante de TI e Direito, apaixonada por IA Generativa, Produto e UX/UI.

<a href="https://www.linkedin.com/in/amanda-pasqualotto-b14ab6327/"><img src="https://img.shields.io/badge/LinkedIn-233A2C?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
<a href="mailto:amandapasqualotto.pf@gmail.com"><img src="https://img.shields.io/badge/Email-C98B8B?style=for-the-badge&logo=gmail&logoColor=white"/></a>
<a href="https://github.com/amandapasqualotto"><img src="https://img.shields.io/badge/GitHub-111E16?style=for-the-badge&logo=github&logoColor=white"/></a>

<br/><br/>

Feito com 🌿 por [Amanda Pasqualotto](https://github.com/amandapasqualotto)

<br/>

<a href="#english">🇺🇸 Read in English</a> &nbsp;|&nbsp; <a href="#portugues">⬆️ Voltar ao topo</a>

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:C98B8B,50:233A2C,100:111E16&height=120&section=footer" width="100%" alt="footer"/>
