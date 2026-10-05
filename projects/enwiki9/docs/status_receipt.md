# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-10-05T03:18:15+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-96m-v4`
- Objective digest: `sha256:409b70547f901a3ac5fffd7fd7a1e1d77b05fb44d9e9d889be1337bd153706d7`
- Objective path: `contracts/research/v4/objective-contract.json`
- Active `9.6000000%` target score: `96,000,000`
- Full-corpus constructive result present: `false`
- Active objective constructive upper bound present: `false`
- Source certificate target (legacy field names): `96,000,000`; certificate upper bound present: `false`

## Operator Summary

- Candidate: `lexth11c_decode_full1g_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `1,000,000,000`
- Scope unit: `raw byte`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Active scorer observed: `true`
- Active cmix mode: `encode`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `17,609`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `6,708,672`
- Latest sampled single RSS KiB: `6,708,672`
- Tightest binary single-process margin KiB: `3,777,088`
- Tightest decimal single-process margin KiB: `3,056,953`
- Latest binary single-process margin KiB: `3,777,088`
- Latest decimal single-process margin KiB: `3,056,953`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `27`
- Held pending adaptive jobs: `26`
- Claimable pending adaptive jobs: `1`
- Canonical release bundles: `4`
- Validated release run receipts: `0`
- Validated failed release attempts: `0`
- Objective-achieved receipts: `0`
- Release index mode: `structure-only-router`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `lexth11c_decode_full1g_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `1,000,000,000`
- Scope unit: `raw byte`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Coordinator PID: `n/a`
- Driver result JSON: `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/run_logs/adaptive/20261005T004723Z_accb851c38.resources/guard.json`
- RSS guard present: `true`
- Execution mode: `discovery`
- Timing authority: `diagnostic`
- Declared memory envelope bytes: `12,884,901,888`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, matching live worker, or frozen adopted process identities.`
- RSS guard status: `running`
- RSS guard JSON bytes: `75,891`
- RSS guard JSON modified UTC: `2026-10-05T03:18:15+00:00`
- RSS guard JSON SHA-256: `7c60febd9889f61e351c3b8c55b73bb644c9f20c70fec272898de8d061d5fa13`
- RSS samples: `17,609`
- Max sampled single RSS KiB: `6,708,672`
- Max sampled tree RSS KiB: `6,836,240`
- Single-process RSS margin KiB: `3,777,088`
- Single-process decimal `10GB` margin KiB: `3,056,953`
- Tree RSS margin KiB: `3,649,520`
- Tree decimal `10GB` margin KiB: `2,929,385`
- Latest sampled single RSS KiB: `6,708,672`
- Latest sampled tree RSS KiB: `6,836,240`
- Latest sampled single-process margin KiB: `3,777,088`
- Latest sampled single-process decimal `10GB` margin KiB: `3,056,953`
- Latest sampled tree margin KiB: `3,649,520`
- Latest sampled tree decimal `10GB` margin KiB: `2,929,385`
- Cgroup memory peak bytes: `7,056,596,992`
- Latest cgroup current bytes: `7,056,596,992`
- Cgroup event deltas: `{'high': 0, 'low': 0, 'max': 0, 'oom': 0, 'oom_group_kill': 0, 'oom_kill': 0, 'sock_throttled': 0}`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `lexth11c_decode_full1g_q0_v1`
- Expected scope bytes: `1,000,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |
|---|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `lexth11c_decode_full1g_q0_v1`
- Expected active scope bytes: `1,000,000,000`
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
- Inventory generated: `2026-10-05T03:09:01+00:00`
- Snapshot identity is verified; inventory inputs were not rescanned. This is not live occupancy or launch authority.
- Program directories: `1,115`
- Registered programs: `654`
- Untracked nonignored entries: `2`
- Modified tracked entries: `5`
- Candidate statuses: `active=18, blocked_dependency=118, candidate=281, measured_negative=100, retired=598`

## View Refresh

