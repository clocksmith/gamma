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

During theorem and supplied-input preparation, no item28 or50 private inputs
were opened and no new Gamma bound or witness was computed. Current-best
selection, M1 thresholds and owner gates remained unchanged.

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

The original-fit measurement below followed the separately reviewed
[execution freeze](FREEZE.md), public-only binding, Claude review and exact
activation. Production and independent reporting retained separate1200-second
phases and600-second cohort caps; the supplied-input measurement alone did not
authorize that launch.

## Accepted original-fit result: small gain, unchanged positive endpoint

The [independent report](evidence/REPORT.md) accepts both fixed300-source
cohorts and reconstructs all514 paired50/53 row values per cohort. The
[full curves and exact deltas](evidence/results.json) have SHA256
`ba4a25c38ce2ab8db6defba02c3e246125af3d31dca7602e64d557c9465cf0c5`.
The largest positive support budget remains **k*=2 in both cohorts**.

| k | R:50 bound | R:53 bound | Naming:50 bound | Naming:53 bound |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 22,197 | 22,197 | 13,727 | 13,727 |
| 1 | 14,666 | 14,666 | 7,105 | 7,105 |
| 2 | 7,136 | 7,136 | 484 | 484 |
| 3 | -394 | -393 | -6,137 | -6,137 |
| 256 | -1,903,184 | -1,903,184 | -1,679,219 | -1,679,219 |

R has a strict raw charge reduction at228 of257 budgets and a one-unit integer
bound gain at52. Naming has a strict raw reduction at210 budgets but no integer
bound gains. P1(exact identity/fixed-potential dominance) and P2(some raw gain)
are true; P3(larger positive endpoint) and P4(positive unrestricted bound) are
false. Both unrestricted k256 charges and bounds are unchanged.

The aggregate old-multiplier reduction is168,390,772,380 integer units for R
and157,849,615,761 for naming, across408,033/364,792 old occurrences and
87,017/78,799 old entries. Yet the largest support-budget charge reduction is
only308,361/5,068 units. With D=1,000,000 these are exact unrounded bound gains
of0.308361/0.005068 before ceiling. Total removed slack is therefore a poor
proxy for improvement in the maximizing256-entry charge on these fixed
potentials. The result does not test changing the potentials.

[Production supervision](evidence/production-supervisor.json) completed in
6.515635seconds and [independent-report supervision](evidence/supervisor.json)
in22.393574seconds; each records integer exits[0,0] and completed cleanup.
Per-process production peaks were545,452KiB(R)/525,948KiB(naming), and report
peaks356,736/344,472KiB. All45 code and23 runtime pins remained unchanged.

The positive bounds exclude C/N<=10% only for the fixed300-source classes with
at most2 one-owner entries; this experiment does not establish their coverage
feasibility. The negative unrestricted bounds are inconclusive, so there is
**no10% exclusion for the unrestricted full entry class**. No dictionary,
witness, new qualification, validation/case access, M1 change or global dual
optimum is claimed. Original13 qualification is reused by exact source hash;
item23's later unchanged-source exit137 remains separate. **Item51 flat remains
the current best at this record.**
