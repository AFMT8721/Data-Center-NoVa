import json

from src.schemas.proposal import Proposal
from src.scoring import synthesis


def _proposal() -> Proposal:
    return Proposal(
        locality="Loudoun",
        utility_territory="Dominion",
        proposed_mw=100,
        filing_year=2026,
        distance_to_residence_miles=0.5,
        has_backup_generators=True,
    )


def _evidence() -> list[dict[str, object]]:
    return [
        {
            "record_id": "jlarc-bill",
            "outcome_type": "projected",
            "source_name": "JLARC",
            "value_low": 14,
            "value_high": 37,
            "target_year": 2040,
            "carry_statement": "Cannot predict one household.",
        }
    ]


def test_validator_accepts_grounded_answer() -> None:
    answer = (
        "JLARC projected a $14 to $37 regional range by 2040. "
        "It cannot estimate one household's bill."
    )
    assert synthesis.validate_synthesis(
        answer,
        ["jlarc-bill"],
        _evidence(),
        {"proposed_mw": 100, "filing_year": 2026},
    )


def test_validator_rejects_unknown_citation() -> None:
    assert not synthesis.validate_synthesis(
        "A projection exists.",
        ["invented-record"],
        _evidence(),
        {},
    )


def test_validator_rejects_invented_number() -> None:
    assert not synthesis.validate_synthesis(
        "The increase could be $99.",
        ["jlarc-bill"],
        _evidence(),
        {},
    )


def test_validator_rejects_prediction_claim() -> None:
    assert not synthesis.validate_synthesis(
        "Your bill will rise by $14.",
        ["jlarc-bill"],
        _evidence(),
        {},
    )


def test_synthesis_parses_valid_structured_response(monkeypatch) -> None:
    generated = (
        "JLARC projected a $14 to $37 regional range by 2040. "
        "It cannot estimate one household's bill."
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "response": json.dumps(
                        {"answer": generated, "citations": ["jlarc-bill"]}
                    )
                }
            ).encode()

    monkeypatch.setattr(
        synthesis.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: Response(),
    )
    result = synthesis.synthesize_answer(
        "What will my bill be?",
        "bill_prediction",
        _proposal(),
        _evidence(),
    )
    assert result == f"{generated} Sources: [jlarc-bill]"
