# LandMARC delivered-export profile

Generated from raw files. Raw files were not modified.

## File identity

- Delivered files: 6
- Byte-distinct files: 2
- Duplicate files: 4

- `LandMARC_Plans_DataCenters.csv`; distinct
- `LandMARC_permits_112015_112020.csv`; distinct
- `LandMARC_permits_112026_9152026.csv`; duplicate of `LandMARC_permits_112015_112020.csv`
- `LandMARC_permits_122020_112023.csv`; duplicate of `LandMARC_permits_112015_112020.csv`
- `LandMARC_permits_122023_112025.csv`; duplicate of `LandMARC_permits_112015_112020.csv`
- `LandMARC_permits_122025_112026.csv`; duplicate of `LandMARC_permits_112015_112020.csv`

## LandMARC_Plans_DataCenters.csv

- Rows: 1,000

### Columns and null rates

| column | inferred_dtype | null_or_blank_count | null_or_blank_rate |
|---|---|---|---|
| Case Number | object | 0 | 0.0% |
| Type | object | 0 | 0.0% |
| Status | object | 0 | 0.0% |
| Project Name | object | 939 | 93.9% |
| Applied Date | object | 0 | 0.0% |
| Expiration Date | object | 1000 | 100.0% |
| Completion Date | object | 1000 | 100.0% |
| Module Name | object | 0 | 0.0% |
| Address | object | 161 | 16.1% |
| Main Parcel | object | 16 | 1.6% |
| Description | object | 15 | 1.5% |

### Date ranges

- Applied Date: 1999-08-01 to 2026-09-17; parseable 1,000/1,000
- Expiration Date: none to none; parseable 0/1,000
- Completion Date: none to none; parseable 0/1,000

### Module Name values

| Module Name | count |
|---|---|
| Plan | 1000 |

### Type values

| Type | count |
|---|---|
| Engineering Plan | 194 |
| Engineering Plan Revision | 152 |
| Zoning Correspondence - Determinations & Verifications (ZCOR) | 119 |
| Plat - Tier 1 - Easements (ESMT), or Dedication Plats (DEDI) | 86 |
| Special Exception | 77 |
| Performance Bond | 74 |
| Legislative Land Development Premeeting | 73 |
| Grading - Grading Bond | 43 |
| Site Plan Premeeting | 31 |
| Legislative Land Development Application | 25 |
| Zoning Map Amendment - ZCASE | 21 |
| Floodplain Alteration Type 2 | 13 |
| Planning Correspondence - Administrative | 12 |
| GIS Update - Natural Resources Team | 10 |
| Plat - BLAD - Boundary Line Adjustment (BLAD) | 9 |
| Commission Permit - Commission Permit | 8 |
| Building and Development Correspondence (BDCOR) | 8 |
| Zoning Concept Plan Amendment - ZCASE | 8 |
| Zoning Modification - ZCASE | 7 |
| Planning Correspondence - Advisory Body | 5 |
| Floodplain Study Type 2 | 5 |
| Zoning Ordinance Amendment - Zoning Ordinance Amendment | 4 |
| Appeal - Appeal | 4 |
| Plat - Tier 2 - Family Subdivision (SBFM), Subdivision Waiver (SBWV), or Subdivision Base Density Plats (SBBD) | 2 |
| Plat - Tier 3 - Preliminary/Record Plat (SBPR) or Record Plat (SBRD) | 2 |
| County Plat - Real Property Asset Management & Planning - Easements (ESMT), or Dedication Plats (DEDI) | 2 |
| Comprehensive Plan Amendment - Comprehensive Plan Amendment | 2 |
| Floodplain - Legacy Study Type not Identified | 1 |
| Natural Resources - Wetlands | 1 |
| Performance Bond Release - PBORE | 1 |
| Subdivision Premeeting | 1 |

### Status values

| Status | count |
|---|---|
| Approved | 408 |
| In Review | 220 |
| Completed | 168 |
| Active Bond | 81 |
| Withdrawn | 35 |
| Void | 32 |
| Submitted - Online | 19 |
| Inactive | 13 |
| Submitted | 12 |
| Released | 8 |
| Superseded | 3 |
| Denied | 1 |

### Parcel coverage

- Unique nonblank parcels: 340
- Rows with blank parcel: 16

## LandMARC_permits_112015_112020.csv

- Rows: 1,000

### Columns and null rates

