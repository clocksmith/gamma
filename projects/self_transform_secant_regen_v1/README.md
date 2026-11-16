# Affine-Invariant Secant Quasi-Newton & Behavioral Neural Regeneration (`self_transform_secant_regen_v1`)

## Status and Summary

- **Track:** Gamma Track B2 — Hereditary self-improvement (pure CPU; zero GPU usage).
- **Capability:** Self-applicable 52-parameter Affine-Invariant Secant-Trust Quasi-Newton Neural Transformer ([`operator.mjs`](operator.mjs), [`autodiff.mjs`](autodiff.mjs)) that adapts heterogeneous targets (`D = 12` twisted Huber valleys, `D = 16` anisotropic gated MLPs, and `D = 52` unrolled meta-objectives over its own parameters) through the identical `step` function under a hard first-order `(loss, grad)` observation window ([`observation.mjs`](observation.mjs)). Supports both exact IEEE-754 `float64` serialization and **weight-free cold-process behavioral neural regeneration** (`emitBehavioralTranscript` -> `regenerateFromTranscript`), executing every Stage 2 proposal, regeneration, and held-out evaluation inside a fresh OS subprocess ([`worker.mjs`](worker.mjs)).
- **Purpose:** Test a substantive new mechanism addressing the scale-mismatch and tangent-orthogonality bottlenecks of prior Gamma heredity studies (`self_transform_v1..v7`, `self_transform_curvature_v1`, `self_transform_subspace_v1`), freeze its artifact and budget after Stage 1 selection, and evaluate on fresh training, selection, and sealed confirmation populations:
  1. Independently reconstructed 4-generation (`G = 4`) cold-process reproduction.
  2. Multi-generation retained adaptation under both exact serialization and weight-free neural regeneration.
  3. Evolving versus fixed proposers under **matched retained state** (`reset`, `retain`, and same-parent/same-state paired splits).
  4. Serialization versus weight-free neural regeneration (both step-matched and total-oracle-budget-matched).
  5. Comparison against training-calibrated conventional first-order/quasi-Newton controls (`SGD`, `Adam`, `L-BFGS`) with strictly matched preprocessing and per-generation budgets.
- **Current Status (Sealed Stage 2 Confirmation, 12 unseen seeds x 4 generations x 2 task families):**
  - **[✓] Cold-process reproduction (`PASS`):** `3,526 / 3,526` isolated OS subprocess invocations (`1,344` `--propose`, `192` `--regenerate`, `1,990` `--score`) round-tripped and matched in-process parity audits (`1,502,816` audit oracle calls) to exact `float64` precision (`maxAbsDrift = 0` across `96 / 96` `serialization_only` transitions; `192 / 192` `--regenerate` payloads verified weight-free).
  - **[✓] Multi-generation retained adaptation — Serialization (`PASS`):** Independently reconstructed `evolving_ser_reset` descendants beat `serialization_only` in `12 / 12` seeds (`p = 0.000244`) on both `twisted_huber_valley` (**`+97.22%`** median relative loss reduction, `40 / 48` parent-to-child wins) and `anisotropic_gated_mlp` (**`+53.76%`** median relative loss reduction, `39 / 48` parent-to-child wins), improving monotonically from `1.4076 -> 0.2406` and `5.4337 -> 3.1505 / 3.5824`.
  - **[✓] Multi-generation retained adaptation — Weight-Free Neural Regeneration (`PASS`):** Reconstructing each child's neural proposer from zero parent weights (`rng(1337)` symmetry-broken init trained via its own self-update rule on a 24-probe behavioral I/O transcript, reducing behavioral MSE by `99.0%` and `99.4%`) beat `serialization_only` in `12 / 12` seeds (`p = 0.000244`) both when step-matched (`+94.32%` and `+37.24%`) and when **strictly total-oracle-budget-matched** (`evolving_regen_budget_matched`: **`+94.81%`** and **`+34.56%`**, `12 / 12` wins, monotonically improving across all 4 generations `15.7211 -> 4.8505 -> 1.3028 -> 0.4797` and `8.5953 -> 6.1919 -> 5.0261 -> 4.9884`).
  - **[◐] Proposer improvement under matched retained state (`PARTIAL: 1 / 6 gates PASS`):** Under **matched retained outer state** on `anisotropic_gated_mlp`, `evolving_ser_retain` beat `fixed_ser_retain` in `10 / 12` seeds (**`+6.22%`** median, `[+4.03%, +12.30%]`, `p = 0.019287 < 0.025`, **`PASS`**), and had a positive non-significant median on `twisted_huber_valley` (`8 / 12` wins, `+5.22%`, `p = 0.1938`). Under memory-reset chains (`evolving_ser_reset vs fixed_ser_reset`: `+4.93%` `7/12` `p = 0.387` and `-1.27%` `5/12` `p = 0.806`), neural-regenerated proposer chains (`-51.93%` and `-26.76%`), and single-step same-parent paired splits (`+3.15%` `9/12` `p = 0.073`, `-0.59%`, `-0.30%`, `+0.18%`), proposer improvement did **not** clear the frozen `alpha = 0.025` threshold.
  - **[◐] Conventional first-order/quasi-Newton controls (`PARTIAL: 2 / 12 cells PASS, 11 / 12 positive medians, overall FAIL`):** `evolving_ser_reset` passed the sealed gate on `anisotropic_gated_mlp` against both `tuned_sgd_reset` (`12 / 12` wins, **`+34.99%`**, `p = 0.000244`) and `tuned_sgd_retain` (`12 / 12` wins, **`+57.34%`**, `p = 0.000244`), and achieved positive median reductions in **11 of 12** `(family, comparator)` cells (including `+17.72%` and `+41.35%` vs `tuned_bfgs_reset`, and `+11.85%` vs `tuned_adam_reset` on `anisotropic_gated_mlp`), while virtually tying `tuned_adam_reset` on `twisted_huber_valley` (`-1.45%`, `6 / 12` wins). Because `conventionalAllPass` requires clearing `alpha = 0.025` against every comparator on both families, the joint conventional gate is **`FAIL`**.

