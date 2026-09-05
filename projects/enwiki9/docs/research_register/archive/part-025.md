# Research Register Archive 025

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-16 - The first remaining divergence is the FF2 transpose

Candidate `nncp_libnc_top_ff2_input_adjoint_64_q0_v1` placed a marked zero
probe on the production layer-19 GEGLU output immediately before `ff2_19` and
captured its complete backward adjoint twice. The frozen comparison withheld
the open residual until both source populations were complete and preserved
all non-probe fixture payloads.

The experiment is valid and its byte-identity hypothesis is refuted. Both
source captures replay exactly, expose all 6,291,456 expected BF16 input and
adjoint words, leave the production fixture unchanged, retain a live
comparator, and pass strict output, source, memory, scratch, and cleanup
guards. The source adjoint nevertheless differs from the open streaming
transpose residual in 775 words, with maximum absolute error
`2.9802322387695312e-08`. See the
[`decision`](../../../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json).

This is the first measured divergence after the exact final-RMSNorm adjoint
and exact `ff2_19` parameter gradient. GEGLU backward is downstream of an
already-nonexact residual and is therefore not needed to explain the retained
`ff_bias1_19` mismatch. The current eight-lane streaming transpose is retired
as source-exact, but FF2 transpose itself is not. The next gate must compare
frozen arithmetic variants against the captured source adjoint before GEGLU
is reopened. This source oracle has zero objective credit and proves no
recursive update, compression improvement, transfer, package, or Hutter
result.

## 2026-08-16 - The first open GEGLU backward contract is refuted

Candidate `nncp_open_profile_top_ff1_bias_gradient_64_q0_v1` started from the
promoted exact final-RMSNorm input residual, regenerated both complete forward
populations with fresh layer-19 FF1 outputs, and applied one frozen backward
contract: streaming BF16 FF2-transpose dots, a BF16 transpose-output boundary,
the measured unfused tanh-GELU derivative, and explicit BF16 product
boundaries. The retained `ff_bias1_19` gradient remained unavailable until both
open projections were complete.

The experiment is valid and the hypothesis is refuted. Both populations and
their complete FF2-input and FF1-output residuals replay byte-for-byte, all
forward checkpoints remain exact, the sign-negated control changes, strict
outputs validate, and dependency, source, memory, scratch, and cleanup guards
pass. Nevertheless, 4,708 of 6,144 retained `ff_bias1_19` BF16 words differ,
with maximum absolute error `1.52587890625e-05`. Both the gate and value halves
contain mismatches, so the bias projection alone cannot distinguish the shared
FF2-transpose adjoint from branch-specific GEGLU arithmetic. See the
[`decision`](../../../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T084751Z_2949ede196.json).

This retires the combined contract, not FF2 transpose or GELU individually.
The next justified experiment must capture or independently validate the
production FF2-input adjoint before changing activation arithmetic. Tuning
against the retained bias vector is forbidden. This result has zero objective
credit and proves no FF1 matrix gradient, earlier-layer backward, recursive
update, compression improvement, transfer, package, or Hutter result.

## 2026-08-16 - The open tail is exact through the top FF2 gradient

Candidate `nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1` installed
only the source-attributed streaming eight-lane FMA reduction at the final
RMSNorm `g*y` dot. Its first job stopped during digest-bound preflight because
the wrapper retargeted an inherited antecedent checker; no scientific payload
was produced. The first immutable retry completed both populations and every
scientific comparison, but strict validation rejected its result because the
cloned output manifest still named the ancestor candidate. Both failures are
retained as implementation evidence in their terminal
[`preflight reflection`](../../../operations/adaptive/reflections/20260816T080014Z_9da1ba0532.json)
and
[`manifest reflection`](../../../operations/adaptive/reflections/20260816T080451Z_d5838c6e4e.json).

The manifest-only second retry preserved the C++ algorithm byte-for-byte and
reran the complete guarded population. The prospectively frozen gate passed
every predicate. Two independent 32-stream executions preserve all inherited
forward, output-head, final-normalization parameter, and projection results;
the complete final-RMSNorm input residual matches the independent source
adjoint in all 2,097,152 BF16 words; and all 3,145,728 retained `ff2_19`
gradient words are exact. Replay is deterministic, the residual-negation and
FF2-negation controls remain live, the strict nine-output manifest validates,
and dependency, source, memory, and scratch guards pass. See the
[`decision`](../../../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/execution.json),
[`guard`](../../../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json).

This opens the production backward tail from the output head through final
RMSNorm and the top-layer FF2 parameter gradient. It remains a zero-credit
teacher-removal result. It proves no FF2 input residual, GEGLU derivative,
`ff1_19` or bias gradient, earlier transformer backward, recursive update,
compression improvement, transfer, package, or Hutter result. The next frozen
boundary is the FF2 transpose residual through GEGLU into the top-layer FF1
and bias gradients.

