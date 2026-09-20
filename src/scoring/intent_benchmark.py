"""Benchmark local-model intent routing against deterministic keywords."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Callable

import pandas as pd

from src.scoring.intent import OLLAMA_MODEL, classify_intent, keyword_intent


def evaluate(
    cases: pd.DataFrame,
    classifier: Callable[[str], str | None],
) -> tuple[pd.DataFrame, float]:
    rows: list[dict[str, object]] = []
    started = perf_counter()
    for case in cases.to_dict(orient="records"):
        item_started = perf_counter()
        predicted = classifier(str(case["query"]))
        rows.append(
            {
                **case,
                "predicted_intent": predicted,
                "correct": predicted == case["expected_intent"],
                "latency_ms": (perf_counter() - item_started) * 1000,
            }
        )
    return pd.DataFrame(rows), (perf_counter() - started) * 1000


def _summary(name: str, results: pd.DataFrame, elapsed_ms: float) -> list[str]:
    correct = int(results["correct"].sum())
    unavailable = int(results["predicted_intent"].isna().sum())
    lines = [
        f"### {name}",
        f"- Exact accuracy: {correct}/{len(results)} ({correct / len(results):.1%})",
        f"- Median latency: {results['latency_ms'].median():.1f} ms/question",
        f"- Total runtime: {elapsed_ms:.0f} ms",
        f"- Unavailable classifications: {unavailable}",
    ]
    errors = results.loc[~results["correct"]]
    if errors.empty:
        lines.append("- Misclassifications: none")
    else:
        pairs = Counter(
            f"{row.expected_intent} → {row.predicted_intent or 'unavailable'}"
            for row in errors.itertuples()
        )
        lines.append(
            "- Misclassifications: "
            + "; ".join(f"{pair} ({count})" for pair, count in sorted(pairs.items()))
        )
    return lines


def build_report(cases_path: Path) -> str:
    cases = pd.read_csv(cases_path)
    keyword_results, keyword_ms = evaluate(cases, keyword_intent)
    model_results, model_ms = evaluate(cases, classify_intent)
    display_path = f"data/curated/{cases_path.name}"
    lines = [
        "# Intent-routing benchmark",
        "",
        f"Dataset: `{display_path}` ({len(cases)} hand-labeled questions).",
        f"Local model: `{OLLAMA_MODEL}`. Answers remain deterministic.",
        "",
        *_summary("Deterministic keyword baseline", keyword_results, keyword_ms),
        "",
        *_summary("Local model", model_results, model_ms),
        "",
        "This is a small demonstration set, not a production validation study.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    output = root / "docs/intent_benchmark.md"
    output.write_text(
        build_report(root / "data/curated/intent_eval.csv"),
        encoding="utf-8",
    )
    print(output.read_text(encoding="utf-8"))
