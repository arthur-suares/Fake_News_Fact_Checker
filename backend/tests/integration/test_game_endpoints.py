import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from fastapi.testclient import TestClient

from app.main import app
from app.models import Game, GameRound, News, Question, User
from seed import SAMPLE_ROUNDS, seed_sample_news_and_questions


def test_create_game_returns_first_round(db_session):
    seed_sample_news_and_questions(db_session)
    client = TestClient(app)

    response = client.post("/api/games")

    assert response.status_code == 201
    body = response.json()
    assert body["game_id"]
    assert body["round"]["number"] == 1
    assert body["round"]["question_id"] == body["question"]["id"]
    assert body["question"]["skill_code"] in {"SOURCE", "EVIDENCE", "CONTEXT", "VISUAL"}
    # A resposta não pode revelar o gabarito antes do envio
    assert "correct_option" not in body["question"]
    assert "explanation" not in body["question"]
    assert "verdict" not in body["news"]


def test_create_game_without_questions_returns_422(db_session):
    client = TestClient(app)

    response = client.post("/api/games")

    assert response.status_code == 422


def test_demo_seed_is_idempotent(db_session):
    seed_sample_news_and_questions(db_session)
    news_count = db_session.query(News).count()
    question_count = db_session.query(Question).count()

    seed_sample_news_and_questions(db_session)

    assert news_count == len(SAMPLE_ROUNDS)
    assert question_count == len(SAMPLE_ROUNDS)
    assert db_session.query(News).count() == news_count
    assert db_session.query(Question).count() == question_count


def test_demo_seed_adds_playable_questions_when_imported_news_already_exist(db_session):
    db_session.add(News(title="Imported article", content="Imported dataset text"))
    db_session.commit()

    seed_sample_news_and_questions(db_session)

    assert db_session.query(News).count() == len(SAMPLE_ROUNDS) + 1
    assert db_session.query(Question).count() == len(SAMPLE_ROUNDS)


def test_next_round_cannot_skip_unanswered_round(db_session):
    seed_sample_news_and_questions(db_session)
    client = TestClient(app)
    first_round = client.post("/api/games").json()

    response = client.get(f"/api/games/{first_round['game_id']}/next")

    assert response.status_code == 409
    assert db_session.query(GameRound).filter_by(game_id=first_round["game_id"]).count() == 1


def test_user_cannot_read_another_users_game_status(db_session):
    seed_sample_news_and_questions(db_session)
    client = TestClient(app)
    other_user = User(
        name="Other User",
        email="other@example.test",
        phone="0000000001",
        password="not-a-real-password-hash",
    )
    db_session.add(other_user)
    db_session.commit()
    other_game = Game(user_id=other_user.id)
    db_session.add(other_game)
    db_session.commit()

    response = client.get(f"/api/games/{other_game.id}")

    assert response.status_code == 403


def test_user_cannot_advance_another_users_game(db_session):
    seed_sample_news_and_questions(db_session)
    client = TestClient(app)
    other_user = User(
        name="Other User",
        email="other-next@example.test",
        phone="0000000003",
        password="not-a-real-password-hash",
    )
    db_session.add(other_user)
    db_session.commit()
    other_game = Game(user_id=other_user.id)
    db_session.add(other_game)
    db_session.commit()

    response = client.get(f"/api/games/{other_game.id}/next")

    assert response.status_code == 403
    assert db_session.query(GameRound).filter_by(game_id=other_game.id).count() == 0


def test_full_game_plays_ten_rounds_then_finishes(db_session):
    seed_sample_news_and_questions(db_session)
    client = TestClient(app)

    current = client.post("/api/games").json()
    game_id = current["game_id"]
    seen_news = set()

    for expected_number in range(1, 11):
        assert current["round"]["number"] == expected_number
        seen_news.add(current["news"]["id"])

        answer = client.post(
            f"/api/games/{game_id}/answers",
            json={
                "question_id": current["question"]["id"],
                "game_round_id": current["round"]["id"],
                "selected_option": "A",
                "confidence": 3,
                "response_time": 4000,
            },
        )
        assert answer.status_code == 201
        if expected_number == 10:
            status_response = client.get(f"/api/games/{game_id}")
            assert status_response.json()["status"] == "FINISHED"

        next_response = client.get(f"/api/games/{game_id}/next")
        assert next_response.status_code == 200
        current = next_response.json()

    # Depois da 10ª rodada a partida termina
    assert current is None
    assert client.get(f"/api/games/{game_id}").json()["status"] == "FINISHED"
    # Com 12 notícias no seed, nenhuma se repete em 10 rodadas
    assert len(seen_news) == 10 <= len(SAMPLE_ROUNDS)
