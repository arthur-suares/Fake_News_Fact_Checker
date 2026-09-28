# Fake News Fact Checker

Projeto com dois componentes executados separadamente:

- **Backend FastAPI**: consulta a Google Fact Check Tools API e oferece rotas de verificação.
- **Servidor MCP de análise de imagem**: oferece a ferramenta `analyze_image` ao OpenCode e usa OpenRouter para análise multimodal.

O servidor MCP não está conectado automaticamente ao fluxo HTTP do backend. O OpenCode inicia o servidor MCP sob demanda quando usa suas ferramentas. A imagem e a afirmação enviadas à ferramenta são encaminhadas ao OpenRouter.

## Pré-requisitos

- Python 3.10 ou superior
- pip
- Chave da Google Fact Check Tools API
- Chave do OpenRouter
- OpenCode instalado e disponível como comando `opencode`

## Ambiente único

Todas as dependências Python são instaladas no ambiente virtual `backend/.venv`. Há um único arquivo de ambiente: `backend/.env`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No macOS/Linux, edite `backend/.env` e configure as quatro variáveis abaixo. Preserve os valores que já estão nesse arquivo; não compartilhe nem versione chaves reais.

```env
DATABASE_URL=sqlite:///./fact_check.db
GOOGLE_FACT_CHECK_API_KEY=sua_chave_google
OPENROUTER_API_KEY=sua_chave_openrouter
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```

O modelo padrão é multimodal e gratuito no catálogo consultado. A disponibilidade e as cotas de modelos gratuitos podem mudar. `OPENROUTER_MODEL` pode ser trocado por outro modelo do OpenRouter que aceite imagens.

O cliente MCP carrega explicitamente esse arquivo central, mesmo sendo iniciado pelo OpenCode a partir da raiz do projeto. O FastAPI carrega o mesmo arquivo ao ser iniciado dentro de `backend/`.

## Executar o backend

Em um terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

O servidor inicia em `http://127.0.0.1:8000`.

Verifique o estado:

```bash
curl http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

Consulte a documentação interativa em `http://127.0.0.1:8000/docs`. Exemplo de consulta ao Google Fact Check:

```bash
curl --get http://127.0.0.1:8000/api/fact-check \
  --data-urlencode "query=vacinas causam autismo" \
  --data-urlencode "language_code=pt-BR"
```

Essa rota necessita de uma chave Google válida. O endpoint `POST /api/verifications` também aceita uma afirmação e pode armazenar uma imagem enviada, mas atualmente a análise multimodal MCP é uma ferramenta separada: esse endpoint não chama o servidor MCP.

## Testes do backend e da imagem

Com o ambiente virtual ativado:

```bash
cd backend
python -m pytest tests
cd ..
backend/.venv/bin/python -m pytest image-analysis/tests
```

Os testes unitários da imagem simulam o cliente OpenRouter; eles não fazem uma chamada externa nem exigem saldo/créditos.

## OpenCode e MCP

A configuração de projeto está em `opencode.json`, na raiz do repositório. Ela registra `image-analysis/server.py` como servidor MCP local usando `backend/.venv/bin/python`. Não é necessário iniciar esse processo manualmente: o OpenCode o inicia quando abre a configuração do projeto.

O transporte usado é stdio, não HTTP. Por isso, iniciar `backend/.venv/bin/python image-analysis/server.py` diretamente deixa o processo em primeiro plano, aguardando mensagens MCP, e o terminal não retorna ao prompt. Esse comportamento é esperado; não significa que o servidor travou. Use o OpenCode como cliente MCP para iniciar e encerrar o processo.

Inicie o OpenCode na raiz do repositório, em outro terminal:

```bash
cd /caminho/para/Fake_News_Fact_Checker
opencode
```

Confirme que o servidor está disponível:

```bash
opencode mcp list
```

O servidor deve aparecer como conectado/disponível. Para parar o MCP, encerre a sessão do OpenCode. Use `Ctrl+C` no terminal do servidor somente quando tiver iniciado o processo manualmente para depuração.

Para solicitar uma análise, use um caminho para uma imagem existente e uma afirmação. Exemplo no TUI do OpenCode:

```text
Use a ferramenta MCP image_analysis_analyze_image para analisar a imagem /caminho/para/vacina.jpg e comparar com a afirmação "Vacina causa autismo". Leia o arquivo, envie os bytes codificados em Base64 e informe o MIME type correto.
```

Também é possível fazer a solicitação pela CLI:

```bash
opencode run 'Use image_analysis_analyze_image para analisar /caminho/para/vacina.jpg e comparar com a afirmação "Vacina causa autismo". Envie a imagem em Base64 com o MIME type correto.'
```

O host MCP fornece o conteúdo da imagem como `image_base64`, o MIME type como `mime_type` e o texto opcional como `text`. O servidor rejeita Base64 inválido e imagens acima de 10 MiB. O resultado contém `description`, `possible_manipulation`, `confidence` e `analysis`.

## Fluxo dos dados

1. O OpenCode lê `opencode.json` e inicia o processo MCP por stdio usando o Python do venv central.
2. O modelo do OpenCode recebe a solicitação do usuário e chama `image_analysis_analyze_image`, passando Base64, MIME type e, se informado, o texto a comparar.
3. `image-analysis/server.py` valida e decodifica a imagem, aplica o limite de tamanho e chama `service.analyze_image`.
4. O serviço chama `vision_client`, que cria uma data URL e envia texto mais imagem ao endpoint compatível com OpenAI do OpenRouter.
5. O OpenRouter executa o modelo definido em `OPENROUTER_MODEL` e devolve uma resposta JSON.
6. O serviço valida os campos e a faixa de confiança com Pydantic; a resposta estruturada volta pelo MCP ao OpenCode.

O MCP é a interface entre o OpenCode e a análise; ele não executa a inferência. Compatibilidade visual não comprova a veracidade de uma afirmação. `confidence` reflete a confiança reportada pelo modelo sobre a interpretação visual, e `possible_manipulation` não é uma avaliação forense.