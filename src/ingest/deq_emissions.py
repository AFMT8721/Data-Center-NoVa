"""Read historical DEQ facility-wide criteria-emissions exports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

POLLUTANT_COLUMNS = {
    "CO Emissions in Tons": "co_tons",
    "NH3 Emissions in Tons": "nh3_tons",
    "NO2 Emissions in Tons": "nox_tons",
    "NOX Emissions in Tons": "nox_tons",
    "PM 10 Emissions in Tons": "pm10_tons",
    "PM 2.5 Emissions in Tons": "pm25_tons",
    "SO2 Emissions in Tons": "so2_tons",
    "VOC Emissions in Tons": "voc_tons",
}


def load_criteria_emissions(
    path: Path, permit_registration_numbers: set[str] | None = None
) -> pd.DataFrame:
    """Return valid facility rows, optionally limited to known permit registrations."""
    frame = pd.read_csv(path, dtype=str)
    required = {
        "Region",
        "Reg #",
        "Facility Name",
        "County",
        "Facility Total",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path}: missing criteria-emissions columns {missing}")
    frame = frame.rename(
        columns={
            "Region": "region",
            "Reg #": "registration_number",
            "Facility Name": "facility_name",
            "Classification": "classification",
            "FIPS": "fips",
            "County": "city_or_county",
            "SIC": "sic",
            "NAICS": "naics",
            "Facility Total": "facility_total_tons",
            **POLLUTANT_COLUMNS,
        }
    )
    frame["registration_number"] = (
        frame["registration_number"].str.strip().str.lstrip("0")
    )
    frame = frame.loc[frame["registration_number"].str.fullmatch(r"\d+", na=False)]
    if permit_registration_numbers is not None:
        normalized = {str(value).strip().lstrip("0") for value in permit_registration_numbers}
        frame = frame.loc[frame["registration_number"].isin(normalized)]
    numeric = ["facility_total_tons", *set(POLLUTANT_COLUMNS.values())]
    for column in numeric:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["emissions_year"] = 2015
    frame["source_file"] = path.as_posix()
    columns = [
        "registration_number",
        "facility_name",
        "classification",
        "region",
        "fips",
        "city_or_county",
        "sic",
        "naics",
        *sorted(set(POLLUTANT_COLUMNS.values())),
        "facility_total_tons",
        "emissions_year",
        "source_file",
    ]
    return frame[[column for column in columns if column in frame]].reset_index(drop=True)
