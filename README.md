# Fake_News_Fact_Checker

Backend desenvolvido em Python utilizando **FastAPI** para consultar a **Google Fact Check Tools API**.

A aplicação disponibiliza uma API própria que recebe uma afirmação ou assunto e consulta verificações existentes na API do Google.

## 1. Pré-requisitos

Antes de iniciar, é necessário ter instalado:

* Python 3.10 ou superior
* `pip`
* Uma conta no Google Cloud
* Uma API Key com acesso à **Fact Check Tools API**

---

## 2. Clonar ou acessar o projeto

Entre no diretório do projeto:

```bash
cd Fake_News_Fact_Checker
```

---

## 3. Criar ambiente virtual

Recomenda-se utilizar um ambiente virtual Python.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 4. Instalar as dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

As principais dependências são:

```text
fastapi
uvicorn
requests
python-dotenv
pydantic-settings
```

### Função das dependências

* **FastAPI** — framework utilizado para criar a API HTTP.
* **Uvicorn** — servidor ASGI responsável por executar a aplicação FastAPI.
* **Requests** — utilizado para realizar requisições HTTP para a API do Google.
* **python-dotenv** — permite carregar variáveis de ambiente a partir do arquivo `.env`.
* **pydantic-settings** — utilizado para gerenciar as configurações da aplicação.

---

## 5. Configurar a Google Fact Check Tools API

É necessário criar um projeto no Google Cloud e ativar a:

**Fact Check Tools API**

A API Key pode ser criada em:

**Google Cloud Console → APIs e serviços → Credenciais → Criar credenciais → Chave de API**

A aplicação utiliza o endpoint:

```text
https://factchecktools.googleapis.com/v1alpha1/claims:search
```

---

## 6. Configurar a API Key

Na raiz do projeto, crie um arquivo chamado:

```text
.env
```

Adicione:

```env
GOOGLE_FACT_CHECK_API_KEY=SUA_API_KEY_AQUI
```

Exemplo:

```env
GOOGLE_FACT_CHECK_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX
```

### Importante

O arquivo `.env` não deve ser enviado para o Git.

Certifique-se de que ele esteja presente no `.gitignore:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## 7. Estrutura do projeto

A estrutura esperada é:

```text
fact-check-backend/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
│
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── models.py
    │
    └── services/
        ├── __init__.py
        └── google_fact_check.py
```

---

## 8. Executar o servidor

Com o ambiente virtual ativado, execute:

```bash
uvicorn app.main:app --reload
```

O servidor será iniciado, normalmente, em:

```text
http://localhost:8000
```

A opção `--reload` faz com que o servidor seja reiniciado automaticamente quando os arquivos do projeto forem alterados.

---

## 9. Verificar se o servidor está funcionando

Abra no navegador:

```text
http://localhost:8000/
```

Resposta esperada:

```json
{
    "message": "Fact Check Backend",
    "status": "running"
}
```

Também é possível verificar o endpoint de saúde:

```text
http://localhost:8000/health
```

Resposta:

```json
{
    "status": "ok"
}
```

---

## 10. Documentação Swagger

O FastAPI fornece uma documentação interativa automaticamente.

Acesse:

```text
http://localhost:8000/docs
```

Nessa página será possível visualizar e testar as rotas da API.

---

## 11. Consultar uma afirmação

A principal rota do backend é:

```http
GET /api/fact-check
```

Ela recebe o parâmetro:

```text
query
```

Exemplo:

```text
http://localhost:8000/api/fact-check?query=vacinas%20causam%20autismo
```

Também podem ser utilizados:

```text
language_code
page_size
max_age_days
```

Exemplo:

```text
http://localhost:8000/api/fact-check?query=vacinas%20causam%20autismo&language_code=pt-BR&page_size=10
```

---

## 12. Teste utilizando Postman

Abra o Postman e crie uma nova requisição.

### Método

```text
GET
```

### URL

```text
http://localhost:8000/api/fact-check
```

Em **Params**, adicione:

| Key             | Value                    |
| --------------- | ------------------------ |
| `query`         | `vacinas causam autismo` |
| `language_code` | `pt-BR`                  |
| `page_size`     | `10`                     |

Clique em **Send**.

O backend irá:

```text
Postman
   ↓
FastAPI
   ↓
Google Fact Check Tools API
   ↓
FastAPI
   ↓
Postman
```

A resposta será um JSON contendo as verificações encontradas.

---

## 13. Exemplo de resposta

Uma resposta poderá possuir a seguinte estrutura:

```json
{
    "claims": [
        {
            "text": "Criança desenvolve autismo após receber 18 doses de vacina em um único dia",
            "claimant": "Postagens em redes sociais",
            "claimReview": [
                {
                    "publisher": {
                        "name": "Estadão",
                        "site": "estadao.com.br"
                    },
                    "title": "É falso que criança tenha recebido 18 vacinas e desenvolvido autismo",
                    "textualRating": "Falso",
                    "languageCode": "pt"
                }
            ]
        }
    ]
}
```

O campo `textualRating` representa a classificação atribuída pelo veículo ou organização responsável pela verificação.

---

## 14. Testes adicionais

É possível testar diferentes afirmações.

### Exemplo 1

```text
query = vacinas causam autismo
```

### Exemplo 2

```text
query = terra plana
```

### Exemplo 3

```text
query = beber água cura qualquer doença
```

Também é recomendado testar uma requisição sem `query`:

```text
GET http://localhost:8000/api/fact-check
```

Nesse caso, a API deverá retornar:

```text
422 Unprocessable Entity
```

pois o parâmetro `query` é obrigatório.

---

## 15. Encerrar o servidor

Para parar o servidor:

```text
CTRL + C
```

Para sair do ambiente virtual:

```bash
deactivate
```

---

## 16. Fluxo completo

O funcionamento do sistema pode ser resumido da seguinte forma:

```text
                 Usuário / Frontend
                         │
                         │ HTTP
                         ▼
              ┌─────────────────────┐
              │   FastAPI Backend   │
              │                     │
              │ /api/fact-check     │
              └──────────┬──────────┘
                         │
                         │ HTTPS
                         │ API Key
                         ▼
              ┌─────────────────────┐
              │ Google Fact Check   │
              │ Tools API           │
              └──────────┬──────────┘
                         │
                         ▼
                  Fact-checks
                   existentes
                         │
                         ▼
              ┌─────────────────────┐
              │   JSON Response     │
              └─────────────────────┘
```

O backend funciona como uma camada intermediária entre o sistema cliente e a Google Fact Check Tools API. Isso permite que posteriormente outros componentes, como um **MCP Server**, consumam o backend sem precisar acessar diretamente a API da Google ou armazenar sua API Key.
