from __future__ import annotations

import csv
import hashlib
import logging
import os
import time
from pathlib import Path

from app.vector_db.schemas import VectorDocumentCreate, VectorIngestResponse
from app.vector_db.store import VectorStore

logger = logging.getLogger(__name__)


def get_default_dataset_paths() -> tuple[Path | None, Path | None]:
    """Localiza os arquivos CSV de datasets limpos (fakes.csv e true.csv)."""
    current_file = Path(__file__).resolve()
    # Tenta caminhos a partir do backend ou raiz do projeto
    candidates = [
        current_file.parents[3] / "EDA" / "datasets" / "limpos",
        current_file.parents[2] / "EDA" / "datasets" / "limpos",
        Path.cwd() / "EDA" / "datasets" / "limpos",
        Path.cwd().parent / "EDA" / "datasets" / "limpos",
    ]

    for base_dir in candidates:
        fakes_file = base_dir / "fakes.csv"
        true_file = base_dir / "true.csv"
        if fakes_file.exists() and true_file.exists():
            return fakes_file, true_file

    return None, None


def generate_doc_id(prefix: str, url: str, text: str, index: int) -> str:
    """Gera um ID único e determinístico para o documento."""
    content_hash = hashlib.sha256(f"{url}_{text}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{index}_{content_hash}"


def ingest_csv_file(
    file_path: Path,
    verdict: str,
    store: VectorStore,
    limit: int | None = None,
    batch_size: int = 100,
) -> int:
    """
    Lê um arquivo CSV de notícias verificadas e o indexa em lotes no banco vetorial.
    """
    if not file_path.exists():
        logger.warning("Arquivo de dataset não encontrado: %s", file_path)
        return 0

    prefix = "fake" if verdict == "fake" else "true"
    batch: list[VectorDocumentCreate] = []
    total_ingested = 0
    seen_texts: set[str] = set()

    with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if limit is not None and total_ingested >= limit:
                break

            # Determina o texto a ser vetorizado: prefere 'text' ou 'title'
            text = (row.get("text") or "").strip()
            title = (row.get("title") or "").strip()
            if not text or len(text) < 5:
                text = title
            if not text or len(text) < 5:
                continue

            # Evita duplicatas exatas dentro do mesmo lote de leitura
            norm_key = text.lower()[:200]
            if norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)

            doc_id = generate_doc_id(prefix, row.get("url", ""), text, idx)
            doc = VectorDocumentCreate(
                id=doc_id,
                text=text,
                title=title,
                url=(row.get("url") or "").strip(),
                publisher_name=(row.get("publisher_name") or "").strip(),
                publisher_site=(row.get("publisher_site") or "").strip(),
                verdict=verdict,
                date=(row.get("date") or "").strip(),
                origin=(row.get("origin") or "").strip(),
                extra_metadata={
                    "text_igual_title": row.get("text_igual_title", "False"),
                    "date_fonte": row.get("date_fonte", ""),
                },
            )
            batch.append(doc)

            if len(batch) >= batch_size:
                store.add_documents(batch)
                total_ingested += len(batch)
                logger.info("Ingeridos %d registros de %s...", total_ingested, file_path.name)
                batch = []

        if batch:
            store.add_documents(batch)
            total_ingested += len(batch)

    logger.info("Finalizada ingestão de %s: %d documentos indexados.", file_path.name, total_ingested)
    return total_ingested


def run_ingestion(
    store: VectorStore,
    limit: int | None = 500,
    batch_size: int = 100,
    recreate_collection: bool = False,
    dataset_source: str = "all",
    fakes_path: str | Path | None = None,
    true_path: str | Path | None = None,
) -> VectorIngestResponse:
    """
    Executa a rotina completa de ingestão de dados para o banco vetorial.
    """
    start_time = time.time()

    if recreate_collection:
        logger.info("Reinicializando a coleção vetorial antes da ingestão...")
        store.reset()

    default_fakes, default_true = get_default_dataset_paths()
    path_fakes = Path(fakes_path) if fakes_path else default_fakes
    path_true = Path(true_path) if true_path else default_true

    fakes_count = 0
    true_count = 0

    source = (dataset_source or "all").lower().strip()

    if source in ("all", "fakes") and path_fakes:
        fakes_count = ingest_csv_file(
            file_path=path_fakes,
            verdict="fake",
            store=store,
            limit=limit,
            batch_size=batch_size,
        )

    if source in ("all", "true") and path_true:
        true_count = ingest_csv_file(
            file_path=path_true,
            verdict="true",
            store=store,
            limit=limit,
            batch_size=batch_size,
        )

    duration = round(time.time() - start_time, 2)
    total = fakes_count + true_count

    return VectorIngestResponse(
        status="success",
        total_ingested=total,
        fakes_count=fakes_count,
        true_count=true_count,
        collection_name=store.collection_name,
        execution_time_seconds=duration,
        message=f"Ingestão concluída: {total} documentos indexados ({fakes_count} fakes, {true_count} verdadeiras) em {duration}s.",
    )
