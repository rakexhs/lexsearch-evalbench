"""Cross-encoder reranker with a deterministic lexical fallback.

If the cross-encoder model can be loaded (sentence-transformers), candidates are
rescored with it. Otherwise a deterministic lexical-overlap reranker is used so the
two-stage pipeline still improves precision offline. `mode` reports the active path.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import List

from app.config import settings
from app.observability.logging_config import get_logger
from app.schemas import ScoredChunk

log = get_logger("reranker")

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


class Reranker:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.rerank_model
        self.mode = "uninitialized"
        self._model = None

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        if settings.offline:
            return False
        try:
            from sentence_transformers import CrossEncoder  # type: ignore

            self._model = CrossEncoder(self.model_name)
            return True
        except Exception as exc:  # pragma: no cover - depends on env
            log.warning("Falling back to lexical reranker (could not load '%s': %s)", self.model_name, exc)
            return False

    # ── deterministic lexical reranker ────────────────────────────────────────
    @staticmethod
    def _lexical_score(query: str, text: str) -> float:
        q = Counter(_tokens(query))
        d = Counter(_tokens(text))
        if not q or not d:
            return 0.0
        # weighted token overlap, idf-ish damping by query token rarity in the doc
        overlap = sum(min(qc, d.get(tok, 0)) for tok, qc in q.items())
        coverage = sum(1 for tok in q if tok in d) / len(q)
        length_penalty = 1.0 / (1.0 + math.log(1 + len(d)))
        return overlap * (0.5 + coverage) * (0.5 + length_penalty)

    def rerank(self, query: str, candidates: List[ScoredChunk], top_k: int | None = None) -> List[ScoredChunk]:
        if not candidates:
            return []
        top_k = top_k or len(candidates)

        if self._ensure_model():
            self.mode = "cross-encoder"
            pairs = [[query, c.chunk.text] for c in candidates]
            scores = self._model.predict(pairs)
            scored = list(zip(candidates, [float(s) for s in scores]))
        else:
            self.mode = "lexical"
            scored = [(c, self._lexical_score(query, c.chunk.text)) for c in candidates]

        scored.sort(key=lambda x: x[1], reverse=True)
        out: List[ScoredChunk] = []
        for rank, (cand, rscore) in enumerate(scored[:top_k]):
            ms = dict(cand.method_scores)
            ms["rerank"] = float(rscore)
            out.append(ScoredChunk(chunk=cand.chunk, score=float(rscore), method_scores=ms, rank=rank))
        return out
