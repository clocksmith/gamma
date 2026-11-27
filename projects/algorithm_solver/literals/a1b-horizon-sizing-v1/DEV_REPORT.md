# BITS Experiment Card A1b — Horizon-Dependent Vocabulary Sizing (Development & Split-Conformal Calibration Report)

Status: **CPU development & strict two-stage split-conformal calibration complete (`n_cal = 14` untouched independent organizations; 1,610 independently decoded `B1RA` archives at 100% fidelity / 0 B drift; all 6 `dev_gate` checks + `replay.py all` PASS).**
- **Strict Split-Conformal Verdict at the 2.0% Sealed Bar:** **DOES NOT CERTIFY DIRECT PICK** — exact finite-sample split-conformal 90% UPB on `max(full_oracle_regret_100KB, full_oracle_regret_100MB)` is **2.1095% > 2.00%** (13/14 orgs <= 1.91%, 1 breach on `networkx` @ 100 KB at 2.11%). `strict_conformal_2_0pct_bar` honestly emits **`SWEEP_REQUIRED`** and falls back to the frozen 3-point geometric pilot, whose own split-conformal 90% UPB on the same 14 orgs is **1.9509% <= 2.00%**.
- **C5 / C6 Compute Gate:** C5 and C6 remain strictly gated behind explicit model-compute approval (**zero GPU/LLM compute executed**, zero sealed holdouts opened, zero files modified outside `a1b-horizon-sizing-v1/`).

---

## 1. Executive Summary & Methodological Corrections

This revision implements five critical methodological and accounting corrections before landing A1b on `main`:

1. **Zero-Mutation `replay.py check`:** `replay.py check` and `verify_dev_gate.py` write all temporary archives and volatile receipts inside `tempfile.TemporaryDirectory()` by default (only writing a JSON report when `--report <path>` / `--out <path>` is explicitly supplied). Running `replay.py check` never dirties any tracked file (`git status --short` is 100% empty before and after).
2. **14 Untouched Independent Calibration Organizations (Strictly Disjoint from All 59 Capacity Lineages, Fit Orgs & Reserved Sealed Domains):** Deterministically selected 14 independent open-source organizations from local `.venv` site-packages (`aio-libs`, `agronholm`, `python-attrs`, `fonttools`, `fsspec`, `encode`, `joblib`, `matplotlib`, `networkx`, `numpy`, `python-pillow`, `Textualize`, `scipy`, `sympy`), verified programmatically for **0 overlap** against all **59** capacity/sealed corpora across `capacity-ladder-v1/real-corpora.json`, `capacity-deficit-race-v1/instances-{a,b}.json`, `capacity-lagrangian-race-v1/public-instances.json`, `capacity-boundary-v1`, `capacity-diagnostic-v1`, and `capacity-race-v1`, all chain-fit & Stage-1 predictor-fit orgs, and all 5 A1b reserved sealed domains (`SQL`, `JSON/Protobuf`, `Rust`, `TypeScript`, `YAML`). No third-party source code is vendored into git — only deterministic manifests (`out/calibration_manifest.json`, 416 files pinned by SHA-256) and independently decoded archive receipts (`out/calibration_grid.json`, 980 archives).
3. **Strict Two-Stage Split-Conformal Protocol (Fixing the Barber et al. `arXiv:1905.02928` LOO Pitfall):**
   - **Why LOLO-CV cannot establish split-conformal coverage:** Leave-one-organization-out (LOLO) residuals evaluate a *different* refitted predictor $\hat{f}^{(-i)}$ on each fold rather than the single shipped predictor $\hat{f}$. Because $\hat{f}^{(-i)} \neq \hat{f}$, the LOLO scores are not exchangeable with a future test organization evaluated under $\hat{f}$, so even at large $n$ they cannot guarantee the advertised `>= 90%` split-conformal coverage (Barber et al., *Predictive inference with the jackknife+*, `arXiv:1905.02928`).
   - **Stage 1 (Fit & Lock):** Fit ONE exact predictor strictly on the 6 Stage-1 predictor-fit orgs (7 codebases; zero data from the 14 calibration orgs), serialize its canonical parameters to [out/locked_predictor.json](out/locked_predictor.json), and pin `locked_predictor_sha256 = 03fc39cf87d2b79c9c97e0ec24275909c2cbe91621c059832410c81f9b9cd68f`.
   - **Stage 2 (Exact Split-Conformal Calibration):** Reload that **EXACT locked predictor** (`03fc39cf87d2...`, zero refitting) and evaluate it ONCE on each of the 14 untouched calibration orgs.
