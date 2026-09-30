from pathlib import Path
import shutil
import pytest

from app.vector_db.embeddings import (
    DeterministicSparseEmbeddingFunction,
    get_embedding_function,
)
from app.vector_db.ingest import run_ingestion
from app.vector_db.schemas import VectorDocumentCreate
from app.vector_db.store import VectorStore
from app.services.vector_service import VectorFactCheckService, set_vector_store


@pytest.fixture
def temp_vector_store(tmp_path):
    storage_dir = str(tmp_path / "test_chroma")
    ef = DeterministicSparseEmbeddingFunction(dimension=128)
    store = VectorStore(
        storage_path=storage_dir,
        collection_name="test_facts",
        embedding_function=ef,
    )
    yield store
    shutil.rmtree(storage_dir, ignore_errors=True)


def test_deterministic_embedding_function():
    ef = DeterministicSparseEmbeddingFunction(dimension=64)
    assert ef.name() == "deterministic"
    assert ef.dimension == 64

    vecs = ef(["Vacina causa autismo", "Outra frase"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 64
    # Normalização L2: norma deve ser aproximadamente 1.0
    norm = sum(x * x for x in vecs[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_get_embedding_function_factory():
    ef_det = get_embedding_function("deterministic")
    assert ef_det.name() == "deterministic"


def test_vector_store_crud(temp_vector_store):
    store = temp_vector_store

    assert store.count() == 0

    doc1 = VectorDocumentCreate(
        text="Vacinas causam autismo em crianças",
        title="Desmentindo fake news de vacinas",
        url="https://lupa.uol.com.br/1",
        publisher_name="Lupa - UOL",
        publisher_site="lupa.uol.com.br",
        verdict="fake",
        origin="WhatsApp",
    )
    doc2 = VectorDocumentCreate(
        text="Governo anuncia queda na inflação oficial",
        title="Inflação cai em março",
        url="https://estadao.com.br/2",
        publisher_name="Estadão",
        publisher_site="estadao.com.br",
        verdict="true",
        origin="Ministério da Economia",
    )

    ids = store.add_documents([doc1, doc2])
    assert len(ids) == 2
    assert store.count() == 2

    # Recupera por ID
    fetched = store.get_document_by_id(ids[0])
    assert fetched is not None
    assert fetched.verdict == "fake"
    assert fetched.publisher_name == "Lupa - UOL"

    # Busca com filtro
    results = store.search(
        query="vacina autismo",
        top_k=2,
        verdict_filter="fake",
    )
    assert len(results) >= 1
    assert results[0].verdict == "fake"
    assert results[0].similarity_score > 0.0

    # Remoção
    deleted_count = store.delete_documents([ids[1]])
    assert deleted_count == 1
    assert store.count() == 1

    # Reset
    store.reset()
    assert store.count() == 0


def test_ingestion_pipeline(temp_vector_store):
    store = temp_vector_store

    response = run_ingestion(
        store=store,
        limit=3,
        batch_size=3,
        recreate_collection=True,
        dataset_source="all",
    )
    assert response.status == "success"
    assert response.total_ingested >= 1
    assert store.count() == response.total_ingested


def test_vector_fact_check_service(temp_vector_store):
    set_vector_store(temp_vector_store)

    doc_id = VectorFactCheckService.index_fact_check(
        text="Cloroquina cura covid comprovadamente",
        verdict="fake",
        publisher="Aos Fatos",
        url="https://aosfatos.org/cloroquina",
        title="É falso que cloroquina cura covid",
    )
    assert doc_id is not None

    verdict, evidences = VectorFactCheckService.verify_claim(
        query="cloroquina cura covid",
        top_k=3,
        min_confidence=0.30,
    )
    assert verdict == "fake"
    assert len(evidences) >= 1
    assert "Aos Fatos" in evidences[0]["source"]
    assert evidences[0]["rating"] == "fake"

    set_vector_store(None)
