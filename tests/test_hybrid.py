"""Tests for hybrid fusion and the end-to-end pipeline."""
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import reciprocal_rank_fusion, weighted_fusion
from app.retrieval.pipeline import METHODS, RetrievalPipeline


def _raw(retriever, query, k):
    return retriever.search(query, k)


def test_rrf_shapes_and_scores(chunks):
    bm = BM25Retriever(); bm.index(chunks)
    de = DenseRetriever(); de.index(chunks)
    q = "merge branches in git"
    fused = reciprocal_rank_fusion(_raw(bm, q, 10), _raw(de, q, 10), top_k=5)
    assert len(fused) == 5
    assert [s.rank for s in fused] == [0, 1, 2, 3, 4]
    assert all("rrf" in s.method_scores for s in fused)
    assert fused[0].score >= fused[-1].score


def test_weighted_fusion_weight_extremes(chunks):
    bm = BM25Retriever(); bm.index(chunks)
    de = DenseRetriever(); de.index(chunks)
    q = "python virtual environment activation"
    only_dense = weighted_fusion(_raw(bm, q, 10), _raw(de, q, 10), top_k=5, weight=1.0)
    only_bm25 = weighted_fusion(_raw(bm, q, 10), _raw(de, q, 10), top_k=5, weight=0.0)
    # weight=1.0 -> ordering follows dense top result; weight=0 -> follows bm25 top
    assert only_dense[0].chunk.chunk_id == de.search(q, 1)[0][0].chunk_id
    assert only_bm25[0].chunk.chunk_id == bm.search(q, 1)[0][0].chunk_id


def test_pipeline_all_methods(chunks):
    pipe = RetrievalPipeline()
    pipe.build(chunks)
    for method in METHODS:
        results, timing = pipe.retrieve("how does reranking improve precision", method=method, top_k=5)
        assert 1 <= len(results) <= 5
        assert [r.rank for r in results] == list(range(len(results)))
        assert "total_ms" in timing


def test_rerank_changes_or_preserves_but_returns_topk(chunks):
    pipe = RetrievalPipeline()
    pipe.build(chunks)
    hy, _ = pipe.retrieve("BM25 rare term exact keyword matching", method="hybrid", top_k=5)
    hr, _ = pipe.retrieve("BM25 rare term exact keyword matching", method="hybrid_rerank", top_k=5)
    assert len(hr) == 5
    # reranker writes a 'rerank' score on every returned candidate
    assert all("rerank" in r.method_scores for r in hr)
