# Referencial Teórico: Knowledge Tracing, Bayesian Knowledge Tracing e Definição dos Parâmetros Iniciais

## 1. Introdução

O desenvolvimento de sistemas adaptativos baseados em inteligência artificial envolve não apenas a identificação de respostas corretas ou incorretas, mas também a capacidade de acompanhar a evolução do usuário ao longo de sucessivas interações. Em ambientes educacionais, essa necessidade é abordada pelo problema de *Knowledge Tracing* (KT), que consiste em estimar o conhecimento ou o domínio de habilidades de um indivíduo a partir de seu histórico de respostas.

Abdelrahman, Wang e Nunes (2023), em *Knowledge Tracing: A Survey*, apresentam uma revisão abrangente dos principais modelos utilizados para acompanhar o desenvolvimento do conhecimento em sistemas computacionais. Os autores destacam a relevância do KT para plataformas educacionais, sistemas tutores inteligentes e aplicações capazes de adaptar conteúdos às necessidades individuais. A pesquisa também organiza as diferentes abordagens de Knowledge Tracing, abrangendo modelos probabilísticos tradicionais e métodos baseados em aprendizagem profunda.

A partir desse referencial, o projeto **Verifica** utiliza o *Bayesian Knowledge Tracing* (BKT) para estimar o domínio de habilidades relacionadas à análise crítica de notícias. A proposta consiste em transformar a avaliação de informações em uma experiência gamificada, na qual as respostas do jogador são utilizadas para atualizar estimativas de domínio e orientar a seleção das questões seguintes.

Como o projeto se encontra em estágio de desenvolvimento de um produto mínimo viável (MVP), não há, neste momento, um conjunto amplo de respostas reais que permita estimar com segurança todos os parâmetros do modelo. Por esse motivo, a definição inicial dos parâmetros é tratada como uma decisão metodológica que deve ser justificada teoricamente, submetida a testes de consistência e avaliada por simulações controladas. Essa estratégia permite verificar o funcionamento do modelo sem confundir resultados experimentais simulados com evidências empíricas sobre jogadores reais.

## 2. Knowledge Tracing

O Knowledge Tracing busca representar a evolução do conhecimento de um indivíduo ao longo de uma sequência de atividades. Diferentemente de uma avaliação que considera apenas o resultado final de um teste, essa abordagem utiliza o histórico de interações para estimar o estado de domínio de determinadas habilidades.

Em um sistema adaptativo, essa estimativa pode apoiar decisões como a seleção de exercícios, a recomendação de conteúdos e a identificação de competências que demandam maior atenção. Dessa forma, o modelo não se limita a registrar o desempenho observado, mas procura inferir um estado de conhecimento que não pode ser medido diretamente.

Segundo Abdelrahman, Wang e Nunes (2023), os modelos de Knowledge Tracing podem ser agrupados, de maneira geral, em abordagens tradicionais e abordagens baseadas em aprendizagem profunda. Entre os modelos tradicionais, o Bayesian Knowledge Tracing ocupa uma posição importante por representar explicitamente a incerteza sobre o domínio de uma habilidade.

Essa característica é relevante para o Verifica porque uma resposta isolada não constitui evidência suficiente para afirmar que uma pessoa domina ou não uma habilidade de análise crítica. Um acerto pode ocorrer por conhecimento prévio ou por acaso, enquanto um erro pode decorrer de uma interpretação equivocada, de uma questão ambígua ou de uma falha pontual. O Knowledge Tracing oferece uma estrutura para interpretar essas observações ao longo de múltiplas interações.

## 3. Bayesian Knowledge Tracing

### 3.1 Fundamentos do modelo

O Bayesian Knowledge Tracing é um modelo probabilístico introduzido por Corbett e Anderson (1994) para acompanhar o desenvolvimento de habilidades em sistemas de aprendizagem. No BKT clássico, o estado de domínio de uma habilidade é representado por uma variável latente binária: o indivíduo é considerado como estando em um estado de domínio ou de não domínio daquela habilidade.

