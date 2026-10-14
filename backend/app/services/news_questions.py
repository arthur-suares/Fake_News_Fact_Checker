"""
Game questions built from fact-checked claims in the EDA datasets.

Each CSV row is a claim (`text`) that circulated, who made or spread it
(`origin`), and the fact-check that judged it (`title`, `url`, publisher, date,
label). The skill and difficulty come from what the row offers as clues:

- SOURCE: the claim circulated through social media, messaging apps or
  anonymous posts, so the origin is the main warning sign.
- EVIDENCE: the claim relies on numbers or data that can be checked.
- CONTEXT: the remaining claims, usually statements by public figures, where
  when and how something was said matters.

VISUAL is never generated: the datasets have no images.

Each option pairs a verdict with a justification for the skill: one sound
criterion and one common fallacy per verdict. Only the right verdict with the
sound criterion is correct, so a lucky guess backed by a fallacy does not count
as mastery of the skill tracked by BKT.

The fact-check headline usually gives the answer away ("É falso que..."), so it
is only revealed in the explanation shown after answering.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import News, Question
from app.services.dataset_import import (
    LABELS,
    dataset_metadata,
    default_dataset_files,
    news_ids_by_source_key,
    normalize_value,
    record_source_key,
)

# Seeds the sampling hash: changing it would pick a different set of claims.
GENERATOR = "dataset-claim-v1"
DEFAULT_PER_CELL = 10
SKILL_SOURCE = "SOURCE"
SKILL_EVIDENCE = "EVIDENCE"
SKILL_CONTEXT = "CONTEXT"

# The frontend splits options on the first ": " to show verdict and justification.
VERDICT_LABEL = {"true": "Verdadeira", "fake": "Falsa ou enganosa"}
OPTION_KEYS = ("A", "B", "C", "D")

# (sound criterion, fallacy) for each verdict, per skill.
JUSTIFICATIONS = {
    SKILL_SOURCE: {
        "true": (
            "mesmo tendo circulado em redes ou mensagens, a informação é confirmada por "
            "fontes identificáveis, como veículos de imprensa ou canais oficiais.",
            "foi compartilhada por muitas pessoas e perfis diferentes, o que mostra que é real.",
        ),
        "fake": (
            "não tem autor identificável nem confirmação em fontes confiáveis; só circula "
            "como mensagem repassada.",
            "tudo o que circula em redes sociais e aplicativos de mensagem costuma ser mentira.",
        ),
    },
    SKILL_EVIDENCE: {
        "true": (
            "os números conferem com a fonte original dos dados, como órgãos oficiais, "
            "estudos ou bases públicas.",
            "a alegação traz números precisos e detalhados, e isso basta para mostrar que "
            "é bem fundamentada.",
        ),
        "fake": (
            "os números não conferem com a fonte original: estão errados, exagerados ou "
            "comparam coisas diferentes.",
            "os números parecem grandes ou estranhos demais para serem reais.",
        ),
    },
    SKILL_CONTEXT: {
        "true": (
            "o que foi dito ou aconteceu confere com o registro original, considerando "
            "quando e em que situação.",
            "quem disse é uma pessoa conhecida, então a informação é confiável.",
        ),
        "fake": (
            "a alegação distorce o que foi dito ou feito, ou tira o fato do contexto "
            "original (data, situação, o que veio antes e depois).",
            "a alegação contradiz o que eu penso de quem disse, então não deve ser verdade.",
        ),
    },
}

QUESTION_TEXT = {
    SKILL_SOURCE: (
        "Observe quem espalhou a alegação e por onde ela circulou. Qual alternativa "
        "traz o veredito correto com a melhor justificativa sobre a origem?"
    ),
    SKILL_EVIDENCE: (
        "A alegação se apoia em números ou dados. Qual alternativa traz o veredito "
        "correto com a melhor justificativa sobre essas evidências?"
    ),
    SKILL_CONTEXT: (
        "Considere quem disse, quando e em que situação. Qual alternativa traz o "
        "veredito correto com a melhor justificativa sobre o contexto?"
    ),
}

LESSON = {
    SKILL_SOURCE: (
        "Mensagens repassadas em redes sociais ou aplicativos, sem autor identificável, "
        "precisam ser confirmadas em veículos de imprensa ou agências de checagem antes "
        "de serem compartilhadas."
    ),
    SKILL_EVIDENCE: (
        "Números e dados precisam ser conferidos na fonte original (órgãos oficiais, "
        "estudos, bases públicas): um dado plausível pode estar errado, exagerado ou "
        "comparar coisas diferentes."
    ),
    SKILL_CONTEXT: (
        "Mesmo falas de pessoas conhecidas precisam ser comparadas com o contexto: quando "
        "foram ditas, o que veio antes e depois e o que os registros oficiais mostram."
    ),
}

RUMOR_ORIGIN = re.compile(
    r"rede|whatsapp|facebook|instagram|twitter|tiktok|youtube|telegram|kwai|boato|"
    r"mensage|post|publica|internet|v[aá]ri[oa]s|utilizador|usu[aá]ri|perfil|corrente|"
    r"blog|site|v[ií]deo|imagem|foto|[aá]udio",
    re.IGNORECASE,
)
HAS_DATA = re.compile(r"\d|%|\bmil\b|milh[õo]|bilh[õo]", re.IGNORECASE)
# Claims that already state the verdict cannot be asked as true or false.
SPOILER = re.compile(
    r"\bfals[oa]s?\b|\bverdad|\bfake\b|\bboato|enganos|checag|fact.?check|verifica|"
    r"desment|mentir|\bmito\b|\bnão é\b",
    re.IGNORECASE,
)
QUESTION_FIELDS = ("text", "difficulty", "options", "correct_option", "explanation")
MIN_CLAIM_LENGTH = 40
MAX_CLAIM_LENGTH = 600


def classify_claim(claim: str, origin: str | None) -> tuple[str, float]:
    """Skill and difficulty from label-independent clues of the claim."""
    if origin and RUMOR_ORIGIN.search(origin):
        skill_code, difficulty = SKILL_SOURCE, 0.35
    elif HAS_DATA.search(claim):
        skill_code, difficulty = SKILL_EVIDENCE, 0.55
    else:
        skill_code, difficulty = SKILL_CONTEXT, 0.5

    # Fewer clues on screen make the judgement harder.
    if not origin:
        difficulty += 0.1
    if len(claim) < 80:
        difficulty += 0.1
    elif len(claim) > 200:
        difficulty -= 0.1
    return skill_code, round(min(0.8, max(0.2, difficulty)), 1)


def usable_claim(claim: str | None, date: str | None) -> bool:
    return bool(
        claim
        and date
        and MIN_CLAIM_LENGTH <= len(claim) <= MAX_CLAIM_LENGTH
        and not claim.endswith("?")
        and not SPOILER.search(claim)
    )


def format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return value


def build_options(skill_code: str, news_class: str, claim: str) -> tuple[dict[str, str], str]:
    """Verdict + justification options and the correct key, shuffled per claim."""
    choices = [
        (verdict, sound, f"{VERDICT_LABEL[verdict]}: {text}")
        for verdict in VERDICT_LABEL
        for sound, text in zip((True, False), JUSTIFICATIONS[skill_code][verdict])
    ]
    # Hashing the claim keeps the order stable across reseeds.
    choices.sort(key=lambda choice: hashlib.sha256(f"{GENERATOR}:{claim}:{choice[2]}".encode()).hexdigest())
    options = {key: text for key, (_, _, text) in zip(OPTION_KEYS, choices)}
    correct = next(
        key
        for key, (verdict, sound, _) in zip(OPTION_KEYS, choices)
        if verdict == news_class and sound
    )
    return options, correct


def build_question(news: News) -> dict | None:
    """Question fields for a dataset news item, or None if it cannot be asked."""
    dataset = (news.fact_check_data or {}).get("dataset") or {}
    news_class = dataset.get("class")
    if news_class not in VERDICT_LABEL:
        return None
    claim = normalize_value(news.content)
    origin = dataset.get("origin")
    if not usable_claim(claim, dataset.get("original_date")):
        return None

    skill_code, difficulty = classify_claim(claim, origin)
    options, correct_option = build_options(skill_code, news_class, claim)
    publisher = dataset.get("publisher_name") or dataset.get("publisher_site") or "Uma agência de checagem"
    verdict = VERDICT_LABEL[news_class].lower()
    checked_on = format_date(dataset.get("original_date"))
    explanation = (
        f"{publisher} classificou esta alegação como {verdict} na checagem "
        f"“{news.title}”{f', publicada em {checked_on}' if checked_on else ''}. "
        f"{LESSON[skill_code]} Leia a checagem completa para ver as evidências usadas."
    )
    return {
        "skill_code": skill_code,
        "text": QUESTION_TEXT[skill_code],
        "difficulty": difficulty,
        "options": options,
        "correct_option": correct_option,
        "explanation": explanation,
    }


def news_details(news: News) -> dict | None:
    """Data shown with a dataset claim during a round, without the verdict."""
    dataset = (news.fact_check_data or {}).get("dataset")
    if not dataset:
        return None
    return {
        "kind": "fact_check_claim",
        "claim": news.content,
        "origin": dataset.get("origin"),
        "checked_on": format_date(dataset.get("original_date")),
        "fact_checker": dataset.get("publisher_name"),
        "fact_checker_site": dataset.get("publisher_site"),
        "source_url": dataset.get("source_url"),
    }


def round_title(news: News) -> str:
    """Title for the round; the fact-check headline would spoil the answer."""
    dataset = (news.fact_check_data or {}).get("dataset")
    if not dataset:
        return news.title
    publisher = dataset.get("publisher_name")
    return f"Alegação checada por {publisher}" if publisher else "Alegação em análise"


def question_hints(news: News, skill_code: str) -> list[str]:
    """What to look at before answering, built from the claim's own data."""
    dataset = (news.fact_check_data or {}).get("dataset")
    if not dataset:
        return []
    origin = dataset.get("origin")
    checked_on = format_date(dataset.get("original_date"))
    publisher = dataset.get("publisher_name") or dataset.get("publisher_site")

    hints = []
    if skill_code == SKILL_SOURCE:
        hints.append(
            f"Origem informada: “{origin}”. Existe um autor identificável ou é só uma "
            "mensagem repassada?"
            if origin
            else "Ninguém assume a autoria da alegação. Isso por si só já pede cautela."
        )
        hints.append("A mesma informação aparece em veículos de imprensa ou canais oficiais?")
    elif skill_code == SKILL_EVIDENCE:
        hints.append("Quais números a alegação usa e de onde eles deveriam vir?")
        hints.append(
            "Dados oficiais (IBGE, ministérios, tribunais, institutos de pesquisa) "
            "costumam estar disponíveis para conferência."
        )
    else:
        if origin:
            hints.append(f"Quem disse: {origin}. Em que situação essa fala foi feita?")
        hints.append("Uma frase pode enganar quando é tirada do contexto em que foi dita.")
    if checked_on:
        hints.append(f"A alegação foi checada em {checked_on}. A informação ainda é atual?")
    if publisher:
        hints.append(f"Na dúvida, abra a checagem completa ({publisher}) pelo link da alegação.")
    return hints


