"""Conservative extraction of published Virginia DEQ data-center permits.

Only text present in a permit is promoted to a field. Missing or ambiguous
values remain null and are listed in ``unverified_fields``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber

EXPECTED_COLUMNS = [
    "site_name",
    "registration_number",
    "issuance_date",
    "program_type",
    "city_or_county",
    "regional_office",
    "permit_url",
]
OPTIONAL_COLUMNS = [
    "address",
    "main_parcel",
    "generator_count",
    "generator_capacity_mw",
    "fuel",
    "operating_limits",
    "pollutant_limits",
    "source_file",
    "is_northern_virginia",
    "unverified_fields",
]
PDF_COLUMNS = EXPECTED_COLUMNS + OPTIONAL_COLUMNS
DATE_PATTERN = (
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+20\d{2}"
)
NORTHERN_LOCALITIES = {
    "alexandria city",
    "arlington county",
    "fairfax city",
    "fairfax county",
    "falls church city",
    "fauquier county",
    "loudoun county",
    "manassas city",
    "manassas park city",
    "prince william county",
    "stafford county",
}


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip(" ,.;:")
    return cleaned or None


def _match(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
    matched = re.search(pattern, text, flags)
    return _clean(matched.group(1)) if matched else None


def _extract_pages(path: Path) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _site_name(pages: list[str]) -> str | None:
    for page in pages[:5]:
        if "STATIONARY SOURCE PERMIT" not in page.upper():
            continue
        matched = re.search(
            r"Regulations for the Control and Abatement of Air Pollution,\s*\n"
            r"(?P<name>[^\n]+)",
            page,
            re.IGNORECASE,
        )
        if matched:
            return _clean(matched.group("name"))
    cover = "\n".join(pages[:3])
    matched = re.search(
        r"permit (?:approval )?to (?:construct|modify) and operate .*? at "
        r"(?!a data center\b)(?P<name>[^.\n]+?) in accordance",
        cover,
        re.IGNORECASE,
    )
    return _clean(matched.group("name")) if matched else None


def _site_address(pages: list[str]) -> str | None:
    for page in pages[:5]:
        matched = re.search(
            r"\blocated at\s*\n(?P<address>.+?)\n\([^)]+(?:County|City)[^)]*\)",
            page,
            re.IGNORECASE | re.DOTALL,
        )
        if matched:
            return _clean(matched.group("address").replace("\n", ", "))
    return None


def _program_type(text: str) -> str | None:
    if re.search(r"\bTitle V permit\b", text, re.IGNORECASE):
        return "Title V"
    if re.search(r"\b(?:minor NSR|mNSR)\b", text, re.IGNORECASE):
        return "Minor NSR"
    if re.search(r"\bnew source review\b", text, re.IGNORECASE):
        return "New Source Review"
    return None


def _page_snippets(pages: list[str], pattern: str, limit: int = 3) -> str | None:
    snippets: list[str] = []
    for number, page in enumerate(pages, start=1):
        for matched in re.finditer(pattern, page, re.IGNORECASE):
            start = max(page.rfind("\n", 0, matched.start()), 0)
            end = page.find("\n", matched.end())
            if end < 0:
                end = len(page)
            snippet = _clean(page[start:end])
            if snippet:
                item = f"p. {number}: {snippet}"
                if item not in snippets:
                    snippets.append(item)
            if len(snippets) >= limit:
                return " | ".join(snippets)
    return " | ".join(snippets) or None


def extract_deq_pdf(path: Path, root: Path | None = None) -> dict[str, object]:
    """Extract high-confidence text fields from one permit PDF."""
    try:
        pages = _extract_pages(path)
    except Exception:
        pages = []
    text = "\n".join(pages)
    cover = "\n".join(pages[:5])
    registration = _match(
        r"\b(?:Registration|Reg\.)\s*(?:No\.?|Number)?\s*:?\s*([0-9-]+)",
        cover,
    )
    locality = _match(r"\bLocation\s*:\s*([^\n]+)", cover)
    if locality:
        locality = re.sub(r",?\s*VA\b.*$", "", locality, flags=re.IGNORECASE)
    if not locality:
        locality = _match(r"\(([^)\n]+(?:County|City)[^)\n]*)\)", cover)
    office = _match(
        r"\b(Northern|Piedmont|Southwest|Tidewater|Valley|Blue Ridge)"
        r"\s+Regional Office\b",
        cover,
    )
    issuance = _match(rf"\b({DATE_PATTERN})\b", cover)
    site = _site_name(pages)
    address = _site_address(pages)
    program = _program_type(text)
    fuel = (
        "diesel"
        if re.search(
            r"\bdiesel[- ](?:fired|fuel(?:ed)?|engine)\b",
            text,
            re.IGNORECASE,
        )
        else None
    )
    operating_limits = _page_snippets(
        pages, r".{0,100}\b(?:hours?|hrs?) per year\b.{0,100}"
    )
    pollutant_limits = _page_snippets(
        pages,
        r".{0,100}\b(?:tons? per year|lb/hr|pounds? per hour)\b.{0,100}",
    )
    locality_key = (locality or "").casefold().replace(", virginia", "").strip()
    is_northern = (
        (office or "").casefold() == "northern"
        or locality_key in NORTHERN_LOCALITIES
    )
    fields: dict[str, object] = {
        "site_name": site,
        "registration_number": registration,
        "issuance_date": issuance,
        "program_type": program,
        "city_or_county": locality,
        "regional_office": office,
        "permit_url": None,
        "address": address,
        "main_parcel": None,
        "generator_count": None,
        "generator_capacity_mw": None,
        "fuel": fuel,
        "operating_limits": operating_limits,
        "pollutant_limits": pollutant_limits,
        "source_file": (
            path.relative_to(root).as_posix()
            if root and path.is_relative_to(root)
            else str(path)
        ),
        "is_northern_virginia": is_northern,
    }
    review_names = (
        "site_name",
        "registration_number",
        "issuance_date",
        "program_type",
        "city_or_county",
        "regional_office",
        "permit_url",
        "address",
        "generator_count",
        "generator_capacity_mw",
    )
    fields["unverified_fields"] = ";".join(
        name for name in review_names if fields[name] is None
    )
    return fields


def extract_deq_directory(path: Path) -> pd.DataFrame:
    rows = [
        extract_deq_pdf(pdf, path.parent.parent)
        for pdf in sorted(path.rglob("*.pdf"))
    ]
    frame = pd.DataFrame(rows, columns=PDF_COLUMNS)
    frame["issuance_date"] = pd.to_datetime(frame["issuance_date"], errors="coerce")
    return frame


def write_deq_extract(path: Path, output_path: Path) -> pd.DataFrame:
    frame = extract_deq_directory(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def load_deq_permits(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame(columns=PDF_COLUMNS)
    if path.is_dir() or path.suffix.lower() == ".pdf":
        frame = (
            extract_deq_directory(path)
            if path.is_dir()
            else pd.DataFrame(
                [extract_deq_pdf(path, path.parents[2])],
                columns=PDF_COLUMNS,
            )
        )
    else:
        frame = pd.read_csv(path, dtype=str)
        frame = frame.rename(
            columns={
                column: column.strip().lower().replace(" ", "_").replace("/", "_or_")
                for column in frame.columns
            }
        )
        missing = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
        if missing:
            raise ValueError(f"{path}: missing DEQ columns {missing}")
        frame["issuance_date"] = pd.to_datetime(
            frame["issuance_date"], errors="coerce"
        )
        if "is_northern_virginia" not in frame:
            frame["is_northern_virginia"] = frame[
                "regional_office"
            ].str.casefold().eq("northern")
    northern = frame["is_northern_virginia"]
    if northern.dtype != bool:
        northern = northern.astype(str).str.casefold().eq("true")
    frame = frame.loc[northern.fillna(False)]
    frame = frame.loc[frame["issuance_date"].ge("2015-01-01")]
    return frame.drop_duplicates(
        ["registration_number", "issuance_date"]
    ).reset_index(drop=True)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    extracted = write_deq_extract(
        project_root / "data/raw/deq_va",
        project_root / "data/interim/deq_permits_extracted.csv",
    )
    print(f"permit_pdfs={len(extracted)}")