A variável é denominada latente porque não pode ser observada diretamente. O sistema observa as respostas fornecidas pelo usuário e utiliza essas evidências para atualizar a probabilidade de que ele domine a habilidade avaliada.

O modelo pode ser representado como um processo probabilístico de estados ocultos, frequentemente formulado por meio de um Modelo Oculto de Markov (*Hidden Markov Model*). As respostas corretas e incorretas constituem observações do processo, enquanto o domínio da habilidade é o estado que se deseja inferir.

De acordo com Badrinath, Wang e Pardos (2021), o BKT e suas extensões são utilizados para estimar o domínio cognitivo a partir de sequências de resolução de problemas. Os autores apresentam a biblioteca pyBKT, que implementa diferentes variantes do modelo e disponibiliza funcionalidades para geração de dados, estimação de parâmetros, predição e validação cruzada.

O uso de probabilidades permite que o sistema represente graus de confiança sobre o domínio de uma habilidade. Por exemplo, uma estimativa de 0,70 indica que, segundo o modelo e os dados observados, a probabilidade estimada de domínio é de 70%. Esse resultado não deve ser interpretado como uma medição direta e infalível do conhecimento do indivíduo, mas como uma inferência condicionada às hipóteses e aos parâmetros adotados.

### 3.2 Parâmetros do BKT clássico

O BKT clássico utiliza quatro parâmetros principais:

- **Probabilidade inicial de domínio — \(P(L_0)\):** representa a probabilidade de o indivíduo já dominar a habilidade antes da primeira interação observada.
- **Probabilidade de transição ou aprendizagem — \(P(T)\):** representa a probabilidade de um indivíduo que ainda não domina a habilidade passar ao estado de domínio após uma oportunidade de aprendizagem.
- **Probabilidade de chute — \(P(G)\):** representa a probabilidade de responder corretamente sem dominar a habilidade.
- **Probabilidade de deslize — \(P(S)\):** representa a probabilidade de responder incorretamente mesmo dominando a habilidade.

Esses parâmetros descrevem aspectos diferentes do processo. A probabilidade inicial representa uma hipótese sobre o conhecimento prévio; a transição representa a possibilidade de aprendizagem; e os parâmetros de chute e deslize representam a relação imperfeita entre o estado de conhecimento e a resposta observada.

O modelo clássico pressupõe que, depois de atingir o domínio, o indivíduo permanece nesse estado. Portanto, o esquecimento não é representado diretamente pela formulação original, embora existam variantes que permitem modelá-lo (Abdelrahman; Wang; Nunes, 2023).

### 3.3 Atualização probabilística

Seja \(P(L_t)\) a probabilidade estimada de domínio de uma habilidade antes da observação da resposta seguinte. A probabilidade de uma resposta correta pode ser expressa por:

\[
P(C_{t+1}) =
P(L_t)(1-P(S)) +
(1-P(L_t))P(G)
\]

A expressão combina dois cenários: o indivíduo domina a habilidade e responde corretamente, ou não a domina, mas acerta por chute.

Quando uma resposta correta é observada, a probabilidade de domínio é atualizada pela regra de Bayes:

\[
P(L_t \mid C_{t+1}) =
\frac{P(L_t)(1-P(S))}
{P(L_t)(1-P(S))+(1-P(L_t))P(G)}
\]

Para uma resposta incorreta, a atualização é:

\[
P(L_t \mid \neg C_{t+1}) =
\frac{P(L_t)P(S)}
{P(L_t)P(S)+(1-P(L_t))(1-P(G))}
\]

Após a atualização associada à resposta, o modelo clássico considera a possibilidade de aprendizagem. A probabilidade posterior de domínio é então ajustada pela probabilidade de transição:

\[
P(L_{t+1}) =
P(L_t \mid \text{resposta}) +
P(T)\left[1-P(L_t \mid \text{resposta})\right]
\]

Nessa expressão, \(P(L_t \mid \text{resposta})\) corresponde à probabilidade de domínio após considerar se a resposta foi correta ou incorreta.

