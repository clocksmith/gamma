# Research Register Archive 007

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-02: MÖBIUS-2 frontier-teacher WRT event alphabet is terminal negative

The frozen heavy-lock ROCm oracle completed with process status zero and a
clean development `REJECT`. It scored 159,767 exact WRT emission groups in 384
independent page-local blocks across 102 complete pages and 349,911 raw bytes.
All 14 role catalogs were learned only from development. They contained 7,174
exact programs spanning 7,173 candidate Gemma token IDs, but no role achieved
both positive calibrated gain and a strict win over the static exact-program
alphabet. Selection and sealed confirmation therefore remained unopened.

The decisive `PROSE_WORD` role had 78,009 opportunities and 23,976 catalog
events. Those events displaced 183,676.797 joint bits, while the calibrated
teacher alphabet required 373,197.753 bits. It lost 23,690.119 bytes to the
exact JANUS-plus-quotient trajectory, was 11,394.559 bytes worse than the
static exact-program alphabet, and was only 3,900.247 bytes better than the
native full-mass Gemma control. `LINK_TARGET` lost 3,343.062 bytes and
`LIST_ITEM` lost 2,938.178 bytes. `LINK_LABEL` and `TABLE_CELL` beat their
static controls by 261.304 and 9.051 bytes respectively, but still lost
690.157 and 59.816 bytes to the joint trajectory. Every other role was also
negative.

This is a scientific rejection rather than a runtime, alignment, or
probability failure. The run proved real ROCm matrix compute, exact WRT/raw
identity, exact joint-P1 truth alignment, complete contiguous event groups,
development-only catalogs, legal finite nonzero distributions, repeatable
event-local tokenization, and repeatable calibration. The repeated calibration
SHA-256 is
`2fb367176ca25b7029fa537bc9e468a28668208d682093244c01f9afd0f845ca`;
the complete development event-score stream SHA-256 is
`a65251bd989a79b22d7be483f3b36fae27db3473e3e470b7690d218e0650527c`.

Retire this exact Gemma-4 12B checkpoint, event-local tokenizer, single-token
program catalog, role partition, escape calibration, page-local 512-token
reset, and static/full-mass controls without model, role, catalog, tokenizer,
context, or smoothing rescue sweeps. Together with the full-vocabulary teacher
rejection, this closes both direct local-Gemma descriptions tried against the
joint residual trajectory. Forecast 109,389,323, debt 1,389,323, score credit
zero, and unknown verified full-1G status remain unchanged.

Decision:
`results/mobius2_frontier_teacher_wrt_event_alphabet_qh0_v1/decision.json`.

## 2026-08-02: NNCP v3.3 activation-backward parity gate frozen

Proposal and candidate: `nncp_v33_libnc_activation_backward_parity_v1`.

The published NNCP v3.3 total remains the only locally documented external
result below 108,000,000 bytes. The existing ROCm port matched the frozen
miniature forward distribution, but its first online update diverged and the
prior gradient interposition found 6.6 to 14.6 percent relative disagreement
through internal backward paths. That result retired an undifferentiated
PyTorch-autograd reproduction, not every individual LibNC derivative.

The official Transformer graph implements GEGLU as `nc_gelu(left) * right`.
A close forward approximation with a different activation derivative can
therefore preserve inference parity while contaminating feed-forward,
residual, attention, and embedding gradients. This gate calls LibNC's public
`nc_gelu` and automatic differentiation APIs directly on a frozen F32 grid,
requires byte-identical repeated output, and compares both values and
derivatives with PyTorch's exact-erf and tanh-approximate GELU contracts.

A unique match within `2e-6` maximum absolute gradient error authorizes one
corrected bound miniature full-gradient and first-update replay. Anything else
retires GELU backward as the cause. The gate has zero score credit and cannot
authorize a mature trace by itself.

Plan: `docs/nncp_v33_libnc_activation_backward_parity_plan.md`.

## 2026-08-02: NNCP v3.3 tanh-GELU online-update parity gate frozen

Proposal and candidate:
`nncp_v33_libnc_tanh_gelu_online_update_parity_v1`.

The direct primitive gate found that LibNC `nc_gelu` is not PyTorch's default
exact-erf GELU. An unfused F32 tanh formula with the observed positive-tail
saturation matches all 41 LibNC values within `1.1921e-7` and all automatic
derivatives within `4.7684e-7`; exact-erf GELU misses the derivative by
`8.6735e-4`. Repeated LibNC output is byte-identical with SHA-256
`30c7050c349156e7b5973986f627414229ff40b3b339c243b87d34778e576f6f`.

