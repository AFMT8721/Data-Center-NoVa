# Intent-routing benchmark

Dataset: `data/curated/intent_eval.csv` (30 hand-labeled questions).
Local model: `llama3.2:3b`. Answers remain deterministic.

### Deterministic keyword baseline
- Exact accuracy: 22/30 (73.3%)
- Median latency: 0.0 ms/question
- Total runtime: 0 ms
- Unavailable classifications: 0
- Misclassifications: bill_prediction → bill_context (1); both → bill_context (2); unrelated → bill_context (5)

### Local model
- Exact accuracy: 30/30 (100.0%)
- Median latency: 281.9 ms/question
- Total runtime: 8429 ms
- Unavailable classifications: 0
- Misclassifications: none

This is a small demonstration set, not a production validation study.
