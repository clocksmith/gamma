# Cumulative Self-Improvement Study v2 (`self_transform_neural_proposer_v2`)

Charter: [CATSCAN.md](CATSCAN.md)

> **Track B2 Status: NOT MET.** Sealed `.work/` receipts remain untouched, and the claims below are corrected to match lineage-level evidence. Meta-training improves the `2,073`-parameter update rule from `Gen 0` to `Gen 4` across all `5` seeds (`0.3273 -> 0.2953`, lineage-level paired `t = -4.52`, `p = 0.0106`), **but recursive self-improvement is not shown** (`exact_gen4` vs non-recursive `fixed_proposer_gen4`: lineage-level `t = -0.52`, `p = 0.6298`, `n = 5`; seed `303` favors `fixed_proposer` and seed `202` stalls with `0` accepted proposals after `Gen 1`), and **conventional optimizers beat `M_Phi_v2` on held-out accuracy across all three classification families** (and `L-BFGS` beats it on regression $R^2$). All four target families—including `unseen_fastweight_adapter_bridge`—are synthetic `1.3k–2.5k` parameter random-teacher toy MLPs touching no real pretrained model.

## Overview and Methodological Audit

`self_transform_neural_proposer_v2` runs `S = 5` lineage seeds (`101, 202, 303, 404, 505`) across `G = 4` cold-subprocess generations (`g = 0 -> 1 -> 2 -> 3 -> 4`) evaluated on `64` synthetic toy target tasks (`seed_base = 850000`, `B = 10` support passes per target).

What `M_Phi_v2` implements vs what confounds the `v2` study:

1. **Preconditioned Basis + Unmatched Output-Head Shrinkage (`proposer_v2.py`)**:
   - Hardcodes 5-step Newton-Schulz momentum orthogonalization (`B_spec`) and two-sided damped K-FAC (`B_kfac`) before applying the `2,073`-parameter SwiGLU gate network.
   - Grants `M_Phi_v2` an output-head multiplicative shrinkage gate (`gamma_head = 0.16 * sigmoid(...)`, shrinking logits up to `16%/step`) not available to `SGD`, `AdamW`, or `L-BFGS`. On `unseen_swiglu_3layer_cls` (where multi-layer gated init produces initial CE loss `~1,265`), damping logit scale slashes cross-entropy loss without improving classification boundaries. Zeroing the output head and running plain `Adam`—an omitted baseline—reaches `0.2914` in `4/5` seeds (`0.456` in `1`) when calibrated beforehand (`0.231` with a post-hoc learning rate), and a constant 1-scalar step-size rule chosen post-hoc gets `0.2950` on seed `101` (`vs 0.2984` for `exact_gen4`).
   - Conventional controls also get only `B = 10` passes per target from a single global hyperparameter search (where `adamw_cosine_b5600` selected the identical config scoring `0.4013` in `4/5` seeds), and untrained `gen0` (`0.3273`) already beats them on normalized loss.
2. **Synthetic Toy Targets (`tasks_b2_v2.py`, `v1/targets.py`)**:
   - All four confirmation families are random-teacher synthetic networks (`1.3k–2.5k` parameters), three of the four families were `v1`'s confirmation families, and **`unseen_fastweight_adapter_bridge` is entirely synthetic** (a random `[48x24] -> [48x48]` frozen MLP trunk with a `[16x48]` synthetic head; no real language model or `B1` adapter is touched).
3. **Cost-Accounting Discrepancies & Receipt Omissions (`worker_v2.py`, `run_study_v2.py`)**:
   - **`regen` is ordinary Adam behavioral distillation costing `~13,900` pass-equivalents per boundary, not `80`**: `worker_v2.py` logs `regen_flops = 1.53e9` (`512` Gaussian probes x `240` Adam distillation steps on a fresh-init student) and states `1` target-oracle pass is `~1.1e5` FLOPs—which equals **`~13,914` pass-equivalents per generation (`~55,655` across `4` generations)**, contradicting the `80`-pass (`8.8e6` FLOPs) allowance charged in the script.
   - `evaluate_diff_query_v2` runs `12` differentiable meta-query forward-backward passes per generation (`n_qry = 128`) outside `ChargedTargetOracleV2` (`0` passes billed).
   - `confirmation_receipt_v2.json` stripped per-task `rows` prior to serialization (so `320`-pair win/loss counts cannot be independently audited from the receipt alone), and `.protocol.json` was written at runtime by `run_study_v2.py`.

