# Banco Vetorial - Fake News Fact Checker

Módulo de armazenamento e busca vetorial semântica do projeto **Fake News Fact Checker**.
Desenvolvido com **ChromaDB**, **ONNX Runtime** e **FastAPI**, permitindo indexar e consultar afirmações e matérias verificadas por agências de checagem brasileiras (*Lupa*, *Aos Fatos*, *Boatos.org*, *Estadão Verifica*, *AFP Checamos*, *Projeto Comprova*).

---

## 1. Como Funciona

### 1.1. Arquitetura Geral

O banco vetorial atua como a memória de fatos checados da aplicação. Diferente de uma busca tradicional por palavras-chave (SQL `LIKE` ou busca exata), o banco vetorial projeta as sentenças em um espaço vetorial de **384 dimensões**, permitindo encontrar notícias com o **mesmo sentido semântico**, mesmo que escritas com vocabulário diferente ou variações sintáticas.

```
 Afirmação do Usuário
 "Nando Reis foi vaiado em festival"
                  │
                  ▼
      [ Modelo de Embedding ]
   all-MiniLM-L6-v2 (ONNX local)
                  │
                  ▼ Vetor denso (384 floats)
   [ 0.042, -0.015, ..., 0.108 ]
                  │
                  ▼ Busca de vizinhos mais próximos (HNSW)
     [ ChromaDB - Índice Cosseno ]
                  │
                  ▼ Documento mais similar (Score: 0.8595)
  "Vídeo com vaias a Nando Reis teve áudio manipulado e não foi gravado no Rock in Rio"
  Veredito: FAKE | Fonte: Lupa - UOL | URL: https://lupa.uol.com.br/...
```

### 1.2. Componentes Técnicos

- **`embeddings.py`**:
  - `LocalONNXEmbeddingFunction`: executa a inferência do modelo `all-MiniLM-L6-v2` utilizando o ONNX Runtime. O modelo fica salvo localmente em `backend/data/models/all-MiniLM-L6-v2/onnx`, permitindo execução rápida e 100% offline.
  - `DeterministicSparseEmbeddingFunction`: gerador determinístico leve baseado em n-gramas e feature hashing com normalização L2, permitindo testes unitários ultra-rápidos e execução em qualquer ambiente.
  - Interfaces plugáveis para **Google Gemini** (`text-embedding-004`) e **OpenRouter**.
- **`store.py`**:
  - Classe `VectorStore` conectada ao `chromadb.PersistentClient` apontando para `backend/data/chroma`.
  - Configurada com métrica espacial de **cosseno** (`{"hnsw:space": "cosine"}`).
  - Métodos para inserção (`add_documents`), busca aproximada com filtros (`search`), consulta por ID (`get_document_by_id`), deleção (`delete_documents`), contagem (`count`) e reset (`reset`).
- **`schemas.py`**:
  - Modelos Pydantic para validação estrita de dados de entrada e saída.
- **`ingest.py`**:
  - Rotina de ingestão e normalização a partir dos arquivos CSV limpos (`EDA/datasets/limpos/fakes.csv` e `true.csv`), que somam mais de 23.000 afirmações verificadas.
- **`cli.py`**:
  - Interface CLI amigável para administração via terminal.
- **`app/services/vector_service.py`**:
  - Camada de serviço de alto nível para consumo do banco vetorial pela lógica de negócios.
- **`app/services/verification.py`**:
  - Motor de checagem híbrida: combina as evidências do banco vetorial com a Google Fact Check API.

---

## 2. Como Operacionalizar

### 2.1. Pré-requisitos e Ambiente

Certifique-se de estar com o ambiente virtual Python ativado:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 2.2. Operações via Linha de Comando (CLI)

O arquivo `app/vector_db/cli.py` fornece comandos para gerenciar o banco:

