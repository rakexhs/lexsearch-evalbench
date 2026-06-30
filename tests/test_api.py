"""Integration test: mini end-to-end through the FastAPI app."""
import pytest
from fastapi.testclient import TestClient

from app.ingestion.sample_corpus import materialize
from app.main import app


@pytest.fixture(scope="module")
def client():
    materialize()  # ensure corpus + golden set exist on disk
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_ingest_then_query_end_to_end(client):
    # ingest from the on-disk sample corpus
    r = client.post("/ingest", json={"rebuild": True})
    assert r.status_code == 200
    ing = r.json()
    assert ing["num_documents"] >= 20
    assert ing["num_chunks"] > ing["num_documents"]

    # health now reports an index
    h = client.get("/health").json()
    assert h["indexed"] is True
    assert h["num_chunks"] == ing["num_chunks"]

    # query end-to-end with grounded answer + citations
    r = client.post(
        "/query",
        json={
            "query": "How do I create a new branch and switch to it in one command?",
            "method": "hybrid_rerank",
            "top_k": 5,
            "generate_answer": True,
        },
    )
    assert r.status_code == 200
    resp = r.json()
    assert len(resp["results"]) == 5
    assert resp["answer"]["answer"]
    assert "total_ms" in resp["latency_ms"]
    # the git-branching doc should appear in the retrieved results
    assert any(rc["chunk"]["doc_id"] == "git-branching" for rc in resp["results"])


def test_query_bad_method(client):
    r = client.post("/query", json={"query": "x", "method": "not_a_method"})
    assert r.status_code == 400


def test_evaluate_small(client):
    client.post("/ingest", json={"rebuild": True})
    r = client.post("/evaluate", json={"methods": ["bm25", "hybrid_rerank"], "k_values": [1, 3, 5], "limit": 6})
    assert r.status_code == 200
    body = r.json()
    assert body["num_questions"] == 6
    methods = {m["method"] for m in body["results"]}
    assert methods == {"bm25", "hybrid_rerank"}
