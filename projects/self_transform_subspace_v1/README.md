# Scale-Homogeneous Active-Subspace Self-Transformation (`self_transform_subspace_v1`)

## Status and Summary

- **Track:** Gamma Track B — Hereditary self-improvement (pure CPU; zero GPU usage).
- **Capability:** Self-applicable 48-parameter (`3 x 16`) zero-order weight transformer (`step` in [`operator.mjs`](operator.mjs)) that updates width-16 downstream task blocks (`M = 1`, `M = 2`) and its own serialized parameter blocks (`M = 3`) through the identical code path under a hard 8-scalar-query-per-step black-box oracle ([`observation.mjs`](observation.mjs)), reconstructing every confirmation child and held-out evaluation inside a fresh OS subprocess ([`worker.mjs`](worker.mjs)).
- **Purpose:** Test whether combining **scale-homogeneous per-block RMS normalization** with a **learned low-rank active probing subspace** $\hat{U}_2(\Phi) \subset \mathbb{R}^{16}$ produces (1) exact cold-process reproduction, (2) retained downstream adaptation on fresh tasks, (3) genuine proposer improvement separated from retained optimizer memory, and (4) an advantage over budget-matched training-calibrated zero-order optimizers (`SPSA`, `Adam`, `L-BFGS`) under separately frozen selection and confirmation protocols.
- **Current Status (Sealed Stage 2 Confirmation, 12 unseen seeds x 2 task families):**
  - **[✓] Cold-process reproduction (`PASS`):** `2,016 / 2,016` clean OS subprocess roundtrips (`864` `--propose`, `1,152` `--score`) and `2,016 / 2,016` direct in-process parity audits matched to exact IEEE-754 `float64` + SHA-256 (`0` drift across `72 / 72` `serialization_only` transitions).
  - **[✓] Retained fresh-task adaptation (`PASS`):** Independently reconstructed `hereditary_reset` descendants (with `history = null`, zero retained optimizer memory) beat `serialization_only` in `12 / 12` seeds (`p = 0.000244`) on both `subspace_logistic` (**`+21.26%`** median relative loss reduction) and `gated_bilinear` (**`+32.85%`** median relative loss reduction), lifting latent subspace overlap $\frac{1}{2}\|\hat{U}_2^\top U_{\text{env}}\|_F^2$ from random chance (`0.124` / `0.130`) to **`0.472`** / **`0.430`**.
  - **[✗] Proposer improvement (`FAIL`):** Despite `+2.94%` and `+6.23%` median gains over `fixed_reset` during Stage 1 selection (`n = 6` seeds), sealed Stage 2 confirmation (`n = 12` unseen seeds) found no proposer advantage either across the 3-generation memory-reset chain (`-0.01%`, `6/12` wins, `p = 0.613` on `subspace_logistic`; `-2.16%`, `5/12` wins, `p = 0.806` on `gated_bilinear`) or in the same-parent paired proposer split (`-0.75%`, `4/12` wins, `p = 0.927`; `-2.23%`, `5/12` wins, `p = 0.806`).
  - **[✗] Overall conventional optimizer gate (`FAIL`, `2 / 5` comparators passed):** `hereditary_reset` passed the sealed gate against noisy secant quasi-Newton baselines on both families (`tuned_bfgs_reset`: `10/12` wins, `p = 0.0193`, `+7.86%` and `+14.75%` medians; `tuned_bfgs_retain`: `11/12` wins, `p = 0.00317`, `+26.47%` and `+15.26%` medians) and had positive non-significant medians against `tuned_adam_reset` / `tuned_adam_retain` (`+1.30%` to `+10.49%`, `p = 0.194..0.387`), but failed against isotropic `tuned_spsa_reset` (`-2.75%`, `3/12` wins on `subspace_logistic`; `+0.04%`, `6/12` wins on `gated_bilinear`).

No recursive self-improvement (RSI), AGI, or general advantage over calibrated conventional zero-order optimization is established.

---

## Hypothesis and Operator Design

### Motivation from Prior Studies