Essas equações demonstram que a estimativa final depende tanto do histórico de respostas quanto dos parâmetros escolhidos. Consequentemente, a definição dos parâmetros iniciais influencia a interpretação dos resultados e o comportamento do sistema adaptativo.

## 4. Aplicação do BKT ao Verifica

### 4.1 Objetivo da aplicação

No Verifica, o BKT é utilizado para estimar o domínio de habilidades relacionadas à análise crítica de notícias. O objetivo não é apenas classificar uma notícia como verdadeira ou falsa, mas acompanhar o desempenho do jogador em diferentes dimensões de avaliação da informação.

A cada questão respondida, o sistema registra o resultado e atualiza a estimativa de domínio da habilidade correspondente. Essas estimativas podem ser utilizadas pelo mecanismo de seleção adaptativa para priorizar questões relacionadas às habilidades com menor domínio estimado.

A abordagem segue o princípio geral de Knowledge Tracing: utilizar o histórico de interações para orientar a adaptação da experiência às necessidades do indivíduo. Entretanto, a aplicação a competências de análise crítica de notícias constitui uma adaptação do modelo ao domínio específico do projeto. A adequação pedagógica dessa aplicação ainda precisa ser investigada por meio de avaliação empírica.

### 4.2 Habilidades monitoradas

O MVP organiza o acompanhamento em quatro habilidades:

| Habilidade | Descrição operacional |
|---|---|
| `SOURCE` | Avaliar a credibilidade e a procedência da fonte de uma notícia. |
| `EVIDENCE` | Verificar se as evidências apresentadas sustentam a alegação. |
| `CONTEXT` | Identificar omissões, distorções ou utilização de informações fora de contexto. |
| `VISUAL` | Avaliar a relação entre uma imagem e a alegação apresentada, incluindo possíveis incompatibilidades contextuais. |

Cada questão deve estar associada a uma única habilidade principal, de forma que a resposta forneça evidência interpretável para a atualização do respectivo estado de domínio.

Essa separação é uma decisão metodológica do projeto. Sua validade depende de que as questões realmente avaliem a habilidade à qual foram associadas. Uma questão que exija simultaneamente avaliar a fonte, verificar evidências e interpretar uma imagem pode produzir uma resposta difícil de atribuir a uma única competência.

Além disso, a dificuldade de uma questão não equivale ao domínio de uma habilidade. A dificuldade caracteriza o desafio oferecido pelo item, enquanto o BKT clássico representa o domínio por meio de uma variável latente e utiliza os parâmetros de chute, deslize e transição para interpretar as respostas. Caso o sistema precise representar explicitamente diferenças de dificuldade, isso deve ser tratado por uma extensão do modelo ou por uma regra adicional de seleção, sem presumir que a dificuldade já esteja contemplada nos quatro parâmetros clássicos.

### 4.3 Seleção adaptativa das questões

As estimativas de domínio podem orientar a escolha das próximas questões. No MVP, o seletor prioriza a habilidade com menor probabilidade estimada de domínio, evita questões já respondidas e considera a dificuldade dos itens disponíveis.

Essa estratégia constitui uma regra adaptativa simples, adequada para testar o fluxo principal do produto. Ela não deve ser confundida com uma política de seleção comprovadamente ótima: sua eficácia pedagógica depende da qualidade das questões, da confiabilidade das estimativas e da avaliação de resultados com usuários.

A utilização do BKT oferece, assim, uma forma de conectar as respostas individuais ao acompanhamento longitudinal das habilidades, enquanto o mecanismo de seleção utiliza essas estimativas para adaptar as partidas.

## 5. Definição e justificativa dos parâmetros iniciais

### 5.1 O problema da estimação em cenários com poucos dados

Em aplicações reais, os parâmetros do BKT podem ser estimados a partir de históricos de respostas. Entretanto, essa estimação depende da quantidade e da qualidade dos dados, da diversidade das sequências observadas e das hipóteses adotadas pelo modelo.

