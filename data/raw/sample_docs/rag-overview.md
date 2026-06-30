# Retrieval-Augmented Generation (RAG) Basics

<!-- category: ai-ml -->

## Motivation
Retrieval-Augmented Generation grounds a language model's output in an external
knowledge base. Instead of relying solely on parameters, the system retrieves
relevant documents at query time and conditions generation on them, which reduces
hallucination and lets answers cite sources.

## Pipeline
A typical RAG pipeline ingests documents, splits them into chunks, embeds the chunks
into vectors, and stores them in an index. At query time it embeds the question,
retrieves the most similar chunks, and passes them to the generator as context.

## Failure modes
RAG quality is bounded by retrieval: if the relevant chunk is not retrieved, the
generator cannot produce a correct grounded answer. Poor chunking, weak embeddings,
and lack of reranking are common causes of low retrieval recall.
