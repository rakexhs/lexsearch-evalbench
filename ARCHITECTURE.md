# Architecture

Lexsearch EvalBench is a small, layered library (`app/`) with thin entry points
(`scripts/`, `ui/`, `app/main.py`). Every layer is independently testable and has
no hidden global state beyond a cached `Settings` object.

## Layered design

```
config / observability   ← cross-cutting (settings, logging, timing)
        │
ingestion                ← loader → chunker → sample_corpus
        │
retrieval                ← bm25 + dense → hybrid fusion → reranker → pipeline
        │
generation               ← answerer (mock/LLM adapters) + citation_checker
        │
evaluation               ← metrics → evaluator → ablations
        │
storage                  ← SQLite (documents, chunks, eval_runs)
        │
interfaces               ← FastAPI (app/main.py) · Streamlit (ui) · scripts
```

## Module responsibilities

### `app/config.py`
A single `Settings` dataclass, environment-overridable via `.env`, cached with
`lru_cache`. Holds paths, chunking params, retrieval params, model names, the answer
backend, and an `offline` flag. All other modules read from `settings` rather than
re-reading the environment.

### `app/ingestion/`
- **`sample_corpus.py`** — the corpus and golden set as structured Python data, plus
  `materialize()` (writes `data/raw/*.md` + `data/eval/golden_questions.jsonl`) and
  `validate()`. Keeping it in code means the repo runs with zero downloads.
- **`loader.py`** — parses markdown into `Document`s (title from `# H1`, category from
  an HTML comment, body stripped of both).
- **`chunker.py`** — section-aware (`## headers`) windowing on character size with
  word-boundary cuts and configurable overlap; emits `Chunk`s carrying
  `doc_id/title/section/position/metadata`. Overlap ≥ size is clamped to avoid
  pathological loops.

### `app/retrieval/`
- **`bm25.py`** — `rank-bm25` with an identifier-aware tokenizer (keeps
  `requirements.txt`, `git.checkout` intact). Picklable persistence.
- **`dense.py`** — sentence-transformers embeddings with **mode locking**: the backend
  ("sentence-transformers" or the deterministic "hashing" fallback) is decided at
  index-build time and honoured for every query, so index and query vectors always
  share a dimensionality. Embeddings persisted as `.npy` + metadata.
- **`hybrid.py`** — Reciprocal Rank Fusion (default, parameter-free and robust) and
  weighted min-max score fusion (tunable dense weight). Returns `ScoredChunk`s with
  per-method scores attached.
- **`reranker.py`** — cross-encoder rescoring with a deterministic lexical-overlap
  fallback when the model can't load. Reports its active `mode`.
- **`pipeline.py`** — orchestrates the four methods (`bm25`, `dense`, `hybrid`,
  `hybrid_rerank`), times each stage, fetches a 30-candidate first-stage pool before
  fusion/rerank, and handles persistence/loading. The single object the API, UI,
  scripts, and evaluator all share.

### `app/generation/`
- **`answerer.py`** — default **mock** backend is *extractive*: it scores sentences
  from retrieved chunks by query overlap + retrieval-rank prior, emits the top few
  with `[n]` citation markers, and therefore cannot hallucinate. Optional
  OpenAI/Anthropic/Ollama adapters share a strict grounding prompt and fall back to
  mock on any failure. Every backend's output is faithfulness-checked.
- **`citation_checker.py`** — splits the answer into sentences (marker-aware), and for
  each sentence measures the fraction of its content tokens (stopwords removed) present
  in the cited evidence. Yields a per-sentence support score, supported/unsupported
  flags, and an aggregate faithfulness.

### `app/evaluation/`
- **`metrics.py`** — pure functions: `recall_at_k`, `precision_at_k`,
  `reciprocal_rank`, `ndcg_at_k`, plus `mean`/`percentile`. Unit-tested against
  hand-computed values.
- **`evaluator.py`** — runs the golden set through a method, warms models before
  timing, aggregates per-method `MethodMetrics`, and returns per-question records for
  error analysis.
- **`ablations.py`** — one-knob-at-a-time sweeps over chunk size, overlap, hybrid
  weight, and reranker on/off, rebuilding the pipeline per setting.

### `app/storage/`
SQLite (`models.py` DDL, `db.py` access) for `documents`, `chunks`, and `eval_runs`
(each run stores the full metrics payload as JSON for `/metrics`).

### `app/observability/`
`logging_config.py` (shared formatter) and `timing.py` (`Timer` context manager that
accumulates per-stage milliseconds, surfaced in every query response).

## Request flow (`POST /query`)

```
query ─► pipeline.retrieve(method)
            ├─ bm25.search ─┐
            ├─ dense.search ┘─► hybrid_search (RRF/weighted) ─► reranker.rerank
            └─ Timer records bm25/dense/fusion/rerank ms
        ─► answerer.generate_answer(top-k)
            └─ citation_checker verifies each sentence ─► faithfulness + flags
        ─► QueryResponse{results, answer, citations, latency_ms}
```

## Design decisions & trade-offs

- **Graceful degradation over hard dependency.** Dense and rerank both have
  deterministic offline fallbacks, so CI and no-network demos always work; mode is
  reported so results are never silently misattributed.
- **RRF as the default fusion.** Parameter-free and robust; weighted fusion is offered
  for tuning (and the ablation shows 0.75 dense is best on this corpus).
- **Extractive default answerer.** Trades fluency for guaranteed faithfulness and a
  zero-key demo; LLM adapters are opt-in for abstractive synthesis.
- **Document-level metrics by default.** Simpler, robust labels; chunk-level labels are
  in the schema for future graded evaluation.
- **Test isolation.** `tests/conftest.py` forces offline mode and points the index/DB
  at a temp dir so the suite never clobbers the real `make index` artifacts.
- **Stable contracts.** Pydantic schemas (`app/schemas.py`) are the shared interface
  across pipeline, API, storage, and UI.
