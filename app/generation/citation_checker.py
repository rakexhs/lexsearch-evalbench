"""Citation faithfulness checking.

Given an answer and the chunks it cites, verify that each answer sentence is
actually supported by the cited evidence. Support is measured as the fraction of a
sentence's content tokens (minus stopwords) that appear in the supporting chunk
text. This is a deterministic, no-API grounding check.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
# Split after sentence punctuation OR a trailing citation marker like "[1]",
# so that ". [1] NextSentence" breaks into two sentences with the marker kept on
# the preceding claim.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?\]])\s+(?=[A-Z`])")

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of",
    "and", "or", "in", "on", "for", "with", "as", "by", "that", "this", "it", "its",
    "from", "at", "into", "than", "then", "so", "such", "you", "your", "can", "will",
    "not", "no", "do", "does", "use", "used", "using", "when", "which", "while", "if",
    "they", "them", "their", "there", "here", "but", "also", "each", "one", "two",
}

SUPPORT_THRESHOLD = 0.6  # fraction of content tokens that must be present


def _content_tokens(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


def split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    # protect citation markers like [1] from being treated as sentence ends
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def sentence_support(sentence: str, evidence: str) -> float:
    """Return fraction of the sentence's content tokens present in evidence."""
    s_tokens = _content_tokens(re.sub(r"\[\d+\]", "", sentence))
    if not s_tokens:
        return 1.0  # nothing to support (e.g. pure citation) -> trivially supported
    ev = set(_content_tokens(evidence))
    present = sum(1 for t in s_tokens if t in ev)
    return present / len(s_tokens)


@dataclass
class FaithfulnessReport:
    faithfulness: float
    supported_sentences: int
    total_sentences: int
    per_sentence: List[Dict]
    unsupported_sentences: List[str]


def check_faithfulness(
    answer: str,
    evidence_by_marker: Dict[str, str],
    threshold: float = SUPPORT_THRESHOLD,
) -> FaithfulnessReport:
    """Check each answer sentence against the evidence of the markers it cites.

    If a sentence cites specific markers (e.g. "[1]"), it is checked only against
    those chunks. If it cites none, it is checked against the union of all evidence.
    """
    sentences = split_sentences(answer)
    all_evidence = " ".join(evidence_by_marker.values())

    per_sentence: List[Dict] = []
    unsupported: List[str] = []
    supported_count = 0

    for sent in sentences:
        markers = re.findall(r"\[(\d+)\]", sent)
        if markers:
            evidence = " ".join(evidence_by_marker.get(f"[{m}]", "") for m in markers)
        else:
            evidence = all_evidence
        score = sentence_support(sent, evidence)
        is_supported = score >= threshold
        supported_count += int(is_supported)
        per_sentence.append({"sentence": sent, "support": round(score, 3), "supported": is_supported})
        if not is_supported:
            unsupported.append(sent)

    total = len(sentences)
    faithfulness = supported_count / total if total else 1.0
    return FaithfulnessReport(
        faithfulness=round(faithfulness, 4),
        supported_sentences=supported_count,
        total_sentences=total,
        per_sentence=per_sentence,
        unsupported_sentences=unsupported,
    )
