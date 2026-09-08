# Opcode field repair

This experiment repairs one observed mismatch in the retained standalone
`opcode_typed_anchor_bitmix_v1`: its frontend replaces XML tags with opcodes,
but its predictor still tests for the original tag spellings. Six field routes
therefore remain inactive in the authenticated synthetic diagnostic.

The [frozen experiment](../operations/adaptive/experiments/opcode_field_repair250k_q0_v1.json)
owns the hypothesis, populations, controls, budgets and selection rule. It is
claimed by `root_explore`. Historical bitmix receipts are comparison targets;
the new legacy revision authenticates current source without retroactively
binding those receipts.

P retains the parent. K computes an opcode recognizer without changing the
field supplied to the predictor. D supplies the recognizer's field. Only this
coordinate changes: byte history, other route variables, arithmetic coding,
model updates and copy-search laws retain their existing definitions.

An opening opcode sets the field only after both bytes have been decoded.
A closing opcode clears it. An escaped zero is a literal and cannot start a
second opcode. Every copied byte passes through the same update procedure as
a literal byte, including overlapping copies and pairs crossing copy edges.
The separate encoder prefix-cost pass uses the same arm's field rule.

The decoder receives the existing arithmetic archive, the counted source and
opcode table, and the declared arm. Its one-byte arm value and the actual CLI
option syntax are inventoried separately. It reconstructs modeled bytes and
then applies the existing opcode inverse. Given equal initial state, each
decoded event produces the same adaptive update and next field on both sides;
the comparison checks this induction with prediction and state evidence.
Encoder lookahead and search tables are not decoder inputs.

The [development receipt](../operations/provenance/opcode_field_repair_terminal_20260908.json)
records 67,959-byte P/K archives and a 67,658-byte D archive: a 301-byte saving.
The unchanged parent was reproduced, P/K identity held, and independent inverses,
raw-input repeats and shared-state checks passed. All inputs below are the same
opening 250,000 original bytes; retained baselines were authenticated rather than
rerun. Their frontend and dependency differences remain explicit in the
[baseline inventory](../operations/provenance/small_input_frontier_baselines_20260908.json).

| Codec | Complete development archive bytes | Evidence scope |
| --- | ---: | --- |
| Framed Deflate | 89,041 | Retained exact inverse and repeat |
| Bitmix parent / bookkeeping | 67,959 | Fresh P/K identity, inverse and repeat |
| Opcode field repair | 67,658 | Fresh inverse, repeat and state witnesses |
| Source-bound FX2 | 33,429 | Retained cold-slice inverse and repeat; supplied trained assets |

These are archive sizes, not prize scores. The candidate's 15,403 uncompressed
source bytes exceed the retained parent's 4,841 by 10,562 bytes. Complete package
economics remain unknown; the archive benefit alone does not pay that raw source
increase. Python and runtime licensing,
accepted complete-package accounting and cross-host floating-point lookup
initialization remain qualification obligations.

Development uses the previously examined opening 250KB. One fixed mutation
must improve its own parent before selection on a disjoint 250KB validation
population; the separately reserved 1MB confirmation population stays outside
design and tuning. The 99,000,000-byte complete objective remains unproved.

The [separate validation receipt](../operations/provenance/opcode_field_validation_terminal_20260908.json)
records P/K 71,788 and D 71,717 bytes, a 71-byte archive gain. All ten phases,
inverses, repeats and shared-state checks pass. The unchanged codec is selected
for the reserved 1MB confirmation; neither sample establishes package savings.
Deflate and FX2 are now measured on the same reserved validation slice below.
The retained field counters show 217,459 of 230,968 modeled bytes in nonzero
fields on development, and 236,452 of 241,793 on validation. Higher overall
coverage accompanies the smaller validation saving. These are opcode-stream
coverage counts, not improved raw bytes or per-field attribution of archive gain.
The [matched comparator contract](../operations/adaptive/experiments/matched_frontier_reserved_q0_v1.json)
binds both reserved populations to the unchanged Deflate CLI and cached FX2
executable. Its [synthetic tests](../operations/evidence/20260908_matched_frontier_unit.json)
cover exact Deflate replay, native header/vocabulary checks, and explicit model
inventory. Its separately published CPU2 corpus job has now closed all fourteen
phases with exact inverses, deterministic repeats and no resource violations.

