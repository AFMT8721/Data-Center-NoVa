# Northern Virginia Data Center Comparability Agent

Minimal resident-facing prototype for retrieving and ranking documented
electricity-bill and air-quality evidence. It does not predict per-resident
costs. Scores are transparent weighted heuristics, not calibrated estimates.

## Build data products

```bash
uv sync
uv run python -m src.ingest.manifest
uv run python -m src.ingest.landmarc
uv run python -m src.ingest.deq_permits
uv run python -m src.preprocess.landmarc_clean
uv run python -m src.preprocess.corpus
uv run python -m src.preprocess.candidate_join
```

Raw files under `data/raw` are read-only inputs. Generated products go to
`data/interim`, `data/processed`, `docs/landmarc_profile.md`, and
`provenance/manifest.csv`.

## Run checks

```bash
uv run pytest -q
uv run marimo check app/comparability_app.py
```

## Run app

```bash
uv run marimo run app/comparability_app.py
```

`mo.ui.chat` calls a deterministic response function that enforces citations,
evidence labels, domain-specific score breakdowns, and the
no-per-resident-prediction rule. No model generates any part of an answer's
content.

Optionally, a local open-weight model (`ollama pull llama3.2:3b`,
`brew services start ollama`) classifies each question into one of six intents:
household bill prediction, bill context, monitored air quality, permits and
emissions, both topics, or unrelated. Routing selects a tailored deterministic
answer and evidence subset; the model never writes answer content. If Ollama
isn't running, `src/scoring/intent.py` uses a deterministic fallback.

Run the small labeled comparison against that fallback with:

```bash
uv run python -m src.scoring.intent_benchmark
```

Results are written to `docs/intent_benchmark.md`.

See `docs/open_issues.md` before interpreting results. DEQ permit rows describe
what was permitted, not measured emissions. The 2015 emissions list is
historical facility-wide context, five LandMARC Permit exports are
byte-identical, and AQI is locality context rather than a
data-center-attributed outcome.