This child gate changes only that activation in the exact bound miniature that
previously failed after one update. It retains the serialized initial and
final LibNC tensors, teacher trace, four-symbol population, learning rate,
per-parameter gradient clipping, and `2e-5` threshold. It repeats the corrected
replay from the serialized initial tensors and binds the complete final tensor
set by hash. A pass authorizes only the next parity localization or frozen
full-profile gate; score credit remains zero.

Plans:
`docs/nncp_v33_libnc_activation_backward_parity_plan.md` and
`docs/nncp_v33_libnc_tanh_gelu_online_update_parity_plan.md`.

## 2026-08-02: NNCP v3.3 GELU repair is real but insufficient

The primitive gate passed. Repeated direct LibNC execution was byte-identical,
and the fitted unfused F32 tanh-GELU contract matched 41 forward values within
`1.1920929e-7` and automatic derivatives within `4.7683716e-7`. PyTorch's
default exact-erf GELU missed the derivative by `8.6735189e-4`. Exact-erf GELU
is therefore a proved implementation bug in the prior NNCP replica.

The one-change full-update child nevertheless produced a clean `REJECT`.
Correcting GELU improved the frozen teacher distribution error from about
`4.2e-7` to `4.6566e-9`. The `embed_out`, `out_bias`, `ff_bias2`, and several
normalization update errors fell to approximately `2.4e-7` through `2.8e-7`.
Internal attention, feed-forward, embedding, and other normalization tensors
still reached `0.000319999643`, the two-sided first-step Adam sign ceiling and
sixteen times the frozen `2e-5` gate. Two independent corrected replays
produced the identical final-tensor SHA-256
`7cccce8ff1c1197fed779a603dcd682281aeef277905a4f6925d4683237fb0ad`.

Retire tanh GELU as a sufficient LibNC online-update parity repair. Do not
launch a mature trace while claiming LibNC update equivalence. The measured
activation contract remains the correct component for any self-consistent
source-level v3.3 realization, which must prove its own encoder/decoder state
identity and compression headroom rather than inherit the published score.
Forecast and score credit remain unchanged.

Decisions:
`results/nncp_v33_libnc_activation_backward_parity_v1/decision.json` and
`results/nncp_v33_libnc_tanh_gelu_online_update_parity_v1/decision.json`.

## 2026-08-02: NNCP v3.3 faithful ROCm constructive Q0 frozen

Proposal and candidate: `nncp_v33_rocm_constructive_one_update_q0_v1`.

Exact LibNC online-update parity remains false, so the next lane cannot inherit
the published archive. It instead builds a self-consistent codec and requires
its own evidence. This is materially different from the retired one-stream
ALiBi ROCm teacher: it restores the official learned relative tables and
shared bias, RMSNorm gain and bias with epsilon `1e-5`, F32 input embedding and
BF16 remaining parameters, measured tanh GEGLU, 32 contiguous streams,
64-symbol updates, and per-parameter rather than global gradient clipping.

Q0 covers exactly one 2,048-symbol update block. Two seeded encoders must emit
identical archives and final model states. A separately seeded decoder derives
every arithmetic frequency from decoded prefixes, reconstructs all symbols,
applies the same update, and must end with the same complete model-state hash.
The official preprocessor inverse and decimal 10 GB allocation ceiling remain
mandatory. A pass authorizes one 65,536-symbol headroom gate but grants no score
credit or LibNC/published-score claim.

Plan: `docs/nncp_v33_rocm_constructive_one_update_q0_plan.md`.

## 2026-08-02: NNCP v3.3 batched constructive Q0 is causally malformed

The heavy-lock Q0 reached the receipt-bound ROCm interpreter, PyTorch
`2.12.1+rocm7.2`, HIP `7.2.53211`, and the Radeon 8060S under the required GFX
override. The matrix-compute SHA-256 was
`9ab0c29d311879d656d7fb6bd5ab0097c830911629ed27cccfef5265ea0ec5b1`.
It stopped before arithmetic encoding because changing segment input position
9 changed earlier logits by `0.009521484375`.

Follow-up localization proved this is not repeat-run GPU noise. Identical
inputs emitted bit-identical logits. For the future perturbation, masked
attention scores and probabilities at earlier positions were still identical,
but the BF16 attended-value reduction differed by
`7.62939453125e-06`; the discrepancy first became externally visible at block
10 and amplified in later layers. This reproduces the prior full-segment ROCm
teacher failure. Record the parent as an infrastructure/cause-of-invalidity
result with no compression verdict, score credit, or headroom authorization.

The one-change child
`nncp_v33_rocm_constructive_causal_replay_q0_v1` retains the full profile and
segment-final update but computes each state from a decoder-known prefix plus
frozen zero future fillers. Encoder and decoder therefore invoke the identical
state-major schedule without materializing future truth. Its frozen gate still
requires two identical encodes, an independent model-driven decode, complete
branch-frequency and final-state identity, official inverse, and decimal 10 GB
compliance. A pass authorizes only 65,536-symbol headroom evidence.