def _sample_rows(csv_paths: list[Path], per_cell: int) -> list[tuple[Path, dict, str]]:
    """Balanced, deterministic sample: as many true as fake claims per skill/difficulty."""
    cells: dict[tuple[str, float, str], list[tuple[str, Path, dict]]] = defaultdict(list)
    for csv_path in csv_paths:
        with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                label = normalize_value(row.get("label"))
                title = normalize_value(row.get("title"))
                claim = normalize_value(row.get("text"))
                url = normalize_value(row.get("url"))
                if label not in LABELS or not title or not url:
                    continue
                if not usable_claim(claim, normalize_value(row.get("date"))):
                    continue
                skill_code, difficulty = classify_claim(claim, normalize_value(row.get("origin")))
                source_key = record_source_key(title, claim, url)
                cells[(skill_code, difficulty, LABELS[label])].append((source_key, csv_path, row))

    sample = []
    for skill_code, difficulty in sorted({(skill, level) for skill, level, _ in cells}):
        true_rows = cells[(skill_code, difficulty, "true")]
        fake_rows = cells[(skill_code, difficulty, "fake")]
        size = min(per_cell, len(true_rows), len(fake_rows))
        for rows in (true_rows, fake_rows):
            # Hashing the key spreads the pick across publishers and years.
            rows.sort(key=lambda item: hashlib.sha256(f"{GENERATOR}:{item[0]}".encode()).hexdigest())
            sample.extend((csv_path, row, source_key) for source_key, csv_path, row in rows[:size])
    return sample


