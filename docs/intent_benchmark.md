# Intent-routing benchmark

Dataset: `data/curated/intent_eval.csv` (40 hand-labeled questions).
Local model: `llama3.2:3b`. Routing is evaluated independently of answer synthesis.

### Deterministic keyword baseline
- Exact accuracy: 35/40 (87.5%)
- Median latency: 0.0 ms/question
- Total runtime: 0 ms
- Unavailable classifications: 0
- Misclassifications: unrelated → bill_context (5)

### Local model
- Exact accuracy: 39/40 (97.5%)
- Median latency: 274.6 ms/question
- Total runtime: 10955 ms
- Unavailable classifications: 0
- Misclassifications: unrelated → greeting (1)

This is a small demonstration set, not a production validation study.