The [reserved 1MB confirmation](../operations/provenance/opcode_field_confirmation_terminal_20260908.json)
passes all ten phases and the resource guard, with P/K 257,369 bytes and D
255,828: a 1,541-byte archive saving. The codec was unchanged across all stages.

| Stage | Parent / bookkeeping | Treatment | Archive saving |
| --- | ---: | ---: | ---: |
| Development 250KB | 67,959 | 67,658 | 301 |
| Separate validation 250KB | 71,788 | 71,717 | 71 |
| Reserved confirmation 1MB | 257,369 | 255,828 | 1,541 |

All inverses, repeats and shared-state checks pass. These improvements retain
their individual populations. Larger gates remain held while complete package
cost is assessed. Reducing source cost
requires an executable release that preserves the confirmed archives, not merely
removing required files from its inventory.

The [matched comparator receipt](../operations/provenance/matched_frontier_reserved_terminal_20260908.json)
authenticates all retained output files and rechecks the native runtime libraries
after closure. No codec was changed for this comparison.

| Population | Framed Deflate | Bitmix parent / K | Field repair D | Source-bound FX2 |
| --- | ---: | ---: | ---: | ---: |
| Opening 250KB development | 89,041 | 67,959 | 67,658 | 33,429 |
| Separate 250KB validation | 94,674 | 71,788 | 71,717 | 35,464 |
| Reserved 1MB confirmation | 360,475 | 257,369 | 255,828 | 131,238 |

Entries are complete archive bytes for identical original bytes within each row.
Opening baselines are retained measurements; both reserved comparator rows are
fresh. The Deflate wrapper retains 65,536-byte frames. FX2 uses its explicit
cold-slice adapter, trained weights and dictionary; this does not reproduce its
published full-corpus pipeline, establish unseen-model generalization, or confer
its compression performance on Gamma's independent codec.

| Comparator phase | Validation wall seconds | Confirmation wall seconds |
| --- | ---: | ---: |
| Deflate encode / decode / repeat | 0.066 / 0.066 / 0.066 | 0.116 / 0.066 / 0.116 |
| FX2 encode / decode / repeat | 38.134 / 38.136 / 39.137 | 128.004 / 124.698 / 124.202 |

The receipt retains CPU measurements separately, including preprocessing. These
are shared-host diagnostic timings. The closed comparator's aggregate cgroup
peak is 5,999,730,688 bytes; FX2 per-phase memory maxima are not measured.
The 6,338,269-byte content-deduplicated inventory includes source, harness and
native assets. Its 3,826,496 runtime-asset bytes include the model and dictionary.
Host shared libraries are separately inventoried. None of these subtotals is a
complete qualified submission package.

The fixed field repair earns further implementation work through its confirmed
parent-relative gain. Its next package question is whether a separately bound
standalone release can implement the same field rule with lower source cost and
preserve the existing archives. This comparison supplies no authority for a
larger corpus run and no projection to the 99,000,000-byte target.

On September 8 the engineering objective moved to
[90M v3](../contracts/research/v3/objective-contract.json); the experiments above
retain their original 99M bindings. The separately owned
[compact implementation](../operations/adaptive/experiments/opcode_field_compact_v1.json)
packs the same predictor and field update with bounded canonical decoding into
two local files totaling 5,746 bytes. Its
[seven synthetic tests and retained fixture](../operations/evidence/20260908_opcode_field_compact_unit.json)
pass exact archive parity, independent inversion, deterministic repeats and
complete common-state witness comparisons. The retained 65-byte fixture produces
a 27-byte archive; this is correctness evidence only.

Local source shrinks by 9,657 bytes from the observed implementation and remains
905 bytes above the original parent. These are source subtotals, not a complete
package result: invocation bytes, runtime and the chosen accounting multiplicity
must still be resolved. The compact codec now passes the corpus parity gate.
Its [parity runner](../tools/opcode_field_compact_gate_v1.py) passes
[seven synthetic runner tests](../operations/evidence/20260908_opcode_field_compact_runner_unit.json).
The sealed CPU2 job `20260908T154100Z_6b9653a04d` started after source publication
at `fbe4b33c4` and fresh admission. Twelve phases compare retained archives and shared state against
fresh unobserved encode, observed encode, independent decode and raw repeat on
each existing population. Limits are 12GiB memory, zero swap, 2GiB scratch and
12,000 elapsed seconds. Historical confirmation inputs may prove exact
implementation parity; they must not be described as fresh model confirmation.
The [terminal receipt](../operations/provenance/opcode_field_compact_terminal_20260908.json)
closes all twelve phases with archives of 67,658 / 71,717 / 255,828 bytes,
matching the three retained D populations. Independent reconstruction, repeats,
complete shared witnesses and frozen input identities pass. Peak cgroup memory
is 1,308,880,896 bytes; every guard is false and cleanup completes. The validated
reflection retains this implementation and selects a separate prediction mutation.