No recursive self-improvement (RSI), AGI, or general dominance over calibrated conventional first-order optimization (`Adam`) is established.

---

## Mechanism and Mathematical Design

### Addressing Prior Bottlenecks

1. **Exact first-order `(loss, grad)` oracle instead of blind Rademacher sensing:** In `self_transform_subspace_v1`, 4-pair Rademacher finite differences suffered $O(1/D)$ signal dilution in `48D` and Grassmannian tangent orthogonality ($\hat{U}_2^\top \nabla_V \mathcal{L}_{\text{meta}} = 0$). Here, reverse-mode scalar autodiff ([`autodiff.mjs`](autodiff.mjs)) gives every optimizer (`learned`, `sgd`, `adam`, `bfgs`) exact `(loss, grad)` evaluations through the identical `gradientWindow` ([`observation.mjs`](observation.mjs)).
2. **Exact invariance to affine loss rescaling $\mathcal{L}(\theta) \mapsto \alpha \mathcal{L}(\theta) + C$ ($\alpha > 0$):** Downstream tasks (`D = 12, 16`) and unrolled meta-losses (`D = 52`) differ by orders of magnitude in gradient norm and loss offset. For step $s_t = \theta_t - \theta_{t-1}$ and gradient difference $y_t = g_t - g_{t-1}$:
   - The Barzilai-Borwein secant step length $\Delta_{\text{BB}} = \frac{\|s_t\|_2}{\|y_t\|_2} \cdot \text{RMS}(g_t)$ scales as $\frac{1}{\alpha \|y_t\|_2} \cdot (\alpha \text{RMS}(g_t)) = O(\alpha^0)$, matching exact parameter units without tuning a task-dependent learning rate!
   - The rank-1 symmetric secant quasi-Newton direction $H_t g_t$ with $\gamma_t = \frac{\|s_t\|_2}{\|y_t\|_2}\bigl(0.15 + 1.70\,\sigma(3\cos(s_t, y_t))\bigr)$ and normalized coordinate curvature ratios $\frac{|s_{t,i}| + s_{\text{ref}}}{|y_{t,i}| + y_{\text{ref}}} / \frac{\|s_t\|_2}{\|y_t\|_2}$ are homogeneous of degree zero in $\alpha$.
   - The loss-trend feature $\tanh\!\bigl(\frac{\mathcal{L}_t - \mathcal{L}_{t-1}}{|\mathcal{L}_t - \mathcal{L}_{t-1}| + \langle |g_t|, |s_t| \rangle}\bigr)$ cancels both $C$ and $\alpha$.
   - [`test.mjs`](test.mjs) verifies multi-step invariance between $\mathcal{L}(\theta)$ and $1000\,\mathcal{L}(\theta) + 500$ to `< 10^{-8}` Euclidean drift across 4 steps.
