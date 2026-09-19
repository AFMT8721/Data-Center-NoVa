"""Resident proposal contract."""

from dataclasses import dataclass
from datetime import date

MIN_PROPOSAL_YEAR = 2015
MAX_PROPOSAL_YEAR = date.today().year + 5


@dataclass(frozen=True)
class Proposal:
    locality: str
    utility_territory: str
    proposed_mw: float
    filing_year: int
    distance_to_residence_miles: float | None
    has_backup_generators: bool

    def __post_init__(self) -> None:
        if self.utility_territory not in {"Dominion", "NOVEC", "other", "unknown"}:
            raise ValueError("Unsupported utility territory")
        if self.proposed_mw < 0:
            raise ValueError("Proposed MW must be nonnegative")
        if not MIN_PROPOSAL_YEAR <= self.filing_year <= MAX_PROPOSAL_YEAR:
            raise ValueError(
                "Expected or actual filing year must be between "
                f"{MIN_PROPOSAL_YEAR} and {MAX_PROPOSAL_YEAR}"
            )
        if (
            self.distance_to_residence_miles is not None
            and self.distance_to_residence_miles < 0
        ):
            raise ValueError("Distance must be nonnegative")

    @property
    def era(self) -> str:
        return "gs5" if self.filing_year >= 2027 else "pre_gs5"
