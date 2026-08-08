# Research Register Archive 008

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-02: LibNC FF2 residual-adjoint replay frozen

Candidate and proposal:
`nncp_v33_libnc_ff2_residual_adjoint_replay_v1`.

This one-change child keeps the matched four-state forward graph exact and
replaces only a backward adjoint. Its baseline remains unchanged. A
FF2-branch-only control applies the captured source adjoint only to the FF2
projection; the decisive variant applies it before the post-FF2 residual add,
where ordinary reverse-mode differentiation sends the same adjoint into the
FF2 and residual branches.

The gate requires byte-identical repeats, unchanged teacher probabilities, a
repeated parent PyTorch gradient hash, local FF2 and bias parity in the
branch-only control, continued upstream failure in that control, and all 18
named gradients within `2e-6` with zero sign mismatches only for the residual
join. A pass authorizes one exact first-update replay. A miss retires this
boundary without any tolerance, optimizer, loss, width, or parameter sweep.
No score or forecast credit is available.

Plan: `docs/nncp_v33_libnc_ff2_residual_adjoint_replay_plan.md`.

## 2026-08-02: LibNC residual-join adjoint reproduces the full gradient map

All baseline, FF2-branch-only, and residual-join executions repeated their
probability and gradient hashes. Every variant emitted the same probability
SHA-256
`2b4b6177d4417dd305cc18e01c902a6e2f2be256d20f1a51cc8919d956ce735a`
and remained within `3.725290298461914e-09` of the source teacher.

The unchanged baseline reproduced the prior PyTorch gradient hash and matched
only 4 of 18 source gradients. Applying the captured adjoint to the FF2 branch
alone matched 10 of 18, including `ff2_0` and `ff_bias2_0`, but left attention
and embedding gradients wrong. Applying exactly the same adjoint at the
post-FF2 residual join matched all 18 gradients: maximum absolute error
`8.940696716308594e-08`, zero sign mismatches, repeated gradient SHA-256
`9ba080bdde21f20d7fbf994d1bea75b96ee52687a249e81d23fcb51b646fec64`.

The missing LibNC behavior is therefore the adjoint delivered to the complete
post-FF2 residual join, not an FF2-local rule. This passes the frozen gate and
authorizes one source-bound first-update replay. The four captured columns are
receipt-specific evidence, not a constructive multi-update rule; score and
forecast credit remain zero.

Decision:
`results/nncp_v33_libnc_ff2_residual_adjoint_replay_v1/decision.json`.

## 2026-08-02: LibNC residual-adjoint first-update replay frozen

Candidate and proposal:
`nncp_v33_libnc_ff2_residual_adjoint_update_parity_v1`.

The existing four-state decoder graph, cross-entropy, per-parameter clipping,
and Adam implementation remain unchanged. The child installs the confirmed
source adjoint only at the four post-FF2 residual joins during backward, then
compares the resulting first-update parameters with the source final export.

The unchanged baseline must exactly repeat its prior maximum parameter error
and remain outside `2e-5`. The repaired forward probabilities must be
byte-identical to baseline, all final tensors must fall within `2e-5`, and two
repaired executions must repeat model, probability, and loss bytes. A pass
authorizes only a causal multi-update contract derivation. No score or forecast
credit is available.

Plan: `docs/nncp_v33_libnc_ff2_residual_adjoint_update_parity_plan.md`.

## 2026-08-02: residual-adjoint repair restores the bound first update

The unchanged decoder-graph baseline exactly repeated its prior maximum final
parameter error of `0.00031999964267015457`. Applying the four captured
adjoint columns at the post-FF2 residual joins left the forward probabilities
byte-identical and reduced the maximum error across every final tensor to
`2.8312206268310547e-07`. Two repaired executions produced final tensor
SHA-256
`b8e6007d538ab2eb0af8cfcd8ad94905df7e029c19f617d946edfcd4954570a6`
and identical probability and loss streams.

This proves that the localized adjoint difference fully explains the prior
one-update failure. It does not yet provide a constructive rule because the
four adjoint columns were captured from source truth. The only authorized
successor derives the adjoint causally from current tensors and decoded truth.
No score or forecast credit changes.

Decision:
`results/nncp_v33_libnc_ff2_residual_adjoint_update_parity_v1/decision.json`.

## 2026-08-02: concat-optimized final RMSNorm contract frozen

Candidate and proposal:
`nncp_v33_libnc_concat_rmsnorm_backward_contract_v1`.

