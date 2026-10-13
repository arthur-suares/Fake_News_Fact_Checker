## Introdução

### Sobre o projeto

O **Fake News Fact Checker** é um projeto que busca desenvolver habilidades de avaliação crítica de informações por meio de uma experiência gamificada. Em vez de se limitar à verificação isolada de notícias, o sistema acompanha o desempenho do usuário ao longo de várias interações, identificando habilidades que precisam ser desenvolvidas.

Durante as partidas, o usuário responde a perguntas relacionadas à análise de notícias, evidências, fontes e imagens. As respostas são registradas para acompanhar sua evolução e orientar a seleção de perguntas futuras.

## Como funciona

O sistema organiza a experiência em partidas compostas por rodadas de perguntas. Cada pergunta está associada a uma habilidade específica:

- **SOURCE:** avaliação da confiabilidade e da origem das fontes.
- **EVIDENCE:** avaliação das evidências apresentadas em apoio a uma afirmação.
- **CONTEXT:** identificação de informações descontextualizadas, omitidas ou distorcidas.
- **VISUAL:** avaliação da relação entre imagens e o conteúdo noticiado.

O desempenho do usuário é acompanhado pelo **Bayesian Knowledge Tracing (BKT)**, um modelo probabilístico utilizado para estimar o domínio de habilidades a partir de sequências de respostas. Essas estimativas ajudam o sistema a priorizar perguntas relacionadas às habilidades em que o usuário apresenta menor domínio estimado.

A verificação externa de notícias pode complementar a experiência, fornecendo informações adicionais sobre conteúdos já avaliados por serviços de checagem. Essa funcionalidade não substitui o acompanhamento de habilidades realizado pelo BKT.

## Objetivos

- Proporcionar uma experiência gamificada de avaliação crítica de notícias.
- Registrar as respostas e o histórico de interação dos usuários.
- Estimar o domínio individual das quatro habilidades monitoradas.
- Adaptar a seleção de perguntas de acordo com as estimativas de domínio.
- Apresentar ao usuário seu desempenho e sua evolução ao longo das partidas.

## Escopo do MVP

A versão inicial contempla o gerenciamento de notícias e perguntas, a execução de partidas, o registro de respostas, a atualização das estimativas de domínio pelo BKT e a apresentação do perfil de habilidades.

Os parâmetros do BKT serão inicialmente configurados para o MVP. O treinamento automático desses parâmetros e a implementação de modelos adaptativos mais complexos não fazem parte do escopo inicial.

## Tecnologias e arquitetura

O projeto utiliza um backend em Python com FastAPI, persistência de dados por meio do SQLAlchemy e uma interface web desenvolvida com Next.js e React. A arquitetura deve permitir a integração entre partidas, perguntas, respostas, acompanhamento de habilidades e funcionalidades de verificação de notícias.

## Observação metodológica

O BKT estima o domínio de habilidades do usuário com base em seu histórico de respostas. Ele não é, por si só, um classificador de notícias falsas ou verdadeiras. A qualidade das estimativas depende da associação adequada entre cada pergunta e a habilidade que ela pretende avaliar, além da consistência do conteúdo e das respostas corretas cadastradas.

## Histórico de Versões

| **Data**   | **Versão** | **Descrição** | **Autor** | **Revisor** |
| :----------:| :----------:| :-------------:| :---------:| :-----------:|
| 13/10/2026 | 1.0        | Confeção do documento             | Arthur Suares         | Ian Lucca           |