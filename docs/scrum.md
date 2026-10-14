# Papéis do Time SCRUM

* **Scrum Master:** Arthur Suares
* **Developers / Equipe de Desenvolvimento:** Ian, Arthur, Gabriel, Laura, Maria Eduarda, Milena

---

## Distribuição de Tarefas e Entregas (Backlog Fechado)

### Arthur Suares *(Scrum Master & Backend/BKT Developer)*
> **Atuação:** Liderança da metodologia e coordenação das sprints, além do desenvolvimento da lógica adaptativa do backend e módulos rastreadores de conhecimento BKT.

* **Backend & Lógica Adaptativa:**
  * **RF-13:** Seleção adaptativa da próxima pergunta.
  * **RF-11:** API para inicialização da partida.
* **Módulos BKT (Bayesian Knowledge Tracing):**
  * **RF-09:** *EvidenceTracker* (rastreador de evidências).
  * **RF-08:** *ContextTracker* (rastreador de contexto).
  * **RF-07:** *VisualTracker* (rastreador visual).
  * **RF-06:** *SourceTracker* (rastreador de fontes).
* **Garantia de Qualidade & Conteúdo (Co-autoria/Review):**
  * **RF-19:** Preparação do dataset inicial de notícias e perguntas.
  * **RF-20:** Testes unitários do motor BKT.
  * **RF-21:** Teste de integração da rodada completa.

---

###  Ian Lucca *(Frontend & Test Automation Developer)*
> **Atuação:** Responsável pelo desenvolvimento da interface do usuário (UI/UX) do jogo, telas de feedback, dashboards e pela qualidade do produto via testes.

* **Frontend & Interface do Usuário:**
  * **RF-14:** Interface principal da rodada do jogo.
  * **RF-16:** Tela de feedback do usuário.
  * **RF-17:** Dashboard de perfil de habilidades do jogador.
* **Regras de Negócio & Backend:**
  * **RF-18:** Lógica de finalização da partida após 10 rodadas.
* **Testes & Conteúdo (Co-autoria):**
  * **RF-19:** Preparação do dataset inicial de notícias e perguntas.
  * **RF-20:** Testes unitários do BKT.
  * **RF-21:** Testes de integração do fluxo completo da rodada.

---

###  Gabriel da Cruz *(Database & Legacy Architecture Developer)*
> **Atuação:** Responsável pela estruturação inicial do banco de dados e suporte ao modelo arquitetural legado.

* **Modelagem de Dados e Banco de Dados Relacional:**
  * **RF-01:** Criação da estrutura e tabelas de *Game* e *GameRound*.
  * **RF-02:** Criação das entidades de *Skill* e *UserSkillState*.
* **Arquitetura Base:**
  * Implementação e suporte à estrutura do modelo antigo.

---

###  Laura Carolina *(BKT Engine & Core Backend Developer)*
> **Atuação:** Responsável pela implementação do motor matemático de IA/BKT, regras de atualização de habilidades e persistência de dados.

* **Motor Matemático & Regras de Negócio BKT:**
  * **RF-05:** Implementação do motor matemático BKT (*Bayesian Knowledge Tracing*).
  * **RF-10:** Criação do *BKTManager* (gerenciador central BKT).
  * **RF-12:** Processamento de respostas e atualização do estado BKT do usuário.
* **Persistência de Dados & Arquitetura:**
  * **RF-04:** Persistência no banco de dados das respostas fornecidas em cada rodada.
  * Suporte e implementação no modelo antigo.

---

###  Maria Eduarda *(Security & AI / Vector Search Developer)*
> **Atuação:** Responsável pela segurança/autenticação da aplicação e pela infraestrutura de IA para consulta histórica em parceria com Milena.

* **Segurança e Autenticação:**
  * Autenticação e autorização via JWT (*JSON Web Token*).
* **Inteligência Artificial e Busca Semântica (Co-autoria com Milena):**
  * Implementação de Banco de Dados Vetorial e Pipeline RAG (*Retrieval-Augmented Generation*) para consulta e checagem no histórico de notícias.
* **Arquitetura Base:**
  * Suporte ao modelo antigo do sistema.

---

###  Milena Marques *(Research & AI / Vector Search Developer)*
> **Atuação:** Responsável pela fundamentação teórica/pesquisa acadêmica do projeto e co-desenvolvimento da infraestrutura de dados vetoriais.

* **Pesquisa & Referencial Teórico:**
  * Levantamento e análise de artigos científicos e pesquisa sobre bancos de dados.
* **Inteligência Artificial e Busca Semântica (Co-autoria com Maria Eduarda):**
  * Implementação do Banco de Dados Vetorial e Pipeline RAG para consulta de histórico de notícias.

---

## Resumo Executivo da Sprint por Área Conceitual

| Domínio do Projeto | Responsáveis | Entregas Principais |
| :--- | :--- | :--- |
| **Frontend & UI/UX** | Ian | Interfaces da rodada, feedback e dashboard de habilidades |
| **Backend & Motor BKT** | Arthur, Laura | Motor BKT, rastreadores (Evidence, Context, Visual, Source), BKTManager e regras adaptativas |
| **Banco de Dados & Persistência** | Gabriel, Laura | Estruturas de Game, GameRound, Skills, UserSkillState e salvamento de respostas |
| **Segurança & Pipeline IA (RAG)** | Maria Eduarda, Milena | Autenticação JWT e Banco Vetorial/Pipeline RAG para consulta de notícias |
| **Pesquisa & Fundamentação** | Milena | Pesquisa de artigos e análise de bancos de dados |
| **Garantia de Qualidade (QA)** | Arthur, Ian | Testes unitários do BKT, testes de integração da rodada e dataset de notícias |