4. **Joint Worst-Horizon Full-Oracle Nonconformity Score ($s_i = \max(\text{regret}_{100\text{KB}}, \text{regret}_{100\text{MB}})$):** Calibrated strictly against the **full 7-chain selector-by-$K$ oracle** (not same-chain) across *both* primary horizons simultaneously, matching the sealed breach event (breaching `2.0%` on *either* 100 KB or 100 MB).
5. **All-In & Amortized Work Accounting (Fixing the `0.112x` Denominator Flaw):** The prior headline `0.112x` wall ratio divided only per-query eval time by per-query same-chain grid eval time and omitted the shared chain-build cost (`279.90 s` to build `exact_closed` + fit its 10 B1RA code tables + lock Stage 1). Section 5 reports honest single-deployment ($N=1$) and amortized ($N \in \{1, 2, 5, 10, 50\}$) all-in ratios against both `same_chain_grid`, `same_chain_pilot`, and `full_multichain_grid` (`3,578.06 s` to build all 7 chains + all-7 grid eval), plus exact break-even $N^*$.

---

## 2. Two-Stage Split-Conformal Calibration Results (`n_cal = 14` Untouched Orgs)

### 2.1 Finite-Sample Split-Conformal Summary ($\alpha = 0.10$, Locked Predictor `03fc39cf87d2`)

| Quantity | Value | Notes |
| --- | ---: | --- |
| Calibration organizations ($n_{\text{cal}}$) | **14** | 0 overlap with 59 capacity corpora, 7 fit/dev orgs, 5 sealed domains |
| Split-conformal rank $k = \lceil 0.90(n_{\text{cal}}+1) \rceil$ | **14 / 14** | Exact finite-sample guarantee $P(s_{\text{new}} \le \hat{q}_{0.90}) \ge 14/15 = \mathbf{93.33\%} \ge 90\%$ |
| **90% UPB on $s_i = \max(\text{full}_{100\text{KB}}, \text{full}_{100\text{MB}})$** | **2.1095%** | **FAILS 2.00% sealed bar** (1/14 org breaches: `networkx` @ 100 KB = 2.11%) |
| `strict_conformal_2_0pct_bar` decision | **`SWEEP_REQUIRED`** | Honest abstention -> falls back to frozen 3-pt geometric pilot |
| Legacy 2.50% bar check (continuity only) | **PASS (2.11% <= 2.50%)** | Reported for continuity; primary sealed bar remains 2.00% |
| Per-horizon 90% UPB (`100 KB` / `100 MB`) | **2.1095% / 1.9081%** | 100 MB alone clears 2.00%; 100 KB drives the single breach |
| Regret decomposition 90% UPB (`budget` / `chain`) | **2.1095% / 1.5306%** | Budget choice drives 100 KB worst case; chain choice drives 100 MB |
| Frozen 3-pt geometric pilot 90% UPB (full max) | **1.9509%** | **CLEARS 2.00% sealed bar** on all 14/14 calibration orgs! |

Sorted nonconformity scores $s_i$ (%) across the 14 untouched calibration orgs:
`[0.4526, 0.5851, 0.6490, 0.6983, 0.7556, 0.8944, 0.9708, 1.0228, 1.0718, 1.0765, 1.2896, 1.8182, 1.9081, 2.1095]`.

### 2.2 Per-Organization Regret & Same-Chain vs Full-Oracle Decomposition (14 Untouched Orgs)

Each entry decomposes exact full-oracle regret into **budget-choice regret** on `exact_closed` (`bud%`) and **irreducible chain-choice regret** vs the best of all 7 verified chains (`ch%`), satisfying $(1 + \text{full}) = (1 + \text{bud})(1 + \text{ch})$.

