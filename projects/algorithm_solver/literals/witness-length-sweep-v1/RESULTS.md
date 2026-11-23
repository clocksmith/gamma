# Results: `K x L` Capacity Sweep and Unseen-Program Transfer (`witness-length-sweep-v1`)

Two pre-registered experiments were frozen before execution (`SHA256SUMS-FROZEN` and `SHA256SUMS-TRANSFER-FROZEN`, unchanged) and verified 100% solver-free. *Provenance note:* the prediction files, freeze checksums, and run outputs entered git together in a single commit (`d36e52f27`), so git history alone does not independently timestamp the pre-registration prior to execution; the on-disk checksums verify internal artifact consistency rather than an external pre-run timestamp.
1. **In-sample `K x L` sweep on frozen `matched80` compact** (`N = 80`, `|Sigma| = 92`, Gamma commit `59ff04415ff2afd04ff2ed451340f4f02852bf18`, `run_length_sweep.py` in `37.82 s`, verified solver-free by `check_length_sweep.py`: `7 lengths, 651 cells (247 exact), 345 dictionaries replayed, 39 integer LP duals checked`, `primesAgree = True` across primes `1,000,000,007` base `2` and `998,244,353` base `3`).
2. **Unseen-program `K x L` transfer test on frozen disjoint `-a -> -b` pairs** (`J-80`, `P-80`, `J-160`, `P-160` from `../witness-scaling-v1/cohorts.json`, `run_unseen_transfer.py` in `794.36 s`, verified solver-free by `check_unseen_transfer.py`: `4 pairs, 2,681 cells, 1,750 frozen dictionaries replayed`).

---

## Part 1: In-Sample `matched80` `K x L` Sweep (3 of 5 Predictions Passed, 2 Failed)

| Id | Pre-registered prediction | Measured result | Outcome |
| --- | --- | --- | --- |
| **L1** | `K_first(L)` non-increasing, `K_first(8) <= 14`, `K_first(32) > 6`, `K_first(160) <= 6` | `K_first = [24, 23, 16, 10, 7, 6, 6]` (`L=32` already reaches `6` via a 25-byte max parse of `#136`) | **FAIL** |
| **L2** | `lower(82, L) == 79` for `L in {16, 32, 160}` and `<= 78` for `L in {1, 2, 4, 8}` | `[78, 78, 78, 78, 79, 79, 79]` (exact `L >= 12` threshold for `X_SAFE_INTEG`) | **PASS** |
| **L3** | `L=16` captures `>= 75%` of `L=1 -> L=160` mean lower gain; `L=2` captures `< 30%` | `L=2`: `1.6%` (`0.0156`), `L=16`: `82.8%` (`0.8281`), `L=32`: `100.0%` (`1.0000`) | **PASS** |
| **L4** | At `K=64`, `freqOcc <= 31` & `freqDoc <= 31` for all `L >= 2`; `charFreqDoc <= 59` | `charFreqDoc(64) = 58`; for all `L >= 2`, `freqOcc(64) = 0` and `freqDoc(64) <= 1` (`1` at `L=2`, `0` for `L >= 4`) | **PASS** |
| **L5** | For `L in {1, 2, 4}`, `upper < C_U` on `>= 15` budgets in `2..57`, `L=2` medW drop `>= 30%`, solver-free pass | `beatsCU_mid`: `L=1: 45`, `L=2: 17`, `L=4: 7` (`< 15` at `L=4`); `L=2` medW drops `60.0%` (`5.0 -> 2.0`); all 651 cells pass solver-free | **FAIL** |

