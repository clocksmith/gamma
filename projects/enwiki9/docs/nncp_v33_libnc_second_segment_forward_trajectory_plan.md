# NNCP v3.3 LibNC second-segment forward trajectory

Candidate: `nncp_v33_libnc_second_segment_forward_trajectory_v1`

## Question

The true post-update receipt proves that source and analytic parameters and
memory agree after update one, while the next probability segment differs by
`0.010298056527972221`. Does that difference begin at a named LibNC forward
block when both implementations start from the exact source state, or is it
only an amplification of the remaining sub-micro-unit state error?

## Frozen intervention

Use the exact first 32 canonical raw bytes and unchanged recovered NNCP source.
Add only observation calls:

- save source parameters, `mem_h`, and `train_h` after each real update;
- enable the source's existing seven `DUMP_HASH` forward observations;
- capture every sequential evaluation twice.

The archive and teacher trace must remain byte-identical to the parent update
state receipt. Export the actual source post-update-one state, then replay only
the second four-symbol segment in the analytic graph. Compare, in chronological
order, `attn_out_bl`, `attn_out`, `ff1_out`, `ff2_in`, `ff_out_bl`, `ff_out`,
and `output` for all four decoder states.

Run the same replay from the analytic post-update-one state as a sensitivity
control. The source state is the localization input; the analytic state is not
substituted into the primary comparison.

## Gates

- both native executions repeat archive, trace, update states, and tensor dump;
- archive and trace equal the parent receipt exactly;
- the source-state and analytic-state replays repeat byte-identically;
- all tensor labels, shapes, and positions align;
- the first error above `2e-6` is unique, or every source-state error stays at
  or below `2e-6` while the analytic-state control reproduces the probability
  miss.

A unique named block authorizes exactly one child that instruments arithmetic
inside that block. A source-state match instead localizes the cause to exact
state evolution and authorizes a state-rounding/serialization contract. Any
changed source trajectory, incomplete dump, nondeterminism, or ambiguous
record alignment is an infrastructure failure. No tolerance, width, learning
rate, optimizer, or population sweep follows a miss.

This diagnostic receives zero score and forecast credit. The forecast remains
`109,389,323` bytes and the verified full-1G result remains unknown.
