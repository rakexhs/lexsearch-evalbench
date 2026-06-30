"""Shared pytest fixtures. Forces offline mode so tests never hit the network
(dense uses the deterministic hashing embedder; reranker uses the lexical fallback)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Force fully-offline, deterministic behaviour BEFORE importing app modules.
os.environ.setdefault("LEXSEARCH_OFFLINE", "1")

# Isolate test storage so the suite never clobbers the real demo index / DB that
# `make index` builds (the API integration test rebuilds + saves an index).
_TEST_TMP = Path(tempfile.mkdtemp(prefix="lexsearch_test_"))
os.environ.setdefault("LEXSEARCH_INDEX_DIR", str(_TEST_TMP / "index"))
os.environ.setdefault("LEXSEARCH_DB_PATH", str(_TEST_TMP / "test.db"))

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from app.ingestion.chunker import chunk_documents  # noqa: E402
from app.ingestion.sample_corpus import DOCS  # noqa: E402
from app.schemas import Document  # noqa: E402


@pytest.fixture(scope="session")
def documents() -> list[Document]:
    return [
        Document(doc_id=did, title=d["title"], category=d["category"], source=f"{did}.md", text=d["text"])
        for did, d in DOCS.items()
    ]


@pytest.fixture(scope="session")
def chunks(documents):
    return chunk_documents(documents, chunk_size=550, chunk_overlap=80)
