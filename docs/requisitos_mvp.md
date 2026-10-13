# Documento de Requisitos --- MVP Fake News Fact Checker com BKT

------------------------------------------------------------------------

## 1. Objetivo do sistema

O sistema oferece uma experiência gamificada de avaliação crítica de
notícias e informações. Ao longo de partidas com múltiplas rodadas, o
usuário responde a questões que avaliam habilidades específicas de
análise da informação. O sistema registra as respostas e utiliza
**Bayesian Knowledge Tracing (BKT)** para estimar a evolução do domínio
de cada habilidade ao longo do tempo.

O MVP deve entregar um fluxo persistente de ponta a ponta: notícias
armazenadas no banco são associadas a questões válidas; o usuário
responde; o backend determina a correção; o BKT atualiza a estimativa da
habilidade avaliada; e o sistema utiliza o estado atualizado para
selecionar questões futuras e apresentar um perfil de habilidades.

A integração existente com a Google Fact Check API e as funcionalidades
de verificação podem continuar disponíveis como recursos complementares.
Elas não substituem o BKT: a verificação externa fornece informações
sobre alegações e verificações publicadas, enquanto o BKT estima o
domínio de habilidades do usuário com base em suas respostas.

## 2. Escopo do MVP

### 2.1. Incluído

-   Persistência de notícias provenientes dos datasets do projeto.
-   Importação repetível e validada de notícias para o banco de dados.
-   Cadastro e persistência de questões associadas às notícias.
-   Classificação de cada questão em uma única habilidade.
-   Definição de gabarito, explicação e dificuldade para cada questão.
-   Partidas com até dez rodadas.
-   Registro de respostas, confiança declarada e tempo de resposta,
    quando disponíveis.
-   Atualização e persistência do estado BKT por habilidade.
-   Seleção determinística de questões, priorizando a habilidade com
    menor domínio estimado.
-   Evitar repetição de questões respondidas enquanto existirem
    alternativas elegíveis.
-   Feedback após a resposta e perfil com as quatro habilidades.
-   Autenticação e autorização para proteger jogos, respostas e estados
    de habilidade.
-   Testes unitários e de integração do fluxo principal.
-   Preservação das funcionalidades existentes de verificação factual,
    quando compatíveis com a arquitetura atual.

### 2.2. Fora do escopo obrigatório

-   Treinar um classificador próprio para decidir se uma notícia é
    verdadeira ou falsa.
-   Estimar automaticamente parâmetros BKT a partir de dados coletados.
    Os parâmetros iniciais podem ser configurados e documentados.
-   Tratar as 24.800 notícias como questões prontas.
-   Gerar automaticamente questões para todas as notícias sem validação.
-   Reinforcement Learning, Deep Knowledge Tracing (DKT), K-Means ou
    outros algoritmos adaptativos complexos.
-   Diagnosticar personalidade, ideologia ou suscetibilidade psicológica
    do usuário.
-   Pipeline contínuo de MLOps ou retreinamento automático.
-   Dependência obrigatória de LLM para iniciar ou executar uma partida.
-   Análise multimodal avançada, busca reversa de imagem ou CLIP como
    requisito para o fluxo principal do jogo. Funcionalidades existentes
    podem ser preservadas, mas não devem bloquear o jogo.

## 3. Conceitos e entidades principais

### 3.1. Notícia (`News`)

Armazena o conteúdo original utilizado para compor questões. Deve
preservar, quando disponíveis, título, texto, URL, origem/publicador,
classificação original, data e referência à imagem.

A classificação de origem da notícia é distinta da resposta do usuário e
de qualquer resultado retornado por uma API de fact-checking.

### 3.2. Questão (`Question`)

Representa uma atividade que utiliza uma notícia para avaliar uma
habilidade. Uma notícia pode estar associada a várias questões, e cada
questão deve avaliar **uma única habilidade**.

Cada questão válida deve possuir notícia associada, habilidade
associada, enunciado, alternativas, gabarito, explicação e dificuldade
numérica entre 0 e 1. O gabarito e a explicação não devem ser enviados
ao frontend antes do envio da resposta.

### 3.3. Habilidades (`Skill`)