The source-minus-PyTorch residual adjoint is constant across the 32 features
within each decoder state. For every state, that observed offset equals
`-inverse * mean(g)` at the final RMSNorm boundary. This yields the analytic
concat-root rule

```text
inverse * (g - mean(g) - output * mean(g * output))
```

instead of the already proved direct RMSNorm rule without `mean(g)`.

The child applies this formula only to final RMSNorm nodes under the four
concat-optimized output roots. The captured adjoint is validation truth and is
not injected. A pass requires analytic adjoint parity, all 18 named gradients,
unchanged forward probabilities, bound final tensors, and repeated executions.
It authorizes one source-bound multi-update receipt, with zero current score or
forecast credit.

Plan: `docs/nncp_v33_libnc_concat_rmsnorm_backward_contract_plan.md`.

## 2026-08-02: analytic concat-RMSNorm rule reproduces source backward

Without substituting a captured gradient, the centered analytic formula
reproduced the source residual-join adjoint within
`7.450580596923828e-08`, with zero sign mismatches. All 18 named gradients
matched within `4.172325134277344e-07`, again with zero sign mismatches. The
one-update forward remained byte-identical to baseline, every final tensor was
within `2.8312206268310547e-07` of the source export, and both gradient and
update executions repeated.

The receipt-specific intervention is therefore replaced by a causal rule over
the current final-RMSNorm input and its incoming adjoint. This passes the
frozen gate and authorizes one source-native multi-update receipt. It still
receives zero score and forecast credit.

Decision:
`results/nncp_v33_libnc_concat_rmsnorm_backward_contract_v1/decision.json`.

## 2026-08-02: concat-RMSNorm multi-update parity frozen

Candidate and proposal:
`nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_v1`.

This gate uses the first 32 raw canonical `enwik9` bytes, eight sequential
four-symbol updates, and the exact recovered NNCP source. Two native executions
must repeat archive, probability trace, final coefficients, and final tensor
export; native decoding must restore the input. The analytic replay then starts
from the same initial export and uses only the frozen centered RMSNorm backward
formula through all eight evolving parameter and memory states.

The command line advertises `--load_coefs`, but upstream compiles both load
calls out and the disabled generic expression is not type-correct. The gate
therefore retains the exact seeded source initialization and omits the inert
option. The already source-bound initial export supplies the same analytic
state. Decoder probabilities and the first restored-byte mismatch are recorded
even on a roundtrip miss so codec reconstruction and update parity cannot be
conflated.

Probability and final-tensor errors must remain at or below `2e-5`, and a
second analytic replay must be byte-identical. A pass authorizes the smallest
faithful-profile constructive prefix gate, not a forecast change. A miss
retires the multi-update parity claim without a population, optimizer, or
tolerance sweep.

Plan: `docs/nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_plan.md`.

## 2026-08-02: concat-RMSNorm multi-update contract rejected

The terminal 32-byte execution is scientifically negative. Both source runs
repeated a 128-byte archive with SHA-256
`abf30857584bf888640c27785cc41d7c260510091fd07f5324d1c61c361af94f`,
the teacher trace, final coefficient package, and canonical tensor export.
Both analytic executions also repeated exactly.

The analytic probabilities match the first four-symbol segment within
`3.725290298461914e-09`, confirming the one-update receipt. At the first
evolving-state segment, error jumps to `0.010298056527972221`; the maximum
across eight updates is `0.01777813397347927`. Final tensors miss the source by
up to `0.001998595893383026`. The exact centered final-RMSNorm formula is
therefore not a sufficient multi-update LibNC contract.

The native archive also decodes deterministically to the wrong 32 bytes, with
the first mismatch at byte zero. The source advertises `--load_coefs` but
compiles both calls out; enabling the invalid generic expression either fails
to compile or corrupts decoder graph shapes, so those infrastructure attempts
do not count as scientific variants. Their adaptive failed receipts remain
preserved separately.

Retire this formula, captured-adjoint replay, fixed one-update repair, and all
learning-rate, clipping, epsilon, tolerance, or shorter-population rescues.
No faithful-profile prefix is authorized. Forecast remains `109,389,323`
bytes; verified full-1G score remains unknown; score credit remains zero.

Decision:
`results/nncp_v33_libnc_concat_rmsnorm_multiupdate_parity_v1/decision.json`.

## 2026-08-02: static page-entity roster screen is subscale

The first post-TESSERA information-source screen tested a page-internal future
entity roster rather than another static semantic type. Each complete page's
title, link targets and labels, template names and keys, and section headings
defined a set of development-catalog lexemes. The proposed operation would
transmit that roster before the page and replace later lexical events with
roster references while preserving the JANUS-plus-quotient truth-update
trajectory.

