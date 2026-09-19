from pathlib import Path

import pandas as pd

from src.ingest import deq_permits
from src.ingest.deq_emissions import load_criteria_emissions

ROOT = Path(__file__).resolve().parents[1]


def test_pdf_parser_keeps_only_explicit_fields(monkeypatch) -> None:
    pages = [
        """VIRGINIA DEPARTMENT OF ENVIRONMENTAL QUALITY
NORTHERN REGIONAL OFFICE
March 19, 2024
Location: Loudoun County
Registration No.: 73233
Attached is a permit approval to construct and operate a project at a data center.
""",
        """STATIONARY SOURCE PERMIT TO CONSTRUCT AND OPERATE
In compliance with the Federal Clean Air Act and the Commonwealth of Virginia
Regulations for the Control and Abatement of Air Pollution,
Equinix, LLC
21711 Filigree Court
Ashburn, Virginia 20147
Registration No.: 73233
is authorized to construct and operate
emergency diesel engine generator-sets
located at
21691 Filigree Court
Ashburn, Virginia 20147
(Loudoun County)
in accordance with the Conditions of this permit document.
JAW/CLS/73233 mNSR (2024-03-19)
""",
    ]
    monkeypatch.setattr(deq_permits, "_extract_pages", lambda _: pages)
    row = deq_permits.extract_deq_pdf(Path("permit.pdf"))
    assert row["site_name"] == "Equinix, LLC"
    assert row["registration_number"] == "73233"
    assert row["issuance_date"] == "March 19, 2024"
    assert row["program_type"] == "Minor NSR"
    assert row["city_or_county"] == "Loudoun County"
    assert row["address"] == "21691 Filigree Court, Ashburn, Virginia 20147"
    assert row["fuel"] == "diesel"
    assert row["generator_count"] is None
    assert row["generator_capacity_mw"] is None
    assert "generator_count" in row["unverified_fields"]
    assert "permit_url" in row["unverified_fields"]


def test_criteria_emissions_match_known_permit_registrations() -> None:
    frame = load_criteria_emissions(
        ROOT / "data/raw/2015_criteria_emissions_10tons.csv",
        {"73233", "73743", "72367"},
    )
    assert set(frame["registration_number"]) == {"73233", "73743", "72367"}
    assert pd.api.types.is_numeric_dtype(frame["facility_total_tons"])
