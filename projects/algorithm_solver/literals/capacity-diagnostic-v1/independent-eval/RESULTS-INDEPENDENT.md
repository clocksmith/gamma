# Independent Whole-Project JS / Python / C Diagnostic Evaluation Receipt (`3e15a8dce`)

Single-pass evaluation of the 9 independently selected whole-project corpora (27 queries under `W2`) frozen at `3e15a8dce` before running `evaluate_independent.py`.

## Provenance & Integrity
- **Independent selector:** isolated read-only subagent (`92b412f0`) that never read `capacity-diagnostic-v1/`, `capacity-theorems-v1/`, `capacity-impossibility-v1/`, `witness-coverage-v1/`, `sixbit-v1/`, or anything under `projects/algorithm_solver/`.
- **Whole-project separation:** 9 mutually disjoint projects/subsystems across JavaScript (`JS-1..3`), Python (`PY-1..3`), and C (`C-1..3`), pinned to `clocksmith/gamma@59ff0441` (7 corpora) and `clocksmith/fawn@a281360f` (2 compact borderline C corpora `C-1`, `C-2`).
- **Pre-scoring freeze verified:** `SHA256SUMS-INDEPENDENT` 5/5 OK; zero edits to instances or predictions after scoring.
- **Evaluator revision:** `e2d88e693` (includes the rank-attaining field fix and forced-block decomposition).

## Headline Metrics (Zero LP/MILP Solver Calls)
- **Settled without a solver:** **`27/27` (`100.0%`)** — `9` `IMPOSSIBLE` (with checkable certificates), `18` `FEASIBLE` (with byte-exact verified dictionaries), `0` `UNRESOLVED`.
- **Agreement with selector's pre-registered primary predictions:** `27/27` settled matches, `0` settled misses.
- **Lift over forced singletons (`|F_1|`) alone:** On **`8/9` (`88.9%`)** of the `IMPOSSIBLE` queries (`JS-1_K48`, `JS-2_K64`, `PY-1_K52`, `PY-2_K64`, `PY-3_K64`, `C-1_K56`, `C-2_K64`, `C-3_K64`), forced singletons alone fell at or below `K` and failed to settle impossibility; mandatory-block rank and disjoint-position witnesses settled all 8. Only `JS-3_K64` (`|F_1| = 73 > 64`) was settled by forced singletons alone.
- **64-slot encoding decisions settled (`9/9` corpora at `K = 64`):**
  - **Plain 6-bit (`K = 64`) `FEASIBLE` (byte-exact, zero escapes):** `JS-1` (`59`), `PY-1` (`61`), `C-1` (`64`, knife-edge).
  - **Plain 6-bit (`K = 64`) `IMPOSSIBLE` (switch to 6-bit + escape or 7-bit):** `C-2` (`|\Sigma| = 67`, `LB = 65 > 64` despite `|F_1| = 37`), `JS-2` (`75`), `PY-2` (`76`), `C-3` (`85`), `PY-3` (`86`), `JS-3` (`90`).
- **Threshold-monotonicity saturation:** `7/9` corpora (`JS-1..3`, `PY-1..3`, `C-3`) hit `LB == |\Sigma|` at `W2`, certifying exact `OPT_W(k) == |\Sigma|` for every $k \ge 2$ from one certificate. Two compact C header corpora (`C-1`: `LB = 61 / 64`; `C-2`: `LB = 65 / 67`) did **not** saturate at `|\Sigma|` (meaning budgets `K in {61..63}` on `C-1` or `K in {65..66}` on `C-2` remain genuinely non-saturated / unresolved without a solver).

## Full 27-Query Comparison Against Baselines

