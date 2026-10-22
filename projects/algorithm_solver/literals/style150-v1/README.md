# style150-v1: shared-style rewrites of the first 150 programs

Frozen design: [FREEZE.md](FREEZE.md) and [contract.json](contract.json) (commit `d97c61463`,
before any rewrite or arm). Public evidence: [evidence/results.json](evidence/results.json)
(per-arm aggregates, per-problem counts, dictionary and manifest hashes) and
[evidence/pool-requalification.json](evidence/pool-requalification.json). Sources, cases,
dictionaries and sequences stay private.

## Result

Rewriting all 150 programs to one shared style ([STYLE.md](STYLE.md)) gives the best
representation of these programs so far. Arm E (rewrites only, searched from the earlier
best dictionary) uses **9,538 eight-bit selections**, median **55**, p95 **151**, with
**50.1%** single-character selections and **18,091** dictionary-plus-packet bytes. The
previous best was 12,337 selections, median 74, p95 198, 58.1% and 22,296 bytes: that is
22.7% fewer selections and 18.9% fewer bytes. Per problem against arm C, 127 programs need
fewer selections and 23 need more (median −15, range −148 to +117).

All 150 rewrites qualify on every corpus case under the unchanged oracle, with strict parity
with the original's result, type, arguments after the call and alias edges. 142 passed on
their first parity check; 161 checks were used in all. The rewrites total 31,283 bytes,
against 37,547 for the previously chosen sources.

This is an improved offline representation of the same 150 known programs. It is not M1
(150 is not the frozen 500, and median 55 and p95 151 remain above the 32 and 96 gates), and
it is not autonomous assembly or unseen solving.

| Arm (256 entries / 8 bits) | Sources | Selections | Median | p95 | Single-char | Package bytes | Trials |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A: existing pool, D0 fixed | S1 | 12,337 | 74 | 198 | 58.1% | 22,296 | fixed |
| A0: originals only, D0 fixed | S0 | 57,257 | 311 | 881 | 85.7% | 65,302 | fixed |
| B: pool + rewrites, D0 fixed | S2 | 11,360 | 67 | 169 | 57.5% | 21,279 | fixed |
| C: pool, search | S1 | 12,334 | 73.5 | 200 | 58.1% | 22,299 | 1,813 |
| D: pool + rewrites, search | S2 | 11,173 | 65 | 168 | 58.0% | 20,753 | 6,312 |
| **E: rewrites only, search** | SE | **9,538** | **55** | **151** | **50.1%** | **18,091** | 47,615 |

| Arm (128 entries / 7 bits) | Selections | Median | p95 | Single-char | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 20,155 | 117.5 | 292 | 79.1% | 25,532 |
| B | 17,806 | 102.5 | 262 | 78.4% | 23,473 |
| C | 20,153 | 117.5 | 292 | 79.3% | 25,331 |
| D | 17,387 | 95.5 | 261 | 79.1% | 22,942 |
| **E** | **16,577** | **94.5** | **242** | **77.0%** | **21,558** |

At 8 bits E needs 76,304 input bits, against 116,039 for E at 7 bits, so eight bits remains
the cheaper input arm on these programs.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| P1 | D at least 10% below C (256) | **Not met**: −9.4% (11,173 vs 12,334) |
| P2 | D's single-character fraction 10 points below C's (256) | **Not met**: 58.0% vs 58.1% |
| P3 | E no more than C (256) | **Met**: 9,538 vs 12,334 |
| P4 | D below C (128) | **Met**: 17,387 vs 20,153 |
| P5 | DH at least 10% below CH on the held-out 30 (256) | **Not met**: −9.7% (4,167 vs 4,614) |
| P6 | at least 120 of 150 rewrites qualify | **Met**: 150 |

## The search confound (negative methodological result)

E's pool is a subset of D's, so D's optimum can be no worse than E's, yet D's search stopped
at 11,173 while E's reached 9,538. The cause is the candidate proposer, not the style. The
joint-v1 span proposer, reused unchanged from matched80-v3, scores candidate strings over the
parses of every source variant in the pool, including variants the encoding does not choose.
With several verbose variants per problem, its shortlist fills with whitespace runs from
unchosen originals that save nothing. So C and D reached a local optimum after 1,813 and
6,312 trials (the cap was 100,000), while E, with one source per problem, searched for 47,615
trials. In matched80-v3 every problem had one source, so the problem did not arise there.

The held-out arms suffer most. CH and DH start from the fallback alphabet, and their greedy
refill stalls at 126–127 entries at both widths. Their dictionaries are therefore identical
at 128 and 256, and much weaker than the D0-started arms (24,432 and 20,605 selections on all
150). The held-out comparison is still matched, and the style helps there too: DH needs 9.7%
fewer selections than CH on the 30 held-out programs (4,167 vs 4,614). It does not measure
what a full-capacity dictionary would do on unseen programs.

So P1, P2 and P5 are not clean tests of the style hypothesis. They fail partly because the
search did not use its budget. The fix is a successor experiment, not a change to this one:
score proposals on chosen sources only (or on one source per problem), then rerun D and the
held-out arms under a new freeze.

## Notes on the rewrites

- Rewriters followed STYLE.md but reported unavoidable deviations: loop heads outside the
  fixed list (`while(l<=h)`, list walks, heap sifts), helpers with four or five parameters,
  and names beyond the role table. Several dropped input checks under rule 11. Three had to
  restore them (28, 62, 892) because the corpus cases include inputs outside the stated
  constraints; parity caught each one.
- 944's rewrite compares characters in place instead of copying each string, lowering memory
  from linear to constant. The guide asks for the same asymptotic memory; this is lower, not
  higher, and it is kept under the one-submission rule.
- Problem 23 has only 3 corpus cases, so its parity rests on much less evidence than the others.
- Eight existing alternatives (`legacy-shared` variants of 169 and 961) fail the corpus cases
  and are excluded from every arm. They had passed only their earlier stage-specific case sets.

## Next

A successor (style150-v2) fixes the proposer to score chosen sources only and reruns D and the
held-out arms. Vocabulary search at scale then uses the frozen 500 with the rewrites available
as source alternatives for the first 150.