- Profile: `routine`
- Historical reports were not refreshed by this routine/status operation and may be stale. Use enwiki9_normalize_receipts.py --profile full for historical audits.

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 1,669,332 | 332,888 | 42,388 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/enwiki9_lab.py run --candidate lexth11c_decode_full1g_q0_v1 --max-workers 1` |
| `resource_guard` | 1,669,431 | 1,669,332 | 54,880 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3.py --limit-kib 12582912 --official-decimal-limit-kib 12582912...` |
| `process` | 3,326,473 | 332,888 | 4,048 | `bash -c cd /home/x/deco/gamma/projects/enwiki9 && /usr/bin/taskset --cpu-list 12 python3 tools/enwiki9_lab.py run --candidate lexth11c_recompress_f...` |
| `process` | 3,326,474 | 3,326,473 | 44,028 | `python3 tools/enwiki9_lab.py run --candidate lexth11c_recompress_full1g_q0_v4 --max-workers 1 --min-free-mib 16384 --max-load 16` |
| `resource_guard` | 3,326,760 | 3,326,474 | 34,696 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3.py --limit-kib 12582912 --official-decimal-limit-kib 12582912...` |
| `process` | 1,669,450 | 1,669,431 | 123,748 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/lexth11c_reproduction_v1.py --root /home/x/deco/gamma/projects/enwiki9 --output /home/x/...` |
| `process` | 1,669,523 | 1,669,450 | 2,364 | `/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --dir /runtime --dir /runtime/lib --dir /lib64 --proc /proc --dev /dev --bi...` |
| `process` | 1,669,524 | 1,669,523 | 1,456 | `/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --dir /runtime --dir /runtime/lib --dir /lib64 --proc /proc --dev /dev --bi...` |
| `process` | 1,669,525 | 1,669,524 | 6,708,664 | `./archive9` |
| `process` | 3,326,774 | 3,326,760 | 24,220 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/lexth11c_full_control_v2.py --root . --output results/lexth11c_recompress_full1g_q0_v4 -...` |
| `process` | 3,328,455 | 3,326,774 | 2,388 | `/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --dir /runtime --dir /runtime/lib --dir /lib64 --proc /proc --dev /dev --bi...` |
| `process` | 3,328,457 | 3,328,455 | 1,456 | `/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --dir /runtime --dir /runtime/lib --dir /lib64 --proc /proc --dev /dev --bi...` |
| `native_cmix` | 3,328,459 | 3,328,457 | 6,007,324 | `./cmix -e /input o` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/.cmix.temp` | 52,330,496 | `2026-10-05T03:18:15+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode.stderr` | 818,298 | `2026-10-05T03:18:12+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode.stdout` | 3,199 | `2026-10-05T03:17:22+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/.ready4cmix_decomp` | 92,559,456 | `2026-10-05T00:51:13+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/.tfweights` | 2,978,039 | `2026-10-05T00:51:13+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/.dict` | 411,996 | `2026-10-05T00:51:13+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/.dict.comp_decomp` | 100,866 | `2026-10-05T00:50:35+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/test.dat` | 16 | `2026-10-05T00:50:35+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/launch.json` | 2,062 | `2026-10-05T00:50:35+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/decode/archive9` | 95,836,613 | `2026-10-05T00:50:35+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/accounting.json` | 583 | `2026-10-05T00:50:35+00:00` |
| `projects/enwiki9/results/lexth11c_decode_full1g_q0_v1/snapshot/tools/lexth11c_reproduction_v1.py` | 250 | `2026-10-05T00:50:35+00:00` |

## Active RSS

- Max cmix PID: `3328459`
- Active cmix mode: `encode`
- Max cmix RSS KiB: `6,007,324`
- Active process tree RSS KiB: `13,051,660`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `4,478,436`
- Single-process decimal margin KiB: `3,758,301`
- Active process tree margin KiB (binary): `-2,565,900`
- Active process tree decimal margin KiB: `-3,286,035`
- Temp input path: `/input`
- Temp output path: `/work/o`
- Temp output staging path: `/work/o.cmix.temp`
- Temp input bytes: `n/a`
- Temp output bytes: `n/a`
- Temp output staging bytes: `n/a`
- Temp input modified UTC: `n/a`
- Temp output modified UTC: `n/a`
- Temp output staging modified UTC: `n/a`
- Process read bytes: `16,384`
- Process write bytes: `6,571,327,488`
- Active process tree warning: `active process tree RSS crossed the local numeric guard; the running kill guard is single-process`

## Contingencies

- If current gate passes: `record pass and inspect the frozen candidate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `fx2_trim_scale10m_v1`; status `exact artifact-backed`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `9.6000000%` full-corpus target.
