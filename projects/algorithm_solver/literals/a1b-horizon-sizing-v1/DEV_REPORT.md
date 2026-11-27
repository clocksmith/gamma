# BITS Experiment Card A1b — Horizon-Dependent Vocabulary Sizing (Development & Split-Conformal Calibration Report)

Status: **HELD / SEALED — CPU development & finite-sample split-conformal calibration fixed at `n_cal = 19` untouched independent organizations (`rank k = 18 / 19`, exact 90.00% coverage tolerating 1 outlier; 1,960 independently decoded `B1RA` archives at 100% fidelity / 0 B drift; all 6 `dev_gate` checks + `replay.py all` PASS). Zero sealed holdouts opened.**
- **Strict Split-Conformal Verdict at the 2.0% Sealed Bar (Single Unconditional Predictor `03fc39cf87d2`):** **DOES NOT CERTIFY DIRECT PICK** — exact finite-sample split-conformal 90% UPB (`k = 18 / 19`, allowing 1 outlier rather than degenerating to the sample maximum) on `s_i = max(full_oracle_regret_100KB, full_oracle_regret_100MB)` is **2.1095% > 2.00%** (17/19 orgs <= 1.91%; 2 breaches: `networkx` @ 100 KB = 2.11% and `executablebooks` @ 100 MB = 2.35%). `strict_conformal_2_0pct_bar` honestly emits **`SWEEP_REQUIRED`**.
- **Conformal Post-Selection Audit (`post_selection_pilot_switch_certified = false`):** This card certifies **only** the single unconditional Stage-1 locked predictor (`03fc39cf87d2`, byte-identical across revisions). It makes **no** claim that conditionally switching to the 3-point geometric pilot after inspecting calibration scores inherits unadjusted 90% split-conformal coverage. Moreover, on the expanded 19-organization calibration set, the separate 3-point pilot benchmark comparator also misses the 2.00% bar (**2.0394% > 2.00%**, with 2 breaches: `pygments` = 2.04%, `executablebooks` = 2.35%).
- **Hold & Compute Gate:** `A1b` remains strictly **HELD (NOT UNSEALED)**. C5 and C6 remain gated behind explicit model-compute approval (**zero GPU/LLM compute executed**, zero sealed holdouts opened).

---

## 1. Executive Summary & Methodological Corrections

This revision resolves the finite-sample conformal selection flaws caught during pre-unseal audit while preserving the Stage-1 locked predictor (`03fc39cf87d2`) byte-identically:

