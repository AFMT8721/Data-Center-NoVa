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
