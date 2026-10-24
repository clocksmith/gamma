# Entry prices with nonoverlapping use bounds

Item71 tightens the63 owner and66 global pricing divisors. Each selected entry
can occur only a bounded number of times on nonoverlapping source paths:
`n_e=sum_p min(m_ep,floor(N_p/length(e)))`. Using n_e instead of all-occurrence
m_e removes at most the same paid price per selected entry, while weakly
lowering every same-price residual cap. Required-owner allocation also
preserves domination of68.

The [draft](DRAFT.md), [tiny proof oracle](proof.py) and [tests](test_proof.py)
use supplied inputs only. A coverable owner example improves charge24 to20
and bound2 to6; a coverable shared-entry example improves global charge92 to88
and bound-100 to-96. Both use general supplied q and the fixed15-price family.
The relaxed path values are independently derived, not arbitrary constants.

Six focused tests passed0.136seconds. They enumerate tiny dictionaries and
complete joint paths, verify actual F=10C-N, every residual schedule and finite
allocation, and cover zero slots, bans, repeated shared strings, signed
ceilings, B0/r>B and invalid input refusal. Root and an independent mathematical
reviewer found no blocker; see [review](REVIEW.md).

This is a theorem and tiny implementation record. No scalable measurement,
original input, price tuning, corpus result, witness improvement or M1 claim.
The count is conservative and can be much larger than exact interval packing.
A separate reviewed scalable design and frozen protocol must precede any
measurement or original-input run. Component intent and admission/publication
boundaries are preserved; ancestor files remain unchanged.