1. **Fixing Finite-Sample Degeneracy (`n_cal = 14 -> 19`, `rank k = 18 / 19`):** At $n_{\text{cal}} = 14$ and $\alpha = 0.10$, the split-conformal rank $\lceil 0.90(14+1) \rceil = 14 = n_{\text{cal}}$ degenerated to the sample maximum (0 outliers tolerated, conservative 93.33% floor). Expanding strictly via 5 pre-committed untouched Python organizations (`pallets/jinja`, `pygments/pygments`, `executablebooks/markdown-it-py`, `scikit-learn/scikit-learn`, `tqdm/tqdm`) yields **$n_{\text{cal}} = 19$** independent calibration organizations (`581` files, `3,453,994 B`, `1,330` calibration archives), where $k = \lceil 0.90(19+1) \rceil = 18 < 19$ achieves the **exact 90.00% finite-sample coverage guarantee** ($18 / 20$) while tolerating 1 outlier (`conformal_rank_is_sample_max = false`).
2. **Removing Post-Selection Conditional Switching Claims (`post_selection_pilot_switch_certified = false`):** Conditionally switching from the Stage-1 predictor (`2.11%`) to the 3-point pilot (`1.95%` at $n=14$) on the same calibration set without multiplicity correction breaks unadjusted 90% split-conformal validity. The protocol now certifies strictly the single unconditional Stage-1 locked predictor; the 3-point pilot is reported solely as a separate non-adaptive comparator, and on all 19 orgs even the 3-point pilot comparator reaches **2.0394% > 2.00%**.
3. **Zero-Drift Reproducibility Pin on `clocksmith_gamma_core`:** `archive_grid.py` pins `clocksmith_gamma_core` to baseline commit `7e9d8abff` (`194` `.py` files, `1,917,069 B`), guaranteeing `out/locked_predictor.json` reproduces **`03fc39cf87d2b79c9c97e0ec24275909c2cbe91621c059832410c81f9b9cd68f`** byte-for-byte regardless of later repository commits.
4. **Zero-Mutation `replay.py check`:** `replay.py check` and `verify_dev_gate.py` write all temporary archives and volatile receipts inside `tempfile.TemporaryDirectory()` by default (`git status --short` is 100% empty before and after).
5. **Strict 3-Way Disjointness & 59-Lineage Exclusion:** All 19 calibration orgs (`aio-libs`, `agronholm`, `python-attrs`, `fonttools`, `fsspec`, `encode`, `joblib`, `matplotlib`, `networkx`, `numpy`, `python-pillow`, `Textualize`, `scipy`, `sympy`, `pallets`, `pygments`, `executablebooks`, `scikit-learn`, `tqdm`) are programmatically verified for **0 overlap** against all **59** capacity/sealed corpora, all chain-fit & Stage-1 predictor-fit orgs, and all 5 A1b reserved sealed domains (`SQL`, `JSON/Protobuf`, `Rust`, `TypeScript`, `YAML`). No third-party source code is vendored into git.
6. **Strict Two-Stage Split-Conformal Protocol (Barber et al., `arXiv:1905.02928`):** Stage 1 fits and locks ONE predictor strictly on the 6 predictor-fit orgs (7 codebases; zero calibration data). Stage 2 reloads that exact locked predictor (`03fc39cf87d2`, zero refitting) and evaluates it once on each of the 19 untouched calibration orgs against $s_i = \max(\text{full}_{100\text{KB}}, \text{full}_{100\text{MB}})$ (full 7-chain oracle).
7. **All-In & Amortized Work Accounting:** Charges `shared_chain_build_sec` (`279.901 s`) and `all_7_chains_build_sec` (`3,578.058 s`) for $N \in \{1, 2, 5, 10, 50\}$ and exact break-even $N^*$ (Section 5).

---

## 2. Two-Stage Split-Conformal Calibration Results (`n_cal = 19` Untouched Orgs)

### 2.1 Finite-Sample Split-Conformal Summary ($\alpha = 0.10$, Locked Predictor `03fc39cf87d2`)

| Quantity | Value | Notes |
| --- | ---: | --- |
| Calibration organizations ($n_{\text{cal}}$) | **19** | 0 overlap with 59 capacity corpora, 7 fit/dev orgs, 5 sealed domains |
| Split-conformal rank $k = \lceil 0.90(n_{\text{cal}}+1) \rceil$ | **18 / 19** | Exact finite-sample guarantee $P(s_{\text{new}} \le \hat{q}_{0.90}) \ge 18/20 = \mathbf{90.00\%}$ (`sample_max = false`, 1 outlier tolerated) |
| **90% UPB on $s_i = \max(\text{full}_{100\text{KB}}, \text{full}_{100\text{MB}})$** | **2.1095%** | **FAILS 2.00% sealed bar** (2/19 orgs breach: `networkx` @ 100 KB = 2.11%, `executablebooks` @ 100 MB = 2.35%) |
| `strict_conformal_2_0pct_bar` decision | **`SWEEP_REQUIRED`** | Honest refusal to certify direct pick (single unconditional predictor only) |
| Post-selection pilot switch certified? | **`false`** | Switching predictors on the same calibration set breaks unadjusted 90% validity |
| Simultaneous selection-safe 90% UPB (`max(direct, pilot)`) | **2.1095%** | `selected_policy_clears_bar = false` (`HOLD` — covers either choice simultaneously) |
| Separate 3-pt geometric pilot comparator 90% UPB | **2.0394%** | **Also misses 2.00% bar** (2/19 breaches: `pygments` = 2.04%, `executablebooks` = 2.35%) |
| Legacy 2.50% bar check (continuity only) | **PASS (2.11% <= 2.50%)** | Reported for continuity; primary sealed bar remains 2.00% |
| Per-horizon 90% UPB (`100 KB` / `100 MB`) | **1.5629% / 1.9081%** | Each horizon clears 2.00% marginally; joint max across horizons reaches 2.1095% |
| Regret decomposition 90% UPB (`budget` / `chain`) | **1.5862% / 1.5306%** | Both components individually < 2.00%, but their sum/worst-case exceeds 2.00% on 2 orgs |