The screen was deliberately more favorable than a realizable codec. Roster
identities, per-page hit and lexeme counts, morphology, exact WRT surface
variants, model bytes, source, framing, and termination were all free. It
charged only the exact enumerative rank of hit positions among supported token
opportunities and the enumerative order of hit lexeme IDs given their exact
per-page counts.

The best role set was `LINK_TARGET`. It displaced `134,258.793` exact joint
qbit-bytes but still required `111,257.294` optimistic side bytes, leaving only
`23,001.499` bytes over canonical 10M. Development, selection, and sealed gains
were positive (`17,818.871`, `3,681.612`, and `1,501.017` bytes), but the full
gain missed the frozen `30,000`-byte gate before paying any roster identity or
surface cost. Prose-only and combined prose/link forms were already negative by
`96,998.759` and `134,300.329` bytes respectively.

Decision: reject the static free-count page-entity roster alphabet before
adaptive proposal materialization. Do not build a roster side coder, role
ladder, relation-subset sweep, or paid model. This does not reject a genuinely
predictive relational model, but such a model must introduce and demonstrate
new sequence information rather than inherit this subscale enumerative result.
Forecast remains `109,389,323` bytes, verified full-1G remains unknown, and
score credit remains zero.

Evidence:

- `tools/mobius2_page_entity_roster_screen.py`
- `results/mobius2_page_entity_roster_enumerative_screen_v0/decision.json`
- `docs/post_tessera_event_universe_portfolio_20260802.json`

## 2026-08-02: LibNC update-state trajectory frozen after provenance correction

Candidate and proposal: `nncp_v33_libnc_update_state_trajectory_v1`.

The prior multi-update receipt contains a material provenance error. Its save
hook runs inside `nc_param_list_end`, so the artifact named `final_coefs` is
the seeded initial parameter list. The comparison between that artifact and
the analytic eight-update state is invalid. The repeated native probability
trace and its `0.010298` second-segment divergence remain valid, as do the
separately bound one-update receipts.

This correction does not relabel the failed analytic formula as a pass. The
one-change successor adds observation-only saves immediately after each actual
source optimizer and memory update. It binds all eight post-update parameter,
`mem_h`, and `train_h` states across two executions, then compares them with a
non-intervened analytic trajectory. The first divergent family distinguishes
optimizer, persistent-memory, and evolving forward-operation contracts.

A unique localization authorizes only the matching component-level child. It
does not authorize a faithful-profile prefix, score credit, forecast credit,
or inheritance of NNCP's published result. Any archive or teacher-trace change
is an infrastructure failure.

Plan: `docs/nncp_v33_libnc_update_state_trajectory_plan.md`.

## 2026-08-02: true post-update state localizes the first mismatch to forward evaluation

The observation-only source child preserved and repeated the 32-byte archive
SHA-256
`abf30857584bf888640c27785cc41d7c260510091fd07f5324d1c61c361af94f`
and teacher-trace SHA-256
`0cebe0c17a64a8bd0183ea9278c8df70e7dd335c2eda3d3d87795afcbc4d59c7`.
It captured the actual source state immediately after each optimizer and memory
update, rather than relying on the earlier pre-evaluation save hook.

After update one, all source and analytic parameters agree within
`2.8312206268310547e-07`; `mem_h` and `train_h` agree within
`2.384185791015625e-07`. Nevertheless, the next four-symbol prediction segment
already differs by `0.010298056527972221`. Parameter and memory errors become
large only after that bad forward/backward pass, at update two
(`0.00045276060700416565` and `2.7441470623016357`, respectively).

The unique first boundary is therefore `evolving_state_forward_operation`:
the optimizer and persistent-memory update are not the initial cause. Retire
this diagnostic after authorizing exactly one child that starts from the
captured source post-update-one parameters and memory and identifies the first
divergent arithmetic node in the second forward segment. Do not rescue with
tolerances, learning rates, clipping, widths, or shorter populations. Score
and forecast credit remain zero; forecast remains `109,389,323` bytes and the
verified full-1G score remains unknown.

Decision:
`results/nncp_v33_libnc_update_state_trajectory_v1/decision.json`.

## 2026-08-02: LibNC second-segment forward trajectory frozen

Candidate and proposal:
`nncp_v33_libnc_second_segment_forward_trajectory_v1`.

This child starts its primary analytic replay from the source's actual
post-update-one parameters and persistent memory, then compares the seven
existing LibNC internal forward observations across the second four-symbol
segment. A second replay starts from the near-matching analytic state and acts
only as a sensitivity control.