Earlier Gamma heredity experiments (`self_transform_v1`..`v7`, `self_transform_curvature_v1`) stalled for three concrete reasons:

1. **Passive isotropic sensing:** Under an 8-query scalar window, isotropic Rademacher perturbations spend $(B - r)/B$ of their directional energy on nuisance dimensions when tasks share a rank-$r$ latent feature subspace.
2. **Cross-level scale mismatch:** Inner task losses and outer unrolled meta-losses differ by orders of magnitude in gradient scale; unnormalized step caps starved self-updates relative to rate-calibrated conventional baselines.
3. **Unmatched preprocessing budgets:** Prior curvature calibration spent ~27x more scalar queries tuning `Adam`/`L-BFGS` hyperparameters than selecting the initial learned rule.

### Unified Block Representation and Scale-Homogeneous Rule

Every optimization target $\Theta \in \mathbb{R}^{M \times 16}$ is partitioned into $M$ width-16 blocks ($B = 16$):

- `subspace_logistic` task weights: $M = 1$ ($D = 16$).
- `gated_bilinear` task weights: $M = 2$ ($D = 32$, $\hat{y}(x) = \tanh(w_1^\top x)(w_2^\top x)$).
- Self-applicable updater weights $\Phi = [v_1; v_2; c]$: $M = 3$ ($D = 48$), where $v_1, v_2 \in \mathbb{R}^{16}$ define an orthonormal 2D probing/preconditioning frame $\hat{U}_2(\Phi) = [u_1, u_2] = \text{GS}(v_1, v_2)$ and $c \in \mathbb{R}^{16}$ encodes smooth bounded dynamical scalars (`baseEta`, `activeBoost1`, `activeBoost2`, `orthoGain`, `rmsBeta`, `momBeta`, `stepDecay`, `relFloor`, `probeRadius`).

Each call to `step` consumes **4 antithetic finite-difference pairs = 8 scalar loss queries** through `observationWindow(limit = 8)` with zero target-identity branching:

1. **Directional probing and active-subspace preconditioning:** Four unit/complement directions $d^{(k)} \in \mathbb{R}^D$ yield central slopes $s_k = (\mathcal{L}(\Theta + r d^{(k)}) - \mathcal{L}(\Theta - r d^{(k)})) / (2r)$, forming raw block gradient estimates $\hat{g}$ and subspace-boosted preconditioned estimates $\tilde{g}$ (`activeBoost1`, `activeBoost2` along $u_1, u_2$; `orthoGain` on $\hat{U}_2^\perp$).
2. **Scale-homogeneous per-block RMS normalization:** Each block $m \in \{0, \dots, M-1\}$ tracks an exponential moving square average $\nu_m$ and first-touch scale $\nu_{m,0}$, normalizing by $\max(\hat{\nu}_m, \text{relFloor} \cdot \nu_{m,0}) + 10^{-12}$. Multiplying any objective $\mathcal{L}$ by $10^{-3}$ or $10^{3}$ leaves single-step updates invariant up to floating-point rounding (`1e-12` guard, verified in [`test.mjs`](test.mjs)).
3. **Smooth step annealing and norm cap:** Block-normalized momentum updates are scaled by $\eta_0 / \sqrt{1 + \gamma s}$ and smoothly bounded via $C^\infty$ hyperbolic tangent capping $c(\Theta)\tanh(\|\Delta\| / c(\Theta)) \frac{\Delta}{\|\Delta\|}$ with $c(\Theta) = 0.5(1 + \|\Theta\|_2)$, avoiding piecewise acceptance kinks in unrolled meta-objectives.

Four candidate probing topologies were frozen in [`protocol.selection.json`](protocol.selection.json) before Stage 1 execution:

