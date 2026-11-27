# BITS Experiment Card A1b — Horizon-Dependent Vocabulary Sizing (Development Report)

Status: **CPU development complete; all 6 `dev_gate` checks PASS; NOT freeze-ready until sealed calibration lineage support reaches >= 9 independent organizations (recommended 16-20).**

All code, verified archive grids, and diagnostics live inside `a1b-horizon-sizing-v1/`. No frozen experiment folder was modified, no sealed corpus was opened, no network access occurred, and no GPU compute was used.

## 1. Executive Summary & Pass-Target Audit

On the 14 repository-disjoint development queries (7 non-CodeNet spent codebases across 6 distinct organizations x 2 primary decimal horizons $M \in \{100\,000\text{ B}, 100\,000\,000\text{ B}\}$), evaluated under strict organization-disjoint leave-one-lineage-out cross-validation (LOLO-CV) with real serialized and independently decoded `B1RA` archives:

| Proposed A1b Target | `shipped_policy_dev_calibrated` | `shipped_policy_strict_conformal` | Target | Verdict |
| --- | ---: | ---: | --- | --- |
| Median excess vs full 7-chain oracle | **0.68%** | 0.98% | <= 1.0% | PASS (both) |
| p95 excess vs full 7-chain oracle | **1.56%** | 2.06% | <= 2.5% | PASS (both) |
| Max excess vs full 7-chain oracle | **2.34%** | 2.34% | (diagnostic) | < 2.5% on 14/14 |
| Fallback (`SWEEP_REQUIRED`) rate | **0.0%** | 100.0% | <= 15.0% | PASS (dev) / FAIL (strict: `n_cal_orgs=5 < 9`) |
| Total ops ratio vs 3-pt pilot | **0.282x** | 1.012x | <= 0.500x | PASS (dev) / FAIL (strict) |
| Total ops ratio vs 10-pt grid | **0.110x** | 0.393x | <= 0.167x | PASS (dev) / FAIL (strict) |
| Total wall ratio vs 3-pt pilot | **0.285x** | 1.006x | <= 0.500x | PASS (dev) / FAIL (strict) |
| Total wall ratio vs 10-pt grid | **0.112x** | 0.393x | <= 0.167x | PASS (dev) / FAIL (strict) |
| Conformal 90% UPB support ($n_{\text{cal\_orgs}} \ge 9$) | **6 orgs total (5/fold)** | **6 orgs total (5/fold)** | >= 9 orgs | **INSUFFICIENT FOR FREEZE** |

**Key scientific findings:**
1. **Fixed-$K$ vocabularies fail badly across horizons.** Every fixed prefix fails one of the two primary horizons: `fixed_K512` incurs up to **+13.61%** excess at 100 MB (p95 **+8.84%**), `fixed_K2048` incurs up to **+20.41%** at 100 KB (p95 **+20.15%**), and `fixed_K4096` incurs up to **+52.87%** at 100 KB (p95 **+52.69%**) while STILL losing at 100 MB on every single out-of-distribution repository due to codeword widening.
2. **Codeword widening creates a real non-monotonic interior optimum at $K = 2048$ on out-of-domain repositories.** On all 7 non-CodeNet repositories, extending `exact_closed` from $K = 2048$ to $K = 4096$ adds mostly unused single-problem fragments (unused entry share rises from 59.2% to 71.9% on Express), widening realized codewords by **+0.94 to +1.09 bits/token** and *raising* coded body rate $\hat{r}_K$ by **+0.49% to +2.79%**. Consequently, the break-even horizon $M^*(K=2048 \to K=4096)$ is **never reached (`null`)** on any of the 7 out-of-domain repositories, whereas on in-distribution CodeNet (`codenet_fresh`, `codenet_fresh2`) $K = 4096$ wins past $M^* \approx 1.07\text{--}1.21\text{ MB}$.
3. **A cheap 4-point centered strided micro-sketch (<= 3.5% bytes, capped at 12 KiB) beats every fixed-$K$ arm and runs at 0.28x pilot / 0.11x grid total work.** In strict org-disjoint LOLO-CV (`shipped_policy_dev_calibrated`), it achieves **0.00% median / 0.78% p95** excess against the same-chain oracle (picking the exact same-chain optimum on 7/7 repos at 100 MB) and **0.68% median / 1.56% p95** against the full 7-chain selector-by-$K$ oracle, while preserving **92.86% (13/14)** empirical coverage of its same-chain 90% UPB.
4. **Local spent repository count is provably insufficient for finite distribution-free 90% conformal calibration before freeze.** The worktree contains only **7** non-CodeNet spent codebases across **6** distinct organizations (`TheAlgorithms`, `clocksmith`, `expressjs`, `lodash`, `python`, `ramda`; **5** strictly third-party orgs), yielding `n_cal_orgs = 5` per LOLO fold and `6` at final refit. Finite distribution-free 90% conformal prediction requires $\lceil 0.90(n+1) \rceil \le n \iff n \ge 9$ independent organizations. `shipped_policy_strict_conformal` honestly emits `SWEEP_REQUIRED` on 100% of local dev queries (`insufficient_lineage_support`) and falls back safely to the frozen 3-point geometric pilot (`median 0.98%, p95 2.06%`). At least **3-4 more** independent repositories are required to cross the mathematical minimum of 9, and **10-14 more** (16-20 total sealed independent organizations) are recommended before freezing A1b.

