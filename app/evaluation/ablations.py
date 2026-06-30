"""Ablation experiments over chunking and fusion hyperparameters.

Each experiment varies one knob and reports the impact on key retrieval metrics so
the README can show *what actually moves the needle*.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

from app.config import settings
from app.evaluation.evaluator import evaluate_method, load_golden
from app.ingestion.chunker import chunk_documents
from app.ingestion.loader import load_documents
from app.observability.logging_config import get_logger
from app.retrieval.pipeline import RetrievalPipeline

log = get_logger("ablations")

K_VALUES = [1, 3, 5, 10]
REPORT_K = 5


@dataclass
class AblationRow:
    experiment: str
    setting: str
    method: str
    recall_at_5: float
    ndcg_at_5: float
    mrr: float
    context_precision: float
    faithfulness: float
    mean_latency_ms: float


def _build_pipeline(chunk_size: int, chunk_overlap: int, fusion: str, weight: float) -> RetrievalPipeline:
    docs = load_documents()
    chunks = chunk_documents(docs, chunk_size, chunk_overlap)
    pipe = RetrievalPipeline(fusion=fusion, hybrid_weight=weight)
    pipe.build(chunks)
    return pipe


def _row(experiment: str, setting: str, method: str, mm) -> AblationRow:
    return AblationRow(
        experiment=experiment,
        setting=setting,
        method=method,
        recall_at_5=mm.recall_at_k.get(REPORT_K, 0.0),
        ndcg_at_5=mm.ndcg_at_k.get(REPORT_K, 0.0),
        mrr=mm.mrr,
        context_precision=mm.context_precision,
        faithfulness=mm.citation_faithfulness,
        mean_latency_ms=mm.mean_latency_ms,
    )


def run_ablations(limit: int | None = None) -> List[Dict]:
    golden = load_golden()
    if limit:
        golden = golden[:limit]

    rows: List[AblationRow] = []

    # ── Experiment 1: chunk size (overlap fixed) ─────────────────────────────
    for size in [300, 550, 800, 1200]:
        pipe = _build_pipeline(size, settings.chunk_overlap, "rrf", settings.hybrid_weight)
        mm, _ = evaluate_method(pipe, golden, "hybrid_rerank", K_VALUES, with_answers=True)
        rows.append(_row("chunk_size", f"size={size}", "hybrid_rerank", mm))
        log.info("chunk_size=%s recall@5=%.3f", size, mm.recall_at_k[REPORT_K])

    # ── Experiment 2: chunk overlap (size fixed) ─────────────────────────────
    for overlap in [0, 40, 80, 160]:
        pipe = _build_pipeline(settings.chunk_size, overlap, "rrf", settings.hybrid_weight)
        mm, _ = evaluate_method(pipe, golden, "hybrid_rerank", K_VALUES, with_answers=True)
        rows.append(_row("chunk_overlap", f"overlap={overlap}", "hybrid_rerank", mm))
        log.info("chunk_overlap=%s recall@5=%.3f", overlap, mm.recall_at_k[REPORT_K])

    # ── Experiment 3: hybrid weight (weighted fusion, dense weight) ───────────
    base = _build_pipeline(settings.chunk_size, settings.chunk_overlap, "weighted", settings.hybrid_weight)
    for w in [0.0, 0.25, 0.5, 0.75, 1.0]:
        base.fusion = "weighted"
        base.hybrid_weight = w
        mm, _ = evaluate_method(base, golden, "hybrid", K_VALUES, with_answers=False)
        rows.append(_row("hybrid_weight", f"dense_weight={w}", "hybrid", mm))
        log.info("hybrid_weight=%s recall@5=%.3f", w, mm.recall_at_k[REPORT_K])

    # ── Experiment 4: reranker on/off ────────────────────────────────────────
    rrf_pipe = _build_pipeline(settings.chunk_size, settings.chunk_overlap, "rrf", settings.hybrid_weight)
    for method, label in [("hybrid", "reranker=off"), ("hybrid_rerank", "reranker=on")]:
        mm, _ = evaluate_method(rrf_pipe, golden, method, K_VALUES, with_answers=True)
        rows.append(_row("reranker", label, method, mm))
        log.info("%s recall@5=%.3f ndcg@5=%.3f", label, mm.recall_at_k[REPORT_K], mm.ndcg_at_k[REPORT_K])

    return [asdict(r) for r in rows]
