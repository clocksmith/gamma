# Pre-Registration: Witness-Rule `K x L` Capacity Sweep (`witness-length-sweep-v1`)

**Status:** Frozen before execution. Do not modify this file, `run_length_sweep.py`, or `check_length_sweep.py` after recording `SHA256SUMS-FROZEN`.

## 1. Research Question

How does exact program-spelling capacity on the frozen `matched80` compact cohort (`N = 80` JavaScript programs, alphabet `|Sigma| = 92` with original trailing newlines, pinned at Gamma commit `59ff04415ff2afd04ff2ed451340f4f02852bf18`) trade off across **vocabulary budget `K in 0..92`** and **maximum entry length `L in {1, 2, 4, 8, 16, 32, 160}`** under the length-capped witness rule `W(L)`?

## 2. Rule `W(L)` and Evaluated Arms

An entry `w` (non-empty byte string) is `W(L)`-legal iff:
1. `1 <= len(w) <= L`;
2. `w` is not a whole program in the cohort;
3. either `len(w) == 1` (single character) or `w` occurs as a substring in at least `2` of the 80 programs.

Because `W(1) <= W(2) <= W(4) <= W(8) <= W(16) <= W(32) <= W(160) <= U`, true capacity `C_{W(L)}(K)` is monotonically non-decreasing in both `K` and `L`.

For every `(K, L)` across `7 x 93 = 651` grid cells, `run_length_sweep.py` computes and stores:
1. **Deterministic frequency-picked baselines** (every dictionary checked for `W(L)`-legality and replayed byte-for-byte):
   - `freqOcc`: top-`K` `W(L)`-legal entries ranked by `(corpus_occurrences DESC, doc_freq DESC, len ASC, bytes ASC)`.
   - `freqDoc`: top-`K` `W(L)`-legal entries ranked by `(doc_freq DESC, corpus_occurrences DESC, len DESC, bytes ASC)` (boilerplate-first tie-break).
   - `charFreqDoc`: top-`K` single characters ranked by `(doc_freq DESC, corpus_occurrences DESC, bytes ASC)` (independent of `L`).
2. **Exact single-character optimum** (`singleCharOpt`, `L = 1` exact optimum from HiGHS MILP, replayed byte-for-byte; solver optimality is recorded separately from solver-free proofs).
3. **Best verified `W(L)` lower end** (`lower`): best replayed `W(L)`-legal dictionary across:
   - exact single-character optimal sets;
   - multi-start greedy shortest-path DP capped at `L` (8 deterministic configurations: single-char preference, multi-char preference, length-bonus multi-char preference, and 5 seeded tie-breakers);
   - rare-character cluster compression capped at `L` applied to single-character optimal subsets and `+1`/`+2` augmented subsets across all `K`;
   - nested inheritance from smaller `L' < L` (re-verified for `W(L)`-legality and replayed).
4. **100% solver-free proven upper end** (`upper`): minimum of independently checkable ceilings verified without any solver in two prime fields (`(1000000007, 2)` and `(998244353, 3)`):
   - trivial `K in {0, 1} -> 0`;
   - exact unrestricted ceiling `C_U(K)` (proved solver-free in `witness-coverage-v1/check_unrestricted.py`: `0` at `K=0`, `K-1` for `1..60`, `K` for `61..67`, `K+1` for `68..79`, `80` for `>= 80`);
   - per-program forced-block rank filter (`prank_L[p] <= K`) and per-program `L`-capped character capacity filter (`|U_1,L(p)| + ceil(|chars(p) \ U_1,L(p)| / L) <= K`), where `U_1,L(p)` is the set of characters appearing as length-1 forced blocks under `W(L)` (all characters of `p` when `L = 1`; forced-cut isolated singletons when `L >= 2`);
   - exact integer-certified LP dual of the `F_span` forced-unit-vector relaxation under `W(L)`;
   - exact integer-certified LP dual of the `L`-capped character-capacity relaxation (`z_p <= x_c` for `c in U_1,L(p)`, `z_p <= x_c + y_c` for `c in chars(p) \ U_1,L(p)`, `L * sum x_c + sum y_c <= L * K`);
   - exact tail subset forced-block ranks `r_80(L)`, `r_79(L)`, and `r_78(L)` (minimum block rank over all `1`, `80`, and `3,160` subsets of sizes `80`, `79`, and `78`), plus backward monotonicity in `K` and cross-`L` monotonicity (`upper(K, L) <= upper(K, L')` for `L < L'`).

## 3. Falsifiable Predictions (L1 to L5)

| Id | Prediction | Pass Criterion |
| --- | --- | --- |
| **L1** | **Length threshold for first-program compression.** Let `K_first(L)` be the smallest `K` with `lower(K, L) >= 1` (`K_first(1) = 24`). | `K_first(L)` is non-increasing in `L`, `K_first(8) <= 14`, `K_first(32) > 6`, and `K_first(160) <= 6`. |
| **L2** | **Length threshold for upper-tail `79/80` compression at `K = 82`.** Single characters need 85 slots for 79 programs; `X_SAFE_INTEG` (12 bytes) saves 3 slots once `L >= 12`. | `lower(82, L) == 79` for `L in {16, 32, 160}` AND `lower(82, L) <= 78` for `L in {1, 2, 4, 8}`. |
| **L3** | **Diminishing returns past `L = 16`.** Define `mean_lower(L) = mean_{K=0..92} lower(K, L)`. | `(mean_lower(16) - mean_lower(1)) / (mean_lower(160) - mean_lower(1)) >= 0.75` AND `(mean_lower(2) - mean_lower(1)) / (mean_lower(160) - mean_lower(1)) < 0.30`. |
| **L4** | **Frequency-picked baselines lose sharply at `K = 64`.** At `K = 64` (exact optimum `64` for all `L`), frequency-ranked multi-character entries waste slots needed for rare required characters. | For every `L >= 2`, `freqOcc(64, L) <= 31` AND `freqDoc(64, L) <= 31`; and `charFreqDoc(64) <= 59`. |
| **L5** | **Solver-free `L`-capped LP dual tightens low-`K` ceilings for small `L`.** | For each `L in {1, 2, 4}`, `upper(K, L) < C_U(K)` on `>= 15` budgets in `2..57`, median interval width at `L = 2` drops by `>= 30%` vs `C_U(K)` alone, and `check_length_sweep.py` verifies all `651` cells solver-free with `primesAgree == True`. |

## 4. Verification Protocol

1. Freeze `PREREGISTRATION.md`, `run_length_sweep.py`, and `check_length_sweep.py` and record SHA-256 hashes in `SHA256SUMS-FROZEN`.
2. Execute `python3 -B run_length_sweep.py /path/to/gamma`.
3. Independently verify every dictionary, baseline, algebraic rank (two prime fields), and integer LP dual certificate with `python3 -B check_length_sweep.py /path/to/gamma` (zero solver imports).
4. Record outcomes of L1–L5 verbatim (passes and failures alike) in `RESULTS.md`, export `length-sweep.csv`, and record result checksums in `SHA256SUMS-RESULTS`.
