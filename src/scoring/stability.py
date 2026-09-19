"""Top-k rank stability under one-at-a-time weight perturbations."""

from __future__ import annotations

import pandas as pd

from src.schemas.proposal import Proposal
from src.scoring.score import rank_domain
from src.scoring.weights import WEIGHTS


def _renormalized(
    domain: str, feature: str, multiplier: float
) -> dict[str, dict[str, float]]:
    perturbed = {name: values.copy() for name, values in WEIGHTS.items()}
    domain_weights = perturbed[domain]
    domain_weights[feature] *= multiplier
    total = sum(domain_weights.values())
    perturbed[domain] = {name: value / total for name, value in domain_weights.items()}
    return perturbed


def rank_stability(
    proposal: Proposal,
    corpus: pd.DataFrame,
    domain: str,
    top_k: int = 3,
    multipliers: tuple[float, ...] = (0.8, 1.2),
) -> pd.DataFrame:
    baseline = [
        row["record_id"] for row in rank_domain(proposal, corpus, domain)[:top_k]
    ]
    baseline_set = set(baseline)
    rows: list[dict[str, object]] = []
    for feature in WEIGHTS[domain]:
        for multiplier in multipliers:
            perturbed = [
                row["record_id"]
                for row in rank_domain(
                    proposal,
                    corpus,
                    domain,
                    _renormalized(domain, feature, multiplier),
                )[:top_k]
            ]
            perturbed_set = set(perturbed)
            union = baseline_set | perturbed_set
            rows.append(
                {
                    "domain": domain,
                    "feature": feature,
                    "multiplier": multiplier,
                    "baseline_top_k": " | ".join(baseline),
                    "perturbed_top_k": " | ".join(perturbed),
                    "top_k_overlap": len(baseline_set & perturbed_set),
                    "top_k_churn": len(baseline_set - perturbed_set),
                    "jaccard": len(baseline_set & perturbed_set) / len(union)
                    if union
                    else 1.0,
                    "same_order": baseline == perturbed,
                }
            )
    return pd.DataFrame(rows)