Sorted nonconformity scores $s_i$ (%) across all 19 untouched calibration orgs (rank 18 bolded):
`[0.4526, 0.5851, 0.6490, 0.6983, 0.7556, 0.8944, 0.9708, 1.0222, 1.0228, 1.0718, 1.0765, 1.2896, 1.5629, 1.5862, 1.7193, 1.8182, 1.9081,` **`2.1095`**, `2.3481]`.

### 2.2 Per-Organization Regret & Same-Chain vs Full-Oracle Decomposition (19 Untouched Orgs)

Each entry decomposes exact full-oracle regret into **budget-choice regret** on `exact_closed` (`bud%`) and **irreducible chain-choice regret** vs the best of all 7 verified chains (`ch%`), satisfying $(1 + \text{full}) = (1 + \text{bud})(1 + \text{ch})$.

| Calibration Org (`package==ver`) | Files / Bytes | 100 KB: Locked $K$ | 100 KB Full Regret (`bud%` / `ch%`, Full Oracle) | 100 MB: Locked $K$ | 100 MB Full Regret (`bud%` / `ch%`, Full Oracle) | $s_i = \max$ | Binding | Pilot $s_i$ (Comp.) |
| --- | ---: | ---: | --- | ---: | --- | ---: | --- | ---: |
| `aio-libs` (`aiohttp==3.13.3`) | 20 / 199 KB | K256 | 0.00% (0.00 / 0.00, `exact_closed:K256`) | K2048 | 1.29% (0.00 / 1.29, `exact_norm_p2:K3924`) | **1.29%** | 100MB | 1.89% |
| `agronholm` (`anyio==4.12.1`) | 28 / 199 KB | K256 | 1.08% (0.99 / 0.09, `bundle_slot:K128`) | K2048 | 0.71% (0.00 / 0.71, `exact_norm_p2:K3924`) | **1.08%** | 100KB | 1.78% |
| `python-attrs` (`attrs==25.4.0`) | 12 / 60 KB | K256 | 0.89% (0.59 / 0.30, `bundle_slot:K512`) | K2048 | 0.25% (0.00 / 0.25, `bpe:K2048`) | **0.89%** | 100KB | 1.95% |
| `fonttools` (`fonttools==4.61.1`) | 31 / 200 KB | K256 | 0.01% (0.00 / 0.01, `bundle_slot:K256`) | K2048 | 1.02% (0.00 / 1.02, `exact_norm_p2:K3924`) | **1.02%** | 100MB | 1.65% |
| `fsspec` (`fsspec==2025.10.0`) | 25 / 199 KB | K256 | 0.24% (0.00 / 0.24, `bundle_slot:K512`) | K2048 | 1.91% (0.37 / 1.53, `exact_norm_p2:K3072`) | **1.91%** | 100MB | 1.53% |
| `encode` (`httpx==0.28.1`) | 20 / 174 KB | K256 | 0.59% (0.59 / 0.00, `exact_closed:K64`) | K2048 | 0.45% (0.00 / 0.45, `exact_norm_p2:K2048`) | **0.59%** | 100KB | 1.39% |
| `joblib` (`joblib==1.5.3`) | 33 / 198 KB | K128 | 0.65% (0.63 / 0.02, `bundle_slot:K128`) | K2048 | 0.70% (0.00 / 0.70, `exact_norm_p2:K3924`) | **0.70%** | 100MB | 1.58% |
| `matplotlib` (`matplotlib==3.10.8`) | 25 / 200 KB | K256 | 0.76% (0.76 / 0.00, `exact_closed:K64`) | K2048 | 0.00% (0.00 / 0.00, `exact_closed:K2048`) | **0.76%** | 100KB | 0.89% |
| `networkx` (`networkx==3.6.1`) | 26 / 200 KB | K256 | **2.11%** (2.11 / 0.00, `exact_closed:K64`) | K2048 | 0.60% (0.00 / 0.60, `bpe:K2048`) | **2.11%** | **100KB** | 1.62% |
| `numpy` (`numpy==2.4.1`) | 46 / 200 KB | K256 | 0.65% (0.00 / 0.65, `bundle_byte:K256`) | K2048 | 0.15% (0.00 / 0.15, `exact_norm_p2:K3924`) | **0.65%** | 100KB | 0.65% |
| `python-pillow` (`pillow==12.1.0`) | 30 / 200 KB | K256 | 0.10% (0.00 / 0.10, `bundle_slot:K128`) | K2048 | 0.45% (0.00 / 0.45, `exact_norm_p2:K3072`) | **0.45%** | 100MB | 0.45% |
| `Textualize` (`rich==14.2.0`) | 41 / 200 KB | K256 | 0.20% (0.00 / 0.20, `bundle_slot:K512`) | K4096 | 1.82% (1.12 / 0.69, `exact_norm_p2:K3924`) | **1.82%** | 100MB | 1.82% |
| `scipy` (`scipy==1.17.0`) | 47 / 200 KB | K256 | 1.07% (0.64 / 0.43, `bundle_slot:K128`) | K2048 | 0.16% (0.00 / 0.16, `bpe:K2048`) | **1.07%** | 100KB | 1.39% |
| `sympy` (`sympy==1.14.0`) | 32 / 200 KB | K256 | 0.97% (0.48 / 0.49, `bundle_slot:K128`) | K2048 | 0.44% (0.00 / 0.44, `exact_norm_p2:K3924`) | **0.97%** | 100KB | 1.60% |
| `pallets` (`Jinja2==3.1.6`) | 17 / 128 KB | K256 | 1.02% (1.02 / 0.00, `exact_closed:K64`) | K2048 | 0.56% (0.00 / 0.56, `exact_norm_p2:K3924`) | **1.02%** | 100KB | 1.50% |
| `pygments` (`Pygments==2.19.2`) | 31 / 200 KB | K256 | 1.56% (0.37 / 1.19, `exact_byte:K256`) | K2048 | 0.38% (0.00 / 0.38, `exact_norm_p2:K3072`) | **1.56%** | 100KB | **2.04%** |
| `executablebooks` (`markdown-it-py==4.0.0`) | 58 / 200 KB | K256 | 0.92% (0.51 / 0.40, `bundle_slot:K512`) | K4096 | **2.35%** (1.24 / 1.09, `exact_norm_p2:K3924`) | **2.35%** | **100MB** | **2.35%** |
| `scikit-learn` (`scikit-learn==1.8.0`) | 30 / 200 KB | K32 | 0.38% (0.38 / 0.00, `exact_closed:K64`) | K1024 | 1.59% (1.59 / 0.00, `exact_closed:K2048`) | **1.59%** | 100MB | 1.59% |
| `tqdm` (`tqdm==4.67.1`) | 29 / 97 KB | K256 | 0.60% (0.42 / 0.19, `bundle_slot:K512`) | K2048 | 1.72% (0.00 / 1.72, `exact_norm_p2:K3924`) | **1.72%** | 100MB | 1.72% |

