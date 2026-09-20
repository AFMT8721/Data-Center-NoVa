"""Deterministic resident-facing reply templates and contract guards."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.schemas.proposal import Proposal
from src.scoring.intent import classify_intent, keyword_intent
from src.scoring.score import rank_domain
from src.scoring.weights import WEIGHTS

MONEY_PATTERN = re.compile(r"\$\s?\d+(?:\.\d+)?")
ALLOWED_ANCHOR_MONEY = {"$14", "$37"}

PUBLIC_FEATURE_LABELS = {
    "utility_territory_match": "Electric utility",
    "rate_vintage_match": "Rate-policy period",
    "scale_mw_proximity": "Project size",
    "timing_proximity": "Timing",
    "distance_to_residence": "Distance from homes",
    "generator_capacity": "Backup-generator size",
    "permit_status": "Air-permit status",
    "cluster_density": "Nearby development concentration",
}
PUBLIC_OUTCOME_LABELS = {
    "measured": "Observed data",
    "projected": "Projection",
    "modeled": "Modeled estimate",
    "permitted": "Permit conditions",
}
PUBLIC_GRAIN_LABELS = {
    "project": "One project",
    "locality": "County or locality",
    "region": "Regional",
    "state": "Statewide",
}
PUBLIC_SOURCE_LABELS = {
    "independent": "Independent research",
    "government": "Government-published",
    "industry-funded": "Industry-funded",
    "advocacy": "Advocacy organization",
}


def _format_score(value: float | None) -> str:
    return "unavailable from delivered fields" if value is None else f"{value:.3f}"


def _citation(record: dict[str, Any]) -> str:
    source = record["source_name"]
    locator = record.get("page_or_section") or "locator unavailable"
    url = record.get("source_url")
    return f"[{source}]({url}), {locator}" if url else f"{source}, {locator}"


def _card(record: dict[str, Any]) -> str:
    breakdown = []
    for feature, item in record["breakdown"].items():
        value = "omitted" if item["value"] is None else f"{item['value']:.3f}"
        breakdown.append(
            f"  - `{feature}`: {value}; configured weight "
            f"{item['configured_weight']:.2f}; effective weight "
            f"{item['effective_weight']:.2f}. {item['reason']}"
        )
    value_text = ""
    if record["record_id"] == "jlarc-2024-dominion-bill-2040":
        value_text = (
            "\n- Documented result: **$14 to $37 per month by 2040**, "
            "constant 2024 dollars, for a typical Dominion residential customer."
        )
    elif pd.notna(record.get("value_low")) and pd.notna(record.get("value_high")):
        value_text = (
            f"\n- Documented range: {record['value_low']:g} to "
            f"{record['value_high']:g} {record.get('unit') or ''}."
        )
    return "\n".join(
        [
            f"#### {record['record_id']}",
            f"- Labels: `{record['outcome_domain']}` / `{record['outcome_type']}` / "
            f"`{record['spatial_grain']}` / `{record['source_independence']}`",
            f"- Citation: {_citation(record)}",
            f"- Comparability score: **{_format_score(record['score'])}** "
            f"(available configured weight: {record['available_weight']:.2f})",
            value_text.lstrip("\n"),
            "- Feature breakdown:",
            *breakdown,
            f"- **How far this carries:** {record['carry_statement']}",
        ]
    ).replace("\n\n", "\n")


def _territory_warning(proposal: Proposal) -> str:
    if proposal.utility_territory == "Dominion":
        return ""
    if proposal.utility_territory == "NOVEC":
        return (
            "> Territory flag: proposal is marked NOVEC. The JLARC Dominion bill "
            "projection is shown as regional evidence but does not apply directly "
            "to a NOVEC customer."
        )
    return (
        "> Territory flag: utility territory is not verified as Dominion. The JLARC "
        "Dominion bill projection cannot be treated as directly applicable."
    )


def enforce_reply_contract(reply: str) -> str:
    money = set(MONEY_PATTERN.findall(reply))
    if money and (
        not money.issubset(ALLOWED_ANCHOR_MONEY)
        or "jlarc-2024-dominion-bill-2040" not in reply
        or "no single-project figure can be attributed" not in reply.lower()
    ):
        raise ValueError("Reply contract blocked an unsupported per-resident dollar figure")
    required = (
        "Labels:",
        "Citation:",
        "Comparability score:",
        "Feature breakdown:",
        "How far this carries:",
    )
    if "#### " in reply and any(item not in reply for item in required):
        raise ValueError("Reply contract blocked an incomplete evidence card")
    return reply


def build_reply(
    query: str,
    proposal: Proposal,
    corpus: pd.DataFrame,
    top_k: int = 3,
) -> str:
    query_lower = query.casefold()
    asks_bill = any(word in query_lower for word in ("bill", "cost", "electric", "rate"))
    asks_air = any(word in query_lower for word in ("air", "generator", "emission", "aqi"))
    domains = ["bill", "air"] if not (asks_bill or asks_air) else []
    if asks_bill:
        domains.append("bill")
    if asks_air:
        domains.append("air")

    sections = [
        "## Comparable evidence",
        "Scores are a transparent weighted heuristic, not a calibrated model.",
    ]
    if "bill" in domains:
        warning = _territory_warning(proposal)
        if warning:
            sections.append(warning)
        sections.append(
            "The JLARC range is anchor evidence. No single-project figure can be "
            "attributed, and this tool does not predict what any resident's bill will be."
        )
    for domain in domains:
        sections.append(f"### {domain.title()} domain")
        sections.append(
            "Configured weights: "
            + ", ".join(f"`{name}`={weight:.2f}" for name, weight in WEIGHTS[domain].items())
        )
        ranked = rank_domain(proposal, corpus, domain)
        selected = ranked[:top_k]
        if not selected:
            sections.append("No delivered evidence records are available for this domain.")
        else:
            sections.extend(_card(record) for record in selected)
    return enforce_reply_contract("\n\n".join(sections))


def _public_match_description(feature: str, item: dict[str, Any]) -> str:
    label = PUBLIC_FEATURE_LABELS[feature]
    value = item["value"]
    if value is None:
        return f"- **{label}:** Information unavailable; this factor did not affect ranking."
    if value >= 0.8:
        strength = "Strong match"
    elif value >= 0.5:
        strength = "Partial match"
    else:
        strength = "Weak match"
    if feature == "rate_vintage_match":
        explanation = (
            "Evidence and proposal fall on the same side of Dominion's 2027 "
            "large-customer rate change."
            if value >= 0.8
            else "Evidence and proposal fall on different sides of Dominion's "
            "2027 large-customer rate change."
        )
    elif feature == "utility_territory_match":
        explanation = "Utility areas match." if value >= 0.8 else "Utility areas differ."
    else:
        explanation = str(item["reason"]).replace("omitted: ", "").capitalize()
    return f"- **{label}:** {strength}. {explanation}"


def _public_limit(record: dict[str, Any]) -> str:
    outcome_type = record["outcome_type"]
    grain = record["spatial_grain"]
    if outcome_type == "projected":
        return (
            "Useful for understanding a possible regional future. It is not an "
            "observed result and cannot predict one household or one project."
        )
    if outcome_type == "permitted":
        return (
            "Shows what regulators permitted. It does not show actual generator "
            "use, emissions, or neighborhood air quality."
        )
    if grain == "locality":
        return (
            "Shows monitored conditions across a locality. It cannot identify "
            "which source caused those conditions."
        )
    if grain == "region":
        return (
            "Shows utility-area conditions. It cannot isolate the effect of one "
            "development."
        )
    return (
        "Describes this evidence record only. Results should not be transferred "
        "to another project without checking site differences."
    )


def _public_card(
    record: dict[str, Any], heading: str = "Best matching evidence"
) -> str:
    score = record["score"]
    score_text = (
        "Not enough delivered information to score"
        if score is None
        else f"{round(score * 100):d} out of 100"
    )
    range_text = ""
    if record["record_id"] == "jlarc-2024-dominion-bill-2040":
        range_text = (
            "\n- **Published finding:** $14 to $37 per month by 2040 for a "
            "typical Dominion residential customer, in constant 2024 dollars."
        )
    elif pd.notna(record.get("value_low")) and pd.notna(record.get("value_high")):
        range_text = (
            f"\n- **Published range:** {record['value_low']:g} to "
            f"{record['value_high']:g} {record.get('unit') or ''}."
        )
    match_lines = [
        _public_match_description(feature, item)
        for feature, item in record["breakdown"].items()
    ]
    return "\n".join(
        [
            f"### {heading}",
            f"- **Evidence type:** {PUBLIC_OUTCOME_LABELS[record['outcome_type']]}",
            f"- **Area covered:** {PUBLIC_GRAIN_LABELS[record['spatial_grain']]}",
            f"- **Publisher type:** "
            f"{PUBLIC_SOURCE_LABELS[record['source_independence']]}",
            f"- **Source:** {_citation(record)}",
            f"- **Similarity score:** {score_text}. This is a sorting aid, not a forecast.",
            range_text.lstrip("\n"),
            "",
            "#### Why it matched",
            *match_lines,
            "",
            "#### What this evidence can and cannot tell you",
            _public_limit(record),
        ]
    ).replace("\n\n\n", "\n\n")


def _public_territory_warning(proposal: Proposal) -> str:
    if proposal.utility_territory == "Dominion":
        return ""
    if proposal.utility_territory == "NOVEC":
        return (
            "> **Utility warning:** You selected NOVEC. Dominion projections do "
            "not directly describe a NOVEC household."
        )
    return (
        "> **Utility warning:** Dominion service has not been confirmed. Treat "
        "Dominion projections as background information only."
    )


def enforce_public_reply_contract(reply: str) -> str:
    money = set(MONEY_PATTERN.findall(reply))
    if money and (
        not money.issubset(ALLOWED_ANCHOR_MONEY)
        or "JLARC" not in reply
        or "cannot estimate your household bill" not in reply.lower()
    ):
        raise ValueError("Public reply blocked an unsupported household dollar claim")
    required = (
        "Evidence type:",
        "Area covered:",
        "Publisher type:",
        "Source:",
        "Similarity score:",
        "Why it matched",
        "What this evidence can and cannot tell you",
    )
    if "### Best matching" in reply and any(
        item not in reply for item in required
    ):
        raise ValueError("Public reply blocked an incomplete evidence summary")
    return reply


def _rank_for_intent(
    proposal: Proposal,
    corpus: pd.DataFrame,
    intent: str,
) -> list[dict[str, Any]]:
    if intent.startswith("bill_"):
        return rank_domain(proposal, corpus, "bill")
    if intent == "air_quality":
        evidence = corpus.loc[
            corpus["source_name"].eq("U.S. EPA daily AQI by county")
        ]
    elif intent == "air_permit":
        evidence = corpus.loc[
            corpus["outcome_type"].eq("permitted")
            | corpus["source_name"].eq(
                "Virginia DEQ 2015 criteria emissions inventory"
            )
        ]
    else:
        evidence = corpus
    return rank_domain(proposal, evidence, "air")


def _select_air_quality(
    proposal: Proposal, ranked: list[dict[str, Any]]
) -> dict[str, Any]:
    normalized_locality = (
        proposal.locality.casefold()
        .replace(" county", "")
        .replace(" city", "")
        .strip()
    )
    local = [
        record
        for record in ranked
        if normalized_locality
        in str(record.get("geography_or_territory", "")).casefold()
    ]
    eligible = [
        record
        for record in local
        if pd.notna(record.get("target_year"))
        and int(record["target_year"]) <= proposal.filing_year
    ]
    choices = eligible or local or ranked
    return max(
        choices,
        key=lambda record: (
            int(record["target_year"])
            if pd.notna(record.get("target_year"))
            else -1
        ),
    )


def build_public_reply(
    query: str,
    proposal: Proposal,
    corpus: pd.DataFrame,
) -> str:
    """Answer one resident question with plain-language, cited evidence."""
    model_intent = classify_intent(query)
    intent = model_intent or keyword_intent(query)
    if intent == "unrelated":
        return (
            "I'm just a tiny open-weight model running on someone's laptop — "
            "what do you think I am, JARVIS?! I can only help with electricity "
            "bills or air quality near a proposed data center. Try one of the "
            "suggested questions above."
            "\n\n_Routed by local Llama 3.2 3B: `unrelated`._"
        )
    if model_intent is not None:
        routing_note = f"_Routed by local Llama 3.2 3B: `{intent}`._"
    else:
        routing_note = (
            f"_Routed by deterministic fallback: `{intent}` "
            "(local model unavailable)._"
        )

    sections = ["## Plain-language answer"]
    if intent == "both":
        bill_ranked = rank_domain(proposal, corpus, "bill")
        air_ranked = _rank_for_intent(proposal, corpus, "air_quality")
        if not bill_ranked or not air_ranked:
            return "No delivered evidence is available for that topic."
        warning = _public_territory_warning(proposal)
        if warning:
            sections.append(warning)
        sections.append(
            "This prototype **cannot estimate your household bill** or attribute "
            "neighborhood air conditions to one project. Here is one documented "
            "record from each topic."
        )
        sections.append(_public_card(bill_ranked[0], "Best matching bill evidence"))
        sections.append(
            _public_card(
                _select_air_quality(proposal, air_ranked),
                "Best matching air evidence",
            )
        )
    elif intent in {"bill_prediction", "bill_context"}:
        ranked = _rank_for_intent(proposal, corpus, intent)
        if not ranked:
            return "No delivered evidence is available for that topic."
        warning = _public_territory_warning(proposal)
        if warning:
            sections.append(warning)
        if intent == "bill_prediction":
            selected = next(
                (
                    record
                    for record in ranked
                    if record["record_id"] == "jlarc-2024-dominion-bill-2040"
                ),
                ranked[0],
            )
            sections.append(
                "This prototype **cannot estimate your household bill from one "
                "proposed development**. JLARC projected that a typical Dominion "
                "residential customer's generation and transmission costs could "
                "rise **$14 to $37 per month by 2040** in constant 2024 dollars. "
                "That estimate covers regional growth and is not attributable to "
                "this proposal."
            )
        else:
            selected = ranked[0]
            sections.append(
                "Published utility records provide historical rate context. This "
                "prototype **cannot estimate your household bill** or isolate one "
                "project's effect."
            )
        sections.append(_public_card(selected))
    elif intent == "air_quality":
        ranked = _rank_for_intent(proposal, corpus, intent)
        if not ranked:
            return "No delivered evidence is available for that topic."
        sections.append(
            "County AQI records describe monitored air conditions. They do not "
            "measure emissions from the proposed site or determine what caused "
            "a particular reading."
        )
        sections.append(_public_card(_select_air_quality(proposal, ranked)))
    else:
        ranked = _rank_for_intent(proposal, corpus, "air_permit")
        if not ranked:
            return "No delivered evidence is available for that topic."
        sections.append(
            "DEQ permits describe allowed equipment and operating conditions—not "
            "actual emissions. Matched 2015 inventory records are historical "
            "facility-wide totals, not generator-only or current measurements."
        )
        sections.append(_public_card(ranked[0]))
    sections.append(routing_note)
    return enforce_public_reply_contract("\n\n".join(sections))