| Query | Lang | K | `|\Sigma|` | `|F_1|` | Block Rank | Disjoint | Diag LB | Status | Pred | Sat `>= Wk` | ms | Peak KiB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | :---: | ---: | ---: |
| `JS-1_K48` | JS | 48 | 59 | 43 | 59 | 59 | **59** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 1,114.7 | 33,522 |
| `JS-1_K64` | JS | 64 | 59 | 43 | 59 | 59 | 59 | `FEASIBLE` | `FEASIBLE` | `W2` | 1,194.6 | 33,522 |
| `JS-1_K72` | JS | 72 | 59 | 43 | 59 | 59 | 59 | `FEASIBLE` | `FEASIBLE` | `W2` | 1,201.1 | 33,522 |
| `JS-2_K64` | JS | 64 | 75 | 49 | 75 | 75 | **75** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 2,085.2 | 24,029 |
| `JS-2_K76` | JS | 76 | 75 | 49 | 75 | 75 | 75 | `FEASIBLE` | `FEASIBLE` | `W2` | 2,195.7 | 24,029 |
| `JS-2_K96` | JS | 96 | 75 | 49 | 75 | 75 | 75 | `FEASIBLE` | `FEASIBLE` | `W2` | 2,184.0 | 24,029 |
| `JS-3_K64` | JS | 64 | 90 | 73 | 90 | 90 | 90 | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 5,025.8 | 61,924 |
| `JS-3_K92` | JS | 92 | 90 | 73 | 90 | 90 | 90 | `FEASIBLE` | `FEASIBLE` | `W2` | 5,404.7 | 61,924 |
| `JS-3_K128` | JS | 128 | 90 | 73 | 90 | 90 | 90 | `FEASIBLE` | `FEASIBLE` | `W2` | 5,403.2 | 61,924 |
| `PY-1_K52` | Py | 52 | 61 | 32 | 61 | 61 | **61** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 22,434.7 | 712,131 |
| `PY-1_K64` | Py | 64 | 61 | 32 | 61 | 61 | 61 | `FEASIBLE` | `FEASIBLE` | `W2` | 23,019.1 | 712,131 |
| `PY-1_K72` | Py | 72 | 61 | 32 | 61 | 61 | 61 | `FEASIBLE` | `FEASIBLE` | `W2` | 23,935.1 | 712,131 |
| `PY-2_K64` | Py | 64 | 76 | 58 | 76 | 76 | **76** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 5,756.8 | 46,793 |
| `PY-2_K78` | Py | 78 | 76 | 58 | 76 | 76 | 76 | `FEASIBLE` | `FEASIBLE` | `W2` | 6,095.2 | 46,793 |
| `PY-2_K96` | Py | 96 | 76 | 58 | 76 | 76 | 76 | `FEASIBLE` | `FEASIBLE` | `W2` | 5,707.8 | 46,793 |
| `PY-3_K64` | Py | 64 | 86 | 53 | 86 | 86 | **86** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 125,171.4 | 1,452,500 |
| `PY-3_K88` | Py | 88 | 86 | 53 | 86 | 86 | 86 | `FEASIBLE` | `FEASIBLE` | `W2` | 122,154.2 | 1,452,500 |
| `PY-3_K128` | Py | 128 | 86 | 53 | 86 | 86 | 86 | `FEASIBLE` | `FEASIBLE` | `W2` | 121,314.9 | 1,452,500 |
| `C-1_K56` | C | 56 | 64 | 38 | **61** | 60 | **61** | `IMPOSSIBLE` | `IMPOSSIBLE` | — | 1,259.1 | 27,347 |
| `C-1_K64` | C | 64 | 64 | 38 | 61 | 60 | 61 | `FEASIBLE` | `FEASIBLE` | — | 1,385.4 | 27,347 |
| `C-1_K72` | C | 72 | 64 | 38 | 61 | 60 | 61 | `FEASIBLE` | `FEASIBLE` | — | 1,371.7 | 27,347 |
| `C-2_K64` | C | 64 | 67 | 37 | **65** | **65** | **65** | `IMPOSSIBLE` | `IMPOSSIBLE` | — | 1,919.1 | 44,732 |
| `C-2_K68` | C | 68 | 67 | 37 | 65 | 65 | 65 | `FEASIBLE` | `FEASIBLE` | — | 2,129.1 | 44,732 |
| `C-2_K80` | C | 80 | 67 | 37 | 65 | 65 | 65 | `FEASIBLE` | `FEASIBLE` | — | 2,128.2 | 44,732 |
| `C-3_K64` | C | 64 | 85 | 46 | 85 | 85 | **85** | `IMPOSSIBLE` | `IMPOSSIBLE` | `W2` | 27,550.7 | 450,528 |
| `C-3_K88` | C | 88 | 85 | 46 | 85 | 85 | 85 | `FEASIBLE` | `FEASIBLE` | `W2` | 28,521.4 | 450,528 |
| `C-3_K128` | C | 128 | 85 | 46 | 85 | 85 | 85 | `FEASIBLE` | `FEASIBLE` | `W2` | 28,429.7 | 450,528 |

## Honest Caveats & Limits Observed

1. **Component decomposition had `Comp = 1` on all 9 real projects:** real multi-file codebases share ASCII keywords and whitespace, so component-wise splitting was not triggered here; the lift over `|F_1|` came from `mandatory_block_rank` and `disjoint_position` (with `mandatory_block_rank` strictly beating `disjoint_position` on `C-1`: `61` vs. `60`).
2. **Non-saturated C headers:** `C-1` (`LB = 61 < 64`) and `C-2` (`LB = 65 < 67`) leave narrow non-saturated bands (`[61..63]` and `[65..66]`) where budgets inside the gap would return `UNRESOLVED`. Notably, `C-2` at `K = 64` still settles `IMPOSSIBLE` (`65 > 64`), ruling out plain 6-bit on the tightest borderline case (`|\Sigma| = 67`, `|F_1| = 37`) without a solver.
3. **Runtime & memory scaling:** Materializing all shared substrings up to 160 bytes in Python caused `PY-3` (`27.1 KB` with repeated docstrings) to take `125 s` and `1.45 GiB` peak traced memory (and `PY-1` `22.4 s` / `712 MiB`), whereas `JS-1`, `JS-2`, `C-1`, and `C-2` completed in `1.1–2.1 s` and `24–45 MiB`. Optimizing memory/runtime on docstring-heavy inputs remains engineering work before claiming fast general scaling.
