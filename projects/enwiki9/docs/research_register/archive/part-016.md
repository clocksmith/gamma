# Research Register Archive 016

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-09 - GGML output-head gradient and update parity proposed

Candidate `nncp_ggml_output_head_update_parity_qm0_v1` is the smallest
NNCP-shaped descendant of the passed open GGML substrate. It does not port the
transformer. Instead, it binds the frozen four-state LibNC miniature's teacher
probabilities, initial output matrix and bias, exact named output gradients,
and final output matrix and bias after one source-native update.

The four post-final-normalization hidden states are reconstructed from the
identity `G_W = R H / 4`, where `R` is the teacher
`probability-minus-onehot` matrix and `G_W` is the captured LibNC output-matrix
gradient. A reconstruction residual gate prevents this proof fixture from
claiming information it does not contain. GGML then evaluates only
`hidden -> output projection + bias -> cross entropy`, obtains both parameter
gradients through its CPU backward graph, and applies the frozen LibNC
per-tensor L2 clipping and first Adam update in small counted scalar code.

Promotion requires fixture hash identity, hidden-gradient reconstruction error
at most `2e-6`, GGML output-matrix and bias gradient errors at most `2e-6`
with zero sign mismatches, final updated head errors at most `2e-5`,
byte-identical repeated outputs, no uncounted GGML or accelerator dependency,
compressed source closure at most `2,000,000` bytes, and decimal-memory pass.
Any miss kills this exact head graph, reduction, clipping, and update contract
without optimizer or tolerance sweeps. A pass authorizes the open implementation
substrate for conditional native arm `O` after the production-alphabet bridge
passes; it grants no compression, mature-transfer, or full-model parity credit.

## 2026-08-09 - GGML head q0 isolates an optimizer-period normalization defect

Candidate `nncp_ggml_output_head_update_parity_qm0_v1` reconstructed the frozen
four-state hidden fixture within `2.98e-8` and reproduced the LibNC first Adam
head update within `2.84e-7`. Repeated outputs were byte-identical; the MIT
source closure was `1,170,500` bytes, had no forbidden dynamic dependency, and
used at most `895,304 KiB` sampled process-tree RSS.

The gradient gate failed because the probe set GGML `opt_period=2` but supplied
one physical batch. GGML therefore exposed exactly one-half of the LibNC mean
gradient: diagnostic nonzero-element median ratios were `0.5` for both matrix
and bias, with no sign mismatches. The update still matched because the frozen
first clipped Adam step is invariant to a uniform positive gradient scale.

Verdict: q0 receives zero compression credit and is preserved as a failed
normalization receipt. One immutable q1 child may change only `opt_period` from
`2` to `1` and rerun the complete parity gate. Evidence:
`results/nncp_ggml_output_head_update_parity_qm0_v1/decision.json`, guard
`results/nncp_ggml_output_head_update_parity_qm0_guard_v1.json`, and job
`20260809T234726Z_df6daaf1af`.

## 2026-08-09 - GGML head q1 exposes the direct-optimizer API boundary

Candidate `nncp_ggml_output_head_update_parity_qm1_v1` changed only
`opt_period` from `2` to `1`. GGML then built and executed its direct optimizer
graph, for which `ggml_opt_grad_acc` returned null; the probe exited `12` before
emitting a scientific decision. This is zero compression evidence and does not
reject head parity. One q2 infrastructure child may restore period `2`, submit
the identical logical batch twice, and read the completed accumulator. Evidence:
guard `results/nncp_ggml_output_head_update_parity_qm1_guard_v1.json`, log
`run_logs/adaptive/20260809T235307Z_b80d31c199.log`.