The [source ZIP diagnostic](../operations/provenance/opcode_field_source_zip_cost_20260908.json)
uses the existing deterministic ZIP builder with one fixed Deflate level9 policy.
Parent, observed field codec and compact source components occupy 5,041, 8,614
and 5,815 bytes respectively. Every source ZIP repeats exactly, and extracted
sources pass nine independent synthetic encode/decode/repeat phases. No corpus
is read by this packaging diagnostic.

The compact source ZIP adds 774 bytes over the parent. If the identical
compressor/decoder source package is counted twice under the separate-archive
form, that adds 1,548 bytes: seven more than the historical 1MB archive saving.
CLI/build entry, required options, license closure and runtime costs remain
unresolved. This arithmetic does not establish a package score or authorize a
larger gate; the subsequently closed compact parity adds no archive savings.

The [synthetic wiki-state probe](../results/opcode_wiki_state_diagnostic_20260908/attempt01/receipt.json)
inspects the unchanged source on eleven predefined strings. Eight expose missed
wiki coordinates after opcode substitution: links, categories, images, template
names/arguments and reference names. Three controls retain their expected state,
including the repaired XML field. All frontend inverses are exact. This proves
the demonstrated state mismatch, not its corpus frequency or compression cost.
The compact gate is now closed and reflected. The next bounded prediction
question is whether exposing a decoder-reconstructed wiki slot pays
against an otherwise unchanged parent and disabled bookkeeping control. Preserve
the byte histories and existing model/copy laws; do not combine another feature.

`root_explore` has implemented [opcode_wiki_slot_v1](../operations/adaptive/experiments/opcode_wiki_slot_v1.json).
It expands completed opcode pairs into a bounded raw-state detector and exposes
only its `slot`; the repaired XML field and all other context coordinates remain
the parent values. P uses the unchanged compact namespace, K runs unused slot
bookkeeping, and D uses the slot. Literal and copy updates follow the same path.
The external audit binds the complete raw side state, slot occupancy, changed
slot bytes by literal/raw-copy/chain-copy mode, and all existing shared witnesses.

[Eleven tests](../operations/evidence/20260908_opcode_wiki_slot_unit.json) pass.
An independently retained ten-phase synthetic CLI comparison produces P/K 43
bytes and D 44, with exact reconstruction, repeats and P/K projection identity.
The first CLI tests caught binary JSON audit values and relative artifact paths;
both were fixed before sealing. A source-closure preflight also rejected an
incomplete dependency list before the sealed plan bound the missing imports.
No corpus ran during these corrections. Required local source is 6,350 bytes,
604 above the compact parent; the complete package remains unqualified.

Job `20260908T162205Z_46ebdbaee4` started after publication at `f12a45666` and
[fresh admission](../results/opcode_wiki_slot_admission_20260908.json), including
31 exact published bindings and a 32GiB host headroom reserve. Its opening250KB
comparison has ten phases, CPU2/one thread, 4GiB
aggregate memory, zero swap, 1GiB scratch and a 2,400-second elapsed stop.
Each phase has 2GiB address-space, 180 CPU-second and 240 wall-second limits.
Promotion requires a strictly smaller archive and all controls/inverses/witnesses;
package cost and fresh confirmation remain separate subsequent decisions.

The [fixed source-ZIP comparison](../results/opcode_wiki_slot_source_zip_20260908/attempt01/cost.json)
measures parent 5,815 / treatment 6,092 bytes, a 277-byte increase. Separate
extracted copies pass six synthetic encode/decode/repeat phases. The conditional
twice-counted program form adds 554 source bytes; the corpus run must supply its
own archive difference. Runtime, options, licensing and final packaging remain
unresolved. No archive gain is inferred from synthetic reconstruction.
