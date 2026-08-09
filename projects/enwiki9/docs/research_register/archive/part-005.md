# Research Register Archive 005

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-07-28 - ROCm batched causal teacher - REJECTED

A corrected shifted-input audit proved the batched ROCm model causal: changing target 8 changed shifted input 9, while outputs 0 through 8 remained exactly identical. Q0 then produced a deterministic 90,931-byte teacher payload through 322,978 raw bytes with exact symbol replay and official inversion. It nevertheless trailed Gamma by 32,369.610 bytes. Q1 extended the identical architecture to 500,000 raw bytes and again passed causality, symbol replay, and official inversion, but the shared-boundary deficit grew to 51,043.031 bytes. The marginal 177,008-byte band lost 18,673.421 bytes, or -105,494.788 B/M, versus the +3,000 B/M authorization gate. The 1M extension and quotient student are not authorized. The lane receives zero score credit. See `docs/nncp_rocm_batched_teacher_decision.md`.
## 2026-07-28: JANUS paid fixed-population residual MDL Q0

`janus_paid_residual_mdl_q0_v1` tested a legal two-part fixed-corpus mechanism
that was not covered by CHIRON's failed chronological-transfer experiment. A
future-informed residual model was trained on the complete evaluated
population, frozen, quantized, transmitted in the accounting model, and used
causally at runtime.

The opening-1M exact parent payload replayed at 173,859 bytes. On the represented
complete population, the parent required 173,807 bytes and JANUS required
168,900 bytes, a gain of 4,907 bytes or 4,908.356301 B/M. A node-bias control
gained only 46 bytes and a circular-shift control lost 11,586 bytes. The model
artifact was 127,695 bytes and provisional compressed implementation source was
3,883 bytes. Literal 1M two-part accounting is negative by 126,671 bytes;
full-corpus amortization projects 4,776.778301 net B/M.

Decision: `AUTHORIZED_10M`, zero score credit. Produce an exact canonical-10M
endpoint428 trace and rerun the frozen Q0 experiment once. Require at least
30,000 gross exact bytes and 21,000 package-adjusted projected net bytes before
authorizing an integer decoder. Do not change architecture, epochs, block
length, optimizer, or quantization after failure.

Receipt:
`results/janus_paid_residual_mdl_1m_v1/decision.json`
## 2026-07-28: JANUS Q0 authorization withdrawn pending exact repair

Review found that the first `janus_paid_residual_mdl_q0_v1` receipt terminated
complete-block substreams separately, omitted the imported oracle dependency
from its provisional source accounting, did not charge J1 as a paid candidate,
and did not prove A/B model and payload identity. The measured 4,907-byte signal
remains a provisional paid-model witness but no longer authorizes Q1.

JANUS is now `blocked_dependency`. A corrected Q0 must prove full-stream parent
payload byte identity, candidate decode, tail fallback, WRT/raw inverse binding,
canonical paid serialization, J1/J2 total selection, and deterministic duplicate
training. The already queued 10M endpoint trace is retained as zero-credit,
archive-identity-gated infrastructure only. No 10M JANUS training may begin
until the corrected Q0 passes.
## 2026-07-28: Exact endpoint428 10M P1 trace infrastructure

The zero-credit trace gate for corrected JANUS completed on the canonical 10M
population. The observation-enabled archive is byte-identical to the existing
trace-off endpoint428 archive: both are 1,635,174 bytes with SHA-256
`dddc0d0e4824433c605d870470d80bb119292b465689d0381933b37c5fb0e8d9`.

The trace contains 100,029,648 bytes and the exact WRT store contains 6,251,857
bytes. Peak sampled single-process RSS was 9,078,320 KiB, below the official
decimal limit, with no guard violation. This artifact has zero score credit and
does not authorize 10M JANUS training until corrected Q0 passes.

Receipt:
`results/endpoint428_pair_layer0_online_native_trace_10m_v1/decision.json`
## 2026-07-28: Corrected JANUS Q0 v2 superseded by null repair

The first repaired Q0 proved exact parent payload identity, full candidate and
J1 arithmetic decode, WRT/raw inverse binding, tail fallback, canonical
serialization, paid J1/J2 accounting, and duplicate model/P1/payload identity.
J2 saved 4,907 exact bytes and its frozen research package allowance was
188,535 bytes.

The receipt is superseded because JS circularly shifted adjusted probabilities
rather than residual logits relative to the parent. That made the null
artificially destructive. Q0 must be repeated with the same deterministic J2
fit and a global byte-row shift of residual logits. The v2 receipt has zero
score credit and does not authorize 10M.