If the exact-source-state replay first differs at a named block, one finer
arithmetic child inside that block is authorized. If it matches while the
near-state control reproduces the probability miss, the cause is localized to
exact state evolution instead. Archive, teacher trace, update-state captures,
and forward dumps must repeat, and the source observations must remain neutral.
No score or forecast credit is available.

Plan:
`docs/nncp_v33_libnc_second_segment_forward_trajectory_plan.md`.

## 2026-08-02: exact source state diverges inside nonzero-memory attention

Both observed native executions preserved the parent archive, probability
trace, eight coefficient states, and eight memory states byte-for-byte. Each
execution produced 224 aligned internal tensor records, and the complete dump
repeated exactly.

Starting the second segment from the source's own exported post-update-one
parameters and `mem_h` does not restore the analytic forward replay. The first
record, state-zero `attn_out_bl`, already differs by
`1.239846110343933`; the corresponding output distribution differs by
`0.010298050008714199`. Starting from the near-matching analytic state produces
the same boundary and a `0.010298056527972221` output error. The residual
`2.8312206268310547e-07` parameter and `2.384185791015625e-07` memory errors are
therefore not the cause of the jump.

Localize the missing contract to the nonzero-memory attention block before its
residual join. Authorize exactly one child that observes embedding, attention
normalization, query/key/value projections, transformed memory, content and
relative scores, softmax weights, attended value, and output projection for
state zero of segment two. No other forward block or numerical sweep is
authorized. Score and forecast credit remain zero.

Decision:
`results/nncp_v33_libnc_second_segment_forward_trajectory_v1/decision.json`.

## 2026-08-02: LibNC nonzero-memory attention trajectory frozen

Candidate and proposal:
`nncp_v33_libnc_second_segment_attention_trajectory_v1`.

The source-state forward receipt authorizes one observation-only child inside
state zero of the second segment's attention block. It binds every major
operation from embedding through output projection, using the actual source
post-update-one parameters and memory and fixed tensor-layout conversions.
The first aligned arithmetic node above `2e-6` is the only authorized
successor boundary. Source identity, dump repeatability, and record alignment
remain mandatory. No score or forecast credit is available.

Plan:
`docs/nncp_v33_libnc_second_segment_attention_trajectory_plan.md`.

## 2026-08-02: nonzero-memory attention first differs at embedding lookup

The instrumented source repeated its archive, teacher trace, eight parameter
states, eight memory states, and all 360 tensor records exactly. The added
observations were neutral relative to the parent receipt, and all eight
segments contained the same 45-record schema.

The first second-segment state differs before attention arithmetic. The source
`a_embed` observation and the replayed embedding differ by
`1.210031509399414`, followed by `2.7441473007202156` at attention
normalization. Content, relative, softmax, attended-value, and projection
differences are downstream. Therefore this receipt does not attribute the
failure to nonzero-memory attention math; it localizes the boundary to the
embedding input or live embedding state at segment entry.

Authorize exactly one child that records the actual decoder input symbol before
the lookup and replays the captured embedding from that symbol. It must
distinguish input schedule from live-versus-exported parameter state. Do not
alter attention, memory length, model width, optimizer, or tolerances. Score
and forecast credit remain zero.

Decision:
`results/nncp_v33_libnc_second_segment_attention_trajectory_v1/decision.json`.

## 2026-08-02: LibNC segment-entry embedding contract frozen

Candidate and proposal:
`nncp_v33_libnc_second_segment_embedding_contract_v1`.

This child adds one state-zero scalar observation of the integer symbol after
LibNC slices and reshapes the decoder input. The exact source post-update-one
embedding is then indexed by that observed symbol, with the existing source
embedding output serving as validation truth. A pass must uniquely identify an
input-schedule mismatch or a live-parameter mismatch while preserving every
parent identity artifact. No score or forecast credit is available.

Plan:
`docs/nncp_v33_libnc_second_segment_embedding_contract_plan.md`.

## 2026-08-02: source uses a fresh zero-input, zero-memory block schedule

The first embedding-contract attempt failed before compilation because the
observer patch rebound itself recursively. The explicit infrastructure retry
fixed that binding and produced the scientific receipt. Its enhanced and
unmodified observer builds emitted identical archives, traces, post-update
states, and all shared internal tensor values; both enhanced executions also
repeated exactly.

