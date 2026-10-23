# Length-sensitive full-substring fraction dual

[Freeze](FREEZE.md); [derivation](DRAFT.md); [metadata](evidence/results.json).

Both cohorts complete and independently replayed. The stronger bounds remain
negative, so the full-substring 10% reachability question remains unresolved.

This design follows item33’s disclosed zero-multiplier result. A larger dual family does not guarantee strict improvement in a finite run. Zero or negative bounds remain inconclusive; only equality with a verified feasible upper bound certifies an exact optimum.

| Cohort | Allowed words | Pieces | Item33 lower | New lower | Numerator gain | Iterations | Best feasible F | Generated failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R | 13553771 | 375160 | -37980 | -27266 | 10713026050 | 519 | 110156 | 42/42 |
| naming | 13561646 | 375342 | -37943 | -28259 | 9683769690 | 537 | 94121 | 44/44 |

Exact packet IDs, framing, Finish, dictionaries and both decoder sources are charged. One-owner/near-whole witnesses remain relaxation diagnostics with unresolved semantic reuse; no M1 legality claim. Installed runtime footprint is unmeasured.

| Prediction | Met |
| --- | --- |
| P1 | True |
| P2 | True |
| P3 | False |
| P4 | True |

M1 unchanged:400/500,<=256 shared entries, median<=32/p95<=96 selections,<=10% single-character bits, zero whole-solution entries. Fit-only fixed-source bounds do not close M1, unseen populations, rewrites or other gates.

## Final activation-bin diagnostic

The independently reconstructed [bin diagnostic](evidence/bin-diagnostics.json)
finds **zero of 256 selected entries in bins 9–10 in both cohorts**. All selected
weights are positive; cutoff ties do not make bin counts ambiguous. R selects
227 length-two entries, 11 length-three, 3 length-four and 15 length-five-to-eight;
naming selects 231, 4, 4 and 17 respectively. Thus the proposed explanation that
the final top-capacity term is dominated by long-bin multiplicity is not supported.
This does not identify the remaining dual gap's cause or prove short-word
bottlenecks. These are relaxed activation choices, not feasible dictionaries.

Execution took 1,207.36 seconds. R/naming stopped at their time boundaries after
519/537 iterations (1,202.82/1,203.19 optimizer seconds, including the last
bounded iteration). Generated proposals all lack coverage: 42/42 and 44/44.
All 1,200 retained witness packets decode; no validation or fresh source
execution occurred. P1/P2/P4 hold; P3 is false. See [review](REVIEW.md).

## Descriptive path replay,2026-10-23

A separate [path-bin replay](evidence/path-diagnostics.json) checks the final-q
minimum paths against the independent heap DP and the feasible seed against
its retained per-program costs. Relaxed paths use29,074/30,579edges, zero
single-character edges and27,335/29,066 length-two edges for R/naming. Only one
edge per cohort is length129+:149/131bytes. Feasible seed paths use28,554/27,099
edges, including13,871/12,122 characters and zero length129+edges. Thus the
relaxed paths also are not dominated by long-bin edges at these points. This
is descriptive, with deterministic path ties; it does not causally decompose
the dual gap. No new search, source execution or witness is introduced.