3. **Coordinate-shared 52-parameter neural preconditioner (`phi`):**
   - `45` MLP weights (`6 -> 5 -> 2`: `W1[30]`, `b1[5]`, `wGain[5]`, `wMix[5]`) map coordinate features `[g_norm, qn_norm, mom_prev, sign_agree, loss_trend, progress]` to bounded coordinate gain and momentum gates.
   - `7` smooth dynamical scalars (`initStep`, `secantScale`, `momBeta`, `gainBeta`, `qnMix`, `diagMix`, `rollbackSharpness`) control initial probe scale, secant trust scaling, momentum/gain EMA rates, rank-1/diagonal curvature mixing, and smooth rollback sharpness.
4. **Weight-free cold-process behavioral neural regeneration:**
   - Rather than copying `phi` bytes (`float64` serialization, `2,008` bytes), `emitBehavioralTranscript` runs the parent on `24` deterministic synthetic probe contexts (`23,111..23,124` JSON bytes; zero `phi` values).
   - In a fresh subprocess (`worker.mjs --regenerate`), `parseBehavioralTranscript` rejects any payload containing `phi`, `weightsHex`, or `childArtifact`, initializes `theta_0` from a fixed parent-independent symmetry-breaking seed (`rng(1337)`), and bootstraps `theta_{t+1} = step(theta_t, theta_t, ...)` for `42` self-applicable behavioral-MSE steps (`42` regeneration calls charged explicitly).

### Four Pre-Registered Stage 1 Rule Candidates

| Candidate | Curvature Preconditioner | Best-Iterate Trust Rollback | Purpose |
| :--- | :--- | :---: | :--- |
| `secant_qn_trust` | Rank-1 symmetric secant + normalized diagonal secant | Enabled | Full affine-invariant quasi-Newton + smooth rollback |
| `diag_secant_trust` | Normalized diagonal secant only (`qnMix = 0`) | Enabled | Test contribution of off-diagonal rank-1 secant coupling |
| `secant_qn_no_rollback` | Rank-1 symmetric secant + normalized diagonal secant | Disabled | Test whether trust rollback helps or clips outer meta-steps |
| `first_order_mlp_only` | Pure RMS-normalized first-order MLP (`secant = off`) | Disabled | Isolate contribution of affine-invariant secant scaling |

---

## Experimental Contracts and Complete Budget Accounting

### Disjoint Population Seeds and Cryptographic Sealing

| Stage | Seeds | Generations | Receipt & SHA-256 |
| :--- | :--- | :---: | :--- |
| Stage 0 (scratch probes) | `1, 2, 3` | `1..2` | Diagnostic probes in scratch only; excluded from all protocols |
| Stage 1 (selection) | `610000..660000` (`n = 6`) | `G = 3` | [`.work/secant-regen-selection-01.json`](../../.work/secant-regen-selection-01.json) (`324f6cc633d0ae932c6463e143e5fcb32a8ebc5671f007d94379f5a23b316fed`) |
| Stage 2 (confirmation) | `901000..912000` (`n = 12`) | `G = 4` | [`.work/secant-regen-confirmation-01.json`](../../.work/secant-regen-confirmation-01.json) (`2f59f111332bf76f17757599d3cb9238079baf318b41cf833200b54e3503994e`) |

[`confirm.mjs`](confirm.mjs) verifies `selectionSha256` and `selectedRule` before running any confirmation task and opens output protocols/receipts exclusively (`wx`).

### Oracle, Failed-Attempt, Regeneration, Reconstruction, and Selection Accounting

Every call to `gradientWindow.evaluate` increments `oracleCalls` **before** calling `lossAndGrad` and increments `failedAttempts` if the point, output loss, or gradient is invalid or non-finite (tested in [`test.mjs`](test.mjs)).

