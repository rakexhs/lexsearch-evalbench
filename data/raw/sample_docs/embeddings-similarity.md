# Text Embeddings and Similarity Search

<!-- category: ai-ml -->

## Embeddings
A text embedding maps a piece of text to a dense vector such that semantically
similar texts land near each other in vector space. Sentence-transformer models are
commonly used to produce these embeddings for retrieval.

## Cosine similarity
Similarity between two embeddings is usually measured with cosine similarity, the
cosine of the angle between the vectors. It ranges from -1 to 1, and because it
ignores magnitude it compares direction, which suits normalized embeddings well.

## Approximate nearest neighbour
For large corpora, exact search is slow, so approximate nearest neighbour indexes
such as HNSW trade a small amount of recall for a large speedup in retrieval.