Plan: `docs/nncp_v33_rocm_constructive_causal_replay_q0_plan.md`.

## 2026-08-02: NNCP v3.3 constructive causal-replay Q0 passes

The one-change state-major Q0 completed in `71.505` measured seconds and
authorized the frozen 65,536-symbol gross-headroom gate. Its causal audit was
exact. Two independently seeded encoders emitted the identical 3,613-byte
archive and final model hash. An independently seeded model decoder reproduced
all 28,673 branch frequencies, all 2,048 preprocessed symbols, the complete
post-update state, the loss, and the official 9,868-byte raw prefix.

The complete state SHA-256 was
`2ae4efe57f08736c3e7d3f67104b74a496f4c54af6ee24b142904ab0be5014f5`;
the archive SHA-256 was
`823ca1f776e8db93911b0670a1043a5190621d2cfd60d40c3e29ce1b830683e4`.
Peak allocated memory was 7,229,241,344 bytes, below decimal 10 GB. This is a
constructive mechanics pass with zero score credit, not evidence that the
self-consistent model compresses competitively.

The authorized child
`nncp_v33_rocm_constructive_65536_headroom_q1_v1` runs 32 consecutive online
updates over one 65,536-symbol, 32-stream block. It requires two exact encodes,
an independent model-driven decode, complete model/Adam/memory identity, the
official inverse, and an exact terminated comparison with the same-raw-boundary
JANUS-plus-quotient prefix. Promotion requires at least 3,000 gross B/M.

Plans and decision:
`docs/nncp_v33_rocm_constructive_65536_headroom_q1_plan.md` and
`results/nncp_v33_rocm_constructive_causal_replay_q0_v1/decision.json`.

## 2026-08-02: NNCP v3.3 constructive 65,536-symbol Q1 is terminal negative

The frozen Q1 completed in `1,744.706` measured seconds with process status
zero and a valid `REJECT`. It covered 65,536 official preprocessed symbols,
322,978 raw bytes, 32 contiguous streams, and 32 online update segments. The
two encoders and independent model-driven decoder reproduced all 917,527
branch frequencies, the arithmetic archive, every decoded symbol, all segment
losses, and the complete model, Adam, and persistent-memory state. The complete
state SHA-256 was
`9da56660c487182375ff9359d26a5dbab93cbfc82a40da50c13da339d827e5b4`.

The official NNCP inverse was exact. The mapped endpoint was also an exact WRT
emission-group boundary, and the independently terminated
JANUS-plus-quotient prefix decoded exactly. Peak allocated ROCm memory was
9,052,226,560 bytes, below decimal 10 GB.

Compression economics failed decisively. The constructive NNCP payload was
96,142 bytes; the same-boundary joint prefix was 57,555 bytes. Q1 therefore
lost 38,587 bytes, or `-119,472.534 B/M`, versus the required `+3,000 B/M`.
Retire this self-consistent PyTorch/ROCm faithful-profile realization without
architecture, precision, stream-count, optimizer, block-layout, or
future-filler sweeps. It earns no score or forecast credit.

This result does not retire the separately published NNCP v3.3 result. It
confirms that approximate topology plus a different online numerical machine
cannot inherit that score. Any successor using the published lead must recover
or reproduce LibNC's actual update semantics component by component before a
mature archive is claimed.

Decision:
`results/nncp_v33_rocm_constructive_65536_headroom_q1_v1/decision.json`.

## 2026-08-02: NNCP v3.3 LibNC RMSNorm backward parity frozen

Candidate and proposal: `nncp_v33_libnc_rmsnorm_backward_parity_v1`.

The GELU correction was real but left internal first-update tensors at the
two-sided Adam sign ceiling. The next component gate calls LibNC
`nc_rms_norm` directly on a frozen F32 matrix with a nonuniform upstream
gradient, captures every output and input-gradient element, and requires
byte-identical repeated execution. A tiny-valued column identifies epsilon
placement.

The current mean-square/inside-sqrt contract, an outside-sqrt epsilon
alternative, and a sum-normalized alternative are frozen before execution.
A unique alternative match within `2e-6` authorizes one corrected bound
miniature update. A unique match to the already implemented contract retires
RMSNorm as the remaining cause. This is zero-credit implementation forensics,
not a model or archive result.

Plan: `docs/nncp_v33_libnc_rmsnorm_backward_parity_plan.md`.

## 2026-08-02: LibNC RMSNorm backward operation-order child frozen

The direct 40-element LibNC probe repeated byte-identically. The existing
RMSNorm formula matched every forward value exactly but missed input gradients
by up to `6.103515625e-05`; the outside-sqrt and sum-normalized alternatives
were decisively wrong. The parent result is therefore an unresolved numerical
contract, not an RMSNorm rejection.

