"""Hybrid fusion of BM25 and dense rankings (RRF or weighted score fusion)."""
from __future__ import annotations

from typing import Dict, List, Tuple

from app.schemas import Chunk, ScoredChunk

RRF_K = 60  # standard reciprocal-rank-fusion constant


def _minmax(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return {k: 0.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def reciprocal_rank_fusion(
    bm25: List[Tuple[Chunk, float]],
    dense: List[Tuple[Chunk, float]],
    top_k: int,
    k: int = RRF_K,
) -> List[ScoredChunk]:
    chunk_by_id: Dict[str, Chunk] = {}
    rrf: Dict[str, float] = {}
    method_scores: Dict[str, Dict[str, float]] = {}

    for rank, (chunk, score) in enumerate(bm25):
        chunk_by_id[chunk.chunk_id] = chunk
        rrf[chunk.chunk_id] = rrf.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank + 1)
        method_scores.setdefault(chunk.chunk_id, {})["bm25"] = float(score)

    for rank, (chunk, score) in enumerate(dense):
        chunk_by_id[chunk.chunk_id] = chunk
        rrf[chunk.chunk_id] = rrf.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank + 1)
        method_scores.setdefault(chunk.chunk_id, {})["dense"] = float(score)

    ordered = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]
    out: List[ScoredChunk] = []
    for rank, (cid, fused) in enumerate(ordered):
        out.append(
            ScoredChunk(
                chunk=chunk_by_id[cid],
                score=float(fused),
                method_scores={**method_scores.get(cid, {}), "rrf": float(fused)},
                rank=rank,
            )
        )
    return out


def weighted_fusion(
    bm25: List[Tuple[Chunk, float]],
    dense: List[Tuple[Chunk, float]],
    top_k: int,
    weight: float = 0.5,
) -> List[ScoredChunk]:
    """Weighted sum of min-max normalized scores. `weight` is the dense weight:
    final = weight * dense_norm + (1 - weight) * bm25_norm."""
    bm25_scores = {c.chunk_id: s for c, s in bm25}
    dense_scores = {c.chunk_id: s for c, s in dense}
    chunk_by_id: Dict[str, Chunk] = {c.chunk_id: c for c, _ in bm25}
    chunk_by_id.update({c.chunk_id: c for c, _ in dense})

    bm25_norm = _minmax(bm25_scores)
    dense_norm = _minmax(dense_scores)

    fused: Dict[str, float] = {}
    for cid in chunk_by_id:
        b = bm25_norm.get(cid, 0.0)
        d = dense_norm.get(cid, 0.0)
        fused[cid] = weight * d + (1.0 - weight) * b

    ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
    out: List[ScoredChunk] = []
    for rank, (cid, score) in enumerate(ordered):
        ms = {"weighted": float(score)}
        if cid in bm25_scores:
            ms["bm25"] = float(bm25_scores[cid])
        if cid in dense_scores:
            ms["dense"] = float(dense_scores[cid])
        out.append(ScoredChunk(chunk=chunk_by_id[cid], score=float(score), method_scores=ms, rank=rank))
    return out


def hybrid_search(
    bm25: List[Tuple[Chunk, float]],
    dense: List[Tuple[Chunk, float]],
    top_k: int,
    fusion: str = "rrf",
    weight: float = 0.5,
) -> List[ScoredChunk]:
    if fusion == "weighted":
        return weighted_fusion(bm25, dense, top_k, weight)
    return reciprocal_rank_fusion(bm25, dense, top_k)
