# NNCP Mid-Segment 32/32 Update Qm0

Status: frozen exact constructive update-schedule gate

## Hypothesis

The faithful NNCP parent predicts 64 symbols per stream before one Adam update.
An update after the first 32 completed symbols may adapt the decoder-visible
model soon enough for the second half to improve, without transmitting model
state or changing the coded alphabet.

The candidate predicts states 0–31 with the incoming model, computes
cross-entropy only on those completed states, performs the frozen Adam update,
and rebuilds the incremental KV caches from the unchanged incoming persistent
memory. It replays known inputs 0–31 under the updated model and predicts states
32–63. It then computes cross-entropy only on the completed second half and
performs the second update. Outgoing persistent memory is taken from the
pre-second-update forward pass, matching the parent's established convention.

Both sides know the split and every training target before its update. No
gradient, selector, checkpoint, or other side information enters the archive.

## Frozen gate

Use the exact receipt-bound 65,536-symbol population, 32 streams, 64-symbol
segments, split 32/32, faithful optimizer and learning rate, and unchanged
balanced branch arithmetic. Compare against the faithful 96,142-byte archive.

Require two byte-identical encodes, exact arithmetic decode, branch-frequency
and complete-state identity, official NNCP raw inversion, exact joint boundary,
decimal-memory compliance, at least 800 actual archive bytes, positive aligned
ideal gain in each true corpus-order third, and at most 65,536 bytes of
compressed incremental source.

A terminal miss retires within-segment split points and more-frequent online
Adam schedules at this frozen parent. It does not authorize learning-rate,
optimizer, loss-weight, or segment-length sweeps.
