# Hutter Upper-Bound Certificate

## Constructive Theorem

If roundtrip_ok is true for archive A and decoder D on target corpus x, then |A| + |D| is a constructive upper bound for x in this testbed.

## Target

- Full input bytes: `1,000,000,000`
- 9.6000000% target score: `96,000,000`
- Calibrated baseline score: `110,181,114`
- Required net gain from calibrated baseline: `14,181,114` bytes
- Required archive slope before program cost: `0.113448912` bits/byte

## Proof Status

- Full-corpus constructive result present: `False`
- 9.6000000% constructive upper bound present: `False`

## Top Status

| Claim | Program | Scope | Score | Evidence | Status |
|---|---|---:|---:|---|---|
| best exact 10M | `n/a` | 10,000,000 | n/a | no exact 10M result has complete score accounting and independent decode; see unranked rows and withdrawn claims | missing |
| best exact 10M archive | `fx2_trim_scale10m_v1` | 10,000,000 | n/a | exact result JSON with roundtrip_ok true; archive-slope reference only | exact artifact-backed |
| best exact 100M | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 100,000,000 | 15,040,789 | metadata-inherited from parent 100M geometry package; no result JSON for this row is present in this checkout | metadata-inherited |
| best full 1G | `n/a` | 1,000,000,000 | n/a | no verified full-corpus result JSON is present in this checkout | not verified |
| best forecast | `n/a` | n/a | n/a | no forecast candidate has complete score accounting with in-repository provenance; withdrawn claims are listed separately | no ranked forecast |
| active candidate | `n/a` | n/a | n/a | Recorded ownership remains unresolved; no launch permission is inferred. | unknown |

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|
| 10,000 | `nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1` | 6,229 | 240,248 | 234,019 | 4.9832 | `results/nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1/2026-07-27T213234.json` |
| 250,000 | `fx2_expert_transfer250k_v1` | 9,488 | unknown | unknown | 0.303616 | `results/fx2_expert_transfer250k_v1/D.driver.json` |
| 1,000,000 | `fx2_expert_confirm1m_v1` | 131,187 | unknown | unknown | 1.049496 | `results/fx2_expert_confirm1m_v1/D.driver.json` |
| 10,000,000 | `fx2_trim_scale10m_v1` | 1,305,268 | unknown | unknown | 1.0442144 | `results/fx2_trim_scale10m_v1/D.driver.json` |

## Unranked Counted Rows (Not Scores)

Smallest counted constructive row per scope that fails the ranking rule.

| data_size | program | counted | archive | program_size | excluded because | result |
|---:|---|---:|---:|---:|---|---|
| 10,000 | `nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1` | 240,248 | 6,229 | 234,019 | score_accounting_complete is not true; independent_decode_ok is not true | `results/nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1/2026-07-27T213234.json` |
| 250,000 | `opcode_typed_anchor_bitmix_v1` | 72,800 | 67,959 | 4,841 | score_accounting_complete is not true; independent_decode_ok is not true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T124407.json` |
| 1,000,000 | `sleeping_trie_global4_selector_raw_v1` | 494,499 | 473,912 | 20,587 | score_accounting_complete is not true; independent_decode_ok is not true | `results/sleeping_trie_global4_selector_raw_v1/2026-08-01T193730.json` |
| 10,000,000 | `endpoint428_pair_layer0_runtime_successor_minified_package_v1` (WITHDRAWN) | 1,895,625 | 1,634,500 | 261,125 | score_accounting_complete is not true; independent_decode_ok is not true; evidence references a path outside the repository; claim withdrawn | `results/endpoint428_pair_layer0_runtime_successor_minified_package_v1/receipt.json` |

## Withdrawn Claims

| Claim | Program | Withdrawn value | Withdrawn | Reason | Evidence |
|---|---|---:|---|---|---|
| best exact 10M | `endpoint428_pair_layer0_runtime_successor_minified_package_v1` | 1,895,625 | 2026-11-26 | The 261,125-byte package is grounded only in an untracked host-local path the certificate never checked; score accounting and independent decode were never established, and the archive is 329,232 bytes larger than fx2_trim_scale10m_v1 on the same 10M input. | `results/endpoint428_pair_layer0_runtime_successor_minified_package_v1/receipt.json` |
| best forecast | `endpoint428_gate_dot_fuse_output_update_loop_v1` | 109,389,323 | 2026-11-26 | Built on the withdrawn package; 52.4% of its forecast drop came from LZMA re-zipping and comment stripping, the linear x66.96 calibration is not supported by offset-500M slices, and its parent projects 88.7 h against a ~15 h runtime cap. | `docs/hutter_frontier.json; results/endpoint428_pair_layer0_runtime_successor_10m_v1/receipt.json` |

## Notes

- A counted row ranks as a score only when score_accounting_complete and independent_decode_ok are true and its evidence stays inside the repository; forecasts rank only on complete in-repository accounting.
- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Unknown program costs or explicitly unknown totals remain unknown; archive-only rows do not compete in counted-score rankings.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 9.6000000% proof requires a full 1,000,000,000-byte result with score <= 96,000,000.
- Canonical proof rows include only Git-tracked result JSON files; ignored host-local artifacts are noncanonical.
