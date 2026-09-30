# Fact Check Backend & Banco Vetorial

Backend desenvolvido em Python com **FastAPI** e **ChromaDB** para verificação de fake news e checagem de fatos.
O sistema combina busca semântica em **banco vetorial local** com a **Google Fact Check Tools API** em uma arquitetura de verificação híbrida.

---

## 1. Visão Geral da Arquitetura do Banco Vetorial

O subsistema de banco vetorial foi projetado para indexar, consultar e categorizar notícias e afirmações previamente verificadas por agências de checagem brasileiras (como *Lupa*, *Aos Fatos*, *Boatos.org*, *Estadão Verifica*, *AFP Checamos*, *Projeto Comprova*).

```
                            Usuário / Frontend / MCP
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │     FastAPI Backend (Rotas)   │
                       │   /api/verifications, /vector │
                       └───────────────┬───────────────┘
                                       │
                  ┌────────────────────┴──────────────────┐
                  ▼                                       ▼
    ┌───────────────────────────┐           ┌───────────────────────────┐
    │       Banco Vetorial      │           │     Google Fact Check     │
    │         (ChromaDB)        │           │         Tools API         │
    │  • HNSW Cosine Index      │           │  • Busca externa por      │
    │  • Embeddings ONNX Neural │           │    afirmação textual      │
    │  • 23.000+ Fakes/True     │           └─────────────┬─────────────┘
    └─────────────┬─────────────┘                         │
                  │                                       │
                  └────────────────────┬──────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │    Motor de Decisão Híbrido   │
                       │  Evidências + Veredito Final  │
                       └───────────────────────────────┘
```

### Principais Funcionalidades:
1. **Modelos de Embedding Flexíveis**:
   - `local_onnx`: utiliza o modelo neural `all-MiniLM-L6-v2` em formato ONNX (384 dimensões), executado 100% localmente sem necessidade de conexão externa.
   - `deterministic`: fallback baseado em feature hashing e n-gramas com normalização L2 para testes rápidos e ambientes offline restritos.
   - Suporte extensível para APIs como Google Gemini (`text-embedding-004`) e OpenRouter.
2. **Armazenamento e Indexação Vetorial**:
   - Persistência estruturada via **ChromaDB** (`PersistentClient`) armazenada em `backend/data/chroma`.
   - Indexação HNSW com métrica de similaridade de cosseno normalizada entre `0.0` e `1.0`.
   - Metadados completos por documento: `title`, `url`, `publisher_name`, `publisher_site`, `verdict` (*fake* / *true*), `date`, `origin`.
3. **Pipeline de Ingestão de Dados**:
   - Capaz de ingerir os datasets tratados da pasta `EDA/datasets/limpos/` (`fakes.csv` e `true.csv`), totalizando mais de 23.000 registros verificados.
   - Deduplicação por hash de conteúdo e controle de lote (`batch_size`).
4. **Verificação Híbrida Inteligente**:
   - Se a API do Google estiver indisponível ou retornar vazia, o sistema utiliza as evidências encontradas no banco vetorial.
   - Se ambas retornarem resultados, as evidências são agregadas e ranqueadas por similaridade.

---

## 2. Instalação e Execução

### Pré-requisitos
* Python 3.10+
* Ambiente virtual em `backend/.venv`

### Instalar Dependências
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Executar a Aplicação
```bash
uvicorn app.main:app --reload
```
Acesse a documentação interativa em: `http://localhost:8000/docs`

---

## 3. Endpoints da API Vetorial (`/api/vector`)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/vector/stats` | Retorna métricas do banco (total de docs, dimensão, provedor de embeddings, status) |
| `POST` | `/api/vector/search` | Busca semântica por similaridade de cosseno com filtros e threshold |
| `GET` | `/api/vector/search` | Busca semântica via query params (ideal para testes rápidos via URL/navegador) |
| `POST` | `/api/vector/documents` | Insere uma ou mais afirmações verificadas diretamente na coleção |
| `GET` | `/api/vector/documents/{id}` | Recupera um documento indexado pelo seu ID |
| `DELETE` | `/api/vector/documents/{id}` | Remove um documento indexado |
| `POST` | `/api/vector/ingest` | Dispara a ingestão de registros dos datasets limpos do projeto |
| `POST` | `/api/vector/reset` | Limpa e recria a coleção vetorial |

### Exemplo de Busca via cURL
```bash
curl -X POST http://localhost:8000/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vacina causa autismo em crianças",
    "top_k": 3,
    "score_threshold": 0.5,
    "verdict_filter": "fake"
  }'
```

### Exemplo de Resposta:
```json
{
  "query": "vacina causa autismo em crianças",
  "total": 1,
  "execution_time_ms": 12.4,
  "results": [
    {
      "id": "fake_8638_c91f089600a9",
      "text": "Médico espalha informações falsas sobre segurança das vacinas...",
      "similarity_score": 0.8603,
      "verdict": "fake",
      "title": "Médico espalha informações falsas sobre vacinas",
      "publisher_name": "Estadão",
      "url": "https://politica.estadao.com.br/...",
      "date": "2020-12-17 17:50:23"
    }
  ]
}
```

---

## 4. Gerenciamento via CLI

O módulo `app.vector_db.cli` oferece comandos práticos de terminal:

### Ingerir Dados do Dataset
```bash
# Ingerir 500 registros de cada dataset (fakes e true)
PYTHONPATH=. python -m app.vector_db.cli ingest --limit 500 --batch-size 100

# Ingerir todos os mais de 23.000 registros
PYTHONPATH=. python -m app.vector_db.cli ingest --limit 0 --batch-size 250 --recreate
```

### Realizar Busca Semântica
```bash
PYTHONPATH=. python -m app.vector_db.cli search "Nando Reis Rock in Rio" --top-k 3
```

### Exibir Estatísticas
```bash
PYTHONPATH=. python -m app.vector_db.cli stats
```

### Contar Documentos Indexados
```bash
PYTHONPATH=. python -m app.vector_db.cli count
```

### Limpar a Coleção
```bash
PYTHONPATH=. python -m app.vector_db.cli reset
```

---

## 5. Testes Automatizados

Para rodar todos os testes unitários e de integração do backend e do banco vetorial:

```bash
cd backend
pytest tests
```
