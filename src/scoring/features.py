"""Feature functions returning value and a displayable reason."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from src.schemas.proposal import Proposal


@dataclass(frozen=True)
class FeatureResult:
    value: float | None
    reason: str


def _number(record: dict[str, Any], key: str) -> float | None:
    value = record.get(key)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def utility_territory_match(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    territory = str(record.get("utility_territory") or "").strip()
    if proposal.utility_territory == "unknown" or not territory:
        return FeatureResult(None, "omitted: utility territory is unknown")
    matched = territory.casefold() == proposal.utility_territory.casefold()
    return FeatureResult(float(matched), f"{proposal.utility_territory} vs {territory}")


def rate_vintage_match(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    era = str(record.get("era") or "").strip()
    if not era:
        return FeatureResult(None, "omitted: comparable rate era is unavailable")
    matched = era == proposal.era
    return FeatureResult(float(matched), f"{proposal.era} vs {era}")


def scale_mw_proximity(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    comparable = _number(record, "scale_mw")
    if comparable is None:
        return FeatureResult(None, "omitted: comparable MW is unavailable")
    denominator = max(proposal.proposed_mw, comparable, 1.0)
    score = max(0.0, 1.0 - abs(proposal.proposed_mw - comparable) / denominator)
    return FeatureResult(score, f"{proposal.proposed_mw:g} MW vs {comparable:g} MW")


def timing_proximity(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    year = _number(record, "filing_year")
    if year is None:
        return FeatureResult(None, "omitted: comparable year is unavailable")
    gap = abs(proposal.filing_year - int(year))
    return FeatureResult(max(0.0, 1.0 - gap / 10.0), f"{gap}-year filing gap")


def distance_to_residence(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    comparable = _number(record, "distance_to_residence_miles")
    if proposal.distance_to_residence_miles is None or comparable is None:
        return FeatureResult(None, "omitted: one or both residence distances are unavailable")
    denominator = max(proposal.distance_to_residence_miles, comparable, 0.1)
    score = max(
        0.0,
        1.0
        - abs(proposal.distance_to_residence_miles - comparable) / denominator,
    )
    return FeatureResult(
        score,
        f"{proposal.distance_to_residence_miles:g} mi vs {comparable:g} mi",
    )


def generator_capacity(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    comparable = _number(record, "generator_capacity_mw")
    if comparable is None:
        return FeatureResult(None, "omitted: generator capacity is unavailable")
    if not proposal.has_backup_generators:
        return FeatureResult(0.0, "proposal has no backup generators")
    return FeatureResult(
        None,
        f"omitted: proposal generator capacity is unavailable; comparable={comparable:g} MW",
    )


def permit_status(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    status = str(record.get("permit_status") or "").strip()
    if not proposal.has_backup_generators:
        return FeatureResult(1.0 if not status else 0.0, "proposal has no backup generators")
    if not status:
        return FeatureResult(None, "omitted: DEQ permit status is unavailable")
    return FeatureResult(
        1.0 if status.casefold() == "permitted" else 0.25,
        f"comparable permit status: {status}",
    )


def cluster_density(proposal: Proposal, record: dict[str, Any]) -> FeatureResult:
    density = _number(record, "cluster_density")
    if density is None:
        return FeatureResult(None, "omitted: cluster density is unavailable")
    geography = str(record.get("geography_or_territory") or "")
    same_locality = proposal.locality.casefold() in geography.casefold()
    return FeatureResult(
        float(same_locality),
        f"{'same' if same_locality else 'different'} locality; density={density:g}",
    )


FEATURES = {
    "utility_territory_match": utility_territory_match,
    "rate_vintage_match": rate_vintage_match,
    "scale_mw_proximity": scale_mw_proximity,
    "timing_proximity": timing_proximity,
    "distance_to_residence": distance_to_residence,
    "generator_capacity": generator_capacity,
    "permit_status": permit_status,
    "cluster_density": cluster_density,
}
