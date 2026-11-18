# Multi-Lineage Self-Referential Neural Proposer Study v3 (`self_transform_neural_proposer_v3`)

Charter: [CATSCAN.md](CATSCAN.md) | Core Protocol Lock (`Commit 1`: `72ac6685b`): [protocol_v3.json](protocol_v3.json) | Additive Asset/Driver Lock (`Commit 2`: `9eb26c204`): [protocol_addendum_v3.json](protocol_addendum_v3.json)

> **Track B2 Verdict (`S = 12` Disjoint-Target Lineages, `576` Unique Confirmation Tasks, `36,864` Retained Rows): Meta-Training Improves a Rule (`12/12` seeds, `p = 2.62e-6`); Recursive Self-Application (`p = 0.6566`) and General Optimizer Superiority (`kfac_no_proposer` wins `12/12` seeds) Are Refuted.**
>
> Under the pre-registered two-commit protocol (`72ac6685b` -> `9eb26c204`), `self_transform_neural_proposer_v3` resolves every methodological confound identified in `v2`:
> 1. **Gate 1 (`exact` vs `fixed_proposer` — *"Meta-training improves a rule"*)**: Meta-training significantly improves the `1,688`-parameter proposer `M_Phi_v3` from `Gen 0` to `Gen 4` across **`12/12` independent seeds** on normalized loss (`0.6092 -> 0.5902`, `t = -8.80`, `p = 2.62e-6`, exact Wilcoxon `p = 0.000488`), classification accuracy (`38.71% -> 43.43%`, `t = +18.60`, `p = 1.16e-9`), and real pretrained `Qwen/Qwen3.5-0.8B` SwiGLU LoRA prompt-removed accuracy (`40.82% -> 48.59%`, `t = +10.12`, `p = 6.57e-7`). However, **recursive self-application (`exact_gen4`, `M_{Phi_g}` modifying `Phi_g`) shows no statistically significant gain over `fixed_proposer_gen4` (`M_{Phi_0}` modifying `Phi_g`)** (`0.5902` vs `0.5912` norm loss, `t = -0.46`, `p = 0.6566`; `43.43%` vs `43.63%` cls acc, `t = -0.58`, `p = 0.5716`; `48.59%` vs `48.73%` real `Qwen3.5-0.8B` acc, `t = -0.27`, `p = 0.7918`).
> 2. **Gate 2 (`exact` vs Six Matched-Budget Baselines — Preconditioning Drives the Gain, Not `Phi`)**: On the real pretrained `Qwen/Qwen3.5-0.8B` Layer-23 SwiGLU LoRA target (`B = 10` support steps, prompt removed at query time), `exact_gen4` (`48.59%`) beats `sgd_nesterov` (`20.73%`, `12/0`, `p = 1.33e-12`), `damped_lbfgs` (`32.91%`, `12/0`, `p = 1.41e-6`), and `constant_step_rule` (`40.76%`, `11/1`, `p = 0.0041`), and leads `adamw_cosine` (`46.91%`, `8/4`, `p = 0.1027`) and `zero_head_adam` (`46.55%`, `8/4`, `p = 0.0742`) without `gamma_head`. Crucially, **`kfac_no_proposer` (`51.25%` real Qwen acc, `45.77%` cls acc, `0.5543` norm loss)—which uses the identical 5-basis Woodbury K-FAC + Newton-Schulz + Adam preconditioning with calibrated scalar weights and *no* neural proposer network—beats `exact_gen4` on `12/12` seeds (`p = 0.00041`)**, isolating the empirical capability to the preconditioned curvature basis rather than the learned `1,688`-parameter gate network.

## Post-Seal Review Note (2026-11-17, not part of the pre-registered analysis)

Two limits on what this study shows, both checked against the code and the receipt:

- `real_qwen35_swiglu_lora_cls` is not an edit of the running model. `tasks_b2_v3.py` averages
  the token embeddings of each sentence into one vector, normalises it, and passes it through
  the layer-23 MLP alone, with a readout over six codeword tokens. No attention layer and no
  full forward pass is involved. The weights are real; the model is not being run.
