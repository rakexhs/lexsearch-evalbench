"""SQLite schema definitions for metadata storage."""
from __future__ import annotations

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id   TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    category TEXT,
    source   TEXT,
    n_chars  INTEGER
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id   TEXT NOT NULL,
    title    TEXT,
    section  TEXT,
    position INTEGER,
    n_chars  INTEGER,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
);

CREATE TABLE IF NOT EXISTS eval_runs (
    run_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    method     TEXT NOT NULL,
    num_questions INTEGER,
    recall_at_5  REAL,
    ndcg_at_5    REAL,
    mrr          REAL,
    context_precision REAL,
    faithfulness REAL,
    mean_latency_ms REAL,
    p95_latency_ms  REAL,
    payload    TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_eval_method ON eval_runs(method);
"""
