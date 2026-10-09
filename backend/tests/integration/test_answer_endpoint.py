import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Question
from app.repositories.game_repository import GameRepository
from seed import seed_sample_news_and_questions


@pytest.fixture
def game_round(db_session):
    seed_sample_news_and_questions(db_session)
    question = db_session.query(Question).first()
    game = GameRepository.create_game(db_session, "test-user")
    round_ = GameRepository.create_game_round(
        db_session, game.id, question.news_id, round_number=1, question_id=question.id
    )
    return game, round_, question


def test_submit_answer_returns_feedback_fields(db_session, game_round):
    game, round_, question = game_round
    client = TestClient(app)

    response = client.post(
        f"/api/games/{game.id}/answers",
        json={
            "question_id": question.id,
            "game_round_id": round_.id,
            "selected_option": question.correct_option,
            "confidence": 4,
            "response_time": 5320,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["correct"] is True
    assert body["correct_option"] == question.correct_option
    assert body["skill_code"] == question.skill.code
    assert body["previous_mastery_probability"] is not None
    assert body["mastery_probability"] >= body["previous_mastery_probability"]


def test_submit_answer_rejects_invalid_confidence(db_session, game_round):
    game, round_, question = game_round
    client = TestClient(app)

    response = client.post(
        f"/api/games/{game.id}/answers",
        json={
            "question_id": question.id,
            "game_round_id": round_.id,
            "selected_option": "A",
            "confidence": 9,
        },
    )

    assert response.status_code == 422
