# Visão Geral do Projeto

## Contexto e objetivo

O projeto Fake News Fact Checker foi concebido como uma aplicação gamificada para auxiliar pessoas a reconhecerem desinformação de forma prática e educativa. A experiência combina elementos de jogo, diagnóstico de habilidades e feedback imediato para que o usuário aprenda a avaliar fontes, evidências, contexto e imagens antes de compartilhar ou acreditar em conteúdos suspeitos.

A proposta central é transformar a verificação de notícias em um processo interativo. Em vez de apenas consultar uma API externa ou visualizar um resultado isolado, o usuário participa de uma sequência de rodadas em que responde perguntas sobre notícias, recebe explicações e evolui conforme seu desempenho.

## Problema que o produto resolve

A disseminação de notícias falsas cresce em ritmo acelerado e frequentemente explora vulnerabilidades na leitura crítica, como:

- desconfiança em fontes desconhecidas;
- aceitação de alegações sem evidências;
- interpretação de texto fora do contexto;
- uso de imagens e gráficos que parecem verdadeiros, mas não sustentam a narrativa;
- dificuldade de avaliar informações rápidas sem processo de checagem.

O produto busca reduzir esse problema ao ensinar, de forma progressiva, os critérios que definem uma notícia confiável.

## Proposta de valor

O sistema oferece:

- uma experiência de aprendizagem baseada em jogos;
- ensino de quatro habilidades centrais de checagem;
- acompanhamento individual do progresso do usuário;
- adaptação de conteúdo conforme o nível de domínio em cada competência;
- feedback explicativo após cada resposta;
- possibilidade de verificar uma notícia específica por meio de um fluxo legado de consulta.

## Público-alvo

O produto é pensado para:

- estudantes;
- usuários de redes sociais interessados em verificar conteúdos;
- plataformas de educação e alfabetização midiática;
- pessoas que desejam desenvolver autonomia para analisar informações antes de compartilhá-las.

## Funcionalidades principais

### 1. Jogo de checagem de notícias

O usuário inicia uma partida e recebe uma notícia associada a uma pergunta. A partir dessa rodada, ele deve analisar a informação e responder uma questão de múltipla escolha.

A cada rodada, o sistema:

- apresenta uma notícia ou contexto relevante;
- exibe uma pergunta direcionada a uma habilidade específica;
- coleta a resposta do usuário;
- avalia se a resposta está correta;
- fornece uma explicação relacionada ao critério de análise.

### 2. Acompanhamento por habilidades

O jogo organiza a aprendizagem em quatro competências:

- SOURCE: análise da fonte e da origem;
- EVIDENCE: avaliação de evidências e comprovação;
- CONTEXT: percepção de contexto omitido ou distorcido;
- VISUAL: verificação da imagem e do suporte visual.

Essas habilidades são monitoradas ao longo do tempo para identificar o nível de domínio do usuário.

### 3. Modelagem de domínio via BKT

O sistema utiliza Bayesian Knowledge Tracing (BKT) para estimar a probabilidade de domínio do usuário em cada habilidade. Com base na resposta anterior, o modelo atualiza a mastery probability e indica em qual competência a pessoa precisa de mais atenção.

Isso permite que o produto não seja apenas um jogo de perguntas aleatórias, mas uma experiência adaptativa que prioriza temas e competências em que o usuário ainda tem menor domínio.

### 4. Seleção adaptativa de perguntas

A seleção da próxima pergunta considera a habilidade com menor nível de domínio, priorizando a revisão de competências mais frágeis. Esse mecanismo torna o jogo mais didático e personalizado.

### 5. Perfil de habilidades do usuário

Ao final de uma sessão ou em consultas específicas, o sistema pode expor o perfil de desempenho do usuário em cada habilidade, mostrando o progresso e a evolução de aprendizagem.

### 6. Verificação de notícia específica

Além do jogo, a aplicação mantém um fluxo mais tradicional de verificação, em que o usuário pode inserir uma notícia, assunto ou afirmação e receber resultados provenientes da Google Fact Check API.

Esse módulo funciona como suporte complementar ao processo de aprendizagem.

## Fluxo de uso do produto

### Fluxo principal: gameplay

1. O usuário acessa a aplicação e inicia uma partida.
2. O sistema cria um jogo e gera a primeira rodada.
3. Uma notícia e uma pergunta são apresentadas ao usuário.
4. O usuário responde a questão.
5. O backend valida a resposta e calcula o impacto no domínio da habilidade.
6. O BKT atualiza o nível de conhecimento da competência.
7. O sistema registra a resposta e continua para a próxima rodada.
8. O jogo evolui até atingir o limite de rodadas ou o fim da partida.

### Fluxo de acompanhamento

O usuário também pode consultar seu perfil de habilidades para entender em quais competências está mais forte ou mais fraco.

## Diferenciais do produto

- abordagem educacional e gamificada;
- suporte a aprendizagem de checagem de fatos com foco em fontes, evidências, contexto e imagens;
- adaptação do conteúdo com base em desempenho real;
- arquitetura modular e expansível para futuras melhorias;
- integração com APIs externas para suporte factual e contexto de verificação.

## Estado atual do projeto

O projeto já apresenta uma estrutura funcional em duas camadas principais:

- Frontend em Next.js para a experiência do usuário;
- Backend em FastAPI para a lógica de negócio, APIs, modelos e rastreamento de conhecimento.

A base da solução está organizada para permitir evolução contínua, mantendo a camada de apresentação separada da camada de raciocínio adaptativo e da persistência de dados.

## Resultado esperado

O produto tem como objetivo dar ao usuário uma forma mais concreta e dinâmica de desenvolver criticidade diante de conteúdos digitais, ajudando a distinguir informação confiável de conteúdo enganoso com base em critérios observáveis e aprendizados progressivos.
