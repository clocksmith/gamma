# Research Register Archive Part 018

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-08-09 - Branch-residual-weighted cache-32 proposed

Candidate `nncp_branch_residual_cache32_qm0_v1` is a zero-credit compact
distillation test motivated by the exact midpoint/cache joint pass. After each
decoded symbol it stores that occurrence's integer faithful-branch error,
`sum(32768 - realized_mass)`, alongside the symbol in the existing preceding
`32` same-stream cache. Future compatible cache occurrences vote in proportion
to that earlier error before the unchanged `16:1` symbol marginal. Every
quantity is decoder-rebuilt from prior truths and prior faithful
probabilities; no state or source identity is transmitted.

Matched arms are faithful base, the measured unit-weight cache, correctly
associated residual weights, and a cyclic association control that keeps the
same cache symbols and residual-weight multiset but assigns each occurrence
the next occurrence's weight. Promotion requires `10,000` actual bytes over
base, `1,000` bytes over both unit-weight and rotated controls, positive
incremental gain over unit-weight in every original-coordinate third, exact
decode, deterministic replay, and at most `65,536` compressed source bytes.

A miss retires this residual coordinate without weight transform, floor,
window, prior, lag, or bucket sweeps. A pass authorizes one unchanged mature
trace replay, not native integration, a forecast, or score credit. Closed
LibNC remains outside the submission boundary. Proposal:
`operations/adaptive/proposals/developed/000_nncp_branch_residual_cache32_qm0_v1.json`.

## 2026-08-09 - Branch-residual-weighted cache-32 is terminal subscale

Candidate `nncp_branch_residual_cache32_qm0_v1` completed the exact
`262,144`-symbol, `3,670,169`-branch replay. The faithful payload reproduces
at `341,558` bytes. The unit-weight cache reproduces at `332,485` bytes, while
the residual-weighted cache reaches `332,360` bytes. Weighting therefore adds
only `125` actual bytes beyond the already measured cache, with positive but
negligible incremental thirds of `40`, `46`, and `39` bytes.

The rotated-association control is `332,814` bytes. Correct residual-to-symbol
association is therefore real but worth only `454` bytes over the matched
control, below the frozen `1,000`-byte margin. Total weighted gain over the
faithful stream is `9,198` bytes against the `10,000`-byte gate. The candidate
repeat is byte-identical, arithmetic decoding reconstructs every symbol,
compressed source is `10,444` bytes, and the guard passed at `50,428 KiB`
sampled process-tree RSS.

Verdict: retire realized-branch-error weighting, its cyclic association
control, and this unchanged cache/prior construction without error transform,
weight floor, window, prior, lag, or bucket sweeps. The small positive result
does not explain the midpoint/cache joint gain and receives no mature,
forecast, package, or score credit. Evidence:
`results/nncp_branch_residual_cache32_qm0_v1/decision.json`, guard
`results/nncp_branch_residual_cache32_qm0_guard_v1.json`, and job
`20260809T143215Z_cab6534165`.

## 2026-08-09 - Historical FRACTAL-8 survival-hazard result recovered and retired

Adaptive activation of `fractal8_survival_hazard_sigma_qm0_v1` exposed a
pre-existing guarded August 8 result that had not been entered in the shared
register or adaptive proposal index. The no-overwrite retry failed before
scientific execution and receives no compression evidence. The preserved
historical decision and guard remain authoritative.

FRACTAL-8 added consecutive source-survival age, support, vote agreement, and
bit position as decoder-visible reliability coordinates over FRACTAL-7's
persistent addressless sources. A bounded beta-binomial hazard and sleeping
Endpoint428 mixture were applied identically to Sigma, recency,
shuffled-source, and byte-8 arms on `6,251,852` WRT bytes, `5,139,821` events,
and `50,014,816` exact parent rows.

The Sigma hindsight ceiling remains `325,190.856` bytes and its minimum ceiling
margin remains `28,016.905`, passing both frozen ceiling gates. Causal gain is
instead `-109.946` bytes, with chronological thirds `-35.129`, `-36.813`, and
`-38.004`. The minimum causal control margin is `-74.485` bytes. Peak sampled
single-process RSS was `538,640 KiB`; the guard completed without violation.

The emitted decision schema incorrectly names FRACTAL-7. This is a preserved
clerical source bug, not rewritten evidence: the directory, guard label,
`SIGMA_HAZARD` arm, measured binary, and source hash bind the result to
FRACTAL-8 in `historical_binding.json`. The exact measured C++ source identity
is restored rather than patched beneath the receipt.

Verdict: retire survival age, support, agreement, bit-position hazard, frozen
priors, mixture share, suffixes, and state cap without sweeps. Source survival
does not explain the gap between hindsight redundancy and causal prediction.
Score and forecast credit remain zero. Evidence:
`results/fractal8_survival_hazard_sigma_qm0_v1/decision.json`,
`results/fractal8_survival_hazard_sigma_qm0_v1/guard.json`, and
`results/fractal8_survival_hazard_sigma_qm0_v1/historical_binding.json`.