## 2026-08-16 - The final RMSNorm discrepancy is the product reduction

The four-cell
`nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1` attribution crossed two
product-reduction orders with two algebraically equivalent scalar placements.
Both generic block-combined dot cells reproduced the retained open residual
and differed from the source adjoint in the same 8 BF16 words. Both ordered
eight-lane streaming FMA cells reproduced the independent source adjoint
exactly. Mean-scaled versus width-scaled placement was BF16-identical across
the complete population, so the frozen uniqueness hypothesis was refuted even
though the causal boundary became sharper.

This retires generic 64-element block combination as a source-equivalent
implementation of the final-RMSNorm `g*y` dot and retires scalar placement as
the cause on this population. It authorizes one uniform streaming reduction,
not coordinate patches or tolerance. See the
[`decision`](../../../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T075342Z_b33521b4a0.json).

The attribution uses retained source tensors only as post-completion
comparators and has zero objective credit. No source executable, captured
adjoint, gradient, trace, or probability may enter a submitted codec.

## 2026-08-16 - The production top-layer FF2 adjoint is localized

The first `nncp_libnc_top_ff2_adjoint_64_q0_v1` job stopped before measurement:
its probe definitions were below their first call sites and lacked forward
declarations. The terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T064522Z_bd9f01360c.json)
classifies that compiler failure as implementation evidence and preserves the
unchanged scientific predicates.

The declaration-only retry attached a zero-valued marked parameter after the
production layer-19 FF2 bias at the first retained update. Two complete source
executions each emitted the same 757-file population and aggregate hash. Every
non-probe file remained byte-identical to the retained production fixture, and
the combined source FF2 inputs, post-FF2 adjoints, reconstructed gradients, and
sign-negated controls replayed byte-for-byte.

The attribution is exact. Source input plus source adjoint under the frozen
128-sample reducer reproduces all 3,145,728 retained `ff2_19` BF16 words with
zero error. The open final-normalization input residual differs from the source
post-FF2 adjoint in 8 of 2,097,152 words across 8 output features, with maximum
absolute error `2.9802322387695312e-08`. This retires FF2 outer-product
reduction order as the cause of the prior 184-word mismatch and moves the next
boundary to an operation-level decomposition of the open final RMSNorm
per-sample adjoint. See the retry
[`decision`](../../../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/guard.json), and
terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T065037Z_1d8853ab41.json).

This source capture is a zero-credit attribution oracle. No teacher
executable, LibNC dependency, captured tensor, gradient, trace, or probability
may ship in a submitted codec, and no compression, transfer, package, or
Hutter result follows.

## 2026-08-16 - The first top-layer FF2 reduction is narrowly refuted

Candidate `nncp_open_profile_top_ff2_gradient_64_q0_v1` retained the complete
exact output-head and final-normalization tails, exposed fresh BF16 layer-19
GEGLU outputs, and applied the promoted 128-sample output-head matrix-gradient
reduction directly to the complete `ff2_19` outer product. Both 32-stream
executions were byte-identical, every inherited comparator remained exact,
both negative controls changed, and dependency, source, memory, scratch, and
finalization guards passed.

The FF2 claim itself failed exactly: 184 of 3,145,728 retained BF16 words
differed, with maximum absolute error `9.5367431640625e-07`. This valid result
localizes the remaining discrepancy to operation-specific FF2 product or
reduction semantics. It retires direct reuse of the output-head reduction
without an FF2-specific arithmetic boundary; it does not weaken exact parity
or authorize tolerance. See the
[`decision`](../../../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T055603Z_52a69ff065.json).

The first immutable retry tested a uniform BF16 boundary after the final
RMSNorm incoming-gradient times gain product. It was a valid numerical no-op:
the digest-bound initial `ln_g_40` tensor is BF16 `1.0` in every coordinate,
and the retry reproduced both the normalization-input residual and `ff2_19`
gradient artifact hashes byte-for-byte, including the same mismatch set. This
retires that boundary at the selected update. See its
[`decision`](../../../results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json).

This experiment has zero Hutter objective credit. The next justified gate is
a zero-credit source capture of the actual production post-FF2 residual-join
adjoint. It must compare that complete per-sample tensor with the open
normalization-input residual before another arithmetic retry is authorized.

## 2026-08-16 - The complete final RMSNorm backward tail is open and exact

The first `nncp_open_profile_final_norm_backward_64_q0_v1` execution generated
both full open populations but failed during result finalization because its
runner removed the work tree before reading cached element counts. Its
terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T045714Z_6eb299ed8d.json)
classifies that attempt as an implementation failure rather than scientific
evidence.