-   `SOURCE`: avaliar origem, rastreabilidade e confiabilidade da fonte.
-   `EVIDENCE`: avaliar se as evidências sustentam a alegação.
-   `CONTEXT`: identificar omissões, distorções ou uso de informação
    fora de contexto.
-   `VISUAL`: avaliar se uma imagem disponível corresponde à alegação e
    constitui evidência relevante.

Uma questão só deve avaliar uma habilidade. Não se deve atualizar várias
habilidades a partir de uma única resposta no MVP.

### 3.4. Estado de habilidade (`UserSkillState`)

Armazena, por usuário e habilidade, a probabilidade atual estimada de
domínio (`mastery_probability`) e a data da última atualização. Deve
existir no máximo um estado atual por combinação de usuário e
habilidade. Os valores devem permanecer entre 0 e 1 e ser persistidos
entre partidas e reinicializações.

### 3.5. Partida e rodada (`Game`, `GameRound`)

`Game` representa uma partida do usuário. `GameRound` representa uma
rodada daquela partida e referencia a notícia apresentada. A questão
efetivamente respondida deve ser identificada de maneira inequívoca pelo
registro de resposta.

### 3.6. Resposta (`Answer`)

Armazena, no mínimo, usuário, rodada, questão, alternativa selecionada,
correção calculada pelo backend e data/hora. Confiança declarada e tempo
de resposta podem ser armazenados quando disponíveis. O backend
determina a correção.

## 4. Requisitos funcionais

Prioridades: **Must have** = obrigatório; **Should have** = importante;
**Could have** = desejável; **Won't have** = fora do escopo desta
versão.

### 4.1. Ingestão e persistência do dataset

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-DAT-01               Importar notícias dos   Must have
                          CSVs selecionados para  
                          `News`, preservando os  
                          campos relevantes       
                          disponíveis.            

  RF-DAT-02               Validar e normalizar    Must have
                          campos, tratar valores  
                          ausentes e registrar    
                          registros ignorados ou  
                          rejeitados.             

  RF-DAT-03               Tornar a importação     Must have
                          idempotente, sem        
                          duplicar registros em   
                          execuções repetidas.    

  RF-DAT-04               Mapear explicitamente   Must have
                          as classes do dataset e 
                          documentar seu          
                          significado.            

  RF-DAT-05               Oferecer modo de        Should have
                          simulação/validação sem 
                          gravação no banco.      

  RF-DAT-06               Importar em lotes, sem  Should have
                          exigir que todo o       
                          dataset esteja na       
                          memória.                
  -----------------------------------------------------------------------

A base contém aproximadamente 22 mil notícias falsas e 2.800
verdadeiras, mas o importador deve conferir as contagens reais dos
arquivos.

### 4.2. Gestão de questões

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-QUE-01               Persistir questões      Must have
                          associadas a notícias   
                          existentes.             

  RF-QUE-02               Associar cada questão a Must have
                          exatamente uma das      
                          quatro habilidades.     

  RF-QUE-03               Exigir enunciado,       Must have
                          opções válidas,         
                          gabarito e explicação.  

  RF-QUE-04               Exigir dificuldade      Must have
                          numérica entre 0 e 1.   

  RF-QUE-05               Validar a existência da Must have
                          notícia e da habilidade 
                          associadas.             

  RF-QUE-06               Disponibilizar questões Must have
                          revisadas associadas a  
                          notícias reais,         
                          suficientes para testar 
                          uma partida completa.   

  RF-QUE-07               Permitir várias         Must have
                          questões por notícia,   
                          inclusive de            
                          habilidades diferentes. 

  RF-QUE-08               Impedir que questões    Must have
                          inválidas sejam         
                          disponibilizadas no     
                          jogo.                   

  RF-QUE-09               Permitir geração de     Could have
                          rascunhos de questões   
                          sujeitos a validação    
                          antes da publicação.    
  -----------------------------------------------------------------------

O dataset de notícias não deve ser tratado como banco de questões. Não
se deve inventar evidências, fontes, contexto, imagens ou gabaritos.
Questões `VISUAL` exigem material visual disponível e suficiente para
avaliar a relação entre imagem e alegação.

