"""Tests for retrieval metric correctness against hand-computed values."""
import math

import pytest

from app.evaluation.metrics import (
    dedup_preserve_order,
    mean,
    ndcg_at_k,
    percentile,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_recall_at_k():
    retrieved = ["a", "b", "c", "d"]
    relevant = {"c", "z"}
    assert recall_at_k(retrieved, relevant, 2) == 0.0          # c not in top-2
    assert recall_at_k(retrieved, relevant, 3) == pytest.approx(0.5)  # found c of {c,z}
    assert recall_at_k(retrieved, relevant, 4) == pytest.approx(0.5)
    assert recall_at_k(retrieved, set(), 4) == 0.0


def test_precision_at_k():
    retrieved = ["a", "b", "c"]
    relevant = {"a", "c"}
    assert precision_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)
    assert precision_at_k(retrieved, relevant, 1) == 1.0
    assert precision_at_k([], relevant, 3) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["x", "y", "rel"], {"rel"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["rel", "y"], {"rel"}) == 1.0
    assert reciprocal_rank(["x", "y"], {"rel"}) == 0.0


def test_ndcg_perfect_and_partial():
    # perfect ranking -> nDCG = 1
    assert ndcg_at_k(["a", "b"], {"a", "b"}, 2) == pytest.approx(1.0)
    # single relevant at rank 2: DCG = 1/log2(3); IDCG = 1/log2(2)=1
    expected = (1 / math.log2(3)) / 1.0
    assert ndcg_at_k(["x", "a", "y"], {"a"}, 3) == pytest.approx(expected)
    assert ndcg_at_k(["x"], set(), 3) == 0.0


def test_dedup_preserve_order():
    assert dedup_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_mean_and_percentile():
    assert mean([]) == 0.0
    assert mean([1, 2, 3]) == 2.0
    assert percentile([10, 20, 30, 40], 50) == pytest.approx(25.0)
    assert percentile([5], 95) == 5.0
