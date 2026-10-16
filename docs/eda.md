    # Base de Dados e Análise Exploratória — Verifica

## 1. Introdução

A base de dados utilizada no projeto Verifica foi inicialmente incorporada com o objetivo de apoiar o desenvolvimento de um sistema de detecção automática de notícias falsas. A proposta original consistia em utilizar técnicas de aprendizado de máquina para treinar um classificador capaz de identificar padrões textuais associados a alegações classificadas como falsas ou verdadeiras.

Para compreender as características dessa base e avaliar sua adequação a essa finalidade, foi desenvolvido um processo de análise exploratória de dados (*Exploratory Data Analysis* — EDA), documentado no notebook `analise_exploratoria.ipynb`. Essa etapa investigou a estrutura dos registros, a distribuição das classes, a qualidade dos dados, as características dos textos e possíveis vieses que poderiam comprometer o treinamento e a avaliação de um classificador.

Entretanto, durante o desenvolvimento, o projeto passou por uma mudança de direcionamento. Em razão de dificuldades técnicas encontradas na implementação da abordagem original, a proposta evoluiu para uma aplicação gamificada que utiliza o *Bayesian Knowledge Tracing* (BKT) para acompanhar o domínio de habilidades relacionadas à análise crítica de notícias.

Essa mudança é importante para compreender o papel atual da base de dados: **o dataset foi preparado e analisado com vistas ao treinamento de um classificador de notícias falsas, mas não foi utilizado como dataset de treinamento do BKT.** O modelo BKT adotado na proposta atual tem outra finalidade e utiliza como evidência as respostas fornecidas pelos jogadores durante as partidas.

## 2. Caracterização da base de dados

A base é composta por dois arquivos CSV, que reúnem alegações verificadas por agências de checagem brasileiras e portuguesas, incluindo Lupa, Aos Fatos, Boatos.org, Polígrafo e AFP Checamos.

Os arquivos utilizados na análise são:

| Arquivo | Conteúdo | Valor de `label` |
|---|---|---:|
| `fakes.csv` | Alegações classificadas como falsas pelas fontes de checagem | 1 |
| `true.csv` | Alegações classificadas como verdadeiras pelas fontes de checagem | 0 |

Na versão examinada pelo notebook, os arquivos continham os seguintes quantitativos:

| Classe | Quantidade de registros |
|---|---:|
| Notícias falsas | 20.478 |
| Notícias verdadeiras | 2.720 |
| **Total** | **23.198** |

Esses números correspondem à versão efetivamente analisada no notebook e podem diferir de contagens divulgadas em versões posteriores da base.

A estrutura dos registros inclui informações textuais e metadados associados às checagens. Entre as principais colunas estão:

- `title`: título do artigo de checagem.
- `text`: alegação ou declaração submetida à verificação.
- `origin`: origem atribuída à alegação, com significado variável entre os arquivos.
- `url`: endereço do artigo de checagem.
- `publisher_name`: nome da agência ou publicação.
- `publisher_site`: domínio da publicação.
- `date`: data registrada para a alegação ou checagem.
- `label`: classificação da alegação como falsa ou verdadeira.

O conteúdo textual constitui o principal elemento de interesse para a proposta original de classificação automática. Os demais campos permitem contextualizar os registros e investigar características da coleta, mas não podem ser utilizados indiscriminadamente como variáveis preditoras, pois alguns podem introduzir vieses ou revelar indiretamente a classe.

## 3. Análise exploratória realizada

A análise exploratória foi desenvolvida para compreender a composição da base, identificar problemas de qualidade e levantar riscos que precisariam ser considerados caso fosse realizado o treinamento de um classificador.

O notebook organiza esse processo em etapas de inspeção inicial, análise de qualidade, limpeza, caracterização dos textos, investigação de padrões lexicais e identificação de temas recorrentes.

### 3.1 Distribuição das classes