Badrinath, Wang e Pardos (2021) apresentam, na biblioteca pyBKT, procedimentos para estimação de parâmetros e experimentos de simulação utilizados para verificar o comportamento desses procedimentos. O trabalho demonstra a utilidade das simulações no desenvolvimento e na avaliação de implementações do BKT, mas não implica que parâmetros obtidos em simulações sejam automaticamente representativos de uma população real.

Shchepakin, Sankaranarayanan e Zimmaro (2024) discutem dificuldades adicionais da estimação por máxima verossimilhança e pelo algoritmo de Expectation-Maximization (EM). Entre os problemas apontados estão a convergência para mínimos locais, a existência de diferentes conjuntos de parâmetros que explicam os mesmos dados de forma semelhante e a obtenção de valores degenerados, incompatíveis com o significado conceitual dos parâmetros.

Esses problemas são particularmente relevantes para o Verifica. Como o MVP ainda não dispõe de um conjunto amplo de sequências reais de jogadores, tentar estimar livremente todos os parâmetros para cada habilidade pode produzir valores instáveis ou difíceis de interpretar.

Além disso, os dados de um conjunto de notícias classificadas como verdadeiras ou falsas não constituem, por si só, dados de aprendizagem adequados para estimar os parâmetros do BKT. A estimação exige observações das respostas dos usuários em sequência e uma definição consistente das habilidades avaliadas. O rótulo de veracidade de uma notícia não informa diretamente se um jogador domina a habilidade `SOURCE`, `EVIDENCE`, `CONTEXT` ou `VISUAL`.

Por esse motivo, o MVP adota uma abordagem inicial baseada em parâmetros definidos explicitamente, com justificativas conceituais e validação por simulações. Essa decisão deve ser entendida como uma estratégia provisória de modelagem, não como uma calibração empírica concluída.

### 5.2 Critérios gerais para a escolha dos parâmetros

A definição dos parâmetros iniciais deve atender a quatro critérios.

**1. Coerência conceitual.** Cada parâmetro precisa representar o fenômeno que o modelo pretende descrever. Por exemplo, a probabilidade de chute deve representar acertos de usuários que ainda não dominam a habilidade, enquanto a probabilidade de deslize deve representar erros de usuários que já a dominam.

**2. Coerência matemática.** Os parâmetros devem pertencer a intervalos probabilisticamente válidos e respeitar restrições que preservem o significado do modelo. Shchepakin, Sankaranarayanan e Zimmaro (2024) demonstram a importância de restringir o espaço de parâmetros para evitar situações em que o modelo atribui maior probabilidade de acerto a indivíduos que não dominam uma habilidade do que àqueles que a dominam.

**3. Adequação ao formato do jogo.** O número de alternativas, a qualidade dos distratores, a ambiguidade das questões e a clareza do feedback influenciam a interpretação das respostas. Assim, valores encontrados em outras aplicações não devem ser transferidos automaticamente para o jogo sem avaliar a compatibilidade entre os contextos.

**4. Transparência sobre a incerteza.** Na ausência de dados reais suficientes, os valores devem ser apresentados como hipóteses iniciais. A documentação precisa informar quais decisões são fundamentadas na literatura, quais são escolhas de engenharia e quais dependem de futura validação empírica.

### 5.3 Justificativa da probabilidade inicial de domínio — \(P(L_0)\)

A probabilidade inicial representa a hipótese de que o jogador já domina uma habilidade antes de responder à primeira questão considerada pelo modelo.

No BKT clássico, esse parâmetro pode representar uma proporção inicial da população que domina determinada habilidade. Entretanto, no contexto do  Verifica, não há necessariamente evidência empírica suficiente para determinar essa proporção antes da coleta de dados reais.

Por isso, o valor inicial deve ser escolhido como uma hipótese explícita de modelagem. Um valor intermediário pode ser útil em testes iniciais por evitar assumir que todos os jogadores começam sem domínio ou que todos já dominam a habilidade. Isso não significa, porém, que uma probabilidade intermediária seja empiricamente correta para o público do projeto.

