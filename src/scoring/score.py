"""Score and rank comparable evidence by domain."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.schemas.proposal import Proposal
from src.scoring.features import FEATURES
from src.scoring.weights import WEIGHTS


def score_record(
    proposal: Proposal,
    record: dict[str, Any],
    domain: str,
    weights: dict[str, dict[str, float]] = WEIGHTS,
) -> dict[str, Any]:
    if domain not in weights:
        raise ValueError(f"Unsupported domain: {domain}")
    breakdown: dict[str, dict[str, Any]] = {}
    numerator = 0.0
    available_weight = 0.0
    for feature_name, weight in weights[domain].items():
        result = FEATURES[feature_name](proposal, record)
        breakdown[feature_name] = {
            "value": result.value,
            "configured_weight": weight,
            "reason": result.reason,
        }
        if result.value is not None:
            numerator += result.value * weight
            available_weight += weight
    score = numerator / available_weight if available_weight else None
    for item in breakdown.values():
        item["effective_weight"] = (
            item["configured_weight"] / available_weight
            if item["value"] is not None and available_weight
            else 0.0
        )
    return {
        "score": score,
        "available_weight": available_weight,
        "breakdown": breakdown,
    }


def rank_domain(
    proposal: Proposal,
    corpus: pd.DataFrame,
    domain: str,
    weights: dict[str, dict[str, float]] = WEIGHTS,
) -> list[dict[str, Any]]:
    rows = corpus.loc[corpus["outcome_domain"].eq(domain)]
    ranked: list[dict[str, Any]] = []
    for record in rows.to_dict(orient="records"):
        scored = score_record(proposal, record, domain, weights)
        ranked.append({**record, **scored})
    return sorted(
        ranked,
        key=lambda row: (
            row["score"] is not None,
            row["score"] if row["score"] is not None else -1.0,
            row["record_id"],
        ),
        reverse=True,
    )
