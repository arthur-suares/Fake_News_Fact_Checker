## Metodologia MoSCoW

A priorização dos requisitos foi realizada com a metodologia **MoSCoW**, que classifica cada item em quatro níveis: **Must have** (essencial — sem ele o sistema não funciona), **Should have** (importante — agrega grande valor, mas o sistema opera sem ele), **Could have** (desejável — melhora a experiência se houver tempo) e **Won't have** (fora do escopo deste ciclo, registrado para trabalhos futuros). A tabela abaixo consolida essa priorização já alinhada aos requisitos elicitados nas seções seguintes.

| Must have | Should have | Could have | Won't have |
|:---------:|:-----------:|:----------:|:----------:|
| **Banco de Dados Estruturado (PostgreSQL):** Para armazenar os inputs e as classificações geradas pelo modelo, permitindo futuros retreinos.<br><br>**Integração com API de Checagem (Google):** O motor de validação da verdade factual que alimenta nosso modelo (RF-VER-01, RF-VER-02).<br><br>**Interface do Usuário (UI) e Questionário:** O formulário de entrada para coleta da notícia e das respostas comportamentais (RF-ING-01 a RF-ING-05).<br><br>**Modelo de Perfilamento de Usuários (IA):** Implementação de modelo de Machine Learning para identificar o nível de viés de confirmação do usuário, cruzando três variáveis principais:<br>• A expectativa do usuário (acha que é verdadeiro ou falso).<br>• O alinhamento da notícia (condiz ou não com suas crenças).<br>• A verdade factual (veredito da API do Google).<br><br>Aplicado por classificação (Random Forest) e/ou clustering de personas (RF-PER-03, RF-PER-04, RF-PER-08).<br><br>**Servidor MCP:** Orquestração das ferramentas de verificação com contratos tipados e tratamento de falhas (RF-MCP-01 a RF-MCP-05, RF-MCP-07, RF-MCP-09).<br><br>**Análise Multimodal de Imagens:** Verificação de origem, sinteticidade e consistência texto-imagem via LLM vision e busca reversa (RF-VER-03, RF-VER-04).<br><br>**Persistência de Evidências e Feedback:** Registro das respostas do questionário vinculadas à notícia avaliada (RF-PER-01). | **Execução Paralela das Tools:** Chamadas simultâneas às ferramentas de verificação para reduzir o tempo de resposta (RF-MCP-08).<br><br>**Registro Comportamental Implícito:** Tempo na página, veredito prévio e delta antes/depois da verificação (RF-PER-02).<br><br>**Qualidade e Atualização do Clustering:** Validação por silhouette score e reexecução periódica via job agendado (RF-PER-06, RF-PER-07).<br><br>**Rotulação de Personas:** Nomeação dos clusters com perfis explicáveis (RF-PER-05).<br><br>**Painel Pessoal do Usuário:** Exibição do perfil de susceptibilidade com dicas personalizadas de verificação (RF-PER-09).<br><br>**Auditoria de Evidências:** Registro das evidências brutas com timestamp para reprodução e análise (RF-VER-06).<br><br>**Dashboard de Explicabilidade (XAI):** Painel simples (SHAP ou LIME) para entender por que o modelo classifica o usuário em determinado perfil.<br><br>**NLP no Link/Texto:** Extração de palavras-chave e tom da notícia, enriquecendo as features do classificador de perfis.<br><br>**Feedback Educativo ao Usuário:** Mensagem personalizada a partir da classificação (ex.: "Notamos que você tende a acreditar em notícias falsas quando elas se alinham à sua visão política. Cuidado com o viés de confirmação!").<br><br>**Pulo do Questionário:** Permitir que o usuário ignore o questionário sem prejuízo do uso da aplicação (RF-ING-06). | **Similaridade Cross-modal (CLIP):** Cálculo de coerência semântica entre embeddings de texto e imagem como sinal adicional (RF-VER-05).<br><br>**Sistema de Login:** Rastreamento do mesmo usuário ao longo de múltiplas consultas, criando uma série temporal do seu viés.<br><br>**Tool de Perfil sob Demanda:** Consulta explícita ao perfil/persona do usuário via MCP (RF-MCP-06). | **Pipeline de MLOps (Retreinamento Contínuo):** Script que reavalie os pesos do modelo conforme a base de dados cresce e novos padrões de viés de confirmação emergem.<br><br>**Modelo Próprio de Fact-Checking:** Continuaremos dependendo da API do Google para a verdade factual, focando nosso esforço de IA 100% no comportamento humano, e não na checagem do texto em si. |