Como as quatro habilidades podem apresentar níveis distintos de familiaridade na população, futuramente poderá ser necessário investigar se elas compartilham a mesma distribuição inicial de domínio. No MVP, a utilização de um valor comum ou de valores diferentes deve ser documentada como uma escolha de implementação.

A justificativa final para \(P(L_0)\) deve registrar o valor adotado, a razão de sua escolha e os resultados de testes que avaliem a influência dessa hipótese sobre as estimativas produzidas.

### 5.4 Justificativa da probabilidade de aprendizagem — \(P(T)\)

A probabilidade de transição representa a possibilidade de um jogador que ainda não domina uma habilidade passar a dominá-la após uma oportunidade de aprendizagem.

No contexto do projeto, essa oportunidade está associada à interação com uma questão e, conforme o funcionamento implementado, ao feedback recebido após a resposta. A hipótese de que uma interação pode contribuir para a aprendizagem é coerente com o propósito de um jogo educativo, mas não determina, por si só, a magnitude da probabilidade de transição.

Uma probabilidade elevada pode fazer as estimativas de domínio aumentarem rapidamente ao longo de uma partida curta. Por outro lado, uma probabilidade muito baixa pode tornar o perfil praticamente insensível ao número de interações. A escolha precisa, portanto, ser avaliada em relação ao comprimento das partidas e ao comportamento esperado do modelo.

No MVP, recomenda-se utilizar um valor inicial conservador e testar diferentes cenários de transição. O objetivo é verificar se o perfil evolui de maneira estável e se o resultado permanece razoável quando a hipótese de aprendizagem é alterada.

É importante reconhecer uma limitação conceitual: o BKT clássico pressupõe que o domínio é adquirido de forma monotônica, sem esquecimento. Além disso, uma resposta correta não prova que houve aprendizagem, assim como uma resposta incorreta não prova que não houve aprendizagem. A probabilidade de transição representa uma hipótese do modelo, e não uma observação direta da aprendizagem ocorrida.

### 5.5 Justificativa da probabilidade de chute — \(P(G)\)

A probabilidade de chute representa a chance de um jogador acertar uma questão sem dominar a habilidade avaliada.

Esse parâmetro é especialmente relevante em questões de múltipla escolha. Se uma questão possui alternativas independentes e igualmente plausíveis, e o jogador escolhe aleatoriamente entre \(k\) alternativas, a probabilidade teórica de acerto ao acaso é:

\[
P(G) = \frac{1}{k}
\]

Por exemplo, em uma questão com quatro alternativas, a probabilidade de acerto por escolha aleatória seria de 0,25 sob essas hipóteses.

Entretanto, essa relação é apenas um ponto de referência teórico. Ela pressupõe escolha aleatória e alternativas equiprováveis. Em um jogo de análise crítica de notícias, um jogador pode eliminar alternativas claramente incorretas, utilizar conhecimento prévio ou reconhecer padrões de formulação das perguntas. Nessas situações, a probabilidade efetiva de acerto sem domínio pleno pode ser diferente da probabilidade de escolha aleatória.

Por esse motivo, o número de alternativas pode orientar a definição inicial de \(P(G)\), mas não deve ser considerado uma estimativa empírica definitiva. O valor adotado precisa ser testado por simulação e reavaliado quando houver respostas reais.

### 5.6 Justificativa da probabilidade de deslize — \(P(S)\)

A probabilidade de deslize representa a chance de um jogador que domina uma habilidade responder incorretamente.

No projeto, os deslizes podem decorrer de fatores como leitura desatenta, interpretação equivocada do enunciado, dificuldade de compreensão ou ambiguidade na construção da questão. Entretanto, o BKT clássico não identifica separadamente essas causas: ele as representa por meio de uma probabilidade agregada de erro no estado de domínio.

