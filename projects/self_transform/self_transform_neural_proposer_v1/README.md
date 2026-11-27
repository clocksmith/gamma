# Self-Applicable SwiGLU Neural Proposer Heredity Study (`self_transform_neural_proposer_v1`)

## Overview and Question

This study evaluates **Gamma Track B2** (hereditary self-improvement) on fresh, cold neural network targets under matched forward-backward pass budgets (`B = 10` passes per cold target, `state = None` at step 0).

Unlike `projects/self_transform/self_transform_secant_regen_v1/` (which wrapped a hand-coded Barzilai-Borwein secant step in a small scalar-gate parameterization and passed `1/6` proposer gates), `self_transform_neural_proposer_v1` constructs a genuine multi-layer **SwiGLU neural weight-proposer** `M_Phi` (`1,783` float64 parameters across `W_gate [48x15]`, `W_up [48x15]`, `W_out [7x49]`) with zero hand-coded secant formulas:

1. **Equivariant Neural Proposal**: Given any multi-layer neural network target `{W_l}` on a support batch `(X_sup, Y_sup)`, one charged forward-backward pass yields layer input activations `A_{l-1}`, pre-activation errors `E_l`, weight gradients `G_l`, and input activation covariance `Sigma_l = A_{l-1}^T A_{l-1} / N`. `M_Phi` maps `14` scale-free per-row structural features to `7` neural controls blending normalized gradient, momentum, diagonal RMS, and activation-preconditioned Kronecker natural-gradient directions (`(Sigma_norm + lambda * I)^{-1}`), row step sizes, and weight-shrinkage gates.
2. **Model-Level Self-Modification**: Across `G = 4` generations (`g = 0 -> 1 -> 2 -> 3 -> 4`), no external SGD or Adam optimizer updates `Phi`. Instead, `M_Phi_g` unrolls `B = 10` adaptation steps on disjoint 2-layer `Tanh`/`GELU` meta-training tasks (`seed_base = 510000`), differentiates held-out query loss through the unrolled graph to extract `M_Phi_g`'s **own** layer input activations `(A_0^Phi, A_1^Phi)` and pre-activation meta-gradients `(E_gate^Phi, E_up^Phi, E_out^Phi)`, and applies `propose_network_update(phi=Phi_g, layers=Phi_g, ...)` to modify its own `1,783` parameters.
3. **Cold Subprocess Isolation and Weight-Free Behavioral Self-Regeneration**:
   - **Exact Cold-Process Lineage (`exact_gen1..4`)**: Each generation spawns an isolated OS subprocess (`worker.py`), reconstructing `ProposerWeights` with `opt_state = None`.
   - **Weight-Free Behavioral Self-Regeneration Lineage (`regen_gen1..4`)**: Zero weight values cross the OS process boundary (enforced by assertion in `worker.py`). The parent evaluates `M_Phi` on `512` synthetic Gaussian probe inputs; a fresh child OS process initializes a random SwiGLU proposer from a distinct seed and distills `(probe_inputs, probe_outputs)` over `240` billed steps (`functional_mse` `4.7e-6` to `1.0e-5`, while `raw_parameter_cosine_vs_teacher` drops to `0.602..0.696` and L2 distance is `5.28..6.46`, confirming functional reconstruction across SwiGLU permutation/scaling symmetries rather than trivial parameter printing).

## Artifacts and Hashes

- Charter: `projects/self_transform/self_transform_neural_proposer_v1/CATSCAN.md`
- Implementation:
  - `proposer.py` (`sha256: 4474d1faf24abca6cca16a4ea4a856ec4145dba0f1f6f808d57bd021a7583031`)
  - `targets.py` (`sha256: 5572ce645327f554f9f6eaccb789974d2eb3f4e809bfee800416cb141d5e1f18`)
  - `baselines.py` (`sha256: 1e3c0073b084d2dfd2c6575fa165c971de64a63f94d55174583322833228327406cde` -> see receipt `1e3c0073b084d2dfd2c6575fa165c971de64a63f94d551745833228327406cde`)
  - `worker.py` (`sha256: d5fb57ecfe393919587f4145e5ee1a27d8ff73b35c2d7ef9379c7604ea696354`)
  - `run_study.py` (`sha256: 79655b9d952a88ed344f3f3f77ecf13bf2bcbaa119d3e2175e51d294242c9082`)
