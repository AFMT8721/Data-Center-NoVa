"""Create a traceable manifest without modifying raw files."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd

MANIFEST_COLUMNS = [
    "source",
    "query_or_url",
    "filters",
    "export_or_pull_date",
    "date_basis",
    "row_count",
    "file_path",
    "sha256",
    "duplicate_of",
    "notes",
]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_row_count(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def _source_metadata(path: Path) -> tuple[str, str, str, str]:
    name = path.name.lower()
    full_path = path.as_posix().lower()
    if name.startswith("landmarc"):
        return (
            "Loudoun County LandMARC",
            'LandMARC export; search phrase "data center"',
            "Plan or Permit tier; delivered export",
            "Export query details beyond filename are unverified.",
        )
    if name.startswith("eia861"):
        return (
            "U.S. EIA Form EIA-861",
            "URL unverified; delivered consolidated extract",
            "2015-2025",
            "Pull URL and pull date were not delivered.",
        )
    if name.startswith("virginia_daily_aqi"):
        frame = pd.read_csv(path, nrows=1, dtype=str)
        source_url = frame.at[0, "source_dataset_url"] or frame.at[0, "source_url"]
        pulled = frame.at[0, "source_downloaded_on"]
        return (
            "U.S. EPA daily AQI by county",
            source_url,
            "Virginia; 2015-2026",
            f"Source-provided downloaded_on={pulled}.",
        )
    if name == "jlarc_report.pdf":
        return (
            "JLARC, Data Centers in Virginia",
            "Local PDF; publication URL not supplied",
            "December 2024 report",
            "Published report; local file delivery date unverified.",
        )
    if name.startswith("2015_criteria_emissions_"):
        return (
            "Virginia DEQ 2015 criteria emissions inventory",
            "DEQ website CSV; exact download URL unverified",
            "Published 10-ton or 100-ton facility list; 2015",
            "Facility-wide reported criteria emissions; not permit limits or "
            "generator-specific measurements.",
        )
    if "deq" in full_path and path.suffix.lower() == ".pdf":
        return (
            "Virginia DEQ issued data center air permits",
            "Published DEQ permit PDF; original URL unavailable in local delivery",
            "Virginia data-center permit collection",
            "Local PDF preserves permit text but not its download URL.",
        )
    return ("Unverified source", "unverified", "unverified", "Source unverified.")


def build_manifest(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    first_by_hash: dict[str, str] = {}
    project_root = output_path.parent.parent
    for path in sorted(
        p
        for p in raw_dir.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(raw_dir).parts)
    ):
        digest = sha256_file(path)
        source, query, filters, note = _source_metadata(path)
        duplicate_of = first_by_hash.get(digest, "")
        relative_path = path.relative_to(project_root).as_posix()
        if not duplicate_of:
            first_by_hash[digest] = relative_path
        mtime = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        rows.append(
            {
                "source": source,
                "query_or_url": query,
                "filters": filters,
                "export_or_pull_date": mtime,
                "date_basis": "local_file_modified_date; unverified as pull date",
                "row_count": csv_row_count(path),
                "file_path": relative_path,
                "sha256": digest,
                "duplicate_of": duplicate_of,
                "notes": note,
            }
        )
    result = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    build_manifest(root / "data/raw", root / "provenance/manifest.csv")
