"""Run ablation experiments and write reports/ablations.{md,csv} + a chart."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from app.config import settings  # noqa: E402
from app.evaluation.ablations import run_ablations  # noqa: E402


def _chart(df: pd.DataFrame, out: Path) -> None:
    experiments = df["experiment"].unique()
    fig, axes = plt.subplots(1, len(experiments), figsize=(4.2 * len(experiments), 4), squeeze=False)
    for ax, exp in zip(axes[0], experiments):
        sub = df[df["experiment"] == exp]
        ax.plot(range(len(sub)), sub["recall_at_5"], marker="o", label="Recall@5")
        ax.plot(range(len(sub)), sub["ndcg_at_5"], marker="s", label="nDCG@5")
        ax.set_xticks(range(len(sub)))
        ax.set_xticklabels(sub["setting"], rotation=30, ha="right", fontsize=8)
        ax.set_title(exp)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Ablation experiments")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main() -> int:
    settings.ensure_dirs()
    print("Running ablations (chunk size, overlap, hybrid weight, reranker)...")
    rows = run_ablations()
    df = pd.DataFrame(rows)

    df.to_csv(settings.reports_dir / "ablations.csv", index=False)
    _chart(df, settings.charts_dir / "ablations.png")

    lines = ["# Lexsearch EvalBench — Ablation Results\n"]
    for exp in df["experiment"].unique():
        sub = df[df["experiment"] == exp].drop(columns=["experiment"])
        lines.append(f"## {exp}\n")
        lines.append(sub.round(4).to_markdown(index=False))
        lines.append("")
    lines.append("![Ablations](charts/ablations.png)\n")
    (settings.reports_dir / "ablations.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n" + df.round(4).to_string(index=False))
    print("\n✅ Wrote reports/ablations.md, ablations.csv, charts/ablations.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
