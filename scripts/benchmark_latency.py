"""Benchmark per-query latency for each retrieval method over the golden set."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from app.config import settings  # noqa: E402
from app.evaluation.evaluator import load_golden  # noqa: E402
from app.evaluation.metrics import mean, percentile  # noqa: E402
from app.retrieval.pipeline import METHODS, RetrievalPipeline  # noqa: E402


def main() -> int:
    settings.ensure_dirs()
    if RetrievalPipeline.index_exists():
        pipe = RetrievalPipeline.load()
    else:
        pipe = RetrievalPipeline()
        pipe.build_from_corpus()

    golden = load_golden()
    rows = []
    # warmup (loads embed/rerank models so they don't skew the first timing)
    pipe.retrieve(golden[0]["question"], method="hybrid_rerank", top_k=5)

    for method in METHODS:
        per_stage: dict[str, list[float]] = {}
        totals: list[float] = []
        for q in golden:
            _, timing = pipe.retrieve(q["question"], method=method, top_k=5)
            totals.append(timing["total_ms"])
            for stage, ms in timing.items():
                if stage == "total_ms":
                    continue
                per_stage.setdefault(stage, []).append(ms)
        row = {
            "method": method,
            "mean_ms": round(mean(totals), 3),
            "p50_ms": round(percentile(totals, 50), 3),
            "p95_ms": round(percentile(totals, 95), 3),
            "max_ms": round(max(totals), 3),
        }
        for stage, vals in per_stage.items():
            row[f"{stage}_ms(mean)"] = round(mean(vals), 3)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(settings.reports_dir / "latency.csv", index=False)
    print(df.to_string(index=False))
    print(f"\n✅ Wrote reports/latency.csv ({len(golden)} queries/method)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
