# NNCP midpoint decoder-visible recurrence attribution

Candidate: `nncp_midpoint_decoder_visible_recurrence_qm0_v1`.

Epistemic tier: exact offline teacher attribution with zero score and forecast
credit. This diagnostic cannot make LibNC eligible and does not change a coded
stream.

## Question

The exact 262,144-symbol midpoint teacher gains `17,185.333881650356` ideal
bytes over its faithful parent. Test whether that gain is concentrated where
the true symbol has already occurred in the decoder-visible history of the
same native stream. Such concentration would identify bounded recurrence as a
candidate coordinate for an open replacement model. Its absence would retire
simple recurrence distillation without implementing another codec.

## Frozen population and feature

Consume the receipt-bound parent and midpoint branch-frequency traces and the
first 262,144 full-dictionary symbols. Reconstruct the exact gain for every
symbol in native execution order. For each stream, compute the distance to the
previous occurrence of the current true symbol using only earlier decoded
symbols. The primary mask is distance at most 32. Also report disjoint distance
buckets, same-segment reuse, and second-half reuse of a first-half symbol.

The specificity control rotates per-symbol gain by exactly 17 complete
64-symbol segments within each stream. This preserves stream identity,
position within the segment, phase, gain population, and total gain while
breaking the target-specific recurrence alignment. It is an attribution
control only and is never presented as causal coding.

## Decision

Diagnostic support requires all of:

```text
recent-32 genuine signed gain       >= 25% of total teacher gain
genuine minus rotated control       >= 10% of total teacher gain
genuine chronological thirds        each positive
registered total and thirds          exact
all recurrence features              prefix-causal
```

A miss retires simple bounded symbol-recurrence distillation of the midpoint
teacher without window, shift, threshold, bucket, or parameter sweeps. A pass
only authorizes design work for an open causal model and receives no inherited
archive bytes.