---

## 2. Shared Spine Contract (`shared_spine`)

All four `shared_spine` fields are recorded in [dev_summary.json](dev_summary.json):

- **`fidelity`:** `1.0` across **630 / 630** serialized `B1RA` archives (9 lineages x 7 verified chains x 10 prefixes), every single archive independently decoded byte-for-byte via `independent_decode.py` (written from `FORMAT.md` alone, zero shared encoder imports), **0 B accounting drift** (`header_bytes + framing_bytes + payload_bytes == len(archive)`), and 100% random-access single-record decode spot checks passing.
- **`complete_bits`:** Exact $8 \times (H_K + M \hat{r}_K)$ reported per arm and per horizon:
  - At $M = 100\,000\text{ B}$ (mean across 7 `dev_disjoint` lineages): `shipped_policy_dev_calibrated` = **472,896.47 bits** vs `same_chain_oracle` = **470,817.16 bits**, `full_selector_by_K_oracle` = **468,150.43 bits**, `fixed_K512` = **474,320.40 bits**, `fixed_K2048` = **547,842.67 bits**, `fixed_K4096` = **689,154.49 bits**.
  - At $M = 100\,000\,000\text{ B}$: `shipped_policy_dev_calibrated` = **423,918,721.94 bits** (exact match with `same_chain_oracle` = **423,918,721.94 bits**!) vs `full_selector_by_K_oracle` = **422,017,837.53 bits**, `fixed_K512` = **444,046,704.49 bits**, `fixed_K4096` = **430,813,086.81 bits**.
- **`measured_work`:** Exact wall-clock seconds, p95 per-query latency, peak RSS bytes, and measured op counts (`edge_scans + edge_matches + dp_relaxations + bit_writes`), including fold-specific calibration and final refit wall time, with identical prefix reuse across all arms (Section 4).
- **`horizon` ($M^*$):** Primary horizons $M \in \{100\,000, 100\,000\,000\}\text{ B}$, diagnostic sweep $M \in [10^4, 10^9]\text{ B}$, and exact analytical break-even horizons $M^*$ per lineage (Section 6).

---

## 3. Verified Chains, Lineages & Leakage Separation

