from typing import Any
from pydantic import BaseModel, Field


class VectorDocumentCreate(BaseModel):
    """Schema para inserção de um documento no banco vetorial."""
    id: str | None = Field(default=None, description="Identificador único (gerado automaticamente se omitido)")
    text: str = Field(..., min_length=3, description="Texto ou afirmação principal a ser vetorizada")
    title: str | None = Field(default=None, description="Título da matéria ou verificação")
    url: str | None = Field(default=None, description="URL da fonte da verificação")
    publisher_name: str | None = Field(default=None, description="Nome da agência checadora (ex: Lupa, Aos Fatos)")
    publisher_site: str | None = Field(default=None, description="Domínio da agência checadora (ex: lupa.uol.com.br)")
    verdict: str = Field(default="fake", description="Veredito: 'fake', 'true' ou 'inconclusive'")
    date: str | None = Field(default=None, description="Data da publicação ou verificação")
    origin: str | None = Field(default=None, description="Origem da afirmação (ex: WhatsApp, Facebook, Político)")
    extra_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais livres")


class VectorSearchResult(BaseModel):
    """Resultado individual de uma busca por similaridade vetorial."""
    id: str
    text: str
    similarity_score: float = Field(..., description="Score de similaridade cosseno normalizado entre 0.0 e 1.0")
    verdict: str | None = None
    title: str | None = None
    url: str | None = None
    publisher_name: str | None = None
    publisher_site: str | None = None
    date: str | None = None
    origin: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchRequest(BaseModel):
    """Parâmetros para consulta semântica no banco vetorial."""
    query: str = Field(..., min_length=2, description="Texto da consulta a ser pesquisada semanticamente")
    top_k: int = Field(default=5, ge=1, le=50, description="Quantidade máxima de resultados a retornar")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Pontuação mínima de similaridade (0.0 a 1.0)")
    verdict_filter: str | None = Field(default=None, description="Filtrar por veredito ('fake' ou 'true')")
    publisher_filter: str | None = Field(default=None, description="Filtrar por nome da agência checadora")


class VectorSearchResponse(BaseModel):
    """Resposta estruturada da busca vetorial."""
    query: str
    total: int
    execution_time_ms: float
    results: list[VectorSearchResult]


class VectorIngestRequest(BaseModel):
    """Requisição para ingestão de datasets no banco vetorial."""
    dataset_source: str = Field(default="all", description="Fonte de dados: 'all', 'fakes', ou 'true'")
    limit: int | None = Field(default=500, description="Limite de registros a ingerir por dataset (None para todos)")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Tamanho de cada lote de inserção")
    recreate_collection: bool = Field(default=False, description="Se True, limpa a coleção antes de ingerir")


class VectorIngestResponse(BaseModel):
    """Resultado da operação de ingestão no banco vetorial."""
    status: str
    total_ingested: int
    fakes_count: int
    true_count: int
    collection_name: str
    execution_time_seconds: float
    message: str


class VectorStatsResponse(BaseModel):
    """Estatísticas e estado atual do banco vetorial."""
    status: str
    collection_name: str
    total_documents: int
    fakes_count: int | None = None
    true_count: int | None = None
    storage_path: str
    embedding_provider: str
    dimension: int