**Diagnostic takeaway from the 19-org decomposition:**
- At **100 MB**, the locked predictor hits the exact same-chain optimum (`K=2048`, **0.00% budget regret**) on **15 of 19** untouched organizations; on `executablebooks` (`markdown-it-py`), picking `K=4096` instead of `K=2048` adds `1.24%` budget regret on top of `1.09%` irreducible chain-choice regret vs `exact_norm_p2`, producing the `2.35%` tail breach (the single tolerated outlier at rank 18/19).
- At **100 KB**, `networkx` (`2.11%`, pure budget-choice regret from picking `K=256` over `exact_closed:K64`) becomes the exact rank-18 order statistic (`2.1095% > 2.00%`), preventing 2.0% certification.

---

## 3. Complete Arm Comparison on the 19 Untouched Calibration Orgs (38 Queries)

| Arm | vs Same-Chain Oracle (med / p95 / max) | vs Full 7-Chain Oracle (med / p95 / max) | Fallback Rate | Eval-Only Wall s (p95 s) | Eval-Only Total Ops | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `locked_predictor_direct` | **0.00% / 1.29% / 2.11%** | **0.65% / 1.94% / 2.35%** | 0.0% (0/38) | 18.89 (0.71) | 74,626,361 | 162 MiB |
| `strict_conformal_2_0pct_bar` | 0.69% / 1.60% / 1.69% | 1.00% / 1.96% / 2.35% | 100.0% (38/38) | 68.79 (2.51) | 269,229,865 | 162 MiB |
| `fixed_K512` | 1.80% / 3.69% / 4.87% | 2.04% / 4.47% / 5.55% | 0.0% | 15.94 (0.54) | 62,042,578 | 121 MiB |
| `fixed_K2048` | 8.65% / 19.87% / 21.62% | 9.45% / 20.47% / 21.62% | 0.0% | 21.54 (0.73) | 81,301,790 | 121 MiB |
| `fixed_K4096` | 24.25% / 51.45% / 53.22% | 24.47% / 52.07% / 53.22% | 0.0% | 23.64 (0.80) | 91,409,518 | 121 MiB |
| `pilot_3pt_geometric` | 0.69% / 1.60% / 1.69% | 1.00% / 1.96% / 2.35% | 0.0% | 67.78 (2.48) | 263,420,219 | 121 MiB |
| `same_chain_oracle` (10-pt grid) | 0.00% / 0.00% / 0.00% | 0.34% / 1.33% / 1.72% | 0.0% | 167.64 (5.72) | 654,727,182 | 121 MiB |
| `full_selector_by_K_oracle` (7 chains) | -0.34% / 0.00% / 0.00% | 0.00% / 0.00% / 0.00% | 0.0% | 1,005.55 (32.64) | 4,539,131,410 | 121 MiB |