## Especificação de Requisitos

A partir da metodologia MoSCoW foi possível elencar a especificação dos seguintes requisitos:

### Requisitos de Ingestão de Dados

| ID        | Requisito                                                                                                                                  | Prioridade |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| RF-ING-01 | O sistema deve permitir que o usuário submeta uma notícia em formato de texto (título e/ou corpo da afirmação)                             | Alta       |
| RF-ING-02 | O sistema deve permitir que o usuário submeta uma imagem associada à notícia (upload de arquivo JPG/PNG/WebP)                              | Alta       |
| RF-ING-03 | O sistema deve permitir a submissão combinada de texto e imagem na mesma consulta                                                          | Alta       |
| RF-ING-04 | O sistema deve validar o formato e o tamanho máximo dos arquivos enviados (limite de 10 MB por imagem)                                     | Alta       |
| RF-ING-05 | O sistema deve apresentar ao usuário, após o veredito, um questionário de no máximo 6 perguntas sobre a percepção de veracidade da notícia | Alta       |
| RF-ING-06 | O sistema deve permitir que o usuário pule o questionário sem prejuízo do uso da aplicação                                                 | Média      |

### Requisitos do Módulo MCP

| ID        | Requisito                                                                                                                                             | Prioridade |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| RF-MCP-01 | O sistema deve implementar um servidor MCP que exponha as ferramentas de verificação como tools tipadas com contrato de entrada e saída definido      | Alta       |
| RF-MCP-02 | O sistema deve disponibilizar a tool `fact_check_claim` que recebe texto e retorna claims correspondentes, publisher, rating e URL da fonte           | Alta       |
| RF-MCP-03 | O sistema deve disponibilizar a tool `check_image_origin` que recebe uma imagem e retorna URLs de imagens similares e contexto de origem              | Alta       |
| RF-MCP-04 | O sistema deve disponibilizar a tool `analyze_image_synthetic` que retorna score de sinteticidade/manipulação da imagem                               | Alta       |
| RF-MCP-05 | O sistema deve disponibilizar a tool `analyze_text_image_consistency` que retorna descrição do conteúdo visual e inconsistências entre texto e imagem | Alta       |
| RF-MCP-06 | O sistema deve disponibilizar a tool `get_user_profile` que retorna a persona/cluster atual do usuário                                                | Média      |
| RF-MCP-07 | O sistema deve disponibilizar a tool `record_feedback` que persiste as respostas do questionário                                                      | Alta       |
| RF-MCP-08 | O sistema deve executar as tools de verificação (RF-MCP-02 a 05) em paralelo sempre que possível                                                      | Média      |
| RF-MCP-09 | O sistema deve tratar falhas em tools individuais sem derrubar o fluxo, retornando evidência "indisponível" para a ferramenta afetada                 | Alta       |

### Requisitos de Verificação das Fake News

