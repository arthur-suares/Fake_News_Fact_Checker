import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest
from fastapi.testclient import TestClient

from app.bkt.manager import BKTManager
from app.dependencies import get_current_user_id
from app.main import app
from app.models import Answer, Question, UserSkillState
from app.repositories.game_repository import GameRepository
from seed import seed_sample_news_and_questions


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def game_round(db_session):
    seed_sample_news_and_questions(db_session)
    question = db_session.query(Question).first()
    game = GameRepository.create_game(db_session, "test-user")
    round_ = GameRepository.create_game_round(db_session, game.id, question.news_id, round_number=1)
    return game, round_, question


def _payload(round_, question, option):
    return {
        "question_id": question.id,
        "game_round_id": round_.id,
        "selected_option": option,
        "confidence": 3,
        "response_time": 4000,
    }


def _wrong_option(question):
    return next(option for option in question.options if option != question.correct_option)


def _mastery(db_session, question):
    state = (
        db_session.query(UserSkillState)
        .filter_by(user_id="test-user", skill_id=question.skill_id)
        .one()
    )
    db_session.refresh(state)
    return state.mastery_probability


@pytest.mark.parametrize("correct", [True, False])
def test_answer_is_corrected_persisted_and_updates_bkt(db_session, client, game_round, correct):
    game, round_, question = game_round
    option = question.correct_option if correct else _wrong_option(question)

    response = client.post(f"/api/games/{game.id}/answers", json=_payload(round_, question, option))

    assert response.status_code == 201
    body = response.json()
    assert body["correct"] is correct

    # Answer persistida com a correção
    answer = db_session.get(Answer, body["id"])
    assert answer.correct is correct
    assert answer.selected_option == option
    assert answer.user_id == "test-user"

    # BKT executado a partir do domínio anterior e UserSkillState atualizado
    expected = BKTManager.update(question.skill.code, 0.3, correct)
    assert body["previous_mastery_probability"] == pytest.approx(0.3)
    assert body["mastery_probability"] == pytest.approx(expected)
    assert _mastery(db_session, question) == pytest.approx(expected)


def test_option_not_in_question_is_rejected(db_session, client, game_round):
    game, round_, question = game_round

    response = client.post(f"/api/games/{game.id}/answers", json=_payload(round_, question, "Z"))

    assert response.status_code == 422
    assert db_session.query(Answer).count() == 0


def test_round_cannot_be_answered_twice(db_session, client, game_round):
    game, round_, question = game_round
    payload = _payload(round_, question, question.correct_option)

    assert client.post(f"/api/games/{game.id}/answers", json=payload).status_code == 201
    mastery_after_first = _mastery(db_session, question)

    response = client.post(f"/api/games/{game.id}/answers", json=payload)

    assert response.status_code == 409
    assert db_session.query(Answer).count() == 1
    assert _mastery(db_session, question) == pytest.approx(mastery_after_first)


def test_user_cannot_answer_round_from_another_users_game(db_session, client, game_round):
    game, round_, question = game_round
    app.dependency_overrides[get_current_user_id] = lambda: "other-user"
    try:
        response = client.post(
            f"/api/games/{game.id}/answers",
            json=_payload(round_, question, question.correct_option),
        )
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)

    assert response.status_code == 403
    assert db_session.query(Answer).count() == 0
    assert db_session.query(UserSkillState).filter_by(user_id="other-user").count() == 0


def test_round_from_another_game_is_rejected(db_session, client, game_round):
    _, round_, question = game_round
    other_game = GameRepository.create_game(db_session, "test-user")

    response = client.post(
        f"/api/games/{other_game.id}/answers",
        json=_payload(round_, question, question.correct_option),
    )

    assert response.status_code == 404
    assert db_session.query(Answer).count() == 0


def test_question_from_another_round_is_rejected(db_session, client, game_round):
    game, round_, question = game_round
    other_question = db_session.query(Question).filter(Question.news_id != round_.news_id).first()

    response = client.post(
        f"/api/games/{game.id}/answers",
        json=_payload(round_, other_question, other_question.correct_option),
    )

    assert response.status_code == 404
    assert db_session.query(Answer).count() == 0


def test_unknown_game_returns_404(db_session, client, game_round):
    _, round_, question = game_round

    response = client.post(
        "/api/games/does-not-exist/answers",
        json=_payload(round_, question, question.correct_option),
    )

    assert response.status_code == 404


def test_finished_game_rejects_answers(db_session, client, game_round):
    game, round_, question = game_round
    GameRepository.finish_game(db_session, game.id)

    response = client.post(
        f"/api/games/{game.id}/answers",
        json=_payload(round_, question, question.correct_option),
    )

    assert response.status_code == 409
    assert db_session.query(Answer).count() == 0