At the start of source segment two, the observed decoder input is `0`, not the
assumed preceding truth symbol `100`. Indexing the exact source post-update-one
embedding at symbol zero restores `a_embed` exactly and keeps query/current
key/value projections within `1.7881393432617188e-07`. The next divergence is
`a_memory_kv`: the source tensor is all zero while the analytic replay retained
the nonzero post-update memory, producing `1.5986770391464233` error.

The combined contract is visible in source control flow. With `block_len=4`,
each four-symbol segment is a separate `process_block` call. Every call invokes
`model_reset`, and state zero reads position `-1` from that fresh block, which
returns zero. The analytic multi-update replay incorrectly carried both the
previous truth symbol and `mem_h` across these block boundaries.

Authorize exactly one constructive eight-update child that resets memory to
zero and prepends input zero for every four-symbol block while retaining the
already proved concat-RMSNorm backward and Adam rules. No alternate reset,
memory length, block length, width, optimizer, or tolerance sweep is
authorized. Score and forecast credit remain zero.

Decision:
`results/nncp_v33_libnc_second_segment_embedding_contract_v1/decision.json`.

## 2026-08-02: LibNC process-block reset multi-update parity frozen

Candidate and proposal:
`nncp_v33_libnc_process_block_reset_multiupdate_parity_v1`.

This child changes only the analytic schedule: each four-symbol block begins
with input zero and zero persistent memory, exactly matching native
`process_block`. It compares all eight probability segments, post-update
parameter states, `train_h`, and post-update `mem_h` against two neutral native
captures. A pass authorizes the smallest source-bound constructive prefix gate;
no score or forecast credit is available.

Plan:
`docs/nncp_v33_libnc_process_block_reset_multiupdate_parity_plan.md`.

## 2026-08-02: process-block reset fixes predictions but misses the frozen memory gate

The corrected schedule reduced the maximum eight-segment probability error
from `0.01777813397347927` to `3.9208680391311646e-07`. Every post-update
parameter remained within `2.034008502960205e-06`, and both native and analytic
executions repeated exactly with legal probability tables. This confirms that
the prior large multi-update rejection was caused by the test harness carrying
input and memory across native `process_block` resets.

The frozen candidate is still a scientific `REJECT`. Source `train_h` and the
post-update `mem_h` differ from the analytic state by up to
`9.894371032714844e-06`, above the predeclared `2e-6` gate. That state is reset
before another prediction in this deliberately four-byte-block profile, but it
was explicitly part of the contract and cannot be waived after inspection.
Retire this exact reset realization and do not relax its tolerance.

This result exposes a separate validity issue in the original multi-update
test: the published NNCP profile uses a long `process_block`, so consecutive
updates share input and memory inside that block. The earlier native command's
`--block_len 4` never exercised that contract. One new source profile with all
32 diagnostic bytes in a single block is therefore authorized as a distinct
continuous-state experiment, not a rescue of the retired reset gate. Score and
forecast credit remain zero.

Decision:
`results/nncp_v33_libnc_process_block_reset_multiupdate_parity_v1/decision.json`.

## 2026-08-02: LibNC continuous-block multi-update parity frozen

Candidate and proposal:
`nncp_v33_libnc_continuous_block_multiupdate_parity_v1`.

This source-bound child places the same 32 symbols and eight four-symbol
updates inside one native `process_block`. It therefore tests the carried
predecessor and persistent-memory trajectory that the published long-block
profile actually uses. The analytic graph, optimizer, and backward contract
are unchanged. A pass requires all probabilities, post-update parameters, and
memory states within their original tolerances across repeated native and
analytic runs. No score or forecast credit is available.

Plan:
`docs/nncp_v33_libnc_continuous_block_multiupdate_parity_plan.md`.

## 2026-08-02: continuous-block parity also misses only the frozen memory gate

The single-process-block source and analytic executions repeated exactly.
Continuous carried-state probability agreement is stronger than the reset
control: the maximum error across eight segments is
`1.4808028936386108e-07`. Every post-update parameter remains within
`2.343207597732544e-06`, far inside the `2e-5` gate.

The candidate nevertheless returns a valid `REJECT`. `train_h` and `mem_h`
reach `9.804964065551758e-06` error at update eight, exceeding the frozen
`2e-6` state threshold. Do not widen the tolerance or extend this miniature.
The result shows that the repaired analytic implementation shadows LibNC
closely, but it does not establish exact numerical identity and cannot inherit
the published `106,632,363`-byte NNCP result.