| Calibration Org (`package==ver`) | Files / Bytes | 100 KB: Locked $K$ | 100 KB Full Regret (`bud%` / `ch%`, Full Oracle) | 100 MB: Locked $K$ | 100 MB Full Regret (`bud%` / `ch%`, Full Oracle) | $s_i = \max$ | Binding | Pilot $s_i$ |
| --- | ---: | ---: | --- | ---: | --- | ---: | --- | ---: |
| `aio-libs` (`aiohttp==3.13.3`) | 20 / 199 KB | K256 | 0.00% (0.00 / 0.00, `exact_closed:K256`) | K2048 | 1.29% (0.00 / 1.29, `exact_norm_p2:K3924`) | **1.29%** | 100MB | 1.88% |
| `agronholm` (`anyio==4.12.1`) | 28 / 199 KB | K256 | 1.08% (0.99 / 0.09, `bundle_slot:K128`) | K2048 | 0.71% (0.00 / 0.71, `exact_norm_p2:K3924`) | **1.08%** | 100KB | 1.20% |
| `python-attrs` (`attrs==25.4.0`) | 12 / 60 KB | K256 | 0.89% (0.59 / 0.30, `bundle_slot:K512`) | K2048 | 0.25% (0.00 / 0.25, `bpe:K2048`) | **0.89%** | 100KB | 1.22% |
| `fonttools` (`fonttools==4.61.1`) | 31 / 200 KB | K256 | 0.01% (0.00 / 0.01, `bundle_slot:K256`) | K2048 | 1.02% (0.00 / 1.02, `exact_norm_p2:K3924`) | **1.02%** | 100MB | 1.75% |
| `fsspec` (`fsspec==2025.10.0`) | 25 / 199 KB | K256 | 0.24% (0.00 / 0.24, `bundle_slot:K512`) | K2048 | 1.91% (0.37 / 1.53, `exact_norm_p2:K3072`) | **1.91%** | 100MB | 1.53% |
| `encode` (`httpx==0.28.1`) | 20 / 174 KB | K256 | 0.59% (0.59 / 0.00, `exact_closed:K64`) | K2048 | 0.45% (0.00 / 0.45, `exact_norm_p2:K2048`) | **0.59%** | 100KB | 1.49% |
| `joblib` (`joblib==1.5.3`) | 33 / 198 KB | K128 | 0.65% (0.63 / 0.02, `bundle_slot:K128`) | K2048 | 0.70% (0.00 / 0.70, `exact_norm_p2:K3924`) | **0.70%** | 100MB | 1.45% |
| `matplotlib` (`matplotlib==3.10.8`) | 25 / 200 KB | K256 | 0.76% (0.76 / 0.00, `exact_closed:K64`) | K2048 | 0.00% (0.00 / 0.00, `exact_closed:K2048`) | **0.76%** | 100KB | 0.89% |
| `networkx` (`networkx==3.6.1`) | 26 / 200 KB | K256 | **2.11%** (2.11 / 0.00, `exact_closed:K64`) | K2048 | 0.60% (0.00 / 0.60, `bpe:K2048`) | **2.11%** | **100KB** | 1.19% |
| `numpy` (`numpy==2.4.1`) | 46 / 200 KB | K256 | 0.65% (0.00 / 0.65, `bundle_byte:K256`) | K2048 | 0.15% (0.00 / 0.15, `exact_norm_p2:K3924`) | **0.65%** | 100KB | 1.38% |
| `python-pillow` (`pillow==12.1.0`) | 30 / 200 KB | K256 | 0.10% (0.00 / 0.10, `bundle_slot:K128`) | K2048 | 0.45% (0.00 / 0.45, `exact_norm_p2:K3072`) | **0.45%** | 100MB | 1.95% |
| `Textualize` (`rich==14.2.0`) | 41 / 200 KB | K256 | 0.20% (0.00 / 0.20, `bundle_slot:K512`) | K4096 | 1.82% (1.12 / 0.69, `exact_norm_p2:K3924`) | **1.82%** | 100MB | 1.85% |
| `scipy` (`scipy==1.17.0`) | 47 / 200 KB | K256 | 1.07% (0.64 / 0.43, `bundle_slot:K128`) | K2048 | 0.16% (0.00 / 0.16, `bpe:K2048`) | **1.07%** | 100KB | 0.99% |
| `sympy` (`sympy==1.14.0`) | 32 / 200 KB | K256 | 0.97% (0.48 / 0.49, `bundle_slot:K128`) | K2048 | 0.44% (0.00 / 0.44, `exact_norm_p2:K3924`) | **0.97%** | 100KB | 0.90% |

