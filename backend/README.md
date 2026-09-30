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
OPENROUTER_FALLBACK_MODELS=qwen/qwen3.8-27b:free
```

O servidor MCP tenta primeiro o modelo de `OPENROUTER_MODEL`; se o OpenRouter retornar erro, tentará os modelos listados em `OPENROUTER_FALLBACK_MODELS`, na ordem. Ambos os padrões aceitam imagem e estão sujeitos às cotas compartilhadas do tier gratuito. Para maior disponibilidade, substitua um fallback por um modelo pago que aceite imagens. Os IDs e cotas podem mudar.

O OpenCode usa credenciais próprias para o modelo conversacional; `OPENROUTER_API_KEY` no `.env` autentica o servidor MCP, mas não conecta automaticamente o OpenCode ao provedor. Na raiz do projeto, inicie `opencode`, execute `/connect`, selecione **OpenRouter** e insira uma chave OpenRouter. Depois, `/models` mostra as opções; a configuração do projeto seleciona `openrouter/google/gemma-3-27b-it` como modelo padrão. O Gemma 3 não está configurado como gratuito: chamadas do OpenCode consomem os créditos da sua conta. O Gemma 4/Qwen free configurados para o MCP podem receber 429 durante picos de uso.

O OpenCode carrega [OPENCODE_INSTRUCTIONS.md](../OPENCODE_INSTRUCTIONS.md) para orientar o uso das ferramentas. Essas instruções melhoram a consistência, mas a decisão final de chamar uma tool ainda depende do modelo. Para modelos sem bom suporte a tool-calling, escolha outro modelo em `/models` ou passe `--model openrouter/google/gemma-3-27b-it` ao comando `opencode run`.

As chaves de API são segredos. Se uma chave for colada em chat, issue ou log compartilhado, revogue-a no provedor e crie outra; não a inclua em `opencode.json` nem em documentação versionada.

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

### Rotas REST de verificação

- `GET /api/fact-check`: retorna a resposta original da Google Fact Check Tools API. Aceita `query`, `language_code`, `max_age_days`, `page_size` e `page_token`.
- `POST /api/fact-check`: recebe JSON com os mesmos parâmetros e retorna avaliações organizadas por afirmação, publicação, classificação, URL e data. A resposta inclui `status`, `review_count` e `next_page_token`; não cria um veredito próprio.
- `POST /api/verifications`: registra uma afirmação e inicia a consulta em segundo plano.
- `GET /api/verifications/{id}`: consulta uma verificação pelo identificador.
- `GET /api/verifications?limit=20&status=completed`: lista as verificações recentes, opcionalmente filtradas por status.
- `POST /api/verifications/{id}/feedback`: registra feedback para uma verificação.

Exemplo da busca organizada:

```bash
curl -X POST http://127.0.0.1:8000/api/fact-check \
  -H 'Content-Type: application/json' \
  -d '{"query":"Vacina causa autismo","language_code":"pt-BR","page_size":5}'
```

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
Use obrigatoriamente a ferramenta MCP image_analysis_compare_claim_with_image para comparar a imagem /caminho/para/vacina.jpg com a afirmação "Vacina causa autismo". Leia os bytes do arquivo, envie-os em Base64 com mime_type image/jpeg e transcreva o texto legível em visible_text. Não tente identificar as pessoas da foto.
```

Também é possível fazer a solicitação pela CLI:

```bash
opencode run 'Use obrigatoriamente image_analysis_compare_claim_with_image para a imagem /caminho/para/vacina.jpg e a afirmação "Vacina causa autismo". Envie a imagem em Base64 com mime_type image/jpeg e transcreva o texto legível. Não tente identificar as pessoas.'
```

O host MCP oferece estas ferramentas:

- `analyze_image`: descreve a imagem, transcreve o texto legível em `visible_text`, estima possível manipulação visual e, opcionalmente, compara seu conteúdo com `text`.
- `search_fact_checks`: busca avaliações publicadas e aceita `query`, `language_code`, `max_age_days`, `page_size` e `page_token`.
- `summarize_fact_checks`: retorna contagem de avaliações por classificação, publicações encontradas e token para continuar a paginação. Não transforma as classificações em um veredito do sistema.
- `compare_claim_with_image`: combina as avaliações da Google Fact Check Tools API com a análise visual do OpenRouter para uma afirmação e uma imagem.

As ferramentas de imagem recebem o conteúdo como `image_base64` e `mime_type`; as ferramentas de comparação também recebem `claim`. O servidor rejeita Base64 inválido e imagens acima de 10 MiB. `visible_text` é uma transcrição automática e pode errar, especialmente em texto pequeno, desfocado ou parcialmente encoberto. Mesmo quando a busca não encontra avaliação, isso não significa que a afirmação seja verdadeira.

## Fluxo dos dados

1. O OpenCode lê `opencode.json` e inicia o processo MCP por stdio usando o Python do venv central.
2. O modelo do OpenCode recebe a solicitação do usuário e chama `image_analysis_analyze_image`, passando Base64, MIME type e, se informado, o texto a comparar.
3. `image-analysis/server.py` valida e decodifica a imagem, aplica o limite de tamanho e chama `service.analyze_image`.
4. O serviço chama `vision_client`, que cria uma data URL e envia texto mais imagem ao endpoint compatível com OpenAI do OpenRouter.
5. O OpenRouter executa o modelo definido em `OPENROUTER_MODEL` e devolve uma resposta JSON.
6. O serviço valida os campos e a faixa de confiança com Pydantic; a resposta estruturada volta pelo MCP ao OpenCode. Para buscas fact-check, o MCP usa o mesmo serviço Google do backend e retorna as avaliações publicadas sem inferir verdade quando não há resultados.

O MCP é a interface entre o OpenCode e a análise; ele não executa a inferência. Compatibilidade visual não comprova a veracidade de uma afirmação. `confidence` reflete a confiança reportada pelo modelo sobre a interpretação visual, e `possible_manipulation` não é uma avaliação forense.