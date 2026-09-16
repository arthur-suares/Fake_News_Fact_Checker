## Arquitetura do Software

### 1. Visão Geral da Arquitetura

O sistema proposto é composto por quatro elementos principais: um Frontend, um Servidor Backend, um Servidor MCP (Model Context Protocol) e uma API externa do Google responsável pela checagem de fatos.
A arquitetura segue uma abordagem modular, na qual cada componente possui uma responsabilidade específica. O Backend atua como intermediário entre a aplicação e a API externa de checagem de fatos, enquanto o servidor MCP funciona como uma camada de processamento responsável por consumir os serviços disponibilizados pelo Backend, interpretar os resultados e humanizar as respostas antes de encaminhá-las ao Frontend.
O fluxo geral de comunicação pode ser descrito da seguinte maneira:
Frontend → Servidor MCP → Servidor Backend → API do Google
Após o processamento das informações:
API do Google → Servidor Backend → Servidor MCP → Frontend
Dessa forma, o Frontend não precisa possuir conhecimento sobre a API externa ou sobre os detalhes de autenticação e comunicação com os serviços de terceiros.

### 2. Componentes da Arquitetura

#### 2.1. Frontend
O Frontend representa a camada de apresentação do sistema e é responsável pela interação direta com o usuário.
Suas principais responsabilidades são:
Receber do usuário o conteúdo que deverá ser analisado;
Enviar a solicitação para o servidor MCP;
Receber a resposta processada e humanizada;
Apresentar os resultados de maneira clara e compreensível;
Informar ao usuário os resultados da checagem de fatos;
Tratar estados de carregamento, erros e ausência de resultados.
O Frontend não deve realizar diretamente chamadas à API do Google. Essa decisão reduz o acoplamento da aplicação com serviços externos e evita que informações sensíveis, como credenciais e chaves de API, sejam expostas no lado do cliente.

#### 2.2. Servidor MCP

O servidor MCP funciona como uma camada intermediária entre a interface da aplicação e o Backend.
Sua principal função é disponibilizar ferramentas (tools) que podem ser utilizadas para executar operações relacionadas à checagem de fatos.
Entre suas responsabilidades estão:
Receber solicitações provenientes do Frontend;
Disponibilizar tools para consulta ao Backend;
Solicitar ao Backend a realização da checagem de fatos;
Receber e interpretar os resultados retornados;
Processar as informações obtidas;
Humanizar a resposta técnica retornada pelo serviço de checagem;
Estruturar a resposta final para o consumo do Frontend.
O uso do MCP permite separar a lógica de interação com os serviços do Backend da lógica responsável pela apresentação das informações ao usuário.
Uma das principais vantagens dessa abordagem é que o MCP pode atuar como uma camada de orquestração. Dessa maneira, futuramente podem ser adicionadas novas tools sem que seja necessário modificar significativamente o Frontend.

#### 2.3. Servidor Backend

O Backend é responsável pela comunicação com os serviços externos e pela disponibilização de uma API interna para o servidor MCP.
Suas principais responsabilidades são:
Disponibilizar endpoints para o servidor MCP;
Receber requisições de checagem de fatos;
Validar os dados recebidos;
Realizar autenticação junto à API externa;
Encaminhar as informações para a API do Google;
Processar e normalizar os dados retornados;
Retornar ao servidor MCP uma resposta estruturada;
Gerenciar erros relacionados à comunicação externa;
Implementar mecanismos de segurança e controle de acesso.
O Backend funciona como uma camada de abstração sobre a API do Google. Assim, caso o serviço externo seja substituído futuramente, as alterações ficam concentradas principalmente nessa camada, sem necessidade de modificar diretamente o Frontend ou o servidor MCP.

#### 2.4. API de Checagem de Fatos

A API externa do Google representa o serviço responsável por fornecer informações utilizadas na verificação dos fatos apresentados pelo usuário.
O Backend realiza as requisições necessárias para esse serviço e recebe informações relacionadas aos resultados encontrados.
Essa comunicação deve ser realizada exclusivamente pelo Backend, mantendo as credenciais e demais configurações sensíveis no ambiente do servidor.
Os dados retornados pela API externa podem apresentar uma estrutura mais técnica ou complexa. Por esse motivo, o Backend deve realizar uma etapa de normalização antes de entregar os dados ao servidor MCP.

## Histórico de Versões

| **Data**   | **Versão** | **Descrição**                              | **Autor** | **Revisor**                             |
| :----------:| :----------:| :------------------------------------------:| :---------:| :---------------------------------------:|
| 16/09/2026 | 1.0        | Transcrevendo documentação inicial do docs | Milena Marques e Arthur Suares | Ian Lucca e Laura Gomes |