# JANUS sparse context DAG Q0

Status: frozen zero-credit paid-model experiment.

Candidate: `janus_sparse_context_dag_q0_v1`

## Hypothesis

A transmitted, MDL-pruned variable-depth suffix DAG can retain residual
information that endpoint428 and the retired flat 65,536-state quotient miss,
while describing substantially fewer states than the terminal dense JANUS GRU.

This is not a width or hash sweep. The model is one canonical sparse set of
context records. At runtime it applies only to the same endpoint428 bitstream
and uses completed WRT bytes, the decoded current-byte prefix, and the current
parent probability.

## Frozen context language

Each row has a base state:

```text
(current byte-tree node, endpoint428 P1 high-nibble)
```

The context suffix contains zero through six completed WRT bytes. A depth-d
key is:

```text
(base state, x[t-d:t])
```

The current byte never enters the completed-byte suffix. Its already decoded
prefix enters only through the byte-tree node. Contexts require support eight.
There is no page ID, block ID, future event length, raw expansion, or hidden
teacher state.

Each retained record chooses one frozen rational odds correction:

```text
1/4, 1/2, 2/3, 1, 3/2, 2, 4
```

Runtime lookup selects the deepest transmitted suffix record, falling back
through shallower records and finally identity.

## Exact MDL pruning

For every supported context, accumulate integer qbit cost for every correction
on the complete fixed population. A bottom-up dynamic program decides whether
to retain the node, retain descendants only, or inherit the ancestor
correction. Each retained canonical `<key:uint64, depth:uint8, code:uint8>`
record is charged exactly ten raw model bytes during selection. This is a
conservative admission charge; final accounting still charges the actual
canonical model blob compressed with zlib level 9.

Tie order is correction codes `1/2, 1, 2/3, 1/4, 3/2, 2, 4`, then the smaller
code number. The entire fit is repeated independently and must reproduce the
same model, adjusted P1 stream, and payload.

## Controls

```text
D0  exact endpoint428 parent replay
D1  depth-zero-only MDL map over node and confidence
D2  complete depth-zero-through-six sparse context DAG
DR  D2 record codes circularly rotated within each depth
```

DR retains depth populations, keys, model size, and correction-code counts
while breaking suffix-to-correction alignment. All models predict the same
bitstream and update no hidden state.

## Package accounting

```text
zlib-9 canonical model
+ 32,768-byte deterministic decoder allowance
+ 64 framing bytes
```

The complete package must not exceed 192 KiB. The oracle tool is reported but
does not substitute for the frozen decoder allowance.

## Population and exactness

Use the receipt-bound recovered endpoint428 opening-1M P1, WRT store, parent
archive, page map, dictionary, backend, and raw input. Fit on the full legal
fixed population, but report independently terminated complete-page
development, selection, and sealed-confirmation payloads.

Require:

```text
parent payload byte identity             exact
D1/D2/DR arithmetic decode               exact
independent D2 model/P1/payload replay    byte-identical
WRT reconstruction                       exact
official WRT-to-raw inverse               exact
all probability values                   legal and nonzero
```

## Decision

Authorize one unchanged canonical-10M replay only if:

```text
D2 gross exact gain                      >= 3,000 B/M
D2 package-adjusted projected gain       >= 2,100 B/M
development gain                         positive
selection gain                           positive
sealed-confirmation gain                 positive
D2 payload                               < D1 payload
D2 payload                               < DR payload
complete package                         <= 192 KiB
all exactness conditions                 pass
```

A valid miss exits zero and retires the frozen six-level suffix language,
support eight, correction alphabet, ten-byte record charge, and rescue sweeps
over depth, support, confidence bins, record cost, or correction values. It
does not retire a context DAG driven by a materially different information
source. Forecast and score credit remain zero until counted native evidence.