*Note on Stage-1 LOLO-CV reference (6 predictor-fit orgs, 14 queries):* median `0.00%` / p95 `0.78%` vs same-chain, median `0.68%` / p95 `1.56%` / max `2.34%` vs full oracle. Explicitly labeled **diagnostic only — NOT valid for split-conformal coverage** (Barber et al., `arXiv:1905.02928`).

*Note on segregated in-distribution CodeNet strata (evaluated under exact locked predictor `03fc39cf87d2`, never used in fit/cal):* `codenet_fresh` @ 100 KB (`K=512`, +0.17% same / +6.12% full vs `exact_open`), @ 100 MB (`K=4096`, **0.00%** same / **+0.58%** full); `codenet_fresh2` @ 100 KB (`K=512`, **0.00%** same / +5.19% full), @ 100 MB (`K=4096`, **0.00%** same / **+0.92%** full).

---

## 4. Shared Spine Contract (`shared_spine`) & Compute Gate

All four `shared_spine` fields and C5/C6 compute gates are recorded in [dev_summary.json](dev_summary.json):
- **`fidelity`:** `1.0` across **1,960 / 1,960** serialized `B1RA` archives (**630** Stage-1 dev/diag + **1,330** Stage-2 calibration), independently decoded byte-for-byte via `independent_decode.py` (stdlib-only, zero encoder imports), **0 B accounting drift**, 100% random-access spot checks passed.
- **`complete_bits` (mean across 19 calibration orgs):**
  - At $M = 100\,000\text{ B}$: `locked_predictor_direct` = **463,008.44 bits**, `strict_conformal_2_0pct_bar` (pilot fallback) = **462,677.37 bits**, `same_chain_oracle` = **460,681.61 bits**, `full_selector_by_K_oracle` = **459,645.52 bits**, `fixed_K512` = **465,096.42 bits**, `fixed_K2048` = **547,068.54 bits**, `fixed_K4096` = **688,299.09 bits**.
  - At $M = 100\,000\,000\text{ B}$: `locked_predictor_direct` = **424,004,815.71 bits**, `strict_conformal_2_0pct_bar` = **426,774,459.43 bits**, `same_chain_oracle` = **423,067,695.17 bits**, `full_selector_by_K_oracle` = **420,418,131.85 bits**, `fixed_K512` = **434,822,726.89 bits**, `fixed_K4096` = **429,957,685.68 bits**.
