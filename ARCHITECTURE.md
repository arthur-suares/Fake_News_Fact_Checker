# Arquitetura: Game + Knowledge Tracing MVP

Este documento detalha a arquitetura da nova versão do Fake News Fact Checker, baseada em games adaptativos e rastreamento de habilidades via BKT (Bayesian Knowledge Tracing).

## 1. Princípios de Design

### 1.1 Simplicidade
- MVP deve ser funcional e compreensível
- Sem microservices, Redis, Celery, ou complexidades desnecessárias
- Algoritmo de seleção adaptativa é propositalmente simples

### 1.2 Modularidade
- Cada módulo tem responsabilidade clara
- Permite desenvolvimento paralelo
- Minimiza conflitos de Git

### 1.3 Separação de Concerns
```
HTTP/API           (routes/)
    ↓
Services           (business logic)
    ↓
BKT/Domain         (regras de negócio, matemática)
    ↓
Repositories       (database access)
    ↓
Database           (SQLAlchemy)
```

### 1.4 Independência do BKT
- `backend/app/bkt/` é completamente independente
- Não importa nada que conheça User, Database, ou FastAPI
- Pode ser testado, reutilizado, ou migrado para outro projeto

## 2. Modelos de Dados

### 2.1 Diagrama de Relacionamento

```
User
  ├── Game (1:N)
  │   └── GameRound (1:N)
  │       ├── News (N:1)
  │       └── Answer (1:N)
  │           ├── Question (N:1)
  │           └── Skill (via Question)
  │
  └── UserSkillState (1:N)
      └── Skill (N:1)

Skill (4 registros: SOURCE, EVIDENCE, CONTEXT, VISUAL)
  ├── UserSkillState (1:N)
  ├── Question (1:N)
  │   ├── News (N:1)
  │   └── Answer (1:N)
```

### 2.2 Estados e Constrains

#### Game
- `status`: IN_PROGRESS | FINISHED
- `user_id`: Foreign Key → User
- Unique? Não (user pode ter múltiplos games)

#### GameRound
- `round_number`: Sequencial por game (1, 2, 3, ...)
- `game_id`: Foreign Key → Game
- `news_id`: Foreign Key → News
- Constraint: Uma rodada = uma notícia

#### Skill
- `code`: UNIQUE (SOURCE, EVIDENCE, CONTEXT, VISUAL)
- `code`: INDEXED (busca frequente)
- 4 registros fixos (seed na inicialização)

#### UserSkillState
- `user_id` + `skill_id`: UNIQUE constraint
- `mastery_probability`: 0.0 ≤ value ≤ 1.0
- `updated_at`: Atualizado toda vez que BKT executa

#### Question
- `news_id`: Foreign Key → News
- `skill_id`: Foreign Key → Skill
- Uma pergunta = uma skill (não multi-skill)
- `difficulty`: 0 (fácil) a 1 (difícil)
- `correct_option`: Letra (A, B, C, D, etc)

#### Answer
- `user_id`: Foreign Key → User
- `game_round_id`: Foreign Key → GameRound
- `question_id`: Foreign Key → Question
- `correct`: Observação do BKT (bool)
- `confidence`: 1-5 (opcional, para feedback)
- `response_time`: milliseconds (opcional, para analytics)

## 3. Componentes Principais

### 3.1 BKT Engine (`backend/app/bkt/engine.py`)

Implementação da fórmula matemática de BKT:

```
Mastery(n+1) = update(Mastery(n), correct, p_guess, p_slip, p_transition)

Parametrização:
- P(L0) = 0.30 → Probabilidade inicial de mastery
- P(G)  = 0.20 → Probabilidade de adivinhar corretamente sem domínio
- P(S)  = 0.05 → Probabilidade de errar sabendo
- P(T)  = 0.10 → Probabilidade de aprender com uma tentativa
```

**Propriedades**:
- Stateless (sem estado interno)
- Sem dependências externas
- Facilmente testável

### 3.2 Trackers (`backend/app/bkt/*_tracker.py`)

Cada skill tem um tracker que encapsula:
- Instância de `BKTEngine` com parâmetros específicos
- Interface uniforme `SkillTracker`
- Método `update(mastery, correct) → new_mastery`

Exemplo: `SourceTracker` usa os mesmos parâmetros padrão (isso pode variar em versões futuras).