Read-only closed-form localization found that LibNC's gradient is reproduced
by `inverse * (g - y * mean(g*y))` to `5.960464477539063e-08`, while the usual
PyTorch autograd order retains the `6.103515625e-05` miss. The child freezes a
`1e-7` unique-match gate across current, output-based, and divided backward
orders. A pass authorizes exactly one tanh-GELU plus LibNC-order RMSNorm bound
miniature update.

Plan: `docs/nncp_v33_libnc_rmsnorm_backward_order_parity_plan.md`.

## 2026-08-02: combined GELU and RMSNorm bound update frozen

The RMSNorm operation-order child passed uniquely. Its output-based backward
matched all direct LibNC gradients within `5.960464477539063e-08`; the divided
closed form missed by `2.3096799850463867e-07`, and ordinary PyTorch autograd
missed by `6.103515625e-05`. Repeated direct LibNC stdout remained
byte-identical with SHA-256
`690f221bbc0f6bad0135d98563f61d0392b24b02f73dccfa7cb02d4a33de06e2`.

The authorized child changes exactly two primitives in the bound miniature:
the already proved tanh GELU and the newly proved RMSNorm backward order. It
retains all serialized teacher artifacts, optimizer semantics, clipping,
population, and the `2e-5` final-tensor threshold. A miss retires the combined
repair as sufficient; a pass authorizes only further exact parity work.

Plan: `docs/nncp_v33_libnc_tanh_gelu_rmsnorm_update_parity_plan.md`.

## 2026-08-02: combined GELU and RMSNorm repair is insufficient

The exact bound-miniature replay completed deterministically but rejected the
combined repair. Corrected probabilities matched the bound LibNC trace within
`4.6566128730773926e-09`, and repeated final tensors were byte-identical, but
the maximum final-parameter error remained
`0.00031999964267015457`, essentially the two-sided one-step Adam ceiling
`2 * 0.00016`. The measured RMSNorm and GELU corrections are real, but they do
not make the full update contract faithful.

An initial positional interpretation of the unnamed LibNC interposition files
appeared to place the first material divergence immediately behind the output
layer. That interpretation assigned a `6.51%` relative-L2 difference to
`ff_bias2_0` and a `12.87%` difference with 50 sign reversals to `ff2_0`.
The later direct tail-composition gate made the `ff_bias2_0` assignment
temporarily non-authoritative: the exact LibNC and PyTorch isolated-tail
gradients agree with one another but both miss that unnamed file by the same
almost constant offset. The subsequent source-named capture restored the
assignment byte-for-byte and showed that the extra term belongs to the full
optimized graph, not the standalone tail. The final-parameter comparison
remains valid.

Decision:
`results/nncp_v33_libnc_tanh_gelu_rmsnorm_update_parity_v1/decision.json`.

## 2026-08-02: LibNC output matmul backward parity frozen

Candidate and proposal:
`nncp_v33_libnc_output_matmul_backward_parity_v1`.

The direct gate uses the exact `256 x 32` by `32 x 4` output-projection shape
from the bound miniature and a deterministic zero-sum upstream fixture. It
captures the complete LibNC forward result and both input gradients twice.
The frozen comparisons are native PyTorch F32 matmul, ascending scalar F32
accumulation, and descending scalar F32 accumulation. A unique non-PyTorch
match within `2e-6` authorizes one corrected bound replay; any other result
retires this reduction as the cause. No numerical result or score credit is
claimed before execution.

Plan: `docs/nncp_v33_libnc_output_matmul_backward_parity_plan.md`.

## 2026-08-02: LibNC output matmul reduction is retired

The direct `256 x 32` by `32 x 4` LibNC probe repeated byte-identically with
aggregate SHA-256
`9bf364dce5a53863a303314251f9ac86aefa87f66570bc1bb7cb4245749d85be`.
PyTorch's left-input gradient matched exactly, and its right-input gradient
missed by only `2.0489096641540527e-08`. All three preregistered contracts were
inside the `2e-6` gate, so no special matrix reduction was identified. This is
a clean rejection of output-projection `nc_matmul` reduction as the source of
the bound update divergence.

Because the parameter-side output gradients are already exact while tiny
per-logit differences can be amplified by cancellation in the transpose
projection, the next isolated boundary is LibNC's unfused
`softmax -> indexed_log -> sum` backward graph versus fused PyTorch
cross-entropy.

Decision:
`results/nncp_v33_libnc_output_matmul_backward_parity_v1/decision.json`.

## 2026-08-02: LibNC softmax-indexed-log backward parity frozen

Candidate and proposal:
`nncp_v33_libnc_softmax_indexed_log_backward_parity_v1`.