### 3.1 Verified Selector Chains (All Fitted Strictly on `codenet_primary`)
All 7 chains were loaded directly from SHA-256-verified artifacts in `closure-holdout-v1/` (400 files, 259,706 B, 171-byte base alphabet, `L = 16`, policy `s1-whole`):
- **`exact_closed`** (PRIMARY shipping chain): `closure-holdout-v1/out/bundle/pair-ext.txt` (prefixes 0..4096 byte-identical to brute-force-verified `exact-closed-s1-whole.txt`), full grid $K \in \{0, 32, 64, 128, 256, 512, 1024, 2048, 3072, 4096\}$.
- **`exact_byte`**: `open-byte-ext.txt` (all 10 grid points).
- **`bundle_byte`**: `bundle-byte.txt` (all 10 grid points).
- **`bundle_slot`**: `bundle-slot.txt` (all 10 grid points).
- **`bpe`**: `closure-holdout-v1/frozen/dictionaries.json` (`bpe-K4096`, grid up to 3072 + verified cap max 3924).
- **`exact_open`**: `exact-entry-s1-whole.txt` (grid up to 3072 + verified cap max 3924).
- **`exact_norm_p2`**: `exact-norm-p2-nowhole.txt` (2-problem support, grid up to 3072 + verified cap max 3924).

### 3.2 Repository-Disjoint Spent Lineage Registry
Zero file hashes overlap across any pair of lineages (verified programmatically).

| Lineage ID | Org ID | Role | Language | Files | Source Bytes | Mean File B |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `codenet_primary` | `ibm_codenet` | `fit` (LOCKED OUT of cal/eval) | Python + JS | 400 | 259,706 | 649.3 |
| `expressjs_express` | `expressjs` | `dev_disjoint` (3rd-party) | JS | 120 | 176,742 | 1,472.8 |
| `ramda_ramda` | `ramda` | `dev_disjoint` (3rd-party) | JS | 200 | 203,300 | 1,016.5 |
| `TheAlgorithms_Python` | `TheAlgorithms` | `dev_disjoint` (3rd-party) | Python | 200 | 382,385 | 1,911.9 |
| `lodash_lodash` | `lodash` | `dev_disjoint` (3rd-party) | JS | 560 | 474,605 | 847.5 |
| `python_cpython` | `python` | `dev_disjoint` (3rd-party) | Python | 720 | 392,507 | 545.1 |
| `authored_catalogue_dev` | `clocksmith` | `dev_disjoint` (same org as gamma) | Python + JS | 400 | 299,069 | 747.7 |
| `clocksmith_gamma_core` | `clocksmith` | `dev_disjoint` (same org as cat) | Python | 194 | 1,917,069 | 9,881.8 |
| `codenet_fresh` | `ibm_codenet` | `in_dist_codenet_diag` (NEVER in cal) | Python + JS | 400 | 255,472 | 638.7 |
| `codenet_fresh2` | `ibm_codenet` | `in_dist_codenet_diag` (NEVER in cal) | Python + JS | 400 | 243,510 | 608.8 |

Note on `clocksmith` org-level disjointness: both `authored_catalogue_dev` and `clocksmith_gamma_core` carry `org_id = "clocksmith"`. When either is held out in LOLO-CV, BOTH are excluded from calibration so every fold uses strictly **5 independent organizations** (`n_cal_orgs = 5`). File-level resampling inside any repository is forbidden and actively rejected by `assert_disjoint_lineages()`.

---

## 4. Complete Arm Comparison & Exact Work Accounting (14 `dev_disjoint` Queries)

All work figures include identical prefix reuse (if pilot or grid already encoded the chosen prefix, deployment encode adds 0 extra ops/time) plus exact fold-specific calibration build and final shipping refit time (`shipped_policy` arms).

