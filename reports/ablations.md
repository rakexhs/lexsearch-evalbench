# Lexsearch EvalBench — Ablation Results

## chunk_size

| setting   | method        |   recall_at_5 |   ndcg_at_5 |   mrr |   context_precision |   faithfulness |   mean_latency_ms |
|:----------|:--------------|--------------:|------------:|------:|--------------------:|---------------:|------------------:|
| size=300  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.214 |              1 |           108.572 |
| size=550  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            99.095 |
| size=800  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            93.034 |
| size=1200 | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            92.793 |

## chunk_overlap

| setting     | method        |   recall_at_5 |   ndcg_at_5 |   mrr |   context_precision |   faithfulness |   mean_latency_ms |
|:------------|:--------------|--------------:|------------:|------:|--------------------:|---------------:|------------------:|
| overlap=0   | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |           103.504 |
| overlap=40  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            98.734 |
| overlap=80  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            97.222 |
| overlap=160 | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |            97.867 |

## hybrid_weight

| setting           | method   |   recall_at_5 |   ndcg_at_5 |   mrr |   context_precision |   faithfulness |   mean_latency_ms |
|:------------------|:---------|--------------:|------------:|------:|--------------------:|---------------:|------------------:|
| dense_weight=0.0  | hybrid   |             1 |      0.9812 |  0.98 |              0.212  |              0 |             9.214 |
| dense_weight=0.25 | hybrid   |             1 |      0.9926 |  0.99 |              0.222  |              0 |             9.872 |
| dense_weight=0.5  | hybrid   |             1 |      0.9926 |  0.99 |              0.231  |              0 |             9.854 |
| dense_weight=0.75 | hybrid   |             1 |      1      |  1    |              0.2397 |              0 |             9.931 |
| dense_weight=1.0  | hybrid   |             1 |      0.9984 |  1    |              0.238  |              0 |             9.942 |

## reranker

| setting      | method        |   recall_at_5 |   ndcg_at_5 |   mrr |   context_precision |   faithfulness |   mean_latency_ms |
|:-------------|:--------------|--------------:|------------:|------:|--------------------:|---------------:|------------------:|
| reranker=off | hybrid        |             1 |      0.9926 |  0.99 |               0.228 |              1 |             9.241 |
| reranker=on  | hybrid_rerank |             1 |      0.9902 |  0.99 |               0.215 |              1 |           101.229 |

![Ablations](charts/ablations.png)