- `block_subspace_2mode`: Cyclic single-block probing (`m = (4s + k) mod M`) allocating 2 probes along $u_1, u_2$ and 2 in $\hat{U}_2^\perp$.
- `block_subspace_1mode`: Cyclic single-block probing allocating 1 probe along $u_1$ and 3 in $u_1^\perp$.
- `kronecker_subspace_2mode`: Simultaneous multi-block Kronecker Rademacher row signs $\sigma_m \in \{\pm 1\}$ tensor-multiplied with $u_1$ (`k=0`), $u_2$ (`k=1`), and two $\hat{U}_2^\perp$ Rademacher projections (`k=2, 3`), while preserving independent per-block RMS normalization.
- `isotropic_homog_ablation`: Identical scale-homogeneous per-block RMS, momentum, schedule, and smooth cap, but replacing $\hat{U}_2$ probing/boosting with isotropic Rademacher probes (`modeGain = 1`).

---

## Experimental Contracts and Budget Accounting

### Disjoint Seed Partitions and Cryptographic Sealing

| Stage | Seeds | Purpose | Receipt & Binding |
| :--- | :--- | :--- | :--- |
| Stage 0 (smoke) | `1, 2, 3` | Mathematical sanity & scale-homogeneity debugging before freezing selection | Scratch only; excluded from all protocols |
| Stage 1 (selection) | `510000..560000` (`n = 6`) | Rank the 4 pre-registered rule candidates across both task families | `.work/subspace-selection-01.json` (`SHA-256: 70ee54f5df411c5dccf36e1cc21abb2f9575e5983afd738a108dac318d4c4be6`) |
| Stage 2 (confirmation) | `801000..812000` (`n = 12`) | Single-shot subprocess-isolated evaluation of sealed Stage 1 winner | `.work/subspace-confirmation-01.json` (`SHA-256: c64f2d1f18876ebfdd44225c2054b396bbb8f19b6ea5a42ac26c7eba45926ec9`) |

[`confirm.mjs`](confirm.mjs) verifies the Stage 1 receipt SHA-256 and `selectedRule` before running any seed and writes `.protocol.json` and receipt outputs with exclusive `wx` flags.

### Exact Scalar-Query Parity

| Phase | Formula | Scalar Queries | Notes |
| :--- | :--- | ---: | :--- |
| Inner task evaluation (1 task) | `8 innerSteps x 8 queries + 1 terminal loss` | `65` | Fresh `history = null` on every task |
| Preprocessing per method per `(family, seed)` | `9 candidates x 2 envs x (9 metaSteps x 8 outer x (4 support x 65) + 4 query x 65)` | `342,936` | **Exact equality** across `learned`, `spsa`, `adam`, and `bfgs` (verified by `assert.equal`) |
| Total shared preprocessing per `(family, seed)` | `4 x 342,936` | `1,371,744` | Executed on independent pretraining (`seed+100..`) and calibration (`seed+400..`) environments |
| Proposal episode per generation (`hereditary_*`, `fixed_*`, `tuned_*`) | `9 metaSteps x 8 outer queries x (1 + 6 support x 65)` | `28,152` | `72` outer meta-loss queries; `0` queries for `serialization_only` |
| Held-out scoring per artifact (Confirmation) | `64 fresh holdout tasks x 65` | `4,160` | Disjoint `holdoutSeed`; never exposed to proposals |
| Direct-vs-worker parity audit (Confirmation total) | In-process re-execution of every worker `--propose` and `--score` call | `26,413,056` | Tracked in `auditBudgetScalarQueries`; never used for selection or adaptation |

Wall-clock execution on Apple Silicon CPU (Node `v22+`, single process): Stage 1 selection took `327.37s` across 4 candidates (`6` seeds x `2` families); Stage 2 confirmation took `414.53s` (`~4.86s` preprocessing per `(family, seed)` plus `2,016` isolated `node worker.mjs` OS subprocess spawns and full in-process parity verification).

---

## Stage 1 Selection Results (`n = 6` seeds: `510000..560000`)

Candidates were ranked by the pre-registered worst-case criterion `compositeScore = 0.5 * min_family(medianVsFixed) + 0.5 * min_{family,conv}(medianVsConv)` at generation `g = 2`:

| Rank | Candidate Rule | Composite Score | Min Proposer Median (`vs fixed`) | Min Conv Median | `subspace_logistic` Overlap / `vs base` / `vs fixed` | `gated_bilinear` Overlap / `vs base` / `vs fixed` |
| :---: | :--- | ---: | ---: | ---: | :--- | :--- |
| 1 | `kronecker_subspace_2mode` | **`+0.00455`** | **`+2.94%`** | `-2.03%` | `0.474` / `+21.23%` / `+2.94%` | `0.421` / `+37.99%` / `+6.23%` |
| 2 | `isotropic_homog_ablation` | `-0.00127` | `-0.08%` | `-0.18%` | `0.081` / `+5.33%` / `-0.08%` | `0.118` / `+12.34%` / `+0.03%` |
| 3 | `block_subspace_1mode` | `-0.01688` | `-1.08%` | `-2.29%` | `0.281` / `+20.23%` / `-0.03%` | `0.114` / `+15.43%` / `-1.08%` |
| 4 | `block_subspace_2mode` | `-0.09426` | `-8.52%` | `-10.34%` | `0.293` / `+16.56%` / `-1.36%` | `0.160` / `+23.58%` / `-8.52%` |

Stage 1 ablation takeaways:
- `kronecker_subspace_2mode` outperformed cyclic single-block probing (`block_subspace_2mode`) because Kronecker sign-tensor probes sense all $M$ blocks on every finite-difference pair (`4` directional measurements per block per step instead of `4/3`) while per-block RMS normalization still prevents gradient-scale crosstalk across blocks.
- `isotropic_homog_ablation` kept latent subspace overlap at random chance (`0.081`, `0.118` vs `2/16 = 0.125`) and reduced retained adaptation from `+21.23% / +37.99%` down to `+5.33% / +12.34%`, confirming that the learned subspace frame $\hat{U}_2(\Phi)$ drives the task-adaptation gain.
- `kronecker_subspace_2mode` was sealed in [`protocol.confirmation.json`](protocol.confirmation.json) without modifying any operator or task code.

---

## Stage 2 Sealed Confirmation Results (`n = 12` unseen seeds: `801000..812000`)

### 1. Cold-Process Reproduction Gate (`PASS`)

- `workerProposalCount`: `864 / 864` clean OS subprocess `--propose` executions round-tripped `childArtifact` and `historyArtifact` (`float64` hex + SHA-256) with zero bit drift and matched in-process `proposeSuccessor` outputs identically.
- `workerScoreCount`: `1,152 / 1,152` clean OS subprocess `--score` executions round-tripped `artifact` and matched in-process held-out task loss vectors identically.
- `serializationOnlyChecks`: `72 / 72` (`3` generations x `12` seeds x `2` families) produced `maxAbsDrift = 0`.

### 2. Generation-by-Generation Progression (Mean Held-Out Loss and Subspace Overlap)

Random 2D subspace overlap in $\mathbb{R}^{16}$ has expectation $2/16 = 0.125$ (`initialMean = 0.1243` on `subspace_logistic`, `0.1298` on `gated_bilinear`).

| Family & Metric | Gen | `serialization_only` | `hereditary_reset` | `fixed_reset` | `hereditary_retain` | `tuned_spsa_reset` | `tuned_adam_reset` | `tuned_bfgs_reset` |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `subspace_logistic` loss | `g=0` | `0.4069` | `0.3661` | `0.3661` | `0.3661` | `0.3302` | `0.3393` | `0.3461` |
| `subspace_logistic` loss | `g=1` | `0.4050` | `0.3309` | `0.3339` | `0.3329` | `0.3167` | `0.3246` | `0.3697` |
| `subspace_logistic` loss | `g=2` | `0.4036` | `0.3144` | `0.3125` | `0.3160` | `0.3055` | `0.3203` | `0.3770` |
| `subspace_logistic` overlap | `g=0->2` | `0.124 -> 0.124` | `0.275 -> 0.472` | `0.275 -> 0.506` | `0.275 -> 0.506` | `0.393 -> 0.546` | `0.348 -> 0.436` | `0.279 -> 0.318` |
| `gated_bilinear` loss | `g=0` | `0.9565` | `0.7273` | `0.7273` | `0.7273` | `0.6891` | `0.7735` | `0.7794` |
| `gated_bilinear` loss | `g=1` | `0.9692` | `0.6461` | `0.6555` | `0.6435` | `0.6828` | `0.6869` | `0.7973` |
| `gated_bilinear` loss | `g=2` | `0.9784` | `0.6516` | `0.6421` | `0.6655` | `0.6642` | `0.6869` | `0.7894` |
| `gated_bilinear` overlap | `g=0->2` | `0.130 -> 0.130` | `0.349 -> 0.430` | `0.349 -> 0.445` | `0.349 -> 0.401` | `0.366 -> 0.407` | `0.278 -> 0.341` | `0.242 -> 0.243` |