### 3.3 BKT Manager (`backend/app/bkt/manager.py`)

Registry que mapeia skills para trackers:

```python
# Uso
new_mastery = BKTManager.update_skill("SOURCE", 0.35, correct=True)

# Internamente
- Valida skill code
- Seleciona tracker correto
- Delega ao tracker.update()
```

**Responsabilidades**:
- Manter registro central de skills válidas
- Validação de skill code
- Acesso a trackers individuais

### 3.4 Repositories (`backend/app/repositories/*.py`)

Abstração de acesso ao banco:

```python
# Exemplo
game = GameRepository.create_game(db, user_id)
rounds = GameRepository.get_game_rounds(db, game_id)
GameRepository.finish_game(db, game_id)
```

**Vantagens**:
- Services não conhecem SQLAlchemy direto
- Fácil mudar implementação (ex: cache, NoSQL)
- Testes podem usar mocks

### 3.5 Services (`backend/app/services/game.py`, `answer.py`)

Orquestração de lógica de negócio:

#### GameService
```python
GameService.create_game_with_first_round(db, user_id)
    → GameRepository.create_game()
    → GameService._ensure_user_skills_initialized()
    → QuestionSelector.select_next_question()
    → GameRepository.create_game_round()
    → retorna dict com game_id, round, question, news
```

#### AnswerService
```python
AnswerService.process_answer(
    db, user_id, game_round_id, question_id, 
    selected_option, confidence, response_time
)
    → QuestionRepository.get_question_by_id()
    → SkillRepository.get_user_skill_state()
    → BKTManager.update_skill()  # IMPORTANTE: atualização BKT
    → AnswerRepository.create_answer()
    → SkillRepository.update_user_skill_mastery()
    → retorna {correct, skill, old_mastery, new_mastery, explanation}
```

### 3.6 Adaptation: Question Selector (`backend/app/adaptation/question_selector.py`)

Estratégia MVP (simples, não otimizada):

```
1. Pegar todas as habilidades do usuário
2. Encontrar a com menor mastery_probability
3. Buscar uma pergunta dessa skill que não tenha sido respondida
4. Se todas as perguntas foram respondidas, permitir repetição
5. Fallback: retornar qualquer pergunta disponível
```

Permite que versões futuras implementem algoritmos mais sofisticados (DKT, RL, etc).

### 3.7 Routes (`backend/app/routes/game.py`, `skills.py`)

HTTP endpoints:

#### Game Routes
- `POST /api/games` → Criar game + primeira rodada
- `GET /api/games/{game_id}` → Status do game
- `GET /api/games/{game_id}/next` → Próxima pergunta

#### Skills Routes
- `GET /api/users/me/skills` → Perfil de habilidades do usuário
- `POST /api/games/{game_id}/answers` → Submeter resposta

**Nota**: Authentication é placeholder (TODO).

## 4. Fluxo de Dados

### 4.1 Criar Game

```
POST /api/games
  ↓
GameService.create_game_with_first_round(db, user_id)
  ├─ GameRepository.create_game(db, user_id)
  │   → INSERT INTO games (user_id, status, started_at)
  │   ← Game(id=g1, status=IN_PROGRESS)
  │
  ├─ GameService._ensure_user_skills_initialized()
  │   → For each Skill in [SOURCE, EVIDENCE, CONTEXT, VISUAL]
  │       → SkillRepository.get_or_create_user_skill_state(db, user_id, skill_id)
  │           → INSERT into user_skill_states IF NOT EXISTS
  │               (user_id, skill_id, mastery_probability=0.3)
  │
  ├─ QuestionSelector.select_next_question(db, user_id, game_id)
  │   ├─ SkillRepository.get_user_skill_states(db, user_id)
  │   │   ← [UserSkillState(skill=SOURCE, mastery=0.3), ...]
  │   │
  │   ├─ Find skill with lowest mastery → SOURCE (0.3)
  │   │
  │   └─ QuestionRepository.get_questions_by_skill(db, SOURCE.id)
  │       ← [Question(id=q1, skill=SOURCE, news=n1), ...]
  │       ← Pick first → q1
  │       ← Associated News → n1
  │
  ├─ GameRepository.create_game_round(db, game_id, n1.id, round_number=1)
  │   → INSERT INTO game_rounds (game_id, news_id, round_number)
  │   ← GameRound(id=r1, round_number=1)
  │
  └─ Return {game_id, round, news, question}
```

