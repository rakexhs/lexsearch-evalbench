"""Tests for dense retrieval (offline hashing embedder path)."""
import numpy as np

from app.retrieval.dense import DenseRetriever, _hash_embed


def test_hash_embed_is_normalized_and_deterministic():
    a = _hash_embed(["git branch create switch"])
    b = _hash_embed(["git branch create switch"])
    assert np.allclose(a, b)  # deterministic
    assert abs(np.linalg.norm(a[0]) - 1.0) < 1e-5  # L2 normalized


def test_index_and_search_shape(chunks):
    r = DenseRetriever()
    r.index(chunks)
    out = r.search("how to undo a commit safely", top_k=5)
    assert len(out) == 5
    scores = [s for _, s in out]
    assert scores == sorted(scores, reverse=True)
    # cosine of normalized vectors must stay within [-1, 1]
    assert all(-1.0001 <= s <= 1.0001 for s in scores)
    assert r.mode == "hashing"  # forced offline in conftest


def test_relevant_doc_retrieved(chunks):
    r = DenseRetriever()
    r.index(chunks)
    out = r.search("docker image versus container running instance", top_k=5)
    docs = {c.doc_id for c, _ in out}
    assert "docker-images-containers" in docs
