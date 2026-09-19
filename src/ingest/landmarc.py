"""Read and profile delivered LandMARC exports without guessing columns."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from src.schemas.landmarc import validate_landmarc_columns

DATE_COLUMNS = ["Applied Date", "Issued Date", "Expiration Date", "Completion Date", "Finalized Date"]


def distinct_landmarc_files(raw_dir: Path) -> tuple[list[Path], dict[Path, Path]]:
    distinct: list[Path] = []
    duplicate_of: dict[Path, Path] = {}
    first_by_hash: dict[str, Path] = {}
    for path in sorted(raw_dir.glob("LandMARC_*.csv")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in first_by_hash:
            duplicate_of[path] = first_by_hash[digest]
        else:
            first_by_hash[digest] = path
            distinct.append(path)
    return distinct, duplicate_of


def load_landmarc(raw_dir: Path) -> pd.DataFrame:
    files, _ = distinct_landmarc_files(raw_dir)
    frames: list[pd.DataFrame] = []
    for path in files:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        validate_landmarc_columns(set(frame.columns), path.name)
        frame.columns = frame.columns.str.strip()
        for column in frame.columns:
            frame[column] = frame[column].str.strip()
        frame["_source_file"] = path.as_posix()
        frame["_source_row"] = range(2, len(frame) + 2)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False)


def _markdown_table(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def write_profile(raw_dir: Path, output_path: Path) -> None:
    files = sorted(raw_dir.glob("LandMARC_*.csv"))
    distinct, duplicate_of = distinct_landmarc_files(raw_dir)
    sections = [
        "# LandMARC delivered-export profile",
        "",
        "Generated from raw files. Raw files were not modified.",
        "",
        "## File identity",
        "",
        f"- Delivered files: {len(files)}",
        f"- Byte-distinct files: {len(distinct)}",
        f"- Duplicate files: {len(duplicate_of)}",
        "",
    ]
    for path in files:
        duplicate = duplicate_of.get(path)
        suffix = f"; duplicate of `{duplicate.name}`" if duplicate else "; distinct"
        sections.append(f"- `{path.name}`{suffix}")

    for path in distinct:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        sections.extend(["", f"## {path.name}", "", f"- Rows: {len(frame):,}"])
        schema = pd.DataFrame(
            {
                "column": frame.columns,
                "inferred_dtype": [str(frame[column].dtype) for column in frame],
                "null_or_blank_count": [
                    int(frame[column].isna().sum() + frame[column].fillna("").str.strip().eq("").sum())
                    for column in frame
                ],
                "null_or_blank_rate": [
                    f"{(frame[column].isna() | frame[column].fillna('').str.strip().eq('')).mean():.1%}"
                    for column in frame
                ],
            }
        )
        sections.extend(["", "### Columns and null rates", "", _markdown_table(schema)])
        sections.extend(["", "### Date ranges", ""])
        for column in DATE_COLUMNS:
            if column in frame:
                parsed = pd.to_datetime(frame[column], format="%m/%d/%Y", errors="coerce")
                sections.append(
                    f"- {column}: {parsed.min().date() if parsed.notna().any() else 'none'} to "
                    f"{parsed.max().date() if parsed.notna().any() else 'none'}; "
                    f"parseable {parsed.notna().sum():,}/{len(frame):,}"
                )
        for column in ("Module Name", "Type", "Status"):
            counts = (
                frame[column].replace("", "(blank)").value_counts(dropna=False).rename_axis(column).reset_index(name="count")
            )
            sections.extend(["", f"### {column} values", "", _markdown_table(counts)])
        parcel = frame["Main Parcel"].fillna("").str.strip()
        sections.extend(
            [
                "",
                "### Parcel coverage",
                "",
                f"- Unique nonblank parcels: {parcel[parcel.ne('')].nunique():,}",
                f"- Rows with blank parcel: {parcel.eq('').sum():,}",
            ]
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections) + "\n", encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    write_profile(root / "data/raw", root / "docs/landmarc_profile.md")