Across all `36` parent-to-child transitions (`12` seeds x `3` generations), `hereditary_reset` improved its own parent on `35 / 36` transitions in `subspace_logistic` and `28 / 36` transitions in `gated_bilinear`.

### 3. Primary Sealed Gate Evaluations (`hereditary_reset` at `g = 2`, `alpha = 0.025`)

Relative loss reduction is $(\mathcal{L}_{\text{comp}} - \mathcal{L}_{\text{hered}}) / \mathcal{L}_{\text{comp}}$; positive values favor `hereditary_reset`. Intervals report the exact 96.14% (`[x_(3), x_(10)]`) order-statistic interval for the population median across `n = 12` seeds.

| Gate / Contrast | Family | Threshold | Wins / Losses | Median Rel. Reduction (96.14% Interval) | Exact 1-Sided Sign `p` | Outcome |
| :--- | :--- | ---: | :---: | ---: | ---: | :---: |
| **Retained Adaptation** (`vs serialization_only`) | `subspace_logistic` | `>= +5.0%` | `12 / 0` | **`+21.26%`** (`[+17.50%, +23.44%]`) | `0.000244` | **PASS** |
| **Retained Adaptation** (`vs serialization_only`) | `gated_bilinear` | `>= +5.0%` | `12 / 0` | **`+32.85%`** (`[+24.27%, +42.36%]`) | `0.000244` | **PASS** |
| **Proposer Chain (Rule Only)** (`vs fixed_reset`) | `subspace_logistic` | `>= +1.0%` | `6 / 6` | `-0.01%` (`[-2.55%, +2.04%]`) | `0.612793` | **FAIL** |
| **Proposer Chain (Rule Only)** (`vs fixed_reset`) | `gated_bilinear` | `>= +1.0%` | `5 / 7` | `-2.16%` (`[-18.44%, +16.07%]`) | `0.806152` | **FAIL** |
| **Same-Parent Paired Proposer** (`paired_self vs paired_fixed`) | `subspace_logistic` | `>= +1.0%` | `4 / 8` | `-0.75%` (`[-1.52%, +0.32%]`) | `0.927002` | **FAIL** |
| **Same-Parent Paired Proposer** (`paired_self vs paired_fixed`) | `gated_bilinear` | `>= +1.0%` | `5 / 7` | `-2.23%` (`[-8.57%, +10.62%]`) | `0.806152` | **FAIL** |
| **Conventional:** `vs tuned_spsa_reset` | `subspace_logistic` | `>= +1.0%` | `3 / 9` | `-2.75%` (`[-6.43%, +0.77%]`) | `0.980713` | **FAIL** |
| **Conventional:** `vs tuned_spsa_reset` | `gated_bilinear` | `>= +1.0%` | `6 / 6` | `+0.04%` (`[-4.82%, +10.49%]`) | `0.612793` | **FAIL** |
| **Conventional:** `vs tuned_adam_reset` | `subspace_logistic` | `>= +1.0%` | `7 / 5` | `+4.36%` (`[-4.16%, +5.78%]`) | `0.387207` | **FAIL** |
| **Conventional:** `vs tuned_adam_reset` | `gated_bilinear` | `>= +1.0%` | `8 / 4` | `+9.06%` (`[-16.82%, +20.03%]`) | `0.193848` | **FAIL** |
| **Conventional:** `vs tuned_adam_retain` | `subspace_logistic` | `>= +1.0%` | `8 / 4` | `+1.30%` (`[-0.71%, +3.39%]`) | `0.193848` | **FAIL** |
| **Conventional:** `vs tuned_adam_retain` | `gated_bilinear` | `>= +1.0%` | `8 / 4` | `+10.49%` (`[-15.76%, +19.25%]`) | `0.193848` | **FAIL** |
| **Conventional:** `vs tuned_bfgs_reset` | `subspace_logistic` | `>= +1.0%` | `10 / 2` | **`+7.86%`** (`[+3.72%, +30.18%]`) | `0.019287` | **PASS** |
| **Conventional:** `vs tuned_bfgs_reset` | `gated_bilinear` | `>= +1.0%` | `10 / 2` | **`+14.75%`** (`[+2.17%, +25.54%]`) | `0.019287` | **PASS** |
| **Conventional:** `vs tuned_bfgs_retain` | `subspace_logistic` | `>= +1.0%` | `11 / 1` | **`+26.47%`** (`[+8.90%, +43.90%]`) | `0.003174` | **PASS** |
| **Conventional:** `vs tuned_bfgs_retain` | `gated_bilinear` | `>= +1.0%` | `11 / 1` | **`+15.26%`** (`[+6.40%, +42.21%]`) | `0.003174` | **PASS** |

