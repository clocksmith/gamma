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
| best forecast | `cmix21_lstm200_fx2lite428_context_recovery_10m_v1` | 10,000,000 | 109,557,404 | exact guarded 10M archive screen with counted program economics; terminal verdict retire_repaired_endpoint428_strict_10m_economics_miss; forecast only, not a constructive full-corpus proof | exact-10m-counted-projection |
| active candidate | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | n/a | n/a | no constructive result is present for the active candidate | not started |

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|
| 1,000,000 | `baseline_lzma` | 290,933 | 290,732 | 201 | 29.0933 | `results/baseline_lzma/2026-07-18T135552.json` |

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|
| 1,000,000 | `baseline_lzma` | 290,732 | 290,933 | 201 | 2.325856 | `results/baseline_lzma/2026-07-18T135552.json` |

## Notes

- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 10.95 proof requires a full 1GB result with score <= 109500000.
