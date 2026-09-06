# Hutter Upper-Bound Certificate

## Constructive Theorem

If roundtrip_ok is true for archive A and decoder D on target corpus x, then |A| + |D| is a constructive upper bound for x in this testbed.

## Target

- Full input bytes: `1,000,000,000`
- 9.9000000% target score: `99,000,000`
- Calibrated baseline score: `110,181,114`
- Required net gain from calibrated baseline: `11,181,114` bytes
- Required archive slope before program cost: `0.089448912` bits/byte

## Proof Status

- Full-corpus constructive result present: `False`
- 9.9000000% constructive upper bound present: `False`

## Top Status

| Claim | Program | Scope | Score | Evidence | Status |
|---|---|---:|---:|---|---|
| best exact 10M | `endpoint428_pair_layer0_runtime_successor_minified_package_v1` | 10,000,000 | 1,895,625 | exact result JSON with roundtrip_ok true | exact artifact-backed |
| best exact 10M archive | `endpoint428_pair_layer0_runtime_successor_10m_v1` | 10,000,000 | 1,914,647 | exact result JSON with roundtrip_ok true; archive-slope reference only | exact artifact-backed |
| best exact 100M | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 100,000,000 | 15,040,789 | metadata-inherited from parent 100M geometry package; no result JSON for this row is present in this checkout | metadata-inherited |
| best full 1G | `n/a` | 1,000,000,000 | n/a | no verified full-corpus result JSON is present in this checkout | not verified |
| best forecast | `endpoint428_gate_dot_fuse_output_update_loop_v1` | 10,000,000 | 109,389,323 | canonical source-bound frontier selection backed by exact 10M codec replay and counted package evidence; forecast only, not a constructive full-corpus proof | source-bound-canonical-forecast |
| active candidate | `endpoint428_horizon_retained_parent_trace_q0_v1` | 1,000,000,000 | n/a | Existing observer binds the active source processes; terminal scientific evidence is absent. | running diagnostic |
| active gate | `endpoint428_horizon_retained_parent_trace_q0_v1` | 1,000,000,000 | n/a | Wait for the existing observer. Recovered probabilities cannot restore missing continuous resource evidence. | running |

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|
| 10,000 | `nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1` | 240,248 | 6,229 | 234,019 | 2402.48 | `results/nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1/2026-07-27T213234.json` |
| 250,000 | `opcode_word_bz2_min_deflate_v1` | 73,335 | 71,887 | 1,448 | 29.334 | `results/opcode_word_bz2_min_deflate_v1/2026-07-21T124141.json` |
| 1,000,000 | `sleeping_trie_global4_selector_raw_v1` | 494,499 | 473,912 | 20,587 | 49.4499 | `results/sleeping_trie_global4_selector_raw_v1/2026-08-01T193730.json` |
| 10,000,000 | `endpoint428_pair_layer0_runtime_successor_minified_package_v1` | 1,895,625 | 1,634,500 | 261,125 | 18.95625 | `results/endpoint428_pair_layer0_runtime_successor_minified_package_v1/receipt.json` |

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|
| 10,000 | `nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1` | 6,229 | 240,248 | 234,019 | 4.9832 | `results/nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1/2026-07-27T213234.json` |
| 250,000 | `opcode_word_bz2_min_deflate_v1` | 71,887 | 73,335 | 1,448 | 2.300384 | `results/opcode_word_bz2_min_deflate_v1/2026-07-21T124141.json` |
| 1,000,000 | `sleeping_trie_global4_selector_raw_v1` | 473,912 | 494,499 | 20,587 | 3.791296 | `results/sleeping_trie_global4_selector_raw_v1/2026-08-01T193730.json` |
| 10,000,000 | `endpoint428_pair_layer0_runtime_successor_10m_v1` | 1,634,500 | 1,914,647 | 280,147 | 1.3076 | `results/endpoint428_pair_layer0_runtime_successor_10m_v1/receipt.json` |

## Notes

- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 9.9000000% proof requires a full 1,000,000,000-byte result with score <= 99,000,000.
- Canonical proof rows include only Git-tracked result JSON files; ignored host-local artifacts are noncanonical.
