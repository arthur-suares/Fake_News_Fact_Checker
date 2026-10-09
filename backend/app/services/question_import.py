"""Import manually reviewed game questions associated with imported news."""

import argparse
import json
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.bkt.manager import BKTManager
from app.database import Base, SessionLocal, engine
from app.migrations import upgrade_game_round_question
from app.models import News, Question, Skill
from app.services.dataset_import import normalize_value
from seed import seed_skills


def validate_question_record(record: dict, news: News, skills_by_code: dict[str, Skill]) -> tuple[Skill, dict]:
    if record.get("reviewed") is not True:
        raise ValueError("questão precisa ter reviewed=true após revisão humana")

    skill_code = normalize_value(record.get("skill_code"))
    if not skill_code or not BKTManager.validate_skill_code(skill_code.upper()):
        raise ValueError(f"skill_code inválido: {skill_code!r}")
    skill = skills_by_code.get(skill_code.upper())
    if not skill:
        raise ValueError(f"skill {skill_code} não existe no banco; inicialize as skills")

    text = normalize_value(record.get("text"))
    explanation = normalize_value(record.get("explanation"))
    if not text or not explanation:
        raise ValueError("enunciado e explicação são obrigatórios")

    options = record.get("options")
    if not isinstance(options, dict) or len(options) < 2:
        raise ValueError("options deve ser um objeto com pelo menos duas alternativas")
    normalized_options = {}
    for option, option_text in options.items():
        label = normalize_value(option)
        value = normalize_value(option_text)
        if not label or not value:
            raise ValueError("rótulos e textos das alternativas não podem ser vazios")
        normalized_options[label] = value

    correct_option = normalize_value(record.get("correct_option"))
    if correct_option not in normalized_options:
        raise ValueError("correct_option deve corresponder a uma alternativa existente")

    difficulty = record.get("difficulty")
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)) or not 0 <= difficulty <= 1:
        raise ValueError("difficulty deve ser um número entre 0 e 1")

    dataset = (news.fact_check_data or {}).get("dataset", {})
    if skill.code == "VISUAL" and not news.image_url:
        raise ValueError("questões VISUAL exigem image_url disponível na notícia")
    if skill.code == "SOURCE" and not any(
        dataset.get(field) for field in ("origin", "publisher_name", "publisher_site")
    ):
        raise ValueError("questões SOURCE exigem origem ou publicador documentado")
    if len((news.content or "").split()) < 3:
        raise ValueError("notícia sem conteúdo suficiente para sustentar uma questão")

    return skill, {
        "text": text,
        "explanation": explanation,
        "options": normalized_options,
        "correct_option": correct_option,
        "difficulty": float(difficulty),
    }


def import_question_jsonl(db: Session, jsonl_path: Path, *, dry_run: bool = False) -> dict:
    news_by_key = {}
    for news in db.query(News).yield_per(1000):
        dataset = (news.fact_check_data or {}).get("dataset", {})
        source_key = dataset.get("source_key")
        if source_key:
            news_by_key[source_key] = news

    skills_by_code = {skill.code: skill for skill in db.query(Skill).all()}
    existing = {
        (question.news_id, question.skill_id, (normalize_value(question.text) or "").casefold())
        for question in db.query(Question).all()
    }
    report = {"read": 0, "imported": 0, "skipped": 0, "rejected": 0, "errors": []}

    try:
        with Path(jsonl_path).open("r", encoding="utf-8-sig") as source_file:
            for line_number, line in enumerate(source_file, start=1):
                if not line.strip():
                    continue
                report["read"] += 1
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError("cada linha deve conter um objeto JSON")
                    source_key = normalize_value(record.get("news_source_key"))
                    news = news_by_key.get(source_key)
                    if news is None:
                        raise ValueError("news_source_key não encontrada nas notícias importadas")

                    skill, question_data = validate_question_record(record, news, skills_by_code)
                    signature = (news.id, skill.id, question_data["text"].casefold())
                    if signature in existing:
                        report["skipped"] += 1
                        continue
                    existing.add(signature)

                    if not dry_run:
                        db.add(
                            Question(
                                news_id=news.id,
                                skill_id=skill.id,
                                **question_data,
                            )
                        )
                    report["imported"] += 1
                except (json.JSONDecodeError, TypeError, ValueError) as error:
                    report["rejected"] += 1
                    report["errors"].append(
                        {"file": str(jsonl_path), "line": line_number, "error": str(error)}
                    )

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa questões revisadas em JSONL.")
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Valida e reporta sem gravar.")
    args = parser.parse_args()

    if not args.dry_run:
        Base.metadata.create_all(bind=engine)
        upgrade_game_round_question(engine)
    elif not inspect(engine).has_table("news"):
        raise RuntimeError("Inicialize o esquema do banco antes de validar questões em dry-run.")
    with SessionLocal() as db:
        if not args.dry_run:
            seed_skills(db)
        report = import_question_jsonl(db, args.jsonl, dry_run=args.dry_run)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()