- On that family the recursive proposer at generation 4 scores `48.59%` against `48.73%` for
  the fixed proposer (5 wins, 7 losses over 12 lineages, paired `t` `p = 0.79`), and `51.25%`
  for `kfac_no_proposer` (0 wins, 12 losses, `p = 0.0004`).

The experiment is finished; the goal of hereditary self-improvement is not met. A successor
needs a mechanism for why self-application should help, and a target evaluated through the
full model.

## Literature Positioning

Learned optimizers training themselves and self-modifying update rules are established results in prior literature:
- `Metz et al. (2021)` (*Training Learned Optimizers with Randomly Initialized Learned Optimizers*)
- `Irie et al. (2022)` (*A Modern Self-Referential Weight Matrix That Learns to Modify Itself*)
- `Kirsch & Schmidhuber (2022)` (*Eliminating Meta Optimization Through Self-Referential Meta Learning*)
- `Lange et al. (2023)` (self-referential meta-evolution strategies)
- `Bae et al. (2022)` (*Amortized Proximal Optimization*, meta-learned Kronecker preconditioning)

`v3` makes no claim of inventing self-referential optimization. Its contribution within Gamma is a **powered (`S = 12` disjoint-target lineages), pre-registered, zero-loophole head-to-head** separating (a) meta-training an update rule, (b) recursive self-application `M_{Phi_g}(Phi_g)` vs fixed `M_{Phi_0}(Phi_g)` under identical curriculum and selection, and (c) neural gating `Phi` vs the underlying `kfac_no_proposer` preconditioned basis on a real pretrained Transformer block.

## Methodological Repairs Over `v2`

1. **Two-Commit Pre-Registration Before Opening Confirmation Seeds**:
   - `Commit 1` (`72ac6685b`) froze `proposer_v3.py`, `baselines_v3.py`, `worker_v3.py`, and `protocol_v3.json` before `tasks_b2_v3.py` was committed.
   - `Commit 2` (`9eb26c204`) bound SHA-256 digests of `tasks_b2_v3.py`, `run_study_v3.py`, and the locally provisioned stock `Qwen/Qwen3.5-0.8B` (`2fc0636`) safetensors (`04b1c301...`) and `tokenizer.json` (`5f9e4d49...`) before `--execute` ran.
2. **Lineage-Level Unit of Inference (`S = 12`) & Disjoint Confirmation Targets**:
   - `12` independent lineage seeds (`1001..1012`), each evaluated on its own strictly disjoint confirmation seed block (`9750000 + seed_idx * 10000 + fam_idx * 1000 + task_idx`, `48` unique tasks/seed = **`576` completely distinct confirmation tasks**; `>= 5,000,000` enforced so development runs never touch confirmation seeds).
   - No pseudoreplicated `320`/`576`-pair p-values are computed; primary inference uses two-sided paired `t` (`df = 11`), exact two-sided Wilcoxon signed-rank (`2^12 = 4,096` enumerations), and exact sign tests across the `12` independent lineage means.
3. **Zero `gamma_head` Loophole & Co-Primary Accuracy/$R^2$**:
   - `gamma_head` is removed (`gamma_head_present = false`); every layer shares the identical small L2 weight-decay gate (`<= 0.03` on non-bias columns). Held-out classification accuracy and regression $R^2$ are co-primary with normalized loss.