Receipt:
`results/janus_paid_residual_mdl_1m_v2/decision.json`
## 2026-07-28: Corrected JANUS paid MDL Q0 v3 authorizes 10M

The repaired `janus_paid_residual_mdl_q0_v1` Q0 now uses one full-stream range
coder, preserves the exact parent P1 on the 166-byte WRT tail, emits and
byte-matches the parent payload, decodes J1 and J2 payloads, binds the WRT/raw
inverse receipt, serializes canonical JBIAS1/JMDL1 objects, charges frozen
decoder allowances, and reproduces identical model, adjusted P1, payload, and
training metrics in two complete fits.

J0 was 173,859 bytes. J1 was 173,814 bytes, a 45-byte gain. J2 was 168,952
bytes, a 4,907-byte gain. The corrected global byte-row residual-shift null was
181,416 bytes, a 7,557-byte loss. J2's canonical compressed model plus decoder
and framing allowance is 188,535 bytes, producing a projected package-adjusted
rate of 4,718.465 B/M. J2 is the projected-total winner.

Decision: `AUTHORIZED_10M`, zero score credit. Run the unchanged fixed model
family once on the exact canonical-10M trace after binding the WRT store to its
raw inverse. A 10M failure retires this recurrent shape unchanged. A pass
authorizes residual concentration and quotient compilation, not a dense native
GRU.

Receipt:
`results/janus_paid_residual_mdl_1m_v3/decision.json`
## 2026-07-29: JANUS paid recurrent residual is terminal negative at 10M

The unchanged canonical-10M `janus_paid_residual_mdl_q0_v1` screen completed
with every exactness and determinism gate intact. J0 was 1,635,137 payload
bytes. J1 gained 74 bytes. J2 gained 14,742 bytes, or 1,474.2 B/M gross. Its
canonical model plus frozen decoder and framing allowance was 183,439 bytes,
leaving a projected package-adjusted rate of 1,290.761 B/M. The corrected
shifted-residual null lost 41,798 bytes.

The candidate fails the predeclared 30,000-byte gross and 2,100 B/M net gates.
Decision: terminal `measured_negative`, zero score credit. Retire the fixed
143,711-parameter two-layer GRU, 256-WRT-byte reset, fixed optimizer/epochs,
per-tensor int8 quantization, and dense native integration. Do not sweep these
dimensions or run larger populations.

This result is not a universal impossibility theorem for paid fixed-corpus
models. Any successor must predeclare a materially different constructive
description, such as an exact MDL-pruned sparse context DAG, and must establish
a target-scale upper bound before native work.

Receipt:
`results/janus_paid_residual_mdl_10m_v1/decision.json`
## 2026-07-29: FXCM dense-budget capacity passes 250K construction gate

`fxcm_budget_preserving_capacity_v1` completed its previously cancelled exact
250K gate. The archive is 45,179 bytes, roundtrip is exact, and the second
archive is byte-identical. The candidate is one byte worse than the frozen
45,178-byte parent at this discovery scope. Live observation placed the codec
below the decimal memory limit.

The proposal's frozen kill rule assigns sign judgment to opening 1M, not 250K.
Authorize exactly one adjacent parent/candidate 1M comparison. Retire unchanged
if the candidate is non-positive. Do not alter dense budget bytes, index
mapping, scrambler constants, or table subsets.

Receipt:
`results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_densebudget96_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-28T204906.json`

## 2026-07-29: FXCM dense-budget capacity is terminal negative at exact 1M

The predeclared adjacent comparison completed on the same canonical opening
1,000,000 raw bytes. The frozen parent produced a 174,536-byte archive and a
564,146-byte package. The budget-preserving capacity candidate produced a
174,533-byte archive and a 564,198-byte package. Both roundtripped exactly and
produced byte-identical deterministic second archives.

The additional 1,215,436 deterministic FXCM cells therefore saved only 3
archive bytes, or 3 B/M, while adding 52 package bytes. Counted total worsened
by 49 bytes. This is three orders of magnitude below the frozen 2,000 B/M
primary-mechanism gate.

Decision: terminally reject `fxcm_budget_preserving_capacity_v1`. Do not tune
the dense budget, scrambler, or table subsets, and do not run 10M, distant, or
1G continuations. The theorem remains valid as representation evidence; its
extra capacity is empirically subeconomic on the target codec.

Decision receipt:
`results/fxcm_budget_preserving_capacity_v1/opening_1m_decision.json`

## 2026-07-29: JANUS-QUOTIENT Q0 paid context-state claim

