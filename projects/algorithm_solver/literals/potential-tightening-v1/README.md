# Fixed-potential tightening cannot weaken the lifted bound

2026-10-24. [Item 53's proof](DRAFT.md) removes slack from old occurrence
penalties while preserving every suffix distance used by item 50. Every
activation weight weakly decreases, so every support-budget certificate is
at least as strong for the identical source universe and fixed potentials.
This guarantees neither a strict improvement nor a positive unrestricted bound.

An independent mathematical review confirmed the dominance argument and
narrowed its optimality statement: the construction maximizes the **fixed-L**
certificate within the Bellman-compatible family, or the exact dual among
assignments preserving the same actual suffix distances. Larger penalties
can increase actual path values; the broader dual optimum remains unresolved.
Finite old suffix distances, retained tight paths and identical feasible-entry
sets are explicit assumptions.

Three [invented oracle tests](test_proof.py) passed in 0.111 seconds. Across
32 small random source pairs, they compare old/full suffix distances and
occurrence weights, enumerate all eligible dictionaries of size at most four,
and check all corresponding support-budget charges and weak duality. Separate
fixtures show that reducing slack can leave the maximum charge unchanged and
that larger penalties can raise the actual path term. These small tests support
the algebra; they are not a corpus run, complexity measurement or production
implementation. The [oracle](proof.py) has no private loader or runner.

No item28 or50 private inputs were opened and no new Gamma bound or witness was
computed. Current-best selection, M1 thresholds and owner gates remain unchanged.

## Supplied-input implementation and measurement

The isolated [production kernel](tighten.py) retains old occurrence entry IDs
and tightens their weights while preserving all suffix potentials. Separate
new-only top256 lists are merged with original and tightened old weights to
reconstruct both50 and53. The [independent checker](independent.py) derives its
own AC/end-order paths and streams every allowed depth; it does not use the
production endpoint-range search. Both explicitly share item33's structural
index/verifier. [Review](REVIEW.md) records the boundary and checks.

One pinned invented measurement completed under the180-second/core6/8GiB-per-
process envelope. The [result](synthetic-results.json) and separate
[supervisor receipt](synthetic-supervisor.json) agree on completed cleanup,
integer exit0 and [specification](synthetic-spec.json) hash
`a35dbd7ea210048f6ddc491ec08e1111f94b169bc00301f8da58699f69e64ecb`.
Whole elapsed time was15.997118seconds; worker peak RSS587,508KiB and supervisor
peak32,292KiB. The17 tiny oracle tests ran within that envelope. All21 code and
12 runtime pins were verified after completion.

| Invented fixture | Old occurrences | Allowed entries | Independent replay seconds | Budgets with strict integer gain |
| --- | ---: | ---: | ---: | ---: |
| Paired-prefix75k,300 sources | 758,605 | 8,966,636 | 9.469452 | 257/257 |
| Repeated one-owner12k,12 sources | 12,832 | 143,070 | 1.139736 | 253/257 |

Both fixtures agree on both257-row curves, exact top identities, all potential/
weight digests and reduction statistics. Original50 saved fields also match;
its historical synthetic receipt did not store top digests, so no historical
top-identity comparison is claimed. The repeated fixture streamed5,991,440
production repeated-new occurrence contributions; the larger fixture exercises
unique-range splitting. Explicit tiny tests cover a previously excluded new
entry replacing a lowered old entry, unchanged charges after slack reduction,
and a raw gain hidden by integer ceiling.

These are invented-input results. They do not establish corpus gains, positive
unrestricted bounds, M1, a dictionary or a qualified witness. They preserve the
quadratic worst case. The prior50 worker peak was489,168KiB; the new peak is
higher. Whole-time ratios are not a matched performance claim: oracle placement
and the clock's import/preflight coverage differ between the two harnesses.

The next gate is a separately reviewed [execution freeze](FREEZE.md), public-
only inactive binding, Claude review and exact activation before any original
fit input is read. Production and independent reporting each retain separate
1200-second phases and600-second cohort caps. No corpus launch follows from
the supplied-input measurement alone.