The local strategic boundary is now explicit. Exact CUDA teacher execution is
unavailable on this AMD host; the earlier self-consistent ROCm full-profile Q1
lost `119,472.534 B/M` at its frozen startup scope; and this component replica
misses exact state identity. The next NNCP action must change execution
capability or information scope rather than continue primitive tolerances. A
source-native CPU concurrency gate may test whether the immutable LibNC teacher
can be accelerated without changing its archive; otherwise mature NNCP
evidence still requires an NVIDIA host. Forecast remains `109,389,323` bytes,
verified full-1G remains unknown, and score credit remains zero.

Decision:
`results/nncp_v33_libnc_continuous_block_multiupdate_parity_v1/decision.json`.

## 2026-08-02: source-native NNCP CPU T16 archive-identity gate frozen

Candidate and proposal: `nncp_v33_cpu_t16_archive_identity_q0_v1`.

The immutable native batch-32 teacher previously emitted the same 9,246-byte
archive twice at four CPU threads, with a `279.797`-second adjacent mean encode
and 5,782,588 KiB peak tree RSS. This host has 16 physical cores. Q0 changes
only the LibNC worker count to 16 and performs one guarded 10,000-symbol encode.

Promotion requires exact archive identity, decimal-10GB compliance, and at
least 50 percent elapsed reduction. A pass authorizes only a T16 repeated
trace-off/trace-on/decode identity gate. A miss closes local CPU thread scaling
without a thread or affinity sweep. No compression score or forecast credit is
available.

Plan: `docs/nncp_v33_cpu_t16_archive_identity_q0_plan.md`.

## 2026-08-02: native NNCP T16 is exact but slower

The immutable source-native T16 execution completed normally and emitted the
exact reference archive: 9,246 bytes, SHA-256
`097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5`,
byte-for-byte identical to both adjacent T4 archives. Peak sampled single and
tree RSS were 5,779,632 KiB, below the decimal-10GB limit.

The performance hypothesis failed decisively. T16 required `379.1668` measured
seconds versus the adjacent T4 mean of `279.797`, a negative reduction of
`-0.3551496263362366`. During the active model phase it used only about 4.2 CPU
cores despite the 16-worker request. Retire local source-native thread scaling
without thread-count, affinity, NUMA, compiler, batch, or model sweeps. Do not
run the T16 trace/decode Q1 or a mature CPU teacher.

The archive identity is useful execution evidence but supplies no compression
or forecast credit. The exact published CUDA teacher remains unavailable on
this AMD-only host; ZLUDA is already terminal because the shipped CUDA module
contains NVIDIA SASS without PTX and fails kernel lookup. Forecast remains
`109,389,323` bytes and the verified full-1G score remains unknown.

Decision: `results/nncp_v33_cpu_t16_archive_identity_q0_v1/decision.json`.

## 2026-08-02: BIFRONS reverse-causal two-ended ceiling frozen

Candidate: `bifrons_reverse_causal_joint_ceiling_q0_v1`.

Proposal: `bifrons_reverse_causal_joint_ceiling_v1`.

The next local information-source gate changes coding direction rather than
adding another left-causal residual feature. It runs the receipt-bound
endpoint428 pair/layer-0 backend over a byte-reversed WRT population, with the
canonical dictionary also deterministically reversed for pretraining. One
explicitly transmitted cut divides the population into a JANUS-plus-quotient
forward prefix and an endpoint428 reverse-causal suffix. This creates no cyclic
dependency: the decoder reconstructs the prefix from the left and the suffix
from the right.

Q0 uses the 171 complete pages ending before raw byte 1,000,000: 984,835 raw-
equivalent bytes, 591,230 WRT bytes, and 4,729,840 P1 rows. Legal cuts are only
zero, complete-page ends, and the population end. Rounded-Q256 codelength
selects one cut with earliest-cut tie breaking. The exact candidate then pays
a 49-byte frame and two actually terminated arithmetic streams. There is no
per-page or per-event selector.

The first guarded reverse run can reject the hypothesis. Only an exact gain of
at least 3,000 B/M after framing triggers a second source execution and its
required archive/P1 identity checks. A pass authorizes one frozen canonical
10M replay; a miss retires this exact one-cut construction without direction,
cut, pretraining, dictionary-order, or page-mode sweeps. Score and forecast
credit remain zero.

Plan: `docs/bifrons_reverse_causal_joint_ceiling_q0_plan.md`.

## 2026-08-02: BIFRONS reverse-causal two-ended ceiling is terminal negative

The guarded source-native reverse execution completed normally in `585.8668`
seconds at 9,046,080 KiB peak sampled RSS, below the decimal-10GB limit. Its
4,729,840-row P1 trace reproduced the 177,522-byte source arithmetic payload
exactly, decoded the reversed WRT prefix exactly, and contained only legal
nonzero probabilities. The two-stream candidate also decoded both sides and
reconstructed all 591,230 original WRT bytes exactly.