LibNC trains the transformer through an explicit probability graph:
`nc_soft_max`, `nc_indexed_log`, reduction, and negative mean scaling. The
current PyTorch replay instead uses fused cross-entropy. The direct gate
serializes all probabilities and logit gradients for the exact 256-class,
four-column bound shape and targets. It compares fused cross-entropy, an
explicit PyTorch probability graph, and the closed-form gradient under one
`2e-6` threshold. A unique non-fused match authorizes only one corrected bound
replay; all other valid outcomes retire this boundary.

Plan:
`docs/nncp_v33_libnc_softmax_indexed_log_backward_parity_plan.md`.

## 2026-08-02: LibNC softmax-indexed-log backward is retired

The 256-class, four-column direct LibNC probe repeated byte-identically with
aggregate SHA-256
`50008628d246555f96d99e45ef2df11da326ac4889fd6891495c6584264fb71e`.
Fused PyTorch cross-entropy matched the complete logit gradient within
`9.313225746154785e-10`; the explicit probability graph and closed form also
passed the frozen `2e-6` gate. There is no paying special loss-backward
contract to apply, so this cause is retired.

The remaining untested difference is graph construction. LibNC makes each
decoder prediction causally, retains the per-state key/value nodes, and only
then factorizes those nodes into the segment gradient graph. The current
PyTorch parity replay builds a single vectorized causal segment graph. The
next one-change gate therefore reconstructs the state-major saved-node graph
while retaining the already measured primitive corrections and every bound
teacher artifact.

Decision:
`results/nncp_v33_libnc_softmax_indexed_log_backward_parity_v1/decision.json`.

## 2026-08-02: LibNC decoder-graph update parity frozen

Candidate and proposal: `nncp_v33_libnc_decoder_graph_update_parity_v1`.

This child changes only graph construction. Instead of one vectorized causal
segment, it creates four chronological decoder-state graphs. Each state makes
only its completed normalized input, key, and value nodes available to later
states; all four logits join at the one frozen segment loss. The bound weights,
symbols, probability trace, final tensors, measured GELU and RMSNorm contracts,
loss, clipping, Adam settings, memory, masks, and `2e-5` tolerance remain
unchanged. A complete final-tensor pass authorizes faithful constructive work;
a miss retires this saved-node schedule as sufficient.

Plan: `docs/nncp_v33_libnc_decoder_graph_update_parity_plan.md`.

## 2026-08-02: LibNC decoder-graph schedule is insufficient

The state-major saved-node replay completed deterministically and reproduced
the four LibNC probability distributions within
`3.725290298461914e-09`, but it retained the same maximum final-parameter
error `0.00031999964267015457`. Its parameter-error pattern is effectively
identical to the vectorized parent: output, final-normalization, and
feed-forward output-bias tensors remain close while scattered internal
coordinates take opposite first-Adam-step signs.

This clean rejection closes the decoder-state versus vectorized-segment graph
schedule as a sufficient explanation. Combined with the direct primitive
receipts, it leaves the bound LibNC internal activation trajectory itself—not
another unmeasured optimizer, width, or schedule variant—as the missing
artifact. Any continuation must capture and compare receipt-bound internal
forward tensors before changing another backward implementation.

Decision:
`results/nncp_v33_libnc_decoder_graph_update_parity_v1/decision.json`.

## 2026-08-02: LibNC internal forward trajectory frozen

Candidate and proposal: `nncp_v33_libnc_internal_forward_trajectory_v1`.

The exact bound command was reconstructed before the gate: it emits the
receipt-bound 100-byte archive SHA-256
`8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da`
and teacher trace SHA-256
`cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4`.
The diagnostic recompiles that source with existing `DUMP_HASH` calls enabled
and replaces only the dump function with a complete F32 serializer. Two runs
must preserve both bound artifacts and repeat every tensor byte-identically.

Seven labeled tensors per decoder state are compared with the matched
state-major PyTorch trajectory. The first source-ordered error above `2e-6`
is the only forward correction this gate may authorize. If all 28 tensors
match, further forward changes are forbidden without new evidence.

Plan: `docs/nncp_v33_libnc_internal_forward_trajectory_plan.md`.

## 2026-08-02: LibNC internal forward trajectory is exact

The source-bound `DUMP_HASH` build reproduced the receipt-bound archive and
teacher trace byte-for-byte on both runs. All 28 labeled internal tensor files
also repeated byte-identically with aggregate SHA-256
`fc8270e93d83baf84e9c8f2fb5ca0a63ec273a8b2c4e5f2d5ea915f48d626d8b`.

No forward divergence exceeded `2e-6`. The largest internal error was
`2.384185791015625e-07` at `ff1_out`; raw attention and feed-forward residuals
were within `8.940696716308594e-08`, and output probabilities were within
`3.725290298461914e-09`. Norm ratios stayed within approximately
`1.1e-7` of one. This eliminates hidden forward scale, direction, decoder
schedule, and probability mismatch as explanations for the first-update sign
failures.

