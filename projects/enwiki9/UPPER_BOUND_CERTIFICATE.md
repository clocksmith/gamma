# Hutter Upper-Bound Certificate

## Constructive Theorem

If roundtrip_ok is true for archive A and decoder D on target corpus x, then |A| + |D| is a constructive upper bound for x in this testbed.

## Target

- Full input bytes: `1,000,000,000`
- 10.95% target score: `109,500,000`
- Calibrated baseline score: `110,181,114`
- Required net gain from calibrated baseline: `681,114` bytes
- Required archive slope before program cost: `0.005448912` bits/byte

## Proof Status

- Full-corpus constructive result present: `False`
- 10.95 constructive upper bound present: `False`

## Top Status

| Claim | Program | Scope | Score | Evidence | Status |
|---|---|---:|---:|---|---|
| best exact 10M | `n/a` | 10,000,000 | n/a | no exact 10M result JSON with roundtrip_ok true found | missing |
| best exact 10M archive | `n/a` | 10,000,000 | n/a | no exact 10M archive result JSON with roundtrip_ok true found | missing |
| best exact 100M | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 100,000,000 | 15,040,789 | metadata-inherited from parent 100M geometry package; no result JSON for this row is present in this checkout | metadata-inherited |
| best full 1G | `n/a` | 1,000,000,000 | n/a | no verified full-corpus result JSON is present in this checkout | not verified |
| best forecast | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | n/a | 110,181,114 | forecast only; not a constructive proof | fx2-calibrated-from-exact-100m |
| active candidate | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | n/a | n/a | no constructive result is present for the active candidate | not started |

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|

## Notes

- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 10.95 proof requires a full 1GB result with score <= 109500000.