### 4.3. Partidas e rodadas

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-JOG-01               Permitir que um usuário Must have
                          autenticado inicie uma  
                          partida.                

  RF-JOG-02               Garantir a existência   Must have
                          dos quatro estados      
                          iniciais de habilidade  
                          do usuário.             

  RF-JOG-03               Criar rodadas           Must have
                          persistidas associadas  
                          à partida e à notícia   
                          selecionada.            

  RF-JOG-04               Apresentar notícia,     Must have
                          questão e opções sem    
                          revelar o gabarito.     

  RF-JOG-05               Aceitar uma resposta    Must have
                          válida por              
                          questão/rodada e        
                          rejeitar duplicatas.    

  RF-JOG-06               Limitar uma partida a   Must have
                          dez rodadas             
                          respondidas.            

  RF-JOG-07               Encerrar a partida após Must have
                          dez rodadas ou quando   
                          não houver questões     
                          elegíveis, informando o 
                          motivo.                 

  RF-JOG-08               Impedir novas respostas Must have
                          em partidas             
                          finalizadas.            

  RF-JOG-09               Preservar o histórico   Must have
                          após o encerramento.    
  -----------------------------------------------------------------------

### 4.4. Respostas e feedback

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-RES-01               Receber a alternativa e Must have
                          identificar usuário,    
                          rodada e questão        
                          correspondentes.        

  RF-RES-02               Calcular a correção no  Must have
                          backend usando o        
                          gabarito persistido.    

  RF-RES-03               Registrar resposta,     Must have
                          correção e data/hora.   

  RF-RES-04               Registrar a confiança   Should have
                          declarada em escala     
                          validada, se            
                          habilitada.             

  RF-RES-05               Registrar o tempo de    Should have
                          resposta em             
                          milissegundos, quando   
                          disponível, validando o 
                          valor.                  

  RF-RES-06               Apresentar correção,    Must have
                          alternativa correta,    
                          explicação e habilidade 
                          avaliada após a         
                          resposta.               

  RF-RES-07               Impedir que uma mesma   Must have
                          resposta seja           
                          processada ou atualize  
                          o BKT mais de uma vez.  
  -----------------------------------------------------------------------

### 4.5. Aferição de habilidades com BKT

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-BKT-01               Manter estado de        Must have
                          domínio independente    
                          para cada uma das       
                          quatro habilidades de   
                          cada usuário.           

  RF-BKT-02               Atualizar a             Must have
                          probabilidade de        
                          domínio após uma        
                          resposta válida.        

  RF-BKT-03               Utilizar parâmetros     Must have
                          configurados para       
                          domínio inicial,        
                          transição, adivinhação  
                          e deslize.              

  RF-BKT-04               Persistir a estimativa  Must have
                          atualizada e a data da  
                          atualização.            

  RF-BKT-05               Atualizar somente a     Must have
                          habilidade associada à  
                          questão respondida.     

  RF-BKT-06               Recuperar o estado      Must have
                          persistido ao iniciar   
                          novas partidas.         

  RF-BKT-07               Permitir consultar as   Must have
                          quatro estimativas do   
                          usuário autenticado.    

  RF-BKT-08               Centralizar a           Should have
                          matemática no motor BKT 
                          compartilhado, sem      
                          duplicar fórmulas nos   
                          trackers.               

  RF-BKT-09               Configurar e documentar Should have
                          os parâmetros iniciais  
                          do BKT.                 

  RF-BKT-10               Estimar parâmetros a    Won't have
                          partir de sequências    
                          reais de respostas em   
                          uma etapa futura.       
  -----------------------------------------------------------------------

Os parâmetros iniciais podem ser definidos manualmente no MVP. Não é
necessário treinar o BKT com o dataset de notícias. As estimativas são
probabilidades do modelo, não medidas clínicas nem provas definitivas de
competência.

### 4.6. Seleção adaptativa de questões

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-SEL-01               Priorizar a habilidade  Must have
                          com menor probabilidade 
                          de domínio atual.       

  RF-SEL-02               Evitar questões já      Must have
                          respondidas pelo        
                          usuário em partidas     
                          anteriores, enquanto    
                          houver alternativas     
                          elegíveis.              

  RF-SEL-03               Priorizar questão cuja  Must have
                          dificuldade seja        
                          compatível com a        
                          mastery atual.          

  RF-SEL-04               Usar critérios          Must have
                          determinísticos para    
                          desempate.              

  RF-SEL-05               Se não houver questão   Must have
                          da habilidade           
                          prioritária, tentar     
                          outras habilidades e    
                          depois qualquer questão 
                          não respondida.         

  RF-SEL-06               Retornar estado         Must have
                          explícito quando não    
                          houver questões         
                          elegíveis.              

  RF-SEL-07               Evitar repetir a        Should have
                          notícia na mesma        
                          partida quando houver   
                          alternativa, sem        
                          descartar outras        
                          questões válidas da     
                          mesma notícia.          
  -----------------------------------------------------------------------

