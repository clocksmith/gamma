# CATSCAN: Multi-lineage self-referential neural proposer study (v3)

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Execute a pre-registered, properly powered (`S = 12` independent lineage seeds, strictly disjoint confirmation targets per seed) head-to-head isolating recursive self-application (`M_{Phi_g}` applied to `Phi_g`) against the identical meta-training pipeline with the update rule held fixed (`M_{Phi_0}` applied to `Phi_g`), and test whether the evolved rule transfers to real-time prompt-derived per-layer LoRA specialization on a stock pretrained `Qwen/Qwen3.5-0.8B` SwiGLU MLP block (retaining the specialty in `Delta W` on prompt-free held-out queries) alongside three unseen nonlinear confirmation families against six matched-budget baselines.

## Literature Positioning

Self-referential learned optimization and meta-learned preconditioning build on established prior work rather than claiming learned optimizers training themselves is new:
- `Metz et al. (2021)` (*Training Learned Optimizers with Randomly Initialized Learned Optimizers*)
- `Irie et al. (2022)` (*A Modern Self-Referential Weight Matrix That Learns to Modify Itself*)
- `Kirsch & Schmidhuber (2022)` (*Eliminating Meta Optimization Through Self-Referential Meta Learning*)
- `Lange et al. (2023)` (self-referential meta-evolution strategies)
- `Bae et al. (2022)` (*Amortized Proximal Optimization*, meta-learned Kronecker/curvature preconditioning)

This lane isolates two specific empirical questions under strict pass/FLOP accounting and zero output-head shrinkage loopholes: (1) whether multi-generational recursive self-application (`exact`) improves over non-recursive `fixed_proposer` across `S = 12` disjoint-target lineages, and (2) whether `M_Phi_v3` beats six matched-budget optimizers—including `zero_head_adam`, `constant_step_rule`, and `kfac_no_proposer`—on held-out accuracy/$R^2$ and real `Qwen/Qwen3.5-0.8B` SwiGLU LoRA prompt-removed skill retention.

## Authority

- Owns [proposer_v3.py](proposer_v3.py), [baselines_v3.py](baselines_v3.py), [worker_v3.py](worker_v3.py), [protocol_v3.json](protocol_v3.json), confirmation runners, tests, and `.work/self-transform-neural-proposer-v3/` receipts.
- Preserves all `v1` and `v2` source files and `.work/` receipts untouched.

## Scope

- `S = 12` lineage seeds (`1001..1012`), `G = 4` cold-subprocess generations (`exact`, `regen`, `fixed_proposer`), `6` matched-budget baselines calibrated at both `exact`-matched (`1,200 * g` passes) and `regen`-matched (`1,400 * g` pass-equivalents) budgets, and `4` unseen confirmation families at `confirmation_seed_base = 9750000` (`>= 5000000` enforced).

## Contracts

- Input: [Gamma research projects charter](../CATSCAN.md), pre-registered [protocol_v3.json](protocol_v3.json) committed before confirmation task generation, and locally provisioned `Qwen/Qwen3.5-0.8B` (`2fc0636`).
- Output: Complete confirmation receipt JSON retaining all per-task `rows`, candidate ledger, exact FLOP/pass conversions, and lineage-level paired `t`, Wilcoxon signed-rank, and sign tests.

## Invariants

- Zero `gamma_head` output-shrinkage parameter anywhere; identical L2 weight-decay freedom across layers.
- Every differentiable meta-query evaluation (`evaluate_diff_query_v3`) is billed (`+1` pass) inside `ChargedTargetOracleV3`, and `regen` FLOPs convert at `ceil(regen_flops / measured_mean_target_pass_flops)`.
- Confirmation seeds (`>= 5000000`, default `9750000`) remain untouched prior to Commit 1 lock.

## Acceptance

- Gate 1 (*Improves at proposing* vs *Meta-training improves a rule*): `exact` beats `fixed_proposer` significantly at the lineage level (`S = 12`) without accepted-proposal rate collapse; otherwise report *meta-training improves a rule* with exact effect size and confidence interval.
- Gate 2 (*Beats optimizers*): `exact` wins on held-out accuracy against all six matched-budget baselines on the real `Qwen/Qwen3.5-0.8B` target; report exact wins, losses, and paired `p`-values honestly either way.

## Non-goals

- Claiming source-code quines, open-ended architecture synthesis, or novelty over `Metz et al. (2021)` / `Kirsch & Schmidhuber (2022)` on the general concept of self-referential optimization.

## Freedom

- Any implementation preserving pre-registered hashes, matched compute budgets, and untouched confirmation splits.
