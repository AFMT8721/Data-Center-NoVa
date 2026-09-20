# Validated AI synthesis contract

The optional local model may summarize retrieved evidence. It may not select
facts outside that evidence or replace deterministic evidence cards.

## Flow

1. Classify the question into one of eight intents.
2. Retrieve and score the relevant evidence subset.
3. Send only selected records, proposal inputs, and the resident question to
   local `llama3.2:3b`.
4. Require structured JSON containing a short answer and cited record IDs.
5. Reject output containing unknown citations, invented numbers, unsupported
   causal claims, household-bill predictions, or more than 120 words.
6. Add citation markers in code and retain deterministic evidence cards.
7. Fall back to the deterministic response after any timeout, parse failure,
   unavailable model, or validation failure.

## Runtime panic button

The app checkbox **Validated AI synthesis** controls generation. Turning it off
keeps intent routing and evidence retrieval but returns deterministic answers
only. Default is on for demonstration.

## Evidence boundaries

- JLARC projections cannot predict one household or isolate one project.
- County AQI cannot establish which source caused local conditions.
- Permit conditions are permitted limits, never actual emissions.
- The 2015 facility inventory is historical and not generator-only.
- Similarity scores sort evidence; they are not forecasts or causal estimates.
