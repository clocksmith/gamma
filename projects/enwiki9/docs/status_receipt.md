# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-09-09T01:18:52+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-90m-v3`
- Objective digest: `sha256:e91ff20e92c3cac8acb0cbe5c79fc8e8a3b427d7e151245c8eecc52b1c32fa00`
- Objective path: `contracts/research/v3/objective-contract.json`
- Active `9.0000000%` target score: `90,000,000`
- Full-corpus constructive result present: `false`
- Active objective constructive upper bound present: `false`
- Source certificate target (legacy field names): `90,000,000`; certificate upper bound present: `false`

## Operator Summary

- Candidate: `opcode_event_parse_confirmation1m_q0_v1`
- Scope bytes: `1,000,000`
- Scope symbols: `n/a`
- Scope unit: `raw byte`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `n/a`
- RSS samples: `n/a`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `n/a`
- Latest sampled single RSS KiB: `n/a`
- Tightest binary single-process margin KiB: `n/a`
- Tightest decimal single-process margin KiB: `n/a`
- Latest binary single-process margin KiB: `n/a`
- Latest decimal single-process margin KiB: `n/a`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `26`
- Held pending adaptive jobs: `26`
- Claimable pending adaptive jobs: `0`
- Canonical release bundles: `2`
- Validated release run receipts: `0`
- Validated failed release attempts: `0`
- Objective-achieved receipts: `0`
- Release index mode: `structure-only-router`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `opcode_event_parse_confirmation1m_q0_v1`
- Scope bytes: `1,000,000`
- Scope symbols: `n/a`
- Scope unit: `raw byte`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Coordinator PID: `n/a`
- Driver result JSON: `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `not present`
- RSS guard present: `unknown`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, matching live worker, or frozen adopted process identities.`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `opcode_event_parse_confirmation1m_q0_v1`
- Expected scope bytes: `1,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |
|---|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `opcode_event_parse_confirmation1m_q0_v1`
- Expected active scope bytes: `1,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch candidate gate: `false`
- Action: `wait_for_gate_receipts`
- Reason: `the gate state is incomplete and cannot drive a mutation yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Gate mutation allowed: `false`
- Recommended action: `wait_for_gate_receipts`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Audit mode: `inventory_snapshot`
- Inventory generated: `2026-09-09T00:42:26+00:00`
- Snapshot identity is verified; inventory inputs were not rescanned. This is not live occupancy or launch authority.
- Program directories: `1,013`
- Registered programs: `552`
- Untracked nonignored entries: `1`
- Modified tracked entries: `1`
- Candidate statuses: `active=18, blocked_dependency=76, candidate=247, measured_negative=100, retired=572`

## View Refresh

- Profile: `routine`
- Historical reports were not refreshed by this routine/status operation and may be stale. Use enwiki9_normalize_receipts.py --profile full for historical audits.

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 3,639,003 | 2,643,307 | 42,556 | `python3 tools/enwiki9_lab.py run --candidate opcode_event_parse_confirmation1m_q0_v1 --max-workers 1` |
| `resource_guard` | 3,639,172 | 3,639,003 | 37,616 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3.py --limit-kib 4194304 --official-decimal-limit-kib 4194304 -...` |
| `process` | 3,639,186 | 3,639,172 | 26,036 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/opcode_event_parse_confirmation_gate_v1.py` |
| `process` | 3,815,620 | 3,639,186 | 476,728 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/opcode_event_parse_corpus1m_v1.py encode /home/x/deco/gamma/projects/enwiki9/results/opc...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-repeat.stderr` | 0 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-repeat.stdout` | 0 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-decode.execution.json` | 863 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-decode.stdout` | 133 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-decode.audit.json` | 94,857 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K.raw` | 1,000,000 | `2026-09-09T01:18:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-decode.stderr` | 0 | `2026-09-09T01:16:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-encode.execution.json` | 879 | `2026-09-09T01:16:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-encode.stdout` | 127 | `2026-09-09T01:16:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-encode.audit.json` | 94,857 | `2026-09-09T01:16:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K.arc` | 259,468 | `2026-09-09T01:16:29+00:00` |
| `projects/enwiki9/results/opcode_event_parse_confirmation1m_q0_v1/K-encode.stderr` | 0 | `2026-09-09T01:12:43+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `582,936`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `9,902,824`
- Active process tree decimal margin KiB: `9,182,689`

## Contingencies

- If current gate passes: `record pass and inspect the frozen candidate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `endpoint428_pair_layer0_runtime_successor_10m_v1`; status `exact artifact-backed`; score `1,914,647`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `9.0000000%` full-corpus target.