### 4.2 Responder Pergunta

```
POST /api/games/{game_id}/answers
  {
    question_id: "q1",
    game_round_id: "r1",
    selected_option: "A",
    confidence: 4,
    response_time: 5320
  }
  ↓
AnswerService.process_answer(db, user_id, ...)
  ├─ QuestionRepository.get_question_by_id(db, "q1")
  │   ← Question(id=q1, correct_option="A", skill=SOURCE)
  │
  ├─ is_correct = ("A" == "A") → TRUE
  │
  ├─ SkillRepository.get_user_skill_state(db, user_id, SOURCE.id)
  │   ← UserSkillState(mastery=0.30)
  │
  ├─ BKTManager.update_skill("SOURCE", 0.30, correct=TRUE)
  │   ├─ Get SourceTracker
  │   ├─ tracker.update(0.30, True)
  │   │   ├─ BKTEngine.update(0.30, True)
  │   │   │   ├─ predicted = 0.30 * (1 - 0.10) + (1 - 0.30) * 0.10 = 0.34
  │   │   │   ├─ numerator = 0.34 * (1 - 0.05) = 0.323
  │   │   │   ├─ denominator = 0.34 * (1 - 0.05) + (1 - 0.34) * 0.20 = 0.323 + 0.132 = 0.455
  │   │   │   └─ result = 0.323 / 0.455 = 0.71
  │   │   └─ Return 0.71
  │   └─ Return 0.71
  │
  ├─ AnswerRepository.create_answer(db, user_id, "r1", "q1", "A", correct=True, ...)
  │   → INSERT INTO answers (...)
  │   ← Answer(id=a1)
  │
  ├─ SkillRepository.update_user_skill_mastery(db, user_id, SOURCE.id, 0.71)
  │   → UPDATE user_skill_states SET mastery_probability=0.71, updated_at=NOW()
  │   ← UserSkillState(mastery=0.71, updated_at=NOW())
  │
  └─ Return {
      correct: TRUE,
      skill_code: "SOURCE",
      old_mastery: 0.30,
      new_mastery: 0.71,
      explanation: "..."
    }
```

### 4.3 Próxima Pergunta

```
GET /api/games/{game_id}/next
  ↓
GameService.get_next_question(db, user_id, game_id)
  ├─ GameRepository.get_game_by_id(db, game_id)
  ├─ Check game.status (should be IN_PROGRESS)
  ├─ Get last round number (currently = 1)
  ├─ Check if round_number >= 10 → NO, continue
  │
  ├─ QuestionSelector.select_next_question(db, user_id, game_id)
  │   ├─ Get used news IDs from game_rounds → [n1]
  │   ├─ Get user skills → [SOURCE: 0.71, EVIDENCE: 0.30, CONTEXT: 0.30, VISUAL: 0.30]
  │   ├─ Find lowest → EVIDENCE: 0.30
  │   ├─ Get questions for EVIDENCE skill
  │   ├─ Find one with news NOT in [n1] → q2 (news=n2)
  │   └─ Return (q2, n2)
  │
  ├─ GameRepository.create_game_round(db, game_id, n2.id, round_number=2)
  │   → INSERT INTO game_rounds (game_id, news_id, round_number=2)
  │   ← GameRound(id=r2, round_number=2)
  │
  └─ Return {game_id, round, news, question}
       (Próximo usuario clica e a pergunta aparece)
```

## 5. Testes

### 5.1 BKT Tests (`backend/tests/bkt/`)

```
test_engine.py
  ✓ Initialization
  ✓ Parameter validation
  ✓ Correct answer increases mastery
  ✓ Incorrect answer decreases mastery
  ✓ Result bounded [0, 1]
  ✓ Convergence tests
  ✓ Edge cases

test_trackers.py
  ✓ All trackers implement interface
  ✓ Manager maps skills correctly
  ✓ Invalid skill rejection
  ✓ Tracker consistency
```

### 5.2 Integration Tests (RF-21)

```
Testes de ponta a ponta sem mockar banco/BKT:
  - Criar game
  - Responder pergunta
  - Verificar atualização de mastery
  - Verificar seleção da próxima pergunta
```

### 5.3 Rodando Testes