The first immutable retry fixed finalization, applied the already measured
concat-root centered RMSNorm input rule, and changed `ln_g_40` to the promoted
chunked reduction. Its valid result isolated two different outcomes. The
centered input residual reproduced every retained top-layer `ff_bias2_19`
projection word exactly, but the gain gradient retained the same mismatches as
the unchunked attempt. This retired reduction reassociation as the gain cause.
See its
[`decision`](../../../results/nncp_open_profile_final_norm_backward_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T051419Z_4df92ec3b4.json).

Candidate `nncp_open_profile_final_norm_backward_64_q0_retry_v2` changed one
remaining boundary: every per-sample normalized-state times incoming-gradient
product is rounded to BF16 before the unchanged reduction. The prospectively
frozen gate then passed every predicate. Both full executions reproduce all
retained output-head gradients, the promoted final-hidden residual, all
`ln_g_40` and `ln_b_40` words, and all `ff_bias2_19` projection words exactly.
The complete centered normalization-input residual replays byte-for-byte, both
negative controls remain live, the open executables have no forbidden dynamic
dependency, and source and resource guards pass. See the
[`decision`](../../../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/execution.json),
[`guard`](../../../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T053159Z_b79233ecb1.json).

This opens the complete production final-normalization affine and centered
input-backward tail. It proves no FF2 activation residual, GEGLU backward,
earlier normalization, attention, recursive training, transfer, archive
score, package eligibility, or full-corpus reconstruction and has zero Hutter
objective credit. The next frozen boundary is the complete top-layer
`ff2_19` parameter gradient from the exact normalization-input residual and a
fresh open GEGLU output.

## 2026-08-16 - The complete output-head activation residual is open

Candidate `nncp_open_profile_final_hidden_residual_64_q0_v1` advances the
exact open BF16 loss residual through the digest-bound initial `embed_out`
transpose. The standalone reducer consumes only decoder-visible targets,
freshly generated probabilities and final hidden states, and initial
parameters. It generates both complete activation-residual payloads before
hash-verifying or reading any retained gradient comparator.

The prospectively frozen gate passed every predicate. Two independent
32-stream executions emitted byte-identical 2,097,152-word BF16 final-hidden
residuals. Their broadcast reductions reproduce all 1,024 retained `ln_b_40`
gradient words exactly, while both previously promoted output-head parameter
gradients remain exact and the cyclic target-shift control changes. The open
executables have no forbidden dynamic dependency, the dependency-closed
incremental source remains within its frozen ceiling, and the guarded work
tree was removed. See the
[`decision`](../../../results/nncp_open_profile_final_hidden_residual_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_final_hidden_residual_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_final_hidden_residual_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T043203Z_ca54b4761d.json).

This independently validates the complete output-head activation residual by
an exact retained final-normalization bias projection. It does not provide a
direct retained comparator for every per-sample residual word and proves no
final-normalization gain or input gradient, transformer-layer backward,
recursive training, transfer, archive score, package eligibility, or
full-corpus reconstruction. It has zero Hutter objective credit. The next
frozen boundary reconstructs `ln_g_40` and the final-normalization input
residual separately, using the retained top-layer `ff_bias2_19` gradient as an
independent projection before entering the transformer block.

## 2026-08-16 - The complete output-head parameter gradient is open and exact

Candidate `nncp_open_profile_output_matrix_gradient_64_q0_v1` advances the
promoted BF16 loss residual through the complete open final hidden state. The
standalone reducer consumes only digest-bound initial parameters and state,
decoder-visible targets, and freshly generated probabilities and hidden
states. Both retained gradient comparators are hash-verified only after two
complete open payloads exist.

The prospectively frozen gate passed every predicate. Two independently built
32-stream executions match all 640 layer-input checkpoints, all 16,392
`out_bias` gradient words, and all 16,785,408 `embed_out` gradient words
exactly. Both gradients and the forward trees replay byte-for-byte, while a
cyclic target remap changes an independently reduced matrix slice. The open
executables have no forbidden dynamic dependency, the counted incremental
source remains below its frozen ceiling, and the guarded work tree is removed.
See the
[`decision`](../../../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T040455Z_f7722f8e27.json).

This removes the complete output-head parameter-gradient tail from the closed
teacher. It does not yet prove the residual propagated into the final hidden
state, normalization backward, any transformer layer, recursive training,
transfer, archive size, package eligibility, or full-corpus reconstruction. It
has zero Hutter objective credit. The next frozen boundary is the
`embed_out`-transpose activation residual, independently checked through the
retained final-normalization bias gradient before any deeper-backward claim.