## Artifacts and Hashes

- Runtime-written protocol file: `.work/self-transform-neural-proposer-v2/confirmation_receipt_v2.protocol.json`
- Sealed confirmation receipt (`145` subprocesses, `360` candidate proposals, summary-only without per-task `rows`): `.work/self-transform-neural-proposer-v2/confirmation_receipt_v2.json`
- Code `sha256`:
  - `proposer_v2.py`: `fca1a43b9a947e10323ec6c9dfc4acf19273eeb368cb26eb4bcdb4cbc76321ec`
  - `tasks_b2_v2.py`: `73a581f93c21307159a361db52eb262df8cc39619f6106e65190da028c1429ca`
  - `worker_v2.py`: `3ac88baeb23910f3da23ae4c4358614e3dfff126045a39ec94d033a686df2a74`
  - `run_study_v2.py`: `98e082787ccc7c6e0cb8f8e4aba2cac48aad5d188790e256abe9fc736cb8d1d1`

## Generational Curves & Per-Seed Trajectories (`n = 5` Independent Lineages)

All `5` seeds were evaluated on the **identical `64` confirmation tasks** (`seed_base = 850000`), so the independent unit of inference is the **lineage (`n = 5`)**, not `320` pseudoreplicated task-seed pairs. Note that seed `202` accepted `[2, 0, 0, 0]` proposals across `Gen 1..4` (completely stalled after `Gen 1`), and seed `303` accepted `[3, 3, 0, 1]` and finished worse on `exact_gen4` (`0.2958`) than non-recursive `fixed_proposer_gen4` (`0.2858`).