**Diagnostic takeaway from the decomposition:**
- At **100 MB**, the locked predictor hits the exact same-chain optimum (`K=2048`, **0.00% budget regret**) on **12 of 14** untouched organizations; most 100 MB full-oracle regret (up to 1.53% on `fsspec`, 1.29% on `aio-libs`, 1.02% on `fonttools`) is **irreducible chain-choice regret** where `exact_norm_p2` avoids `exact_closed`'s late-tail codeword widening.
- At **100 KB**, chain-choice regret is tiny (`0.00%` to `0.65%`), and the single 2.0% breach (`networkx`: `2.11%`) is pure **budget-choice regret** (`K=256` picked over `exact_closed:K64`) caused by micro-sketch sampling variance on `networkx`.

---

## 3. Complete Arm Comparison on the 14 Untouched Calibration Orgs (28 Queries)

| Arm | vs Same-Chain Oracle (med / p95 / max) | vs Full 7-Chain Oracle (med / p95 / max) | Fallback Rate | Eval-Only Wall s (p95 s) | Eval-Only Total Ops | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `locked_predictor_direct` | **0.00% / 1.08% / 2.11%** | **0.62% / 1.88% / 2.11%** | 0.0% (0/28) | 50.27 (3.75) | 56,870,999 | 132 MiB |
| `strict_conformal_2_0pct_bar` | 0.61% / 1.20% / 1.50% | **0.89% / 1.87% / 1.95%** | 100.0% (28/28) | 188.80 (14.42) | 208,446,017 | 132 MiB |
| `fixed_K512` | 1.51% / 3.49% / 4.29% | 1.95% / 4.29% / 5.50% | 0.0% | 42.83 (3.55) | 47,134,338 | 121 MiB |
| `fixed_K2048` | 8.65% / 19.75% / 20.11% | 9.45% / 19.94% / 20.28% | 0.0% | 55.15 (4.24) | 61,606,690 | 121 MiB |
| `fixed_K4096` | 24.25% / 51.13% / 51.67% | 24.47% / 51.44% / 51.90% | 0.0% | 63.67 (4.62) | 69,294,788 | 121 MiB |
| `pilot_3pt_geometric` | 0.61% / 1.20% / 1.50% | 0.89% / 1.87% / 1.95% | 0.0% | 186.05 (14.30) | 204,027,029 | 121 MiB |
| `same_chain_oracle` (10-pt grid) | 0.00% / 0.00% / 0.00% | 0.28% / 1.20% / 1.53% | 0.0% | 450.40 (34.60) | 497,284,604 | 121 MiB |
| `full_selector_by_K_oracle` (7 chains) | -0.28% / 0.00% / 0.00% | 0.00% / 0.00% / 0.00% | 0.0% | 2,809.79 (204.04) | 3,448,748,044 | 121 MiB |

*Note on Stage-1 LOLO-CV reference (6 predictor-fit orgs, 14 queries):* median `0.00%` / p95 `0.78%` vs same-chain, median `0.68%` / p95 `1.56%` / max `2.34%` vs full oracle. Explicitly labeled **diagnostic only — NOT valid for split-conformal coverage** (Barber et al., `arXiv:1905.02928`).

*Note on segregated in-distribution CodeNet strata (evaluated under exact locked predictor `03fc39cf87d2`, never used in fit/cal):* `codenet_fresh` @ 100 KB (`K=512`, +0.17% same / +6.12% full vs `exact_open`), @ 100 MB (`K=4096`, **0.00%** same / **+0.58%** full); `codenet_fresh2` @ 100 KB (`K=512`, **0.00%** same / +5.19% full), @ 100 MB (`K=4096`, **0.00%** same / **+0.92%** full).

---

## 4. Shared Spine Contract (`shared_spine`) & Compute Gate

All four `shared_spine` fields and C5/C6 compute gates are recorded in [dev_summary.json](dev_summary.json):
- **`fidelity`:** `1.0` across **1,610 / 1,610** serialized `B1RA` archives (**630** Stage-1 dev/diag + **980** Stage-2 calibration), independently decoded byte-for-byte via `independent_decode.py` (stdlib-only, zero encoder imports), **0 B accounting drift**, 100% random-access spot checks passed.
- **`complete_bits` (mean across 14 calibration orgs):**
  - At $M = 100\,000\text{ B}$: `locked_predictor_direct` = **480,034.10 bits**, `strict_conformal_2_0pct_bar` (pilot) = **481,698.61 bits**, `same_chain_oracle` = **477,644.62 bits**, `full_selector_by_K_oracle` = **476,756.39 bits**, `fixed_K512` = **484,565.34 bits**, `fixed_K2048` = **556,419.65 bits**, `fixed_K4096` = **699,115.65 bits**.
  - At $M = 100\,000\,000\text{ B}$: `locked_predictor_direct` = **433,195,976.57 bits**, `strict_conformal_2_0pct_bar` = **435,233,735.99 bits**, `same_chain_oracle` = **432,761,150.25 bits**, `full_selector_by_K_oracle` = **430,275,922.52 bits**, `fixed_K512` = **445,849,886.96 bits**, `fixed_K4096` = **439,405,747.82 bits**.
