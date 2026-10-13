import csv
import json
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.migrations import upgrade_game_round_question
from app.models import News, Question
from app.services.dataset_import import import_dataset_files, record_source_key
from app.services.question_import import import_question_jsonl
from seed import seed_skills


def _write_dataset(path: Path, rows: list[dict]) -> Path:
    fields = ["title", "text", "origin", "url", "label", "publisher_name", "publisher_site", "date"]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_dataset_import_maps_labels_and_is_idempotent(db_session, tmp_path):
    csv_path = _write_dataset(
        tmp_path / "news.csv",
        [
            {"title": "Claim A", "text": "Content with enough detail", "origin": "Facebook", "url": "https://example.test/a", "label": 1, "publisher_name": "Checker", "publisher_site": "checker.test", "date": "2024-01-01"},
            {"title": "Claim B", "text": "Another checked statement", "origin": "Politician", "url": "https://example.test/b", "label": 0, "publisher_name": "Checker", "publisher_site": "checker.test", "date": "2024-01-02"},
            {"title": "Missing claim", "text": "", "origin": "", "url": "https://example.test/c", "label": 1, "publisher_name": "", "publisher_site": "", "date": ""},
        ],
    )

    dry_run = import_dataset_files(db_session, [csv_path], dry_run=True)
    assert dry_run["imported"] == 2
    assert dry_run["rejected"] == 1
    assert db_session.query(News).count() == 0

    imported = import_dataset_files(db_session, [csv_path])
    assert imported["imported"] == 2
    assert imported["rejected"] == 1
    metadata = [news.fact_check_data["dataset"] for news in db_session.query(News).all()]
    assert {entry["class"] for entry in metadata} == {"fake", "true"}
    assert all(news.verdict is None for news in db_session.query(News).all())

    rerun = import_dataset_files(db_session, [csv_path])
    assert rerun["imported"] == 0
    assert rerun["skipped"] == 2
    assert db_session.query(News).count() == 2


def test_question_import_requires_review_valid_answer_and_is_idempotent(db_session, tmp_path):
    seed_skills(db_session)
    title = "Reviewed news"
    content = "A checked statement with context"
    source_url = "https://example.test/reviewed"
    source_key = record_source_key(title, content, source_url)
    news = News(
        title=title,
        content=content,
        fact_check_data={"dataset": {"source_key": source_key, "origin": "A public post"}},
    )
    db_session.add(news)
    db_session.commit()
    record = {
        "news_source_key": source_key,
        "skill_code": "SOURCE",
        "reviewed": True,
        "text": "What makes the origin verifiable?",
        "difficulty": 0.4,
        "options": {"A": "An identified publisher", "B": "The number of shares"},
        "correct_option": "A",
        "explanation": "The source is identified in the supplied record.",
    }
    jsonl_path = tmp_path / "questions.jsonl"
    jsonl_path.write_text(json.dumps(record) + "\n" + json.dumps(record), encoding="utf-8")

    first = import_question_jsonl(db_session, jsonl_path)
    second = import_question_jsonl(db_session, jsonl_path)

    assert first["imported"] == 1
    assert first["skipped"] == 1
    assert second["imported"] == 0
    assert second["skipped"] == 2
    assert db_session.query(Question).filter_by(news_id=news.id).count() == 1


def test_question_import_rejects_unreviewed_and_visual_without_image(db_session, tmp_path):
    seed_skills(db_session)
    title, content, source_url = "No image", "A statement with enough content", "https://example.test/no-image"
    source_key = record_source_key(title, content, source_url)
    db_session.add(
        News(title=title, content=content, fact_check_data={"dataset": {"source_key": source_key}})
    )
    db_session.commit()
    record = {
        "news_source_key": source_key,
        "skill_code": "VISUAL",
        "reviewed": True,
        "text": "Does the image match?",
        "difficulty": 0.5,
        "options": {"A": "Yes", "B": "No"},
        "correct_option": "B",
        "explanation": "No image is available.",
    }
    jsonl_path = tmp_path / "invalid.jsonl"
    jsonl_path.write_text(json.dumps(record), encoding="utf-8")

    report = import_question_jsonl(db_session, jsonl_path)

    assert report["rejected"] == 1
    assert db_session.query(Question).count() == 0


def test_game_round_question_migration_is_idempotent_and_backfills_existing_answers():
    migration_engine = create_engine("sqlite://")
    with migration_engine.begin() as connection:
        connection.execute(text("CREATE TABLE questions (id TEXT PRIMARY KEY, news_id TEXT NOT NULL)"))
        connection.execute(text("CREATE TABLE game_rounds (id TEXT PRIMARY KEY, game_id TEXT NOT NULL, news_id TEXT NOT NULL, round_number INTEGER NOT NULL)"))
        connection.execute(text("CREATE TABLE answers (id TEXT PRIMARY KEY, game_round_id TEXT, question_id TEXT, created_at TEXT)"))
        connection.execute(text("INSERT INTO questions (id, news_id) VALUES ('q1', 'n1'), ('q2', 'n2')"))
        connection.execute(text("INSERT INTO game_rounds (id, game_id, news_id, round_number) VALUES ('r1', 'g1', 'n1', 1), ('r2', 'g1', 'n2', 2)"))
        connection.execute(text("INSERT INTO answers (id, game_round_id, question_id, created_at) VALUES ('a1', 'r1', 'q1', '2025-01-01')"))

    upgrade_game_round_question(migration_engine)
    upgrade_game_round_question(migration_engine)

    with migration_engine.connect() as connection:
        values = connection.execute(text("SELECT id, question_id FROM game_rounds ORDER BY id")).all()
    assert values == [("r1", "q1"), ("r2", "q2")]
    assert "question_id" in {column["name"] for column in inspect(migration_engine).get_columns("game_rounds")}
    indexes = inspect(migration_engine).get_indexes("game_rounds")
    assert any(index["name"] == "uq_game_round_number" and index["unique"] for index in indexes)
    with migration_engine.begin() as connection:
        try:
            connection.execute(
                text(
                    "INSERT INTO game_rounds "
                    "(id, game_id, news_id, round_number, question_id) "
                    "VALUES ('r3', 'g1', 'n1', 1, 'q1')"
                )
            )
        except IntegrityError:
            pass
        else:
            raise AssertionError("duplicate game round number should be rejected")
    migration_engine.dispose()