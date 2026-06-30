"""Retrieval quality metrics: Recall@K, MRR, nDCG@K, context precision.

All functions operate on an ordered list of retrieved item ids and a set of
relevant ids. They are deterministic and unit-tested in tests/test_metrics.py.
"""
from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Set


def dedup_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def recall_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Fraction of relevant items that appear in the top-k retrieved items."""
    if not relevant:
        return 0.0
    topk = set(retrieved[:k])
    return len(topk & relevant) / len(relevant)


def precision_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Fraction of the top-k retrieved items that are relevant (context precision)."""
    if k <= 0:
        return 0.0
    topk = retrieved[:k]
    if not topk:
        return 0.0
    hits = sum(1 for r in topk if r in relevant)
    return hits / len(topk)


def reciprocal_rank(retrieved: Sequence[str], relevant: Set[str]) -> float:
    """1 / rank of the first relevant item (0 if none retrieved)."""
    for idx, item in enumerate(retrieved):
        if item in relevant:
            return 1.0 / (idx + 1)
    return 0.0


def dcg_at_k(gains: Sequence[float], k: int) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains[:k]))


def ndcg_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Binary-gain nDCG@k. IDCG assumes all relevant items ranked first."""
    if not relevant:
        return 0.0
    gains = [1.0 if item in relevant else 0.0 for item in retrieved[:k]]
    dcg = dcg_at_k(gains, k)
    ideal_hits = min(len(relevant), k)
    idcg = dcg_at_k([1.0] * ideal_hits, k)
    return dcg / idcg if idcg > 0 else 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: Sequence[float], pct: float) -> float:
    """Linear-interpolation percentile (pct in [0, 100])."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    rank = (pct / 100.0) * (len(s) - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return s[lo]
    frac = rank - lo
    return s[lo] * (1 - frac) + s[hi] * frac