#### 1. Ingerir dados dos Datasets
```bash
# Ingerir 500 registros de cada dataset (total ~1000 registros):
PYTHONPATH=backend python -m app.vector_db.cli ingest --limit 500 --batch-size 100

# Ingerir apenas fake news:
PYTHONPATH=backend python -m app.vector_db.cli ingest --limit 200 --source fakes

# Ingerir apenas notícias verdadeiras:
PYTHONPATH=backend python -m app.vector_db.cli ingest --limit 200 --source true

# Ingerir a base COMPLETA (mais de 23.000 registros) recriando a coleção:
PYTHONPATH=backend python -m app.vector_db.cli ingest --limit 0 --batch-size 250 --recreate
```

#### 2. Consultar o total de registros indexados
```bash
PYTHONPATH=backend python -m app.vector_db.cli count
```

#### 3. Exibir estatísticas e saúde do banco
```bash
PYTHONPATH=backend python -m app.vector_db.cli stats
```
Exemplo de retorno:
```json
{
  "status": "ready",
  "collection_name": "fact_checks",
  "total_documents": 200,
  "storage_path": "/Users/aluno1/Fake_News_Fact_Checker/backend/data/chroma",
  "embedding_provider": "local_onnx",
  "dimension": 384
}
```

#### 4. Realizar buscas semânticas pelo terminal
```bash
# Busca geral
PYTHONPATH=backend python -m app.vector_db.cli search "Nando Reis Rock in Rio" --top-k 3

# Busca filtrando apenas por fake news
PYTHONPATH=backend python -m app.vector_db.cli search "vacina causa autismo" --verdict fake --top-k 3

# Busca com score mínimo de corte (ex: similaridade >= 0.60)
PYTHONPATH=backend python -m app.vector_db.cli search "gasolina diesel impostos" --threshold 0.60
```

#### 5. Limpar / Resetar a coleção
```bash
PYTHONPATH=backend python -m app.vector_db.cli reset
```

---

### 2.3. Operações via API REST (FastAPI)

Inicie o servidor backend:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```
Acesse a documentação interativa Swagger em: `http://localhost:8000/docs`

#### Endpoints Disponíveis:

| Rota | Método | Função |
|---|---|---|
| `/api/vector/stats` | `GET` | Retorna status, contagem de documentos, dimensão e provedor. |
| `/api/vector/search` | `POST` | Busca semântica estruturada com filtros (`verdict_filter`, `publisher_filter`, `score_threshold`). |
| `/api/vector/search` | `GET` | Busca semântica rápida via query parameters. |
| `/api/vector/documents` | `POST` | Indexa manualmente novos fatos checados (único ou em lote). |
| `/api/vector/documents/{id}` | `GET` | Busca documento por ID. |
| `/api/vector/documents/{id}` | `DELETE` | Remove documento da base. |
| `/api/vector/ingest` | `POST` | Dispara a ingestão de registros via requisição HTTP. |
| `/api/vector/reset` | `POST` | Reseta a coleção vetorial. |

#### Exemplo: Busca Semântica via cURL
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

#### Exemplo: Inserir Nova Verificação via cURL
```bash
curl -X POST http://localhost:8000/api/vector/documents \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Nova vacina contra gripe contém microchip 5G",
    "title": "É falso que vacina contra gripe contém microchip",
    "publisher_name": "Aos Fatos",
    "publisher_site": "aosfatos.org",
    "url": "https://aosfatos.org/noticias/falso-chip-vacina",
    "verdict": "fake",
    "origin": "WhatsApp"
  }'
```

---

### 2.4. Como Funciona a Verificação Híbrida (`/api/verifications`)

Quando um usuário ou frontend envia uma notícia para checagem em `POST /api/verifications`:

1. O backend inicia a tarefa assíncrona em background.
2. Consulta o **Banco Vetorial** para verificar se a afirmação é similar a algum caso já apurado por agências brasileiras.
3. Consulta a **Google Fact Check Tools API** (caso configurada).
4. As evidências do banco vetorial são formatadas e anexadas ao objeto da verificação.
5. Se a similaridade for alta ($\ge 0.55$), o veredito final (`false` ou `true`) é atribuído automaticamente e as fontes oficiais são retornadas.

---

### 2.5. Executar os Testes Automatizados

Para rodar a suíte completa de testes unitários e de integração do banco vetorial:

```bash
cd backend
source .venv/bin/activate
pytest tests -v
```
