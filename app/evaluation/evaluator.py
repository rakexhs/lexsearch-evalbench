"""Evaluator: runs golden questions through each retrieval method and aggregates
Recall@K, MRR, nDCG@K, context precision, citation faithfulness, and latency.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.evaluation import metrics as M
from app.generation.answerer import generate_answer
from app.observability.logging_config import get_logger
from app.retrieval.pipeline import RetrievalPipeline
from app.schemas import MethodMetrics

log = get_logger("evaluator")

DEFAULT_METHODS = ["bm25", "dense", "hybrid", "hybrid_rerank"]
DEFAULT_K = [1, 3, 5, 10]
CONTEXT_PRECISION_K = 5


def load_golden(path: Path | None = None) -> List[dict]:
    path = path or (settings.eval_dir / "golden_questions.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Golden set {path} not found. Run `make sample-data` first.")
    out: List[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


@dataclass
class QuestionRecord:
    qid: str
    method: str
    retrieved_doc_ids: List[str]
    relevant_doc_ids: List[str]
    hit: bool
    reciprocal_rank: float
    recall_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]
    context_precision: float
    faithfulness: float
    latency_ms: float
    latency_breakdown: Dict[str, float] = field(default_factory=dict)


def evaluate_method(
    pipeline: RetrievalPipeline,
    golden: List[dict],
    method: str,
    k_values: List[int],
    with_answers: bool = True,
) -> tuple[MethodMetrics, List[QuestionRecord]]:
    max_k = max(k_values)
    records: List[QuestionRecord] = []

    # Warm up models for this method so the first query's cold-start (model load /
    # first encode) does not skew the reported latency. Untimed and discarded.
    if golden:
        pipeline.retrieve(golden[0]["question"], method=method, top_k=max_k)

    recalls: Dict[int, List[float]] = {k: [] for k in k_values}
    ndcgs: Dict[int, List[float]] = {k: [] for k in k_values}
    rrs: List[float] = []
    precisions: List[float] = []
    faiths: List[float] = []
    latencies: List[float] = []

    for q in golden:
        relevant = set(q["relevant_doc_ids"])
        results, timing = pipeline.retrieve(q["question"], method=method, top_k=max_k)
        retrieved_doc_ids = M.dedup_preserve_order([r.chunk.doc_id for r in results])

        rr = M.reciprocal_rank(retrieved_doc_ids, relevant)
        rec_k = {k: M.recall_at_k(retrieved_doc_ids, relevant, k) for k in k_values}
        ndcg_k = {k: M.ndcg_at_k(retrieved_doc_ids, relevant, k) for k in k_values}
        ctx_p = M.precision_at_k(retrieved_doc_ids, relevant, CONTEXT_PRECISION_K)

        faith = 0.0
        if with_answers:
            ans = generate_answer(q["question"], results[:5], backend="mock")
            faith = ans.faithfulness

        latency = timing.get("total_ms", 0.0)

        rrs.append(rr)
        precisions.append(ctx_p)
        faiths.append(faith)
        latencies.append(latency)
        for k in k_values:
            recalls[k].append(rec_k[k])
            ndcgs[k].append(ndcg_k[k])

        records.append(
            QuestionRecord(
                qid=q["id"],
                method=method,
                retrieved_doc_ids=retrieved_doc_ids[:max_k],
                relevant_doc_ids=list(relevant),
                hit=rr > 0,
                reciprocal_rank=rr,
                recall_at_k=rec_k,
                ndcg_at_k=ndcg_k,
                context_precision=ctx_p,
                faithfulness=faith,
                latency_ms=latency,
                latency_breakdown=timing,
            )
        )

    mm = MethodMetrics(
        method=method,
        num_questions=len(golden),
        recall_at_k={k: round(M.mean(recalls[k]), 4) for k in k_values},
        ndcg_at_k={k: round(M.mean(ndcgs[k]), 4) for k in k_values},
        mrr=round(M.mean(rrs), 4),
        context_precision=round(M.mean(precisions), 4),
        citation_faithfulness=round(M.mean(faiths), 4),
        mean_latency_ms=round(M.mean(latencies), 3),
        p95_latency_ms=round(M.percentile(latencies, 95), 3),
    )
    return mm, records


def evaluate_all(
    pipeline: RetrievalPipeline,
    methods: Optional[List[str]] = None,
    k_values: Optional[List[int]] = None,
    limit: Optional[int] = None,
    with_answers: bool = True,
) -> tuple[List[MethodMetrics], List[QuestionRecord]]:
    methods = methods or DEFAULT_METHODS
    k_values = k_values or DEFAULT_K
    golden = load_golden()
    if limit:
        golden = golden[:limit]

    all_metrics: List[MethodMetrics] = []
    all_records: List[QuestionRecord] = []
    for method in methods:
        log.info("Evaluating method=%s on %d questions", method, len(golden))
        mm, recs = evaluate_method(pipeline, golden, method, k_values, with_answers)
        all_metrics.append(mm)
        all_records.extend(recs)
    return all_metrics, all_records
