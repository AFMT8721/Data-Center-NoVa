# DEQ issued data center air permits input contract

Status: 194 published permit PDFs delivered and locally extracted as of
2026-09-19. Original permit URLs were not preserved.

Expected normalized CSV columns:

| Column | Meaning |
|---|---|
| `site_name` | DEQ-listed site name |
| `registration_number` | DEQ registration number |
| `issuance_date` | Issued permit date |
| `program_type` | DEQ program type |
| `city_or_county` | Listed Virginia locality |
| `regional_office` | DEQ regional office |
| `permit_url` | Linked permit PDF URL, null when unavailable |
| `address` | Facility address stated on permit title page |
| `generator_count` | Verified fleet count; currently null pending review |
| `generator_capacity_mw` | Verified aggregate capacity; currently null pending review |
| `fuel` | Explicitly stated fuel |
| `operating_limits` | Page-cited permit text containing annual-hour limits |
| `pollutant_limits` | Page-cited permit text containing mass-rate limits |
| `unverified_fields` | Fields not safely established from extracted text |

Automated extraction never derives a value from filename suffixes or unstated
assumptions. It leaves ambiguous generator totals and capacities null.

Ingest rules:

1. Preserve one extracted row per PDF.
2. For comparability, keep verified Northern-office or Northern-locality rows.
3. Keep issuance dates on or after 2015-01-01.
4. Deduplicate only identical registration-number and issuance-date pairs.
5. Label rows `air / permitted / project / government`.
6. Use permit status `permitted`, never `measured`.
7. Treat permit limits as neither actual emissions nor ambient air quality.

The separate 2015 criteria-emissions CSV is measured, historical,
facility-wide inventory evidence. It is not a permit limit, current emission
rate, generator-only measurement, or project-attributable neighborhood impact.
