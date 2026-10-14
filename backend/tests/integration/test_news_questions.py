import csv
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import News, Question
from app.services.news_questions import (
    JUSTIFICATIONS,
    VERDICT_LABEL,
    build_question,
    classify_claim,
    seed_news_questions,
)
from seed import seed_skills

FIELDS = ["title", "text", "origin", "url", "label", "publisher_name", "publisher_site", "date"]


def _row(index: int, label: int, origin: str, text: str) -> dict:
    return {
        "title": f"Checagem {index}: é falso ou verdadeiro?",
        "text": text,
        "origin": origin,
        "url": f"https://checker.test/{index}",
        "label": label,
        "publisher_name": "Checker",
        "publisher_site": "checker.test",
        "date": "2022-09-06 00:00:00",
    }


def _write(path: Path, rows: list[dict]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _dataset(tmp_path: Path) -> list[Path]:
    rumor = "Governo vai liberar um benefício extra para todas as famílias inscritas no programa"
    fakes = [_row(i, 1, "Mensagem no WhatsApp", f"{rumor} a partir da semana {chr(97 + i)}") for i in range(5)]
    trues = [_row(10 + i, 0, "Post no Facebook", f"{rumor} conforme anunciado na região {chr(97 + i)}") for i in range(2)]
    spoilers = [_row(20, 1, "Mensagem no WhatsApp", "É falso que o governo vai liberar um benefício extra para famílias")]
    questions = [_row(21, 0, "Mensagem no WhatsApp", "O governo vai liberar um benefício extra para as famílias inscritas?")]
    return [
        _write(tmp_path / "fakes.csv", fakes + spoilers),
        _write(tmp_path / "true.csv", trues + questions),
    ]


def test_classify_claim_uses_origin_and_data_clues():
    assert classify_claim("Mensagem longa o bastante para análise de origem do boato", "Post no Facebook")[0] == "SOURCE"
    assert classify_claim("O desemprego caiu 12% no último trimestre segundo o governo", "Ministro")[0] == "EVIDENCE"
    assert classify_claim("Eu nunca disse que apoiaria essa proposta durante a campanha", "Candidato")[0] == "CONTEXT"


def test_seed_is_balanced_skips_spoilers_and_is_idempotent(db_session, tmp_path):
    seed_skills(db_session)
    paths = _dataset(tmp_path)

    report = seed_news_questions(db_session, paths, per_cell=10)

    # Só 2 alegações verdadeiras utilizáveis, então 2 falsas entram para equilibrar
    assert report["questions_created"] == 4
    answers = sorted(
        question.options[question.correct_option].split(":")[0]
        for question in db_session.query(Question).all()
    )
    assert answers == ["Falsa ou enganosa", "Falsa ou enganosa", "Verdadeira", "Verdadeira"]
    assert all("falso" not in news.content.lower() for news in db_session.query(News).all())

    rerun = seed_news_questions(db_session, paths, per_cell=10)
    assert rerun["news_created"] == rerun["questions_created"] == rerun["questions_updated"] == 0
    assert db_session.query(Question).count() == 4


def test_options_pair_verdict_with_skill_justification(db_session, tmp_path):
    seed_skills(db_session)
    seed_news_questions(db_session, _dataset(tmp_path), per_cell=10)

    for question in db_session.query(Question).all():
        skill_code = question.skill.code
        news_class = question.news.fact_check_data["dataset"]["class"]
        assert sorted(question.options) == ["A", "B", "C", "D"]
        assert set(question.options.values()) == {
            f"{VERDICT_LABEL[verdict]}: {text}"
            for verdict, texts in JUSTIFICATIONS[skill_code].items()
            for text in texts
        }
        # Só o veredito certo com o critério correto da skill conta como acerto
        sound = JUSTIFICATIONS[skill_code][news_class][0]
        assert question.options[question.correct_option] == f"{VERDICT_LABEL[news_class]}: {sound}"
    assert len({question.correct_option for question in db_session.query(Question).all()}) > 1


def test_seed_upgrades_true_false_questions(db_session, tmp_path):
    seed_skills(db_session)
    paths = _dataset(tmp_path)
    seed_news_questions(db_session, paths, per_cell=10)
    for question in db_session.query(Question).all():
        question.options = {"A": "Verdadeira", "B": "Falsa"}
        question.correct_option = "A"
    db_session.commit()

    report = seed_news_questions(db_session, paths, per_cell=10)

    assert report["questions_created"] == 0
    assert report["questions_updated"] == 4
    assert all(len(question.options) == 4 for question in db_session.query(Question).all())


def test_question_explanation_reveals_fact_check_only_after_answering(db_session, tmp_path):
    seed_skills(db_session)
    seed_news_questions(db_session, _dataset(tmp_path), per_cell=10)
    client = TestClient(app)

    payload = client.post("/api/games").json()

    news = db_session.get(News, payload["news"]["id"])
    details = payload["news"]["details"]
    assert details["source_url"].startswith("https://checker.test/")
    assert details["origin"] and details["checked_on"] == "06/09/2022"
    assert details["fact_checker"] == "Checker"
    assert payload["question"]["hints"]
    # A manchete da checagem entrega a resposta: só aparece na explicação
    assert news.title not in str(payload)
    assert news.title in build_question(news)["explanation"]
