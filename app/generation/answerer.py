"""Grounded answer generation with citations.

Default backend is "mock": a fully local, deterministic *extractive* answerer that
selects the answer sentences most relevant to the query from the retrieved chunks
and attaches citation markers. Because it only emits sentences taken from the
evidence, it cannot hallucinate unsupported claims.

Optional backends (openai | anthropic | ollama) are supported via adapters and are
only used when explicitly configured; they receive a strict grounding prompt. All
backends run citation faithfulness checking on their output.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import Dict, List, Tuple

from app.config import settings
from app.generation.citation_checker import _content_tokens, check_faithfulness, split_sentences
from app.observability.logging_config import get_logger
from app.schemas import AnswerResult, Citation, ScoredChunk

log = get_logger("answerer")

MAX_CITATIONS = 4
MAX_ANSWER_SENTENCES = 3


def _query_overlap(query: str, sentence: str) -> float:
    q = Counter(_content_tokens(query))
    if not q:
        return 0.0
    s = set(_content_tokens(sentence))
    hit = sum(c for tok, c in q.items() if tok in s)
    return hit / sum(q.values())


def _select_evidence_sentences(query: str, results: List[ScoredChunk]) -> List[Tuple[str, ScoredChunk, float]]:
    """Return (sentence, source_chunk, score) sorted by relevance to the query."""
    scored: List[Tuple[str, ScoredChunk, float]] = []
    for sc in results:
        for sent in split_sentences(sc.chunk.text):
            if len(sent) < 15:
                continue
            rel = _query_overlap(query, sent)
            # blend sentence relevance with retrieval rank prior
            rank_prior = 1.0 / (1.0 + sc.rank)
            scored.append((sent, sc, rel * 0.8 + rank_prior * 0.2))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored


def _build_extractive_answer(query: str, results: List[ScoredChunk]) -> Tuple[str, List[Citation], Dict[str, str]]:
    selected = _select_evidence_sentences(query, results)
    if not selected or selected[0][2] <= 0.0:
        return (
            "I could not find supporting information for this question in the retrieved context.",
            [],
            {},
        )

    # assign citation markers per source chunk, dedup sentences
    marker_by_chunk: Dict[str, str] = {}
    citations: List[Citation] = []
    evidence_by_marker: Dict[str, str] = {}
    answer_parts: List[str] = []
    used_text: set[str] = set()

    for sent, sc, score in selected:
        if len(answer_parts) >= MAX_ANSWER_SENTENCES:
            break
        if score <= 0.0:
            break
        key = sent.lower()[:60]
        if key in used_text:
            continue
        used_text.add(key)

        cid = sc.chunk.chunk_id
        if cid not in marker_by_chunk:
            if len(marker_by_chunk) >= MAX_CITATIONS:
                continue
            marker = f"[{len(marker_by_chunk) + 1}]"
            marker_by_chunk[cid] = marker
            evidence_by_marker[marker] = sc.chunk.text
            citations.append(
                Citation(
                    marker=marker,
                    chunk_id=cid,
                    doc_id=sc.chunk.doc_id,
                    title=sc.chunk.title,
                )
            )
        marker = marker_by_chunk[cid]
        sent_clean = sent.rstrip()
        if not sent_clean.endswith((".", "!", "?")):
            sent_clean += "."
        answer_parts.append(f"{sent_clean} {marker}")

    answer = " ".join(answer_parts)
    return answer, citations, evidence_by_marker


# ── optional LLM backends ─────────────────────────────────────────────────────
def _grounding_prompt(query: str, results: List[ScoredChunk]) -> str:
    ctx = "\n\n".join(f"[{i + 1}] (doc: {r.chunk.doc_id}) {r.chunk.text}" for i, r in enumerate(results[:MAX_CITATIONS]))
    return (
        "You answer strictly from the provided context. If the answer is not in the "
        "context, say you don't know. Cite sources inline with bracket markers like [1].\n\n"
        f"Context:\n{ctx}\n\nQuestion: {query}\nGrounded answer with citations:"
    )


def _openai_answer(query: str, results: List[ScoredChunk]) -> str:  # pragma: no cover - needs key
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": _grounding_prompt(query, results)}],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()


def _anthropic_answer(query: str, results: List[ScoredChunk]) -> str:  # pragma: no cover - needs key
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=512,
        messages=[{"role": "user", "content": _grounding_prompt(query, results)}],
    )
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text").strip()


def _ollama_answer(query: str, results: List[ScoredChunk]) -> str:  # pragma: no cover - needs server
    import requests

    resp = requests.post(
        f"{settings.ollama_host}/api/generate",
        json={"model": settings.ollama_model, "prompt": _grounding_prompt(query, results), "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def _build_citations_for_llm(answer: str, results: List[ScoredChunk]) -> Tuple[List[Citation], Dict[str, str]]:
    citations: List[Citation] = []
    evidence_by_marker: Dict[str, str] = {}
    cited_markers = set(re.findall(r"\[(\d+)\]", answer))
    for i, r in enumerate(results[:MAX_CITATIONS]):
        marker = f"[{i + 1}]"
        if str(i + 1) not in cited_markers:
            continue
        evidence_by_marker[marker] = r.chunk.text
        citations.append(Citation(marker=marker, chunk_id=r.chunk.chunk_id, doc_id=r.chunk.doc_id, title=r.chunk.title))
    return citations, evidence_by_marker


# ── public API ────────────────────────────────────────────────────────────────
def generate_answer(query: str, results: List[ScoredChunk], backend: str | None = None) -> AnswerResult:
    backend = (backend or settings.answer_backend or "mock").lower()
    if not results:
        return AnswerResult(answer="No relevant context was retrieved.", backend=backend, faithfulness=0.0)

    try:
        if backend == "openai" and os.environ.get("OPENAI_API_KEY"):
            text = _openai_answer(query, results)
            citations, evidence = _build_citations_for_llm(text, results)
        elif backend == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
            text = _anthropic_answer(query, results)
            citations, evidence = _build_citations_for_llm(text, results)
        elif backend == "ollama":
            text = _ollama_answer(query, results)
            citations, evidence = _build_citations_for_llm(text, results)
        else:
            backend = "mock"
            text, citations, evidence = _build_extractive_answer(query, results)
    except Exception as exc:  # graceful degradation to mock on any backend failure
        log.warning("Answer backend '%s' failed (%s); falling back to mock.", backend, exc)
        backend = "mock"
        text, citations, evidence = _build_extractive_answer(query, results)

    report = check_faithfulness(text, evidence)
    # attach per-citation support: a citation is "supported" if any sentence citing it passes
    support_by_marker: Dict[str, float] = {}
    for ps in report.per_sentence:
        for m in re.findall(r"\[(\d+)\]", ps["sentence"]):
            mk = f"[{m}]"
            support_by_marker[mk] = max(support_by_marker.get(mk, 0.0), ps["support"])
    for c in citations:
        c.support_score = round(support_by_marker.get(c.marker, 0.0), 3)
        c.supported = c.support_score >= 0.5

    return AnswerResult(
        answer=text,
        citations=citations,
        faithfulness=report.faithfulness,
        backend=backend,
        unsupported_sentences=report.unsupported_sentences,
    )
