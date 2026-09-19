# Comparability scoring notes

The score is a transparent weighted heuristic. It is not statistically
calibrated.

## Bill domain

- Utility territory match: 0.35
- Rate-vintage match (`pre_gs5` vs `gs5`): 0.25
- MW proximity: 0.25
- Filing-year proximity: 0.15

## Air domain

- Distance-to-residence proximity: 0.35
- Generator-capacity proximity: 0.30
- Permit-status match: 0.20
- Cluster-density locality match: 0.15

Every feature returns a value from 0 to 1 or `None`. `None` means the delivered
data do not support the comparison. Missing features are shown as omitted;
their configured weights are excluded and available weights are renormalized.
Each result includes configured and effective weights plus a reason string.

There is no combined bill-and-air score.

## Rate vintage

Records before 2027-01-01 are `pre_gs5`; records on or after that date are
`gs5`. The boundary follows the Virginia SCC final order dated 2025-11-25 in
PUR-2025-00058, which establishes GS-5 for customers of 25 MW or more,
effective 2027-01-01. A source URL was not supplied, so none is asserted here.