- **`measured_work`:** Full all-in + amortized breakdown including `shared_chain_build_sec = 279.901 s` and `all_7_chains_build_sec = 3,578.058 s` (Section 5).
- **`horizon` ($M^*$):** Primary horizons $M \in \{100\,000, 100\,000\,000\}\text{ B}$, diagnostic sweep $M \in [10^4, 10^9]\text{ B}$, and exact break-even $M^*$ per lineage (Section 6).
- **`compute_gate_policy`:** `C5_status = GATED_BEHIND_EXPLICIT_MODEL_COMPUTE_APPROVAL`, `C6_status = GATED_BEHIND_EXPLICIT_MODEL_COMPUTE_APPROVAL`, `gpu_compute_run = false`, `llm_compute_run = false`, `sealed_holdouts_opened = false`.

---

## 5. Honest All-In & Amortized Work Accounting

### 5.1 Exact Measured Build & Per-Deployment Components

| Component | Exact Measured Seconds | Source / Provenance |
| --- | ---: | --- |
| Primary chain engine build (`exact_closed`) | 257.950 s | Verified footer of `closure-holdout-v1/out/bundle/pair-ext.txt` |
| Primary chain B1RA header fit (10 prefixes) | 21.949 s | Sum of measured `fit_work.wall_seconds` in `out/prefix_grid.json` |
| Stage-1 locked predictor fit (`out/locked_predictor.json`) | 0.002 s | Live measured `LockedHorizonPredictor.fit_and_lock()` |
| **`shared_chain_build_sec` (1 deployed chain total)** | **279.901 s** | Exact sum of the 3 build components above |
| All 7 chains engine build | 3,491.700 s | Verified chain footers + `objective-holdout-v1/frozen/train-summary.json` |
| All 7 chains B1RA header fit (deduplicating shared `K=0`) | 86.358 s | Sum of measured `fit_work.wall_seconds` in `out/prefix_grid.json` |
| **`all_7_chains_build_sec` (full 7-chain build total)** | **3,578.058 s** | Exact sum of all 7 chain builds + all 7 header fits |
| Per-deployment `locked_predictor_direct` (cal-19 mean, ~182 KB/org) | 0.497 s / dep | Micro-sketch + prediction + 1 deployment encode |
| Per-deployment `strict_conformal` effective (100% pilot fallback) | 1.810 s / dep | Micro-sketch + 3-pt geometric pilot (with prefix reuse) |
| Per-deployment `same_chain_pilot` (cal-19 mean) | 1.784 s / dep | Frozen 3-pt geometric pilot (`K in {64, 512, 4096}`) |
| Per-deployment `same_chain_grid` (cal-19 mean) | 4.412 s / dep | All 10 grid prefixes on `exact_closed` |
| Per-deployment `all_7_chains_grid_eval` (cal-19 mean) | 26.462 s / dep | All 7 chains x eligible prefixes |

### 5.2 Single-Deployment ($N=1$) & Amortized ($N \in \{1, 2, 5, 10, 50\}$) All-In Work Ratios

**Calibration 19-Org Basis (~182 KB/org mean):**

