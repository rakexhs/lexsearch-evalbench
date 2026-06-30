"""FastAPI backend for Lexsearch EvalBench.

Endpoints:
  GET  /health    - liveness + index/model status
  POST /ingest    - (re)build the corpus index from disk or supplied documents
  POST /query     - retrieve + (optionally) generate a grounded, cited answer
  POST /evaluate  - run the evaluation harness across methods
  GET  /metrics   - return the most recent evaluation metrics
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.evaluation.evaluator import evaluate_all
from app.generation.answerer import generate_answer
from app.ingestion.chunker import chunk_documents
from app.ingestion.loader import load_documents
from app.observability.logging_config import get_logger
from app.retrieval.pipeline import RetrievalPipeline
from app.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from app.storage import db

log = get_logger("api")


class AppState:
    pipeline: Optional[RetrievalPipeline] = None


state = AppState()


def _load_or_none() -> Optional[RetrievalPipeline]:
    if RetrievalPipeline.index_exists():
        try:
            return RetrievalPipeline.load()
        except Exception as exc:  # pragma: no cover
            log.warning("Could not load existing index: %s", exc)
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    db.init_db()
    state.pipeline = _load_or_none()
    if state.pipeline:
        log.info("Loaded index with %d chunks", state.pipeline.num_chunks)
    else:
        log.info("No index found. POST /ingest or run `make index`.")
    yield


app = FastAPI(title="Lexsearch EvalBench", version="1.0.0", lifespan=lifespan)


def _require_pipeline() -> RetrievalPipeline:
    if state.pipeline is None:
        state.pipeline = _load_or_none()
    if state.pipeline is None:
        raise HTTPException(status_code=409, detail="No index built. Call POST /ingest or run `make index`.")
    return state.pipeline


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    pipe = state.pipeline
    desc = pipe.describe() if pipe else {}
    return HealthResponse(
        status="ok",
        indexed=pipe is not None,
        num_chunks=pipe.num_chunks if pipe else 0,
        answer_backend=settings.answer_backend,
        embed_model=settings.embed_model,
        dense_mode=desc.get("dense_mode", "(none)"),
        rerank_mode=desc.get("rerank_mode", "(none)"),
    )


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    if req.documents:
        docs = req.documents
    else:
        docs = load_documents()
    chunks = chunk_documents(docs)
    pipe = RetrievalPipeline()
    pipe.build(chunks)
    pipe.save()
    db.store_corpus(docs, chunks)
    state.pipeline = pipe
    return IngestResponse(
        num_documents=len(docs),
        num_chunks=len(chunks),
        index_dir=str(settings.index_dir),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    pipe = _require_pipeline()
    try:
        results, timing = pipe.retrieve(req.query, method=req.method, top_k=req.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    answer = None
    if req.generate_answer:
        answer = generate_answer(req.query, results, backend=settings.answer_backend)
    return QueryResponse(query=req.query, method=req.method, results=results, answer=answer, latency_ms=timing)


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    pipe = _require_pipeline()
    metrics, _ = evaluate_all(pipe, methods=req.methods, k_values=req.k_values, limit=req.limit)
    db.record_eval(metrics)
    return EvaluateResponse(results=metrics, num_questions=metrics[0].num_questions if metrics else 0)


@app.get("/metrics")
def metrics() -> dict:
    latest = db.latest_eval()
    return {"results": latest, "num_methods": len(latest)}
