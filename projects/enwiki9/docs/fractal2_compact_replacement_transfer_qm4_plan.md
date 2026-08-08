# FRACTAL-2 compact-replacement transfer QM4 (retired before scoring)

Status: rejected on causality audit. The generic compact final-P1 trace remains
valid observation infrastructure, but this frozen rule universe must not be
priced or promoted.

## Objective

This proposal would have repriced the frozen FRACTAL-2 QM3 FORM/ECHO universe
on the compact-only Endpoint428 replacement. The later paid-replay audit proved
that arbitrary QM3 opportunities are not a decoder-derived schedule: target
positions and candidate lengths require an explicit occurrence ledger. The
proposal is therefore rejected before its scoring tool is run.

## Bound parent and economics

The compact replacement has a source-bound forecast of `109,499,618` bytes and
therefore owes `4,499,618` bytes to the current `105,000,000` target before any
new rule, command, framing, decoder, or source byte. At canonical `10M`, the
paid successor must leave at least `60,000` net bytes after every counted cost.

The original numeric gate is void for QM3 because a free noncausal ceiling
cannot authorize a paid successor. A separate proposal may reuse the compact
trace only with decoder-causal spans and independently frozen economics.

## Trace contract

`tools/materialize_compact_final_p1_trace.py` copies the frozen compact source
into an isolated directory, verifies the encoder hash, and adds only a final-P1
observer. The trace-on and trace-off `10M` encodes use the same built binary.
Their archives must be byte-identical, the trace must contain exactly two bytes
per WRT truth bit after its 16-byte header, and both process guards must stay
below decimal 10 GB. Timing is excluded because the runs may overlap other
work.

The exact `1M` infrastructure prerequisite passes: archive `174,099`, SHA-256
`f8dbb64d...`, `4,805,936` trace rows, and peak single RSS `7,574,544` KiB.

## Promotion boundary

Nothing in this retired QM4 proposal authorizes paid replay or native compact
integration. The trace is observation-only, earns zero score credit, and does
not change the forecast.
