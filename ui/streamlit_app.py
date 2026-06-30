"""Lexsearch EvalBench — Streamlit dashboard.

Run with:  streamlit run ui/streamlit_app.py
Lets you build the index, ask queries, compare retrieval methods side-by-side,
inspect grounded answers with citations, and view evaluation metrics + charts.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.config import settings  # noqa: E402
from app.generation.answerer import generate_answer  # noqa: E402
from app.retrieval.pipeline import METHODS, RetrievalPipeline  # noqa: E402

st.set_page_config(page_title="Lexsearch EvalBench", page_icon="🔎", layout="wide")

METHOD_LABELS = {
    "bm25": "BM25 (lexical)",
    "dense": "Dense (embeddings)",
    "hybrid": "Hybrid (RRF)",
    "hybrid_rerank": "Hybrid + Cross-Encoder Rerank",
}


@st.cache_resource(show_spinner="Loading / building index...")
def get_pipeline() -> RetrievalPipeline | None:
    if RetrievalPipeline.index_exists():
        return RetrievalPipeline.load()
    return None


def build_index() -> RetrievalPipeline:
    pipe = RetrievalPipeline()
    pipe.build_from_corpus()
    pipe.save()
    return pipe


# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔎 Lexsearch EvalBench")
st.sidebar.caption("Agentic Domain RAG • Hybrid Retrieval • Reranking • Eval")

pipe = get_pipeline()
if pipe is None:
    st.sidebar.warning("No index found.")
    if st.sidebar.button("Build index from sample corpus", type="primary"):
        get_pipeline.clear()
        with st.spinner("Building BM25 + dense indexes..."):
            build_index()
        st.rerun()
else:
    desc = pipe.describe()
    st.sidebar.success(f"Index ready · {pipe.num_chunks} chunks")
    st.sidebar.write(f"**Dense:** {desc['dense_mode']}")
    st.sidebar.write(f"**Rerank:** {desc['rerank_mode']}")
    st.sidebar.write(f"**Fusion:** {desc['fusion']}")
    st.sidebar.write(f"**Answer backend:** {settings.answer_backend}")
    if st.sidebar.button("Rebuild index"):
        get_pipeline.clear()
        with st.spinner("Rebuilding..."):
            build_index()
        st.rerun()

st.sidebar.divider()
top_k = st.sidebar.slider("Top-K", 1, 10, 5)

tab_query, tab_compare, tab_eval = st.tabs(["💬 Query & Answer", "⚖️ Compare Methods", "📊 Evaluation"])


def render_chunk(sc, show_scores=True):
    c = sc.chunk
    with st.container(border=True):
        st.markdown(f"**`{c.doc_id}`** · *{c.title}* — _{c.section}_")
        st.write(c.text)
        if show_scores:
            scores = " · ".join(f"{k}={v:.3f}" for k, v in sc.method_scores.items())
            st.caption(f"rank {sc.rank} · {scores}")


# ── Query tab ─────────────────────────────────────────────────────────────────
with tab_query:
    st.subheader("Ask a question about the technical-docs corpus")
    method = st.selectbox("Retrieval method", METHODS, index=METHODS.index("hybrid_rerank"),
                          format_func=lambda m: METHOD_LABELS[m])
    query = st.text_input("Question", "How do I create a new branch and switch to it in one command?")
    go = st.button("Search", type="primary")

    if go and pipe is None:
        st.error("Build the index first (sidebar).")
    elif go and query.strip():
        results, timing = pipe.retrieve(query, method=method, top_k=top_k)
        answer = generate_answer(query, results, backend=settings.answer_backend)

        left, right = st.columns([3, 2])
        with left:
            st.markdown("### Grounded answer")
            st.info(answer.answer)
            faith_color = "green" if answer.faithfulness >= 0.8 else ("orange" if answer.faithfulness >= 0.5 else "red")
            st.markdown(f"**Faithfulness:** :{faith_color}[{answer.faithfulness:.2f}] · backend: `{answer.backend}`")
            if answer.citations:
                st.markdown("#### Citations")
                for cit in answer.citations:
                    flag = "✅" if cit.supported else "⚠️"
                    st.markdown(f"{flag} {cit.marker} `{cit.doc_id}` — {cit.title} (support={cit.support_score:.2f})")
            if answer.unsupported_sentences:
                st.warning("Unsupported sentences flagged: " + " / ".join(answer.unsupported_sentences))
        with right:
            st.markdown("### Latency (ms)")
            st.json(timing)

        st.markdown("### Retrieved chunks")
        for sc in results:
            render_chunk(sc)


# ── Compare tab ───────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("Compare BM25 vs Dense vs Hybrid vs Hybrid+Rerank")
    cquery = st.text_input("Question to compare", "Why does BM25 complement dense retrieval in hybrid search?",
                           key="compare_q")
    cgo = st.button("Compare", type="primary", key="compare_btn")
    if cgo and pipe is None:
        st.error("Build the index first (sidebar).")
    elif cgo and cquery.strip():
        cols = st.columns(len(METHODS))
        for col, m in zip(cols, METHODS):
            results, timing = pipe.retrieve(cquery, method=m, top_k=top_k)
            with col:
                st.markdown(f"#### {METHOD_LABELS[m]}")
                st.caption(f"total {timing['total_ms']:.1f} ms")
                for sc in results:
                    st.markdown(f"`{sc.chunk.doc_id}` · score {sc.score:.3f}")
                    st.caption(sc.chunk.section)


# ── Eval tab ──────────────────────────────────────────────────────────────────
with tab_eval:
    st.subheader("Evaluation metrics")
    results_csv = settings.reports_dir / "results.csv"
    if results_csv.exists():
        df = pd.read_csv(results_csv)
        st.dataframe(df, use_container_width=True)
        for name in ["recall_at_k.png", "metrics_bars.png", "latency.png"]:
            p = settings.charts_dir / name
            if p.exists():
                st.image(str(p))
    else:
        st.info("No evaluation results yet. Run `make eval` (or `python scripts/run_eval.py`).")

    abl_csv = settings.reports_dir / "ablations.csv"
    if abl_csv.exists():
        st.markdown("### Ablations")
        st.dataframe(pd.read_csv(abl_csv), use_container_width=True)
        abl_png = settings.charts_dir / "ablations.png"
        if abl_png.exists():
            st.image(str(abl_png))