- **`measured_work`:** Full all-in + amortized breakdown including `shared_chain_build_sec = 279.902 s` and `all_7_chains_build_sec = 3,578.058 s` (Section 5).
- **`horizon` ($M^*$):** Primary horizons $M \in \{100\,000, 100\,000\,000\}\text{ B}$, diagnostic sweep $M \in [10^4, 10^9]\text{ B}$, and exact break-even $M^*$ per lineage (Section 6).
- **`compute_gate_policy`:** `C5_status = GATED_BEHIND_EXPLICIT_MODEL_COMPUTE_APPROVAL`, `C6_status = GATED_BEHIND_EXPLICIT_MODEL_COMPUTE_APPROVAL`, `gpu_compute_run = false`, `llm_compute_run = false`.

---

## 5. Honest All-In & Amortized Work Accounting (Fixing the `0.112x` Denominator Flaw)

### 5.1 Why the Earlier `0.112x` Figure Was Incomplete
The previous `0.112x` figure divided only per-query evaluation time (`policy_eval_sec`) by per-query same-chain grid evaluation time (`same_chain_grid_sec`), omitting the shared offline cost of building the deployed chain and fitting its `B1RA` prefix code tables (`shared_chain_build_sec`), and using only a 1-chain grid as denominator rather than the full 7-chain multi-chain grid.

### 5.2 Exact Measured Build & Per-Deployment Components

| Component | Exact Measured Seconds | Source / Provenance |
| --- | ---: | --- |
| Primary chain engine build (`exact_closed`) | 257.950 s | Verified footer of `closure-holdout-v1/out/bundle/pair-ext.txt` |
| Primary chain B1RA header fit (10 prefixes) | 21.949 s | Sum of measured `fit_work.wall_seconds` in `out/prefix_grid.json` |
| Stage-1 locked predictor fit (`out/locked_predictor.json`) | 0.002 s | Live measured `LockedHorizonPredictor.fit_and_lock()` |
| **`shared_chain_build_sec` (1 deployed chain total)** | **279.902 s** | Exact sum of the 3 build components above |
| All 7 chains engine build (`bpe` 13.50, `exact_closed` 257.95, `exact_byte` 594.54, `bundle_byte` 597.10, `exact_norm_p2` 634.74, `exact_open` 647.87, `bundle_slot` 746.00) | 3,491.700 s | Verified chain footers + `objective-holdout-v1/frozen/train-summary.json` |
| All 7 chains B1RA header fit (deduplicating shared `K=0`) | 86.358 s | Sum of measured `fit_work.wall_seconds` in `out/prefix_grid.json` |
| **`all_7_chains_build_sec` (full 7-chain build total)** | **3,578.058 s** | Exact sum of all 7 chain builds + all 7 header fits |
| Per-deployment `locked_predictor_direct` (cal-14 mean, ~188 KB/org) | 1.795 s / dep | Micro-sketch + prediction + 1 deployment encode |
| Per-deployment `strict_conformal` effective (100% pilot fallback) | 6.743 s / dep | Micro-sketch + 3-pt geometric pilot (with prefix reuse) |
| Per-deployment `same_chain_pilot` (cal-14 mean) | 6.645 s / dep | Frozen 3-pt geometric pilot (`K in {64, 512, 4096}`) |
| Per-deployment `same_chain_grid` (cal-14 mean) | 16.086 s / dep | All 10 grid prefixes on `exact_closed` |
| Per-deployment `all_7_chains_grid_eval` (cal-14 mean) | 100.350 s / dep | All 7 chains x eligible prefixes |

### 5.3 Single-Deployment ($N=1$) & Amortized ($N \in \{1, 2, 5, 10, 50\}$) All-In Work Ratios

**Calibration 14-Org Basis (~188 KB/org mean):**

