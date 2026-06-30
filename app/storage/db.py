"""SQLite metadata store for documents, chunks, and evaluation runs."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.schemas import Chunk, Document, MethodMetrics
from app.storage.models import SCHEMA


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or settings.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)


def store_corpus(documents: List[Document], chunks: List[Chunk], db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
        conn.executemany(
            "INSERT OR REPLACE INTO documents (doc_id, title, category, source, n_chars) VALUES (?, ?, ?, ?, ?)",
            [(d.doc_id, d.title, d.category, d.source, len(d.text)) for d in documents],
        )
        conn.executemany(
            "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, title, section, position, n_chars) VALUES (?, ?, ?, ?, ?, ?)",
            [(c.chunk_id, c.doc_id, c.title, c.section, c.position, len(c.text)) for c in chunks],
        )
        conn.commit()


def counts(db_path: Path | None = None) -> Dict[str, int]:
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)
        docs = conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]
        chunks = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
    return {"documents": docs, "chunks": chunks}


def record_eval(metrics: List[MethodMetrics], db_path: Path | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)
        for m in metrics:
            conn.execute(
                """INSERT INTO eval_runs
                   (created_at, method, num_questions, recall_at_5, ndcg_at_5, mrr,
                    context_precision, faithfulness, mean_latency_ms, p95_latency_ms, payload)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    now,
                    m.method,
                    m.num_questions,
                    m.recall_at_k.get(5, 0.0),
                    m.ndcg_at_k.get(5, 0.0),
                    m.mrr,
                    m.context_precision,
                    m.citation_faithfulness,
                    m.mean_latency_ms,
                    m.p95_latency_ms,
                    json.dumps(m.model_dump()),
                ),
            )
        conn.commit()


def latest_eval(db_path: Path | None = None) -> List[Dict]:
    """Return the most recent evaluation run's metrics per method."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)
        row = conn.execute("SELECT MAX(created_at) AS ts FROM eval_runs").fetchone()
        if not row or row["ts"] is None:
            return []
        ts = row["ts"]
        rows = conn.execute("SELECT payload FROM eval_runs WHERE created_at = ?", (ts,)).fetchall()
    return [json.loads(r["payload"]) for r in rows]
