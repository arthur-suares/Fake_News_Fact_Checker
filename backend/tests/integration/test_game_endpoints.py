import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from fastapi.testclient import TestClient

from app.main import app
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

        next_response = client.get(f"/api/games/{game_id}/next")
        assert next_response.status_code == 200
        current = next_response.json()

    # Depois da 10ª rodada a partida termina
    assert current is None
    assert client.get(f"/api/games/{game_id}").json()["status"] == "FINISHED"
    # Com 12 notícias no seed, nenhuma se repete em 10 rodadas
    assert len(seen_news) == 10 <= len(SAMPLE_ROUNDS)
