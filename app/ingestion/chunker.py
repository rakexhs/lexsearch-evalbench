"""Section-aware, word-based chunker with configurable size and overlap.

Chunks are built within markdown `## Section` boundaries where possible, then
split into windows of approximately `chunk_size` characters with `chunk_overlap`
characters of overlap. Each chunk records its source doc, title, and section.
"""
from __future__ import annotations

import re
from typing import List

from app.config import settings
from app.schemas import Chunk, Document

_SECTION_RE = re.compile(r"^##\s+(?P<name>.+)$", re.MULTILINE)


def _split_sections(text: str) -> List[tuple[str, str]]:
    """Return list of (section_name, section_text). Text before the first
    header (if any) is attributed to a 'Preamble' section."""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

    sections: List[tuple[str, str]] = []
    # Preamble before first header
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            sections.append(("Preamble", pre))

    for i, m in enumerate(matches):
        name = m.group("name").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((name, body))
    return sections


def _window(text: str, size: int, overlap: int) -> List[str]:
    """Split text into overlapping windows on word boundaries.

    `size`/`overlap` are measured in characters; we cut on the nearest preceding
    whitespace so words are never split.
    """
    text = " ".join(text.split())  # normalize whitespace
    if size <= 0:
        return [text] if text else []
    if len(text) <= size:
        return [text] if text else []

    step = max(1, size - overlap)
    windows: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # back off to the last whitespace within the window for a clean cut
            ws = text.rfind(" ", start, end)
            if ws > start:
                end = ws
        chunk = text[start:end].strip()
        if chunk:
            windows.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
        # ensure forward progress
        if step <= 0:
            break
    return windows


def chunk_document(
    doc: Document,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Chunk]:
    chunk_size = settings.chunk_size if chunk_size is None else chunk_size
    chunk_overlap = settings.chunk_overlap if chunk_overlap is None else chunk_overlap
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 4)

    chunks: List[Chunk] = []
    position = 0
    for section_name, section_text in _split_sections(doc.text):
        for window in _window(section_text, chunk_size, chunk_overlap):
            chunk_id = f"{doc.doc_id}::{position:03d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=section_name,
                    text=window,
                    position=position,
                    metadata={"category": doc.category, "source": doc.source},
                )
            )
            position += 1
    return chunks


def chunk_documents(
    docs: List[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Chunk]:
    out: List[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, chunk_size, chunk_overlap))
    return out