O seletor não deve utilizar Reinforcement Learning, DKT, K-Means ou
algoritmos complexos. A dificuldade é um atributo da questão e não deve
ser confundida com a mastery do usuário.

### 4.7. Interface e perfil

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-UI-01                Iniciar uma partida e   Must have
                          apresentar a questão    
                          retornada pelo backend. 

  RF-UI-02                Permitir selecionar uma Must have
                          opção e enviar a        
                          resposta à API.         

  RF-UI-03                Apresentar feedback     Must have
                          após confirmação do     
                          backend.                

  RF-UI-04                Exibir progresso e      Must have
                          estado de conclusão da  
                          partida.                

  RF-UI-05                Exibir as estimativas   Must have
                          de `SOURCE`,            
                          `EVIDENCE`, `CONTEXT` e 
                          `VISUAL`.               

  RF-UI-06                Carregar o perfil da    Must have
                          API, sem calcular uma   
                          estimativa alternativa  
                          no frontend.            

  RF-UI-07                Informar erros de       Must have
                          comunicação e ausência  
                          de questões             
                          disponíveis.            

  RF-UI-08                Exibir evolução entre   Could have
                          partidas quando houver  
                          histórico suficiente.   
  -----------------------------------------------------------------------

### 4.8. Autenticação e integração

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RF-INT-01               Associar partidas,      Must have
                          respostas e estados ao  
                          usuário autenticado.    

  RF-INT-02               Impedir acesso ou       Must have
                          alteração não           
                          autorizados aos dados   
                          de outro usuário.       

  RF-INT-03               Reutilizar serviços,    Must have
                          schemas e repositórios  
                          existentes, evitando    
                          duplicação              
                          desnecessária.          

  RF-INT-04               Preservar               Should have
                          funcionalidades         
                          existentes de           
                          verificação factual     
                          quando compatíveis, sem 
                          exigir fact-check       
                          externo a cada rodada.  

  RF-INT-05               Manter distintas a      Must have
                          classificação original  
                          do dataset, as          
                          respostas, as           
                          estimativas BKT e os    
                          vereditos externos.     
  -----------------------------------------------------------------------

## 5. Requisitos não funcionais

  -----------------------------------------------------------------------
  ID                      Requisito               Prioridade
  ----------------------- ----------------------- -----------------------
  RNF-01                  Validar e sanitizar os  Must have
                          dados recebidos pelas   
                          APIs.                   

  RNF-02                  Isolar os dados por     Must have
                          usuário e proteger      
                          rotas autenticadas.     

  RNF-03                  Manter consistentes o   Must have
                          registro da resposta e  
                          a atualização da        
                          mastery, evitando       
                          duplicação.             

  RNF-04                  Persistir notícias,     Must have
                          questões, partidas,     
                          rodadas, respostas e    
                          estados de habilidade.  

  RNF-05                  Tornar idempotente a    Must have
                          inicialização das       
                          skills e dos dados de   
                          demonstração.           

  RNF-06                  Tornar a importação     Must have
                          repetível, sem          
                          duplicação, com resumo  
                          dos resultados.         

  RNF-07                  Garantir seleção        Must have
                          determinística para o   
                          mesmo estado do banco.  

  RNF-08                  Oferecer interface      Should have
                          utilizável em desktop e 
                          dispositivos móveis.    

  RNF-09                  Apresentar enunciados e Must have
                          feedback em linguagem   
                          acessível.              

  RNF-10                  Tratar falhas de APIs   Must have
                          externas sem impedir    
                          partidas que não        
                          dependam delas.         

  RNF-11                  Usar banco isolado nos  Must have
                          testes e não modificar  
                          os datasets originais.  

  RNF-12                  Registrar erros         Must have
                          relevantes sem expor    
                          credenciais ou dados    
                          sensíveis nos logs.     

  RNF-13                  Utilizar HTTPS nas      Must have
                          comunicações com APIs   
                          externas.               

  RNF-14                  Documentar              Must have
                          configuração,           
                          inicialização,          
                          importação e execução   
                          dos testes.             

  RNF-15                  Evitar chamadas         Should have
                          externas desnecessárias 
                          no caminho crítico da   
                          resposta e da seleção   
                          de questões.            
  -----------------------------------------------------------------------

