"""Document loader: reads markdown docs from disk into Document objects."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from app.config import settings
from app.schemas import Document

_CATEGORY_RE = re.compile(r"<!--\s*category:\s*(?P<cat>[\w-]+)\s*-->")
_TITLE_RE = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)


def _parse_markdown(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    doc_id = path.stem

    title_match = _TITLE_RE.search(raw)
    title = title_match.group("title").strip() if title_match else doc_id

    cat_match = _CATEGORY_RE.search(raw)
    category = cat_match.group("cat") if cat_match else ""

    # Strip the leading H1 title line and the category comment from the body.
    body = raw
    if title_match:
        body = body[: title_match.start()] + body[title_match.end():]
    body = _CATEGORY_RE.sub("", body).strip()

    return Document(doc_id=doc_id, title=title, source=str(path.name), category=category, text=body)


def load_documents(raw_dir: Path | None = None) -> List[Document]:
    """Load all `*.md` documents from the corpus directory, sorted by id."""
    raw_dir = raw_dir or settings.raw_dir
    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Corpus dir {raw_dir} not found. Run `make sample-data` (or scripts/setup_sample_data.py) first."
        )
    paths = sorted(raw_dir.glob("*.md"))
    return [_parse_markdown(p) for p in paths]