| Mode | $N$ Deployments | Policy All-In s | Same-Chain Pilot All-In s | Same-Chain Grid All-In s | Full 7-Chain All-In s | Ratio vs Same-Chain Pilot | Ratio vs Same-Chain Grid | Ratio vs Full 7-Chain Grid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `locked_direct` | **1** | 281.70 | 286.55 | 295.99 | 3,678.41 | **0.9831x** | **0.9517x** | **0.0766x** |
| `locked_direct` | 2 | 283.49 | 293.19 | 312.07 | 3,778.76 | 0.9669x | 0.9084x | 0.0750x |
| `locked_direct` | 5 | 288.88 | 313.13 | 360.33 | 4,079.81 | 0.9226x | 0.8017x | 0.0708x |
| `locked_direct` | 10 | 297.86 | 346.35 | 440.76 | 4,581.55 | 0.8600x | 0.6758x | 0.0650x |
| `locked_direct` | 50 | 369.67 | 612.14 | 1,084.19 | 8,595.54 | 0.6039x | 0.3410x | 0.0430x |
| `strict_conformal` | **1** | 286.65 | 286.55 | 295.99 | 3,678.41 | **1.0003x** | **0.9684x** | **0.0779x** |
| `strict_conformal` | 2 | 293.39 | 293.19 | 312.07 | 3,778.76 | 1.0007x | 0.9401x | 0.0776x |
| `strict_conformal` | 5 | 313.62 | 313.13 | 360.33 | 4,079.81 | 1.0016x | 0.8704x | 0.0769x |
| `strict_conformal` | 10 | 347.33 | 346.35 | 440.76 | 4,581.55 | 1.0028x | 0.7880x | 0.0758x |
| `strict_conformal` | 50 | 617.05 | 612.14 | 1,084.19 | 8,595.54 | 1.0080x | 0.5691x | 0.0718x |

**Exact Break-Even Deployment Counts $N^*$ (reusing the single pre-built chain):**
- **`locked_predictor_direct` (cal-14 ~188 KB/org basis):**
  - Asymptotic ($N \to \infty$) eval-only ratios: **0.270x** vs same-chain pilot, **0.112x** vs same-chain grid, **0.018x** vs full 7-chain grid.
  - All-in break-even to cross `<= 1/2` of same-chain pilot: **`N* = 92`** deployments (or `N* = 95` on the larger ~549 KB Stage-1 dev cohort).
  - All-in break-even to cross `<= 1/6` of same-chain grid: **`N* = 264`** deployments (or `N* = 242` on the ~549 KB Stage-1 dev cohort).
  - All-in vs `full_multichain_grid`: already **0.0766x** (`<< 1/6`) at **`N = 1`**!
- **`strict_conformal_2_0pct_bar` (currently 100% pilot fallback because 2.11% > 2.00%):**
  - All-in vs `full_multichain_grid`: **0.0779x** (`<< 1/6`) at **`N = 1`**.
  - Break-even vs `1/2` same-chain pilot or `1/6` same-chain grid: **`None` (never)** while abstaining to the 3-point pilot (asymptotes `1.015x` pilot, `0.419x` same-chain grid).

---

## 6. Codeword Widening, Lower Envelope & Token/RAM Variant (14 Calibration Orgs)

### 6.1 Codeword Widening Replicates 100% (21 / 21 Non-CodeNet Codebases)
On **all 14 / 14** untouched calibration organizations (in addition to all 7 / 7 Stage-1 dev codebases), extending `exact_closed` from `K = 2048` to `K = 4096` causes non-monotonic tail degradation:
- Realized codewords widen by **+0.955 to +1.089 bits/token**.
- Coded body rate $\hat{r}_K$ *increases* by **+0.73% to +2.60%**, so $M^*(K=2048 \to K=4096) = \text{never}$ on every single out-of-distribution codebase (`21 / 21`), whereas in-distribution CodeNet keeps dropping (`-4.32%` / `-4.87%`, $M^* \approx 1.07\text{--}1.21\text{ MB}$).

### 6.2 Near-Tie Flatness ($\ge 4\times$-Separated Prefixes Within Tolerance)
Across the 14 untouched calibration orgs:
- Primary horizons (28 queries): **5 / 28 (17.9%)** within 0.5%, **14 / 28 (50.0%)** within 1.0% (primarily at 100 KB where `K=64` vs `K=256` or `K=128` vs `K=512` sit near the flat valley floor).
- Diagnostic 10-horizon sweep (140 queries): **7 / 140 (5.0%)** within 0.5%, **27 / 140 (19.3%)** within 1.0%.