Candidate: `janus_paid_context_quotient_q0_v1`

The terminal JANUS recurrent witness established 1,474.2 B/M gross fixed-corpus
residual gain at exact 10M, but its 183,439-byte package allowance left only
1,290.761 B/M. The authorized materially different successor is one compact
fixed-population context quotient rather than a recurrent architecture sweep.

Q0 maps the exact endpoint P1, current WRT byte-tree node, and four previously
decoded WRT bytes into exactly 65,536 states. Each state selects one of seven
frozen rational odds corrections. The canonical table, a 24,576-byte native
decoder allowance, and 64 framing bytes are charged. Two complete fits, full
candidate range decode, shifted-table specificity, parent payload identity,
and the existing WRT/raw inverse binding are mandatory.

Authorization requires at least 3,000 B/M gross, 2,100 B/M after package
allowance, a strict win over the shifted-table null, and a complete package no
larger than 128 KiB. Failure retires the exact quotient without a state-count,
hash, suffix-depth, or correction-alphabet sweep.

Plan:
`docs/janus_paid_context_quotient_plan.md`

## 2026-07-29: JANUS-QUOTIENT Q0 is terminal negative

The exact canonical-10M paid quotient completed successfully. Parent payload
identity, both independent model fits, adjusted P1 identity, candidate payload
identity, both candidate decodes, shifted-control decode, and the WRT/raw
inverse binding all passed.

The 65,536-state table saved 2,862 exact payload bytes: 286.2 B/M gross. Its
canonical model compressed to 10,086 bytes; after the frozen 24,576-byte
decoder allowance and 64 framing bytes, projected gain was 251.474 B/M. The
candidate strongly beat the shifted-table null, so its small signal is real,
but it missed the 3,000 gross and 2,100 net B/M gates by approximately an order
of magnitude.

Decision: terminally reject this exact paid quotient. Do not sweep state count,
hash, suffix depth, confidence bins, or correction alphabet. This result,
together with the recurrent JANUS result, shows that fixed-population access
alone does not rescue either tested residual family at target scale.

Receipt:
`results/janus_paid_context_quotient_10m_q0_v1/decision.json`

## 2026-07-29: JANUS recurrent + quotient joint replay claimed

Candidate: `janus_recurrent_quotient_joint_10m_v1`

The two paid fixed-population models were independently positive but terminally
subscale. Their separate package-adjusted rates cannot be added; nevertheless,
their arithmetic sum narrowly crosses the nominal design debt. One frozen
interaction replay is therefore authorized.

The existing JANUS model is refit only to export its deterministic adjusted P1
trajectory. The unchanged 65,536-state quotient is then fit against that
trajectory, and one exact composed payload is decoded. Both packages are
charged once. Promotion requires 3,000 B/M gross, 2,100 B/M after both package
allowances, a strict residual gain over JANUS alone, and a strict win over the
shifted quotient. Failure is terminal and authorizes no architecture, state,
blend, or interaction-order sweep.

Plan:
`docs/janus_recurrent_quotient_joint_plan.md`

## 2026-07-29: JANUS recurrent + quotient joint replay is terminal fragile

The deterministic JANUS export exactly reproduced the terminal model, adjusted
P1, and payload hashes. The frozen quotient was then refit on that P1 stream.
Parent payload identity, quotient A/B model/P1/payload identity, complete
candidate decodes, shifted-control decode, and WRT/raw inverse binding passed.

The quotient saved 2,911 bytes beyond JANUS. The complete joint payload saved
17,653 bytes versus the original parent, or 1,765.3 B/M gross. Charging the
183,439-byte JANUS package and 34,709-byte quotient package leaves 1,547.152
B/M.

This is a real, nearly additive signal. A naive linear application to the
current 109,524,268 planning forecast would cross the 108,000,000 design target
by only 22,884 bytes. That is not a certificate: the baseline is not an exact
full-corpus score, opening-10M slopes are not reliable, mature transfer is
unproved, and the dense recurrent path has no CPU runtime qualification.

Decision: reject the composition under the frozen 3,000 gross and 2,100 net
B/M safety gates. Do not sweep blend, interaction order, state count, or
architecture, and do not promote this fragile projection to score credit.

Joint receipt:
`results/janus_recurrent_quotient_joint_10m_v1/joint/decision.json`

## 2026-08-01: 108 MB control-plane and proposal reconciliation

