from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Garante inclusão do diretório backend no PYTHONPATH
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.vector_db.ingest import run_ingestion
from app.vector_db.store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vector_db_cli")


def get_default_store() -> VectorStore:
    return VectorStore()


def handle_ingest(args: argparse.Namespace) -> None:
    store = get_default_store()
    limit = None if args.limit == 0 or args.limit is None else args.limit
    logger.info(
        "Iniciando ingestão de dados (limit=%s, batch_size=%d, source=%s, recreate=%s)...",
        limit,
        args.batch_size,
        args.source,
        args.recreate,
    )
    result = run_ingestion(
        store=store,
        limit=limit,
        batch_size=args.batch_size,
        recreate_collection=args.recreate,
        dataset_source=args.source,
    )
    print("\n" + "=" * 60)
    print("STATUS DA INGESTÃO:")
    print(f"Total indexado : {result.total_ingested}")
    print(f"Fakes          : {result.fakes_count}")
    print(f"Verdadeiras    : {result.true_count}")
    print(f"Tempo          : {result.execution_time_seconds}s")
    print(f"Coleção        : {result.collection_name}")
    print(f"Total no banco : {store.count()}")
    print("=" * 60)


def handle_search(args: argparse.Namespace) -> None:
    store = get_default_store()
    results = store.search(
        query=args.query,
        top_k=args.top_k,
        score_threshold=args.threshold,
        verdict_filter=args.verdict,
        publisher_filter=args.publisher,
    )
    print("\n" + "=" * 70)
    print(f"BUSCA VETORIAL: '{args.query}' (Resultados: {len(results)})")
    print("=" * 70)
    for idx, r in enumerate(results, 1):
        print(f"\n[{idx}] Score: {r.similarity_score:.4f} | Veredito: {r.verdict.upper() if r.verdict else 'N/A'}")
        print(f"     Título: {r.title or 'Sem título'}")
        print(f"     Fonte : {r.publisher_name or 'Desconhecida'} ({r.publisher_site or 'N/A'})")
        print(f"     URL   : {r.url or 'N/A'}")
        print(f"     Texto : {r.text[:140]}...")
    print("=" * 70)


def handle_stats(_args: argparse.Namespace) -> None:
    store = get_default_store()
    stats = store.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def handle_count(_args: argparse.Namespace) -> None:
    store = get_default_store()
    print(f"Total de documentos indexados: {store.count()}")


def handle_reset(_args: argparse.Namespace) -> None:
    store = get_default_store()
    store.reset()
    print("Coleção vetorial resetada com sucesso.")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI para gerenciamento do Banco Vetorial")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingere notícias dos datasets CSV para o banco vetorial")
    ingest_parser.add_argument("--limit", type=int, default=500, help="Limite de registros por CSV (0 ou omitir para todos)")
    ingest_parser.add_argument("--batch-size", type=int, default=100, help="Tamanho dos lotes de inserção")
    ingest_parser.add_argument("--source", type=str, default="all", choices=["all", "fakes", "true"], help="Fonte de dados")
    ingest_parser.add_argument("--recreate", action="store_true", help="Recria a coleção antes de ingerir")

    # Search
    search_parser = subparsers.add_parser("search", help="Busca semântica no banco vetorial")
    search_parser.add_argument("query", type=str, help="Texto da afirmação ou notícia")
    search_parser.add_argument("--top-k", type=int, default=5, help="Quantidade máxima de resultados")
    search_parser.add_argument("--threshold", type=float, default=0.0, help="Score mínimo de corte (0.0 a 1.0)")
    search_parser.add_argument("--verdict", type=str, default=None, choices=["fake", "true"], help="Filtrar por veredito")
    search_parser.add_argument("--publisher", type=str, default=None, help="Filtrar por agência checadora")

    # Stats
    subparsers.add_parser("stats", help="Exibe estatísticas do banco vetorial")

    # Count
    subparsers.add_parser("count", help="Exibe o número de documentos indexados")

    # Reset
    subparsers.add_parser("reset", help="Limpa todos os documentos da coleção")

    args = parser.parse_args()

    handlers = {
        "ingest": handle_ingest,
        "search": handle_search,
        "stats": handle_stats,
        "count": handle_count,
        "reset": handle_reset,
    }

    handlers[args.command](args)


if __name__ == "__main__":
    main()