The information hypothesis failed. The minimum-Q256 legal cut was the final
population byte, so the chosen reverse suffix was empty. The exact candidate
was consequently the 168,106-byte joint-prefix archive plus its twelve
additional cut and length bytes: 168,118 bytes, a 12-byte loss or
`-12.184782222402738 B/M`. All-reverse required 177,559 bytes, 9,453 bytes
more than the joint parent. The closest interior cut reversed the final 19,586
WRT bytes and was already 3,464,050 qbits, or about 1,691.431 bytes, worse
before framing. All 170 interior page-boundary suffixes were worse than the
all-forward trajectory.

This is a scientific rejection, not an infrastructure failure. Retire the
whole-prefix/suffix, one-cut, reversed-dictionary endpoint428 reverse expert.
Do not run the conditional second source pass or canonical 10M replay, and do
not sweep direction granularity, dictionary order, pretraining, or cut
restrictions. The result does not close a future-information codec with a
different causal construction, but it shows that source-native endpoint428
run backward supplies no paying suffix at this population after the strongest
joint trajectory.

Forecast remains `109,389,323` bytes, verified full-1G remains unknown, and
score credit remains zero.

Decision:
`results/bifrons_reverse_causal_joint_ceiling_q0_v1/decision.json`.

## 2026-08-02: NNCP v3.3 ROCm incremental-KV runtime Q0 frozen

Candidate and proposal: `nncp_v33_rocm_incremental_kv_runtime_q0_v1`.

The published NNCP family remains the only locally held direct under-target
external construction, but its exact faithful ROCm realization is not yet a
viable Gamma candidate. The existing constructive decoder evaluates a full
64-position Transformer segment after every newly decoded state, repeating
causally redundant prefix work 64 times per online update. Its exact
65,536-symbol Q1 also loses heavily to the matching JANUS-plus-quotient
prefix, so this runtime experiment earns no score or forecast credit.

This substrate child changes only inference execution. Each layer projects
the fixed 256-position memory into one key/value cache, then appends the key
and value of each newly decoder-visible input symbol. One-token attention uses
the exact relative-position slice corresponding to the parent's shifted
64-query layout. Once all 64 positions have been reconstructed, the caches
are discarded and the unchanged full differentiable segment replay performs
the same cross entropy, clipping, Adam update, and persistent-memory update.

Q0 uses the exact first 2,048 preprocessed symbols, two independent encoders,
and one model-driven decoder. It requires candidate archive, branch trace,
symbols, loss, model, optimizer, and memory identity; exact parent final-model
and loss identity; decimal-10GB compliance; no more than 16 archive bytes of
drift; and at least 50 percent median runtime reduction versus the adjacent
18.220641091-second receipt. Exact parent stream identity authorizes one
65,536-symbol runtime replay. A changed but self-consistent stream authorizes
only a separately scored 65,536-symbol headroom replay. A miss retires this
eager PyTorch cache realization without implementation rescue sweeps.

Plan: `docs/nncp_v33_rocm_incremental_kv_runtime_q0_plan.md`.

## 2026-08-02: NNCP incremental-KV runtime Q0 passes as a changed stream

The heavy-lock ROCm Q0 completed normally. Two encoders and one independent
model decoder emitted the same 3,613-byte archive and 28,673-entry branch
trace, reconstructed all 2,048 symbols, and produced identical loss, model,
Adam, and persistent-memory hashes. The unchanged differentiable replay also
matched the full-prefix parent's final model SHA-256
`2ae4efe57f08736c3e7d3f67104b74a496f4c54af6ee24b142904ab0be5014f5`
and loss `9.782143592834473` exactly.

Median measured model execution fell from `18.220641091` to
`3.401104436001333` seconds, an `81.33378282896293%` reduction. Peak allocated
and reserved memory were 7,229,241,344 and 7,822,376,960 bytes, both below
decimal 10 GB. The archive length delta was zero.

The smaller GEMM shapes changed BF16 rounding: candidate archive SHA-256
`836002ec194075dbc76739f6d734f1207fcd343b99b17d1bb352b030c7c4d8c7`
and branch-trace SHA-256
`e3294d1ac424fa1611be7a72aedb811cc2c62b7f4aacb3b9fbecdf453d34153d`
do not match the parent. This is therefore a substrate pass and
`AUTHORIZED_CHANGED_STREAM_65536_HEADROOM`, not parent-stream identity or
compression evidence. Score and forecast credit remain zero.