A escolha de \(P(S)\) deve considerar a qualidade esperada das questões e a possibilidade de que usuários competentes cometam erros ocasionais. Assumir uma probabilidade nula implicaria que todo jogador que domina uma habilidade responderia corretamente a todas as questões associadas a ela, hipótese excessivamente restritiva para uma aplicação real.

Por outro lado, uma probabilidade de deslize elevada pode reduzir a capacidade do sistema de interpretar acertos e erros como evidências de domínio. Assim, o valor deve ser suficientemente plausível para representar erros ocasionais, mas precisa ser avaliado quanto ao impacto nas atualizações probabilísticas.

Como ainda não há dados suficientes para estimar a taxa de erro de jogadores que comprovadamente dominam cada habilidade, o valor inicial de \(P(S)\) deve ser apresentado como uma hipótese de projeto.

### 5.7 Restrições conceituais e matemáticas

Além de definir valores iniciais plausíveis, é necessário garantir que os parâmetros respeitem as relações exigidas pelo modelo.

Shchepakin, Sankaranarayanan e Zimmaro (2024) apresentam restrições derivadas do significado probabilístico do BKT. Entre as condições discutidas pelos autores estão:

\[
0 < P(G) < 1
\]

\[
0 < P(S) < 1
\]

\[
0 < P(T) < 1
\]

e

\[
P(G) + P(S) \leq 1
\]

Uma consequência importante é:

\[
1-P(S) \geq P(G)
\]

Essa relação assegura que a probabilidade de responder corretamente quando se domina a habilidade não seja inferior à probabilidade de acerto por chute quando a habilidade não é dominada.

Os autores também apresentam uma condição adicional relacionada à probabilidade inicial e à dinâmica de transição do modelo. Portanto, as desigualdades acima são critérios importantes, mas não substituem a verificação conjunta de todas as condições aplicáveis à parametrização adotada.

Essas restrições não determinam um único conjunto de parâmetros correto para o projeto. Elas delimitam combinações matematicamente admissíveis e conceitualmente coerentes. A escolha entre os conjuntos admissíveis ainda depende das hipóteses sobre o jogo e da futura avaliação empírica.

### 5.8 Registro e rastreabilidade dos parâmetros

Para garantir a transparência metodológica, os parâmetros devem ser documentados em uma tabela de configuração.

| Parâmetro | Valor inicial | Justificativa | Situação |
|---|---:|---|---|
| \(P(L_0)\) | A definir | Hipótese sobre o domínio anterior à primeira questão | Provisório |
| \(P(T)\) | A definir | Hipótese sobre a aprendizagem por oportunidade de interação | Provisório |
| \(P(G)\) | A definir | Formato das alternativas e possibilidade de acerto sem domínio | Provisório |
| \(P(S)\) | A definir | Possibilidade de erros ocasionais apesar do domínio | Provisório |

Os valores devem ser preenchidos a partir da configuração efetivamente utilizada no código. Não é apropriado apresentar valores hipotéticos nesta tabela como se fossem os valores implementados.

Para cada parâmetro, recomenda-se registrar também a data da configuração, a versão do modelo, a origem da justificativa, as restrições verificadas e os resultados dos testes de sensibilidade. Esse registro permite comparar versões futuras e identificar se alterações nos resultados decorreram de mudanças nos parâmetros, na implementação ou nas questões utilizadas.

## 6. Conhecimento prévio, elicitação de parâmetros e simulação

### 6.1 Elicitação de conhecimento prévio

Bockting, Radev e Bürkner (2024) investigam métodos para traduzir conhecimento de especialistas em distribuições a priori para parâmetros de modelos bayesianos. Os autores propõem uma abordagem baseada em simulação para auxiliar na escolha dos hiperparâmetros de distribuições a priori, demonstrando sua aplicação em diferentes cenários de modelagem.

Esse trabalho oferece uma fundamentação metodológica para reconhecer que o conhecimento prévio pode ser incorporado de maneira explícita quando os dados são limitados. Entretanto, sua contribuição não deve ser interpretada como uma receita direta de valores para os parâmetros do BKT. O método estudado é geral e trata da elicitação de distribuições a priori; sua aplicação específica ao BKT exigiria definir uma formulação probabilística apropriada e executar o procedimento correspondente.