| Arm | `s = 101` | `s = 202` | `s = 303` | `s = 404` | `s = 505` | Lineage Mean `+-` Sample SD (`n = 5`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `gen0` (`M_{Phi_0}` untrained) | `0.3270` | `0.3278` | `0.3279` | `0.3276` | `0.3263` | `0.3273 +- 0.0007` |
| `exact_gen1` (`1.32k` billed + query) | `0.3147` | `0.3202` | `0.3133` | `0.3126` | `0.3140` | `0.3150 +- 0.0030` |
| `exact_gen2` (`2.64k` billed + query) | `0.3029` | `0.3202` | `0.2992` | `0.3006` | `0.2975` | `0.3041 +- 0.0092` |
| `exact_gen3` (`3.96k` billed + query) | `0.3025` | `0.3202` | `0.2992` | `0.2901` | `0.2857` | `0.2995 +- 0.0134` |
| `exact_gen4` (`M_{Phi_g}` recursive) | `0.2984` | `0.3202` | `0.2958` | `0.2803` | `0.2819` | `0.2953 +- 0.0161` |
| `regen_gen4` (Adam distill, `~13.9k` pass-eq/gen) | `0.3032` | `0.3190` | `0.2837` | `0.2848` | `0.2857` | `0.2953 +- 0.0155` |
| `fixed_proposer_gen4` (`M_{Phi_0}` fixed rule) | `0.2994` | `0.3203` | `0.2858` | `0.2869` | `0.2937` | `0.2972 +- 0.0140` |
| `sgd_nesterov_b5600` | `0.3964` | `0.4240` | `0.3332` | `0.3268` | `0.3268` | `0.3614 +- 0.0456` |
| `adamw_cosine_b5600` | `0.5086` | `0.4013` | `0.4013` | `0.4013` | `0.4013` | `0.4228 +- 0.0480` |
| `damped_lbfgs_b5600` | `0.4530` | `0.4201` | `0.4773` | `0.4201` | `0.4129` | `0.4367 +- 0.0275` |

### Lineage-Level Paired Comparisons on Normalized Loss (`n = 5` Seeds)

Per-seed `exact_gen4 - fixed_proposer_gen4` differences are `[-0.0010, -0.0001, +0.0100, -0.0066, -0.0119]` (`mean = -0.0019 +- 0.0082`, paired `t = -0.52`, `|t| = 0.52`, two-sided `p = 0.6298`), showing **no statistically significant recursive advantage over `fixed_proposer_gen4`**. Note also that with `n = 5` lineages, a two-sided exact sign test has a floor of `p = 0.0625` even at `5/0`.

| Lineage Comparison (`n = 5`) | Mean Diff (`Focal - Ref`) `+-` SD | Seed Wins / Losses / Ties | Paired `t` (`df = 4`) | Two-Sided `p` (`t`-test / Sign) | Audit Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `exact_gen4` vs `gen0` | `-0.0320 +- 0.0158` | `5 / 0 / 0` | `-4.52` | `0.0106` / `0.0625` | Meta-training improves rule over `Gen 0` |
| `exact_gen4` vs `exact_gen1` | `-0.0197 +- 0.0134` | `4 / 0 / 1` | `-3.28` | `0.0305` / `0.1250` | Seed `202` tied (`0` post-Gen1 accepts) |
| `exact_gen4` vs `exact_gen2` | `-0.0088 +- 0.0087` | `4 / 0 / 1` | `-2.25` | `0.0879` / `0.1250` | Not significant at `alpha = 0.05` |
| `exact_gen4` vs `exact_gen3` | `-0.0042 +- 0.0035` | `4 / 0 / 1` | `-2.66` | `0.0564` / `0.1250` | Not significant at `alpha = 0.05` |
| **`exact_gen4` vs `fixed_proposer_gen4`** | **`-0.0019 +- 0.0082`** | **`4 / 1 / 0`** | **`-0.52`** | **`0.6298` / `0.3750`** | **Null — recursive self-improvement NOT shown** |
| `regen_gen4` vs `fixed_proposer_gen4` | `-0.0020 +- 0.0042` | `4 / 1 / 0` | `-1.04` | `0.3553` / `0.3750` | Null — Adam distillation (`~13.9k` pass-eq/gen) |
| `exact_gen4` vs `sgd_nesterov_b5600` | `-0.0661 +- 0.0320` | `5 / 0 / 0` | `-4.62` | `0.0099` / `0.0625` | Confounded by `gamma_head` logit damping (loses on Acc) |
| `exact_gen4` vs `adamw_cosine_b5600` | `-0.1274 +- 0.0490` | `5 / 0 / 0` | `-5.82` | `0.0043` / `0.0625` | Confounded by `gamma_head` logit damping (loses `0/5` on Acc) |
| `exact_gen4` vs `damped_lbfgs_b5600` | `-0.1413 +- 0.0300` | `5 / 0 / 0` | `-10.52` | `0.0005` / `0.0625` | Confounded by `gamma_head` (loses on Acc & `0/5` on $R^2$) |

## Held-Out Task Accuracy and Regression $R^2$ (Conventional Controls Win)

On predictive task metrics (classification accuracy across all three classification families, and held-out $R^2$ on `unseen_bottleneck_4layer_reg`), **conventional optimizers beat `exact_gen4` and `regen_gen4`**:
- **`adamw_cosine_b5600` wins on mean classification accuracy in `5/5` seeds** (`48.64%` vs `45.78%`, paired `t = -3.56`, `p = 0.0236`), leading on every classification family (`32.09% vs 30.16%`, `54.34% vs 49.45%`, `59.49% vs 57.74%`).
- **`sgd_nesterov_b5600` beats `exact_gen4` on all three classification families** (`46.87%` vs `45.78%` mean accuracy; wins `4/5` seeds).
- **`damped_lbfgs_b5600` beats `exact_gen4` on `unseen_bottleneck_4layer_reg` $R^2$ in `5/5` seeds** (`+0.619` vs `+0.562`, paired `t = -1.71`, `p = 0.1627`) and on mean classification accuracy (`46.70%` vs `45.78%`).

| Arm (`B = 10` cold passes) | `swiglu_3layer_cls` Acc (Loss) | `synthetic_adapter_bridge` Acc (Loss) | `deep_elu_5layer_cls` Acc (Loss) | Mean 3-Family Cls Acc (`n = 5` Seeds) | `bottleneck_4layer_reg` $R^2$ (MSE) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `gen0` (`M_{Phi_0}`) | `27.41%` (`349.92`) | `44.12%` (`1.819`) | `55.97%` (`1.248`) | `42.50%` | `+0.436` (`0.567`) |
| `exact_gen4` | `30.16%` (`278.79`) | `49.45%` (`1.716`) | `57.74%` (`1.202`) | `45.78%` | `+0.562` (`0.440`) |
| `regen_gen4` | `30.05%` (`278.60`) | `49.16%` (`1.721`) | `57.93%` (`1.199`) | `45.72%` | `+0.558` (`0.444`) |
| `fixed_proposer_gen4` | `30.13%` (`284.72`) | `48.87%` (`1.724`) | `57.74%` (`1.201`) | `45.58%` | `+0.555` (`0.447`) |
| **`sgd_nesterov_b5600`** | `31.46%` (`307.36`) | `50.65%` (`2.082`) | `58.49%` (`1.237`) | **`46.87%`** (`4/5` seeds > `exact`) | `+0.277` (`0.726`) |
| **`adamw_cosine_b5600`** | **`32.09%`** (`544.33`) | **`54.34%`** (`2.589`) | **`59.49%`** (`1.340`) | **`48.64%`** (**`5/5` seeds > `exact`**) | `+0.518` (`0.484`) |
| **`damped_lbfgs_b5600`** | `27.56%` (`723.06`) | `54.13%` (`2.239`) | `58.39%` (`1.329`) | **`46.70%`** (`3/5` seeds > `exact`) | **`+0.619`** (`0.381`, **`5/5` seeds > `exact`**) |

## Requirements for `self_transform_neural_proposer_v3`

1. **Lineage-level design (`S >= 12`)**: Draw disjoint confirmation targets per lineage seed, run at least `12` independent lineage seeds, and make the lineage-level paired test primary.
2. **Co-primary accuracy/$R^2$ & matched head-scale freedom**: Make held-out accuracy/$R^2$ co-primary with loss, and either remove `gamma_head` or grant every baseline identical output-shrinkage / logit-temperature freedom.
3. **Required new baselines**:
   - `zero_head + Adam` with learning rate calibrated beforehand;
   - a constant-step hand rule;
   - a K-FAC / Newton-Schulz preconditioned optimizer *without* the learned proposer network.
4. **Honest compute billing & complete receipts**: Bill meta-query passes (`evaluate_diff_query_v2`) and `regen` FLOPs at the code's actual conversion rate (`~13,900` pass-equivalents), and retain all per-task `rows` in the confirmation receipt.
5. **Real pretrained model bridge & fresh families**: Make at least one confirmation family edit a real pretrained language model, replace all `v1` confirmation families, and change the default `--confirmation-seed-base` so development runs cannot touch confirmation seeds.
6. **Acceptance gates**:
   - *"Improves at proposing"* is met only when `exact` beats `fixed_proposer` significantly at the lineage level (`S >= 12`) and the accepted-proposal rate does not collapse across generations (otherwise report *"meta-training improves a rule"*).
   - *"Beats optimizers"* is met only when `exact` wins on held-out accuracy against all added baselines on the real-model target.

## Reproduction

```bash
.venv/bin/python -m unittest projects/self_transform_neural_proposer_v2/test_proposer_v2.py -v
OMP_NUM_THREADS=1 .venv/bin/python projects/self_transform_neural_proposer_v2/run_study_v2.py \
  --output-json .work/self-transform-neural-proposer-v2/confirmation_receipt_v2.json \
  --confirmation-seed-base 850000 --seeds 101 202 303 404 505 --generations 4 --confirmation-tasks-per-family 16
```