```bash
# Instalar pytest (já em requirements.txt)
pip install pytest

# Rodar testes BKT
pytest backend/tests/bkt/ -v

# Rodar testes específicos
pytest backend/tests/bkt/test_engine.py::TestBKTEngine::test_update_correct_answer_increases_mastery -v

# Rodar todos os testes
pytest backend/tests/ -v
```

## 6. Desenvolvimento Paralelo

A arquitetura permite que diferentes pessoas/equipes trabalhem em paralelo:

### Pessoa 1: BKT + Engine
- `backend/app/bkt/engine.py` ← Implementar fórmula
- `backend/tests/bkt/test_engine.py` ← Testar isoladamente

### Pessoa 2: Trackers
- `backend/app/bkt/source_tracker.py`
- `backend/app/bkt/evidence_tracker.py`
- (usa BKTEngine da Pessoa 1)

### Pessoa 3: Repositories + Services
- `backend/app/repositories/*.py`
- `backend/app/services/*.py`
- (independente de BKT enquanto interface é estável)

### Pessoa 4: Routes + API
- `backend/app/routes/game.py`
- `backend/app/routes/skills.py`
- (integra services da Pessoa 3)

### Pessoa 5: Frontend
- `frontend/app/game/`
- `frontend/components/game/`
- (consome API da Pessoa 4)

### Pessoa 6: Seed + Testes
- `backend/seed/`
- `backend/tests/integration/`

**Chave**: Cada componente tem interface clara e não interfere nos outros.

## 7. Migrações e Banco de Dados

### 7.1 Abordagem Atual

- Usando `Base.metadata.create_all(bind=engine)` em `main.py`
- Rápido para MVP
- **Problema**: Difícil para produção com múltiplas instâncias

### 7.2 Futuro (após MVP)

Migrar para Alembic:

```bash
alembic init -t async backend/alembic
alembic revision --autogenerate -m "Initial: Game, Skill, UserSkillState"
alembic upgrade head
```

### 7.3 Compatibilidade

- Testes locais: SQLite
- CI/CD: SQLite
- Produção: PostgreSQL
- Modelos evitam features específicas do DB

## 8. Documentação de Componentes

### Pasta `/backend/app/bkt/`
- **Propósito**: Núcleo matemático isolado
- **Dependências**: Nenhuma (puro Python)
- **Acoplamento**: Baixo (interface padrão)
- **Testabilidade**: Alta

### Pasta `/backend/app/repositories/`
- **Propósito**: Abstração de banco de dados
- **Dependências**: SQLAlchemy, models
- **Acoplamento**: Médio (conhece modelos)
- **Testabilidade**: Média (pode mockar)

### Pasta `/backend/app/services/`
- **Propósito**: Regra de negócio
- **Dependências**: Repositories, BKT
- **Acoplamento**: Médio
- **Testabilidade**: Média

### Pasta `/backend/app/routes/`
- **Propósito**: HTTP endpoints
- **Dependências**: Services, schemas
- **Acoplamento**: Alto (conhece FastAPI)
- **Testabilidade**: Baixa (precisa mocking HTTP)

## 9. Checklist para Completar MVP

- [x] Modelos de dados (Game, Skill, UserSkillState, Question, Answer, etc)
- [x] BKTEngine + Trackers
- [x] BKTManager
- [x] Repositories (Game, Skill, Question, Answer)
- [x] QuestionSelector (adaptação simples)
- [x] Services (Game, Answer)
- [x] Routes (game, skills)
- [x] Testes BKT
- [ ] Seed de notícias/perguntas (RF-19)
- [ ] Frontend components (RF-14 a RF-18)
- [ ] Testes de integração (RF-21)
- [ ] Auth propriamente implementada
- [ ] Validações mais robustas
- [ ] Documentação adicional

## 10. Roadmap Pós-MVP

1. **Migrations com Alembic** ← Essencial para produção
2. **Auth com JWT** ← Segurança
3. **Algoritmos adaptativos mais sofisticados** ← ML futuro
4. **Analytics** ← Entender uso
5. **Gamification** ← Badges, pontos, leaderboard
6. **Multiplayer** ← Competição
7. **DKT (Deep Knowledge Tracing)** ← Se BKT não suficiente

---

**Autor**: Refatoração para MVP Game + KT
**Data**: 2026-10-07
**Status**: Arquitetura definida, implementação em andamento
