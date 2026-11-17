# Cumulative Self-Improvement Study v2 (`self_transform_neural_proposer_v2`)

Charter: [CATSCAN.md](CATSCAN.md)

## Overview and Architectural Advances Over `v1`

`self_transform_neural_proposer_v2` evaluates **Gamma Track B2** (cumulative hereditary self-improvement) across `S = 5` independent lineage seeds (`101, 202, 303, 404, 505`) and `G = 4` cold-subprocess generations (`g = 0 -> 1 -> 2 -> 3 -> 4`) on `64` untouched unseen neural target tasks (`seed_base = 850000`, `B = 10` cold support passes per task, `320` pooled evaluations per arm).

`v1` (`projects/self_transform_neural_proposer_v1/`) established genuine neural self-modification over `Gen 0` (`p = 0.0133` exact / `p = 0.00209` regen), but plateaued after `Gen 1..2` (`p = 0.666` vs `Gen 1`) and lost to calibrated `AdamW` and `SGD+Nesterov` on pooled noisy-label cross-entropy due to degrading accepted steps, basis-norm entanglement, uncalibrated logit temperatures across activation scales, and unregularized weight decay erasing learned proposer weights during self-modification.

`M_Phi_v2` (`2,073` float64 parameters across `W_gate [48x17]`, `W_up [48x17]`, `W_out [9x49]`) resolves each failure mechanism at **zero extra target forward-backward passes**:

1. **Unit-RMS Basis Decoupling + Newton-Schulz Polar & Two-Sided K-FAC Basis**:
   - Computes 5-iteration polynomial Newton-Schulz polar orthogonalization (`B_spec`) on layer momentum alongside Marchenko-Pastur sample-aspect-damped two-sided Kronecker curvature (`B_kfac`, `B_in_k` with `damp_in = 0.08 + 0.36 * (d_in1 / N)`).
   - Normalizes the combined basis direction `B_comb = norm_dir(D_comb)` to unit RMS so unlocking `B_curv` and `B_spec` rotates update geometry without inflating step magnitude.
2. **muP Functional Output-Scale Step Calibration & Split-Half Gradient Coherence**:
   - Exposes `16` scale-free per-row features including total network depth `log(L)`, sample aspect ratio `log(d_in1 / N)`, zero-extra-pass split-half gradient coherence `cos(G_half1, G_half2)`, and pre-activation functional output scale `log(sqrt(d_in1) * act_rms * ||w_i||)`.
   - Scales row step size by `layer_scale = max(init_layer_rms, min(0.24, 1 / (sqrt(d_in1) * act_rms)))`, lifting under-scaled output heads (`||Z|| < 1`) at `O(1)` functional speed without exploding over-confident classification heads (`||Z|| >= 1`) under `10%–15%` label noise.
3. **Proximal Self-Modification & Active Conventional Opponent Sparring**:
   - During `self_modify_proposer_v2`, shrinkage acts proximally toward `parent_phi` (`W - W_parent`) rather than `0`, preserving inherited proposer structure across generations.
   - Inside every generation subprocess (`worker_v2.py`), `M_Phi_v2` competes directly against an escalating tournament of `SGD+Nesterov` and `AdamW+Cosine` sparring opponents on a 12-task progressive validation anchor (`2/3/4`-layer `Tanh`/`GELU`/`SiLU` + gated `SwiGLU` networks, strictly disjoint from all 4 confirmation architectures), retaining improvements under coarse-to-fine trust radii.

## Full Cost Accounting and Matched Lineages

Every upstream evaluation, active-opponent pass, elitist selection check, and behavioral reconstruction step is explicitly billed:

- **`exact` (`exact_gen0..gen4`)**: Recursive self-modification (`M_{Phi_g}` modifies `Phi_g`) across isolated OS subprocesses; consumes exact `1,320` target-oracle passes per generation (`240` active-opponent tournament passes + `120` parent-anchor passes + `3` batches x `320` proposal/opponent/2-scale-anchor passes = `5,280` cumulative passes at `g = 4`).
- **`regen` (`regen_gen0..gen4`)**: True 4-generation **weight-free behavioral regeneration** at **every** generation boundary (`512` Gaussian-probe evaluations + `240` fresh-init student distillation steps per boundary, zero weight scalars crossing any OS subprocess boundary; `1.53e9` FLOPs = `+80` target-pass-equivalents billed per boundary -> `1,400 * g` = `5,600` total pass-equivalents at `g = 4`). Across all `20` regeneration boundaries (`5` seeds x `4` generations), `functional_mse_after` ranged in `[2.02e-6, 1.20e-5]` while `raw_parameter_cosine_vs_teacher` ranged in `[0.519, 0.624]`, confirming functional distillation across SwiGLU permutation/scaling symmetries.
- **`fixed_proposer` (`fixed_proposer_gen0..gen4`)**: Identical `1,320 * g` budget, anchor tasks, active opponents, elitist parent retention, and trust-radius schedule, except `self_modify_proposer_v2` holds the proposer update rule fixed at `M_{Phi_0}` (`proposer_rule_phi = Phi_0`). Isolates genuine recursive compounding from parent retention + curriculum effects.
- **Conventional Optimizer Controls (`sgd_nesterov`, `adamw_cosine`, `damped_lbfgs`)**: Each receives `1,400 * g` (`1400, 2800, 4200, 5600`) upstream target-oracle calibration passes (`14` configurations/gen x `10` calibration tasks x `10` passes = `56` configurations per seed), strictly `>=` both `exact` (`5,280`) and `regen` (`5,600`).