## 2026-08-15 - The production loss-to-output-bias backward tail is exact

The first all-stream open backward attempt completed both forward populations
but failed before evidence finalization because its source packer treated a
candidate-owned materializer as a project tool. It also exposed a control-design
error: permuting target states preserves the target histogram and therefore
cannot change a bias-only gradient. The failed job and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T031213Z_57a9477621.json)
retain those defects as implementation evidence; its scientific hypothesis was
not tested.

Diagnosis from the independently generated outputs localized the remaining
arithmetic boundary. The production graph converts each per-sample F32 softmax
residual to BF16 before reducing the broadcast output bias. An F32-only
reduction was close but not identical. Candidate
`nncp_open_profile_output_bias_gradient_64_q0_retry_v1` preserves the complete
forward and loss population, applies that BF16 boundary explicitly, packages
candidate source without broadening the tool closure, and replaces the dead
state permutation with a cyclic vocabulary-successor target remap.

The guarded retry passed every frozen predicate. Two independently rebuilt
32-stream populations match all 640 retained layer-input checkpoints and all
16,392 BF16 output-bias gradient words exactly, with zero maximum error,
byte-identical replay, a live negative control, no forbidden dynamic
dependency, and a dependency-closed source package below its frozen ceiling.
See the
[`decision`](../../../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T033450Z_727c49438a.json).

This proves only the production negative-log-likelihood tail through
`out_bias`. It has zero objective credit and proves no output-matrix,
normalization, transformer-layer, embedding, recursive-training, archive,
transfer, package, or full-corpus result. The next teacher-removal boundary is
the output-matrix gradient and hidden-state residual generated from this exact
open BF16 logit residual.

## 2026-08-15 - One causal open production segment transition is exact

The post-update boundary is no longer an incumbent-state-only forward probe.
The retained post-update fixture first exposed a small arithmetic mismatch:
the complete open forward matched all tensors, while a scalar left-fold tree
reduction changed a subset of integer branch counts. Focused candidate
`nncp_open_branch_reduction_postupdate_64_q0_retry_v2` proved that the
previously promoted LibNC-order reducer eliminates the difference. Candidate
`nncp_ggml_postupdate_forward_parity_64_q1_retry_v2` then replayed the complete
retained next segment twice with exact tensor, topology, truth-path, and branch
parity. See its
[`decision`](../../../results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json).

The first joint integration attempt was deliberately retained as an
implementation failure. Its canonical Adam reports and all recurrent-memory
layers were exact, but a separately duplicated output loop emitted `203`
parameter payloads differently. The resulting next-forward error was therefore
not evidence against the open update. Its
[`decision`](../../../results/nncp_open_profile_update_forward_chain_64_q0_v1/decision.json)
and
[`reflection`](../../../operations/adaptive/reflections/20260816T023511Z_83fa6c7a64.json)
record the non-equivalent treatment and authorize only an emitter retry.

Candidate `nncp_open_profile_update_forward_chain_64_q0_retry_v1` removes that
duplicate arithmetic. A reproducible source patch writes each predicted word
from the canonical exact Adam replay function immediately before its existing
comparison. Two fresh chains independently generate all `246` parameter
payloads, both complete pre-update forwards, all `20` target-stream recurrent
memory layers, and both complete next-segment forwards. The incumbent
post-update parameter and state containers are removed before the chained
forward. All `244` next-forward tensor groups and `896` arithmetic branches are
exact in both repetitions, with byte-deterministic outputs and no forbidden
dynamic dependency. The guarded run stayed below the frozen decimal-memory and
scratch limits. See the
[`decision`](../../../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/decision.json),
[`chain receipt`](../../../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/chain-receipt.json),
[`guard`](../../../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T024338Z_3839f396a6.json).

This is one causal open production segment transition, not recursive training.
Its dense gradients remain captured teacher outputs. It has zero objective
credit and proves no open backward pass, archive gain, transfer, package
economics, or full-corpus result. The next honest teacher-removal boundary is
an open backward pass that reproduces the same named dense gradients and then
feeds this unchanged update-to-forward chain. The best source-bound forecast
and target debt are unchanged.

## 2026-08-15 - Complete open production optimizer replay is exact

The segment-transition program now has a complete, retained production update
oracle. The Q0 through Q2 fixture attempts were terminal implementation
evidence: stale external digests, callback identity, and incomplete gradient
naming prevented a scientific conclusion. Candidate
`nncp_libnc_profile_update_fixture_64_q3_v1` corrected the shared callback
boundary by using the callback's opaque `NCParam` pointer as the parameter-name
key. Two fresh teacher executions then emitted byte-identical complete
fixtures. The retained local fixture contains all `246` dense gradients,
initial and final parameter/optimizer containers, initial and final recurrent
state, and the train-step `4` to `5` boundary. See its
[`decision`](../../../results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json).