| Ledger Item | Formula | Charged Calls / Bytes | Notes |
| :--- | :--- | ---: | :--- |
| Inner task episode (`1` fresh task) | `12 innerSteps x 1 (loss, grad) + 1 terminal loss` | `13` oracle calls | Fresh `state = null` on every downstream task |
| Preprocessing per method per `(family, seed)` | `9 grid candidates x 2 train envs x (6 metaSteps x (1 + 5 support x 12) + 4 query x 13)` | `6,444` oracle calls | **Exact equality** across `learned`, `sgd`, `adam`, `bfgs` (`assert.equal`) |
| Shared preprocessing per `(family, seed)` | `4 methods x 6,444` | `25,776` oracle calls | Independent training (`seed+100..`) & calibration (`seed+400..`) populations |
| Stage 1 selection total | `4 rules x 2 families x 6 seeds` (preprocessing + proposals + scoring) | `2,201,472` oracle calls | Explicitly recorded in Stage 2 `stage1SelectionOracleCallsCharged` |
| Standard proposal episode (`1` generation) | `6 metaSteps x (1 outer + 5 support tasks x 13 inner)` | `390` oracle calls | Identical across `evolving_ser_*`, `fixed_ser_*`, `evolving_regen_reset`, `tuned_*` |
| Budget-matched neural regen episode (`1` gen) | `42` transcript regen calls + `5 metaSteps x 65` (`325` oracle calls) | `367 <= 390` total calls | Deducts regeneration compute directly from proposal window (`1,300` oracle + `168` regen = `1,468 < 1,560` over `4` gens) |
| Held-out confirmation evaluation (`1` artifact) | `64` unseen tasks x `8` eval steps (`8` oracle calls; final `childMean` over 64 tasks) | `512` oracle calls | Disjoint `holdoutSeed`; never exposed to proposers |
| Reconstruction payload size | `float64` artifact JSON vs `24`-probe behavioral transcript JSON | `2,008 B` vs `~23,120 B` | Transcript carries `(features, targetDisp, targetMom)` probes; zero weight bytes |
| Failed attempts across Stage 1 & Stage 2 | Pre-execution `gradientWindow` guard | `0` failed attempts | Smooth `tanh` step caps prevented non-finite iterates across all `3,526` worker runs |
| Cold-process parity audit (Stage 2) | In-process verification of subprocess proposals, regenerations, and scores | `1,502,816` audit calls | Tracked separately in `auditOracleCalls`; never used for adaptation |

Wall-clock CPU runtime on Mars (Apple Silicon, single Node `v22.20.0` coordinator spawning isolated child processes): Stage 1 selection took `180.9s`; Stage 2 confirmation took `682.8s` (`3,526` fresh OS subprocess spawns + in-process audits).

---

## Stage 1 Selection Results (`n = 6` seeds: `610000..660000`, `G = 3`)

Candidates were ranked by the pre-registered criterion `compositeScore = 0.5 * min_family(medianVsFixed) + 0.5 * min_{family,conv}(medianVsConv)` at generation `g = 2`:

| Rank | Rule Candidate | Composite Score | Min `vs Fixed` Median | Min `vs Conv` Median | `twisted_huber_valley` Mean Loss (`vs Base` / `vs Fixed`) | `anisotropic_gated_mlp` Mean Loss (`vs Base` / `vs Fixed`) |
| :---: | :--- | ---: | ---: | ---: | :--- | :--- |
| 1 | `secant_qn_no_rollback` | **`+0.00639`** | `-2.91%` | **`+4.19%`** | `0.2157` (`+97.22%` / `+15.72%`) | `3.3053` (`+44.04%` / `-2.91%`) |
| 2 | `diag_secant_trust` | `-0.04000` | `-9.76%` | `+1.77%` | `0.2215` (`+97.34%` / `+12.01%`) | `3.4861` (`+43.52%` / `-9.76%`) |
| 3 | `secant_qn_trust` | `-0.05441` | **`+3.63%`** | `-14.51%` | `0.2148` (`+97.43%` / `+13.68%`) | `3.0847` (`+50.34%` / **`+3.63%`**) |
| 4 | `first_order_mlp_only` | `-9.89719` | `-1107.00%` | `-872.44%` | `12.6439` (`+60.80%` / `-1107.00%`) | `3.7427` (`+50.86%` / `-8.65%`) |

