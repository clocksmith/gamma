# Head-to-Head Boundary Race: BITS Nullspace-Kernel vs. Canzar et al. (2012) Flow Solver

- **Rule:** `W2` (`max_bytes = 160`, whole programs excluded), per-query timeout `60 s`.
- **Verification bar:** both sides timed to the exact same independently verified artifact (`IMPOSSIBLE` lower-bound certificate with zero floating-point trust, or `FEASIBLE` legal dictionary + byte-exact parse).
- **Soundness contradictions:** `0` across `24` queries (`21` non-trivial queries with `K < |Sigma|`).

## 1. Structural Profile of the 12 Unseen Corpora (Nullspace-Kernel Theorem)

| ID | Language | Bytes | `|Sigma|` | Rank `r` | Nullity `d` | `|S_free|` | `k_free` | `Delta_det*` | Kernel Verdict | Exact `OPT`? | Profile (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| B01 | Python | 3657 | 58 | 58 | 0 | 0 | 0 | 0 | `SATURATED` | 58 | 11.8 |
| B02 | Zig | 3664 | 59 | 59 | 0 | 0 | 0 | 0 | `SATURATED` | 59 | 10.0 |
| B03 | WGSL | 2237 | 64 | 64 | 0 | 0 | 0 | 0 | `SATURATED` | 64 | 6.1 |
| B04 | WGSL | 5976 | 65 | 22 | 43 | 56 | 13 | 0 | `RANK_UNATTAINABLE` | >=23 | 2950.9 |
| B05 | JavaScript | 1797 | 66 | 66 | 0 | 0 | 0 | 0 | `SATURATED` | 66 | 8.1 |
| B06 | Python | 8255 | 67 | 67 | 0 | 0 | 0 | 0 | `SATURATED` | 67 | 25.5 |
| B07 | C | 3308 | 68 | 65 | 3 | 5 | 2 | 0 | `RANK_ATTAINED` | 65 | 94.9 |
| B08 | Python | 5248 | 69 | 69 | 0 | 0 | 0 | 0 | `SATURATED` | 69 | 19.9 |
| B09 | JavaScript | 5204 | 70 | 70 | 0 | 0 | 0 | 0 | `SATURATED` | 70 | 21.1 |
| B10 | C | 6434 | 71 | 71 | 0 | 0 | 0 | 0 | `SATURATED` | 71 | 22.3 |
| B11 | WGSL | 9186 | 73 | 62 | 11 | 13 | 2 | 2 | `RANK_ATTAINED` | 62 | 1580.7 |
| B12 | JavaScript | 4167 | 74 | 74 | 0 | 0 | 0 | 0 | `SATURATED` | 74 | 18.6 |

## 2. Aggregate Race Summary (Non-trivial Queries: `K < |Sigma|`)

| Metric | BITS (stdlib Python) | Canzar et al. (HiGHS LP/MILP) |
| --- | ---: | ---: |
| Non-trivial queries settled (`/21`) | **21** | **16** |
| Unresolved / Timeout | 0 / 0 | 0 / 5 |
| Settled exclusively by this side | 5 | 0 |
| `IMPOSSIBLE` queries settled by both (`n=15`) total wall time | **537.4 ms** | 64621.7 ms (median speedup **39.23x**) |
| Below-alphabet `FEASIBLE` settled by both (`n=1`) total wall time | **122.6 ms** | 1613.6 ms (median speedup **13.16x**) |

## 3. Query-by-Query Ledger (`24` Queries Across `12` Unseen Projects)

| ID | Query | `K` | `|Sigma|` | BITS Verdict | BITS LB / D | BITS (ms) | BITS KiB | Canzar Verdict | Canzar LB / D | Canzar Phase | Canzar (ms) | Speedup |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| B01 | 64-slot-cliff | 64 | 58 | `FEASIBLE` | 58 / 58 | 24.8 | 238 | `FEASIBLE` | - / 58 | `singleton` | 0.8 | 0.0x |
| B01 | below-alphabet | 57 | 58 | `IMPOSSIBLE` | 58 / - | 24.1 | 238 | `IMPOSSIBLE` | 58 / - | `primal-flow-lp` | 1146.1 | 47.5x |
| B02 | 64-slot-cliff | 64 | 59 | `FEASIBLE` | 59 / 59 | 21.0 | 204 | `FEASIBLE` | - / 59 | `singleton` | 0.8 | 0.0x |
| B02 | below-alphabet | 58 | 59 | `IMPOSSIBLE` | 59 / - | 20.5 | 204 | `IMPOSSIBLE` | 59 / - | `primal-flow-lp` | 1528.8 | 74.7x |
| B03 | 64-slot-cliff | 64 | 64 | `FEASIBLE` | 64 / 64 | 12.2 | 160 | `FEASIBLE` | - / 64 | `singleton` | 0.5 | 0.0x |
| B03 | below-alphabet | 62 | 64 | `IMPOSSIBLE` | 64 / - | 11.6 | 160 | `TIMEOUT` | - / - | `lp-timeout` | 60083.9 | 5165.4x |
| B04 | 64-slot-cliff | 64 | 65 | `FEASIBLE` | 30 / 60 | 27688.7 | 9974 | `TIMEOUT` | - / - | `lp-timeout` | 60367.5 | 2.2x |
| B04 | below-alphabet | 63 | 65 | `FEASIBLE` | 30 / 60 | 27123.8 | 9974 | `TIMEOUT` | - / - | `lp-timeout` | 60366.8 | 2.2x |
| B05 | 64-slot-cliff | 64 | 66 | `IMPOSSIBLE` | 66 / - | 14.3 | 245 | `IMPOSSIBLE` | 66 / - | `primal-flow-lp` | 61.3 | 4.3x |
| B05 | below-alphabet | 64 | 66 | `IMPOSSIBLE` | 66 / - | 14.1 | 245 | `IMPOSSIBLE` | 66 / - | `primal-flow-lp` | 61.2 | 4.3x |
| B06 | 64-slot-cliff | 64 | 67 | `IMPOSSIBLE` | 67 / - | 53.1 | 476 | `IMPOSSIBLE` | 67 / - | `primal-flow-lp` | 790.9 | 14.9x |
| B06 | below-alphabet | 65 | 67 | `IMPOSSIBLE` | 67 / - | 53.0 | 476 | `IMPOSSIBLE` | 67 / - | `primal-flow-lp` | 787.5 | 14.9x |
| B07 | 64-slot-cliff | 64 | 68 | `IMPOSSIBLE` | 65 / - | 27.9 | 270 | `IMPOSSIBLE` | 65 / - | `primal-flow-lp` | 1374.1 | 49.3x |
| B07 | below-alphabet | 66 | 68 | `FEASIBLE` | 65 / 65 | 122.6 | 971 | `FEASIBLE` | 65 / 65 | `lp-integral` | 1613.6 | 13.2x |
| B08 | 64-slot-cliff | 64 | 69 | `IMPOSSIBLE` | 69 / - | 39.6 | 335 | `IMPOSSIBLE` | 69 / - | `primal-flow-lp` | 8501.4 | 214.9x |
| B08 | below-alphabet | 67 | 69 | `IMPOSSIBLE` | 69 / - | 39.8 | 335 | `IMPOSSIBLE` | 69 / - | `primal-flow-lp` | 8434.2 | 211.8x |
| B09 | 64-slot-cliff | 64 | 70 | `IMPOSSIBLE` | 70 / - | 43.2 | 366 | `IMPOSSIBLE` | 70 / - | `primal-flow-lp` | 1696.5 | 39.2x |
| B09 | below-alphabet | 68 | 70 | `IMPOSSIBLE` | 70 / - | 43.6 | 366 | `IMPOSSIBLE` | 70 / - | `primal-flow-lp` | 1709.8 | 39.2x |
| B10 | 64-slot-cliff | 64 | 71 | `IMPOSSIBLE` | 71 / - | 46.9 | 364 | `IMPOSSIBLE` | 71 / - | `primal-flow-lp` | 19031.7 | 405.9x |
| B10 | below-alphabet | 69 | 71 | `IMPOSSIBLE` | 71 / - | 46.0 | 364 | `IMPOSSIBLE` | 71 / - | `primal-flow-lp` | 19080.7 | 414.5x |
| B11 | 64-slot-cliff | 64 | 73 | `FEASIBLE` | 62 / 62 | 1624.7 | 3774 | `TIMEOUT` | - / - | `lp-timeout` | 60264.0 | 37.1x |
| B11 | below-alphabet | 71 | 73 | `FEASIBLE` | 62 / 62 | 1619.7 | 3774 | `TIMEOUT` | - / - | `lp-timeout` | 60266.8 | 37.2x |
| B12 | 64-slot-cliff | 64 | 74 | `IMPOSSIBLE` | 74 / - | 35.8 | 386 | `IMPOSSIBLE` | 74 / - | `primal-flow-lp` | 208.8 | 5.8x |
| B12 | below-alphabet | 72 | 74 | `IMPOSSIBLE` | 74 / - | 35.4 | 386 | `IMPOSSIBLE` | 74 / - | `primal-flow-lp` | 208.7 | 5.9x |


## 4. Pre-registered Predictions Check, Audit Note, and Honest Caveats

- **P1 (Zero soundness violations — PASS):** `0` contradictions across all `24` queries; 100% of `IMPOSSIBLE` certificates and `FEASIBLE` dictionaries passed independent exact verification (`Fraction` potential check for Canzar; $\mathbb{F}_p$ RREF / Nullspace-Kernel check for BITS; byte-exact `parse_program` for all `FEASIBLE` dictionaries).
- **P2 (Nullspace-Kernel structure on unseen code — PASS):** `10/12` unseen corpora satisfied $\Delta_{\mathrm{det}}^{\star} = 0$ with $|S_{\mathrm{free}}| \le 12$ (predicted `>= 8/12`), and `3/12` unseen corpora beat their alphabet size (`B07`: `68 -> 65`; `B11`: `73 -> 62 < 64`; `B04`: `65 -> <=60 < 64`, predicted `>= 2/12`).
- **P3 (Rejection speedup — PASS):** On all `15` non-trivial `IMPOSSIBLE` queries settled by both sides, BITS took `537.4 ms` total vs. Canzar's `64,621.7 ms` (median speedup **`39.2x`**, predicted `>= 10x`; up to `414.5x` on `B10`, plus `B03 K=62` where BITS proved `IMPOSSIBLE` in `11.6 ms` while Canzar timed out at `60,084 ms`).
- **P4 (Below-alphabet construction — PASS on both sides of 64 slots):** BITS settled **`5/5`** below-alphabet `FEASIBLE` queries (`B07 K=66` exact `65` in `122.6 ms` vs. Canzar `1,613.6 ms` [`13.2x`]; `B11 K=64, 71` exact `62` via `['MAX_WORKGROUP_SIZE', 'WORKGROUP_SIZE']` in `1.62 s` while Canzar timed out at `60.3 s`; `B04 K=64, 63` byte-exact `60` in `27.1-27.7 s` while Canzar timed out at `60.4 s`).
- **P5 (Structural failure boundary validated on `B04`):** `B04` (`wgsl-linear-attention-kernels`, two nearly identical f32/f16 shader pairs) had `d = 43`, `|S_free| = 56`, where the Nullspace-Kernel Theorem immediately reported `RANK_UNATTAINABLE` (`>= 23`) and handed off to Tier 3 (`fast_constructive_dictionary`, `27 s`), confirming the exact boundary between small-kernel corpora (`11/12` projects, `6 ms`--`1.6 s`) and large-nullspace twin-file corpora (`B04`).

### Transparent Audit Notes & Caveats

1. **Pre-audit Canzar LP wrapper fix (`race_canzar.py`):** In the initial run after freeze commit `c0c927633`, `linprog(..., bounds=(0, 1))` introduced non-zero upper-bound duals `u_t` on token variables `x_t <= 1`, causing our rational potential rescaler to halve Canzar's certified lower bound on `B01`, `B06`, `B09`, `B10`, and `B12`. Changing that single argument to `bounds=(0, None)` (leaving `diagnostic.py`, `boundary-instances.json`, and `PREREGISTRATION.md` byte-identical to `c0c927633`) restored Canzar's full primal flow LP duals on all 5 corpora. All numbers in Sections 1--3 are from the unhandicapped `bounds=(0, None)` run.
2. **Trivial singleton queries (`K >= |Sigma|`):** On `B01`, `B02`, and `B03` at `K = 64`, Canzar's `0.5-0.8 ms` singleton shortcut beat BITS (`12-25 ms`) because `diagnose_full_corpus` still computes `certified_rank_bound` before returning the trivial alphabet dictionary.
3. **Duplicate budget on `B05`:** Because `|Sigma| = 66` on `B05`, the symmetric rule `K = |Sigma| - 2` evaluated `K = 64` twice (`23` distinct queries across `24` rows).
4. **Separate press-count question:** Fitting `62 <= 64` slots on `B11` or `60 <= 64` on `B04` proves lossless fixed-width 6-bit capacity without escapes; whether 6-bit saves presses or encoded bits over 7/8-bit or BPE remains a separate bake-off.