Do not alter another forward primitive. A valid continuation must either
capture direct internal backward tensors/compositions or use native LibNC as
the teacher. The result carries zero score and forecast credit.

Decision:
`results/nncp_v33_libnc_internal_forward_trajectory_v1/decision.json`.

## 2026-08-02: LibNC tail-backward composition frozen

Candidate and proposal: `nncp_v33_libnc_tail_backward_composition_v1`.

The source-bound forward gate closes further activation changes but leaves a
sign-discontinuous first Adam update. This child supplies the four exact
captured `ff_out_bl` states to a direct LibNC graph containing final RMSNorm,
gain and bias, output projection and bias, F32 conversion, softmax, four-state
concat optimization, indexed log, and negative mean. One shared zero-valued
parameter exposes the complete downstream gradient that must reach
`ff_bias2_0`.

Two source captures must retain the exact bound archive and teacher trace and
repeat all tensors. Two direct tail probes must repeat byte-identically and
match the teacher probabilities. The decisive comparison is the direct shared
gradient against bound `unknown_0006.bin`, with the matched PyTorch tail as a
control. A LibNC match within `2e-6` with identical signs, combined with a
PyTorch miss, authorizes only composed-tail operation-order localization. A
valid miss rejects the mapping or isolated graph and does not reopen a forward
primitive. No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_tail_backward_composition_plan.md`.

## 2026-08-02: LibNC tail does not reproduce the positional gradient

Both instrumented source runs reproduced the exact archive, teacher trace, and
all 28 forward tensors. The direct LibNC tail repeated byte-identically with
aggregate SHA-256
`82b6443ad8f698005f2a3b5f9c4163849a7518d3bdb1581c9e59e6a19cdaf628`
and reproduced all 1,024 teacher probabilities exactly.

The direct LibNC and matched PyTorch shared tail gradients agree within
`7.450580596923828e-08`, but both differ from positional file
`unknown_0006.bin` by approximately `0.0060333` in every one of 32
coordinates. Their relative difference from that file is `6.5088%`, with no
sign mismatches. Therefore the tail is not a distinct backward contract and
the premise `unknown_0006.bin -> ff_bias2_0` is not source-bound evidence.

This is a clean rejection of the composed-tail hypothesis and a correction to
the earlier positional mapping, not a forward or arithmetic identity failure.
The only justified continuation is an archive-identical build that names each
gradient from the live `NCParamList` at the actual backward callback. No score
or forecast credit changes.

Decision:
`results/nncp_v33_libnc_tail_backward_composition_v1/decision.json`.

## 2026-08-02: source-authoritative named gradients frozen

Candidate and proposal: `nncp_v33_libnc_named_gradient_trajectory_v1`.

The positional gradient interpretation is quarantined, so this child patches a
temporary copy of the receipt-bound source only at two observation points. It
exposes the live transformer `NCParamList` immediately before `nc_backward`,
then maps each callback's opaque `NCParam *` directly to the list and serializes
the tensor under the corresponding `NCParam.name` before the unchanged update
call. Disassembly of the exact library binds this pointer contract:
`nc_new_param_str` passes its newly allocated `NCParam *` to `nc_set_param`.

Two executions must reproduce the bound archive and teacher trace, repeat all
named gradient bytes, cover the 18 initial-manifest parameters exactly once,
and bind every named file byte-for-byte to its old positional counterpart. A
fresh deterministic state-major PyTorch replay supplies matched gradients.
Only the first source-named tensor above `2e-6` or with a sign mismatch may
authorize a direct subgraph child. If all named gradients match, the next
boundary is Adam. No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_named_gradient_trajectory_plan.md`.

## 2026-08-02: named gradients restore the mapping and localize `ff2_0`

The first infrastructure attempt correctly failed because it treated the
callback opaque value as an optimizer-variable pointer. Disassembly of the
exact `libnc.so` showed the real contract: `nc_new_param_str` passes its newly
allocated `NCParam *` directly to `nc_set_param`. The corrected retry uses that
pointer and is source-bound.

Both corrected runs reproduced the exact archive and teacher trace. All 18
named gradients repeated byte-identically with aggregate SHA-256
`db3a585b942ddcbb560a47ad9587d7457ddd718215799fb70ae8ff982dfed0ba`.
Every callback name is unique, covers the complete initial manifest, has the
manifest dimensions, and is byte-identical to the corresponding old
`unknown_N` file. The positional mapping is therefore restored as:

```text
0 embed_out   1 ff2_0       2 ff1_0       3 ln_g_1
4 ln_b_1      5 ff_bias1_0  6 ff_bias2_0  7 w_o_0
8 w_r_0       9 b_r_0      10 w_kv_0     11 w_q_0
12 ln_g_0    13 ln_b_0     14 embed       15 ln_g_2
16 ln_b_2    17 out_bias
```