The generated operator view had diverged from the canonical source-bound
frontier after the target revision. `docs/hutter_frontier.json` selected
`endpoint428_gate_dot_fuse_output_update_loop_v1` at a forecast-only
`109,389,323` bytes, while the operational receipt still exposed older
`109,524,268` and `110,181,114` planning values. The certificate generator now
imports the explicit canonical frontier selection and recomputes its signed
distance against the active `108,000,000` design target. The status receipt
also stops treating an inactive candidate metadata row as a live gate.

The adaptive queue contained one persisted `running` receipt with no live
owner and 76 pending gates whose candidates were already retired in the
canonical inventory. The runner now persists worker PIDs, distinguishes live
and orphaned running receipts, and supports explicit cancellation of an
orphaned running receipt. The orphan and all 76 retired-candidate pending jobs
were cancelled with durable reasons. Twenty-eight pending gates whose current
inventory status remains `active` or `candidate` were preserved; none was run
as part of this reconciliation.

Four stale claimed proposals were terminalized:

- `endpoint428_recurrent_fanin64_v1`: its 18-byte 250K gain did not clear the
  declared 8% runtime gate, and the no-fill successor regressed.
- `endpoint428_exact_source_runtime_stack_v1`: the exact cell-major successor
  regressed matched runtime by 1.94%; the emhash-only result is a distinct
  mechanism and does not rescue this patch stack.
- `seal2_route_a_paid_predictor_partition_v1`: the register records terminal
  `+7`- and `+6`-byte gross page oracles with negative paid forms. Its named
  decision artifacts are missing in this checkout, so the rejection preserves
  that provenance gap explicitly and gives zero credit.
- `wrt_link_surface_cmem_shadow_v1`: both external inputs are absent on this
  host and its declared 200,000-byte expectation cannot independently cover
  the 1,389,323-byte debt. It is parked as rejected pending a new target-bearing
  composition with restored hash-bound inputs.

Route C remains claimed but blocked on an independently reproducible exact
full-1G teacher below `108,000,000` with complete eligibility accounting.
AF-1 remains a proposed memory substrate; no heavy AF-1 gate is authorized by
this reconciliation because it has no declared score leverage.

The Atlas-Clockwork commitment now resolves adaptive proposal artifacts across
lifecycle state, binds the consistent `109,389,323` forecast, and verifies as
`VALID_UNBOUND`. Candidate distribution remains forbidden.

## 2026-08-01: Seal-2 Route D timestamp-envelope Q0 is terminal negative

Candidate: `seal2_route_d_timestamp_microblock_rank_q0_v1`

The exact Q0 selected one named structural class: the 20-byte MediaWiki
revision timestamp followed by its 12-byte closing tag. Each object used the
previous chronologically decoded timestamp envelope as its prototype. The
frozen 1M population contained 171 complete timestamp pages and 170 coded
records, split into development pages, page-index-mod-5 holdout pages, and a
chronological offset beginning at raw byte 800,000. Widths 8, 16, and 32 bytes
were evaluated; development selected 8 bytes.

Exact direct rank/unrank, explicit byte edits, matched causal arithmetic
coding, deterministic nested parity rows, bounded first-hit reconstruction,
and literal fallback all roundtripped. The receipt reproduced byte-for-byte on
an independent second execution.

The selected 8-byte aggregate was decisively negative:

```text
matched causal control:                 2,098 bits
parity plus mode/depth/fallback:         3,902 bits
gross delta versus causal:             -1,804 bits
direct-rank Elias-delta payload:         2,332 bits
parity/direct payload ratio:              1.673
development bounded-search success:       0.816
holdout bounded-search success:           0.8387
offset bounded-search success:             1.000
compressed candidate plus gate source: 8,976 bytes
paid rate after source:             -9,359.602 B/M
```

Every split lost gross bytes to the causal control. The 128- and 256-bit forms
had only 13.6%/16.1%/7.1% and 10.4%/9.7%/0% bounded success across
development/holdout/offset, with true-rank expansion counts growing far beyond
the fixed 65,536 budget.

Decision: retire this timestamp class and reject the unchanged general Route D
proposal. Do not run a width, matrix, parity-depth, or expansion ladder. A
successor must be a new proposal naming a materially different decoder-visible
structural class and prototype. Score and Seal credit remain zero.

Evidence:

- `programs/seal2_route_d_timestamp_microblock_rank_q0_v1/`
- `tools/route_d_timestamp_microblock_gate.py`
- `results/seal2_route_d_timestamp_microblock_rank_q0_v1/decision.json`
- `run_logs/adaptive/20260801T181822Z_366e35e4df.log`

## 2026-08-01: Seal-2 Route E state-preserving prototype bypass claimed