### 6.3 Token / RAM Variant (Scored Separately on 14 Untouched Calibration Orgs)
Using the frozen deterministic deployment RAM model (`1,890 B` at `K=0` to `15,909 B` at `K=512`, `59,883 B` at `K=2048`, `119,710 B` at `K=4096`) and the locked token-rate bias fitted strictly on the 6 Stage-1 predictor-fit orgs:
- **Priced Token/RAM ($\lambda \in \{0.5, 0.05, 0.005\}$, 84 queries):**
  - `locked_token_policy`: **0.00% med / 0.13% p95 / 1.81% max** vs same-chain (**2.19% med / 3.14% p95** vs full 7-chain oracle).
  - `pilot_3pt_token`: 0.00% / 0.23% vs same-chain (2.20% / 3.22% vs full).
  - `fixed_K512`: 33.69% / 37.97% vs same-chain (36.87% / 40.84% vs full).
  - `fixed_K2048`: 8.51% / 19.55% vs same-chain (10.12% / 22.26% vs full).
  - `fixed_K4096`: 0.00% / 64.19% vs same-chain (2.26% / 67.93% vs full).
- **Hard RAM Caps (14 calibration orgs each):**
  - `16 KiB` cap ($K \le 512$): **0.00% med / 0.00% max** vs same-chain (**2.43% med / 3.67% p95** vs full).
  - `64 KiB` cap ($K \le 2048$): **0.00% med / 0.00% max** vs same-chain (**1.38% med / 2.39% p95** vs full).

---

## 7. Strict `dev_gate` & `replay.py` Verification Status

| Check | Status | Measured Evidence |
| --- | --- | --- |
| `replay.py check` zero-mutation guarantee | **PASS** | `git status --short` is empty both before and after `replay.py check` |
| 59-lineage + fit-org + reserved-domain disjointness | **PASS** | 14 calibration orgs verified 0-overlap against all 59 capacity corpora, fit/dev orgs, and 5 sealed domains; live `.venv` verified 416/416 files (0 mismatches) |
| Gate 1 (`independent_decode_100pct_fidelity`) | **PASS** | 1,610/1,610 grid archives (630 dev/diag + 980 calibration) + 5 live isolated-subprocess archives (`K=0,64,512,2048,4096`, 4 ESC bytes), 100% fidelity, 0 B drift |
| Gate 2 (`exhaustive_score_reproduction`) | **PASS** | `locked_predictor_sha256` verified; all 14 calibration orgs' `100KB`, `100MB`, `s_i = max(...)`, `rank k = 14/14`, `UPB = 2.1095%`, and 28 x 8 arm choices reproduced via exact `Fraction` enumeration |
| Gate 3 (`negative_control_corrupted_code_table`) | **PASS** | +1 Kraft underflow, -1 Kraft overflow, Kraft-preserving length swap all rejected; CLI exits 1 |
| Gate 4 (`negative_control_leakage_and_59_lineage_disjointness`) | **PASS** | Fit lineage/org/hash leaks, 3-way Stage-1->Stage-2 leak, within-repo resampling, capacity repos (`ggml`, `ajv`), and sealed domains (`yaml`, `sql`) all rejected |
| Gate 5 (`adversarial_synthetic_curves`) | **PASS** | Exact flat curve selects smallest header (`K=0` grid / `K=64` pilot); non-convex bad-intermediate bump escaped to `K=4096` by exhaustive, pilot, and sketch policy |
| Gate 6 (`abstain_and_end_to_end_shipping`) | **PASS** | Exact locked predictor (`03fc39cf87d2`) triggers honest `SWEEP_REQUIRED` -> 3-pt pilot fallback at 2.0% bar and passes full live B1RA encode + isolated `independent_decode.py` at 100 KB and 100 MB |
| `replay.py all` + `EMOJI.md` audit | **PASS** | `out/locked_predictor.json` reproduced byte-for-byte; `dev_summary.json` identical outside timings; RFC-8259 JSON valid; 0 emojis across all 15 files |

## Reproduction Commands

```bash
cd projects/algorithm_solver/literals/a1b-horizon-sizing-v1
/Users/xyz/deco/gamma/.venv/bin/python replay.py check                  # ~9s, never dirties tracked files
/Users/xyz/deco/gamma/.venv/bin/python replay.py check --report /tmp/a1b.json
/Users/xyz/deco/gamma/.venv/bin/python replay.py all                    # ~19s, full deterministic recomputation
```
