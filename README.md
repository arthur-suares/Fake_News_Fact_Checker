# Fake_News_Fact_Checker

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

### Legacy / compatibilidade

A arquitetura antiga continua preservada como legado e compatibilidade:

- `Profile`
- `GMM / perfil antigo`
- `modelo_perfis.joblib`
- questionário inicial e rotas legadas de verificação

Esses componentes continuam presentes para não quebrar funcionalidades existentes, mas o fluxo principal do MVP deve utilizar `UserSkillState` + `BKTManager` + `SkillTracker`.

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

## 10. Documentação Swagger

O FastAPI fornece uma documentação interativa automaticamente.

Acesse:

```text
http://localhost:8000/docs
```

Nessa página será possível visualizar e testar as rotas da API.

---

## 11. Consultar uma afirmação

A principal rota do backend é:

```http
GET /api/fact-check
```

Ela recebe o parâmetro:

```text
query
```

Exemplo:

```text
http://localhost:8000/api/fact-check?query=vacinas%20causam%20autismo
```

Também podem ser utilizados:

```text
language_code
page_size
max_age_days
```

Exemplo:

```text
http://localhost:8000/api/fact-check?query=vacinas%20causam%20autismo&language_code=pt-BR&page_size=10
```

---

## 12. Teste utilizando Postman

Abra o Postman e crie uma nova requisição.

### Método

```text
GET
```

### URL

```text
http://localhost:8000/api/fact-check
```

Em **Params**, adicione:

| Key             | Value                    |
| --------------- | ------------------------ |
| `query`         | `vacinas causam autismo` |
| `language_code` | `pt-BR`                  |
| `page_size`     | `10`                     |

Clique em **Send**.

O backend irá:

```text
Postman
   ↓
FastAPI
   ↓
Google Fact Check Tools API
   ↓
FastAPI
   ↓
Postman
```

A resposta será um JSON contendo as verificações encontradas.

---

## 13. Exemplo de resposta

Uma resposta poderá possuir a seguinte estrutura:

```json
{
    "claims": [
        {
            "text": "Criança desenvolve autismo após receber 18 doses de vacina em um único dia",
            "claimant": "Postagens em redes sociais",
            "claimReview": [
                {
                    "publisher": {
                        "name": "Estadão",
                        "site": "estadao.com.br"
                    },
                    "title": "É falso que criança tenha recebido 18 vacinas e desenvolvido autismo",
                    "textualRating": "Falso",
                    "languageCode": "pt"
                }
            ]
        }
    ]
}
```

O campo `textualRating` representa a classificação atribuída pelo veículo ou organização responsável pela verificação.

---

## 14. Testes adicionais

É possível testar diferentes afirmações.

### Exemplo 1

```text
query = vacinas causam autismo
```

### Exemplo 2

```text
query = terra plana
```

### Exemplo 3

```text
query = beber água cura qualquer doença
```

Também é recomendado testar uma requisição sem `query`:

```text
GET http://localhost:8000/api/fact-check
```

Nesse caso, a API deverá retornar:

```text
422 Unprocessable Entity
```

pois o parâmetro `query` é obrigatório.

---

## 15. Perfil do usuário (questionário)

Depois da verificação, o frontend salva o questionário em:

```http
POST /api/verifications/{verification_id}/feedback
```

```json
{
    "answers": {"q1": 4, "q2": 5, "q3": 2, "q4": 5, "q5": 1, "q6": 1, "q7": 1, "q8": 2, "q9": 3}
}
```

* `q1`..`q7`: perguntas do perfil (escala de 1 a 5).
* `q8`: pergunta invertida da `q4`, usada para corrigir quem concorda ou discorda de tudo.
* `q9`: mudança de opinião depois da verificação (não entra no modelo).

Ao salvar, o perfil é calculado na hora (hook síncrono) por um **Gaussian Mixture Model** (com K-Means como baseline). Questionários incompletos são salvos, mas não geram perfil.

Rotas:

