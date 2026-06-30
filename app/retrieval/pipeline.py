"""End-to-end retrieval pipeline orchestrating BM25, dense, hybrid, and rerank.

Supported methods:
  - "bm25"          : lexical only
  - "dense"         : embedding similarity only
  - "hybrid"        : RRF/weighted fusion of bm25 + dense
  - "hybrid_rerank" : hybrid candidate pool rescored by the cross-encoder reranker
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from app.config import settings
from app.ingestion.chunker import chunk_documents
from app.ingestion.loader import load_documents
from app.observability.logging_config import get_logger
from app.observability.timing import Timer
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import hybrid_search
from app.retrieval.reranker import Reranker
from app.schemas import Chunk, ScoredChunk

log = get_logger("pipeline")

METHODS = ["bm25", "dense", "hybrid", "hybrid_rerank"]
CANDIDATE_POOL = 30  # first-stage depth before fusion / reranking


class RetrievalPipeline:
    def __init__(
        self,
        fusion: str | None = None,
        hybrid_weight: float | None = None,
    ) -> None:
        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever()
        self.reranker = Reranker()
        self.chunks: List[Chunk] = []
        self.fusion = fusion or settings.fusion
        self.hybrid_weight = settings.hybrid_weight if hybrid_weight is None else hybrid_weight

    @property
    def num_chunks(self) -> int:
        return len(self.chunks)

    # ── building ──────────────────────────────────────────────────────────────
    def build(self, chunks: List[Chunk]) -> None:
        self.chunks = list(chunks)
        self.bm25.index(self.chunks)
        self.dense.index(self.chunks)

    def build_from_corpus(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        docs = load_documents()
        chunks = chunk_documents(docs, chunk_size, chunk_overlap)
        self.build(chunks)

    def save(self, index_dir: Path | None = None) -> None:
        index_dir = index_dir or settings.index_dir
        index_dir.mkdir(parents=True, exist_ok=True)
        self.bm25.save(index_dir)
        self.dense.save(index_dir)

    @classmethod
    def load(cls, index_dir: Path | None = None) -> "RetrievalPipeline":
        index_dir = index_dir or settings.index_dir
        obj = cls()
        obj.bm25 = BM25Retriever.load(index_dir)
        obj.dense = DenseRetriever.load(index_dir)
        obj.chunks = obj.bm25.chunks
        return obj

    @staticmethod
    def index_exists(index_dir: Path | None = None) -> bool:
        index_dir = index_dir or settings.index_dir
        return (index_dir / "bm25.pkl").exists() and (index_dir / "dense_meta.pkl").exists()

    # ── retrieval ───────────────────────────────────────────────────────────--
    def retrieve(
        self,
        query: str,
        method: str = "hybrid_rerank",
        top_k: int = 5,
    ) -> Tuple[List[ScoredChunk], Dict[str, float]]:
        if method not in METHODS:
            raise ValueError(f"Unknown method '{method}'. Choose from {METHODS}.")
        timer = Timer()
        pool = max(top_k, CANDIDATE_POOL)

        if method == "bm25":
            with timer.measure("bm25"):
                raw = self.bm25.search(query, top_k)
            results = [
                ScoredChunk(chunk=c, score=float(s), method_scores={"bm25": float(s)}, rank=i)
                for i, (c, s) in enumerate(raw)
            ]
            return results, timer.as_dict()

        if method == "dense":
            with timer.measure("dense"):
                raw = self.dense.search(query, top_k)
            results = [
                ScoredChunk(chunk=c, score=float(s), method_scores={"dense": float(s)}, rank=i)
                for i, (c, s) in enumerate(raw)
            ]
            return results, timer.as_dict()

        # hybrid + hybrid_rerank share the first stage
        with timer.measure("bm25"):
            bm25_raw = self.bm25.search(query, pool)
        with timer.measure("dense"):
            dense_raw = self.dense.search(query, pool)
        with timer.measure("fusion"):
            fused = hybrid_search(bm25_raw, dense_raw, pool, fusion=self.fusion, weight=self.hybrid_weight)

        if method == "hybrid":
            return self._reindex(fused[:top_k]), timer.as_dict()

        # hybrid_rerank
        with timer.measure("rerank"):
            reranked = self.reranker.rerank(query, fused, top_k)
        return reranked, timer.as_dict()

    @staticmethod
    def _reindex(results: List[ScoredChunk]) -> List[ScoredChunk]:
        for i, r in enumerate(results):
            r.rank = i
        return results

    def describe(self) -> Dict[str, str]:
        return {
            "dense_mode": self.dense.mode if self.dense.mode != "uninitialized" else "(lazy)",
            "rerank_mode": self.reranker.mode if self.reranker.mode != "uninitialized" else "(lazy)",
            "embed_model": self.dense.model_name,
            "fusion": self.fusion,
        }
