"""
[RF-04] Persistir respostas das rodadas: modelo Answer, regras e migration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Answer, Game, GameRound, News, Question, User
from app.repositories.answer_repository import AnswerRepository
from app.repositories.skill_repository import SkillRepository
from seed import seed_skills


BACKEND_DIR = Path(__file__).parents[1]


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    seed_skills(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def round_data(db):
    """Usuário, rodada e pergunta prontos para receber uma resposta."""
    user = User(name="Ana", email="ana@example.com", phone="0", password="x")
    news = News(title="Notícia", content="Conteúdo")
    db.add_all([user, news])
    db.flush()

    skill = SkillRepository.get_skill_by_code(db, "SOURCE")
    question = Question(
        news_id=news.id,
        skill_id=skill.id,
        text="Pergunta?",
        difficulty=0.5,
        options={"A": "Sim", "B": "Não"},
        correct_option="B",
    )
    game = Game(user_id=user.id)
    db.add_all([question, game])
    db.flush()

    game_round = GameRound(game_id=game.id, news_id=news.id, round_number=1)
    db.add(game_round)
    db.commit()
    return user, game_round, question


def _create_answer(db, round_data, **overrides):
    user, game_round, question = round_data
    fields = {
        "selected_option": "B",
        "correct": True,
        "confidence": 4,
        "response_time": 5320,
    } | overrides
    return AnswerRepository.create_answer(db, user.id, game_round.id, question.id, **fields)


# ------------------------------------------------------------
# Persistência
# ------------------------------------------------------------

def test_answer_is_linked_to_user_round_and_question(db, round_data):
    user, game_round, question = round_data

    answer = _create_answer(db, round_data)

    assert answer.user.id == user.id
    assert answer.game_round.id == game_round.id
    assert answer.question.id == question.id
    assert answer in game_round.answers
    assert answer in question.answers


@pytest.mark.parametrize("correct", [True, False])
def test_correctness_is_persisted(db, round_data, correct):
    answer = _create_answer(db, round_data, selected_option="B" if correct else "A", correct=correct)
    db.expire_all()

    stored = AnswerRepository.get_answer_by_id(db, answer.id)
    assert stored.correct is correct
    assert stored.selected_option == ("B" if correct else "A")


def test_confidence_response_time_and_created_at_are_persisted(db, round_data):
    answer = _create_answer(db, round_data, confidence=5, response_time=1234)
    db.expire_all()

    stored = AnswerRepository.get_answer_by_id(db, answer.id)
    assert stored.confidence == 5
    assert stored.response_time == 1234
    assert stored.created_at is not None


def test_confidence_and_response_time_are_optional(db, round_data):
    answer = _create_answer(db, round_data, confidence=None, response_time=None)

    assert answer.confidence is None
    assert answer.response_time is None


# ------------------------------------------------------------
# Validações
# ------------------------------------------------------------

@pytest.mark.parametrize("confidence", [1, 3, 5])
def test_confidence_between_1_and_5_is_accepted(db, round_data, confidence):
    assert _create_answer(db, round_data, confidence=confidence).confidence == confidence


@pytest.mark.parametrize("confidence", [0, 6, -1])
def test_confidence_outside_1_and_5_is_rejected(confidence):
    with pytest.raises(ValueError):
        Answer(confidence=confidence)


def test_negative_response_time_is_rejected():
    with pytest.raises(ValueError):
        Answer(response_time=-1)


def test_zero_response_time_is_accepted(db, round_data):
    assert _create_answer(db, round_data, response_time=0).response_time == 0


@pytest.mark.parametrize(
    "column, value",
    [("confidence", 0), ("confidence", 6), ("response_time", -5)],
)
def test_database_checks_reject_invalid_values(db, round_data, column, value):
    user, game_round, question = round_data
    values = {"confidence": 3, "response_time": 1000, column: value}

    # Ignora a validação do ORM para garantir que o próprio banco barra o valor
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO answers (id, user_id, game_round_id, question_id, selected_option, "
                "correct, confidence, response_time, created_at) VALUES ('x', :user_id, :round_id, "
                ":question_id, 'A', 0, :confidence, :response_time, CURRENT_TIMESTAMP)"
            ),
            {
                "user_id": user.id,
                "round_id": game_round.id,
                "question_id": question.id,
                **values,
            },
        )


# ------------------------------------------------------------
# Migration
# ------------------------------------------------------------

def _alembic(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def _check_names(engine, table):
    return {c["name"] for c in inspect(engine).get_check_constraints(table)}


def test_migration_creates_answers_with_rules(tmp_path):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"

    command.upgrade(_alembic(url), "head")

    engine = create_engine(url)
    columns = {c["name"] for c in inspect(engine).get_columns("answers")}
    assert {
        "id", "user_id", "game_round_id", "question_id", "selected_option",
        "correct", "confidence", "response_time", "created_at",
    } <= columns
    assert {
        "ck_answer_confidence_range",
        "ck_answer_response_time_non_negative",
    } <= _check_names(engine, "answers")


def test_migration_adds_rules_to_existing_answers_table(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    config = _alembic(url)
    command.upgrade(config, "0001")

    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE answers (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
            "game_round_id VARCHAR(36) NOT NULL, question_id VARCHAR(36) NOT NULL, "
            "selected_option VARCHAR(10) NOT NULL, correct BOOLEAN NOT NULL, confidence INTEGER, "
            "response_time INTEGER, created_at DATETIME NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO answers VALUES ('a1', 'u1', 'r1', 'q1', 'A', 1, 9, -10, CURRENT_TIMESTAMP)"
        ))

    command.upgrade(config, "head")

    with engine.connect() as connection:
        confidence, response_time = connection.execute(
            text("SELECT confidence, response_time FROM answers")
        ).one()
    assert confidence is None       # fora de 1–5 vira "não informado"
    assert response_time is None    # negativo vira "não informado"
    assert {
        "ck_answer_confidence_range",
        "ck_answer_response_time_non_negative",
    } <= _check_names(engine, "answers")