| Método | Rota | O que faz |
| ------ | ---- | --------- |
| `GET`  | `/api/verifications/{verification_id}/profile` | Retorna o perfil salvo (404 se não houver) |
| `POST` | `/api/verifications/{verification_id}/profile` | Recalcula a partir do último questionário (422 se incompleto) |

Resposta:

```json
{
    "verification_id": "123",
    "profile_result": {
        "assigned_cluster": 4,
        "cluster_label": "Cético de baixa circulação",
        "probabilities": {"cluster_0": 0.0, "cluster_1": 0.0, "cluster_2": 0.0, "cluster_3": 0.0, "cluster_4": 1.0, "cluster_5": 0.0},
        "details": {"confidence": 1.0, "second_label": "Verificador crítico", "kmeans_label": "Cético de baixa circulação", "acquiescence": 0.0, "alerts": []},
        "processed_at": "2026-09-30T10:00:00"
    }
}
```

O modelo fica em `backend/app/ml/modelo_perfis.joblib` e é gerado por `treinamento/treinar.py`. Treino, validação e matriz de confusão estão documentados em [`treinamento/README.md`](treinamento/README.md).

---

## 16. Encerrar o servidor

Para parar o servidor:

```text
CTRL + C
```

Para sair do ambiente virtual:

```bash
deactivate
```

---

## 17. Fluxo completo

O funcionamento do sistema pode ser resumido da seguinte forma:

```text
                 Usuário / Frontend
                         │
                         │ HTTP
                         ▼
              ┌─────────────────────┐
              │   FastAPI Backend   │
              │                     │
              │ /api/fact-check     │
              └──────────┬──────────┘
                         │
                         │ HTTPS
                         │ API Key
                         ▼
              ┌─────────────────────┐
              │ Google Fact Check   │
              │ Tools API           │
              └──────────┬──────────┘
                         │
                         ▼
                  Fact-checks
                   existentes
                         │
                         ▼
              ┌─────────────────────┐
              │   JSON Response     │
              └─────────────────────┘
```

O backend funciona como uma camada intermediária entre o sistema cliente e a Google Fact Check Tools API. Isso permite que posteriormente outros componentes, como um **MCP Server**, consumam o backend sem precisar acessar diretamente a API da Google ou armazenar sua API Key.

---

## 18. Nova Arquitetura — Game + Knowledge Tracing

O projeto está evoluindo para um novo modelo baseado em **jogos adaptativos** com rastreamento de habilidades via **Bayesian Knowledge Tracing (BKT)**.

### 18.1 Visão Geral

Em vez de um questionário inicial com diagnóstico psicológico, o sistema agora oferece:

1. **Games**: Sessões onde o usuário responde perguntas sobre notícias
2. **Habilidades**: Quatro dimensões de competência em análise de informação
3. **Rastreamento Adaptativo**: BKT atualiza a probabilidade de domínio após cada resposta
4. **Seleção Adaptativa**: A próxima pergunta é escolhida para otimizar aprendizado

### 18.2 As Quatro Habilidades

```
SOURCE    → Capacidade de analisar a origem/fonte da informação
EVIDENCE  → Capacidade de avaliar as evidências apresentadas
CONTEXT   → Capacidade de perceber contexto omitido ou distorcido
VISUAL    → Capacidade de avaliar relação entre imagem e alegação
```

As habilidades **não** são perfil psicológico ou personalidade, mas sim um **perfil de habilidades de avaliação de informação**.

### 18.3 Arquitetura de Camadas

```
┌─────────────────────────────────────┐
│         Frontend (Next.js)          │
│      /game, /profile                │
└────────────────┬────────────────────┘
                 │
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────┐
│        API Routes (FastAPI)         │
│   POST /api/games                   │
│   POST /api/games/{id}/answers      │
│   GET  /api/users/me/skills         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│     Services (Business Logic)       │
│   - GameService                     │
│   - AnswerService                   │
│   - QuestionSelector (Adaptation)   │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  BKT (Bayesian Knowledge Tracing)   │
│   - BKTEngine (Math)                │
│   - BKTManager (Registry)           │
│   - SourceTracker                   │
│   - EvidenceTracker                 │
│   - ContextTracker                  │
│   - VisualTracker                   │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Repositories (Database Access)     │
│   - GameRepository                  │
│   - SkillRepository                 │
│   - QuestionRepository              │
│   - AnswerRepository                │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   SQLAlchemy + SQLite/PostgreSQL    │
└─────────────────────────────────────┘
```

