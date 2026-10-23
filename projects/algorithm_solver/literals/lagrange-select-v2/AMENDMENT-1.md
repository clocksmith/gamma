# Amendment 1, 2026-10-23: private certificate replay receipt (before launch)

Codex's approval of v2 (gamma-team LOG, 17:59Z) suggested persisting the quantized multiplier vector and a hash
of the pool and occurrence ordering, so the exact certificate can be replayed without rerunning the
floating-point optimization. Nothing has run.

`selection.py` now writes, privately per width:
- `certificate-q.npy`, the integer multipliers;
- `q_sha256` and `pool_occurrence_order_sha256` in the results.

The pool strings are not published. No policy, budget, arm or prediction changes.

`contract.json`'s hash for `lagrange-select-v2/selection.py` changes from `7b29acb56e2ca3543df453c9dcc02fc26b2a978b0d3f7d6e178d3f59bf33958c` to
`fed3640dd86735a59491578552e0654c1ae6d5f3d1f4d155ee711c941739c757`. This file is added to the contract's code hashes.
