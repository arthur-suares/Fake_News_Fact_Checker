# Projeto _Verifica_ - Residência em IA Eldorado|UnB

## Descrição 
Este é um projeto desenvolvido por alunos participantes do programa de residência em IA feito em parceria entre a Universidade de Brasília e o Instituto Eldorado. Motivados pelo tema de fake news, este projeto tenta reforçar o pensamento crítico dos usuários da aplicação desenvolvida utilizando tecnologias de IA, mais especificamente o _Bayesian Knowledge Tracing_(BKT), para rastrear como está o aprendizado do usuário nas habilidades de análise crítica de notícias para que o próprio usuário consiga determinar a confiança e validade de uma notícia.

## Vídeo de Apresentação do projeto
https://youtu.be/Wkn8gjQ_tHc

## Link do Repositório do Github
https://github.com/arthur-suares/Projeto_Verifica_2026/

## Documentação do projeto
https://arthur-suares.github.io/Fake_News_Fact_Checker/

# Arquitetura do projeto
Backend desenvolvido em Python utilizando **FastAPI** para consultar a **Google Fact Check Tools API**.

A aplicação disponibiliza uma API própria que recebe uma afirmação ou assunto e consulta verificações existentes na API do Google.

## Nova arquitetura — Game + Knowledge Tracing

O projeto evoluiu de um fluxo baseado em questionário inicial para uma arquitetura orientada a jogo, rodadas, perguntas e rastreamento de domínio por habilidade.

```text
User
 ↓
Game
 ↓
GameRound
 ↓
Question
 ↓
Answer
 ↓
BKTManager
 ↓
SkillTracker
 ↓
BKTEngine
 ↓
UserSkillState
 ↓
Adaptive Question Selection
```

### Habilidades do MVP

As quatro habilidades centrais são:

- SOURCE: capacidade de analisar origem e fonte da informação.
- EVIDENCE: capacidade de avaliar evidências que sustentam a alegação.
- CONTEXT: capacidade de perceber contexto omitido, distorcido ou incompatível.
- VISUAL: capacidade de validar se uma imagem realmente sustenta a alegação.

### Onde fica o BKT

A lógica principal do BKT está em:

- `backend/app/bkt/engine.py` — matemática central do algoritmo
- `backend/app/bkt/base.py` — interface comum dos trackers
- `backend/app/bkt/manager.py` — registro de skills e atualização por habilidade
- `backend/app/bkt/source_tracker.py`
- `backend/app/bkt/evidence_tracker.py`
- `backend/app/bkt/context_tracker.py`
- `backend/app/bkt/visual_tracker.py`

### Onde ficam as partidas e as habilidades

- `backend/app/services/game.py` — lógica de criação de partida e rodadas
- `backend/app/services/answer.py` — processamento da resposta e atualização de domínio
- `backend/app/adaptation/question_selector.py` — seleção adaptativa simples
- `backend/app/models.py` — modelos do domínio, incluindo `Game`, `GameRound`, `Skill`, `UserSkillState`, `Question` e `Answer`

## Como rodar o projeto?

### Como iniciar o backend

```bash
cd Fake_News_Fact_Checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
```

### Como iniciar o frontend

```bash
cd Fake_News_Fact_Checker/frontend
npm install
npm run dev
```

### Como rodar teste

```bash
cd Fake_News_Fact_Checker
source .venv/bin/activate
cd backend
pytest -q
```

### Migrations (Alembic)

As migrations ficam em `backend/migrations/versions/` e usam o mesmo `DATABASE_URL` da aplicação:

```bash
cd backend
alembic upgrade head      # aplica as migrations pendentes
alembic downgrade -1      # desfaz a última
```

- `0001` (RF-02): cria `skills` e `user_skill_states`, cadastra as quatro skills (SOURCE, EVIDENCE, CONTEXT, VISUAL) e garante no máximo um estado por usuário + skill, com `mastery_probability` entre 0 e 1.
- `0002` (RF-04): cria `answers` (vinculada a usuário, rodada e pergunta) com `confidence` entre 1 e 5 e `response_time` em milissegundos (≥ 0). Num banco vazio cria também `news`, `questions`, `games` e `game_rounds`.

As migrations também funcionam em bancos já criados pelo `create_all`, completando só o que falta.

### Legacy / compatibilidade

A verificação de notícias e o questionário pós-verificação continuam presentes como rotas legadas. O antigo cálculo de perfil (GMM) foi removido: o fluxo principal do MVP utiliza `UserSkillState` + `BKTManager` + `SkillTracker`.

---

## 1. Pré-requisitos

Antes de iniciar, é necessário ter instalado:

* Python 3.10 ou superior
* `pip`
* Uma conta no Google Cloud
* Uma API Key com acesso à **Fact Check Tools API**

---

## 2. Clonar ou acessar o projeto

Entre no diretório do projeto:

```bash
cd Fake_News_Fact_Checker
```

---

## 3. Criar ambiente virtual

Recomenda-se utilizar um ambiente virtual Python.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 4. Instalar as dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

As principais dependências são:

```text
fastapi
uvicorn
requests
python-dotenv
pydantic-settings
```

### Função das dependências

* **FastAPI** — framework utilizado para criar a API HTTP.
* **Uvicorn** — servidor ASGI responsável por executar a aplicação FastAPI.
* **Requests** — utilizado para realizar requisições HTTP para a API do Google.
* **python-dotenv** — permite carregar variáveis de ambiente a partir do arquivo `.env`.
* **pydantic-settings** — utilizado para gerenciar as configurações da aplicação.

---

## 5. Configurar a Google Fact Check Tools API

É necessário criar um projeto no Google Cloud e ativar a:

**Fact Check Tools API**

A API Key pode ser criada em:

**Google Cloud Console → APIs e serviços → Credenciais → Criar credenciais → Chave de API**

A aplicação utiliza o endpoint:

```text
https://factchecktools.googleapis.com/v1alpha1/claims:search
```

---

## 6. Configurar a API Key

Na raiz do projeto, crie um arquivo chamado:

```text
.env
```

Adicione:

```env
GOOGLE_FACT_CHECK_API_KEY=SUA_API_KEY_AQUI
```

Exemplo:

```env
GOOGLE_FACT_CHECK_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX
```

### Importante

O arquivo `.env` não deve ser enviado para o Git.

Certifique-se de que ele esteja presente no `.gitignore:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## 7. Estrutura do projeto

A estrutura esperada é:

```text
fact-check-backend/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
│
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── models.py
    │
    └── services/
        ├── __init__.py
        └── google_fact_check.py
```

---

## 8. Executar o servidor

Com o ambiente virtual ativado, execute:

```bash
uvicorn app.main:app --reload
```

O servidor será iniciado, normalmente, em:

```text
http://localhost:8000
```

A opção `--reload` faz com que o servidor seja reiniciado automaticamente quando os arquivos do projeto forem alterados.

---

## 9. Verificar se o servidor está funcionando

Abra no navegador:

```text
http://localhost:8000/
```

Resposta esperada:

```json
{
    "message": "Fact Check Backend",
    "status": "running"
}
```

Também é possível verificar o endpoint de saúde:

```text
http://localhost:8000/health
```

Resposta:

```json
{
    "status": "ok"
}
```

---