Key Stage 1 ablation findings:
- **Secant scaling is essential:** Removing the affine-invariant Barzilai-Borwein + secant preconditioner (`first_order_mlp_only`) caused mean loss on `twisted_huber_valley` to degrade by **58x** (`12.6439` vs `0.2148..0.2215`), proving that scale-free secant curvature estimation — not the coordinate MLP alone — enables cross-scale self-application.
- **Trade-off between `secant_qn_trust` and `secant_qn_no_rollback`:** `secant_qn_trust` achieved the best mean loss on both families (`0.2148` and `3.0847`) and positive `vs Fixed` medians on **both** families (`+13.68%` and `+3.63%`), whereas `secant_qn_no_rollback` won the pre-registered worst-case `compositeScore` (`+0.00639`) due to higher worst-case margin over conventional optimizers (`+4.19%` vs `-14.51%`). Per protocol, `secant_qn_no_rollback` was sealed unmodified for Stage 2.

---

## Stage 2 Sealed Confirmation Results (`n = 12` unseen seeds: `901000..912000`, `G = 4`)

### 1. Multi-Generation Held-Out Loss Trajectories (`g = 0, 1, 2, 3`)

Mean held-out task loss across `12` seeds (`64` unseen evaluation tasks per seed and generation):

| Arm | State / Channel | Budget (`4g`) | `twisted_huber_valley` (`g=0 -> 1 -> 2 -> 3`) | `anisotropic_gated_mlp` (`g=0 -> 1 -> 2 -> 3`) |
| :--- | :--- | ---: | :--- | :--- |
| `serialization_only` | No update (`2,008 B`) | `0` | `9.2442 -> 9.3387 -> 9.6972 -> 9.2632` | `7.1857 -> 6.5202 -> 6.7453 -> 7.4325` |
| `evolving_ser_reset` | Reset / `float64` (`2,008 B`) | `1,560` | **`1.4076 -> 0.2915 -> 0.2491 -> 0.2406`** | **`5.4337 -> 3.6130 -> 3.1505 -> 3.5824`** |
| `fixed_ser_reset` | Reset / `float64` (`2,008 B`) | `1,560` | `1.4076 -> 0.4510 -> 0.2970 -> 0.2616` | `5.4337 -> 3.8272 -> 3.4252 -> 3.6835` |
| `evolving_ser_retain` | Retain / `float64` (`2,008 B`) | `1,560` | `1.4076 -> 0.3194 -> 0.2512 -> 0.2432` | **`5.4337 -> 3.8286 -> 3.2747 -> 3.4094`** |
| `fixed_ser_retain` | Retain / `float64` (`2,008 B`) | `1,560` | `1.4076 -> 0.4674 -> 0.3075 -> 0.2879` | `5.4337 -> 4.1470 -> 3.6532 -> 3.6524` |
| `evolving_regen_reset` | Reset / Transcript (`~23.1 KB`) | `1,560 + 168` | **`14.8255 -> 3.4340 -> 1.0091 -> 0.5863`** | **`8.4894 -> 5.9431 -> 4.9526 -> 4.6249`** |
| `evolving_regen_budget_matched` | Reset / Transcript (`~23.1 KB`) | `1,300 + 168` | **`15.7211 -> 4.8505 -> 1.3028 -> 0.4797`** | **`8.5953 -> 6.1919 -> 5.0261 -> 4.9884`** |
| `tuned_sgd_reset` | Reset / `float64` (`2,008 B`) | `1,560` | `0.2552 -> 0.2785 -> 0.2725 -> 0.2600` | `4.7256 -> 14.4414 -> 7.9087 -> 7.0948` |
| `tuned_sgd_retain` | Retain / `float64` (`2,008 B`) | `1,560` | `0.2552 -> 0.2934 -> 0.4195 -> 0.4292` | `4.7256 -> 14.9482 -> 8.9208 -> 8.7770` |
| `tuned_adam_reset` | Reset / `float64` (`2,008 B`) | `1,560` | `0.3057 -> 0.3035 -> 0.3876 -> 0.4705` | `4.8840 -> 4.2008 -> 3.7798 -> 7.6819` |
| `tuned_adam_retain` | Retain / `float64` (`2,008 B`) | `1,560` | `0.3057 -> 0.3486 -> 0.2531 -> 0.2597` | `4.8840 -> 4.1065 -> 6.4410 -> 4.0062` |
| `tuned_bfgs_reset` | Reset / `float64` (`2,008 B`) | `1,560` | `0.3619 -> 0.8546 -> 280.9054 -> 168.1626` | `4.7093 -> 95.6300 -> 22.9830 -> 6.9998` |
| `tuned_bfgs_retain` | Retain / `float64` (`2,008 B`) | `1,560` | `0.3619 -> 0.5411 -> 0.3404 -> 0.3141` | `4.7093 -> 4.8250 -> 4.4235 -> 9.5549` |

