"""Tests for citation faithfulness checking and grounded answer generation."""
from app.generation.answerer import generate_answer
from app.generation.citation_checker import check_faithfulness, sentence_support, split_sentences
from app.retrieval.pipeline import RetrievalPipeline


def test_split_sentences():
    s = split_sentences("First sentence. Second one! Third? Done.")
    assert len(s) == 4


def test_sentence_support_high_and_low():
    evidence = "git revert creates a new commit that undoes the changes without rewriting history"
    supported = "git revert creates a new commit that undoes the changes"
    assert sentence_support(supported, evidence) >= 0.9
    unsupported = "kubernetes pods autoscale across availability zones automatically"
    assert sentence_support(unsupported, evidence) < 0.3


def test_check_faithfulness_flags_unsupported():
    evidence = {"[1]": "A docker image is a read-only template containing code and dependencies."}
    answer = "A docker image is a read-only template. [1] Bananas grow in tropical climates worldwide."
    report = check_faithfulness(answer, evidence)
    assert report.total_sentences == 2
    assert report.supported_sentences == 1
    assert report.faithfulness == 0.5
    assert any("Bananas" in s for s in report.unsupported_sentences)


def test_generate_answer_is_grounded_and_cited(chunks):
    pipe = RetrievalPipeline()
    pipe.build(chunks)
    results, _ = pipe.retrieve("How do I create a branch and switch to it in one command?",
                               method="hybrid_rerank", top_k=5)
    ans = generate_answer("How do I create a branch and switch to it in one command?", results, backend="mock")
    assert ans.backend == "mock"
    assert ans.answer
    assert ans.citations, "extractive answer must include at least one citation"
    # mock backend only emits sentences from evidence -> should be highly faithful
    assert ans.faithfulness >= 0.8
    # every citation marker referenced in the answer should resolve to a chunk
    for cit in ans.citations:
        assert cit.chunk_id


def test_generate_answer_handles_no_results():
    ans = generate_answer("anything", [], backend="mock")
    assert ans.citations == []
    assert ans.faithfulness == 0.0
