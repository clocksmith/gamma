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
Deflate and FX2 have not yet been measured on this reserved validation slice.