### Why L1 and L5 failed
- **L1 (`K_first(32) == 6` instead of `> 6`):** We assumed spelling `#136` in 6 entries required the 36-byte header entry from `witness-coverage-v1`. Multi-start DP at `L = 32` instead split the header into two `<= 25`-byte shared fragments (`function solve(a){let b=0` and `;for(const c of a){`) plus `b`, `^`, `=c`, `;}return b;}\n`, spelling `#136` in 6 slots with max entry length 25 bytes.
- **L5 (`L = 4` beat `C_U(K)` on only `7` budgets in `2..57`):** Once an entry can carry up to 4 distinct characters, the `L`-capped character-capacity LP dual (`L * sum x_c + sum y_c <= L * K`) crosses above `C_U(K) = K - 1` by `K = 9`. By contrast, at `L = 1` it beats `C_U` on `45` budgets (60/93 exact solver-free; median width `0.0`) and at `L = 2` it beats `C_U` on `17` budgets (cutting median width by `60%`, from `5.0` to `2.0`).

### Summary across `max_len L` (`matched80` compact, `N = 80`, `|Sigma| = 92`)

All `lower` entries are replayed `W(L)`-legal dictionaries; all `upper` entries are 100% solver-free proven ceilings verified in two prime fields (`primesAgree = True` everywhere).

| `L` | Legal `W(L)` entries | Exact `/93` | `K_first` | `mean(lower)` | `med(width)` | `K=16 [lo, hi]` | `K=32 [lo, hi]` | `K=64 [lo, hi]` (`freqOcc`, `freqDoc`) | `K=82 [lo, hi]` |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `1` | `92` | `60` | `24` | `34.23` | `0.0` | `[0, 0]` | `[4, 6]` | `[64, 64]` (`57`, `58`) | `[78, 78]` |
| `2` | `802` | `34` | `23` | `34.24` | `2.0` | `[0, 6]` | `[4, 31]` | `[64, 64]` (`0`, `1`) | `[78, 79]` |
| `4` | `3,986` | `29` | `16` | `34.41` | `4.0` | `[1, 15]` | `[4, 31]` | `[64, 64]` (`0`, `0`) | `[78, 79]` |
| `8` | `10,941` | `28` | `10` | `34.60` | `5.0` | `[1, 15]` | `[4, 31]` | `[64, 64]` (`0`, `0`) | `[78, 79]` |
| `16` | `21,642` | `32` | `7` | `34.80` | `5.0` | `[2, 15]` | `[4, 31]` | `[64, 64]` (`0`, `0`) | `[79, 79]` |
| `32` | `30,711` | `32` | `6` | `34.91` | `5.0` | `[2, 15]` | `[4, 31]` | `[64, 64]` (`0`, `0`) | `[79, 79]` |
| `160` | `33,802` | `32` | `6` | `34.91` | `5.0` | `[2, 15]` | `[4, 31]` | `[64, 64]` (`0`, `0`) | `[79, 79]` |

Key in-sample findings:
- **Zero lift in the exact single-character plateau (`K = 58..71`):** For every `L in 1..160`, single characters alone already reach the exact unrestricted ceiling `C_U(K)` (including `64/80` at `K = 64`), so multi-character entries add `0` programs there.
- **Frequency-picked `W(L)` substrings collapse as soon as `L >= 2`:** Because overlapping substrings of shared boilerplate dominate raw frequency counts, top-64 `freqOcc` and `freqDoc` dictionaries starve rare required characters and spell `0` to `1` program at `K = 64` (vs. `58` for `charFreqDoc` and `64` for optimal single characters).
- **Diminishing returns past `L = 16`:** `L = 16` already captures `82.8%` of the total in-sample lower-bound gain from `L = 1` to `L = 160`, and `L = 32` captures `100.0%`.

---

## Part 2: Unseen-Program Transfer (`-a` Frozen -> Unseen `-b`)

**Headline finding: ZERO repeatable unseen-program advantage from multi-character `W(L)` fragments over single-character selection.**

