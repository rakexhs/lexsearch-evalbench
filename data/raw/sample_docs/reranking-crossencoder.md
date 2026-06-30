# Cross-Encoder Reranking

<!-- category: ai-ml -->

## Bi-encoders vs cross-encoders
A bi-encoder embeds the query and document separately, which is fast and allows
precomputing document vectors. A cross-encoder instead feeds the query and a
candidate document together through the model and outputs a single relevance score,
which is more accurate but too slow to run over an entire corpus.

## Two-stage retrieval
The standard pattern is two-stage: a fast retriever (BM25, dense, or hybrid) fetches
a candidate set of, say, the top 50 chunks, and a cross-encoder reranker rescores
just those candidates to produce the final ordering. This improves precision at the
top ranks without the cost of scoring every document.

## Reciprocal rank fusion
Reciprocal rank fusion (RRF) combines several ranked lists by summing 1/(k + rank)
across lists, which is a simple and robust way to merge BM25 and dense results before
reranking.
