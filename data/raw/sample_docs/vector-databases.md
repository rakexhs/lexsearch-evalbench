# Vector Databases and ANN Indexes

<!-- category: ai-ml -->

## What they store
A vector database stores high-dimensional embeddings and supports nearest-neighbour
search over them. Each vector is usually stored alongside metadata used for filtering
results, such as a document id or category.

## Index types
Flat indexes compare the query against every vector for exact results. Graph indexes
like HNSW and quantization-based indexes like IVF-PQ trade a little recall for much
faster approximate search on large collections.

## Filtering
Metadata filtering restricts the search to vectors matching a condition, for example
a tenant id, which is essential for multi-tenant retrieval but can interact awkwardly
with approximate indexes if applied after the search.
