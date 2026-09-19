# Open issues and evidence limits

Updated: 2026-09-19

## Blocking source gaps

1. **DEQ permit URLs and some PDF fields remain unavailable.** The 194 local
   permit PDFs preserve permit text but not their original web URLs. Automated
   extraction leaves ambiguous site fields null. Generator fleet totals and
   aggregate MW remain unverified pending document-level review. See
   `docs/deq_contract.md`.
2. **LandMARC permit exports are duplicates.** Five differently named files
   have the same sha256
   `dc1e1e45b88027a58ab3187e081f0aef0313f0c4ccd904937219a3bdaf5718b0`.
   Each contains the same 1,000 rows and spans applied dates from 1999-12-09
   through 2025-10-02. The filenames do not represent actual date slices.
   Preprocessing reads this content once.
3. **LandMARC exports appear capped.** The Plan file has 1,000 rows, below the
   1,099 search result count reported in the handoff. The delivered Permit
   content also has exactly 1,000 rows. Coverage is incomplete.

## Attribution limits

1. **AQI is locality context only.** Daily county AQI cannot identify a data
   center contribution or backup-generator effect. AQI records are labeled
   `measured / locality / government`, marked context-only, and carry a
   non-attribution statement.
2. **Generator capacity remains unverified.** Individual equipment tables
   contain rated capacities, but amendments and mixed fleets make automated
   aggregation unsafe. The feature remains omitted.
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
4. Original DEQ PDF URLs and the reported page as-of date of 2026-09-14 are
   unavailable from the delivered files.
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
