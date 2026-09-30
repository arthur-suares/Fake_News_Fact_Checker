from __future__ import annotations

import logging
from typing import Any

from app.vector_db.schemas import VectorDocumentCreate, VectorSearchResult
from app.vector_db.store import VectorStore

logger = logging.getLogger(__name__)

_store_instance: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Retorna uma instância singleton do VectorStore."""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance


def set_vector_store(store: VectorStore | None) -> None:
    """Permite sobrescrever a instância (útil para testes unitários com mocks/test stores)."""
    global _store_instance
    _store_instance = store


class VectorFactCheckService:
    """
    Serviço de alto nível para checagem de fatos via busca semântica no banco vetorial.
    Consome o histórico curado de verificações (Lupa, Aos Fatos, Boatos.org, Estadão, etc.).
    """

    @classmethod
    def search_similar_claims(
        cls,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        verdict_filter: str | None = None,
        publisher_filter: str | None = None,
    ) -> list[VectorSearchResult]:
        store = get_vector_store()
        return store.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            verdict_filter=verdict_filter,
            publisher_filter=publisher_filter,
        )

    @classmethod
    def verify_claim(
        cls,
        query: str,
        top_k: int = 5,
        min_confidence: float = 0.60,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Consulta o banco vetorial para identificar se a afirmação já foi verificada.
        Retorna (veredicto, lista_de_evidencias_formatadas).
        """
        matches = cls.search_similar_claims(
            query=query,
            top_k=top_k,
            score_threshold=min_confidence,
        )

        if not matches:
            return None, []

        evidences: list[dict[str, Any]] = []
        for match in matches:
            pub = match.publisher_name or "Base Vetorial de Checagens"
            evidences.append({
                "source": f"{pub} (Banco Vetorial)",
                "rating": match.verdict or "não verificado",
                "url": match.url or "",
                "title": match.title or match.text,
                "similarity_score": match.similarity_score,
            })

        best_match = matches[0]
        verdict: str | None = best_match.verdict
        return verdict, evidences

    @classmethod
    def index_fact_check(
        cls,
        text: str,
        verdict: str,
        title: str | None = None,
        publisher: str | None = None,
        publisher_site: str | None = None,
        url: str | None = None,
        origin: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> str:
        """Adiciona uma nova verificação ao banco vetorial."""
        store = get_vector_store()
        doc = VectorDocumentCreate(
            text=text,
            title=title or text,
            publisher_name=publisher,
            publisher_site=publisher_site,
            url=url,
            verdict=verdict,
            origin=origin,
            extra_metadata=extra_metadata or {},
        )
        ids = store.add_documents([doc])
        return ids[0]