| Arm | vs Same-Chain Oracle (med / p95 / max) | vs Full 7-Chain Oracle (med / p95 / max) | 3rd-Party 5-Org Only vs Full (med / p95) | Fallback Rate | Total Wall s (p95 lat s) | Total Ops | Peak RSS | Ops vs Pilot | Ops vs Grid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `shipped_policy_dev_calibrated` | **0.00% / 0.78% / 1.14%** | **0.68% / 1.56% / 2.34%** | **0.55% / 1.08%** | 0.0% (0/14) | 28.17 (6.87) | 78,901,754 | 186 MiB | **0.282x** | **0.110x** |
| `shipped_policy_strict_conformal` | 0.42% / 1.34% / 1.51% | 0.98% / 2.06% / 2.34% | 0.83% / 1.79% | 100.0% (14/14) | 99.32 (27.89) | 282,710,640 | 186 MiB | 1.012x | 0.393x |
| `fixed_K512` | 1.21% / 8.18% / 12.59% | 2.17% / 8.84% / 13.61% | 2.65% / 5.91% | 0.0% | 24.70 (6.61) | 68,182,916 | 90 MiB | 0.244x | 0.095x |
| `fixed_K2048` | 5.54% / 19.46% / 19.98% | 7.17% / 20.15% / 20.41% | 7.35% / 19.44% | 0.0% | 33.09 (9.01) | 87,912,034 | 91 MiB | 0.315x | 0.122x |
| `fixed_K4096` | 22.17% / 51.81% / 52.32% | 22.44% / 52.69% / 52.87% | 22.44% / 50.89% | 0.0% | 35.93 (10.02) | 98,883,924 | 95 MiB | 0.354x | 0.138x |
| `pilot_3pt_geometric` | 0.42% / 1.34% / 1.51% | 0.98% / 2.06% / 2.34% | 0.83% / 1.79% | 0.0% | 98.76 (27.84) | 279,460,556 | 95 MiB | 1.000x | 0.389x |
| `same_chain_oracle` (10-pt grid) | 0.00% / 0.00% / 0.00% | 0.39% / 1.33% / 2.12% | 0.32% / 0.68% | 0.0% | 252.61 (68.81) | 719,052,072 | 95 MiB | 2.573x | 1.000x |
| `full_selector_by_K_oracle` (7 chains) | -0.38% / -0.09% / 0.00% | 0.00% / 0.00% / 0.00% | 0.00% / 0.00% | 0.0% | 1,649.21 (485.65) | 4,985,799,168 | 98 MiB | 17.841x | 6.934x |

### Worst Misses vs Full 7-Chain Oracle
- **`shipped_policy_dev_calibrated`:**
  1. `authored_catalogue_dev` @ 100 KB: picked `K=512` vs full oracle `exact_open:K512` (**+2.34%**, of which **+2.12%** is the irreducible cross-chain gap and only **+0.22%** is same-chain sizing error).
  2. `ramda_ramda` @ 100 KB: picked `K=512` vs `exact_closed:K256` (**+1.14%**).
  3. `python_cpython` @ 100 KB: picked `K=256` vs `bundle_slot:K128` (**+1.00%**, same-chain error **+0.59%**).
- **`fixed_K512`:** `authored_catalogue_dev` @ 100 MB (**+13.61%**), `TheAlgorithms_Python` @ 100 MB (**+6.28%**), `lodash_lodash` @ 100 MB (**+5.45%**).
- **`fixed_K2048`:** `clocksmith_gamma_core` @ 100 KB (**+20.41%**), `expressjs_express` @ 100 KB (**+20.01%**), `python_cpython` @ 100 KB (**+18.75%**).
- **`fixed_K4096`:** `clocksmith_gamma_core` @ 100 KB (**+52.87%**), `expressjs_express` @ 100 KB (**+52.59%**), `python_cpython` @ 100 KB (**+48.81%**).
- **`pilot_3pt_geometric`:** `authored_catalogue_dev` @ 100 KB (**+2.34%**), `python_cpython` @ 100 MB (**+1.91%**, picked `K=4096` instead of `K=2048`), `lodash_lodash` @ 100 MB (**+1.65%**, picked `K=3072`).