No Verifica, a contribuição mais imediata desse referencial é a distinção entre escolher parâmetros arbitrariamente e formular hipóteses explícitas que possam ser examinadas por simulações. A elicitação pode se tornar uma extensão metodológica futura, caso o projeto passe a representar formalmente a incerteza sobre os parâmetros.

### 6.2 Uso de simulações no desenvolvimento do BKT

Badrinath, Wang e Pardos (2021) apresentam experimentos com dados simulados para verificar o comportamento dos procedimentos de estimação implementados na biblioteca pyBKT. Esse tipo de experimento é útil porque permite construir sequências nas quais os parâmetros geradores e os estados latentes são conhecidos.

No projeto, as simulações podem ser utilizadas para avaliar se o algoritmo atualiza as probabilidades corretamente, se as estimativas respondem de maneira coerente a sequências de acertos e erros e se o seletor adaptativo respeita as regras definidas para a escolha das questões.

Uma avaliação mais completa deve distinguir pelo menos três objetivos:

1. **Verificação da implementação:** confirmar que as equações e as atualizações são executadas corretamente.
2. **Recuperação de parâmetros ou estados:** verificar se um procedimento de estimação consegue recuperar valores ou estados conhecidos que geraram os dados simulados.
3. **Avaliação de decisões adaptativas:** verificar se o sistema seleciona as questões esperadas de acordo com as probabilidades de domínio e as restrições operacionais.

Esses testes não são equivalentes. Uma implementação pode executar corretamente as equações sem que os parâmetros escolhidos representem adequadamente o comportamento humano. Da mesma forma, uma boa recuperação de parâmetros em dados gerados a partir do próprio modelo não garante que as hipóteses do modelo correspondam ao processo real de aprendizagem.

### 6.3 Limites da validação simulada

A validação por simulação permite controlar as condições experimentais e conhecer os valores que geraram os dados. Contudo, quando os dados são inteiramente artificiais, as conclusões dependem das hipóteses adotadas para gerar as sequências.

Se as simulações utilizarem os mesmos parâmetros fixos empregados pelo algoritmo, elas podem demonstrar consistência interna, mas não constituem evidência independente de que esses parâmetros sejam adequados para jogadores reais.

Para reduzir esse risco, a avaliação deve considerar diferentes cenários de domínio inicial, aprendizagem, chute e deslize, além de variar o número de respostas por jogador. Quando houver um procedimento de estimação, os parâmetros recuperados devem ser comparados com os valores usados para gerar os dados.

A análise de sensibilidade também deve investigar se pequenas mudanças nos parâmetros alteram significativamente as estimativas de domínio ou as decisões do seletor adaptativo. Se o comportamento variar muito entre cenários plausíveis, os resultados devem ser apresentados como dependentes das hipóteses utilizadas.

Dessa forma, as simulações constituem uma etapa legítima de verificação e análise metodológica, mas não substituem a coleta de respostas reais para validar a interpretação pedagógica do perfil gerado.

## 7. Estratégia de validação adotada no MVP

Considerando a ausência de um conjunto amplo de interações reais, a estratégia inicial de validação do Verifica deve priorizar a transparência dos parâmetros e a verificação do comportamento do modelo.

A abordagem pode ser organizada em quatro etapas:

1. **Definição dos parâmetros de referência:** documentar os valores efetivamente implementados, suas justificativas e as restrições verificadas.
2. **Testes com sequências controladas:** gerar respostas simuladas para verificar o comportamento das atualizações e, quando aplicável, a recuperação de estados ou parâmetros conhecidos.
3. **Análise de sensibilidade:** repetir os testes com combinações alternativas de parâmetros e comparar as estimativas de domínio e as decisões de seleção.
4. **Coleta futura de dados reais:** registrar as respostas dos jogadores, as questões respondidas, as habilidades associadas e a ordem temporal das interações, de forma a permitir uma avaliação empírica posterior.