Um dos primeiros resultados identificados foi o desbalanceamento entre as classes. A base contém aproximadamente 7,5 registros de notícias falsas para cada registro de notícia verdadeira.

Esse desequilíbrio representa um desafio para o treinamento de um classificador. Um modelo que classificasse todos os registros como falsos obteria aproximadamente 88% de acurácia nessa distribuição, mesmo sem aprender a distinguir as duas classes.

Por esse motivo, o notebook destaca que a acurácia isolada não seria suficiente para avaliar um modelo futuro. Métricas como precisão, revocação (*recall*), F1-score e resultados separados por classe seriam necessárias para avaliar melhor seu desempenho.

Na análise exploratória, as comparações entre as classes foram realizadas preferencialmente por proporções, reduzindo a influência da diferença no número de registros.

### 3.2 Qualidade e consistência dos dados

O notebook investigou problemas que poderiam prejudicar a interpretação dos resultados ou o processamento posterior da base.

Entre os problemas identificados estão:

- **Valores ausentes:** as colunas `title` e `text` estavam preenchidas nos registros analisados, mas havia valores ausentes em `origin` e `date`.
- **Duplicatas:** foram identificadas 18 linhas envolvidas em duplicações segundo a combinação de título, texto e URL. Após a remoção de duplicatas exatas por esses campos, foram eliminadas nove linhas.
- **Conteúdo repetido:** em 4.083 registros, aproximadamente 17,6% do total, o campo `text` era igual ao campo `title`. Isso exigia cuidado ao combinar os campos para evitar a contagem duplicada de palavras.
- **Inconsistências nos nomes das publicações:** uma mesma agência aparecia com grafias diferentes, o que poderia distorcer as estatísticas por fonte.
- **Variações no campo `origin`:** foram encontradas diferentes grafias para uma mesma origem, além de valores genéricos que não identificavam uma origem específica.
- **Datas inconsistentes:** foi identificada uma data de 2005 atribuída ao Observador, publicação fundada posteriormente. Também foram identificadas URLs que permitiam recuperar datas ausentes.

Esses problemas foram tratados conforme a possibilidade de correção segura. A limpeza buscou corrigir inconsistências identificáveis sem descartar automaticamente todos os registros que apresentavam informações incompletas.

### 3.3 Procedimentos de limpeza

A limpeza foi realizada sobre uma cópia dos dados carregados em memória, preservando os arquivos originais.

Os procedimentos implementados no notebook incluem:

1. Remoção de espaços indevidos, quebras de linha e caracteres problemáticos nos campos textuais.
2. Eliminação de duplicatas considerando a combinação de título, texto e URL.
3. Criação de uma variável indicadora para identificar quando `text` é igual a `title`.
4. Padronização dos nomes das agências com base no domínio de publicação.
5. Normalização de grafias equivalentes no campo `origin` e tratamento de valores genéricos.
6. Conversão e validação das datas, incluindo a recuperação de datas a partir de URLs quando possível.
7. Criação de campos auxiliares, como texto combinado e quantidade de palavras, para apoiar as análises posteriores.

Após a limpeza registrada no notebook, a tabela passou de 23.198 para 23.189 registros, com a remoção de nove duplicatas. O número de valores distintos em `origin` caiu de 1.503 para 1.462, e a quantidade de datas ausentes foi reduzida de 3.070 para 2.569.

O notebook também faz referência ao script `00_limpeza.py`, responsável por reproduzir esse processo e exportar os dados limpos para `datasets/limpos/`, além de gerar um arquivo `nao_tratados.csv` com casos que não puderam ser resolvidos automaticamente.

### 3.4 Características textuais

A análise dos textos procurou identificar diferenças entre as alegações falsas e verdadeiras que poderiam ser relevantes para um classificador.

Foram investigados o tamanho dos textos, o uso de letras maiúsculas, a frequência de pontos de exclamação, as palavras mais recorrentes, os pares de palavras (*bigramas*) e o vocabulário característico de cada classe.

