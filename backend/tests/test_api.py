import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def fake_search(_text):
    return (
        {"claims": []},
        [{"source": "Reuters", "rating": "false", "url": "https://reuters.example/check"}],
    )


def test_create_and_get_verification(monkeypatch):
    monkeypatch.setattr("app.routes.verification.search_and_map_claims", fake_search)

    created = client.post("/api/verifications", json={"text": "Vacinas causam autismo"})
    assert created.status_code == 202
    verification_id = created.json()["id"]

    result = client.get(f"/api/verifications/{verification_id}")
    assert result.status_code == 200
    assert result.json()["status"] == "completed"
    assert result.json()["evidence"][0]["source"] == "Reuters"


def test_create_feedback():
    created = client.post("/api/verifications", json={"text": "Uma afirmação"})
    verification_id = created.json()["id"]

    response = client.post(
        f"/api/verifications/{verification_id}/feedback",
        json={"answers": {"expectation": True, "alignment": False}},
    )
    assert response.status_code == 201
    assert response.json()["verification_id"] == verification_id


def test_missing_verification_returns_404():
    response = client.get("/api/verifications/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Verification not found"
