# Arquitetura do Projeto

## Visão geral da arquitetura

O sistema foi estruturado em camadas para separar responsabilidades bem definidas. O Frontend interage com o usuário; o Backend expõe APIs e coordena regras de negócio; o banco de dados persiste os dados do jogo, dos usuários, das habilidades e das respostas; e o modelo BKT atualiza o estado de domínio das competências ao longo das rodadas.

A arquitetura atual combina:

- uma interface web em Next.js;
- uma API em FastAPI;
- persistência em SQLAlchemy com banco relacional;
- lógica de BKT em módulos dedicados;
- integração com a Google Fact Check API como serviço externo de verificação.

## Diagrama conceitual

```text
Usuário
  ↓
Frontend (Next.js)
  ↓
API Backend (FastAPI)
  ├── Routes / Controllers
  ├── Services
  ├── Repositories
  ├── BKT Manager + Trackers
  └── Modelos do domínio
  ↓
Banco de dados (SQLAlchemy / SQLite em ambiente local)
  ↓
Google Fact Check API (serviço externo)
```

## Camadas principais

### 1. Frontend

O Frontend é responsável pela interface do usuário e pela navegação da experiência de jogo. Ele apresenta as rodadas, os questionários, os feedbacks e o estado atual do usuário.

No projeto, o frontend é implementado em Next.js e possui módulos para:

- apresentação da landing page;
- fluxo de jogo;
- perfil de habilidades;
- busca e verificação de notícia específica.

A camada de frontend não atua diretamente na lógica matemática do BKT nem no acesso ao banco. Ela comunica-se com o backend por meio de requisições HTTP.

### 2. Backend

O Backend é a camada central de orquestração do sistema. Ele recebe requisições, valida regras de negócio e coordena operações de persistência, autenticação e processamento de respostas.

Sua estrutura principal está organizada em:

- routes: endpoints REST para jogos, habilidades e verificação;
- services: lógica de negócio, como criação de jogo e processamento de resposta;
- repositories: acesso aos dados e operações de banco;
- models: entidades do domínio;
- config e database: configuração de ambiente e sessão do banco.

### 3. Banco de dados e modelos de domínio

Os dados principais do sistema são representados por entidades como:

- User;
- Skill;
- UserSkillState;
- News;
- Question;
- Game;
- GameRound;
- Answer.

Essas entidades permitem registrar:

- quem jogou;
- qual habilidade está sendo avaliada;
- a probabilidade de domínio da habilidade;
- qual notícia foi apresentada;
- qual pergunta foi respondida;
- se a resposta foi correta;
- o histórico da rodada e do jogo.

### 4. Módulo BKT

A lógica de conhecimento do usuário está concentrada em `backend/app/bkt`.

Esse módulo contém:

- `engine.py`: implementação do cálculo do BKT;
- `base.py`: interface comum para trackers;
- `manager.py`: registro dos trackers por habilidade;
- `source_tracker.py`, `evidence_tracker.py`, `context_tracker.py`, `visual_tracker.py`: trackers específicos para cada competência.

A responsabilidade do BKT é atualizar a probabilidade de domínio do usuário para uma habilidade específica com base no resultado da resposta.

## Fluxo de funcionamento do jogo

### Criação de partida

Quando o usuário inicia um jogo, o backend:

1. garante que existam estados iniciais para as habilidades do usuário;
2. cria um objeto `Game` associado ao usuário;
3. seleciona a próxima pergunta com base no nível atual do usuário;
4. cria a primeira `GameRound` com a notícia e a pergunta associadas;
5. retorna o payload inicial para o frontend.

### Resposta do usuário

Ao enviar a resposta, o backend executa o seguinte fluxo:

1. valida se o jogo e a rodada pertencem ao usuário;
2. verifica se a pergunta é válida para a rodada;
3. compara a escolha com a opção correta;
4. identifica a competência da pergunta;
5. busca o estado atual da habilidade no `UserSkillState`;
6. aplica o BKT para atualizar a mastery probability;
7. persiste a resposta;
8. atualiza a habilidade no banco;
9. retorna o feedback com o resultado e a nova probabilidade.

### Seleção adaptativa

A seleção da próxima pergunta é feita por `QuestionSelector`, que prioriza a habilidade com menor domínio ou maior necessidade de reforço. Esse mecanismo é o núcleo da experiência adaptativa do projeto.

## Fluxo de dados e persistência

A camada de persistência é orientada por repositories, que centralizam as operações de acesso ao banco. Isso mantém a lógica de negócios mais limpa e facilita manutenção e testes.

Exemplo de organização:

- `game_repository.py`: jogos e rodadas;
- `skill_repository.py`: habilidades e estados de domínio;
- `question_repository.py`: perguntas e notícias;
- `answer_repository.py`: respostas registradas pelo usuário.

A separação entre services e repositories reduz a acoplamento e organiza melhor o padrão de acesso a dados.

## integração com API externa

O projeto também contempla uma integração com a Google Fact Check API, responsável por consultar verificações de fatos em notícias e conteúdos públicos.

Essa integração é acessada principalmente no módulo de verificação de notícias e não faz parte do mecanismo principal de aprendizagem do jogo. Ela funciona como suporte documental e de contexto para a análise de conteúdos específicos.

## Relação com o produto

A arquitetura atual mantém uma divisão clara entre:

- aprendizagem e gamificação;
- rastreamento de conhecimento;
- verificação factual externa;
- apresentação ao usuário.

Essa separação é importante porque permite evoluir o sistema sem misturar o modelo educacional, a lógica de jogo e a integração externa.

## Padrões de projeto observados

O projeto segue algumas boas práticas de organização de software:

- separação de camadas;
- uso de serviços para regras de negócio;
- repositories para acesso a dados;
- models para representação do domínio;
- endpoints dedicados por funcionalidade;
- uso de BKT como módulo independente e reutilizável.

## Pontos importantes da arquitetura atual

- O modelo BKT está encapsulado em um conjunto de trackers por habilidade, permitindo extensão para novas competências no futuro.
- O fluxo de jogo é totalmente orientado a rodadas e perguntas, com rastreio do progresso do usuário.
- A interface e o backend são independentes, o que facilita manutenção e testes.
- O projeto ainda preserva rotas legadas de verificação, mas a arquitetura principal do MVP é centrada em jogo e performance adaptativa.

## Conclusão

A arquitetura do projeto reflete uma abordagem de software educacional e adaptativo. Ela combina experiência de usuário, backend robusto, persistência consistente e inteligência de aprendizagem para criar um sistema que não apenas apresenta informações, mas acompanha o desenvolvimento do usuário em competências relevantes para a identificação de desinformação.