| ID        | Requisito                                                                                                                                                                     | Prioridade |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| RF-VER-01 | O sistema deve consultar a Google Fact Check API para verificação textual por afirmação                                                                                       | Alta       |
| RF-VER-02 | O sistema deve registrar como "inconclusivo" quando a Fact Check API não retornar claims correspondentes                                                                      | Alta       |
| RF-VER-03 | O sistema deve realizar busca reversa de imagem para detectar reutilização de imagem em contextos diferentes                                                                  | Alta       |
| RF-VER-04 | O sistema deve analisar imagens submetidas por meio de LLM multimodal (vision), retornando descrição do conteúdo, plausibilidade de manipulação e inconsistências com o texto | Alta       |
| RF-VER-05 | O sistema deve, opcionalmente, calcular similaridade semântica entre embeddings de texto e imagem (CLIP) como sinal de coerência cross-modal                                  | Baixa      |
| RF-VER-06 | O sistema deve registrar todas as evidências brutas retornadas pelas ferramentas, com timestamp, para auditoria                                                               | Média      |

### Módulo de Perfilamento de Usuário

| ID        | Requisito                                                                                                                                                                                                            | Prioridade |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| RF-PER-01 | O sistema deve armazenar as respostas do questionário vinculadas ao usuário e à notícia avaliada                                                                                                                     | Alta       |
| RF-PER-02 | O sistema deve registrar dados comportamentais implícitos: tempo na página, veredito prévio (se coletado), e delta antes/depois da verificação                                                                       | Média      |
| RF-PER-03 | O sistema deve construir um vetor de características por usuário com as dimensões: confiança em fontes, susceptibilidade emocional, comportamento de verificação, dependência de redes sociais e abertura a correção | Alta       |
| RF-PER-04 | O sistema deve executar clustering (K-means ou Gaussian Mixture) sobre os vetores de usuário, com k entre 3 e 4                                                                                                      | Alta       |
| RF-PER-05 | O sistema deve rotular cada cluster como uma persona (ex.: "Crédulo emocional", "Cético verificador", "Passivo-scroll", "Confiante em autoridade")                                                                   | Média      |
| RF-PER-06 | O sistema deve validar a qualidade do clustering por silhouette score e registrar o resultado                                                                                                                        | Média      |
| RF-PER-07 | O sistema deve reexecutar o clustering periodicamente (job agendado) à medida que novas respostas chegam                                                                                                             | Média      |
| RF-PER-08 | O sistema deve reordenar a apresentação da justificativa do veredito conforme a persona do usuário (adaptação da explicação)                                                                                         | Alta       |
| RF-PER-09 | O sistema deve exibir ao usuário um painel pessoal com seu perfil de susceptibilidade e dicas personalizadas de verificação                                                                                          | Média      |

---

### O que são Requisitos Funcionais e Não Funcionais?

Os **requisitos funcionais** descrevem **o que o sistema deve fazer** — as funcionalidades, comportamentos e operações que ele precisa entregar ao usuário. Neste projeto, eles cobrem desde a submissão de notícias com texto e imagem (RF-ING), passando pela orquestração das ferramentas de verificação via servidor MCP (RF-MCP) e pela checagem multimodal com IA (RF-VER), até o perfilamento do usuário com questionário e clustering (RF-PER). Em outras palavras: são as "ações" do sistema.

Já os **requisitos não funcionais** definem **como o sistema deve ser** — qualidades e restrições de desempenho, usabilidade, confiabilidade e segurança. Eles não agregam funcionalidades novas, mas garantem que as existentes sejam entregues com qualidade: tempo de resposta de até 30 segundos, tolerância a falhas nas APIs externas, linguagem acessível na interface e proteção dos dados coletados no questionário.

### O que é a metodologia MoSCoW?

A metodologia **MoSCoW** é uma técnica de priorização de requisitos amplamente usada em metodologias ágeis, cujo nome é um acrônimo dos quatro níveis de classificação:

- **Must have** — requisitos **essenciais**, sem os quais o sistema não entrega valor. São o núcleo do MVP (Produto Mínimo Viável).
- **Should have** — requisitos **importantes**, que agregam valor significativo, mas cuja ausência não impede a operação do sistema.
- **Could have** — requisitos **desejáveis**, incluídos se houver tempo e recursos disponíveis.
- **Won't have** — requisitos **fora do escopo** deste ciclo, explicitamente registrados para evitar desvio de foco e orientar trabalhos futuros.

