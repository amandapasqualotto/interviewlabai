# Interview Lab AI

Plataforma de preparação para entrevistas com Streamlit, Google Gemini e Supabase.
Inclui cadastro livre, login, recuperação de senha, perfil profissional, currículo,
simulações, perguntas da curadoria, respostas por texto/áudio, avaliações, mentor com
pesquisa na web, histórico e painel administrativo.

## 1. Arquivos do projeto

```text
interview_lab_ai/
├── app.py
├── curadoria.py
├── gemini_engine.py
├── requirements.txt
├── README.md
├── PRIVACY.md
├── auth/
│   └── service.py
├── database/
│   ├── client.py
│   ├── repository.py
│   └── schema.sql
└── .streamlit/
    └── secrets.toml.example
```

## 2. Criar o projeto Supabase

1. Entre em https://supabase.com/ e crie um projeto.
2. Abra **SQL Editor** no painel do projeto.
3. Abra `database/schema.sql`, copie todo o conteúdo e execute.
4. Em **Project Settings > API**, copie a Project URL e a chave `anon`/`publishable`.
5. Em **Authentication > URL Configuration**, configure a URL pública do app Streamlit como Site URL e adicione-a às Redirect URLs.
6. Em **Authentication > Providers > Email**, defina se a confirmação de e-mail ficará ativada. Se estiver ativada, o usuário deverá confirmar o endereço antes de entrar.

O SQL cria as tabelas, índices, políticas RLS e o bucket privado `candidate-resumes`.

## 3. Configurar o primeiro administrador

1. Faça o cadastro normal pelo site usando o e-mail que será administrador.
2. Confirme o e-mail, se a confirmação estiver habilitada, e entre na conta pelo menos uma vez.
3. No Supabase, abra **SQL Editor** e execute, substituindo pelo e-mail correto:

```sql
update public.profiles
set role = 'admin'
where id = (
  select id from auth.users
  where lower(email) = lower('admin@seudominio.com')
);
```

4. Saia e entre novamente no site. A conta passará a visualizar o painel administrativo.

Não disponibilize uma opção de escolher perfil administrativo no cadastro público.

## 4. Configurar o Streamlit Cloud

1. Envie todos os arquivos e pastas deste projeto para a raiz do repositório GitHub conectado ao Streamlit Cloud.
2. Confirme que o arquivo principal é `app.py` e que `requirements.txt` está na raiz.
3. No Streamlit Cloud, abra **App > Settings > Secrets** e adicione:

```toml
GEMINI_API_KEY = "SUA_CHAVE_GEMINI"
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_ANON_KEY = "SUA_CHAVE_ANON_PUBLIC"
```

4. Salve e reinicie/reimplante o aplicativo.

O arquivo `.streamlit/secrets.toml.example` é apenas um modelo. Não renomeie para `secrets.toml` com chaves reais dentro do GitHub. Nunca publique a chave `service_role` do Supabase.

## 5. Como o histórico funciona

- Cada simulação é vinculada ao identificador autenticado do candidato.
- Respostas e avaliações são salvas no banco após cada avaliação concluída.
- Mensagens do mentor são salvas individualmente.
- O candidato consulta e continua suas próprias simulações.
- O administrador autorizado consulta usuários, simulações, respostas, avaliações e conversas.
- Eventos de login, logout, criação de simulação e avaliação são registrados em `access_logs`.
- Currículos enviados são guardados em bucket privado; o texto extraído é armazenado para personalização da simulação.

O log não é um gravador de tela e não registra cada clique. Ele registra os eventos explicitamente implementados.

## 6. Privacidade e segurança

Leia `PRIVACY.md` e adapte os dados do controlador, contato, prazos de retenção e procedimentos de atendimento antes de disponibilizar publicamente.

As políticas RLS são parte essencial da proteção. Não remova as políticas nem use a chave `service_role` no app. A chave anon/public deve ser usada junto com a sessão autenticada do usuário.

Como o administrador pode visualizar históricos, informe isso claramente aos candidatos e limite as contas administrativas às pessoas autorizadas. Considere definir política de exclusão e retenção de currículos e históricos.

## 7. Execução local (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para execução local, crie `.streamlit/secrets.toml` com as três variáveis descritas acima. Esse arquivo não deve ser enviado ao GitHub.

## 8. Observações

- O mentor usa a ferramenta Google Search do Gemini quando a pesquisa externa é pertinente. A disponibilidade depende do modelo, da conta e da API.
- O LinkedIn pode restringir acesso automatizado. O link é usado como referência; o sistema não afirma ter lido conteúdo privado.
- O áudio é transcrito pelo Gemini e a transcrição é salva como resposta. O arquivo bruto de áudio não é armazenado.
- Currículos aceitos: PDF, DOCX e TXT, com limite de 10 MB no bucket.
- O app precisa ser validado no projeto Supabase real, com as chaves e as configurações de confirmação de e-mail escolhidas pelo proprietário.
