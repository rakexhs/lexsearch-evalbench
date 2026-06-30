"""Tests for the section-aware chunker."""
from app.ingestion.chunker import chunk_document, chunk_documents
from app.schemas import Document


def _doc(text: str) -> Document:
    return Document(doc_id="d1", title="Title", category="cat", source="d1.md", text=text)


def test_chunk_ids_and_metadata(documents):
    chunks = chunk_documents(documents[:3], chunk_size=400, chunk_overlap=50)
    assert len(chunks) > 0
    for c in chunks:
        assert c.chunk_id.startswith(c.doc_id)
        assert c.text
        assert c.metadata.get("category")  # propagated from doc


def test_section_attribution():
    doc = _doc("## Alpha\nFirst section body about alpha topic.\n\n## Beta\nSecond section about beta topic.")
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=0)
    sections = {c.section for c in chunks}
    assert "Alpha" in sections
    assert "Beta" in sections


def test_chunk_size_is_respected():
    body = "word " * 400  # ~2000 chars in one section
    doc = _doc("## S\n" + body)
    chunks = chunk_document(doc, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    # no chunk should greatly exceed the configured size (allow small slack for word boundaries)
    assert all(len(c.text) <= 300 + 20 for c in chunks)


def test_overlap_creates_shared_text():
    body = " ".join(f"token{i}" for i in range(200))
    doc = _doc("## S\n" + body)
    no_overlap = chunk_document(doc, chunk_size=200, chunk_overlap=0)
    with_overlap = chunk_document(doc, chunk_size=200, chunk_overlap=80)
    # overlap should not reduce the number of chunks and typically increases it
    assert len(with_overlap) >= len(no_overlap)


def test_overlap_clamped_when_larger_than_size():
    doc = _doc("## S\n" + ("alpha beta gamma delta " * 50))
    # overlap >= size must not hang or error
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=200)
    assert len(chunks) >= 1


def test_positions_are_monotonic(documents):
    chunks = chunk_document(documents[0])
    positions = [c.position for c in chunks]
    assert positions == sorted(positions)
    assert positions[0] == 0