Candidate: `seal2_route_e_state_preserving_prototype_bypass_q0_v1`

Route E introduces a new coding operation rather than another endpoint,
calibration, table, or width sweep. Selected exact WRT spans are reconstructed
from one earlier complete page and omitted from the arithmetic truth stream,
while every reconstructed bit remains part of the parent predictor update
trajectory. Q0 uses the exact endpoint428 P1 trace to price the literal stream;
native predictor-state identity remains a later proof obligation.

This is materially different from the terminal explicit-copy screen. That
screen paid independent exact-copy positions and found only 219.52 optimistic
bytes before the omitted position stream. Route E amortizes one prior-page
prototype across multiple separated copy intervals with literal holes, pays a
complete finite command stream, constructs the actual residual arithmetic
payload, and compares against exact-repeat and rotated-prototype controls.

The frozen opening-1M gate requires at least 3,000 B/M gross and 2,100 B/M
after full-corpus source amortization, exact parent replay, command/WRT/raw
roundtrips, byte-identical archive reconstruction, a strict win over E1 and
ER, and positive exact selection and sealed-confirmation signs. Any miss
retires the unchanged single-prototype prior-page mechanism without parameter
or prototype-count sweeps.

Plan and schema:

- `docs/seal2_route_e_state_preserving_prototype_bypass_plan.md`
- `docs/seal2_route_e_state_preserving_prototype_bypass_decision.schema.json`

## 2026-08-01: Seal-2 Route E single-prototype bypass is terminal negative

Candidate: `seal2_route_e_state_preserving_prototype_bypass_q0_v1`

The frozen exact opening-1M Q0 searched all 171 complete chronological pages
and every one of the 14,535 legal earlier-page prototype pairs. For each pair,
it enumerated exact WRT matches with a reversed suffix automaton, allowed every
copy-prefix length of at least eight bytes, and solved the alternating
COPY/LITERAL selection by exact dynamic programming against integer parent
qbits and canonical ULEB command bytes.

No page retained a positive plan after paying its target-page framing,
prototype reference, and copy commands. E1, E2, and rotated ER therefore all
fell back to a four-byte empty command stream and the complete parent literal
payload:

```text
parent E0 archive:                     173,896 bytes
E1 exact-repeat archive:               173,911 bytes
E2 aligned-prototype archive:          173,911 bytes
ER rotated-prototype archive:          173,911 bytes
E2 gross gain:                             -15 B/M
measured source allowance:              12,969 bytes
E2 projected net after source:          -27.969 B/M
active E2 pages:                              0
E2 copy commands:                            0
```

The negative result is not an infrastructure failure. E0 reproduced the bound
173,859-byte parent arithmetic payload exactly. Command streams roundtripped,
every archive reproduced byte-for-byte, E2 reconstructed the exact WRT store,
and the official inverse returned the exact 1,000,000-byte raw input and hash.

Decision: retire unchanged single-prior-page state-preserving bypass. Do not
sweep minimum copy length, prototype count, distance windows, or integer codes.
A materially different successor must amortize transmitted many-use grammar
rules across pages and must provide a paid upper-bound certificate before a
full implementation. Score and forecast credit remain zero; the canonical
forecast remains 109,389,323 bytes.

Evidence:

- `results/seal2_route_e_state_preserving_prototype_bypass_q0_v1/decision.json`
- `run_logs/adaptive/20260801T205411Z_8a371e48f7.log`
- `docs/seal2_route_e_state_preserving_prototype_bypass_plan.md`

## 2026-08-01: MOBIUS-2 architecture recorded, unmeasured and zero-credit

MOBIUS-2 is a two-lane successor architecture, not a score claim. LOGOS is a
self-describing many-use grammar whose paid `GEN`, `COPY`, `PATCH`, and
`LITERAL` operations reconstruct exact WRT bytes while preserving Gamma's
truth-update trajectory. NOEMA is a proposed compact, recursively
weight-shared, dyadic residual-memory predictor for the literal remainder and
eventual LOGOS controls. Frontier models may propose structures offline, but
the final decoder may contain only counted deterministic code and data.

The lanes are intentionally separated. LOGOS must beat surface-only, shuffled,
and forced-literal controls after ontology, slot, command, framing, and source
costs. NOEMA must beat a matched-package flat recurrent control, page-shifted
states, and memory-disabled ablation with exact repeated hashes. Neither lane
is allowed to borrow projected credit from the other. One actual 10M joint
archive is authorized only after both isolated Q0 gates pass.

