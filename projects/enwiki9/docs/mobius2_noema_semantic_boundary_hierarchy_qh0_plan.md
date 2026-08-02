# MOBIUS-2 NOEMA semantic-boundary hierarchy QH0

Date: 2026-08-02

Proposal: `mobius2_noema_semantic_boundary_hierarchy_v1`

Candidate: `mobius2_noema_semantic_boundary_hierarchy_qh0_v1`

## Claim boundary

This zero-credit headroom gate asks whether decoder-visible linguistic and
structural boundaries expose residual information absent from the exact
JANUS-plus-quotient trajectory. It is not a dyadic decoder, native Gamma
integration, distant replay, forecast update, or score claim.

The retired NOEMA candidate recursively merged equal 128-byte spans and lost
on selection and sealed pages. This candidate changes the topology, not its
width: variable spans end only after the WRT inverse has emitted `.`, `?`,
`!`, `;`, newline, or a closing markup token. No boundary is visible before
the final WRT byte responsible for it has been decoded.

## Frozen population and causality

Use the first 171 complete pages of the exact exported 10M
JANUS-plus-quotient trajectory:

```text
raw-equivalent bytes     984,835
WRT bytes                591,230
P1 rows                4,729,840
development pages        first 60%
selection pages           next 20%
sealed pages             final 20%
```

Pages are divided into complete 128-WRT-byte patches. Bytes outside complete
patches retain the joint P1. Before byte `t`, model state contains only bytes
strictly before `t`. A boundary caused by byte `t` can affect only byte
`t + 1`. Model state resets at each patch, so checkpoint evaluation never
reuses state produced by another checkpoint.

## One shared model

Every learned control has identical tensors and update opportunities:

```text
byte embedding          257 x 32
leaf projection          32 -> 48
level embedding           2 x 8
shared GRU                input 56, hidden 48
binary-prefix readout      48 -> 255
```

Within each segment, the shared GRU summarizes decoded bytes. Its final state
is then passed through the same GRU, with the second level embedding, to
summarize completed segments. Prediction aggregates the current segment prefix
and all completed-segment state. The current byte becomes input only after all
eight truth bits have been decoded.

Training is frozen at seed 428, AdamW, learning rate 0.002, weight decay
0.000001, gradient clipping 1.0, batch 16, and six epochs. Exact terminated
selection payload chooses the checkpoint; ties choose the earliest epoch.
Each selected checkpoint is canonically int8-quantized per tensor, reloaded,
and fitted twice from the same seed. Repeated model, P1, payload, history, and
selected epoch must be identical.

## Controls

```text
N0  exact joint-prefix parent
NF  one flat 128-byte segment per patch
NB  eight fixed 16-byte segments per patch
NL  causal lag-31 boundary schedules with the same semantic length population
NS  actual decoder-visible semantic/structural boundary schedule
```

`NL` uses only an already completed patch's segment lengths; the first 31
patches use the fixed schedule. It preserves update density and length
statistics while denying correct boundary alignment. Each learned control is
trained independently under the identical contract.

## Exact accounting

Construct and terminate actual range-coded streams for the complete prefix and
each chronological split. The complete candidate P1 must arithmetic-decode to
the original WRT prefix. Reinsert that prefix into the canonical 10M WRT store,
run the official inverse, and reproduce the exact 10M raw SHA-256. Repeat the
entire selected-model inference and range encoding.

Charge both semantic and control models the maximum zlib-9 model size plus a
65,536-byte decoder allowance and 32-byte framing allowance. The matched charge
must not exceed 131,072 bytes.

## Frozen decision

Authorize only a distant replay when all conditions hold:

```text
joint antecedent proof                         exact
prefix parent arithmetic decode                exact
candidate arithmetic decode                    exact
complete WRT and official raw inverse           exact
second fit/model/P1/payload                     byte-identical
development NS gain                            positive
selection NS gain                              positive
sealed NS gross gain                           >= 3,000 B/M
sealed NS package-adjusted gain                 >= 2,100 B/M
sealed NS payload                               < NF payload
sealed NS payload                               < NB payload
sealed NS payload                               < NL payload
all P1 values                                   legal and nonzero
matched package                                 <= 131,072 bytes
```

A scientific miss exits zero and retires this exact boundary alphabet, shared
cell, patch/reset policy, width, training schedule, and quantizer without
rescue sweeps. Infrastructure, causality, arithmetic, inverse, or determinism
failure exits nonzero.
