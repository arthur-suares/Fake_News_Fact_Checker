from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.vector_service import set_vector_store
from app.vector_db.embeddings import DeterministicSparseEmbeddingFunction
from app.vector_db.store import VectorStore


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_store(tmp_path):
    storage_dir = str(tmp_path / "test_api_chroma")
    ef = DeterministicSparseEmbeddingFunction(dimension=128)
    store = VectorStore(
        storage_path=storage_dir,
        collection_name="test_api_collection",
        embedding_function=ef,
    )
    set_vector_store(store)
    yield store
    set_vector_store(None)


def test_api_vector_stats():
    response = client.get("/api/vector/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["collection_name"] == "test_api_collection"
    assert data["total_documents"] == 0


def test_api_add_and_search_documents():
    # Adicionar documento
    payload = {
        "text": "Mamadeira de piroca foi distribuída nas escolas",
        "title": "Desmentido sobre kit gay e mamadeiras",
        "url": "https://lupa.uol.com.br/mamadeira",
        "publisher_name": "Lupa - UOL",
        "verdict": "fake",
    }
    post_res = client.post("/api/vector/documents", json=payload)
    assert post_res.status_code == 201
    inserted_id = post_res.json()["ids"][0]

    # Obter por ID
    get_res = client.get(f"/api/vector/documents/{inserted_id}")
    assert get_res.status_code == 200
    assert get_res.json()["publisher_name"] == "Lupa - UOL"

    # Busca POST
    search_res = client.post(
        "/api/vector/search",
        json={"query": "mamadeira piroca escolas", "top_k": 3, "score_threshold": 0.0},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert search_data["results"][0]["verdict"] == "fake"

    # Busca GET
    search_get = client.get("/api/vector/search?query=mamadeira+escolas&top_k=2")
    assert search_get.status_code == 200
    assert search_get.json()["total"] >= 1

    # Deletar documento
    del_res = client.delete(f"/api/vector/documents/{inserted_id}")
    assert del_res.status_code == 200

    # Tentar buscar após exclusão
    get_after_del = client.get(f"/api/vector/documents/{inserted_id}")
    assert get_after_del.status_code == 404


def test_api_vector_ingest_and_reset():
    ingest_res = client.post(
        "/api/vector/ingest",
        json={"limit": 2, "batch_size": 2, "recreate_collection": True},
    )
    assert ingest_res.status_code == 200
    data = ingest_res.json()
    assert data["status"] == "success"
    assert data["total_ingested"] >= 1

    stats_res = client.get("/api/vector/stats")
    assert stats_res.json()["total_documents"] == data["total_ingested"]

    # Reset
    reset_res = client.post("/api/vector/reset")
    assert reset_res.status_code == 200
    stats_after_reset = client.get("/api/vector/stats")
    assert stats_after_reset.json()["total_documents"] == 0


def test_hybrid_verification_with_vector_db():
    # Inserir um documento falso conhecido
    client.post(
        "/api/vector/documents",
        json={
            "text": "Urnas eletrônicas foram fraudadas nas eleições",
            "title": "TSE desmente fraude em urnas",
            "url": "https://tse.jus.br/desmentido",
            "publisher_name": "TSE Checagens",
            "verdict": "fake",
        },
    )

    # Submeter verificação
    create_res = client.post(
        "/api/verifications",
        json={"text": "Urnas eletrônicas fraudadas"},
    )
    assert create_res.status_code == 202
    v_id = create_res.json()["id"]

    # Obter resultado
    verif_res = client.get(f"/api/verifications/{v_id}")
    assert verif_res.status_code == 200
    v_data = verif_res.json()
    assert v_data["status"] == "completed"
    # Deve conter evidência encontrada no banco vetorial
    evidence_sources = [e["source"] for e in v_data["evidence"]]
    assert any("Banco Vetorial" in s for s in evidence_sources)