- Receipts:
  - Protocol lock: `.work/self-transform-neural-proposer-v1/confirmation_receipt.protocol.json`
  - Confirmation receipt (`21` isolated OS subprocesses, `33.35s` wall-clock): `.work/self-transform-neural-proposer-v1/confirmation_receipt.json`

## Hereditary Lineage Progression (Disjoint 2-Layer Meta-Validation Ratio)

| Generation | Exact Subprocess PID | Exact `meta_val` (`before -> after`) | Regen Subprocess PIDs | Regen `func_mse` | Raw Param Cosine vs Teacher | Raw Param L2 Distance |
| --- | --- | --- | --- | --- | --- | --- |
| `0 -> 1` | `32192` | `0.7419 -> 0.3831` | `32194 / 32196` | `4.73e-6` | `0.696` | `5.284` |
| `1 -> 2` | `32197` | `0.3726 -> 0.3406` | `32199 / 32202` | `6.52e-6` | `0.609` | `6.286` |
| `2 -> 3` | `32203` | `0.3127 -> 0.3096` | `32205 / 32206` | `8.40e-6` | `0.612` | `6.457` |
| `3 -> 4` | `32208` | `0.3629 -> 0.3521` | `32211 / 32214` | `1.01e-5` | `0.602` | `6.538` |

## Sealed Confirmation on 48 Unseen Cold Neural Targets (`seed_base = 710000`, `B = 10` Passes)

None of the three confirmation architectures appeared in the 2-layer `Tanh`/`GELU` meta-training curriculum. Conventional baselines (`SGD+Nesterov`, `AdamW+Cosine`, `Damped L-BFGS`) were grid-calibrated on `24` separate calibration tasks (`seed_base = 610000`, `24,960` calibration passes billed).

| Arm (`B = 10` passes, `state = None`) | `unseen_swiglu_3layer_cls` (Acc / Qry Loss) | `unseen_bottleneck_4layer_reg` ($R^2$ / Qry MSE) | `unseen_fastweight_adapter_bridge` (Acc / Qry Loss) |
| --- | --- | --- | --- |
| `gen0_fixed` (`M_Phi_0`) | `24.26%` / `290.17` | `-1.865` / `2.831` | `19.34%` / `7.774` |
| `exact_gen1` | `32.62%` / `304.71` | `+0.359` / `0.623` | `45.43%` / `2.465` |
| `exact_gen2` | `33.44%` / `281.57` | `+0.488` / `0.498` | `50.27%` / `2.441` |
| `exact_gen3` | `32.38%` / `297.34` | `+0.472` / `0.514` | `49.57%` / `2.318` |
| `exact_gen4` | `31.84%` / `345.78` | **`+0.476`** / **`0.510`** | **`49.77%`** / `2.824` |
| `regen_gen3` | `33.87%` / `267.21` | **`+0.503`** / **`0.486`** | **`50.39%`** / `2.642` |
| `regen_gen4` | `32.66%` / **`261.87`** | `+0.448` / `0.539` | `48.95%` / `2.797` |
| `sgd_nesterov` (calibrated) | `31.41%` / `274.77` | `+0.216` / `0.766` | `43.44%` / **`1.940`** |
| `adamw_cosine` (calibrated) | **`33.98%`** / `400.32` | `+0.449` / `0.537` | `49.65%` / `2.235` |
| `damped_lbfgs` (calibrated) | `24.22%` / `815.26` | `+0.272` / `0.713` | `41.64%` / `2.478` |

### Paired Sign-Test Summary (`48` Tasks Pooled)