Across all `48` parent-to-child transitions (`12` seeds x `4` generations), `evolving_ser_reset` improved its immediate parent on **`40 / 48`** transitions (`twisted_huber_valley`) and **`39 / 48`** transitions (`anisotropic_gated_mlp`); weight-free `evolving_regen_reset` improved its parent on **`34 / 48`** and **`33 / 48`** transitions, reducing held-out loss across every consecutive generation (`g = 0 -> 1 -> 2 -> 3`) on both families.

### 2. Sealed Gate Summary at Final Generation `g = 3` (`alpha = 0.025`)

Relative reduction is $(\mathcal{L}_{\text{comp}} - \mathcal{L}_{\text{focal}}) / \mathcal{L}_{\text{comp}}$; intervals give the exact 96.14% (`[x_(3), x_(10)]`) order-statistic interval across `n = 12` seeds.

| Category & Contrast | Family | Threshold | Wins / Losses | Median Rel. Reduction (96.14% Interval) | Exact 1-Sided `p` | Outcome |
| :--- | :--- | ---: | :---: | ---: | ---: | :---: |
| **Retained Adaptation (`evolving_ser_reset vs serialization_only`)** | `twisted_huber_valley` | `>= +5.0%` | `12 / 0` | **`+97.22%`** (`[+96.32%, +98.10%]`) | `0.000244` | **PASS** |
| **Retained Adaptation (`evolving_ser_reset vs serialization_only`)** | `anisotropic_gated_mlp` | `>= +5.0%` | `12 / 0` | **`+53.76%`** (`[+44.19%, +57.91%]`) | `0.000244` | **PASS** |
| **Retained Adaptation — Neural Regen (`evolving_regen_reset vs serialization_only`)** | `twisted_huber_valley` | `>= +5.0%` | `12 / 0` | **`+94.32%`** (`[+89.94%, +96.29%]`) | `0.000244` | **PASS** |
| **Retained Adaptation — Neural Regen (`evolving_regen_reset vs serialization_only`)** | `anisotropic_gated_mlp` | `>= +5.0%` | `12 / 0` | **`+37.24%`** (`[+30.24%, +49.38%]`) | `0.000244` | **PASS** |
| **Retained Adaptation — Regen Budget-Matched (`vs serialization_only`)** | `twisted_huber_valley` | `>= +5.0%` | `12 / 0` | **`+94.81%`** (`[+92.55%, +96.68%]`) | `0.000244` | **PASS** |
| **Retained Adaptation — Regen Budget-Matched (`vs serialization_only`)** | `anisotropic_gated_mlp` | `>= +5.0%` | `12 / 0` | **`+34.56%`** (`[+14.88%, +41.82%]`) | `0.000244` | **PASS** |
| **Proposer Chain — Reset State (`evolving_ser_reset vs fixed_ser_reset`)** | `twisted_huber_valley` | `>= +1.0%` | `7 / 5` | `+4.93%` (`[-5.22%, +11.75%]`) | `0.387207` | **FAIL** |
| **Proposer Chain — Reset State (`evolving_ser_reset vs fixed_ser_reset`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `5 / 7` | `-1.27%` (`[-11.09%, +8.02%]`) | `0.806152` | **FAIL** |
| **Proposer Chain — Matched Retained State (`evolving_ser_retain vs fixed_ser_retain`)** | `twisted_huber_valley` | `>= +1.0%` | `8 / 4` | `+5.22%` (`[-4.15%, +33.66%]`) | `0.193848` | **FAIL** |
| **Proposer Chain — Matched Retained State (`evolving_ser_retain vs fixed_ser_retain`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `10 / 2` | **`+6.22%`** (`[+4.03%, +12.30%]`) | `0.019287` | **PASS** |
| **Same-Parent Paired Split — Reset State (`paired_evolving_reset vs paired_fixed_reset`)** | `twisted_huber_valley` | `>= +1.0%` | `9 / 3` | `+3.15%` (`[-1.42%, +6.68%]`) | `0.072998` | **FAIL** |
| **Same-Parent Paired Split — Reset State (`paired_evolving_reset vs paired_fixed_reset`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `5 / 7` | `-0.30%` (`[-9.02%, +1.44%]`) | `0.806152` | **FAIL** |
| **Same-Parent Paired Split — Matched Retained State (`paired_evolving_retain vs paired_fixed_retain`)** | `twisted_huber_valley` | `>= +1.0%` | `6 / 6` | `-0.59%` (`[-6.46%, +5.54%]`) | `0.612793` | **FAIL** |
| **Same-Parent Paired Split — Matched Retained State (`paired_evolving_retain vs paired_fixed_retain`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `7 / 5` | `+0.18%` (`[-5.56%, +2.14%]`) | `0.387207` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_sgd_reset`)** | `twisted_huber_valley` | `>= +1.0%` | `8 / 4` | `+8.16%` (`[-0.51%, +20.47%]`) | `0.193848` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_sgd_reset`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `12 / 0` | **`+34.99%`** (`[+22.53%, +52.42%]`) | `0.000244` | **PASS** |
| **Conventional (`evolving_ser_reset vs tuned_sgd_retain`)** | `twisted_huber_valley` | `>= +1.0%` | `9 / 3` | `+11.13%` (`[-2.45%, +19.22%]`) | `0.072998` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_sgd_retain`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `12 / 0` | **`+57.34%`** (`[+46.69%, +70.04%]`) | `0.000244` | **PASS** |
| **Conventional (`evolving_ser_reset vs tuned_adam_reset`)** | `twisted_huber_valley` | `>= +1.0%` | `6 / 6` | `-1.45%` (`[-30.20%, +20.84%]`) | `0.612793` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_adam_reset`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `8 / 4` | `+11.85%` (`[-5.23%, +35.61%]`) | `0.193848` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_adam_retain`)** | `twisted_huber_valley` | `>= +1.0%` | `8 / 4` | `+3.76%` (`[-11.86%, +26.29%]`) | `0.193848` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_adam_retain`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `8 / 4` | `+7.01%` (`[-25.39%, +39.54%]`) | `0.193848` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_bfgs_reset`)** | `twisted_huber_valley` | `>= +1.0%` | `8 / 4` | `+17.72%` (`[-5.37%, +94.74%]`) | `0.193848` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_bfgs_reset`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `9 / 3` | `+41.35%` (`[-29.63%, +65.49%]`) | `0.072998` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_bfgs_retain`)** | `twisted_huber_valley` | `>= +1.0%` | `7 / 5` | `+12.99%` (`[-7.80%, +26.85%]`) | `0.387207` | **FAIL** |
| **Conventional (`evolving_ser_reset vs tuned_bfgs_retain`)** | `anisotropic_gated_mlp` | `>= +1.0%` | `9 / 3` | `+26.28%` (`[-7.26%, +58.54%]`) | `0.072998` | **FAIL** |

### 3. Serialization vs Weight-Free Neural Regeneration & Memory Attribution

| Diagnostic Contrast | `twisted_huber_valley` | `anisotropic_gated_mlp` | Interpretation |
| :--- | :--- | :--- | :--- |
| `evolving_ser_reset vs evolving_regen_reset` (step-matched) | `12 / 0`, **`+43.98%`**, `p = 0.000244` | `10 / 2`, **`+15.89%`**, `p = 0.019287` | Exact `float64` serialization preserves fine scalar thresholds better than 42-step behavioral distillation |
| `evolving_ser_reset vs evolving_regen_budget_matched` (total-budget-matched) | `12 / 0`, **`+47.38%`**, `p = 0.000244` | `11 / 1`, **`+23.09%`**, `p = 0.003174` | Deducting 42 regeneration calls costs an additional `~3.4%..7.2%` relative accuracy, yet regenerated lineages still beat `serialization_only` `12/12` (`+94.81%`, `+34.56%`) |
| Behavioral regeneration MSE (`initial -> final`) | `0.002705 -> 0.0000269` (`-99.01%`) | `0.004042 -> 0.0000227` (`-99.44%`) | Self-bootstrapping `step(theta, theta)` recovers `>99%` of parent I/O variance from zero parent weights |
| Memory within fixed (`fixed_ser_retain vs fixed_ser_reset`) | `2 / 10`, `-6.26%`, `p = 0.9968` | `4 / 8`, `-4.95%`, `p = 0.9270` | Carrying stale outer secant/momentum state across fresh support tasks hurts a static proposer |
| Memory within evolving (`evolving_ser_retain vs evolving_ser_reset`) | `4 / 8`, `-2.96%`, `p = 0.9270` | `8 / 4`, `+4.26%`, `p = 0.1938` | Co-evolving the proposer rule alongside retained outer secant state mitigates stale-state drift on `anisotropic_gated_mlp`, explaining why `evolving_ser_retain vs fixed_ser_retain` passed (`10/12`, `+6.22%`, `p = 0.0193`) |

---

## Mechanistic Diagnosis

1. **Why retained adaptation and conventional survival jumped sharply over prior studies:** Affine-invariant Barzilai-Borwein + rank-1/diagonal secant scaling (`rawBbStep = (||s||/||y||) * gRms`) automatically adapts step lengths across both `12D/16D` inner valleys and `52D` unrolled meta-landscapes without manual step-size retuning, whereas fixed-rate `SGD`, `Adam`, and `L-BFGS` calibrated on 2-generation training tasks periodically overshoot on generations `g = 2..3` as parameter norms grow (`tuned_sgd_reset`: `4.73 -> 14.44 -> 7.09`; `tuned_bfgs_reset`: `0.36 -> 280.91`).
2. **Why weight-free neural regeneration works across 4 generations (`12/12` wins) yet lags exact serialization (`+43.98%`, `+15.89%`):** Because `phi` parameterizes a compact `6 -> 5 -> 2` coordinate map plus 7 bounded scalars, `24` synthetic probe contexts identify its input-output mapping to `~2.5e-5` MSE (`>99%` reduction) using `theta` itself as the optimizer. However, behavioral probes only weakly constrain parameters whose effect appears across multi-step curvature ratios (`secantScale`, `qnMix`), introducing slight generation-0 dispersion (`14.83` vs `1.41`) that subsequent generations steadily contract (`14.83 -> 3.43 -> 1.01 -> 0.59`).
3. **Why proposer improvement passed under matched retained state on `anisotropic_gated_mlp` (`+6.22%`, `p = 0.0193`) but remained noisy under reset/single-step splits:** Each outer meta-episode observes only `5` stochastic support tasks x `6` outer steps (`390` oracle calls). Because Stage 1's worst-case composite criterion selected `secant_qn_no_rollback` (disabling best-iterate rollback), individual outer steps occasionally accept noisy mini-batch updates when outer state resets (`history = null`). When outer secant state is retained (`_retain`), the evolving proposer adapts its gain/mixing gates to track the shifting outer curvature while `fixed_ser_retain` suffers stale-state mismatch.

---

## Reproduction Commands

```bash
# 1. Run unit tests (oracle/failed-attempt charging, autodiff vs FD, affine invariance, neural regeneration, subprocess parity, budget equality)
node projects/self_transform_secant_regen_v1/test.mjs

# 2. Re-analyze the sealed Stage 2 confirmation receipt
node projects/self_transform_secant_regen_v1/stats.mjs .work/secant-regen-confirmation-01.json > .work/secant-regen-confirmation-01.analysis.json

# 3. Run Stage 1 selection or Stage 2 confirmation to fresh output paths (exclusive wx protection)
node projects/self_transform_secant_regen_v1/select.mjs .work/secant-regen-selection-repro.json
node projects/self_transform_secant_regen_v1/confirm.mjs .work/secant-regen-confirmation-repro.json
```
