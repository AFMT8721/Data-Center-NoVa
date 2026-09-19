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
EQUIPMENT_SECTION_START = re.compile(
    r"(?:Equipment(?:\s+List)?\s*[-–]\s*)?Equipment at this facility"
    r".{0,100}?consists of(?: the following)?:?",
    re.IGNORECASE | re.DOTALL,
)
EQUIPMENT_SECTION_END = re.compile(
    r"(?:Specifications included|PROCESS LIMITATIONS|"
    r"OPERATING[/ ]EMISSION LIMITATIONS|EMISSION LIMITS|OPERATING LIMITATIONS|"
    r"\d+\.\s*(?:Emission Controls|Fuel\b))",
    re.IGNORECASE,
)
# Any second labeled equipment group (prior fleet, added fleet, exempt
# equipment, etc.) in one permit means the total is an amendment/mixed-fleet
# history, not a single verifiable total, so it stays null.
EQUIPMENT_CATEGORY_PATTERNS = {
    "to_be_constructed": r"Equipment to be Constructed",
    "to_be_added": r"Equipment to be Added",
    "prior": r"Equipment permitted prior to the date of this permit",
    "prev_permitted": r"(?:Previously Permitted Equipment|Equipment Previously Permitted)",
    "prev_constructed": r"(?:Equipment [Pp]reviously [Cc]onstructed|Previously Constructed Equipment)",
    "included_in_project": r"Equipment included in the project",
    "other_permitted": r"Other [Pp]ermitted [Ee]quipment",
    "exempt": r"Exempt(?:ed)? from Permitting",
    "existing": r"Existing Equipment",
    "removed": r"Equipment (?:to be )?Removed",
    "decommissioned": r"Decommissioned",
}
EQUIPMENT_CATEGORY_RE = re.compile(
    "|".join(f"(?P<{k}>{v})" for k, v in EQUIPMENT_CATEGORY_PATTERNS.items()),
    re.IGNORECASE,
)
EQUIPMENT_HEADER_ROW = re.compile(r"\bRef(?:erence)?\.?\s*No", re.IGNORECASE)
EQUIPMENT_DESCRIPTION_CELL = re.compile(r"Description", re.IGNORECASE)
GENERATOR_CAPACITY_KW = re.compile(r"([\d,]+(?:\.\d+)?)\s*e?kW", re.IGNORECASE)
GENERATOR_WORD = re.compile(r"generat|engine|gen[- ]?set", re.IGNORECASE)
NON_GENERATOR_WORD = re.compile(
    r"\bboiler\b|\bwater heater\b|\bpump\b|\bMMBtu\b|\bcooling tower\b|\bchiller\b",
    re.IGNORECASE,
)
GENERATOR_QTY_PAREN = re.compile(r"\((\d{1,3})\)")
GENERATOR_QTY_UNITS = re.compile(r"\((\d{1,3})\s*units?\)", re.IGNORECASE)
GENERATOR_QTY_THROUGH = re.compile(
    r"^\s*(\d{1,3})\s+through\s+(\d{1,3})\s*$", re.IGNORECASE
)
GENERATOR_SPELLED_NUMBER = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thir\w*|"
    r"four\w*|fif\w*|six\w*|seven\w*|eigh\w*|nine\w*|hundred|thousand)\b",
    re.IGNORECASE,
)
GENERATOR_LETTER_DASH_RANGE = re.compile(r"[A-Za-z]+\d+\s*-\s*[A-Za-z]*\d+")
GENERATOR_SINGLE_REF = re.compile(r"^[A-Za-z0-9/#\- ]+$")

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


def _extract_page_tables(path: Path) -> list[list[list[list[str | None]]]]:
    with pdfplumber.open(path) as pdf:
        return [page.extract_tables() for page in pdf.pages]


