"""Tests for BM25 retrieval."""
import pytest

from app.retrieval.bm25 import BM25Retriever, tokenize


def test_tokenize_keeps_identifiers():
    toks = tokenize("Use git.checkout and requirements.txt with --hard")
    assert "git.checkout" in toks
    assert "requirements.txt" in toks


def test_index_and_search_shape(chunks):
    r = BM25Retriever()
    r.index(chunks)
    out = r.search("git branch create switch", top_k=5)
    assert len(out) == 5
    # results are (chunk, score) sorted descending
    scores = [s for _, s in out]
    assert scores == sorted(scores, reverse=True)


def test_relevant_doc_ranked_first(chunks):
    r = BM25Retriever()
    r.index(chunks)
    out = r.search("git stash pop apply stack", top_k=3)
    top_docs = {c.doc_id for c, _ in out}
    assert "git-stash" in top_docs


def test_search_before_index_raises():
    r = BM25Retriever()
    with pytest.raises(RuntimeError):
        r.search("anything")


def test_empty_index_raises():
    r = BM25Retriever()
    with pytest.raises(ValueError):
        r.index([])
