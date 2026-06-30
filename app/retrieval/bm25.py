"""BM25 lexical retriever backed by rank-bm25."""
from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import List, Tuple

from rank_bm25 import BM25Okapi

from app.schemas import Chunk

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")


def tokenize(text: str) -> List[str]:
    """Lowercase tokenizer that keeps dotted/underscored identifiers like
    `git.checkout`, `requirements.txt`, `--hard` together-ish for API names."""
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    def __init__(self) -> None:
        self.chunks: List[Chunk] = []
        self._bm25: BM25Okapi | None = None

    def index(self, chunks: List[Chunk]) -> None:
        self.chunks = list(chunks)
        corpus_tokens = [tokenize(c.text + " " + c.title) for c in self.chunks]
        # rank-bm25 requires a non-empty corpus
        if not corpus_tokens:
            raise ValueError("BM25Retriever.index received zero chunks")
        self._bm25 = BM25Okapi(corpus_tokens)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Chunk, float]]:
        if self._bm25 is None:
            raise RuntimeError("BM25 index not built. Call index() first.")
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.chunks, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    # ── persistence ──────────────────────────────────────────────────────────
    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        with (index_dir / "bm25.pkl").open("wb") as fh:
            pickle.dump({"chunks": [c.model_dump() for c in self.chunks], "bm25": self._bm25}, fh)

    @classmethod
    def load(cls, index_dir: Path) -> "BM25Retriever":
        with (index_dir / "bm25.pkl").open("rb") as fh:
            payload = pickle.load(fh)
        obj = cls()
        obj.chunks = [Chunk(**c) for c in payload["chunks"]]
        obj._bm25 = payload["bm25"]
        return obj
