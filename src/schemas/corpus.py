"""Outcome corpus labels and validation."""

from __future__ import annotations

import pandera.pandas as pa

OUTCOME_DOMAINS = ("bill", "air", "fiscal")
OUTCOME_TYPES = ("measured", "projected", "modeled", "permitted")
SPATIAL_GRAINS = ("project", "locality", "region", "state")
SOURCE_INDEPENDENCE = ("independent", "government", "industry-funded", "advocacy")

CORPUS_COLUMNS = [
    "record_id",
    "outcome_domain",
    "outcome_type",
    "spatial_grain",
    "source_independence",
    "source_name",
    "source_url",
    "page_or_section",
    "value_low",
    "value_high",
    "unit",
    "dollars_basis",
    "target_year",
    "geography_or_territory",
    "utility_territory",
    "filing_year",
    "era",
    "scale_mw",
    "distance_to_residence_miles",
    "generator_capacity_mw",
    "permit_status",
    "cluster_density",
    "notes",
    "carry_statement",
    "is_context_only",
]

CORPUS_SCHEMA = pa.DataFrameSchema(
    {
        "record_id": pa.Column(str, nullable=False, unique=True),
        "outcome_domain": pa.Column(str, pa.Check.isin(OUTCOME_DOMAINS), nullable=False),
        "outcome_type": pa.Column(str, pa.Check.isin(OUTCOME_TYPES), nullable=False),
        "spatial_grain": pa.Column(str, pa.Check.isin(SPATIAL_GRAINS), nullable=False),
        "source_independence": pa.Column(
            str, pa.Check.isin(SOURCE_INDEPENDENCE), nullable=False
        ),
        "source_name": pa.Column(str, nullable=False),
        "source_url": pa.Column(str, nullable=True),
        "page_or_section": pa.Column(str, nullable=True),
        "value_low": pa.Column(float, nullable=True),
        "value_high": pa.Column(float, nullable=True),
        "unit": pa.Column(str, nullable=True),
        "dollars_basis": pa.Column(str, nullable=True),
        "target_year": pa.Column(float, nullable=True),
        "geography_or_territory": pa.Column(str, nullable=False),
        "utility_territory": pa.Column(str, nullable=True),
        "filing_year": pa.Column(float, nullable=True),
        "era": pa.Column(str, pa.Check.isin(["pre_gs5", "gs5"]), nullable=True),
        "scale_mw": pa.Column(float, pa.Check.ge(0), nullable=True),
        "distance_to_residence_miles": pa.Column(float, pa.Check.ge(0), nullable=True),
        "generator_capacity_mw": pa.Column(float, pa.Check.ge(0), nullable=True),
        "permit_status": pa.Column(str, nullable=True),
        "cluster_density": pa.Column(float, pa.Check.ge(0), nullable=True),
        "notes": pa.Column(str, nullable=True),
        "carry_statement": pa.Column(str, nullable=False),
        "is_context_only": pa.Column(bool, nullable=False),
    },
    strict=True,
    coerce=True,
)