The first two official open-replay jobs stopped before arithmetic. Their
separate reflections preserve two general orchestration defects: a consumer
decoded the structured reflection decision as a scalar, then rejected the
empty scratch root that `enqueue-tool` had correctly pre-created. Measured
source and experiment bindings were not edited in place. Each repair received
a new candidate and prospective experiment, leaving both failed jobs
auditable.

Candidate `nncp_open_profile_adam_replay_64_q0_retry_v2` passed the resulting
gate. Its standalone Gamma-authored C++ implementation parses the retained
containers and reproduces the complete production update without calling
LibNC. It implements the exact 64-value reduction, per-tensor norm clipping,
step-five Adam correction, deterministic fast reciprocal square root, fused
update order, BF16 round-to-nearest-even, and biased low-word serialization.
Across `313,000,456` parameter words, `245` BF16 tensors, one F32 tensor, and
all variance tensors, both fresh reports are byte-identical and every mismatch
counter is zero. The dependency-closed source package is retained with the
[`decision`](../../../results/nncp_open_profile_adam_replay_64_q0_retry_v2/decision.json),
[`guard`](../../../results/nncp_open_profile_adam_replay_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T003855Z_aab09244b0.json).

This closes the optimizer and serialization oracle, not recursive training.
The dense gradients are still captured teacher outputs, the result has zero
objective credit, and no open backward pass, second-segment forward, archive
gain, transfer result, or full-corpus package exists. The next admissible gate
is a separately frozen post-update forward fixture and open
update-to-next-forward replay. Only after that passes may work claim one
causally continuous segment transition; open gradient generation remains the
larger teacher-removal blocker.

## 2026-08-15 - Open production arithmetic identity is exact

The retained Q18 GGML forward already matched every exported output tensor,
but its scalar left-fold tree reduction differed from LibNC by one integer
frequency count on a small subset of visited branches. Candidate
`nncp_ggml_profile_arithmetic_64_q0_v1` terminated both paths through the same
fixed Gamma range coder and independent decoder. Both payloads reconstructed
the exact frozen transformed symbols and had equal length, but their bytes
differed. The terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T225004Z_10e9a0f5af.json)
therefore retires one-count branch tolerance as sufficient codec-boundary
evidence. It does not reject the open GGML forward or the Gamma coder.

Candidate `nncp_ggml_profile_arithmetic_64_q1_v1` changed only that final
reduction. Its counted source reconstructs LibNC's 64-value AVX reduction,
masked-tail semantics, and binary partial accumulation; model parameters,
forward tensors, softmax, quantizer, coder, fixture, and population remained
frozen. The prospective
[`experiment`](../../../operations/adaptive/experiments/nncp_ggml_profile_arithmetic_64_q1_v1.json)
required zero frequency drift rather than preserving Q18's tolerance.

The guarded run passed. Every visited integer branch frequency is exact, both
open tree paths repeat byte-for-byte, oracle/open/repeated-open payloads are
identical, and all three payloads independently decode the exact symbols. See
the [`decision`](../../../results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T230010Z_836682be9c.json).
This is a real open-runtime correctness gain with zero objective credit: it
proves one production-profile segment, not online parameter updates,
multi-segment continuity, package economics, transfer, or archive improvement.

The next admissible integration had to preserve this exact arithmetic boundary
while exposing the segment transition explicitly. Candidate
`nncp_ggml_profile_memory_transition_64_q0_v1` compiled LibNC's visible
`mem_update` rule into a counted shift-and-append transform. For every layer it
independently combined the retained initial teacher memory with either the
ordered teacher layer inputs or one of two open executions. All layer states
match byte-for-byte and all three aggregate state digests are identical. See
the [`decision`](../../../results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json),
[`state receipt`](../../../results/nncp_ggml_profile_memory_transition_64_q0_v1/state-digests.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json).

This removes memory movement as the blocker, but it does not authorize a
fixed-parameter second segment. The incumbent also computes full deep
gradients, clipping, optimizer moments, and updated parameters after each
production segment. The next honest boundary is therefore a prospectively
frozen full-update receipt, followed only after a pass by a later-segment
oracle. Generic prefix compressor jobs for these infrastructure descriptors
remain held because they would compare different work.

## 2026-08-15 - Direct-F32 named-gradient oracle retires the localization lineage

The q0 named-gradient implementation reached the first production F backward
pass and reproducibly aborted at `libnc.c:7564`: `nc_free_tensor` observed an
already-consumed tensor reference. The defect is localized: LibNC's
`nc_tensor_isfinite` consumes its input, while q0 passed the callback-owned
gradient without first duplicating the reference. The
[`reproduction guard`](../../../results/delta_midas_named_midpoint_gradient_65536_q0_v1/abort-reproduction.guard.json)
records the same `SIGABRT` under the declared memory and scratch bounds.