### In-Distribution CodeNet Diagnostic (Segregated; Calibrated on Non-CodeNet Only)
Using the final refitted policy calibrated strictly on the 7 non-CodeNet codebases:
- `codenet_fresh` @ 100 KB: picked `K=512` (same-chain oracle `K=1024`, **+0.17%** vs same-chain; **+6.12%** vs `exact_open:K512`, reproducing `closure-holdout-v1`'s known small-budget open-selection advantage on in-distribution CodeNet).
- `codenet_fresh` @ 100 MB: picked **`K=4096`** (**+0.00%** vs same-chain oracle, **+0.58%** vs full 7-chain oracle!).
- `codenet_fresh2` @ 100 KB: picked **`K=512`** (**+0.00%** vs same-chain oracle; **+5.19%** vs `exact_open:K512`).
- `codenet_fresh2` @ 100 MB: picked **`K=4096`** (**+0.00%** vs same-chain oracle, **+0.92%** vs full 7-chain oracle!).

Notice that even though the policy was calibrated *exclusively* on out-of-distribution non-CodeNet repositories where `K=2048` always beat `K=4096`, the 4-point micro-sketch immediately detected that CodeNet's body rate continues dropping from `K=2048` to `K=4096` and correctly switched to **`K=4096`** on both `codenet_fresh` and `codenet_fresh2`!

---

## 5. Header/Body Decomposition & Codeword Widening

### 5.1 Representative Prefix Curve (`expressjs_express`, 120 files, 176,742 B, `exact_closed`)

| Prefix $K$ | Header $H_K$ (dict + table) | Framing B | Payload B | $\hat{r}_K$ | Avg Header Code Len | Realized Bits/Token | Unused Entries (%) | Frozen RAM B |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 521 (342 + 173) | 237 | 112,290 | 0.6367 | 10.84 | 5.08 | 52 / 171 (30.4%) | 1,890 |
| 32 | 669 (458 + 205) | 237 | 103,224 | 0.5854 | 10.11 | 6.23 | 53 / 203 (26.1%) | 2,710 |
| 64 | 833 (590 + 237) | 237 | 102,668 | 0.5822 | 10.00 | 6.58 | 59 / 235 (25.1%) | 3,546 |
| 128 | 1,196 (889 + 301) | 237 | 97,404 | 0.5524 | 9.94 | 6.92 | 74 / 299 (24.7%) | 5,253 |
| 256 | 1,970 (1,535 + 429) | 236 | 96,298 | 0.5462 | 10.32 | 7.60 | 121 / 427 (28.3%) | 8,715 |
| 512 | 3,788 (3,097 + 685) | 236 | 94,106 | 0.5338 | 10.80 | 8.39 | 254 / 683 (37.2%) | 15,909 |
| 1024 | 7,487 (6,284 + 1,197) | 236 | 93,380 | 0.5297 | 11.32 | 9.31 | 548 / 1,195 (45.9%) | 30,360 |
| **2048** | **15,506 (13,279 + 2,221)** | **236** | **91,241** | **0.5176** | **12.18** | **10.09** | **1,313 / 2,219 (59.2%)** | **59,883** |
| 3072 | 24,314 (21,063 + 3,245) | 236 | 92,653 | 0.5256 | 12.69 | 10.66 | 2,179 / 3,243 (67.2%) | 90,195 |
| 4096 | 32,325 (28,050 + 4,269) | 236 | 93,795 | 0.5320 | 13.10 | 11.17 | 3,069 / 4,267 (71.9%) | 119,710 |

### 5.2 Codeword Widening Across All 9 Lineages ($K = 2048 \to K = 4096$, `exact_closed`)

| Lineage | Role | $\hat{r}_{4096} - \hat{r}_{2048}$ | Rel. Body Change | Realized Bits/Token Delta | Non-Monotone Tail? |
| --- | --- | ---: | ---: | ---: | --- |
| `expressjs_express` | `dev_disjoint` | +0.014450 | **+2.79%** | +1.0762 | YES |
| `ramda_ramda` | `dev_disjoint` | +0.009046 | **+1.61%** | +1.0403 | YES |
| `TheAlgorithms_Python` | `dev_disjoint` | +0.003512 | **+0.65%** | +1.0312 | YES |
| `lodash_lodash` | `dev_disjoint` | +0.011540 | **+1.98%** | +1.0931 | YES |
| `python_cpython` | `dev_disjoint` | +0.006502 | **+1.21%** | +1.0374 | YES |
| `authored_catalogue_dev` | `dev_disjoint` | +0.002250 | **+0.49%** | +0.9367 | YES |
| `clocksmith_gamma_core` | `dev_disjoint` | +0.011848 | **+2.31%** | +1.0396 | YES |
| `codenet_fresh` | `in_dist_diag` | -0.013931 | -4.32% | +0.7944 | no |
| `codenet_fresh2` | `in_dist_diag` | -0.015687 | -4.87% | +0.7677 | no |

**Mechanism:** Adding fragments 2049..4096 (mostly single-problem `codenet_primary` strings) reallocates Huffman probability mass away from frequently used short tokens, widening realized codewords by ~1.0 bit/token on out-of-domain code without paying back enough token reduction. Notably, `exact_norm_p2` (which filters out single-problem fragments via 2-problem support) eliminates this reversal at $K=3924$ on Python repositories, explaining why `exact_norm_p2:K3924` is the full-oracle winner at 100 MB on `TheAlgorithms_Python`, `python_cpython`, `authored_catalogue_dev`, and `clocksmith_gamma_core`.

---

## 6. Lower Envelope Across Horizons, Break-Even $M^*$, and Flat-Minimum Frequency

### 6.1 Optimal Prefix $K^*(M)$ Across Diagnostic Horizon Sweep (`exact_closed`)

| Lineage | $M^*(0{\to}64)$ | $M^*(64{\to}512)$ | $M^*(512{\to}2048)$ | $M^*(2048{\to}4096)$ | 10 KB | 30 KB | **100 KB** | 300 KB | 1 MB | 3 MB | 10 MB | **100 MB** | 1 GB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `expressjs_express` | 5.7 KB | 61.0 KB | 722.9 KB | never | 32 | 128 | **128** | 512 | 2048 | 2048 | 2048 | **2048** | 2048 |
| `ramda_ramda` | 9.7 KB | 50.7 KB | 661.9 KB | never | 32 | 128 | **256** | 1024 | 1024 | 2048 | 2048 | **2048** | 2048 |
| `TheAlgorithms_Python` | 6.8 KB | 114.5 KB | 371.3 KB | never | 32 | 64 | **256** | 512 | 2048 | 2048 | 2048 | **2048** | 2048 |
| `lodash_lodash` | 17.8 KB | 46.3 KB | 377.9 KB | never | 0 | 256 | **256** | 1024 | 2048 | 2048 | 2048 | **2048** | 2048 |
| `python_cpython` | 6.4 KB | 123.8 KB | 689.2 KB | never | 32 | 64 | **128** | 512 | 1024 | 2048 | 2048 | **2048** | 2048 |
| `authored_catalogue_dev` | 6.1 KB | 39.9 KB | 203.9 KB | never | 32 | 256 | **1024** | 1024 | 2048 | 2048 | 2048 | **2048** | 2048 |
| `clocksmith_gamma_core` | 5.4 KB | 81.7 KB | 1.96 MB | never | 32 | 64 | **512** | 512 | 512 | 2048 | 2048 | **2048** | 2048 |
| `codenet_fresh` (diag) | 3.1 KB | 19.2 KB | 170.3 KB | 1.21 MB | 128 | 256 | **1024** | 2048 | 3072 | 4096 | 4096 | **4096** | 4096 |
| `codenet_fresh2` (diag) | 3.0 KB | 19.3 KB | 189.3 KB | 1.07 MB | 128 | 256 | **512** | 2048 | 3072 | 4096 | 4096 | **4096** | 4096 |

### 6.2 How Often Widely Separated $K$ Values ($\ge 4\times$ Apart) Produce Practically Identical Archives
- **Primary horizons (14 `dev_disjoint` queries):**
  - Within **0.5%** of optimal archive size: **1 / 14 (7.14%)**.
  - Within **1.0%** of optimal archive size: **2 / 14 (14.29%)**.
- **Full 10-horizon diagnostic sweep (70 `dev_disjoint` queries):**
  - Within **0.5%** of optimal archive size: **2 / 70 (2.86%)**.
  - Within **1.0%** of optimal archive size: **6 / 70 (8.57%)**.

Interpretation: the horizon optimum is *not* flat globally (only 7-14% of primary queries admit a $\ge 4\times$-separated prefix within 0.5-1.0%), which is why fixed-$K$ policies suffer 9-53% p95 excess; locally around $K^*(100\text{ KB})$, adjacent $2\times$ neighbors (e.g. `128` vs `256` or `256` vs `512`) are typically within 0.2-1.2%, explaining why micro-sketch prediction achieves 0.68% median excess without needing a full sweep.

---

## 7. Predicted vs Realized Regret, UPB Calibration, and Fallback Cost

- **Predicted vs realized coverage (`shipped_policy_dev_calibrated`):**
  - Same-chain 90% UPB covers realized pre-fallback same-chain excess on **13 / 14 (92.86%)** of `dev_disjoint` queries (nominal target: 90%). Only 1 miss (`ramda_ramda` @ 100 KB: UPB = 0.71%, realized = 1.14%).
  - Full-oracle diagnostic 90% UPB covers realized full-oracle excess on **12 / 14 (85.71%)**.
- **Fallback coverage and cost:**
  - In `dev_calibrated` mode on local dev, `SWEEP_REQUIRED` triggered on **0 / 14 (0.0%)** queries because every query's calibrated same-chain 90% UPB stayed in `[0.00%, 1.76%] <= 2.50%`. In `verify_dev_gate.py` (Gate 6b), injecting high sketch SE (`0.08`) immediately pushes UPB above `2.5%` and triggers `SWEEP_REQUIRED`.
  - In `strict_conformal` mode, `SWEEP_REQUIRED` triggered on **14 / 14 (100.0%)** queries solely because `n_cal_orgs = 5 < 9` (`conformal_90_base_upb = null / +inf`). Falling back to the 3-point geometric pilot adds `+203.8M` ops (`+71.15s` wall across 14 queries, bringing total work to `1.012x` of pilot and `0.393x` of grid) while bounding excess to `0.98%` median / `2.06%` p95 vs full oracle.

---

## 8. Token / RAM Variant (Scored Separately)

Using the frozen deterministic deployment RAM footprint `Dictionary.ram_footprint_bytes()` (from `1,890 B` at $K=0$ to `15,909 B` at $K=512$, `59,883 B` at $K=2048$, and `119,710 B` at $K=4096$):

### 8.1 Priced Token/RAM Objective: $\min_K (\lambda \cdot \text{RAM}_K + M \cdot \hat{\tau}_K)$
Evaluated across **42 queries** (7 `dev_disjoint` lineages x 3 frozen RAM prices $\lambda \in \{0.5, 0.05, 0.005\}$ tokens/RAM-byte x 2 horizons $M \in \{10^5, 10^8\}$):

| Arm | Regret vs Same-Chain Token/RAM Oracle (med / p95 / max) | Regret vs Full 7-Chain Token/RAM Oracle (med / p95 / max) |
| --- | ---: | ---: |
| `shipped_token_policy` | **0.00% / 0.43% / 1.54%** | **1.85% / 3.29% / 3.80%** |
| `pilot_3pt_token` | 0.00% / 0.79% / 1.54% | 1.93% / 3.55% / 4.21% |
| `fixed_K512` | 33.54% / 48.83% / 67.35% | 35.65% / 49.36% / 67.35% |
| `fixed_K2048` | 8.54% / 18.21% / 22.90% | 9.73% / 21.07% / 23.09% |
| `fixed_K4096` | 0.00% / 66.41% / 88.24% | 2.07% / 69.50% / 88.24% |

### 8.2 Hard RAM-Cap Objective: $\min_{K:\;\text{RAM}_K \le R_{\max}} \text{tokens}_K$
- **$R_{\max} = 16\,384\text{ B}$ (16 KiB, eligible $K \le 512$):** `shipped_token_policy` achieves **0.00% median / 0.00% max** regret vs same-chain oracle (**3.55% median / 4.87% p95** vs full 7-chain oracle).
- **$R_{\max} = 65\,536\text{ B}$ (64 KiB, eligible $K \le 2048$):** `shipped_token_policy` achieves **0.00% median / 0.00% max** regret vs same-chain oracle (**1.30% median / 2.14% p95** vs full 7-chain oracle).

---

## 9. Strict `dev_gate` Verification Status (`verify_dev_gate.py` & `replay.py`)

Every single `dev_gate` item passed cleanly (`replay.py all` -> **ALL PASSED in 15.23s**):

| Gate | Requirement | Status | Measured Evidence |
| --- | --- | --- | --- |
| Gate 1 | Independent decode of actual archives (100% byte fidelity) | **PASS** | 630/630 grid archives + 5 live isolated-subprocess (`python -I independent_decode.py`) archives at `K=0,64,512,2048,4096` exercising 4 ESC bytes; 100% fidelity, 0 B drift, random-access spot checks pass |
| Gate 2 | Reproduce chosen prefixes by exhaustive enumeration | **PASS** | 14/14 queries x 8 arms reproduced identically via exact `Fraction` enumeration of `out/prefix_grid.json` |
| Gate 3 | Negative control 1: corrupted code table rejected | **PASS** | +1 length (`Kraft 131064 != 131072`), -1 length (`Kraft 131088 != 131072`), and Kraft-preserving swap (`mismatched_count=8`) all rejected; CLI exits 1 |
| Gate 4 | Negative control 2: fit-to-cal/eval leakage rejected | **PASS** | Fit lineage, fit org (`ibm_codenet`), 1-file disguised hash leak (cal & eval), within-repo file resampling, and same-org cal->eval (`clocksmith`) all raise `LeakageError` |
| Gate 5 | Adversarial synthetic curves (flat tie-break + non-convex trap) | **PASS** | Exact flat curve selects `K=0` (full grid) / `K=64` (pilot) strictly toward smallest header $H_K$; bad intermediate bump (`K=128..1024` at `r=0.78`) followed by `K=4096` (`r=0.20`) escaped by exhaustive selector, 3-pt pilot, and micro-sketch policy at both 100 KB and 100 MB |
| Gate 6 | Abstain gate + end-to-end shipping procedure (incl. refit) | **PASS** | `strict_conformal` emits `SWEEP_REQUIRED` on `n_cal_orgs=6 < 9`; noisy query emits `SWEEP_REQUIRED` in `dev_calibrated`; synthetic 10-org calibration yields finite conformal 90% UPB (`1.14%`); full shipping refit -> predict -> encode -> isolated `independent_decode.py` passes at both horizons |
| Replay | `replay.py check` / `replay.py all` + `EMOJI.md` audit | **PASS** | Upstream chain SHA-256 checks, RFC-8259 strict JSON check, full deterministic recomputation of `dev_summary.json`, and 0-emoji audit all PASS |

---

## 10. Calibration Support Verdict & Requirements Before Freeze

- **Current local spent support:** 7 non-CodeNet codebases across **6 distinct organizations** (5 strictly third-party orgs: `expressjs`, `ramda`, `TheAlgorithms`, `lodash`, `python`; plus `clocksmith` covering `authored_catalogue_dev` and `clocksmith_gamma_core`).
- **Minimum mathematical support for finite distribution-free 90% conformal UPB:** $n_{\text{cal\_orgs}} \ge 9$ ($\lceil 0.90(n+1) \rceil \le n$), requiring at least **3 additional** independent organizations for the final refit and **4 additional** for every LOLO-CV fold.
- **Recommended pre-freeze calibration budget:** **16-20 independent sealed/held-out repository organizations** (10-14 additional independent repos across multiple languages) so the 90% conformal UPB quantile and p95 regret estimates are stable before freezing A1b for sealed evaluation.

## Reproduction Commands

```bash
cd projects/algorithm_solver/literals/a1b-horizon-sizing-v1
/Users/xyz/deco/gamma/.venv/bin/python replay.py check   # ~7s: integrity + all 6 dev_gate checks + EMOJI.md
/Users/xyz/deco/gamma/.venv/bin/python replay.py all     # ~15s: check + deterministic recomputation of dev_summary.json
```
