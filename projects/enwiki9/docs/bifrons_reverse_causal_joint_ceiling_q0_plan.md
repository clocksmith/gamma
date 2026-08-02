# BIFRONS reverse-causal joint ceiling Q0

Candidate: `bifrons_reverse_causal_joint_ceiling_q0_v1`.

Proposal: `bifrons_reverse_causal_joint_ceiling_v1`.

## Hypothesis

The exact JANUS-plus-quotient trajectory is causal from the left. A source-
native endpoint428 predictor run over the WRT bytes in reverse order can expose
right-context information that is absent from that trajectory. One transmitted
cut may combine a forward-coded prefix with a reverse-coded suffix without a
cyclic decode dependency.

This is not a reverse-energy or syndrome search. Both halves are terminated
arithmetic streams. The reverse expert predicts the same WRT bytes in reverse
order and sees only bytes already reconstructed in that order.

## Frozen population

Use the canonical 10M WRT store and the last complete page ending before raw
byte 1,000,000. The frozen boundary is:

```text
complete pages       171
raw-equivalent bytes 984,835
WRT bytes            591,230
P1 rows              4,729,840
```

Legal cuts are zero, the WRT end of each of those complete pages, and the
population end. Select exactly one cut by minimum rounded-Q256 codelength.
Ties choose the earliest cut. There is no per-page or per-event mode choice.

## Reverse expert

Run the receipt-bound endpoint428 pair/layer-0 backend over the byte-reversed
WRT population with `-r`. Pretrain it with the byte-reversed canonical
dictionary. Both transformations are deterministic and add no learned table.
The source executable, dictionary, WRT store, endpoint P1, joint P1, page map,
and antecedent decisions are hash-bound.

## Exact archive accounting

The candidate archive contains:

```text
standard CMIX length/vocabulary header  37 bytes
cut byte offset                           4 bytes
forward payload length                    4 bytes
reverse payload length                    4 bytes
forward joint arithmetic payload          exact
reverse endpoint arithmetic payload       exact
```

The parent control contains the same 37-byte standard header and an exactly
terminated joint payload. Endpoint-forward and all-reverse controls are also
reported. The trace gate must range-decode both candidate payloads, reverse the
suffix, and reproduce every WRT byte.

## Conditional determinism

The first guarded reverse run is sufficient for a scientific rejection. If and
only if the exact candidate clears the economic gate, run a second independent
source execution and require byte-identical reverse archive and P1 trace. This
conditional repeat is frozen before observing the result.

## Promotion and retirement

Promotion requires all of:

```text
source and input identities                 exact
reverse source arithmetic replay            exact
candidate forward arithmetic decode         exact
candidate reverse arithmetic decode         exact
complete WRT reconstruction                  exact
all probabilities                            legal and nonzero
decimal-10GB guard                           pass
second reverse archive and trace             byte-identical
candidate total                              < endpoint-forward total
candidate total                              < all-reverse total
gain over joint                              >= 3,000 B/M
```

At this population the gross threshold is 2,955 bytes after the exact 49-byte
candidate frame. A pass authorizes one canonical 10M replay with the frozen
format. It gives no source, forecast, or full-corpus score credit.

A miss retires this whole-prefix/suffix, one-cut, reversed-dictionary,
endpoint428 reverse expert. Do not sweep cut restrictions, reverse pretraining,
dictionary order, direction granularity, or page modes. Blockwise or semantic
future-information codecs remain separate mechanisms and require independent
causal constructions.
