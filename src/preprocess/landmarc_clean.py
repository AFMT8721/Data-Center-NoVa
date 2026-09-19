"""Filter and deduplicate LandMARC exports to traceable project records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from src.ingest.landmarc import load_landmarc
from src.schemas.landmarc import PROJECT_SCHEMA

CUTOFF = pd.Timestamp("2015-01-01")
KEEP_PERMIT_TYPES = {
    "Building Commercial - New Construction",
    "Building Commercial - Addition",
    "Building Commercial - Alteration",
    "Building Commercial - Miscellaneous Structure",
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _project_key(row: pd.Series) -> str:
    for prefix, column in (
        ("parcel", "Main Parcel"),
        ("name", "Project Name"),
        ("address", "Address"),
    ):
        value = _normalize(str(row.get(column, "")))
        if value:
            return f"{prefix}:{value}"
    return f"case:{_normalize(str(row['Case Number']))}"


def _json_values(series: pd.Series) -> str:
    values = sorted({str(value).strip() for value in series if str(value).strip()})
    return json.dumps(values)


def preprocess_landmarc(raw_dir: Path, interim_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = load_landmarc(raw_dir)
    rows["applied_date"] = pd.to_datetime(
        rows["Applied Date"], format="%m/%d/%Y", errors="coerce"
    )
    rows["date_parse_ok"] = rows["applied_date"].notna()
    rows["after_cutoff"] = rows["applied_date"].ge(CUTOFF)
    module = rows["Module Name"].str.casefold()
    rows["record_class"] = "excluded"
    rows.loc[module.eq("plan"), "record_class"] = "land_use_application"
    rows.loc[
        module.eq("permit") & rows["Type"].isin(KEEP_PERMIT_TYPES),
        "record_class",
    ] = "building_permit"
    rows["included"] = rows["after_cutoff"] & rows["record_class"].ne("excluded")
    rows["project_key"] = rows.apply(_project_key, axis=1)
    rows["project_id"] = rows["project_key"].map(
        lambda value: "lm-" + hashlib.sha256(value.encode()).hexdigest()[:12]
    )

    included = rows.loc[rows["included"]].copy()
    projects: list[dict[str, object]] = []
    for project_id, group in included.groupby("project_id", sort=True):
        first = group.sort_values("applied_date").iloc[0]
        projects.append(
            {
                "project_id": project_id,
                "project_name": next(
                    (value for value in group["Project Name"] if value), ""
                ),
                "address": next((value for value in group["Address"] if value), ""),
                "main_parcel": next(
                    (value for value in group["Main Parcel"] if value), ""
                ),
                "locality": "Loudoun County",
                "module_tiers": _json_values(group["Module Name"]),
                "record_types": _json_values(group["Type"]),
                "statuses": _json_values(group["Status"]),
                "applied_date": group["applied_date"].min(),
                "filing_year": int(group["applied_date"].min().year),
                "era": "gs5"
                if group["applied_date"].min() >= pd.Timestamp("2027-01-01")
                else "pre_gs5",
                "source_case_numbers": _json_values(group["Case Number"]),
                "source_files": _json_values(group["_source_file"]),
                "source_row_count": len(group),
            }
        )
    project_frame = pd.DataFrame(projects)
    project_frame = PROJECT_SCHEMA.validate(project_frame)

    interim_dir.mkdir(parents=True, exist_ok=True)
    project_frame.to_parquet(interim_dir / "landmarc_projects.parquet", index=False)
    rows.to_parquet(interim_dir / "landmarc_source_rows.parquet", index=False)
    rows.loc[~rows["included"]].to_parquet(
        interim_dir / "landmarc_excluded_rows.parquet", index=False
    )
    return project_frame, rows


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    projects, source_rows = preprocess_landmarc(
        root / "data/raw", root / "data/interim"
    )
    print(
        f"projects={len(projects)} source_rows={len(source_rows)} "
        f"included_rows={source_rows['included'].sum()}"
    )
