# Witness-rule coverage scaling across 40, 80 and 160 programs (`witness-scaling-v1`)

Pre-registered follow-on scaling study (Item 9) testing how witness-rule coverage curves, proven intervals, and cheap algebraic certificates behave as cohort size scales from `40 -> 80 -> 160` programs across two disjoint public source families (`lodash@4.17.21` root `.js` modules and `CPython 3.14.2` `Lib/` top-level `def` functions), plus a controlled module-locality contrast (`P-80-clustered` vs `P-80-diverse`).

- **Pre-registration:** frozen and committed before execution at Gamma `b4b405f80` (`PREREGISTRATION.md`, `SHA256SUMS-FROZEN`).
- **Results & prediction scoreboard:** `RESULTS.md` (`7/10` pre-registered predictions passed, `3/10` failed — `S5`, `S6`, `S8` — with full failure analysis and an explicit cheap-certificate vs. escalation decision rule).

## Reproduce & verify (no solver required to verify)

```sh
shasum -a 256 -c SHA256SUMS-FROZEN
shasum -a 256 -c SHA256SUMS-RESULTS
python3 -B check_scaling.py cohorts.json results.json
```

`check_scaling.py` uses Python 3.10+ and `numpy` only (no `scipy` or MILP/LP solver). It replays all `656` stored dictionaries and all `1,322` single-character sets against `cohorts.json`, recomputes all forced-block ranks and whole-program ranks in two prime fields, and checks all `208` stored integer LP dual certificates in exact integer arithmetic.

To rerun from scratch (requires `scipy`):

```sh
python3 -B run_scaling.py cohorts.json results.json
```

## Files

| File | Description |
| --- | --- |
| `PREREGISTRATION.md` | Frozen questions, selection rules, fixed search/bound protocol, and 10 falsifiable predictions (`S1`–`S10`) |
| `select_cohorts.py` | Deterministic selector (metadata/size/AST spans only; never writes local paths) |
| `cohorts.json` | 14 disjoint cohorts (`1,280` programs, zero overlap) |
| `run_scaling.py` | Frozen evaluation and out-of-sample curve-generalization script |
| `check_scaling.py` | Independent solver-free verifier (`numpy` only) |
| `results.json` | Full per-budget bounds, replayed dictionaries, integer LP dual certificates, and out-of-sample scores |
| `scaling-summary.csv` | One row per cohort (ranks, intervals, `25/50/75%` thresholds, `K=64`, fragment lift) |
| `scaling-curves.csv` | Full per-budget curves on raw and normalized axes (`1,322` rows) |
| `out-of-sample.csv` | Out-of-sample MAE and interval-violation scores across 20 held-out cohort pairs |
| `RESULTS.md` | Prediction scoreboard (`7/10`), analysis of the 3 failed predictions, and cheap-certificate vs. escalation rule |
| `SHA256SUMS-FROZEN` | Checksums of pre-registration artifacts (frozen at `b4b405f80`) |
| `SHA256SUMS-RESULTS` | Checksums of output artifacts and `RESULTS.md` |