The matched PyTorch probabilities remain within
`3.725290298461914e-09` of the teacher and its complete gradient map repeats.
`embed_out` is exact to `8.940696716308594e-08`. The first actual divergence is
`ff2_0`: maximum error `0.008702129125595093`, relative L2 error `12.8747%`,
and 50 sign mismatches. `ff_bias2_0` retains the `6.5088%` relative-L2 offset
without sign mismatches.

Combined with the rejected isolated-tail gate, this localizes the missing
contract to the graph that joins the feed-forward output block into the
four-state optimized loss, rather than final RMSNorm, output projection, or
loss alone. The authorized child must start from exact captured `ff2_in` and
residual states, include shared `ff2_0` and `ff_bias2_0`, and reproduce both
named gradients before changing the full replay. No score or forecast credit
changes.

Decision:
`results/nncp_v33_libnc_named_gradient_trajectory_v1/decision.json`.

## 2026-08-02: LibNC FF2-to-loss composition frozen

Candidate and proposal:
`nncp_v33_libnc_ff2_to_loss_backward_composition_v1`.

The named trajectory localizes the first actual gradient divergence to
`ff2_0`, while the isolated exact decoder tail fails to reproduce the bound
`ff_bias2_0` gradient. This child adds exactly the missing shared feed-forward
output projection. It consumes source-captured `ff2_in` and `attn_out` states,
applies shared `ff2_0` and `ff_bias2_0`, joins the residual, and then evaluates
the already isolated final tail and four-state concat optimization.

Two archive-identical source captures and two byte-identical direct block runs
are required. Direct probabilities must match the teacher. Both direct named
gradients must match the source-bound tensors within `2e-6` with identical
signs while a matched PyTorch block misses before any replay child is
authorized. A direct miss retires this boundary as sufficient and moves the
next direct graph earlier. No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_ff2_to_loss_backward_composition_plan.md`.

## 2026-08-02: LibNC FF2-to-loss composition is insufficient

Both source captures retained the exact archive, teacher trace, and all 28
forward tensors. The direct block repeated byte-identically with aggregate
SHA-256
`6fa3a5f06d31a999aef780560d24263f60c016e33b12da9a4e75f9f77e281082`
and reproduced all teacher probabilities exactly.

Direct LibNC and matched PyTorch agree within
`4.470348358154297e-08` on `ff2_0` and
`7.450580596923828e-08` on `ff_bias2_0`. Nevertheless, both retain the same
bound misses: `ff2_0` has `12.8747%` relative-L2 error and 50 sign mismatches;
`ff_bias2_0` has the nearly constant `0.0060333` offset and `6.5088%`
relative-L2 error. The FF2 projection, residual join, final normalization,
output projection, softmax, and loss therefore do not explain the native full
graph gradient.

The direct probe supplies only the output root to `nc_concat_optimization`.
The source supplies three root families together after rewiring causal key and
value nodes: key, value, and output. That joint root scope is now the only
concrete graph-contract difference downstream of otherwise exact captured
values. Any continuation must test the source's concat-root set directly;
moving another ordinary primitive is forbidden. No score or forecast credit
changes.

Decision:
`results/nncp_v33_libnc_ff2_to_loss_backward_composition_v1/decision.json`.

## 2026-08-02: LibNC concat root-scope gradient gate frozen

Candidate and proposal: `nncp_v33_libnc_concat_root_scope_gradient_v1`.

The source's joint `nc_concat_optimization` call is the last concrete graph
difference downstream of exact forward values. This child builds four
temporary source variants that supply output only, key plus output, value plus
output, or the original key plus value plus output roots. All causal node
rewiring and every arithmetic operation remain unchanged.

Each variant must preserve the bound archive and teacher trace, name all 18
gradients, and repeat byte-identically. The full variant must reproduce every
prior named gradient byte. A pass requires output-only to match PyTorch on
`ff2_0` and `ff_bias2_0`, while adding one frozen key/value root set transitions
both tensors to the full bound gradients. A miss retires concat root scope as
the isolated cause. No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_concat_root_scope_gradient_plan.md`.

## 2026-08-02: concat root-set membership does not explain FF2

All eight executions preserved the bound archive and trace, named all
gradients, and repeated. The full-root gradient directory reproduced the prior
named receipt exactly with SHA-256
`db3a585b942ddcbb560a47ad9587d7457ddd718215799fb70ae8ff982dfed0ba`.

`output_only`, `key_output`, and `value_output` all produced the same complete
gradient-directory SHA-256
`251e5186b223233fcecaa43ce25315d269af7bd72de11317fa08e799ea5cce42`.
The full root set changes some earlier gradients, so the control is sensitive,
but every root set reproduces `ff2_0` and `ff_bias2_0` bound gradients exactly.
Even output-only retains the 50 FF2 sign differences from PyTorch and the
`0.0060333` bias offset.