4. **Six Matched-Budget Baselines & Complete Pass/FLOP Billing**:
   - Every `evaluate_diff_query_v3` pass during meta-training is billed inside `ChargedTargetOracleV3` (`11` passes/train task -> exact `1,160` passes/gen = `4,640` at `Gen 4`).
   - `regen` (`96` Gaussian probes x `60` Adam distillation steps = `58,661,376` analytic FLOPs) converts at the measured curriculum target-pass rate (`ceil(58,661,376 / 286,515) = 205` pass-equivalents/gen -> `1,365` pass-equivalents/gen = `5,460` at `Gen 4`).
   - All six baselines (`sgd_nesterov`, `adamw_cosine`, `damped_lbfgs`, `zero_head_adam`, `constant_step_rule`, and `kfac_no_proposer`) are calibrated beforehand per seed at both `exact_matched` (`1,200 * g` = `4,800` passes) and `regen_matched` (`1,400 * g` = `5,600` pass-equivalents) budgets.
   - All `36,864` per-task evaluation `rows` are retained in `.work/self-transform-neural-proposer-v3/confirmation_receipt_v3.json`.
5. **Real Pretrained Model Bridge + Fresh Nonlinear Families**:
   - `real_qwen35_swiglu_lora_cls`: Tokenizes natural multi-domain English sentences with stock `Qwen/Qwen3.5-0.8B` (`2fc0636`), embeds through real `embed_tokens` + `layers.23.post_attention_layernorm` + full-width `1024 -> 3584 -> 1024` Layer-23 SwiGLU MLP (`gate_proj`, `up_proj`, `down_proj`), and adapts a rank-`12` LoRA `(A_down, B_down=0)` into `norm` + frozen `embed_tokens` codeword unembeddings in `B = 10` support steps, scoring unseen prompt-free queries.
   - Three fresh unseen families (`0` overlap with `v1` or `v2`): `fourier_kan_multifreq_reg`, `bilinear_gated_interaction_cls`, and `layernorm_residual_gelu_cls`.

## Generational Curves (`S = 12` Independent Lineages)

Accepted-proposal rates across `Gen 1 -> Gen 2 -> Gen 3 -> Gen 4` were `60.0% -> 50.0% -> 35.0% -> 35.0%` (`exact`), `60.0% -> 60.0% -> 45.0% -> 46.7%` (`regen`), and `60.0% -> 50.0% -> 36.7% -> 46.7%` (`fixed_proposer`).

| Lineage (`S = 12` Mean `+-` SD) | `Gen 0` ( Norm / Cls Acc ) | `Gen 1` | `Gen 2` | `Gen 3` | `Gen 4` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `exact` (`M_{Phi_g}` recursive, `1.16k * g` passes) | `0.6092 +- 0.0151` (`38.7%`) | `0.5990 +- 0.0147` (`43.5%`) | `0.5992 +- 0.0166` (`43.9%`) | `0.5903 +- 0.0136` (`43.7%`) | `0.5902 +- 0.0128` (`43.4%`) |
| `regen` (Adam probe distill, `1.365k * g` pass-eq) | `0.6092 +- 0.0151` (`38.7%`) | `0.5983 +- 0.0169` (`42.8%`) | `0.6014 +- 0.0197` (`43.2%`) | `0.6000 +- 0.0215` (`43.5%`) | `0.5957 +- 0.0223` (`42.5%`) |
| `fixed_proposer` (`M_{Phi_0}` fixed rule, `1.16k * g`) | `0.6092 +- 0.0151` (`38.7%`) | `0.5990 +- 0.0147` (`43.5%`) | `0.5983 +- 0.0158` (`43.8%`) | `0.5938 +- 0.0146` (`44.0%`) | `0.5912 +- 0.0142` (`43.6%`) |

## Generation-4 Per-Family Breakdown (`S = 12` Seeds x `48` Disjoint Tasks = `576` Unique Targets)

