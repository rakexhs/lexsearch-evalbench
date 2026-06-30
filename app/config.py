"""Central configuration for Lexsearch EvalBench.

All knobs are environment-overridable (via `.env`) but ship with sensible
defaults so the demo runs with zero configuration and no API keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (no-op otherwise). Never required for the default demo.
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "sample_docs"
EVAL_DIR = DATA_DIR / "eval"
REPORTS_DIR = PROJECT_ROOT / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _get_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # Paths
    db_path: Path = field(default_factory=lambda: PROJECT_ROOT / _get("LEXSEARCH_DB_PATH", "data/lexsearch.db"))
    index_dir: Path = field(default_factory=lambda: PROJECT_ROOT / _get("LEXSEARCH_INDEX_DIR", "data/index"))
    raw_dir: Path = RAW_DIR
    eval_dir: Path = EVAL_DIR
    reports_dir: Path = REPORTS_DIR
    charts_dir: Path = CHARTS_DIR

    # Chunking
    chunk_size: int = field(default_factory=lambda: _get_int("LEXSEARCH_CHUNK_SIZE", 550))
    chunk_overlap: int = field(default_factory=lambda: _get_int("LEXSEARCH_CHUNK_OVERLAP", 80))

    # Retrieval
    top_k: int = field(default_factory=lambda: _get_int("LEXSEARCH_TOP_K", 10))
    hybrid_weight: float = field(default_factory=lambda: _get_float("LEXSEARCH_HYBRID_WEIGHT", 0.5))
    fusion: str = field(default_factory=lambda: _get("LEXSEARCH_FUSION", "rrf"))  # rrf | weighted

    # Models
    embed_model: str = field(default_factory=lambda: _get("LEXSEARCH_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    rerank_model: str = field(default_factory=lambda: _get("LEXSEARCH_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"))

    # Generation
    answer_backend: str = field(default_factory=lambda: _get("LEXSEARCH_ANSWER_BACKEND", "mock"))
    openai_model: str = field(default_factory=lambda: _get("OPENAI_MODEL", "gpt-4o-mini"))
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"))
    ollama_host: str = field(default_factory=lambda: _get("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _get("OLLAMA_MODEL", "llama3.1"))

    # Modes
    offline: bool = field(default_factory=lambda: _get_bool("LEXSEARCH_OFFLINE", False))

    def ensure_dirs(self) -> None:
        for d in (self.db_path.parent, self.index_dir, self.reports_dir, self.charts_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    return s


settings = get_settings()