| Id | Pre-registered criterion | Measured result | Outcome |
| --- | --- | --- | --- |
| **T1** | At `L=160`, `jointBest` vs `charOpt` on unseen `-b`: peak lift `<= 2` (`>= 3/4`), `K=64` lift `<= 0` (`>= 3/4`), `|meanDiff| < 1.0` (`4/4`) | Peak multi-char unseen lift is **`0` on `4/4` pairs** (the only `+2` blip on `J-80` at `K=52` uses single characters only, `0` multi-char fragments); `K=64` lift `0` on `4/4`; `meanDiff` in `[-0.08, -0.03]` on `4/4` | **PASS** |
| **T2** | At `L=160`, `mean(greedyDP_test) < mean(charOpt_test)` (`4/4`) and `dictBytes(greedyDP, K=64) > 64` (`4/4`) | `mean(greedyDP_test) == 0.00` on all `4/4` pairs (vs `14.66..36.12` for `charOpt`); `dictBytes` at `K=64` is `294..1,953 B` (`4.6x..30.5x` larger than `64 B`) | **PASS** |
| **T3** | At `K=64`, `freqOcc_test <= 1` & `freqDoc_test <= 1` for all `L >= 4` (`4/4`); `charFreqDoc >= 0.80 * charOpt` (`>= 3/4`); solver-free pass | `freqOcc_test = 0` and `freqDoc_test = 0` on `4/4` for all `L >= 2`; `charFreqDoc / charOpt` is `0.78` (`J-80`), `1.08` (`P-80`), `1.75` (`J-160`), `0.89` (`P-160`) -> `>= 0.80` on `3/4`; `check_unseen_transfer.py` verified 100% solver-free | **PASS** |
| **T4** | **Vocabulary-design promotion bar:** `>= +5 percentage points` unseen `-b` lift above best baseline at matched `K` and matched stored bytes on `>= 2/4` pairs | **`0/4` pairs** (`0.00%` multi-character unseen lift across all `4` pairs, all `6` lengths `L >= 2`, and all budgets `K`) | **FAIL (null/negative transfer)** |

### Summary across all 4 frozen transfer pairs (`L = 160` vs `L = 1`)

| Pair (`-a -> -b`) | Test `N` | `K=64` unseen `-b`: `charOpt` (`64 B`) | `charFreq` (`64 B`) | `freqOcc` / `freqDoc` | `jointBest` (`bytes`) | `greedyDP` (`bytes`) | Multi-char budgets on `-a` (train lift -> unseen `-b` lift) | Multi-char unseen gains (any `L >= 2`, any `K`) |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: |
| `J-80` | `80` | `9` | `7` | `0 / 0` | `9` (`64 B`) | `0` (`1,332 B`) | `40` budgets (`+1..+3` -> **`-3..0`**) | **`0`** |
| `P-80` | `80` | `12` | `13` | `0 / 0` | `12` (`64 B`) | `0` (`294 B`) | `1` budget (`+1` -> **`0`**) | **`0`** |
| `J-160` | `160` | `4` | `7` | `0 / 0` | `4` (`64 B`) | `0` (`1,953 B`) | `47` budgets (`+1..+4` -> **`-2..0`**) | **`0`** |
| `P-160` | `160` | `36` | `32` | `0 / 0` | `36` (`64 B`) | `0` (`808 B`) | `30` budgets (`+1..+3` -> **`-1..0`**) | **`0`** |

### Why multi-character `W(L)` fragments fail to transfer to unseen files

Across `118` budgets where `jointBest` (`L = 160`) strictly beat single characters on training cohort `-a` (gaining `+1` to `+4` training programs), those dictionaries produced **zero** net unseen gains (`-3` to `0`) on the held-out `-b` cohort. Likewise, pure fragment-heavy `greedyDP` dictionaries spelled `3` to `9` training programs while consuming `294` to `1,953` dictionary bytes at `K = 64`, yet spelled **`0` unseen `-b` programs** across every budget `K in 0..|Sigma_a|`, every length `L >= 2`, and all four pairs.

The mechanism is direct: exact byte-for-byte spelling is conjunctive across an entire file. Replacing rare single characters with multi-character fragments learned from `-a` saves slots only for files whose occurrences of those rare characters appear inside those exact fragments; on an unseen 450–800-byte file, even one occurrence of a dropped character in a different context breaks spelling completely. Because T4 failed (`0/4` pairs, `0.00%` multi-character unseen lift), the evidence supports framing this work as **certified capacity bounds and algebraic proof boundaries**, not as a vocabulary-design advantage for unseen code.