### 18.4 Fluxo de um Game

```
1. Usuário inicia jogo
   ↓ POST /api/games
   └→ GameService cria Game + primeira GameRound
      └→ QuestionSelector escolhe pergunta baseada em skills fracos
         └→ UserSkillState inicializado com mastery_probability=0.3

2. Usuário vê pergunta
   ↓
   └→ Responde com opção + confiança + tempo

3. Backend processa resposta
   ↓ POST /api/games/{game_id}/answers
   └→ AnswerService valida e armazena
      └→ BKTManager.update_skill() atualiza probabilidade
         └→ UserSkillState atualizado com nova mastery
            └→ Feedback enviado ao usuário

4. Próxima rodada
   ↓ GET /api/games/{game_id}/next
   └→ GameService.get_next_question()
      └→ QuestionSelector escolhe com base em novo perfil
         └→ GameRound criada automaticamente

5. Fim após 10 rodadas ou sem perguntas
   ↓
   └→ Game.status = FINISHED
```

### 18.5 Estrutura de Diretórios

```
backend/app/
  ├── bkt/                          # Núcleo BKT (puro, sem DB)
  │   ├── engine.py                 # Fórmula matemática BKT
  │   ├── manager.py                # Registry de trackers
  │   ├── base.py                   # Interface SkillTracker
  │   ├── source_tracker.py         # SOURCE skill
  │   ├── evidence_tracker.py       # EVIDENCE skill
  │   ├── context_tracker.py        # CONTEXT skill
  │   └── visual_tracker.py         # VISUAL skill
  │
  ├── adaptation/
  │   └── question_selector.py      # Seleção adaptativa simples
  │
  ├── repositories/                 # Database access
  │   ├── game_repository.py
  │   ├── skill_repository.py
  │   ├── question_repository.py
  │   └── answer_repository.py
  │
  ├── services/
  │   ├── game.py                   # Game business logic
  │   ├── answer.py                 # Answer + BKT update
  │   ├── verification.py           # LEGACY
  │   └── profile.py                # LEGACY
  │
  ├── routes/
  │   ├── game.py                   # POST /api/games, GET /api/games/{id}
  │   ├── skills.py                 # GET /api/users/me/skills, POST .../answers
  │   ├── verification.py           # LEGACY
  │   ├── feedback.py               # LEGACY
  │   ├── profile.py                # LEGACY
  │   └── auth.py
  │
  ├── models.py                     # SQLAlchemy models (new + legacy)
  ├── schemas.py                    # Pydantic schemas (new + legacy)
  ├── main.py                       # FastAPI app + route registration
  ├── database.py
  ├── config.py
  └── security.py

seed/                               # Initial data
  └── __init__.py                   # seed_skills(), seed_sample_data()

tests/
  ├── bkt/
  │   ├── test_engine.py           # BKT math tests
  │   └── test_trackers.py         # Tracker + Manager tests
  └── integration/
      └── ...                       # Integration tests (RF-21)
```

### 18.6 Principais Entidades (Novos Modelos)

| Entidade | Campos | Descrição |
| --- | --- | --- |
| `Game` | id, user_id, status, started_at, finished_at | Sessão de jogo do usuário |
| `GameRound` | id, game_id, news_id, round_number, started_at, finished_at | Uma rodada dentro de um jogo |
| `Skill` | id, code, name, description | Uma das 4 habilidades (SOURCE, EVIDENCE, CONTEXT, VISUAL) |
| `UserSkillState` | id, user_id, skill_id, mastery_probability, updated_at | Estado atual de domínio de skill do usuário (0..1) |
| `News` | id, title, content, image_url, verdict, fact_check_data | Notícia ou alegação a ser avaliada |
| `Question` | id, news_id, skill_id, text, difficulty, options, correct_option, explanation | Pergunta sobre uma notícia, associada a uma skill |
| `Answer` | id, user_id, game_round_id, question_id, selected_option, correct, confidence, response_time | Resposta do usuário a uma pergunta |

