# Conditional cost of the fixed KDA trajectories

Candidate `fx2_kda_conditional_cost250k_v1`, owner `root_kda_attribution`,
applies the prior reflection's distinction between global archive loss and
conditional predictive information. The fixed carry codec remains retired:
its measured archive gains are `g_P=-3` and `g_S=11` on exposed `[0,250000)`.
This audit changes no codec and runs no native model.

The [frozen contract](../operations/adaptive/experiments/fx2_kda_conditional_cost250k_v1.json)
binds 38 inputs, including independent P/K/D/S archives, coder traces and reset
states. It rechecks byte identity, all truth/count coordinates and exact WRT
inversion. Two separate subprocesses must emit byte-identical numerical receipts.
The scope is 250,000 raw bytes, 151,210 modeled bytes, 1,209,680 bit records
and 98 native reset pieces. Original cold initialization is unchanged.

The audit retains every piece's P/D/S ideal cost and groups gains by causal
piece age: `[0,1)`, `[1,4)`, `[4,16)`, `[16,64)`, `[64,256)`, `[256,1024)`
and `[1024,infinity)`. It also records previous completed piece length.
Selecting favorable pieces or age bins after observing their gains is hindsight;
these tables do not implement a causal selector.

For each bit, let `p` be P's integer truth count and `m` the maximum truth count
across the fixed supplied trajectories. Any selection or convex mixture of
those same distributions gives truth mass at most `m/65536`. Products of
`m/p` over 4,096 strictly beneficial events, with exact integer log2 ceilings,
therefore bound ideal gain even when selection and simultaneous model access
are free. P/D and P/D/S bounds are recorded separately.

This is not a finite-archive bound. It does not cover changed feedback, new
trajectories, a native reset gated by a new rule, or full-corpus behavior.
The frozen 4,096-ideal-bit floor is a development-budget decision, not a theorem
about minimum implementation cost. A miss stops selection work over these
specific supplied streams; it does not erase any positive conditional effects.

Five [synthetic tests](../tests/test_fx2_kda_conditional_cost_v1.py) pass:
hand-computed gains, zero gain, last-bit misalignment rejection, exact chunk
rollover, and decoded-only boundaries with fixed age bins. Resource stops are
CPU2, 1,073,741,824 memory bytes, zero swap, 16,777,216 scratch bytes and
300 elapsed seconds. No new archive gain, complete package or prize score is
claimed; the target remains 90,000,000 bytes (9.0000000%), full score unknown,
best counted forecast 109,389,323, distance +19,389,323 bytes.
