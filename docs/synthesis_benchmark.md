# Grounded-synthesis smoke benchmark

Run locally on 2026-09-20 with `llama3.2:3b`, a fixed Loudoun proposal, and the
processed evidence corpus.

## Results

- In-domain summaries accepted by deterministic validator: 5/5
- Median end-to-end latency: 2.92 seconds/question
- Tested paths: household bill, JLARC context, county AQI, generator permits,
  and combined bill/air evidence
- Adversarial request for an invented `$500` bill reduction: classified
  unrelated and refused with the canned JARVIS response
- Deterministic fallback remained attached to every accepted synthesis
- Automated contract suite: 43 tests passing

## Interpretation

This smoke set demonstrates integration and guard behavior, not production
accuracy. Intent quality is measured separately in `docs/intent_benchmark.md`.
Generated summaries remain optional and may fall back whenever strict
validation rejects output.
