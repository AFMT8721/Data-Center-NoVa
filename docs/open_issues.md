# Open issues and evidence limits

Updated: 2026-09-19

## Blocking source gaps

1. **DEQ permit URLs: mostly resolved.** Original permit URLs were
   reconstructed for 192/194 rows by matching registration number against a
   user-supplied browser export (deq.virginia.gov returns HTTP 403 to
   automated WebFetch, so no URL was independently re-fetched by an agent).
   Generator fleet totals and aggregate MW are filled for 35/194 permits
   under a fail-closed rule (amendments, mixed fleets, split tables, or
   ambiguous readings leave both fields null); the remaining ~160 stay null
   for documented reasons. See `docs/deq_contract.md` and item 4 below for
   the 2 rows whose URLs are still unresolved.
2. **LandMARC permit exports are duplicates -- root cause confirmed.** Five
   differently named files have the same sha256
   `dc1e1e45b88027a58ab3187e081f0aef0313f0c4ccd904937219a3bdaf5718b0` and are
   verified byte-identical (not just hash-equal), same 264,602-byte size.
   Their file modification times are roughly a minute apart, all
   2026-09-19, consistent with the same query being exported 5 times from
   the LandMARC portal while its date-range UI control did not actually
   change the result set -- a source-portal limitation, not an ingest bug.
   See `docs/landmarc_profile.md`, "Root-cause investigation (2026-09-19)".
3. **LandMARC exports appear capped -- root cause confirmed.** The Plan file
   has 1,000 rows, below the 1,099 search result count reported in the
   handoff; the delivered Permit content also has exactly 1,000 rows.
   `src/ingest/landmarc.py`'s `load_landmarc()` was verified to apply no
   `nrows`/`.head()`/limit and to read every distinct file in full, so the
   cap originates entirely in the delivered raw files (a LandMARC
   source-portal export-size limit), not this repo's ingest code. See
   `docs/landmarc_profile.md`, "Root-cause investigation (2026-09-19)".
4. **Two DEQ permit URLs remain unresolved.** Not all 194 rows are solid:
   registration 30142 (`3014202_DC_Permit.pdf`) has no matched URL at all --
   the source page's amendment-number digit could not be read reliably from
   a screenshot. The URL matched to `7364303_DC_Permit.pdf` is flagged
   CONTESTED in `provenance/manifest.csv`: a later manual re-check disputed
   whether its amendment number is "3" or "1"; unresolved as of 2026-09-19.

## Ingest-script hazards

1. **`manifest.py` and `landmarc.py` are non-idempotent and will destroy
   hand-edited content.** `src/ingest/manifest.py` and `src/ingest/landmarc.py`
   fully regenerate their output files (`provenance/manifest.csv` and
   `docs/landmarc_profile.md` respectively) from scratch on every run, with
   no awareness of and no preservation of prior manual edits. Running
   `uv run python -m src.ingest.manifest` or
   `uv run python -m src.ingest.landmarc` after either file has been
   hand-edited (for example, the DEQ URL verification and root-cause
   investigation work described above) will silently overwrite that work.
   This caused a real data-loss incident in this repo's history; it was
   recovered from git, but the underlying hazard is not fixed in the
   scripts. **Do not re-run either command casually once either output file
   has manual edits.** Any future manual verification work on
   `provenance/manifest.csv` or `docs/landmarc_profile.md` should be
   committed immediately rather than left pending in the working tree, so
   an accidental re-run has something to recover from.

## Attribution limits

1. **AQI is locality context only.** Daily county AQI cannot identify a data
   center contribution or backup-generator effect. AQI records are labeled
   `measured / locality / government`, marked context-only, and carry a
   non-attribution statement.
2. **Generator capacity remains unverified for most permits.** Individual
   equipment tables contain rated capacities, but amendments and mixed
   fleets make automated aggregation unsafe. `generator_count` and
   `generator_capacity_mw` are filled for 35/194 permits under a
   fail-closed rule; the remaining ~160 stay null. The feature remains
   omitted from comparability scoring. See `docs/deq_contract.md`.
3. **Permits are not measurements.** Extracted permit records use status
   `permitted`. Permit limits cannot establish actual generator use, emissions,
   or ambient neighborhood conditions.
4. **Project scale unavailable.** LandMARC does not contain MW. Bill-scale
   proximity is omitted for delivered records.
5. **Utility territory must be supplied.** Prince William and other locality
   names do not establish Dominion or NOVEC service. The app never infers
   territory from locality.

## Unverified claims and metadata

1. The claim that JLARC excluded distribution costs is unverified and is not
   presented by the app.
2. EIA-861 pull URL and pull date were not delivered. The manifest labels both
   unverified. Source workbook filenames remain attached to each context row.
3. LandMARC query metadata beyond the delivered filenames and the reported
   search phrase is unverified.
4. Original DEQ PDF URLs are now populated for 192/194 rows (matched against
   a user-supplied browser export; see item 1 and item 4 under "Blocking
   source gaps"), but were not independently re-fetched by an automated
   agent (deq.virginia.gov returns HTTP 403 to WebFetch). The reported page
   as-of date of 2026-09-14 remains unavailable from the delivered files.
5. The DEQ 2015 criteria-emissions CSV supplies historical facility-wide
   measured totals for six Northern Virginia registration matches. It does
   not identify generator-only emissions, current emissions, or causal
   neighborhood effects. The 100-ton CSV adds no permit-PDF registration match.

## Interpretation limits

- The JLARC $14 to $37 monthly range is a region-level, modeled projection for
  a typical Dominion residential customer by 2040 in constant 2024 dollars.
  It is not a realized outcome and cannot be attributed to one project.
- JLARC analyzed the pre-GS-5 structure. The SCC GS-5 class for customers of
  25 MW or more takes effect 2027-01-01, so rate-era match is explicit.
- Comparability scores are transparent weighted heuristics. They are not
  calibrated, causal estimates, forecasts, or per-resident cost predictions.