| Arm (`B = 10` Cold Support Passes) | Pooled Norm Loss (`+-` SD) | Mean 3-Cls Acc | `real_qwen35_swiglu_lora_cls` (Norm / Acc) | `fourier_kan_multifreq_reg` (Norm / $R^2$) | `bilinear_gated_interaction_cls` (Norm / Acc) | `layernorm_residual_gelu_cls` (Norm / Acc) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `gen0` (`M_{Phi_0}` untrained) | `0.6092 +- 0.0151` | `38.71%` | `0.667` / `40.82%` | `0.250` / `+0.601` | `0.797` / `23.70%` | `0.722` / `51.62%` |
| `exact_gen4` (`4,640` passes) | `0.5902 +- 0.0128` | `43.43%` | `0.657` / `48.59%` | `0.228` / `+0.640` | `0.850` / `24.15%` | `0.627` / `57.55%` |
| `regen_gen4` (`5,460` pass-eq) | `0.5957 +- 0.0223` | `42.45%` | `0.667` / `45.93%` | `0.224` / `+0.646` | `0.851` / `24.57%` | `0.640` / `56.87%` |
| `fixed_proposer_gen4` (`4,640` passes) | `0.5912 +- 0.0142` | `43.63%` | `0.664` / `48.73%` | `0.225` / `+0.644` | `0.847` / `24.61%` | `0.629` / `57.54%` |
| `sgd_nesterov` (`4,800` exact-matched) | `0.6719 +- 0.0201` | `33.30%` | `0.886` / `20.73%` | `0.290` / `+0.536` | `0.841` / `25.29%` | `0.671` / `53.87%` |
| `adamw_cosine` (`4,800` exact-matched) | `0.8458 +- 0.1007` | `43.98%` | `1.697` / `46.91%` | `0.215` / `+0.657` | `0.876` / `25.86%` | `0.595` / `59.17%` |
| `damped_lbfgs` (`4,800` exact-matched) | `0.6136 +- 0.0321` | `38.93%` | `0.779` / `32.91%` | `0.245` / `+0.609` | `0.839` / `24.04%` | `0.591` / `59.83%` |
| `zero_head_adam` (`4,800` exact-matched) | `0.7776 +- 0.1376` | `43.88%` | `1.456` / `46.55%` | `0.176` / `+0.724` | `0.871` / `26.07%` | `0.608` / `59.01%` |
| `constant_step_rule` (`4,800` exact-matched) | `0.6130 +- 0.0592` | `41.53%` | `0.958` / `40.76%` | `0.205` / `+0.675` | `0.669` / `25.57%` | `0.621` / `58.27%` |
| **`kfac_no_proposer` (`4,800` exact-matched)** | **`0.5543 +- 0.0239`** | **`45.77%`** | **`0.759` / `51.25%`** | **`0.164` / `+0.741`** | **`0.681` / `26.72%`** | `0.613` / `59.35%` |
| `kfac_no_proposer` (`5,600` regen-matched) | `0.5558 +- 0.0238` | `45.64%` | `0.763` / `51.09%` | `0.164` / `+0.740` | `0.683` / `26.50%` | `0.613` / `59.33%` |

## Primary Lineage-Level Paired Statistical Tests (`S = 12`, `df = 11`)