Quando houver dados reais suficientes e de qualidade adequada, será possível avaliar a estimação dos parâmetros por métodos como máxima verossimilhança e Expectation-Maximization, com restrições conceituais quando apropriado. A avaliação deverá considerar a capacidade de prever respostas não utilizadas na estimação, preferencialmente com separação entre jogadores nos conjuntos de treinamento e teste.

Métricas como log-loss e Brier score podem ser utilizadas para avaliar a qualidade das probabilidades previstas, enquanto curvas de calibração ajudam a investigar se as probabilidades estimadas correspondem às frequências observadas. A escolha das métricas e a interpretação dos resultados precisam considerar o objetivo da avaliação e as limitações da amostra.

Até que essa validação seja realizada, os parâmetros devem permanecer identificados como iniciais ou provisórios, e as conclusões sobre o domínio dos jogadores devem ser interpretadas como estimativas do modelo, não como diagnósticos definitivos de suas competências.

## 8. Considerações finais

O Bayesian Knowledge Tracing fornece uma estrutura probabilística para estimar a evolução do domínio de habilidades a partir de sequências de respostas. Sua utilização no Verifica permite relacionar as interações do jogador a estimativas individualizadas de domínio, que podem orientar a seleção adaptativa de questões.

A escolha desse modelo está alinhada à literatura de Knowledge Tracing, que reconhece a relevância de acompanhar estados latentes de conhecimento em sistemas adaptativos. Entretanto, a qualidade dos resultados depende da definição das habilidades, da qualidade das questões, da coerência dos parâmetros e da adequação das hipóteses do modelo ao contexto de aplicação.

Diante da limitação de dados reais no estágio atual do projeto, a definição explícita de parâmetros iniciais, a imposição de restrições conceituais e a realização de simulações constituem uma estratégia metodológica apropriada para desenvolver e verificar o MVP. Essa estratégia não equivale a uma calibração empírica definitiva, mas oferece uma base transparente e reproduzível para a implementação.

Como continuidade, a coleta de interações reais permitirá investigar a adequação dos parâmetros, comparar configurações e avaliar se as estimativas produzidas refletem de maneira útil o desempenho dos jogadores. Dessa forma, a proposta reconhece tanto o potencial do BKT para a adaptação da experiência quanto a necessidade de validação contínua antes de atribuir significado empírico forte ao perfil de habilidades gerado.

## Referências

> ABDELRAHMAN, Ghodai; WANG, Qing; NUNES, Bernardo. Knowledge Tracing: A Survey. *ACM Computing Surveys*, v. 55, n. 11, art. 224, 2023. DOI: https://doi.org/10.1145/3569576.

> BADRINATH, Anirudhan; WANG, Frederic; PARDOS, Zachary A. pyBKT: An Accessible Python Library of Bayesian Knowledge Tracing Models. In: *Proceedings of the 14th International Conference on Educational Data Mining (EDM)*, 2021, p. 468–474. Disponível em: https://arxiv.org/abs/2105.00385.

> BOCKTING, Florence; RADEV, Stefan T.; BÜRKNER, Paul-Christian. Simulation-based prior knowledge elicitation for parametric Bayesian models. *Scientific Reports*, v. 14, art. 17330, 2024. DOI: https://doi.org/10.1038/s41598-024-68090-7.

> CORBETT, Albert T.; ANDERSON, John R. Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, v. 4, p. 253–278, 1994. DOI: https://doi.org/10.1007/BF01099821.

> SHCHEPAKIN, Denis; SANKARANARAYANAN, Sreecharan; ZIMMARO, Dawn. Parametric Constraints for Bayesian Knowledge Tracing from First Principles. In: *Proceedings of the 17th International Conference on Educational Data Mining (EDM)*, 2024. Disponível em: https://educationaldatamining.org/edm2024/proceedings/2024.EDM-long-papers.2/index.html.