Route E is a direct constraint, not supporting score evidence: its complete
single-page-prototype search selected zero paying pages. LOGOS must therefore
show many-use rule amortization rather than reopen prototype-width or command-
coding sweeps. NOEMA likewise needs a hierarchy-specific headroom certificate
against the terminal flat recurrent/residual neighborhoods.

The initial incremental package ceiling is 393,216 bytes. Covering that ceiling
and the current 1,389,323-byte forecast debt requires at least 1,782,539 gross
full-corpus bytes. The per-lane gates remain 3,000 B/M gross and 2,100 B/M net.

Decision: record and park both lanes at zero credit. Before either becomes an
adaptive proposal, freeze its exact construction algorithm, inputs, package
measurement, controls, and no-sweep kill condition. No MOBIUS tools, candidates,
or queue jobs are authorized by this architecture entry.

Architecture:

- `docs/mobius2_architecture.md`

## 2026-08-01: MOBIUS-2 LOGOS ordered-template surface ceiling claimed

Candidate: `mobius2_logos_surface_grammar_ceiling_q0_v1`

This prerequisite tests one exact many-use rule family before broader semantic
ontology work. It reuses the recorded WikiIR ordered-template parser, but does
not serialize an alternate raw IR or feed commands through LZMA. Fixed raw
segments and value-hole boundaries are mapped to complete WRT emission groups;
only identical tuples of exact WRT fixed segments share a rule.

The first 60 percent of complete chronological pages determine rule keys and
definitions. A key needs at least two development occurrences. The finite
control stream transmits each WRT rule definition, absolute invocation start,
rule ID, and literal-hole WRT lengths. Generated fixed segments are omitted
from an actual terminated residual range payload, while later literal bytes
retain their receipt-bound parent P1 rows. Native model-state hashing remains
a later obligation.

The gate reports both an exact uncharged residual-payload ceiling over every
development-repeated rule and a paid S1 archive. SL transmits the identical
rules and invocations but forces every byte literal, isolating generated-span
value from descriptor freedom. Parent, command, WRT, raw inverse, and second-
archive identities are mandatory.

Promotion requires at least 3,000 B/M for both the uncharged exact ceiling and
paid gross archive, at least 2,100 B/M after measured source, an S1 win over SL,
and positive development, selection, and sealed-confirmation signs. A ceiling
miss retires ordered-template surface LOGOS without occurrence, hole, nesting,
rule-width, or integer-code sweeps. It does not retire untested semantic LOGOS
or NOEMA.

Plan and schema:

- `docs/mobius2_logos_surface_grammar_ceiling_plan.md`
- `docs/mobius2_logos_surface_grammar_ceiling_decision.schema.json`

## 2026-08-01: MOBIUS-2 LOGOS ordered-template surface ceiling retired

The exact opening-1M gate mapped 443 parameterized ordered templates onto the
WRT stream. Development exposed 18 exact WRT skeleton keys with at least two
occurrences, producing 201 legal candidate invocations and 2,209 potentially
generated WRT bytes.

The uncharged U0 oracle omitted every eligible fixed span, charged no rule,
invocation, framing, or source bytes, and built an actual terminated residual
arithmetic payload. It saved only 291 bytes, or 291 B/M, against the exact
173,859-byte parent payload. This is below one tenth of the frozen 3,000 B/M
ceiling gate. The parent qbit attribution for those spans was 290.019 bytes,
which independently agrees with the constructed-payload ceiling.

Paid MDL selection retained zero rules and zero invocations. S1 totaled
173,923 bytes versus the 173,896-byte parent archive: -27 B/M gross and
-42.496 B/M after the measured 15,496-byte source allowance. With no selected
rules, S1 could not beat the identical-descriptor forced-literal SL control,
and none of the chronological split signs was positive.

The first adaptive attempt failed before measurement because the inherited
WikiIR representation stores its first value hole after two adjacent fixed
segments. The WRT mapper was corrected to that recorded ordering and the same
frozen candidate was retried as an infrastructure retry. The successful run
then passed exact parent-payload identity, finite control roundtrip, WRT
reconstruction, official WRT-to-raw inverse, raw hash, and byte-identical
second-archive controls.

Decision: retire unchanged ordered-template surface LOGOS, including rescue
sweeps over occurrence thresholds, hole counts, nesting, rule widths, integer
codes, and rule-definition compression. This result does not test or retire a
materially broader semantic-rule information source or NOEMA. Both remain
zero-credit. The 109,389,323-byte forecast is unchanged.

Evidence:

- `results/mobius2_logos_surface_grammar_ceiling_q0_v1/decision.json`
- `run_logs/adaptive/20260801T211842Z_1ac4e76b26.log`
- `operations/adaptive/exclusions/mobius2_logos_ordered_template_surface_grammar_opening_1m_v1.json`

## 2026-08-01: MOBIUS-2 LOGOS cross-page lexical-frame ceiling claimed

Candidate: `mobius2_logos_lexical_frame_ceiling_q0_v1`

Route E explicitly left transmitted many-use grammar bypass unsettled, while
the first LOGOS gate retired only exact ordered MediaWiki-template shells. The
next information certificate therefore moves inside page text and asks whether
parameterized prose frames have enough endpoint428 codelength to matter before
any command format is built.

The frozen rule consists of two exact five-emission-group lexical anchors
around one literal hole of one through twelve complete WRT emission groups.
Both anchors must be prose-like ASCII surface spans inside a page text element.
A rule exists only when development contains two distinct hole realizations on
at least two distinct pages. Selection and sealed-confirmation pages cannot
create rules.

Q0 is deliberately an upper bound. It uses exact weighted interval scheduling
to choose nonoverlapping frame envelopes, omits anchor truth from an actual
terminated residual payload, and supplies the rule plan out of band at zero
cost. L1 is a matched zero-hole contiguous lexical-phrase ceiling. LR rotates
right anchors among frozen rules before finding exact occurrences. Every
control must decode the exact WRT stream, and L2 must pass the official raw
inverse.

Promotion requires at least 3,000 B/M exact L2 gain, positive development,
selection, and sealed-confirmation signs, strict wins over L1 and LR, and exact
parent, residual-decode, raw, and determinism proofs. A miss retires this exact
anchor/hole construction without width, threshold, alphabet, or code sweeps.
It does not retire a materially broader semantic ontology or NOEMA.

Plan and schema:

- `docs/mobius2_logos_lexical_frame_ceiling_plan.md`
- `docs/mobius2_logos_lexical_frame_ceiling_decision.schema.json`

## 2026-08-01: MOBIUS-2 LOGOS cross-page lexical-frame ceiling retired

The exact opening-1M certificate scanned 420,533 development frame rows and
found 156 rule keys that occurred on at least two development pages with at
least two distinct literal-hole realizations. Across all splits, those rules
matched 837 times. Exact maximum-parent-qbit interval scheduling retained 584
nonoverlapping invocations, covering 5,975 generated WRT anchor bytes.

L2 is a real, transferable information source. Its actual terminated residual
payload saved 1,064 bytes. The matched zero-hole contiguous control saved only
55 bytes, and the cyclically rotated-right-anchor control saved 59 bytes.
Development, selection, and sealed-confirmation L2 gains were respectively
620, 56, and 390 bytes. All signs were positive and L2 decisively beat both
specificity controls.

The magnitude is nevertheless terminal. The frozen gate required 3,000 B/M,
and 1,064 B/M is an optimistic upper bound with rule definitions, invocation
positions, hole lengths, framing, decoder source, and state-integration source
all charged as zero. A finite grammar can only reduce the net value. Building
or tuning that grammar cannot close the current target debt under the frozen
research margin.

Parent payload identity, every residual arithmetic decode, duplicate payload
identity, exact WRT reconstruction, the official WRT-to-raw inverse, and the
raw hash all passed. This is a scientific gate miss, not an infrastructure
failure.

Decision: retire the exact five-emission-group anchor, one-to-twelve-group
hole, two-development-page lexical-frame construction and its width, gap,
threshold, alphabet, weighting, and integer-code rescue sweeps. Preserve its
1,064 B/M result as positive component evidence only. A broader semantic
ontology must expose non-lexical equivalence and first clear the same 3,000 B/M
zero-cost ceiling. NOEMA remains an independent unsettled lane. Score and
forecast credit remain zero; the canonical forecast remains 109,389,323 bytes.

Evidence:

- `results/mobius2_logos_lexical_frame_ceiling_q0_v1/decision.json`
- `run_logs/adaptive/20260801T223213Z_993e105544.log`
- `operations/adaptive/exclusions/mobius2_logos_cross_page_lexical_frame_opening_1m_v1.json`

## 2026-08-01: MOBIUS-2 NOEMA binary-carry hierarchy headroom claimed

Candidate: `mobius2_noema_binary_carry_headroom_qh0_v1`

The prerequisite NOEMA experiment asks whether a recursively summarized causal
state contains endpoint428 residual information absent from the terminal flat
recurrent and direct-lag neighborhoods. It is deliberately not a full NOEMA
implementation or score claim.