Os resultados mostraram que as alegações falsas apresentavam maior variabilidade no tamanho: a mediana era de 14 palavras, assim como na classe verdadeira, mas os textos falsos incluíam desde alegações muito curtas até textos extensos.

A análise lexical também identificou temas frequentes relacionados a política, eleições, COVID-19, vacinas, tratamentos de saúde e figuras públicas. Entre as palavras e expressões associadas às alegações falsas estavam referências a urnas eletrônicas, fraude, hidroxicloroquina e diferentes narrativas políticas.

Esses resultados permitiram levantar possíveis características textuais para uma futura etapa de modelagem. Contudo, a presença de determinados termos não comprova, isoladamente, a falsidade de uma alegação. Um classificador que dependesse excessivamente de palavras ou temas específicos poderia perder desempenho quando os assuntos da desinformação mudassem.

### 3.5 Vieses e limitações identificados

Um dos achados mais importantes foi o potencial viés associado às fontes de publicação.

A análise identificou que aproximadamente 97% dos registros classificados como verdadeiros vinham de duas agências: Polígrafo e Lupa. Outras publicações apareciam predominantemente ou exclusivamente na classe falsa.

Esse padrão poderia levar um classificador a aprender diferenças de estilo, idioma ou procedência editorial, em vez de aprender características realmente relacionadas à veracidade das alegações.

Outro problema relevante foi o campo `origin`. Nas notícias falsas, ele frequentemente indicava onde o boato circulou, como Facebook ou WhatsApp. Nas notícias verdadeiras, frequentemente identificava quem havia feito uma declaração, como um político. Utilizar esse campo diretamente como variável de treinamento poderia revelar indiretamente a classe.

A análise também constatou que os dados terminavam em 2022, o que limita sua representatividade em relação a narrativas e acontecimentos posteriores. Além disso, aproximadamente 42% dos registros não foram associados a nenhum dos temas definidos por palavras-chave no notebook, demonstrando que a categorização temática era apenas parcial.

Essas limitações seriam importantes para o desenvolvimento de um classificador e precisariam ser consideradas em sua preparação, treinamento e avaliação.

## 4. Finalidade original: treinamento de um classificador

Na concepção inicial do projeto, a base seria utilizada para desenvolver um classificador supervisionado de notícias falsas.

Nesse cenário, cada registro forneceria um exemplo de treinamento composto por um texto e um rótulo conhecido. O modelo procuraria aprender padrões que ajudassem a distinguir alegações classificadas como falsas daquelas classificadas como verdadeiras.

O fluxo previsto seria, de forma geral:

1. Preparar e limpar os dados.
2. Definir quais campos poderiam ser utilizados como entradas do modelo.
3. Transformar os textos em representações adequadas ao algoritmo escolhido.
4. Separar os dados em conjuntos de treinamento, validação e teste.
5. Treinar o classificador e ajustar seus hiperparâmetros.
6. Avaliar o desempenho com métricas adequadas ao desbalanceamento das classes e investigar possíveis vieses.

A análise exploratória desenvolvida representa uma etapa preparatória desse fluxo. Ela ajudou a compreender os dados, identificar riscos e levantar decisões que precisariam ser tomadas antes do treinamento.

**Entretanto, a realização da análise exploratória não significa que um classificador tenha sido treinado ou validado.** O notebook documenta a inspeção, a limpeza e a caracterização da base, mas não constitui evidência de que o fluxo completo de treinamento de um classificador tenha sido concluído.

## 5. Mudança de direção do projeto

Durante o desenvolvimento, foram encontradas dificuldades técnicas na implementação da abordagem original de análise automatizada de notícias. Em consequência, o escopo do projeto foi reformulado para priorizar um MVP gamificado, com acompanhamento de habilidades por meio do Bayesian Knowledge Tracing.

Na proposta atual, o objetivo central deixou de ser exclusivamente classificar cada notícia como falsa ou verdadeira. O foco passou a ser a criação de uma experiência de perguntas e respostas que permita acompanhar o desempenho do jogador em diferentes dimensões da análise crítica de informações.

