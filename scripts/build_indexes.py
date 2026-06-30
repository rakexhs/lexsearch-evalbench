"""Ingest the corpus, chunk it, and build BM25 + dense indexes; persist to disk."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.ingestion.chunker import chunk_documents  # noqa: E402
from app.ingestion.loader import load_documents  # noqa: E402
from app.retrieval.pipeline import RetrievalPipeline  # noqa: E402
from app.storage import db  # noqa: E402


def main() -> int:
    settings.ensure_dirs()
    t0 = time.perf_counter()

    docs = load_documents()
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} docs -> {len(chunks)} chunks "
          f"(size={settings.chunk_size}, overlap={settings.chunk_overlap})")

    pipe = RetrievalPipeline()
    pipe.build(chunks)
    pipe.save()

    db.store_corpus(docs, chunks)

    desc = pipe.describe()
    dt = time.perf_counter() - t0
    print(f"✅ Built indexes in {dt:.2f}s")
    print(f"   dense mode : {desc['dense_mode']} ({desc['embed_model']})")
    print(f"   fusion     : {desc['fusion']}")
    print(f"   index dir  : {settings.index_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
