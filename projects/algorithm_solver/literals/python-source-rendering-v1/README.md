# Python rendering lowers actions slightly but raises character share

All360experimental/reference views independently decode and qualify. Five
distinct new selected sources pass513strict observation checks, with no
failure. No rendering arm passes the frozen readiness gates.

| Width | Arm | Validation actions | Median selections | p95 selections | Character share | Package bytes |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 128 | U/D/R | 1,420 | 127 | 252 | 74.2736% | 2,411 |
| 128 | S | 1,408 | 121 | 248 | 76.7691% | 2,400 |
| 128 | J | 1,405 | 121 | 248 | 76.7908% | 2,400 |
| 256 | U/S/D/J | 935 | 97 | 180 | 56.9114% | 3,721 |
| 256 | R | 949 | 97 | 181 | 57.7660% | 3,720 |

At128, S improves2of9validation programs and J3of9, with none worse; J improves
one program versus S. The gains miss5% and breadth gates, and character share
worsens against the controls. At256, all experimental arms tie their unchanged
anchor. There is no cross-width winner selection.

The supervisor completes in9.08seconds. Dictionary continuations stop at
bounded-neighborhood local optima, not their time limits; this is no global
optimality claim. AllP1–P5predictions hold. Exact qualification is finite
evidence, not semantic equivalence or independent generalization. M1/JS rows
and all protected populations remain unchanged.

[Freeze](FREEZE.md), [design](DRAFT.md), [review](REVIEW.md),
[detailed report](evidence/REPORT.md), [metadata](evidence/results.json).

The detailed report's median/p90 columns are actions including Finish; this
summary explicitly uses selections. Full dictionaries, packets, headers,
padding, Finish and13,010decoder-source bytes are charged; installed runtime
footprint remains unmeasured. No model or training cost.
