"""Build the labeled evidence corpus from curated and delivered sources."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ingest.aqi import load_aqi_context
from src.ingest.deq_emissions import load_criteria_emissions
from src.ingest.deq_permits import load_deq_permits
from src.ingest.eia861 import load_eia861_context
from src.schemas.corpus import CORPUS_COLUMNS, CORPUS_SCHEMA

ANCHOR_COLUMNS = [
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
    "notes",
]


def carry_statement(outcome_type: str, spatial_grain: str, context_only: bool) -> str:
    type_clause = {
        "measured": "This is measured evidence",
        "projected": "This is a projection, not a realized outcome",
        "modeled": "This is a modeled estimate, not a measured outcome",
        "permitted": "This documents permitted capacity, not actual emissions",
    }[outcome_type]
    grain_clause = {
        "project": "It is project-specific but does not transfer automatically to another site.",
        "locality": "It describes locality conditions and cannot be attributed to one development.",
        "region": "It describes a region and cannot establish a single-project effect.",
        "state": "It describes statewide conditions and cannot establish a local project effect.",
    }[spatial_grain]
    context_clause = " It is context only, not a project outcome." if context_only else ""
    return f"{type_clause}. {grain_clause}{context_clause}"


def _base_record() -> dict[str, object]:
    return {column: None for column in CORPUS_COLUMNS}


def _anchors(path: Path) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    missing = sorted(set(ANCHOR_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"{path}: missing anchor columns {missing}")
    records: list[dict[str, object]] = []
    for raw in frame.to_dict(orient="records"):
        record = _base_record()
        record.update(raw)
        record.update(
            {
                "utility_territory": "Dominion",
                "filing_year": 2024,
                "era": "pre_gs5",
                "carry_statement": carry_statement(
                    raw["outcome_type"], raw["spatial_grain"], False
                ),
                "is_context_only": False,
            }
        )
        records.append(record)
    return records


def _eia_records(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in load_eia861_context(path).to_dict(orient="records"):
        record = _base_record()
        year = int(row["year"])
        territory = row["utility_territory"]
        price = row["average_price_cents_per_kwh"]
        record.update(
            {
                "record_id": f"eia861-{territory.lower()}-{year}-residential",
                "outcome_domain": "bill",
                "outcome_type": "measured",
                "spatial_grain": "region",
                "source_independence": "government",
                "source_name": "U.S. EIA Form EIA-861",
                "source_url": "",
                "page_or_section": str(row["source_file"]),
                "value_low": price,
                "value_high": price,
                "unit": "cents per kWh, residential average",
                "dollars_basis": "",
                "target_year": year,
                "geography_or_territory": f"{territory} Virginia utility territory",
                "utility_territory": territory,
                "filing_year": year,
                "era": "pre_gs5" if year < 2027 else "gs5",
                "notes": (
                    f"EIA data_status={row['data_status']}. Utility-level rate context; "
                    "not a data-center-attributed outcome. Source URL and pull date unverified."
                ),
                "carry_statement": carry_statement("measured", "region", True),
                "is_context_only": True,
            }
        )
        records.append(record)
    return records


def _aqi_records(path: Path, loudoun_density: float | None) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in load_aqi_context(path).to_dict(orient="records"):
        locality = str(row["county_or_city_name"])
        year = int(row["year"])
        record = _base_record()
        record.update(
            {
                "record_id": f"epa-aqi-{locality.lower().replace(' ', '-')}-{year}",
                "outcome_domain": "air",
                "outcome_type": "measured",
                "spatial_grain": "locality",
                "source_independence": "government",
                "source_name": "U.S. EPA daily AQI by county",
                "source_url": row["source_url"],
                "page_or_section": f"daily observations aggregated for {year}",
                "value_low": row["value_low"],
                "value_high": row["value_high"],
                "unit": "AQI daily minimum to maximum",
                "dollars_basis": "",
                "target_year": year,
                "geography_or_territory": locality,
                "filing_year": year,
                "era": "pre_gs5" if year < 2027 else "gs5",
                "cluster_density": loudoun_density if locality == "Loudoun" else None,
                "notes": (
                    f"{int(row['observation_days'])} daily observations; downloaded_on="
                    f"{row['downloaded_on']}. Ambient county AQI is not attributable to "
                    "a data center or its generators."
                ),
                "carry_statement": carry_statement("measured", "locality", True),
                "is_context_only": True,
            }
        )
        records.append(record)
    return records


def _deq_records(path: Path | None) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in load_deq_permits(path).to_dict(orient="records"):
        if pd.isna(row.get("city_or_county")):
            continue
        year = int(pd.Timestamp(row["issuance_date"]).year)
        registration = str(row["registration_number"])
        issued = pd.Timestamp(row["issuance_date"]).date().isoformat()
        details = [
            f"Site={row['site_name']}" if pd.notna(row.get("site_name")) else None,
            f"program={row['program_type']}" if pd.notna(row.get("program_type")) else None,
            f"fuel={row['fuel']}" if pd.notna(row.get("fuel")) else None,
            (
                f"operating-limit text={row['operating_limits']}"
                if pd.notna(row.get("operating_limits"))
                else None
            ),
            (
                f"pollutant-limit text={row['pollutant_limits']}"
                if pd.notna(row.get("pollutant_limits"))
                else None
            ),
            f"source_file={row['source_file']}",
            f"unverified_fields={row['unverified_fields']}",
        ]
        record = _base_record()
        record.update(
            {
                "record_id": f"deq-permit-{registration}-{issued}",
                "outcome_domain": "air",
                "outcome_type": "permitted",
                "spatial_grain": "project",
                "source_independence": "government",
                "source_name": "Virginia DEQ issued data center air permits",
                "source_url": row["permit_url"],
                "page_or_section": f"registration {registration}; issued {issued}",
                "unit": "permit conditions; not measured emissions",
                "target_year": year,
                "geography_or_territory": row["city_or_county"],
                "filing_year": year,
                "era": "pre_gs5" if year < 2027 else "gs5",
                "generator_capacity_mw": row.get("generator_capacity_mw"),
                "permit_status": "permitted",
                "notes": "; ".join(str(item) for item in details if item)
                + ". Permit conditions do not establish actual emissions.",
                "carry_statement": carry_statement("permitted", "project", False),
                "is_context_only": False,
            }
        )
        records.append(record)
    return records


def _deq_emission_records(
    path: Path, permit_registration_numbers: set[str]
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    emissions = load_criteria_emissions(path, permit_registration_numbers)
    pollutants = (
        "co_tons",
        "nh3_tons",
        "nox_tons",
        "pm10_tons",
        "pm25_tons",
        "so2_tons",
        "voc_tons",
    )
    for row in emissions.to_dict(orient="records"):
        registration = str(row["registration_number"])
        values = ", ".join(
            f"{name.removesuffix('_tons')}={row[name]:g} tons"
            for name in pollutants
            if name in row and pd.notna(row[name])
        )
        record = _base_record()
        record.update(
            {
                "record_id": f"deq-criteria-2015-{registration}",
                "outcome_domain": "air",
                "outcome_type": "measured",
                "spatial_grain": "project",
                "source_independence": "government",
                "source_name": "Virginia DEQ 2015 criteria emissions inventory",
                "source_url": "",
                "page_or_section": (
                    f"registration {registration}; "
                    f"{Path(str(row['source_file'])).name}"
                ),
                "value_low": row["facility_total_tons"],
                "value_high": row["facility_total_tons"],
                "unit": "tons/year, facility total criteria pollutants",
                "target_year": 2015,
                "geography_or_territory": row["city_or_county"],
                "filing_year": 2015,
                "era": "pre_gs5",
                "notes": (
                    f"Facility={row['facility_name']}; classification="
                    f"{row['classification']}; {values}. Historical facility-wide "
                    "inventory total; not generator-only, current, or attributable "
                    "to a proposed project."
                ),
                "carry_statement": carry_statement("measured", "project", False),
                "is_context_only": False,
            }
        )
        records.append(record)
    return records


def build_corpus(root: Path) -> pd.DataFrame:
    projects_path = root / "data/interim/landmarc_projects.parquet"
    loudoun_density = (
        float(len(pd.read_parquet(projects_path))) if projects_path.exists() else None
    )
    deq_extract = root / "data/interim/deq_permits_extracted.csv"
    permits = load_deq_permits(deq_extract if deq_extract.exists() else None)
    records = _anchors(root / "data/curated/anchor_outcomes.csv")
    records.extend(_eia_records(root / "data/raw/eia861_sales_ultimate_customers_2015_2025.csv"))
    records.extend(_aqi_records(root / "data/raw/virginia_daily_aqi_by_county_2015_2026.csv", loudoun_density))
    records.extend(_deq_records(deq_extract if deq_extract.exists() else None))
    permit_registrations = set(permits["registration_number"].dropna().astype(str))
    records.extend(
        _deq_emission_records(
            root / "data/raw/2015_criteria_emissions_10tons.csv",
            permit_registrations,
        )
    )
    frame = pd.DataFrame(records, columns=CORPUS_COLUMNS)
    frame = CORPUS_SCHEMA.validate(frame)
    output = root / "data/processed/outcome_corpus.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    frame.to_csv(output.with_suffix(".csv"), index=False)
    return frame


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    corpus = build_corpus(project_root)
    print(corpus.groupby(["outcome_domain", "outcome_type", "spatial_grain"]).size())