def _upgrade_questions(db: Session) -> int:
    """Rewrite stored dataset questions whose fields differ from the current generator."""
    updated = 0
    for question in db.query(Question).join(News).filter(News.fact_check_data.isnot(None)):
        fields = build_question(question.news)
        if not fields or fields["skill_code"] != question.skill.code:
            continue
        current = {key: fields[key] for key in QUESTION_FIELDS}
        if {key: getattr(question, key) for key in QUESTION_FIELDS} != current:
            for key, value in current.items():
                setattr(question, key, value)
            updated += 1
    return updated


def seed_news_questions(
    db: Session,
    csv_paths: list[Path] | None = None,
    *,
    per_cell: int = DEFAULT_PER_CELL,
    dry_run: bool = False,
) -> dict:
    """
    Ensure a balanced sample of dataset claims exists as news + game questions.

    Reuses news already imported by dataset_import (same source key) and never
    duplicates questions, so it is safe to run on every startup. Questions from
    an older generator (e.g. plain true/false) are rewritten in place.
    """
    from app.repositories.skill_repository import SkillRepository

    csv_paths = csv_paths or default_dataset_files()
    report = {"sampled": 0, "news_created": 0, "questions_created": 0, "questions_updated": 0}
    if not all(Path(path).exists() for path in csv_paths):
        report["skipped"] = "dataset CSVs not found"
        return report

    skills_by_code = {skill.code: skill for skill in SkillRepository.get_all_skills(db)}
    existing_news = news_ids_by_source_key(db)
    try:
        for csv_path, row, source_key in _sample_rows(csv_paths, per_cell):
            report["sampled"] += 1
            news = db.get(News, existing_news[source_key]) if source_key in existing_news else None
            if news is None:
                news = News(
                    title=normalize_value(row.get("title")),
                    content=normalize_value(row.get("text")),
                    image_url=None,
                    verdict=None,
                    fact_check_data={"dataset": dataset_metadata(row, csv_path, source_key)},
                )
                db.add(news)
                db.flush()
                existing_news[source_key] = news.id
                report["news_created"] += 1

            fields = build_question(news)
            skill = skills_by_code.get(fields["skill_code"]) if fields else None
            if not skill:
                continue
            if db.query(Question.id).filter_by(news_id=news.id, skill_id=skill.id).first():
                continue
            db.add(
                Question(
                    news_id=news.id,
                    skill_id=skill.id,
                    text=fields["text"],
                    difficulty=fields["difficulty"],
                    options=fields["options"],
                    correct_option=fields["correct_option"],
                    explanation=fields["explanation"],
                )
            )
            report["questions_created"] += 1

        report["questions_updated"] = _upgrade_questions(db)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return report


def main() -> None:
    from app.database import Base, SessionLocal, engine
    from app.migrations import upgrade_game_round_question
    from seed import seed_skills

    defaults = default_dataset_files()
    parser = argparse.ArgumentParser(
        description="Gera questões de veredito + justificativa a partir das alegações checadas do dataset."
    )
    parser.add_argument("--fake-csv", type=Path, default=defaults[0])
    parser.add_argument("--true-csv", type=Path, default=defaults[1])
    parser.add_argument(
        "--per-cell",
        type=int,
        default=DEFAULT_PER_CELL,
        help="Alegações verdadeiras (e o mesmo número de falsas) por skill/dificuldade.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    upgrade_game_round_question(engine)
    with SessionLocal() as db:
        seed_skills(db)
        report = seed_news_questions(
            db,
            [args.fake_csv, args.true_csv],
            per_cell=args.per_cell,
            dry_run=args.dry_run,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