Candidate `delta_midas_named_midpoint_gradient_65536_q1_v1` is an immutable
implementation retry. Its
[`experiment contract`](../../../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q1_v1.json)
changes only reference ownership by calling `nc_tensor_isfinite` on a duplicate
and makes subprocess failure streams durable. Population, F-arm behavior,
grouping, thresholds, repeats, promotion, kill conditions, and zero-credit
boundary are unchanged. Q0 remains terminal implementation evidence; q1 must
still prove both exact archives and complete deterministic rows before any
gradient localization conclusion is allowed.

Q1 then preserved the native stream and exposed the next exact defect:
`nc_get_scalar_f32` rejected the non-F32 squared-energy reduction. Its
[`reflection`](../../../operations/adaptive/reflections/20260815T172412Z_47ccd874f6.json)
again leaves the scientific hypothesis untested. Candidate
`delta_midas_named_midpoint_gradient_65536_q2_v1` is frozen from q1 with the
new implementation-retry composer: every scientific field and predicate is
inherited, while the runner, materializer, parent revision, negative control,
failure evidence, outputs, and declared implementation delta are rebound. Q2
converts only the completed BF16 squared-energy reduction to `NC_TYPE_F32`
before the scalar read. That restores the scalar-reader type contract but does
not make the accumulated energy authoritative: a direct F32 reducer must
re-evaluate the unchanged localization predicates before any group ablation can
be authorized. Agreement with q2 is a sensitivity diagnostic, not a promotion
condition, because q2's low-precision ranking is not scientific ground truth.

Q2 subsequently completed both encodes with byte-identical retained F archives
and identical complete named-gradient rows. Its schema and semantic receipt
validation pass, including the 64-state block coordinates, parameter coverage,
artifact hashes, and predicate derivation. The low-precision summary selects
feed-forward overall but not in every chronological third, falls below the
frozen minimum-third share, and remains output-head dominated. Those values are
retained as sensitivity evidence only. The terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T172824Z_465e6837f4.json)
classifies the ranking as incomplete evidence, authorizes `retry`, and retires
only post-reduction F32 conversion as an authoritative localization oracle.

Candidate `delta_midas_named_midpoint_gradient_65536_q3_v1` was frozen from
that reflection. Its
[`experiment contract`](../../../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q3_v1.json)
binds the direct reducer, explicit F32 reference, complete runtime source and
JSON-contract closure, q2 decision/detail/reflection, retained F comparator,
exact midpoint patch, and strict output set before execution. Direct-reference
finiteness and relative agreement are prerequisites for both promotion and
retirement. Q2 comparisons are diagnostic only. Q3 remains closed-teacher,
zero-credit attribution; it cannot claim codec savings or objective progress.

Job `20260815T200718Z_9b504935f5` completed both encodes under the declared
process-tree memory and scratch guard. The two archives are byte-identical to
each other and to retained F, the two complete named-gradient tables repeat
exactly, and every direct-F32 energy equals its independent explicit-F32
reference. The valid result remains output-head dominated. Feed-forward is the
largest non-head group overall but the dominant non-head group changes across
chronological thirds, and the minimum-third share misses its prospectively
frozen threshold. See the [`decision`](../../../results/delta_midas_named_midpoint_gradient_65536_q3_v1/decision.json),
[`gradient detail`](../../../results/delta_midas_named_midpoint_gradient_65536_q3_v1/gradient-detail.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T200718Z_9b504935f5.json).

The exact hypothesis is refuted: squared-gradient energy does not select one
stable deep midpoint parameter group on the frozen production F population.
No group ablation is authorized, and this entire localization lineage is
retired with zero objective credit. The result does not refute a multi-group,
signed-logit, Hessian, activation-residual, or decoder-visible causal
mechanism. The next experiment must be materially different and prospectively
bound; it may not inherit teacher energy, archive savings, or score credit.

## 2026-08-15 - Named production midpoint-gradient localization is prospectively frozen

Candidate `delta_midas_named_midpoint_gradient_65536_q0_v1` is the next
bounded teacher attribution after the positive deep F-versus-O residual and
the negative compact hashed-linear probe. Its structured
[`experiment contract`](../../../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q0_v1.json)
binds the exact `65,536`-symbol production population, the legacy attribution
receipt that names retained F, closed-source inputs, immutable parent revision,
analyzer, materializer, two repeat encodes, and zero-credit boundary. That
legacy receipt carries the retained archive digest, but q0 through q2 do not
bind the archive itself as a separate prospective input; their archive-identity
measurement is therefore useful execution evidence, not a tamper-evident
comparator boundary.

