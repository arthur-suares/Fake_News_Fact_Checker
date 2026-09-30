from __future__ import annotations

import time
from typing import Union

from fastapi import APIRouter, HTTPException, Query, status

from app.services.vector_service import get_vector_store
from app.vector_db.ingest import run_ingestion
from app.vector_db.schemas import (
    VectorDocumentCreate,
    VectorIngestRequest,
    VectorIngestResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
    VectorStatsResponse,
)

router = APIRouter(prefix="/api/vector", tags=["vector_database"])


@router.get("/stats", response_model=VectorStatsResponse)
def get_vector_stats():
    """Retorna as métricas e o status do banco vetorial."""
    store = get_vector_store()
    stats = store.get_stats()
    return VectorStatsResponse(**stats)


@router.post("/search", response_model=VectorSearchResponse)
def search_vector_post(payload: VectorSearchRequest):
    """Executa busca semântica por similaridade via POST."""
    start_time = time.perf_counter()
    store = get_vector_store()

    results = store.search(
        query=payload.query,
        top_k=payload.top_k,
        score_threshold=payload.score_threshold,
        verdict_filter=payload.verdict_filter,
        publisher_filter=payload.publisher_filter,
    )

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    return VectorSearchResponse(
        query=payload.query,
        total=len(results),
        execution_time_ms=elapsed_ms,
        results=results,
    )


@router.get("/search", response_model=VectorSearchResponse)
def search_vector_get(
    query: str = Query(..., min_length=2, description="Texto ou afirmação para consulta semântica"),
    top_k: int = Query(5, ge=1, le=50, description="Quantidade de resultados"),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="Score mínimo de corte (0.0 a 1.0)"),
    verdict: str | None = Query(None, description="Filtro por veredito ('fake' ou 'true')"),
    publisher: str | None = Query(None, description="Filtro por agência checadora"),
):
    """Executa busca semântica por similaridade via GET (para consultas rápidas e testes via browser)."""
    return search_vector_post(
        VectorSearchRequest(
            query=query,
            top_k=top_k,
            score_threshold=threshold,
            verdict_filter=verdict,
            publisher_filter=publisher,
        )
    )


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def add_documents(payload: Union[VectorDocumentCreate, list[VectorDocumentCreate]]):
    """Adiciona um ou mais documentos verificados ao banco vetorial."""
    store = get_vector_store()
    docs = payload if isinstance(payload, list) else [payload]
    inserted_ids = store.add_documents(docs)
    return {
        "status": "success",
        "inserted_count": len(inserted_ids),
        "ids": inserted_ids,
    }


@router.get("/documents/{doc_id}", response_model=VectorSearchResult)
def get_document(doc_id: str):
    """Recupera um documento específico pelo ID."""
    store = get_vector_store()
    doc = store.get_document_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado no banco vetorial")
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Remove um documento do banco vetorial pelo ID."""
    store = get_vector_store()
    deleted = store.delete_documents([doc_id])
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Documento não encontrado para remoção")
    return {"status": "success", "message": f"Documento '{doc_id}' removido com sucesso."}


@router.post("/ingest", response_model=VectorIngestResponse)
def ingest_datasets(payload: VectorIngestRequest = VectorIngestRequest()):
    """Aciona a ingestão dos datasets limpos do projeto no banco vetorial."""
    store = get_vector_store()
    response = run_ingestion(
        store=store,
        limit=payload.limit,
        batch_size=payload.batch_size,
        recreate_collection=payload.recreate_collection,
        dataset_source=payload.dataset_source,
    )
    return response


@router.post("/reset")
def reset_collection():
    """Limpa e recria a coleção vetorial."""
    store = get_vector_store()
    store.reset()
    return {"status": "success", "message": f"Coleção '{store.collection_name}' limpa com sucesso."}
