from pathlib import Path

import pandas as pd
import pytest

from src.schemas.proposal import Proposal
from src.scoring.reply import (
    build_public_reply,
    build_reply,
    enforce_public_reply_contract,
    enforce_reply_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def _proposal(territory: str = "Dominion") -> Proposal:
    return Proposal(
        locality="Loudoun",
        utility_territory=territory,
        proposed_mw=100,
        filing_year=2026,
        distance_to_residence_miles=0.5,
        has_backup_generators=True,
    )


def test_bill_reply_uses_anchor_and_refuses_prediction() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    reply = build_reply("What will my electricity bill be?", _proposal(), corpus)
    assert "$14 to $37" in reply
    assert "projected" in reply
    assert "No single-project figure can be attributed" in reply
    assert "How far this carries:" in reply


def test_novec_proposal_triggers_territory_flag() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    reply = build_reply("Compare bill evidence", _proposal("NOVEC"), corpus)
    assert "Territory flag" in reply
    assert "does not apply directly to a NOVEC customer" in reply


def test_guard_blocks_unsupported_dollar_claim() -> None:
    with pytest.raises(ValueError, match="unsupported per-resident"):
        enforce_reply_contract("Your bill will be $99.")


def test_public_bill_answer_is_plain_language_and_uses_anchor() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    reply = build_public_reply(
        "Can this prototype tell me what my bill will be?",
        _proposal(),
        corpus,
    )
    assert "$14 to $37" in reply
    assert "cannot estimate your household bill" in reply
    assert "Similarity score:" in reply
    assert "configured weight" not in reply
    assert "pre_gs5" not in reply


def test_public_air_answer_explains_non_attribution() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    reply = build_public_reply(
        "What does the air map show for my county?",
        _proposal(),
        corpus,
    )
    assert "monitored county conditions" in reply
    assert "cannot identify which source caused" in reply
    assert "configured weight" not in reply


def test_public_guard_blocks_unsupported_household_claim() -> None:
    with pytest.raises(ValueError, match="unsupported household"):
        enforce_public_reply_contract("Your household bill will increase by $99.")


@pytest.mark.parametrize(
    ("proposal_id", "expected_text", "absent_text"),
    [
        (
            "dominion_pre_gs5",
            "No single-project figure can be attributed",
            "Territory flag",
        ),
        ("novec_flag", "does not apply directly to a NOVEC customer", None),
        ("unknown_territory", "utility territory is not verified", None),
        ("no_backup_generators", "proposal has no backup generators", None),
        ("gs5_vintage", "gs5 vs pre_gs5", None),
    ],
)
def test_hand_written_proposals(
    proposal_id: str, expected_text: str, absent_text: str | None
) -> None:
    proposals = pd.read_csv(ROOT / "data/curated/test_proposals.csv")
    row = proposals.loc[proposals["proposal_id"].eq(proposal_id)].iloc[0]
    proposal = Proposal(
        locality=row["locality"],
        utility_territory=row["utility_territory"],
        proposed_mw=float(row["proposed_mw"]),
        filing_year=int(row["filing_year"]),
        distance_to_residence_miles=float(row["distance_to_residence_miles"]),
        has_backup_generators=bool(row["has_backup_generators"]),
    )
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    reply = build_reply(row["query"], proposal, corpus)
    assert expected_text.casefold() in reply.casefold()
    if absent_text:
        assert absent_text.casefold() not in reply.casefold()
