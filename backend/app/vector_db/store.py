from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings
from app.vector_db.embeddings import BaseEmbeddingFunction, get_embedding_function
from app.vector_db.schemas import VectorDocumentCreate, VectorSearchResult

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Gerenciador de armazenamento vetorial baseado em ChromaDB.
    Permite indexação persistente, busca semântica aproximada (HNSW + Cosseno),
    filtragem por metadados e gerenciamento de coleções.
    """

    def __init__(
        self,
        storage_path: str | None = None,
        collection_name: str | None = None,
        embedding_function: BaseEmbeddingFunction | None = None,
    ) -> None:
        self.storage_path = os.path.abspath(
            storage_path or getattr(settings, "vector_db_path", "./data/chroma")
        )
        self.collection_name = collection_name or getattr(settings, "vector_db_collection", "fact_checks")
        os.makedirs(self.storage_path, exist_ok=True)

        self.embedding_function = embedding_function or get_embedding_function(
            provider=getattr(settings, "vector_db_embedding_provider", "auto"),
            model_dir=getattr(settings, "vector_db_model_dir", None),
            api_key=getattr(settings, "google_fact_check_api_key", None),
        )

        self.client = chromadb.PersistentClient(path=self.storage_path)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> Collection:
        """Cria ou recupera a coleção configurada com distância cosseno."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
        """ChromaDB aceita apenas str, int, float, bool em metadados."""
        sanitized: dict[str, str | int | float | bool] = {}
        for key, value in meta.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    def add_documents(self, documents: list[VectorDocumentCreate]) -> list[str]:
        """
        Insere ou atualiza documentos no banco vetorial com metadados estruturados.
        Gera IDs únicos se não forem fornecidos.
        """
        if not documents:
            return []

        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict[str, str | int | float | bool]] = []

        for doc in documents:
            doc_id = doc.id or f"doc_{uuid.uuid4().hex[:12]}"
            ids.append(doc_id)
            texts.append(doc.text.strip())

            raw_meta: dict[str, Any] = {
                "verdict": doc.verdict.strip().lower(),
                "title": doc.title or "",
                "url": doc.url or "",
                "publisher_name": doc.publisher_name or "",
                "publisher_site": doc.publisher_site or "",
                "date": doc.date or "",
                "origin": doc.origin or "",
            }
            if doc.extra_metadata:
                raw_meta.update(doc.extra_metadata)

            metadatas.append(self._sanitize_metadata(raw_meta))

        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info("Adicionados/atualizados %d documentos na coleção '%s'", len(ids), self.collection_name)
        return ids

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        verdict_filter: str | None = None,
        publisher_filter: str | None = None,
    ) -> list[VectorSearchResult]:
        """
        Executa busca por similaridade de cosseno com ranking e filtragem opcional.
        Retorna resultados com score de similaridade normalizado entre 0.0 e 1.0.
        """
        total_in_collection = self.collection.count()
        if total_in_collection == 0:
            return []

        # Construir filtro de metadados
        conditions: list[dict[str, Any]] = []
        if verdict_filter:
            conditions.append({"verdict": verdict_filter.strip().lower()})
        if publisher_filter:
            conditions.append({"publisher_name": publisher_filter.strip()})

        where_clause: dict[str, Any] | None = None
        if len(conditions) == 1:
            where_clause = conditions[0]
        elif len(conditions) > 1:
            where_clause = {"$and": conditions}

        actual_k = min(max(1, top_k), total_in_collection)

        query_kwargs: dict[str, Any] = {
            "query_texts": [query.strip()],
            "n_results": actual_k,
        }
        if where_clause:
            query_kwargs["where"] = where_clause

        try:
            results = self.collection.query(**query_kwargs)
        except Exception as exc:
            logger.error("Erro ao consultar coleção vetorial: %s", exc)
            return []

        ids_list = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        search_results: list[VectorSearchResult] = []
        for doc_id, dist, doc_text, meta in zip(ids_list, distances, documents, metadatas):
            # Para distância cosseno no Chroma, dist = 1 - sim => sim = 1 - dist
            # Garantir intervalo [0.0, 1.0]
            similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)

            if similarity < score_threshold:
                continue

            meta_dict = dict(meta) if meta else {}
            search_results.append(
                VectorSearchResult(
                    id=doc_id,
                    text=doc_text,
                    similarity_score=similarity,
                    verdict=meta_dict.get("verdict"),
                    title=meta_dict.get("title"),
                    url=meta_dict.get("url"),
                    publisher_name=meta_dict.get("publisher_name"),
                    publisher_site=meta_dict.get("publisher_site"),
                    date=meta_dict.get("date"),
                    origin=meta_dict.get("origin"),
                    metadata=meta_dict,
                )
            )

        # Ordenar por similaridade decrescente
        search_results.sort(key=lambda r: r.similarity_score, reverse=True)
        return search_results

    def get_document_by_id(self, doc_id: str) -> VectorSearchResult | None:
        """Recupera um documento específico pelo ID."""
        try:
            data = self.collection.get(ids=[doc_id])
            ids = data.get("ids", [])
            if not ids:
                return None

            doc_text = data.get("documents", [""])[0]
            meta = data.get("metadatas", [{}])[0] or {}

            return VectorSearchResult(
                id=doc_id,
                text=doc_text,
                similarity_score=1.0,
                verdict=meta.get("verdict"),
                title=meta.get("title"),
                url=meta.get("url"),
                publisher_name=meta.get("publisher_name"),
                publisher_site=meta.get("publisher_site"),
                date=meta.get("date"),
                origin=meta.get("origin"),
                metadata=dict(meta),
            )
        except Exception as exc:
            logger.error("Erro ao buscar documento '%s': %s", doc_id, exc)
            return None

    def delete_documents(self, doc_ids: list[str]) -> int:
        """Remove documentos da coleção pelo ID."""
        if not doc_ids:
            return 0
        try:
            self.collection.delete(ids=doc_ids)
            logger.info("Removidos %d documentos da coleção", len(doc_ids))
            return len(doc_ids)
        except Exception as exc:
            logger.error("Erro ao remover documentos: %s", exc)
            return 0

    def count(self) -> int:
        """Retorna o número total de documentos na coleção."""
        return self.collection.count()

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas detalhadas da coleção vetorial."""
        total = self.collection.count()
        return {
            "status": "ready",
            "collection_name": self.collection_name,
            "total_documents": total,
            "storage_path": self.storage_path,
            "embedding_provider": getattr(self.embedding_function, "name", lambda: "unknown")(),
            "dimension": getattr(self.embedding_function, "dimension", 384),
        }

    def reset(self) -> None:
        """Limpa e reinicializa a coleção."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self._get_or_create_collection()
        logger.info("Coleção '%s' reinicializada.", self.collection_name)
