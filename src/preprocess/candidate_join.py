"""Generate review candidates between DEQ sites and LandMARC projects.

This module never merges records. It emits ranked candidates for manual review.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from src.ingest.deq_permits import load_deq_permits

COLUMNS = [
    "deq_site_name",
    "deq_registration_number",
    "landmarc_project_id",
    "landmarc_project_name",
    "name_confidence",
    "address_confidence",
    "parcel_confidence",
    "overall_confidence",
    "confidence_basis",
    "review_status",
]


def _normalize(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _similarity(left: object, right: object) -> float | None:
    left_normalized, right_normalized = _normalize(left), _normalize(right)
    if not left_normalized or not right_normalized:
        return None
    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def _confidence(values: dict[str, float | None]) -> tuple[float, str]:
    configured = {"name": 0.50, "address": 0.30, "parcel": 0.20}
    available = {name: value for name, value in values.items() if value is not None}
    total = sum(configured[name] for name in available)
    if not total:
        return 0.0, "no comparable fields"
    score = sum(configured[name] * value for name, value in available.items()) / total
    return score, "+".join(sorted(available))


def build_candidate_join(
    projects_path: Path, output_path: Path, deq_path: Path | None = None
) -> pd.DataFrame:
    deq = load_deq_permits(deq_path)
    projects = pd.read_parquet(projects_path)
    candidates: list[dict[str, object]] = []
    for site in deq.to_dict(orient="records"):
        site_candidates: list[dict[str, object]] = []
        for project in projects.to_dict(orient="records"):
            values = {
                "name": _similarity(site.get("site_name"), project["project_name"]),
                "address": _similarity(site.get("address"), project["address"]),
                "parcel": (
                    1.0
                    if _normalize(site.get("main_parcel"))
                    and _normalize(site.get("main_parcel"))
                    == _normalize(project["main_parcel"])
                    else None
                ),
            }
            overall, basis = _confidence(values)
            if overall < 0.30:
                continue
            site_candidates.append(
                {
                    "deq_site_name": site["site_name"],
                    "deq_registration_number": site["registration_number"],
                    "landmarc_project_id": project["project_id"],
                    "landmarc_project_name": project["project_name"],
                    "name_confidence": values["name"],
                    "address_confidence": values["address"],
                    "parcel_confidence": values["parcel"],
                    "overall_confidence": overall,
                    "confidence_basis": basis,
                    "review_status": "unreviewed",
                }
            )
        candidates.extend(
            sorted(
                site_candidates,
                key=lambda row: float(row["overall_confidence"]),
                reverse=True,
            )[:3]
        )
    result = pd.DataFrame(candidates, columns=COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    deq_extract = root / "data/interim/deq_permits_extracted.csv"
    result = build_candidate_join(
        root / "data/interim/landmarc_projects.parquet",
        root / "data/interim/deq_landmarc_candidate_join.csv",
        deq_extract if deq_extract.exists() else None,
    )
    print(f"candidate_rows={len(result)}")
