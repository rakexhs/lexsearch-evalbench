# BM25 Lexical Ranking

<!-- category: ai-ml -->

## What BM25 is
BM25 is a bag-of-words ranking function that scores documents by term frequency and
inverse document frequency. It rewards documents where query terms appear often but
discounts terms that are common across the whole corpus.

## Saturation and length
Unlike raw TF-IDF, BM25 saturates term frequency so that the tenth occurrence of a
word adds less than the second. It also normalizes for document length so that long
documents are not unfairly favoured simply for containing more words.

## Strengths
BM25 excels at exact keyword and rare-term matching, such as error codes or API
names, where dense embeddings may miss the precise token. This complementary
strength is why hybrid retrieval combines BM25 with dense retrieval.