def _generator_totals(pages: list[str], path: Path) -> tuple[int | None, float | None]:
    """Sum generator count and capacity only for a single, unsplit equipment
    table with one resolvable quantity and one capacity value per row.

    Any amendment history, a second labeled equipment group, a competing
    capacity/quantity reading in one row, or text corrupted badly enough to
    contain many "^" substitution artifacts leaves the totals null.
    """
    full_text = "\n".join(pages)
    if full_text.count("^") > 5:
        return None, None
    starts = list(EQUIPMENT_SECTION_START.finditer(full_text))
    if len(starts) != 1:
        return None, None

    start_page = next(i for i, t in enumerate(pages) if EQUIPMENT_SECTION_START.search(t))
    end_page = start_page
    for i in range(start_page, len(pages)):
        if EQUIPMENT_SECTION_END.search(pages[i]):
            end_page = i
            break
    else:
        end_page = min(start_page + 1, len(pages) - 1)

    section_text = "\n".join(pages[start_page : end_page + 1])
    section_start = EQUIPMENT_SECTION_START.search(section_text)
    section_end = EQUIPMENT_SECTION_END.search(section_text, section_start.end())
    section_text = section_text[
        section_start.end() : section_end.start() if section_end else section_start.end() + 4000
    ]

    categories: set[str] = set()
    for match in EQUIPMENT_CATEGORY_RE.finditer(section_text):
        categories.update(k for k, v in match.groupdict().items() if v)
    if len(categories) >= 2 or "exempt" in categories:
        return None, None

    try:
        page_tables = _extract_page_tables(path)
    except Exception:
        return None, None

    # A second "Reference No / Equipment Description" header row anywhere in
    # the section means a second equipment table exists even when no
    # category phrase above matched (permit templates reorder and reword
    # these headers, e.g. "Equipment Previously Permitted" vs "Previously
    # Permitted Equipment"). A header row that is the first row of the first
    # table on a continuation page is instead pdfplumber re-emitting the
    # same table's header across a page break -- that's one table, not two,
    # and must not count.
    header_rows = 0
    for page_idx in range(start_page, min(end_page, len(page_tables) - 1) + 1):
        for table_idx, table in enumerate(page_tables[page_idx]):
            for row_idx, row in enumerate(table):
                row_text = " | ".join(cell for cell in row if cell)
                if not (
                    EQUIPMENT_HEADER_ROW.search(row_text)
                    and EQUIPMENT_DESCRIPTION_CELL.search(row_text)
                ):
                    continue
                is_page_start_continuation = (
                    page_idx > start_page and table_idx == 0 and row_idx == 0
                )
                if is_page_start_continuation:
                    continue
                header_rows += 1
    if header_rows >= 2:
        return None, None

    count_total = 0
    capacity_total_kw = 0.0
    any_row = False
    for page_idx in range(start_page, min(end_page, len(page_tables) - 1) + 1):
        for table in page_tables[page_idx]:
            for row in table:
                cells = [cell for cell in row if cell]
                if not cells:
                    continue
                row_text = " | ".join(cells)
                if EQUIPMENT_HEADER_ROW.search(row_text) or (
                    EQUIPMENT_DESCRIPTION_CELL.search(row_text) and len(row_text) < 40
                ):
                    continue
                if len(row_text.strip()) < 40 and not GENERATOR_CAPACITY_KW.search(row_text):
                    continue

                has_capacity = bool(GENERATOR_CAPACITY_KW.search(row_text))
                is_generator = bool(GENERATOR_WORD.search(row_text))
                is_excluded = bool(NON_GENERATOR_WORD.search(row_text))
                if is_excluded and not is_generator:
                    continue
                if not has_capacity and not is_generator:
                    continue
                # A generator row without a capacity, or a capacity reading
                # on a row that isn't clearly generator equipment, can't be
                # silently skipped without under- or over-stating the total.
                if is_generator != has_capacity:
                    return None, None

                capacity_matches = list(GENERATOR_CAPACITY_KW.finditer(row_text))
                if len({m.group(1) for m in capacity_matches}) > 1:
                    return None, None
                capacity_value = float(capacity_matches[0].group(1).replace(",", ""))

                paren_matches = GENERATOR_QTY_PAREN.findall(row_text)
                units_matches = GENERATOR_QTY_UNITS.findall(row_text)
                ref_cell = (cells[0] if cells else "").replace("\n", " ").strip()
                desc_cell = (cells[1] if len(cells) > 1 else "").replace("\n", " ").strip()
                through_match = GENERATOR_QTY_THROUGH.match(ref_cell)
                quantity: int | None = None
                if paren_matches:
                    if len(set(paren_matches)) > 1:
                        return None, None
                    quantity = int(paren_matches[0])
                elif units_matches:
                    if len(set(units_matches)) > 1:
                        return None, None
                    quantity = int(units_matches[0])
                elif through_match:
                    low, high = int(through_match.group(1)), int(through_match.group(2))
                    if high >= low:
                        quantity = high - low + 1
                elif GENERATOR_LETTER_DASH_RANGE.search(ref_cell):
                    return None, None
                elif GENERATOR_SPELLED_NUMBER.search(desc_cell):
                    return None, None
                elif (
                    GENERATOR_SINGLE_REF.fullmatch(ref_cell or "")
                    and "," not in ref_cell
                    and " and " not in ref_cell.lower()
                    and not re.search(r"\d\s*-\s*\d", ref_cell)
                ):
                    quantity = 1
                else:
                    return None, None

                count_total += quantity
                capacity_total_kw += quantity * capacity_value
                any_row = True

    if not any_row:
        return None, None
    return count_total, round(capacity_total_kw / 1000.0, 3)


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
    generator_count, generator_capacity_mw = (
        _generator_totals(pages, path) if pages else (None, None)
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
        "generator_count": generator_count,
        "generator_capacity_mw": generator_capacity_mw,
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
