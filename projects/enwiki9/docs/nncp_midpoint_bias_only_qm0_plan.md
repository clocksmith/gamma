# NNCP output-bias-only midpoint attribution

Candidate: `nncp_midpoint_bias_only_qm0_v1`

The exact 32/32 schedule saves `4,791` bytes over the faithful parent at
`65,536` symbols and `17,185` bytes at `262,144` symbols. This gate asks whether
the new information is largely a compact symbol-rate correction.

The candidate keeps the faithful 64-state model, memory, optimizer, learning
rate, arithmetic alphabet, and full-parameter update after state 63. It adds
one Adam step after states 0-31, but discards every midpoint gradient except the
existing `16,392`-entry output bias. The second half is replayed under that
updated bias, and the ordinary full-parameter update follows after state 63.
No table, parameter, archive bit, or external state is added.

Promotion requires at least `1,600` actual bytes over the identical faithful
archive, positive chronological thirds, exact repeated archives and complete
states, exact independent decode and official raw inverse, at most `65,536`
compressed incremental source bytes, and decimal-memory compliance. This is
an attribution and transfer authorization only. A pass licenses a compact
symbol-bias realization over a runnable substrate; a miss closes bias-only
midpoint transfer without parameter-group, split, optimizer, learning-rate,
or scope sweeps. The full midpoint result remains independent evidence.