| column | inferred_dtype | null_or_blank_count | null_or_blank_rate |
|---|---|---|---|
| Case Number | object | 0 | 0.0% |
| Type | object | 0 | 0.0% |
| Status | object | 0 | 0.0% |
| Project Name | object | 988 | 98.8% |
| Issued Date | object | 196 | 19.6% |
| Applied Date | object | 0 | 0.0% |
| Expiration Date | object | 346 | 34.6% |
| Finalized Date | object | 596 | 59.6% |
| Module Name | object | 0 | 0.0% |
| Address | object | 6 | 0.6% |
| Main Parcel | object | 2 | 0.2% |
| Description | object | 1 | 0.1% |

### Date ranges

- Applied Date: 1999-12-09 to 2025-10-02; parseable 1,000/1,000
- Issued Date: 2000-01-19 to 2026-05-07; parseable 804/1,000
- Expiration Date: 2023-07-24 to 2027-12-24; parseable 654/1,000
- Finalized Date: 2000-07-14 to 2026-09-17; parseable 404/1,000

### Module Name values

| Module Name | count |
|---|---|
| Permit | 1000 |

### Type values

| Type | count |
|---|---|
| Building Commercial - Tenant Fit-Up | 385 |
| Building Commercial - Alteration | 311 |
| Building Commercial - New Construction | 191 |
| Building Commercial - Miscellaneous Structure | 72 |
| Building Commercial - Addition | 16 |
| Building Commercial - Telecommunication | 10 |
| Building Commercial - Demolition | 6 |
| Building Commercial - Occupancy Only | 3 |
| Building Commercial - Sales Trailer | 2 |
| Amusement Device - Construction | 1 |
| Building (Commercial) - Other - Legacy | 1 |
| Building Commercial - Repair | 1 |
| Building Commercial - Change of Use | 1 |

### Status values

| Status | count |
|---|---|
| Issued | 370 |
| Finaled | 265 |
| Cancelled | 134 |
| Issued Certificate of Occupancy | 123 |
| Fees Due | 50 |
| In Review | 46 |
| Expired | 3 |
| On Hold | 3 |
| Void | 2 |
| Not Required | 2 |
| Fees Paid | 1 |
| Complete | 1 |

### Parcel coverage

- Unique nonblank parcels: 180
- Rows with blank parcel: 2

## Root-cause investigation (2026-09-19)

Investigated whether the ~1,000-row cap on both delivered exports and the
byte-identical duplicate permit files are an ingest bug in this repo or a
source-data limitation from the LandMARC portal.

**1,000-row cap: confirmed source-data limitation, not an ingest bug.**
`src/ingest/landmarc.py`'s `load_landmarc()` uses plain `pd.read_csv` with no
`nrows`/`.head()`/limit, and reads every distinct file in full.
`distinct_landmarc_files()` correctly dedups by sha256 before loading (only
the 2 byte-distinct files get concatenated) — this prevents inflating the
1,000 permit rows to 5,000 duplicates, it does not truncate them.
`preprocess_landmarc()` applies intentional business-logic filters (2015
cutoff, permit-type allowlist, project-level dedup) on top of the
already-loaded rows — none of these could produce the raw files' 1,000-row
size. No code changes were made; the cap originates entirely in the
delivered raw files.

**5 "different" permit files: verified 100% byte-identical, not just
sha256-equal.** A byte comparison (not just hash) across all 5 confirmed
they are identical, same file size (264,602 bytes). Their file modification
times differ in strict filename-chronological order, roughly a minute apart,
all on 2026-09-19 — consistent with the same query being exported 5 times
from the LandMARC portal where the date-range UI control did not actually
change the result set.

**New concrete evidence:**
- Both raw files are well-formed: header plus exactly 1,000 data rows,
  consistent column counts, no trailing footer/pagination-metadata row — the
  cap looks like a hard row limit, not a truncated or corrupted export.
- The permits file is sorted in strict ascending Case Number order
  (verified programmatically) — its 1999-2025 applied-date span is an
  emergent side effect of which case numbers land in the first 1,000, which
  confirms the filenames' implied date ranges are fictional.
- The plans file is not sorted by Case Number or Applied Date (ascending or
  descending) in any detectable way — no available sort key explains its
  order.
- Physical line counts exceed row counts purely because of embedded
  newlines inside quoted `Description` fields — normal CSV quoting, not a
  parsing issue.

**What a human should chase with LandMARC or the vendor:**
- Whether the portal export enforces a hard 1,000-row cap regardless of
  date-range or search parameters.
- Why the 5 differently-dated exports are byte-identical — points to the
  export screen's date-range control not being wired to the actual query
  (a portal-side bug or workflow issue, not something in this repo).
- What sort/ranking order the portal applies by default (permits appear to
  be ascending Case Number; plans file order is unknown), since that
  determines which 1,000 of the 1,099+ reported results get delivered.
