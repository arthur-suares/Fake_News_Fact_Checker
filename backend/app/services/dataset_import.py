"""Streaming importer for the fact-check news datasets used by the EDA."""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import News
from app.migrations import upgrade_game_round_question

REQUIRED_COLUMNS = {"title", "text", "url", "label"}
LABELS = {"1": "fake", "0": "true"}


def normalize_value(value: object) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", str(value))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def record_source_key(title: str, content: str, source_url: str) -> str:
    """Stable identity for a dataset record, independent of generated UUIDs."""
    components = [normalize_value(value) or "" for value in (title, content, source_url)]
    canonical = "\x1f".join(
        [components[0].casefold(), components[1].casefold(), components[2]]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _existing_source_keys(db: Session) -> set[str]:
    keys: set[str] = set()
    for title, content, fact_check_data in db.query(
        News.title, News.content, News.fact_check_data
    ).yield_per(1000):
        dataset = (fact_check_data or {}).get("dataset", {})
        source_key = dataset.get("source_key")
        if source_key:
            keys.add(source_key)
        else:
            source_url = dataset.get("source_url", "")
            keys.add(record_source_key(title, content, source_url))
    return keys


def import_dataset_files(
    db: Session,
    csv_paths: list[Path],
    *,
    dry_run: bool = False,
    batch_size: int = 500,
) -> dict:
    """Import news rows, one at a time, keeping only keys and one DB batch in memory."""
    report = {"read": 0, "imported": 0, "skipped": 0, "rejected": 0, "errors": []}
    source_keys = _existing_source_keys(db)
    pending = 0

    try:
        for csv_path in csv_paths:
            with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    raise ValueError(f"{csv_path}: colunas obrigatórias ausentes: {sorted(missing)}")

                for line_number, row in enumerate(reader, start=2):
                    report["read"] += 1
                    try:
                        title = normalize_value(row.get("title"))
                        content = normalize_value(row.get("text"))
                        source_url = normalize_value(row.get("url"))
                        if not title or not content or not source_url:
                            raise ValueError("title, text e url são obrigatórios")

                        source_label = normalize_value(row.get("label"))
                        if source_label not in LABELS:
                            raise ValueError(f"label inválido: {source_label!r}; esperado 0 ou 1")

                        source_key = record_source_key(title, content, source_url)
                        if source_key in source_keys:
                            report["skipped"] += 1
                            continue
                        source_keys.add(source_key)

                        if not dry_run:
                            dataset_metadata = {
                                "source_key": source_key,
                                "source_file": Path(csv_path).name,
                                "source_label": int(source_label),
                                "class": LABELS[source_label],
                                "source_url": source_url,
                                "origin": normalize_value(row.get("origin")),
                                "publisher_name": normalize_value(row.get("publisher_name")),
                                "publisher_site": normalize_value(row.get("publisher_site")),
                                "original_date": normalize_value(row.get("date")),
                                "date_source": normalize_value(row.get("date_fonte")),
                                "text_equals_title": normalize_value(row.get("text_igual_title")),
                            }
                            db.add(
                                News(
                                    title=title,
                                    content=content,
                                    image_url=None,
                                    verdict=None,
                                    fact_check_data={"dataset": dataset_metadata},
                                )
                            )
                            pending += 1
                            if pending >= batch_size:
                                db.commit()
                                pending = 0
                        report["imported"] += 1
                    except (TypeError, ValueError) as error:
                        report["rejected"] += 1
                        report["errors"].append(
                            {"file": str(csv_path), "line": line_number, "error": str(error)}
                        )

        if dry_run:
            db.rollback()
        elif pending:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return report


def _default_dataset_files(repo_root: Path) -> list[Path]:
    cleaned = repo_root / "EDA" / "datasets" / "limpos"
    originals = repo_root / "EDA" / "datasets"
    paths = [cleaned / "fakes.csv", cleaned / "true.csv"]
    if all(path.exists() for path in paths):
        return paths
    return [originals / "fakes.csv", originals / "true.csv"]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    defaults = _default_dataset_files(repo_root)
    parser = argparse.ArgumentParser(description="Importa notícias dos CSVs de checagem.")
    parser.add_argument("--fake-csv", type=Path, default=defaults[0])
    parser.add_argument("--true-csv", type=Path, default=defaults[1])
    parser.add_argument("--dry-run", action="store_true", help="Valida e reporta sem gravar.")
    args = parser.parse_args()

    if not args.dry_run:
        Base.metadata.create_all(bind=engine)
        upgrade_game_round_question(engine)
    with SessionLocal() as db:
        report = import_dataset_files(
            db,
            [args.fake_csv, args.true_csv],
            dry_run=args.dry_run,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()