| Comparison (`Focal` vs `Reference`) | Norm Loss Diff (`+W/-L`, `t`, `p_t` / `p_wilc`) | 3-Cls Acc Diff (`+W/-L`, `t`, `p_t` / `p_wilc`) | Real `Qwen3.5-0.8B` LoRA Acc Diff (`+W/-L`, `t`, `p_t` / `p_wilc`) | Verdict |
| :--- | :---: | :---: | :---: | :--- |
| `exact_gen4` vs `gen0` | `-0.0190` (`+12/-0`, `t=-8.80`, `2.62e-6` / `4.88e-4`) | `+4.72%` (`+12/-0`, `t=+18.60`, `1.16e-9` / `4.88e-4`) | `+7.77%` (`+12/-0`, `t=+10.12`, `6.57e-7` / `4.88e-4`) | **Significant** (`meta-training improves a rule`) |
| `exact_gen4` vs `exact_gen1` | `-0.0089` (`+10/-2`, `t=-3.43`, `0.0056` / `0.0093`) | `-0.03%` (`+4/-8`, `t=-0.14`, `0.890` / `0.380`) | `-0.57%` (`+4/-8`, `t=-0.97`, `0.355` / `0.412`) | Loss improves post-`Gen 1`; accuracy flat |
| **`exact_gen4` vs `fixed_proposer_gen4`** | **`-0.0011` (`+8/-4`, `t=-0.46`, `0.657` / `0.470`)** | **`-0.20%` (`+8/-4`, `t=-0.58`, `0.572` / `0.850`)** | **`-0.14%` (`+5/-7`, `t=-0.27`, `0.792` / `1.00`)** | **Null — Gate 1 ("improves at proposing") NOT met** |
| `regen_gen4` vs `fixed_proposer_gen4` | `+0.0044` (`+5/-7`, `t=+1.01`, `0.334` / `0.424`) | `-1.17%` (`+2/-10`, `t=-1.63`, `0.132` / `0.110`) | `-2.80%` (`+2/-10`, `t=-2.23`, `0.0476` / `0.0522`) | Probe distillation trails direct weights |
| `exact_gen4` vs `sgd_nesterov` | `-0.0818` (`+12/-0`, `t=-15.70`, `7.06e-9` / `4.88e-4`) | `+10.13%` (`+12/-0`, `t=+25.07`, `4.67e-11` / `4.88e-4`) | `+27.86%` (`+12/-0`, `t=+34.78`, `1.33e-12` / `4.88e-4`) | `exact_gen4` wins all metrics |
| `exact_gen4` vs `damped_lbfgs` | `-0.0234` (`+10/-2`, `t=-2.84`, `0.0161` / `0.0068`) | `+4.50%` (`+12/-0`, `t=+6.47`, `4.63e-5` / `4.88e-4`) | `+15.68%` (`+12/-0`, `t=+9.37`, `1.41e-6` / `4.88e-4`) | `exact_gen4` wins all metrics |
| `exact_gen4` vs `constant_step_rule` | `-0.0229` (`+8/-4`, `t=-1.40`, `0.189` / `0.424`) | `+1.90%` (`+8/-4`, `t=+2.15`, `0.0542` / `0.0771`) | `+7.82%` (`+11/-1`, `t=+3.61`, `0.0041` / `0.0015`) | `exact_gen4` wins on real `Qwen3.5` LoRA |
| `exact_gen4` vs `adamw_cosine` | `-0.2556` (`+12/-0`, `t=-8.83`, `2.52e-6` / `4.88e-4`) | `-0.55%` (`+2/-10`, `t=-1.00`, `0.338` / `0.0923`) | `+1.68%` (`+8/-4`, `t=+1.78`, `0.103` / `0.129`) | Loss win; Qwen3.5 acc `+1.68%` NS |
| `exact_gen4` vs `zero_head_adam` | `-0.1875` (`+12/-0`, `t=-4.91`, `4.66e-4` / `4.88e-4`) | `-0.44%` (`+3/-9`, `t=-1.00`, `0.340` / `0.339`) | `+2.04%` (`+8/-4`, `t=+1.97`, `0.0742` / `0.105`) | Loss win; Qwen3.5 acc `+2.04%` NS |
| **`exact_gen4` vs `kfac_no_proposer`** | **`+0.0359` (`+1/-11`, `t=+5.90`, `1.03e-4` / `0.0015`)** | **`-2.34%` (`+0/-12`, `t=-7.23`, `1.69e-5` / `4.88e-4`)** | **`-2.66%` (`+0/-12`, `t=-4.99`, `4.06e-4` / `4.88e-4`)** | **`kfac_no_proposer` wins `12/12` seeds — Gate 2 NOT met** |

## Reproduction

```bash
.venv/bin/python -m unittest projects/self_transform_neural_proposer_v3/test_proposer_v3.py -v
.venv/bin/python projects/self_transform_neural_proposer_v3/run_study_v3.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python projects/self_transform_neural_proposer_v3/run_study_v3.py \
  --execute --output .work/self-transform-neural-proposer-v3 --workers 6
```
