# DV-1 Solution: Delayed-View Residual Prediction

Induct on encoded bit position. Before the first bit, both sides have empty
completed-group history, the same current-group state, and identical empty
tables.

Assume equality before bit \(t\). All context coordinates are deterministic
functions of this common state, so both sides form the same key, obtain the
same \(r_t\), and compute the same integer \(q_t\). Arithmetic decoding
therefore recovers the encoder's truth bit. Both sides then apply the same
counter update, insertion rule, and deterministic eviction rule.

If the bit does not finish its group, neither side exposes the raw expansion.
If it does, the group inverse is a deterministic function of the now-complete
encoded group, so both sides obtain the same \(R_j\) and append it
simultaneously. This restores the invariant for the next bit.

By induction, every encoded bit and every completed raw expansion agrees.
After the final group, concatenating the identical expansions yields the
original raw stream.

No learned table is transmitted because decoding reconstructs every update.
This is a correctness theorem only. The implementation and fixed source are
still counted, bounded storage must respect the memory limit, and only an
exact arithmetic replay can establish compression benefit.