| Mode | $N$ Deployments | Policy All-In s | Same-Chain Pilot All-In s | Same-Chain Grid All-In s | Full 7-Chain All-In s | Ratio vs Same-Chain Pilot | Ratio vs Same-Chain Grid | Ratio vs Full 7-Chain Grid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `locked_direct` | **1** | 280.40 | 281.68 | 284.31 | 3,604.52 | **0.9954x** | **0.9862x** | **0.0778x** |
| `locked_direct` | 2 | 280.90 | 283.47 | 288.72 | 3,630.98 | 0.9909x | 0.9729x | 0.0774x |
| `locked_direct` | 5 | 282.39 | 288.82 | 301.96 | 3,710.37 | 0.9777x | 0.9352x | 0.0761x |
| `locked_direct` | 10 | 284.87 | 297.74 | 324.02 | 3,842.68 | 0.9568x | 0.8792x | 0.0741x |
| `locked_direct` | 50 | 304.76 | 369.08 | 500.48 | 4,901.14 | 0.8257x | 0.6089x | 0.0622x |
| `strict_conformal` | **1** | 281.71 | 281.68 | 284.31 | 3,604.52 | **1.0001x** | **0.9909x** | **0.0782x** |
| `strict_conformal` | 2 | 283.52 | 283.47 | 288.72 | 3,630.98 | 1.0002x | 0.9820x | 0.0781x |
| `strict_conformal` | 5 | 288.95 | 288.82 | 301.96 | 3,710.37 | 1.0005x | 0.9569x | 0.0779x |
| `strict_conformal` | 10 | 298.00 | 297.74 | 324.02 | 3,842.68 | 1.0009x | 0.9197x | 0.0776x |
| `strict_conformal` | 50 | 370.41 | 369.08 | 500.48 | 4,901.14 | 1.0036x | 0.7401x | 0.0756x |

**Exact Break-Even Deployment Counts $N^*$ (reusing the single pre-built chain):**
- **`locked_predictor_direct` (cal-19 ~182 KB/org basis):**
  - Asymptotic ($N \to \infty$) eval-only ratios: **0.279x** vs same-chain pilot, **0.113x** vs same-chain grid, **0.019x** vs full 7-chain grid.
  - All-in break-even to cross `<= 1/2` of same-chain pilot: **`N* = 355`** deployments.
  - All-in break-even to cross `<= 1/6` of same-chain grid: **`N* = 980`** deployments.
  - All-in vs `full_multichain_grid`: already **0.0778x** (`<< 1/6`) at **`N = 1`**.
- **`strict_conformal_2_0pct_bar` (100% pilot fallback while uncertified):**
  - All-in vs `full_multichain_grid`: **0.0782x** (`<< 1/6`) at **`N = 1`**.
  - Break-even vs `1/2` same-chain pilot or `1/6` same-chain grid: **`None` (never)**.

---

## 6. Codeword Widening, Lower Envelope & Token/RAM Variant (19 Calibration Orgs)

### 6.1 Codeword Widening Replicates 100% (26 / 26 Non-CodeNet Codebases)
On **all 19 / 19** untouched calibration organizations (in addition to all 7 / 7 Stage-1 dev codebases), extending `exact_closed` from `K = 2048` to `K = 4096` causes non-monotonic tail degradation:
- Realized codewords widen by **+0.955 to +1.102 bits/token**.
- Coded body rate $\hat{r}_K$ *increases* by **+0.73% to +2.60%**, so $M^*(K=2048 \to K=4096) = \text{never}$ on every single out-of-distribution codebase (`26 / 26`), whereas in-distribution CodeNet keeps dropping (`-4.32%` / `-4.87%`).

### 6.2 Near-Tie Flatness ($\ge 4\times$-Separated Prefixes Within Tolerance)
Across the 19 untouched calibration orgs:
- Primary horizons (38 queries): **6 / 38 (15.8%)** within 0.5%, **17 / 38 (44.7%)** within 1.0%.
- Diagnostic 10-horizon sweep (190 queries): **9 / 190 (4.7%)** within 0.5%, **35 / 190 (18.4%)** within 1.0%.

