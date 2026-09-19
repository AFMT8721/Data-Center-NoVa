import pytest

from src.schemas.proposal import MAX_PROPOSAL_YEAR, Proposal
from src.scoring.score import score_record


@pytest.fixture
def proposal() -> Proposal:
    return Proposal(
        locality="Loudoun",
        utility_territory="Dominion",
        proposed_mw=100,
        filing_year=2026,
        distance_to_residence_miles=0.5,
        has_backup_generators=True,
    )


def test_bill_missing_feature_renormalizes_weights(proposal: Proposal) -> None:
    result = score_record(
        proposal,
        {
            "utility_territory": "Dominion",
            "era": "pre_gs5",
            "scale_mw": None,
            "filing_year": 2024,
        },
        "bill",
    )
    assert result["available_weight"] == pytest.approx(0.75)
    assert result["score"] == pytest.approx(0.96)
    assert result["breakdown"]["scale_mw_proximity"]["value"] is None
    assert result["breakdown"]["utility_territory_match"]["effective_weight"] == pytest.approx(
        0.35 / 0.75
    )


def test_domains_have_separate_feature_breakdowns(proposal: Proposal) -> None:
    result = score_record(
        proposal,
        {
            "distance_to_residence_miles": None,
            "generator_capacity_mw": None,
            "permit_status": None,
            "cluster_density": 358,
            "geography_or_territory": "Loudoun",
        },
        "air",
    )
    assert set(result["breakdown"]) == {
        "distance_to_residence",
        "generator_capacity",
        "permit_status",
        "cluster_density",
    }
    assert result["score"] == pytest.approx(1.0)


def test_all_unknown_features_produce_no_score(proposal: Proposal) -> None:
    result = score_record(proposal, {}, "air")
    assert result["score"] is None
    assert result["available_weight"] == 0


def test_proposal_rejects_implausibly_distant_filing_year() -> None:
    with pytest.raises(ValueError, match="Expected or actual filing year"):
        Proposal(
            locality="Loudoun",
            utility_territory="Dominion",
            proposed_mw=100,
            filing_year=MAX_PROPOSAL_YEAR + 1,
            distance_to_residence_miles=0.5,
            has_backup_generators=True,
        )