Decision:
`results/nncp_v33_rocm_incremental_kv_runtime_q0_v1/decision.json`.

## 2026-08-02: NNCP incremental-KV 65,536-symbol headroom Q1 frozen

Candidate and proposal:
`nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1`.

The sole authorized successor applies the frozen incremental cache through 32
consecutive online update segments over the exact first 65,536 NNCP symbols.
It runs two encoders and one model-driven decoder, restores the exact raw
prefix through the official NNCP inverse, and compares its actually terminated
archive with a newly terminated JANUS-plus-quotient payload at the identical
WRT emission-group/raw boundary.

Promotion requires every archive, trace, symbol, loss, complete-state, inverse,
probability, repeat, and allocated/reserved decimal-10GB gate plus at least
3,000 gross bytes per raw million. A valid miss retires the changed-stream
realization without rescue sweeps. The published NNCP score remains external
context only.

Plan:
`docs/nncp_v33_rocm_incremental_kv_65536_headroom_q1_plan.md`.

## 2026-08-02: NNCP incremental-KV 65,536-symbol Q1 is terminal negative

The changed-stream Q1 completed normally in `333.416` worker seconds. Both
encoders and the independent decoder produced the identical 96,142-byte
archive and 917,527-entry branch-frequency trace, decoded all 65,536 symbols,
matched all 32 segment losses, and ended at complete model/Adam/memory SHA-256
`9da56660c487182375ff9359d26a5dbab93cbfc82a40da50c13da339d827e5b4`.
The official NNCP inverse restored the exact 322,978-byte raw prefix. All
probabilities were legal and the allocated/reserved peaks of 8,632,796,160 and
9,271,508,992 bytes remained below decimal 10 GB.

The compression hypothesis failed decisively. The candidate archive was
96,142 bytes while the actually terminated and decoded JANUS-plus-quotient
payload at the identical boundary was 57,555 bytes. Incremental NNCP therefore
lost 38,587 bytes, or `-119,472.53373294775 B/M`, against a required gain of
3,000 B/M. Its smaller GEMM schedule materially improves execution: the three
runs took 105.587, 104.686, and 106.027 seconds versus approximately 575 to
577 seconds for the full-prefix Q1. That runtime result does not rescue the
negative archive economics.

Retire this faithful-profile changed-stream construction without architecture,
precision, cache-layout, stream-count, optimizer, block-layout, or compiler
sweeps. Preserve incremental KV only as a runtime primitive if a future NNCP
model independently demonstrates target-bearing compression headroom. Score
credit remains zero; forecast `109,389,323` and unknown full-1G status are
unchanged.

Decision:
`results/nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1/decision.json`.

## 2026-08-02: MÖBIUS-2 JANUS parity token-fill ceiling frozen

Proposal: `mobius2_janus_parity_token_fill_ceiling_v1`.

Candidate: `mobius2_janus_parity_token_fill_ceiling_qh0_v1`.

The post-TESSERA boundary requires new information about prose-token identities
after the exact JANUS-plus-quotient trajectory. Ordinary causal word modeling
is not new: the bounded Sequence Memoizer saved one exact byte, legal typed
Skip-CTS is subscale, and direct token XZ, BWT, BWT-plus-MTF, and legacy RePair
streams all fail optimistic ceilings.

This QH0 changes the coded factorization. Within each complete page, it first
codes prose-token positions 0, 2, 4, and so on. It then codes positions 1, 3,
5, and so on after their immediate left and right even anchors have already
been decoded. The side model is a development-frozen Q24 PPM with explicit
escape/backoff over canonical lexemes plus an exact WRT-program variant field.
U0 is a unigram, C1 is the original-order causal control, FL uses only the left
even anchor, FB uses the true left/right anchors, and FR substitutes the next
decoded even anchor to destroy immediate-right alignment while preserving the
same pass order and table family.

QH0 supplies the exact token-position schedule, static tables, lexeme/variant
catalogs, and implementation free. It still constructs and terminates the
actual side and residual range streams and pays an 80-byte frame. Every other
WRT byte stays on its joint P1 row. Repeated model/archive identity, side
decode, residual decode, complete WRT reconstruction, and official raw inverse
are mandatory. Promotion requires positive 60/20/20 page-split FB gains, FB
strictly smaller than all four controls, and at least 30,000 bytes saved on
canonical 10M. A pass authorizes only a paid schedule/table/source gate; a miss
retires this event universe and all preregistered parity rescues.

Plan:
`docs/mobius2_janus_parity_token_fill_ceiling_plan.md`.