### 6.3 Token / RAM Variant (Scored Separately on 19 Untouched Calibration Orgs)
Using the frozen deterministic deployment RAM model (`1,890 B` at `K=0` to `15,909 B` at `K=512`, `59,883 B` at `K=2048`, `119,710 B` at `K=4096`) and the locked token-rate bias fitted strictly on the 6 Stage-1 predictor-fit orgs:
- **Priced Token/RAM ($\lambda \in \{0.5, 0.05, 0.005\}$, 114 queries):**
  - `locked_token_policy`: **0.00% med / 0.20% p95 / 1.81% max** vs same-chain (**2.09% med / 3.16% p95** vs full 7-chain oracle).
  - `pilot_3pt_token`: 0.00% / 0.31% vs same-chain (2.09% / 3.29% vs full).
  - `fixed_K512`: 33.89% / 39.21% vs same-chain (36.95% / 41.54% vs full).
  - `fixed_K2048`: 8.51% / 19.61% vs same-chain (10.15% / 22.70% vs full).
  - `fixed_K4096`: 0.00% / 64.38% vs same-chain (2.20% / 68.40% vs full).
- **Hard RAM Caps (19 calibration orgs each):**
  - `16 KiB` cap ($K \le 512$): **0.00% med / 0.00% max** vs same-chain (**2.40% med / 4.26% p95** vs full).
  - `64 KiB` cap ($K \le 2048$): **0.00% med / 0.00% max** vs same-chain (**1.39% med / 2.49% p95** vs full).

---

## 7. Strict `dev_gate` & `replay.py` Verification Status

| Check | Status | Measured Evidence |
| --- | --- | --- |
| `replay.py check` zero-mutation guarantee | **PASS** | `git status --short` is empty both before and after `replay.py check` |
| 59-lineage + fit-org + reserved-domain disjointness | **PASS** | 19 calibration orgs verified 0-overlap against all 59 capacity corpora, fit/dev orgs, and 5 sealed domains; live `.venv` verified 581/581 files (0 mismatches) |
| Gate 1 (`independent_decode_100pct_fidelity`) | **PASS** | 1,960/1,960 grid archives (630 dev/diag + 1,330 calibration) + 5 live isolated-subprocess archives (`K=0,64,512,2048,4096`, 4 ESC bytes), 100% fidelity, 0 B drift |
| Gate 2 (`exhaustive_score_reproduction`) | **PASS** | `locked_predictor_sha256` (`03fc39cf87d2`) verified byte-identical; all 19 calibration orgs' `100KB`, `100MB`, `s_i = max(...)`, `rank k = 18/19` (`sample_max = false`), `UPB = 2.1095%`, `post_selection_pilot_switch_certified = false`, and 38 x 8 arm choices reproduced via exact `Fraction` enumeration |
| Gate 3 (`negative_control_corrupted_code_table`) | **PASS** | +1 Kraft underflow, -1 Kraft overflow, Kraft-preserving length swap all rejected; CLI exits 1 |
| Gate 4 (`negative_control_leakage_and_59_lineage_disjointness`) | **PASS** | Fit lineage/org/hash leaks, 3-way Stage-1->Stage-2 leak, within-repo resampling, capacity repos (`ggml`, `ajv`), and sealed domains (`yaml`, `sql`) all rejected |
| Gate 5 (`adversarial_synthetic_curves`) | **PASS** | Exact flat curve selects smallest header (`K=0` grid / `K=64` pilot); non-convex bad-intermediate bump escaped to `K=4096` by exhaustive, pilot, and sketch policy |
| Gate 6 (`abstain_and_end_to_end_shipping`) | **PASS** | Exact locked predictor (`03fc39cf87d2`) triggers honest `SWEEP_REQUIRED` at 2.0% bar and passes full live B1RA encode + isolated `independent_decode.py` at 100 KB and 100 MB |
| `replay.py all` + `EMOJI.md` audit | **PASS** | `out/locked_predictor.json` reproduced byte-for-byte; `dev_summary.json` identical outside timings; RFC-8259 JSON valid; 0 emojis across all 15 files |

## Reproduction Commands

```bash
cd projects/algorithm_solver/literals/a1b-horizon-sizing-v1
/Users/xyz/deco/gamma/.venv/bin/python replay.py check                  # ~7s, never dirties tracked files
/Users/xyz/deco/gamma/.venv/bin/python replay.py check --report /tmp/a1b.json
/Users/xyz/deco/gamma/.venv/bin/python replay.py all                    # ~14s, full deterministic recomputation
```