### 4. Separation of Retained Optimizer Memory from Evolved Update Rules

Both the $2 \times 2$ outer-memory factorial (`reset` vs `retain` $\times$ `fixed` vs `hereditary`) and the same-parent paired proposer split (`paired_*` starting from the identical final `hereditary_reset` artifact $\Phi_3$ with `history = null`) isolate update-rule changes from carried episode state:

| Attribution Contrast | `subspace_logistic` (Wins/Losses, Median, `p`) | `gated_bilinear` (Wins/Losses, Median, `p`) | Interpretation |
| :--- | :--- | :--- | :--- |
| Memory effect within `fixed` (`fixed_retain vs fixed_reset`) | `4 / 8`, `-0.59%`, `p = 0.927` | `7 / 5`, `+1.86%`, `p = 0.387` | Carrying outer momentum/RMS for a fixed proposer is near-neutral |
| Memory effect within `hereditary` (`hereditary_retain vs hereditary_reset`) | `7 / 5`, `+0.47%`, `p = 0.387` | `5 / 7`, `-5.35%`, `p = 0.806` | Carrying stale outer state while the proposer's subspace rotates degrades non-convex meta-steps |
| Rule effect within retained memory (`hereditary_retain vs fixed_retain`) | `8 / 4`, `+0.50%`, `p = 0.194` | `3 / 9`, `-5.77%`, `p = 0.981` | Negative interaction between rotating proposer basis and retained outer momentum |
| Same-parent continuation (`paired_self vs paired_parent_unchanged`) | `11 / 1`, `+2.98%`, `p = 0.00317` | `6 / 6`, `+2.09%`, `p = 0.613` | Evolved $\Phi_3$ still improves $\Phi_3$ further on convex logistic tasks, but no faster than $\Phi_0$ (`paired_fixed`: `-0.75%`) or `paired_spsa` (`-0.70%`) |

---

## Mechanistic Diagnosis: Why Task Adaptation Succeeded While Proposer Improvement Failed

The generation trajectories and subspace-overlap receipts expose a sharp geometric reason why a shared-basis active-subspace self-transformer succeeds at **retained downstream adaptation** (`+21.26%`, `+32.85%`, `12/12` wins) while failing **proposer improvement**:

1. **Downstream task gradients stay inside $U_{\text{env}}$:** On every fresh task in an environment, $\nabla_w \mathcal{L}_{\text{task}}(w)$ concentrates along $U_{\text{env}}$. Aligning $\hat{U}_2(\Phi)$ with $U_{\text{env}}$ directly boosts signal-to-noise on every new downstream task episode.
2. **Outer Grassmannian meta-gradients move into $\hat{U}_2^\perp$:** Once generation `g = 0` rotates $\hat{U}_2(\Phi_1)$ partway toward $U_{\text{env}}$ (overlap `0.124 -> 0.275` on `subspace_logistic`; `0.130 -> 0.349` on `gated_bilinear`), `hereditary_reset` briefly matches or edges `fixed_reset` at `g = 1` (`0.3309 vs 0.3339` and `0.6461 vs 0.6555`). However, as overlap approaches `~0.40`, the *remaining* undiscovered subspace component of $\nabla_{v_r} J(\Phi)$ lies in the Grassmannian tangent space $\hat{U}_2(\Phi)^\perp \cap U_{\text{env}}$. Dedicating 2 of the 4 outer query pairs to re-probing the *already-discovered* $\hat{U}_2(\Phi)$ leaves only 2 complement probes to sense $\hat{U}_2(\Phi)^\perp$, slowing further subspace discovery (`0.393 -> 0.472` for `hereditary_reset` vs `0.387 -> 0.506` for unaligned `fixed_reset` and `0.486 -> 0.546` for isotropic `tuned_spsa_reset`).
3. **Control-block coordinate mismatch:** Block $m = 2$ ($c \in \mathbb{R}^{16}$) parameterizes scalar learning-rate, boost, and decay schedules along canonical coordinates `c[0..8]`, which have no geometric alignment with the rotated feature subspace $U_{\text{env}}$. Applying $\hat{U}_2(\Phi)$ preconditioning to $c$ adds structured directional bias without matching $\nabla_c J(\Phi)$.
4. **Why Stage 1 (`n = 6`) vs Stage 2 (`n = 12`) separation mattered:** On the 6 selection seeds, `kronecker_subspace_2mode` showed `+2.94%` and `+6.23%` median proposer gains; on 12 fresh confirmation seeds, that apparent proposer lift regressed to `-0.01%` and `-2.16%`. Without separately frozen selection and confirmation, small-sample seed variance across 4 candidates would have produced an unverified proposer-improvement claim.

**Implication for subsequent Track B hypotheses:** In self-application, *task-exploitation geometry* ($\text{span}(U_{\text{env}})$) and *remaining meta-improvement geometry* (the Grassmannian tangent $\hat{U}_2^\perp$ plus architectural/control coordinates) are orthogonal rather than identical. A self-improving proposer cannot simply apply its downstream feature-exploitation prior to its own weights; it requires an update mechanism whose outer search distribution adapts to *residual meta-uncertainty* (e.g., orthogonal-complement exploration or distinct meta-credit assignment across parameter roles) while still passing through a uniform self-applicable representation.

---

## Explicit Non-Claims

- **Not a source-printing quine:** `worker.mjs` loads static interpreter code from disk and reconstructs the 48 `float64` weights $\Phi$ + rule identifier from a SHA-256-verified artifact string.
- **No recursive self-improvement or conventional superiority claim:** Evolved children are strong downstream task optimizers (`12/12` wins over `serialization_only` and `10/12..11/12` wins over noisy secant `L-BFGS`), but they do **not** become better proposers than their unaligned ancestor (`fixed_reset`) or calibrated zero-order `SPSA` (`tuned_spsa_reset`).
- **No neural/LLM or GPU transfer claim:** All experiments are CPU-only synthetic 16D/32D/48D zero-order optimization benchmarks.

---

## Reproduction Commands

Run unit, budget-parity, scale-homogeneity, and subprocess-isolation checks:

```bash
node projects/self_transform_subspace_v1/test.mjs
```

Re-run Stage 1 candidate selection (`6` selection seeds x `2` families x `4` candidates) to a new local receipt path:

```bash
node projects/self_transform_subspace_v1/select.mjs .work/subspace-selection-repro.json
```

Re-run sealed Stage 2 confirmation (`12` unseen confirmation seeds x `2` families, `2,016` isolated subprocess calls + in-process parity audit; requires `.work/subspace-selection-01.json` matching `selectionReceiptSha256` in [`protocol.confirmation.json`](protocol.confirmation.json)):

```bash
node projects/self_transform_subspace_v1/confirm.mjs .work/subspace-confirmation-repro.json
node projects/self_transform_subspace_v1/stats.mjs .work/subspace-confirmation-repro.json
```