- **Cold-target improvement over Fixed Gen-0 (`M_Phi_0`)**:
  - `exact_gen4 vs gen0_fixed`: **`33` wins / `15` losses** (`+11.30%` mean relative query-loss gain, two-sided sign-test `p = 0.0133`).
  - `regen_gen4 vs gen0_fixed`: **`35` wins / `13` losses** (`+22.76%` mean relative query-loss gain, `p = 0.00209`).
- **Multi-generation trajectory (`Gen 4 vs Gen 1`)**:
  - `exact_gen4 vs exact_gen1`: `26` wins / `22` losses (`p = 0.6655`) — improvement mostly occurs in `Gen 0 -> Gen 2` and plateaus by `Gen 3..4`.
  - `regen_gen4 vs regen_gen1`: `23` wins / `25` losses (`p = 0.8854`).
- **Comparison vs calibrated conventional optimizers (`B = 10` matched oracle passes)**:
  - vs `damped_lbfgs`: **`34/48` wins (`+21.09%`, `p = 0.0055`)** for `regen_gen4`; `31/48` (`+17.26%`, `p = 0.0595`) for `exact_gen4`.
  - vs `sgd_nesterov`: Beats SGD on `unseen_bottleneck_4layer_reg` (`14/16` wins, `+30.54%`, `p = 0.0042` exact; `13/16`, `p = 0.0213` regen) and achieves higher classification accuracy on both `unseen_swiglu_3layer_cls` (`32.66% vs 31.41%`) and `unseen_fastweight_adapter_bridge` (`49.77% vs 43.44%`), **but loses on pooled raw query cross-entropy loss (`21/48` exact, `23/48` regen)** because larger Kronecker classification logits incur steeper tail cross-entropy on the `10%–12%` misclassified outliers.
  - vs `adamw_cosine`: Beats `AdamW` on `unseen_swiglu_3layer_cls` (`12/16` wins, `+20.18%` for `regen_gen4`) and achieves lower mean MSE on `unseen_bottleneck_4layer_reg` (`0.510 vs 0.537`), **but loses on pooled query loss (`22/48`)**.

## Honest Status and Remaining Gaps for Track B2

1. **Demonstrated**: Genuine neural self-application (`M_Phi` updating its own `1,783` SwiGLU weights without an external optimizer), cold subprocess isolation, non-trivial weight-free behavioral self-regeneration across SwiGLU symmetries (`cos = 0.602`), significant cold-target proposer gains over `Gen-0` (`p = 0.0021` / `p = 0.0133`), and clear superiority over calibrated `Damped L-BFGS` (`p = 0.0055`) and over `SGD+Nesterov` on deep ill-conditioned regression (`p = 0.0042`).
2. **Not Yet Demonstrated (Why Track B2 Remains Open)**:
   - Recursive improvement plateaus after `g = 2..3` (`Gen 4` does not significantly beat `Gen 1` or `Gen 2`), because fixed-capacity (`H = 48`) meta-updates on stationary 2-layer MLPs saturate quickly.
   - Pooled superiority over `Tuned AdamW` and `Tuned SGD+Nesterov` across all unseen target families is **not** achieved due to classification logit-temperature miscalibration under noisy support labels.
3. **Next Concrete Hypotheses & Reproduction Commands**:
   - Add an explicit final-layer temperature / output-norm calibration head to `M_Phi` and expand generational meta-tasks progressively (`2-layer -> 3-layer -> 4-layer` curriculum with cross-generation anchor acceptance) to test whether `Gen 4 > Gen 2 > Gen 1` holds strictly without saturation.
   - Reproduce unit tests and confirmation study:
     ```bash
     .venv/bin/python -m unittest projects/self_transform/self_transform_neural_proposer_v1/test_neural_proposer.py -v
     OMP_NUM_THREADS=1 .venv/bin/python projects/self_transform/self_transform_neural_proposer_v1/run_study.py \
       --output-json .work/self-transform-neural-proposer-v1/confirmation_receipt.json \
       --generations 4 --confirmation-seeds 16 --meta-steps 12
     ```
