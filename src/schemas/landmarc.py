"""LandMARC input and project-level output contracts."""

from __future__ import annotations

import pandera.pandas as pa


LANDMARC_REQUIRED_COLUMNS = {
    "Case Number",
    "Type",
    "Status",
    "Project Name",
    "Applied Date",
    "Module Name",
    "Address",
    "Main Parcel",
    "Description",
}

PROJECT_SCHEMA = pa.DataFrameSchema(
    {
        "project_id": pa.Column(str, nullable=False, unique=True),
        "project_name": pa.Column(str, nullable=True),
        "address": pa.Column(str, nullable=True),
        "main_parcel": pa.Column(str, nullable=True),
        "locality": pa.Column(str, nullable=False),
        "module_tiers": pa.Column(str, nullable=False),
        "record_types": pa.Column(str, nullable=False),
        "statuses": pa.Column(str, nullable=False),
        "applied_date": pa.Column(pa.DateTime, nullable=False),
        "filing_year": pa.Column(int, pa.Check.ge(2015), nullable=False),
        "era": pa.Column(str, pa.Check.isin(["pre_gs5", "gs5"]), nullable=False),
        "source_case_numbers": pa.Column(str, nullable=False),
        "source_files": pa.Column(str, nullable=False),
        "source_row_count": pa.Column(int, pa.Check.ge(1), nullable=False),
    },
    strict=True,
    coerce=True,
)


def validate_landmarc_columns(columns: set[str], source: str) -> None:
    """Raise a traceable error when a raw export lacks required columns."""
    missing = sorted(LANDMARC_REQUIRED_COLUMNS - columns)
    if missing:
        raise ValueError(f"{source}: missing LandMARC columns: {missing}")
