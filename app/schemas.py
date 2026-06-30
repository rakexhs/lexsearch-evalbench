"""Pydantic schemas shared by the API, pipeline, and storage layers."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Core domain objects ───────────────────────────────────────────────────────
class Document(BaseModel):
    doc_id: str
    title: str
    source: str = ""
    category: str = ""
    text: str


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    section: str = ""
    text: str
    position: int = 0
    metadata: Dict[str, str] = Field(default_factory=dict)


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float
    method_scores: Dict[str, float] = Field(default_factory=dict)
    rank: int = 0


# ── Retrieval / query ─────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    method: str = Field(default="hybrid_rerank", description="bm25 | dense | hybrid | hybrid_rerank")
    top_k: int = 5
    generate_answer: bool = True


class Citation(BaseModel):
    marker: str          # e.g. "[1]"
    chunk_id: str
    doc_id: str
    title: str
    supported: bool = True
    support_score: float = 0.0


class AnswerResult(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    faithfulness: float = 0.0
    backend: str = "mock"
    unsupported_sentences: List[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    query: str
    method: str
    results: List[ScoredChunk] = Field(default_factory=list)
    answer: Optional[AnswerResult] = None
    latency_ms: Dict[str, float] = Field(default_factory=dict)


# ── Ingestion ─────────────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    documents: Optional[List[Document]] = None
    rebuild: bool = True


class IngestResponse(BaseModel):
    num_documents: int
    num_chunks: int
    index_dir: str
    chunk_size: int
    chunk_overlap: int


# ── Evaluation ────────────────────────────────────────────────────────────────
class EvaluateRequest(BaseModel):
    methods: List[str] = Field(default_factory=lambda: ["bm25", "dense", "hybrid", "hybrid_rerank"])
    k_values: List[int] = Field(default_factory=lambda: [1, 3, 5, 10])
    limit: Optional[int] = None


class MethodMetrics(BaseModel):
    method: str
    num_questions: int
    recall_at_k: Dict[int, float] = Field(default_factory=dict)
    ndcg_at_k: Dict[int, float] = Field(default_factory=dict)
    mrr: float = 0.0
    context_precision: float = 0.0
    citation_faithfulness: float = 0.0
    mean_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0


class EvaluateResponse(BaseModel):
    results: List[MethodMetrics]
    num_questions: int


class HealthResponse(BaseModel):
    status: str
    indexed: bool
    num_chunks: int
    answer_backend: str
    embed_model: str
    dense_mode: str
    rerank_mode: str