### 18.7 Pontos-Chave de Design

#### BKT é puro (sem dependências)
- `backend/app/bkt/engine.py` contém apenas matemática
- Não acessa banco, não conhece User, não conhece FastAPI
- Facilita testes e reutilização

#### Interfaces estáveis
- Todos os trackers implementam `SkillTracker` (abstract)
- Permite que diferentes pessoas trabalhem em diferentes trackers sem conflito

#### Separação clara de responsabilidades
- **API** (routes/) ← HTTP
- **Services** ← Regra de negócio
- **BKT** ← Matemática pura
- **Repositories** ← Banco de dados

#### Compatibilidade SQLite + PostgreSQL
- Modelos usam tipos padrão (String, Float, DateTime)
- Evita features específicas de um banco

### 18.8 Como Iniciar um Game (Exemplo)

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Testar com curl
curl -X POST http://localhost:8000/api/games \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"

# Resposta:
# {
#   "game_id": "abc123",
#   "round": {
#     "id": "round1",
#     "number": 1,
#     "news_id": "news1",
#     "question_id": "q1"
#   },
#   "news": {...},
#   "question": {...}
# }
```

### 18.9 Legacy: Perfil Antigo (GMM)

O sistema antigo baseado em **questionário + GMM** continua existente:

```
backend/app/ml/modelo_perfis.joblib  # Modelo treinado
backend/app/ml/perfil.py             # Predictor
backend/app/services/profile.py      # Service (LEGACY)
backend/app/routes/profile.py        # Endpoints (LEGACY)
```

**Não foi removido** porque pode ser necessário durante a transição. Para evitar confusão, considere renomear ou documentar como "LEGACY - GMM Profile System" em futuras versões.

### 18.10 Próximas Etapas (Issues RF-01 a RF-21)

A estrutura acima prepara o caminho para:

- **RF-01, RF-02**: Completar models (Game, Skill, UserSkillState) ✅
- **RF-03, RF-04**: Endpoints básicos do game ✅
- **RF-05**: BKTEngine matemático ✅
- **RF-06 a RF-09**: Trackers específicas ✅
- **RF-10 a RF-18**: Integração completa game/BKT/adaptation ✅
- **RF-19**: Seed de notícias e perguntas
- **RF-20**: Testes unitários BKT ✅
- **RF-21**: Testes de integração
- **Frontend**: Componentes game, profile, feedback

A arquitetura permite que **diferentes pessoas trabalhem em paralelo** sem conflitos, desde que sigam as interfaces definidas (ex: `SkillTracker`, `AnswerService`, etc.).

---

## 19. Rodando frontend + backend juntos

1. **Backend** (terminal 1) — o `.env` pode ficar na raiz do repositório ou em `backend/`:

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend** (terminal 2):

   ```bash
   cd frontend
   cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
   npm install
   npm run dev
   ```

3. Acesse `http://localhost:3000`.

Fluxo da integração:

| Etapa no frontend | Chamada ao backend |
| --- | --- |
| Envio da notícia (texto + imagem opcional) | `POST /api/verifications` (multipart) → `202 { id, status }` |
| Tela "Analisando notícia..." | `GET /api/verifications/{id}` a cada 1s até `status` = `completed`/`failed` |
| Resultado | `verdict` + `evidence` (fonte, classificação, link) |
| "Depois da verificação, sua opinião mudou?" | `POST /api/verifications/{id}/feedback` com as respostas do questionário inicial + `opiniaoMudou` |

Como a Google Fact Check API busca por afirmações curtas, quando o texto completo da notícia não retorna checagens o backend tenta novamente com a primeira frase e depois com palavras-chave.