## 6. Priorização MoSCoW

  -----------------------------------------------------------------------
  Must have         Should have       Could have        Won't have
  ----------------- ----------------- ----------------- -----------------
  Importação        Simulação de      Rascunhos de      Treinamento de
  idempotente;      importação;       questões com LLM  parâmetros BKT
  persistência de   confiança e tempo sujeitos a        neste ciclo; DKT;
  notícias e        de resposta;      revisão;          Reinforcement
  questões; quatro  evitar repetição  visualização      Learning; K-Means
  skills; partidas  de notícia na     longitudinal;     e personas
  e rodadas;        mesma partida;    ferramentas       psicológicas;
  respostas; BKT    parâmetros BKT    administrativas   classificador
  persistido;       configuráveis;    de curadoria.     próprio de
  seleção           integração                          veracidade;
  adaptativa        complementar com                    geração
  simples; perfil;  Google Fact                         automática sem
  autenticação e    Check; evolução                     validação; MLOps
  autorização;      entre partidas.                     contínuo.
  testes unitários                                      
  e de integração.                                      

  -----------------------------------------------------------------------

## 7. Critérios de aceite ponta a ponta

O MVP será considerado funcional quando:

1.  O banco é inicializado e as quatro skills existem sem duplicação.
2.  Um subconjunto do dataset é importado e a reexecução não duplica
    registros.
3.  Existem questões válidas persistidas e associadas a notícias
    importadas.
4.  Um usuário autenticado inicia uma partida e recebe uma questão
    elegível.
5.  A API apresenta enunciado e alternativas sem revelar o gabarito.
6.  O usuário envia uma resposta e o backend determina a correção.
7.  A resposta é persistida e a habilidade correspondente é atualizada
    pelo BKT exatamente uma vez.
8.  O perfil retorna as quatro estimativas persistidas.
9.  A próxima seleção utiliza o estado atualizado e evita repetir
    questões respondidas quando há alternativas.
10. O sistema apresenta feedback e encerra a partida após dez rodadas
    respondidas ou antes, se não houver questões elegíveis.
11. Histórico e perfil permanecem disponíveis após reinicialização do
    backend.
12. Os testes do backend passam e o frontend compila com tipos alinhados
    à API.

## 8. Dados e limitações metodológicas

A base atual contém aproximadamente 22 mil notícias falsas e 2.800
verdadeiras. Esses registros são fontes de conteúdo, não um banco de
questões pronto.

A importação deve preservar a origem e a classificação original. As
questões precisam ser elaboradas ou curadas com base nas informações
disponíveis. Não se deve inferir que uma notícia possui imagem, fonte
verificável ou evidência suficiente apenas porque existe no dataset.

O MVP deve começar com um conjunto controlado de questões revisadas,
suficiente para exercitar as quatro habilidades e concluir partidas de
teste. A cobertura integral do dataset pode ocorrer incrementalmente.

Quando houver material válido, o conjunto deve incluir notícias
classificadas como verdadeiras e falsas. O sistema não deve permitir que
responder sempre "falso" seja uma estratégia suficiente para obter bom
desempenho.

A qualidade do BKT depende da validade dos enunciados, gabaritos e
associações entre questões e habilidades. A calibração dos parâmetros
com interações reais é uma possível evolução de pesquisa, não um
requisito para concluir o MVP.

## 9. Histórico de versões

| **Data**   | **Versão** | **Descrição**                                                        | **Autor**     | **Revisor**    |
| :----------:| :----------:| :--------------------------------------------------------------------:| :-------------:| :--------------:|
| 18/09/2026 | 1.0        | Confecção inicial do documento                                       | Arthur Suares | Milena Marques |
| 13/10/2026 | 1.1        | Reestruturação do documento de requisitos para atender ao modelo bkt | Arthur Suares | Ian Lucca      |