A força do MoSCoW está em tornar as decisões de escopo transparentes e negociáveis — especialmente valioso em projetos com prazo curto, como este de aproximadamente um mês, pois protege o time de "escopo creep" (crescimento descontrolado de requisitos).

### Conclusão

Com a elicitação e a priorização MoSCoW consolidadas, o projeto assume um escopo **viável e defensável**: o núcleo (Must have) concentra-se na verificação híbrida de fake news — combinando a Google Fact Check API com análise multimodal de imagens via LLM vision — e no perfilamento do usuário a partir do questionário com clustering, tudo orquestrado por um servidor MCP. Os requisitos Should e Could representam refinamentos de qualidade e experiência que podem ser incorporados conforme o tempo do sprint permitir, enquanto os Won't have delimitam honestamente o que ficará fora deste ciclo (MLOps contínuo e modelo próprio de fact-checking). Essa organização garante que, ao final do mês, exista um sistema completo e funcional, e não um conjunto de funcionalidades pela metade.

---

## Requisitos Não Funcionais

| ID         | Requisito                                                                                                                    | Prioridade |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------- |
| RNF-01     | O sistema deve retornar o veredito em no máximo 30 segundos para consultas com texto + imagem                               | Alta       |
| RNF-02     | As tools MCP devem responder individualmente em no máximo 10 segundos (com timeout configurável)                            | Alta       |
| RNF-03     | O sistema deve suportar o processamento de pelo menos 5 consultas simultâneas                                               | Média      |
| RNF-04     | O job de clustering deve executar em background sem impactar o tempo de resposta das verificações                           | Média      |
| RNF-05     | A interface deve exibir o veredito com linguagem acessível, evitando jargão técnico                                         | Alta       |
| RNF-06     | A justificativa deve ser apresentada por modalidade de evidência (texto, imagem, fonte externa) de forma visualmente distinta | Alta       |
| RNF-07     | O questionário deve levar no máximo 2 minutos para ser respondido                                                           | Média      |
| RNF-08     | A interface deve indicar progresso durante o processamento da verificação                                                   | Média      |
| RNF-09     | O sistema deve armazenar imagens enviadas apenas pelo tempo necessário à análise, com remoção ou anonimização posterior      | Alta       |
| RNF-10     | O sistema deve aplicar validação e sanitização de todas as entradas do usuário                                              | Alta       |
| RNF-11     | O questionário deve informar ao usuário a finalidade da coleta de dados e obter consentimento                                | Alta       |
| RNF-12     | O sistema deve tratar falhas em APIs externas com retry e backoff, mantendo funcionalidade degradada                        | Alta       |
| RNF-13     | Todas as evidências e vereditos devem ser persistidos para permitir auditoria e reprodução                                   | Média      |
| RNF-14     | A interface deve ser responsiva, funcionando em desktop e mobile                                                            | Média      |
| RNF-15     | O sistema deve comunicar-se com APIs externas exclusivamente via HTTPS                                                      | Alta       |

## Histórico de Versões

| **Data**   | **Versão** | **Descrição** | **Autor** | **Revisor** |
|:----------:|:----------:|:-------------:|:---------:|:-----------:|
| 18/09/2026 | 1.0        | Confecção inicial do documento | Laura Gomes | Arthur Suares |
| 18/09/2026 | 1.1        | Elaboração dos tópicos de elicitação de requisitos | Arthur Suares, Laura Gomes, Gabriel, Maria Eduarda |
| 21/09/2026 | 1.2        | Levantamento de requisitos | Arthur Suares, Laura Gomes, Gabriel, Maria Eduarda, Milena e Ian |
| 21/09/2026 | 1.3        | Ajuste da tabela MoSCoW com os requisitos elicitados, inclusão de seções explicativas e ampliação dos requisitos não funcionais | Arthur Suares, Laura Gomes, Gabriel, Maria Eduarda, Milena e Ian | |