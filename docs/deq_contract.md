# DEQ issued data center air permits input contract

Status: 194 published permit PDFs delivered and locally extracted as of
2026-09-19. Original permit URLs were reconstructed for 192/194 rows by
matching registration number against a user-supplied browser export
(deq.virginia.gov blocks automated WebFetch with HTTP 403, so no URL in this
manifest was independently re-fetched by an agent). Two rows remain
unresolved: registration 30142 (`3014202_DC_Permit.pdf`) has no matched URL
at all -- the source page's amendment-number digit could not be read
reliably from a screenshot -- and the URL for `7364303_DC_Permit.pdf` is
flagged CONTESTED in `provenance/manifest.csv`, where a later manual re-check
disputed whether its amendment number is "3" or "1". See
`docs/open_issues.md`.

Expected normalized CSV columns:

| Column | Meaning |
|---|---|
| `site_name` | DEQ-listed site name |
| `registration_number` | DEQ registration number |
| `issuance_date` | Issued permit date |
| `program_type` | DEQ program type |
| `city_or_county` | Listed Virginia locality |
| `regional_office` | DEQ regional office |
| `permit_url` | Linked permit PDF URL; populated for 192/194 rows (see Status), null for the 2 unresolved rows |
| `address` | Facility address stated on permit title page |
| `generator_count` | Verified fleet count; filled for 35/194 permits, null elsewhere (see fail-closed rule below) |
| `generator_capacity_mw` | Verified aggregate capacity; filled for 35/194 permits, null elsewhere (see fail-closed rule below) |
| `fuel` | Explicitly stated fuel |
| `operating_limits` | Page-cited permit text containing annual-hour limits |
| `pollutant_limits` | Page-cited permit text containing mass-rate limits |
| `unverified_fields` | Fields not safely established from extracted text |

Automated extraction never derives a value from filename suffixes or unstated
assumptions. It leaves ambiguous generator totals and capacities null.

`src/ingest/deq_permits.py` fills `generator_count`/`generator_capacity_mw`
for 35/194 permits. The rule is fail-closed: any amendment history, mixed
fleet, split equipment table, or ambiguous capacity/quantity reading leaves
both fields null rather than guessing. The remaining ~160 stay null for
documented reasons: 77 multi-category or amended fleets, 36 OCR-garbled
PDFs, 17 with no equipment table found, 12 with no generator rows matched, 6
caught by a structural two-table safety check, and roughly 10 smaller edge
cases.

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
