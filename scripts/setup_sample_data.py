"""Generate (and validate) the built-in sample corpus and golden question set."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.sample_corpus import materialize, validate  # noqa: E402


def main() -> int:
    counts = materialize()
    issues = validate()
    print(f"✅ Wrote {counts['num_docs']} sample docs to data/raw/sample_docs/")
    print(f"✅ Wrote {counts['num_questions']} golden questions to data/eval/golden_questions.jsonl")
    if issues:
        print("\n⚠️  Validation issues:")
        for i in issues:
            print("   -", i)
        return 1
    print("✅ Validation OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
