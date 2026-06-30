"""Dense embedding retriever.

Primary path uses sentence-transformers. If the model cannot be loaded (no
network on first run, or the package/torch is unavailable, or LEXSEARCH_OFFLINE=1),
it degrades to a deterministic feature-hashing embedder so the pipeline still runs
fully offline. `mode` reports which path is active ("sentence-transformers" | "hashing").
"""
from __future__ import annotations

import hashlib
import pickle
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np

from app.config import settings
from app.observability.logging_config import get_logger
from app.schemas import Chunk

log = get_logger("dense")

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
_HASH_DIM = 1024


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _hash_embed(texts: List[str], dim: int = _HASH_DIM) -> np.ndarray:
    """Deterministic feature-hashing embedding with sublinear TF + L2 norm.

    This is a lexical stand-in for a learned embedder; it keeps the dense path
    functional offline. It adds light character-bigram features so near-synonym
    surface forms get partial overlap.
    """
    vecs = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        toks = _tokens(text)
        # add token bigrams for a bit of word-order signal
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        for feat in feats:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 17) & 1 else -1.0
            vecs[i, idx] += sign
        # sublinear scaling
        nz = vecs[i] != 0
        vecs[i, nz] = np.sign(vecs[i, nz]) * (1.0 + np.log(np.abs(vecs[i, nz])))
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


class DenseRetriever:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embed_model
        self.chunks: List[Chunk] = []
        self.embeddings: np.ndarray | None = None
        self.mode: str = "uninitialized"
        self._model = None

    # ── model loading ────────────────────────────────────────────────────────
    def _ensure_model(self) -> bool:
        """Try to load a sentence-transformers model. Returns True on success."""
        if self._model is not None:
            return True
        if settings.offline:
            return False
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
            return True
        except Exception as exc:  # pragma: no cover - depends on env
            log.warning("Falling back to hashing embedder (could not load '%s': %s)", self.model_name, exc)
            return False

    def _encode(self, texts: List[str]) -> np.ndarray:
        # Lock the embedding mode at index-build time, then honour it for every
        # subsequent query so the index and query vectors always share a backend
        # (and dimensionality). Silently switching backends at query time would
        # produce mismatched vectors.
        if self.mode == "uninitialized":
            self.mode = "sentence-transformers" if self._ensure_model() else "hashing"

        if self.mode == "sentence-transformers":
            if not self._ensure_model():
                raise RuntimeError(
                    "Dense index was built with sentence-transformers but the model could "
                    "not be loaded for querying. Rebuild the index (set LEXSEARCH_OFFLINE=1 "
                    "to use the hashing embedder consistently)."
                )
            emb = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(emb, dtype=np.float32)

        return _hash_embed(texts)

    # ── indexing / search ────────────────────────────────────────────────────
    def index(self, chunks: List[Chunk]) -> None:
        self.chunks = list(chunks)
        if not self.chunks:
            raise ValueError("DenseRetriever.index received zero chunks")
        texts = [f"{c.title}. {c.text}" for c in self.chunks]
        self.embeddings = self._encode(texts)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Chunk, float]]:
        if self.embeddings is None:
            raise RuntimeError("Dense index not built. Call index() first.")
        q = self._encode([query])[0]
        sims = self.embeddings @ q  # both normalized -> cosine similarity
        order = np.argsort(-sims)[:top_k]
        return [(self.chunks[i], float(sims[i])) for i in order]

    # ── persistence ──────────────────────────────────────────────────────────
    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / "dense_embeddings.npy", self.embeddings)
        with (index_dir / "dense_meta.pkl").open("wb") as fh:
            pickle.dump(
                {
                    "chunks": [c.model_dump() for c in self.chunks],
                    "mode": self.mode,
                    "model_name": self.model_name,
                },
                fh,
            )

    @classmethod
    def load(cls, index_dir: Path) -> "DenseRetriever":
        with (index_dir / "dense_meta.pkl").open("rb") as fh:
            meta = pickle.load(fh)
        obj = cls(model_name=meta["model_name"])
        obj.chunks = [Chunk(**c) for c in meta["chunks"]]
        obj.embeddings = np.load(index_dir / "dense_embeddings.npy")
        obj.mode = meta["mode"]
        return obj