The only changed mechanism is observation: during each F-arm first-half
midpoint backward pass, the instrumented teacher emits the stable `NCParam`
name, gradient shape, hash, finiteness, and squared gradient energy. The
instrumented archive must remain byte-identical to retained F, both encodes and
complete named-gradient rows must repeat exactly, and every block must expose
the same parameter set. A successor is authorized only if one non-head group
is dominant in every chronological third, its minimum share of non-head energy
is at least `0.35`, and the output-head share of total energy is at most `0.5`.

Passing selects exactly one separately preregistered group-ablation arm.
Failing the localization thresholds with all integrity predicates intact
retires gradient-energy localization. Gradient magnitude is not probability
attribution, the closed LibNC teacher remains unshippable, and this run cannot
claim archive savings, an open correction, transfer, package economics, or
objective bytes.

The first queued execution, job `20260815T170528Z_778414d866`, stopped before
the teacher began because the guard required its declared result scratch
directory to pre-exist. The terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T170528Z_778414d866.json)
classifies this as an infrastructure failure and leaves the hypothesis
untested. The general executor boundary now records candidate-owned scratch
directories in the job, constrains them below `results/<candidate_id>/`, and
materializes them before guard preflight. Retry job
`20260815T171447Z_33eeb89e5c` retains the same experiment, candidate revision,
proposal, and runner bindings while adding that explicit lifecycle input.
That retry confirmed the lifecycle fix and entered the first instrumented F
encode, then NNCP terminated with `SIGABRT` before archive completion. Peak
sampled process-tree RSS remained below the declared guard; the terminal
[`implementation reflection`](../../../operations/adaptive/reflections/20260815T171447Z_33eeb89e5c.json)
keeps the hypothesis untested. Because the analyzer discarded captured native
stderr when `check=True` raised, the next action is an exact stream-preserving
reproduction, not a localization conclusion or parameter sweep.

## 2026-08-15 - Fixed decoder-visible DELTA-MIDAS probe is terminal negative

The first prospective successor to the deep-residual receipt is terminal
`REJECT`. Candidate `delta_midas_decoder_feature_probe_65536_q0_v1` froze one
`4,096`-weight hashed-linear model, four normalized online passes, chronological
train/validation/test partitions, int16 replay, an `8,200`-byte payload ceiling,
and a one-segment shifted-label control before execution.

The experiment was causally valid but lost `887.0184641356755` ideal bits on
validation and `1,080.7027626223207` on sealed test. Every test third was
negative, only `13` of `171` test segments improved, and the aligned treatment
was `696.9629361023035` bits worse than the shifted-label control. See the
[`decision`](../../../results/delta_midas_decoder_feature_probe_65536_q0_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260815T162913Z_047c55d5ea.json).

This retires the exact feature map, optimizer, clipping, partition,
quantization, and O-offset replay contract without sweeps. It does not refute
the measured deep teacher residual. Any recurrent or low-rank successor must be
a materially new, prospectively bound mechanism; it cannot be a parameter retry
or inherit archive bytes, transfer, package economics, or score credit.

A source-bound design audit confirms that LibNC exposes stable `NCParam` names
at the midpoint backward callback (`embed`, output head, attention, feed-forward,
normalization, and per-layer parameters). The next justified teacher action is
the now-frozen F-arm midpoint-only named gradient projection above, summarized
by group and chronological third. Its only possible consequence is selection
of one later group-ablation arm; gradient magnitude is not itself probability
attribution. It remains zero-credit teacher work.

## 2026-08-15 - DELTA-MIDAS deep residual survives exact retained-trace gate

Terminal candidate
`nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1` closes the
output-head theory. On its same-run population, rebuild-only `K` is `148,141` bytes, full midpoint `F` is
`143,414`, and output-head-only `O` is `148,709`. Thus F beats K by `4,727`
bytes while O is `568` bytes worse than K. The earlier bridge reports `4,726`
because its parent archive is one byte smaller; those values come from
different exact runs and are not combined. The terminal decision remains a
four-thread closed-LibNC teacher result with zero score credit.

Proposals `nncp_gram_midas_full_hidden_65536_qm0_v1` and
`gamma_orbit192_gram_midas_65536_qm0_v1` are retired because both depended on
an output-head gain that does not exist. Their rejection receipts preserve the
closed neighborhood; the ORBIT feature idea is not inherited into a new result.