## Artifacts and Hashes

- Protocol lock: `.work/self-transform-neural-proposer-v2/confirmation_receipt_v2.protocol.json`
- Sealed confirmation receipt (`145` isolated OS subprocesses, `360` logged candidate proposals, `275.64s` wall-clock): `.work/self-transform-neural-proposer-v2/confirmation_receipt_v2.json`
- Code `sha256`:
  - `proposer_v2.py`: `fca1a43b9a947e10323ec6c9dfc4acf19273eeb368cb26eb4bcdb4cbc76321ec`
  - `tasks_b2_v2.py`: `73a581f93c21307159a361db52eb262df8cc39619f6106e65190da028c1429ca`
  - `worker_v2.py`: `3ac88baeb23910f3da23ae4c4358614e3dfff126045a39ec94d033a686df2a74`
  - `run_study_v2.py`: `98e082787ccc7c6e0cb8f8e4aba2cac48aad5d188790e256abe9fc736cb8d1d1`

## Generational Held-Out Confirmation Curves (`seed_base = 850000`, `S = 5` Seeds, `64` Tasks/Seed)

Normalized query-loss ratio (`final_query_loss / init_query_loss`, lower is better):

| Lineage | `Gen 0` (`0` passes) | `Gen 1` (`1.32k / 1.4k`) | `Gen 2` (`2.64k / 2.8k`) | `Gen 3` (`3.96k / 4.2k`) | `Gen 4` (`5.28k / 5.6k`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`exact` (`M_{Phi_g}` recursive)** | `0.3273 +- 0.0006` | `0.3150 +- 0.0027` | `0.3041 +- 0.0083` | `0.2995 +- 0.0120` | **`0.2953 +- 0.0144`** |
| **`regen` (weight-free 4-gen)** | `0.3273 +- 0.0006` | `0.3154 +- 0.0024` | `0.3036 +- 0.0087` | `0.2985 +- 0.0111` | **`0.2953 +- 0.0139`** |
| `fixed_proposer` (`M_{Phi_0}` rule) | `0.3273 +- 0.0006` | `0.3158 +- 0.0027` | `0.3050 +- 0.0077` | `0.3021 +- 0.0101` | `0.2972 +- 0.0125` |

### Per-Architecture Confirmation Breakdown (Mean Across `5` Seeds x `16` Tasks = `80` Evals/Family)

Every unseen target family improves monotonically across all 4 generations on both loss and accuracy/$R^2$:

| Arm (`B = 10` cold passes) | Pooled Norm Ratio | `unseen_swiglu_3layer_cls` (Norm / Loss / Acc) | `unseen_bottleneck_4layer_reg` (Norm / MSE / $R^2$) | `unseen_fastweight_adapter_bridge` (Norm / Loss / Acc) | `unseen_deep_elu_5layer_cls` (Norm / Loss / Acc) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `gen0` (`M_{Phi_0}`) | `0.3273` | `0.2765` / `349.92` / `27.41%` | `0.2184` / `0.567` / `+0.436` | `0.4185` / `1.819` / `44.12%` | `0.3959` / `1.248` / `55.97%` |
| `exact_gen1` | `0.3150` | `0.2537` / `323.05` / `28.71%` | `0.2060` / `0.531` / `+0.472` | `0.4108` / `1.780` / `45.73%` | `0.3894` / `1.228` / `56.60%` |
| `exact_gen2` | `0.3041` | `0.2359` / `294.60` / `29.50%` | `0.1905` / `0.486` / `+0.517` | `0.4061` / `1.751` / `46.97%` | `0.3840` / `1.211` / `57.03%` |
| `exact_gen3` | `0.2995` | `0.2283` / `286.87` / `29.85%` | `0.1842` / `0.467` / `+0.536` | `0.4033` / `1.736` / `47.85%` | `0.3823` / `1.205` / `57.35%` |
| **`exact_gen4`** | **`0.2953`** | **`0.2249` / `278.79` / `30.16%`** | **`0.1758` / `0.440` / `+0.562`** | **`0.3996` / `1.716` / `49.45%`** | **`0.3810` / `1.202` / `57.74%`** |
| **`regen_gen4`** | **`0.2953`** | **`0.2234` / `278.60` / `30.05%`** | **`0.1764` / `0.444` / `+0.558`** | **`0.4011` / `1.721` / `49.16%`** | **`0.3802` / `1.199` / `57.93%`** |
| `fixed_proposer_gen4` | `0.2972` | `0.2291` / `284.72` / `30.13%` | `0.1776` / `0.447` / `+0.555` | `0.4013` / `1.724` / `48.87%` | `0.3809` / `1.201` / `57.74%` |
| `sgd_nesterov_b5600` | `0.3614` | `0.2690` / `307.36` / `31.46%` | `0.2909` / `0.726` / `+0.277` | `0.4917` / `2.082` / `50.65%` | `0.3941` / `1.237` / `58.49%` |
| `adamw_cosine_b5600` | `0.4228` | `0.4567` / `544.33` / `32.09%` | `0.1977` / `0.484` / `+0.518` | `0.6048` / `2.589` / `54.34%` | `0.4320` / `1.340` / `59.49%` |
| `damped_lbfgs_b5600` | `0.4367` | `0.6265` / `723.06` / `27.56%` | `0.1719` / `0.381` / `+0.619` | `0.5260` / `2.239` / `54.13%` | `0.4223` / `1.329` / `58.39%` |

### Pooled Paired Sign-Test Results (`N = 320` Task Evaluations)

| Comparison | Focal Wins / Ref Wins | Clipped Mean Rel Gain | Exact Two-Sided Sign `p` |
| :--- | :---: | :---: | :---: |
| `exact_gen4` vs `gen0` | `305 / 15` (`64` ties=`0`) | `+12.75%` | `2.04e-71` |
| `exact_gen4` vs `exact_gen1` | `229 / 27` (`64` ties) | `+8.70%` | `4.57e-41` |
| `exact_gen4` vs `exact_gen2` | `208 / 48` (`64` ties) | `+4.46%` | `6.41e-25` |
| `exact_gen4` vs `exact_gen3` | `200 / 56` (`64` ties) | `+2.54%` | `3.65e-20` |
| **`exact_gen4` vs `fixed_proposer_gen4`** | **`219 / 101`** | **`+0.69%`** | **`3.71e-11`** |
| **`exact_gen4` vs `sgd_nesterov_b5600`** | **`207 / 113`** | **`+5.66%`** | **`1.65e-7`** |
| **`exact_gen4` vs `adamw_cosine_b5600`** | **`231 / 89`** | **`+13.17%`** | **`1.08e-15`** |
| **`exact_gen4` vs `damped_lbfgs_b5600`** | **`238 / 82`** | **`+12.32%`** | **`8.91e-19`** |
| `regen_gen4` vs `gen0` | `304 / 16` | `+12.66%` | `3.90e-70` |
| `regen_gen4` vs `regen_gen1` | `279 / 41` | `+8.56%` | `1.16e-44` |
| `regen_gen4` vs `regen_gen2` | `266 / 54` | `+4.14%` | `8.38e-35` |
| `regen_gen4` vs `regen_gen3` | `207 / 113` | `+1.94%` | `1.65e-7` |
| **`regen_gen4` vs `fixed_proposer_gen4`** | **`201 / 119`** | **`+0.69%`** | **`5.32e-6`** |
| **`regen_gen4` vs `sgd_nesterov_b5600`** | **`210 / 110`** | **`+5.42%`** | **`2.43e-8`** |
| **`regen_gen4` vs `adamw_cosine_b5600`** | **`232 / 88`** | **`+12.91%`** | **`4.11e-16`** |
| **`regen_gen4` vs `damped_lbfgs_b5600`** | **`238 / 82`** | **`+12.16%`** | **`8.91e-19`** |

## Reproduction

```bash
.venv/bin/python -m unittest projects/self_transform_neural_proposer_v2/test_proposer_v2.py -v
OMP_NUM_THREADS=1 .venv/bin/python projects/self_transform_neural_proposer_v2/run_study_v2.py \
  --output-json .work/self-transform-neural-proposer-v2/confirmation_receipt_v2.json \
  --confirmation-seed-base 850000 --seeds 101 202 303 404 505 --generations 4 --confirmation-tasks-per-family 16
```