Every complete page contributes complete 128-WRT-byte patches. Development,
selection, and sealed confirmation are the first 60%, next 20%, and final 20%
of complete pages by chronological page count. Weights train only on
development. The minimum exact quantized selection payload chooses one of
eight frozen checkpoints, with earlier-epoch ties. Sealed confirmation is then
read once.

N1 is one 48-wide flat GRU state. N2/NM represents the decoded patch prefix as
a binary carry tree: each byte creates a leaf, equal-sized adjacent summaries
merge through one shared GRUCell, and the occupied summaries form the next-byte
state. Both controls have exactly 37,623 parameters and identical tensor
shapes. Surprise memory is disabled. NS cyclically rotates N2 summary states
across pages within each split. Unlike the retired direct-lag model, N2 never
queries fixed lag coordinates.

Promotion requires positive development and selection gains, at least 3,000
gross and 2,100 package-adjusted B/M on sealed pages, strict sealed wins over
N1 and NS, a matched package no larger than 131,072 bytes, duplicate model/P1/
payload/history identity, exact parent replay and arithmetic decode, exact WRT
reconstruction, and official raw inversion. A pass authorizes one frozen
distant reset-population replay only. A miss retires the exact patch geometry,
cell, widths, optimizer, epoch selection, aggregation, quantization, and null
without rescue sweeps or surprise-memory rescue.

The frozen candidate passed pre-run syntax, schema, normal-ROCm matrix compute,
matched parameter-count, finite forward, and backward probes. It retains zero
score and forecast credit pending the exact adaptive receipt.

The first adaptive attempt stopped before its first optimizer step because the
harness passed uint8 WRT values directly to PyTorch's embedding operation. The
frozen model was not measured. The harness now converts those same values to
integer indices at the device boundary; this is an infrastructure retry with no
architecture, population, training, selection, accounting, or gate change.

Plan and schema:

- `docs/mobius2_noema_binary_carry_headroom_plan.md`
- `docs/mobius2_noema_binary_carry_headroom_decision.schema.json`

## 2026-08-01: MOBIUS-2 NOEMA binary-carry hierarchy is terminal negative

The infrastructure retry completed the exact opening-1M QH0. N1 selected epoch
2 and N2 selected epoch 1 using independently terminated quantized selection
payloads. Both independent fits produced identical training histories, selected
epochs, canonical model blobs, complete adjusted P1 streams, and payloads.

N2 gained 112 development bytes, but lost 35 selection bytes and 135 sealed
bytes. The sealed rate is -261.397 B/M gross and -362.677 B/M after the matched
101,280-byte package allowance. Its complete payload loses 56 bytes to the
173,859-byte parent. The matched flat N1 gains 98 complete-stream bytes and is
65 bytes better than N2 on sealed confirmation, so the hierarchy fails both
transfer and hierarchy-specific attribution. Page-rotated NS loses 302 complete
bytes; N2 beats that nonconstructive specificity diagnostic, but this cannot
rescue its negative magnitude or loss to N1.

All identity gates passed: receipt-bound parent payload bytes, both repeated
fits, complete arithmetic decode, exact WRT reconstruction, byte-identical
second payload, official inverse return code, and the exact 1,000,000-byte raw
hash. The package remains below its 131,072-byte ceiling. This is a valid
scientific rejection rather than an infrastructure failure.

Decision: retire the exact 128-byte reset, seven-level equal-span binary-carry
topology, 48-wide shared cell, training/checkpoint schedule, aggregation,
per-tensor int8 form, and associated rescue sweeps. Do not add surprise memory
to rescue the miss and do not run the distant replay.

The strengthened successor contract is now recorded in
`docs/mobius2_noema_causal_replay_contract.md`. It requires explicit frontier
and merge-count invariants, checkpoint-owned state replay, two-part checkpoint
selection, a causal earlier-page misalignment control, parsing the measured
model from its checksummed canonical blob, expanded ROCm provenance, and two-
layer repeated identity. QH0 predates parts of that contract, but its decisive
negative selection, sealed magnitude, and loss to N1 do not depend on the
future-derived NS or an uncharged serializer advantage.

Broader semantic LOGOS and a hierarchy with a materially different semantic
boundary information source remain unsettled and zero-credit. The forecast
remains 109,389,323 bytes and the exact full-1G score remains unknown.

Evidence:

- `results/mobius2_noema_binary_carry_headroom_qh0_v1/decision.json`
- `run_logs/adaptive/20260801T225624Z_3987dcc6e8.log`
- `docs/mobius2_noema_causal_replay_contract.md`