Experiment `delta_midas_deep_residual_65536_q0_v1` retrospectively froze an
exact F-versus-O retained-trace analysis before its analyzer emitted a result.
All `65,536` rows and `917,527` truth-path branches aligned. On second halves,
F beats O by `22,783.981772296793` ideal bits. All original-coordinate thirds
are positive, and `1,001` of `1,024` segments are positive. See
[`decision.json`](../../../results/delta_midas_deep_residual_65536_q0_v1/decision.json)
and the hash-linked
[`reflection`](../../../operations/adaptive/reflections/20260815T161658Z_636aa4dd6c.json).

The result localizes useful information beyond the output head and authorizes
only one prospectively frozen decoder-visible feature-capture experiment. It
does not show realizable archive savings, a compact student, transfer, package
cost, or Hutter score credit. Hidden state, teacher probabilities, and the
closed LibNC executable remain forbidden submission inputs.

The running q2 named-gradient retry has a separate numeric-validity boundary.
The production profile defaults parameters to BF16, and q1's retained native
[`nc_get1_f32` assertion](../../../results/delta_midas_named_midpoint_gradient_65536_q1_v1/F_named_gradient_1.stderr)
proves the squared-energy reduction did not produce an F32 tensor. The
[`q2 materializer`](../../../tools/materialize_nncp_named_midpoint_gradient_q2.py)
converts only after the BF16 elementwise square and reduction, so it repairs
the scalar-reader crash but does not establish precision-stable group shares.
The hash-bound LibNC binary exports `nc_reduce_sum_sqr`; its implementation
creates an F32 scalar and dispatches BF16 inputs through the direct
`vec_sum_sqr_bf16` F32 accumulation path. Therefore q2 may retain archive,
gradient-hash, coverage, and implementation-liveness evidence, but its energy
ranking cannot by itself authorize a group ablation. The smallest valid
measurement retry replaces only the energy expression with
`nc_reduce_sum_sqr(nc_dup_tensor(gradient))`, repeats both exact F encodes, and
cross-checks every value against an explicit BF16-to-F32 multiply-and-sum path.
Both paths must be finite and pass the frozen relative-error bound before the
original group and chronological-third predicates can authorize or retire an
ablation. Agreement with q2 remains diagnostic because q2's BF16 ranking is not
an oracle. Q3 also binds retained `F_clean.nncp` directly and checks its path,
byte count, and digest against the legacy attribution receipt before starting
the teacher, closing the comparator-identity gap instead of inheriting it.

## 2026-08-15 - Recursive self-improvement boundary audited

The adaptive lane now binds the objective, immutable candidate revisions,
structured experiments, terminal reflections, evidence-aware selection,
dependency packaging, and clean-room receipt composition. The executor uses
three fresh builds, two archive-identity runs, and a corpus-blind decode under
sealed one-core resource guards. It is still not authorized for unattended
mutation or prize-facing promotion because no eligible Gamma candidate has
produced a complete full-1G package receipt or second-host identity receipt.
See [`recursive_self_improvement_system_audit.md`](../../recursive_self_improvement_system_audit.md).
Missing roundtrip, determinism, process-tree resource, dependency-closure, or
peer evidence still fails closed.

## 2026-08-09 - Agent A/B strategy and ownership merge under the 105M target

Agent B has accepted Agent A's handoff and now owns both active scientific
tracks. The canonical objective is an exact, self-contained full-1G score no
larger than `105,000,000` bytes. `cmix-obias` is David Freelan's externally
authored submission candidate, derived from Ibrahim Marcouch's `cmix-lex` and
earlier cmix/PAQ work; Gamma did not invent it and cannot treat reproduction as
a Gamma prize entry. Its reported `108,492,825` score leaves `3,492,825` bytes
of counted debt to the project target. The active full-corpus jobs are
zero-credit external-baseline, provenance, determinism, and resource evidence
only. They may support an independently novel, fully attributed Gamma child,
but they cannot satisfy the objective by themselves. KAIROS was the first
same-stream Gamma correction test, but its completed paid opening replay
retired the frozen dyadic final-head realization; it is no longer a promotion
path.

The independent NNCP lane has now confirmed that the changed update cadence
persists over `1,998,848` symbols, saving `82,432` actual encode-only archive
bytes. That teacher result authorizes the predeclared production-alphabet
state-refresh/output-head/full-update attribution and, only if attribution
passes, a compact MIDAS-style descendant.

The external cmix-obias baseline and NNCP teacher lanes do not inherit or add
projected savings. Only a separately attributable Gamma mechanism may enter
the winning path, and any use of upstream code requires complete attribution
and compliance with its authorship and licensing boundary. A future
combination is authorized only after the new mechanism independently passes
its paid gate, and then only through a new exact joint coder replay with
complete package and memory accounting. The XML-safe far-history/copy family
and the measured KAIROS dyadic realization remain terminally closed.