O sistema considera quatro habilidades principais:

- `SOURCE`: avaliação da fonte.
- `EVIDENCE`: avaliação das evidências.
- `CONTEXT`: análise do contexto.
- `VISUAL`: análise da relação entre imagens e alegações.

O BKT utiliza as respostas dadas pelo jogador para atualizar a probabilidade estimada de domínio de cada habilidade. Essas estimativas podem, então, orientar a seleção das próximas perguntas.

Essa mudança representa uma alteração na finalidade dos dados necessários ao modelo. Enquanto um classificador supervisionado utiliza exemplos de textos rotulados para aprender a distinguir classes, o BKT acompanha sequências de respostas de usuários associadas a habilidades específicas.

Por isso, a base de notícias analisada anteriormente não foi utilizada como dataset de treinamento do BKT. Os rótulos `label` indicam a classificação atribuída às alegações, mas não informam se um jogador domina uma habilidade nem descrevem como seu domínio evolui ao longo das partidas.

## 6. Por que a base não foi utilizada para treinar o BKT?

A distinção decorre da finalidade e da estrutura dos dados exigidos por cada abordagem.

| Aspecto | Classificador de notícias (proposta original) | BKT (proposta atual) |
|---|---|---|
| Objetivo | Classificar alegações como falsas ou verdadeiras | Estimar o domínio de habilidades do jogador |
| Unidade principal de análise | Registro de notícia ou alegação rotulada | Resposta do jogador a uma questão associada a uma habilidade |
| Dados necessários | Textos e rótulos de classe | Sequências de respostas corretas e incorretas, associadas às habilidades |
| Significado do rótulo | Veracidade atribuída à alegação | Resultado da resposta do jogador em relação à questão |
| Resultado produzido | Predição de classe para uma alegação | Probabilidade estimada de domínio por habilidade |
| Uso previsto | Detecção automática de notícias falsas | Acompanhamento de habilidades e seleção adaptativa de questões |

A base original não contém, por si só, as sequências de respostas necessárias para estimar o desenvolvimento das habilidades de um jogador. Ainda que seus registros sejam utilizados como material para elaborar questões, isso não transforma automaticamente o dataset em dados de treinamento do BKT.

Para que uma notícia seja utilizada no jogo, é necessário criar ou selecionar uma questão apropriada, definir sua habilidade principal, estabelecer uma resposta correta com base em evidências verificáveis e preparar uma explicação coerente. Depois, são as respostas dadas pelos jogadores a essas questões, ao longo do tempo, que podem alimentar o acompanhamento pelo BKT.

Da mesma forma, a classificação de uma notícia como falsa não determina automaticamente a habilidade avaliada. Uma questão pode abordar a fonte de uma alegação falsa, a ausência de evidências, a distorção de contexto ou a incompatibilidade de uma imagem. A habilidade depende do objetivo específico da questão, e não apenas do rótulo da notícia.

Portanto, **o dataset de notícias e o histórico de respostas dos jogadores cumprem funções diferentes na arquitetura atual**. O primeiro pode servir como fonte de material para a elaboração de questões, desde que haja curadoria e verificação. O segundo constitui a fonte de evidências para atualizar as estimativas de domínio do BKT.

## 7. Papel atual da base de dados

Após a mudança de escopo, a base permanece relevante como parte do trabalho de investigação e preparação de dados realizado no projeto. A análise exploratória permite documentar a origem dos registros, compreender sua distribuição, identificar problemas de qualidade e registrar limitações que seriam importantes para qualquer uso posterior.

No contexto atual, a base pode eventualmente apoiar a seleção de alegações para a elaboração de perguntas, mas esse uso exige cuidados adicionais. Os registros não devem ser convertidos automaticamente em questões sem verificar o conteúdo, o gabarito, a fonte, a habilidade avaliada e a explicação apresentada ao jogador.