Root-set membership is therefore not the localized cause. The distinction
between the output-only complete source and the output-only synthetic FF2
block is upstream graph connectivity inside the output root. The next direct
control should keep source forward values exact while independently applying
`nc_stop_grad` to the FF2 hidden input and residual connection. This tests
whether recursive concat factorization depends on either upstream graph without
changing another arithmetic primitive. No score or forecast credit changes.

Decision:
`results/nncp_v33_libnc_concat_root_scope_gradient_v1/decision.json`.

## 2026-08-02: LibNC FF2 upstream-connectivity gate frozen

Candidate and proposal:
`nncp_v33_libnc_ff2_upstream_connectivity_gradient_v1`.

Output-only root scope in the complete source still produces bound-native FF2
gradients, while an output-only synthetic block from exact captured inputs
produces PyTorch-like gradients. This child varies the remaining structural
difference with forward-identical constant-copy controls on the activated FF2
hidden input and the residual connection. The first `nc_stop_grad` realization
failed before evidence because it mutates shared saved graph state; the frozen
replacement allocates an untracked tensor and copies the same value. The
variants cut neither,
hidden only, residual only, or both upstream graphs; all original concat roots
remain enabled.

Each source variant must retain exact archive and trace identity and repeat its
named gradients. The uncut variant must reproduce the full prior receipt. A
pass requires both-stop to transition FF2 matrix and bias gradients from the
bound values to PyTorch values, with single-cut controls identifying the
minimal responsible connection. A miss retires upstream connectivity as the
isolated cause. No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_ff2_upstream_connectivity_gradient_plan.md`.

Disposition: blocked infrastructure, zero scientific and score credit. The
initial `nc_stop_grad` realization and a replacement using
`nc_new_tensor_from_tensor_nz` plus `nc_tensor_copy` both reproduced the uncut
case but segfaulted on the first hidden-cut execution before emitting a named
gradient receipt. The saved concat-optimized graph therefore cannot be
intervened on at this boundary with either supported graph-detachment form.
The two failed adaptive receipts are
`operations/adaptive/failed/832_20260802T053058Z_aabbe879db.json` and
`operations/adaptive/failed/832_20260802T053447Z_8c6879e845.json`; the middle
compile-only failure is
`operations/adaptive/failed/832_20260802T053412Z_148d2d0c05.json`. This is not
a rejection of the connectivity hypothesis, but it closes this source-patch
realization and authorizes no further parity child.

## 2026-08-02: LibNC FF2 output-adjoint trajectory frozen

Candidate and proposal:
`nncp_v33_libnc_ff2_output_adjoint_trajectory_v1`.

The failed graph cuts do not justify abandoning the published LibNC update
contract. This successor observes rather than detaches the boundary. It adds
one distinct all-zero parameter tensor after each decoder state's FF2 bias,
captures that tensor's gradient as the exact FF2-output adjoint, and serializes
the exact activated FF2 input immediately before the projection. The addition
must preserve the bound archive, teacher trace, and every source-named
parameter-gradient byte across two executions.

Composing the adjoint `A` and input `H` as `A * transpose(H)`, with
`column_sum(A)` for the bias, distinguishes an upstream adjoint divergence
from special concat-optimized parameter-gradient accumulation. The matched
PyTorch graph supplies an algebraic control before either interpretation is
accepted. A unique localization authorizes only one miniature parity repair;
an intrusive probe or ambiguous composition is rejected. Score and forecast
credit remain zero.

Plan: `docs/nncp_v33_libnc_ff2_output_adjoint_trajectory_plan.md`.

## 2026-08-02: LibNC FF2 output adjoint localizes the missing gradient upstream

Two instrumented source executions retained the exact bound archive SHA-256
`8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da`,
teacher trace SHA-256
`cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4`,
and all 18 named gradient bytes. The zero probe was observation-neutral and
its input and adjoint directories repeated byte-identically.

The exact source adjoint differs from the matched PyTorch adjoint by
`0.0091472826898098` maximum absolute error, `11.4507277%` relative L2,
and two signs. Composing that source adjoint with the exact source FF2 input
reproduces `ff2_0` with zero error and `ff_bias2_0` within
`1.4901161193847656e-08`. The missing gradient is therefore upstream of the
FF2 matrix multiplication, not a special concat-matmul parameter-gradient
rule. The canonical adjoint bytes are now embedded in the decision receipt;
the only authorized child replays them at the post-FF2 residual join. No
compression score or forecast credit changes.

Decision:
`results/nncp_v33_libnc_ff2_output_adjoint_trajectory_v1/decision.json`.