A base também não deve ser descrita como o conjunto de treinamento do BKT. O treinamento de um classificador supervisionado e a atualização de um modelo de Knowledge Tracing são processos diferentes, com objetivos e requisitos de dados distintos.

A análise exploratória, por sua vez, continua sendo um artefato válido do projeto, pois documenta uma etapa real do desenvolvimento e fornece evidências sobre o material que estava disponível quando a proposta original ainda previa um classificador.

## 8. Limitações e trabalhos futuros

A mudança de direção permitiu concentrar os esforços no desenvolvimento da experiência gamificada e na implementação do acompanhamento de habilidades. Contudo, ela também implica que a finalidade original de classificação automática não foi concluída como parte da abordagem atual.

Como próximos passos relacionados aos dados, podem ser consideradas as seguintes atividades:

1. **Curadoria de questões:** transformar alegações selecionadas em questões verificáveis, associadas a uma única habilidade principal.
2. **Verificação das respostas corretas:** assegurar que os gabaritos e as explicações estejam fundamentados em fontes adequadas.
3. **Organização do banco de questões:** armazenar enunciados, alternativas, respostas corretas, explicações, dificuldade e habilidade avaliada.
4. **Coleta de interações reais:** registrar as respostas dos jogadores, a questão respondida, a habilidade associada e a sequência temporal das partidas.
5. **Avaliação futura do BKT:** utilizar os históricos de respostas para investigar a adequação dos parâmetros e a qualidade das estimativas de domínio.
6. **Retomada eventual da classificação automática:** caso volte a ser pertinente ao escopo, desenvolver e avaliar um classificador separadamente, utilizando a base de notícias e procedimentos apropriados de treinamento e validação.

Essas atividades não devem ser interpretadas como funcionalidades já concluídas. Elas representam possibilidades de continuidade que dependem das prioridades e da evolução do projeto.

## 9. Considerações finais

A base utilizada no Verifica reúne 23.198 registros na versão examinada pelo notebook, divididos entre alegações classificadas como falsas e verdadeiras. A análise exploratória documentou a estrutura dos arquivos, investigou a qualidade dos dados, aplicou procedimentos de limpeza e identificou características textuais, padrões temáticos e possíveis vieses relevantes para a modelagem.

Inicialmente, o dataset foi considerado para o treinamento de um classificador supervisionado de notícias falsas. Entretanto, dificuldades técnicas na implementação dessa abordagem contribuíram para a mudança de direção do projeto, que passou a priorizar uma aplicação gamificada baseada em Bayesian Knowledge Tracing.

Na proposta atual, o BKT tem a finalidade de estimar o domínio de habilidades do jogador a partir de suas respostas, e não de aprender a classificar notícias a partir dos rótulos existentes na base. Por esse motivo, os dados de notícias não foram utilizados como dataset de treinamento do BKT.

A distinção é essencial para descrever corretamente o trabalho realizado: **a base de dados foi objeto de análise exploratória com vistas à abordagem original de classificação, enquanto a proposta atual de BKT depende de questões associadas a habilidades e de sequências de respostas dos jogadores.** Embora a base possa contribuir para a elaboração futura de questões, seu uso nessa função exige curadoria e não equivale ao treinamento ou à calibração do BKT.

## Referências e artefatos do projeto

- `analise_exploratoria.ipynb` — notebook de análise exploratória, inspeção da qualidade, limpeza e investigação dos padrões da base.
- `00_limpeza.py` — script citado no notebook para reproduzir a limpeza e exportar os dados tratados.
- `datasets/fakes.csv` — registros de alegações classificadas como falsas na versão analisada.
- `datasets/true.csv` — registros de alegações classificadas como verdadeiras na versão analisada.
- `datasets/limpos/` — diretório de saída citado pelo processo de limpeza para os dados tratados.

Os caminhos e quantitativos apresentados correspondem à organização e à versão descritas no notebook analisado e devem ser conferidos caso a estrutura do repositório ou os arquivos tenham sido atualizados.