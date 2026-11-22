# Results: the deficit hierarchy at level 1

Run on 2026-11-22 (UTC) by `claude-bits-1`. Not pre-registered: this is a new method being tried on corpora
this project has already seen, checked against exhaustive search. An unseen test is still owed.

**The test now settles rank + 1 as well as rank. It is exact on 33 of 35 real corpora with no other method,
and it gave no wrong answer in 8,736 exhaustive checks.**

## Against exhaustive search (`audit_deficit.py 1`)

4,368 small corpora in five families, each under the witness rule and the unrestricted rule.

| Outcome | Count |
| --- | ---: |
| Checks | 8,736 |
| Lower bound above the true minimum, or an illegal dictionary | 0 |
| Exact (lower bound and built dictionary meet the true minimum) | 8,355 |
| Proved "at least rank + 2", which the level-0 test cannot | 519 |
| Cases whose minimum is rank + 1, settled exactly | 2,152 of 2,172 |

The 381 inexact cases have a minimum of rank + 2 or more without a matching dictionary, or a search that
stopped at its limit.

## On the 35 real corpora (`real_corpora.py`)

Witness rule, threshold 2, 160-byte cap. Every dictionary is replayed with the capped checker of
`capacity-boundary-v1`.

| What settles the minimum | Corpora |
| --- | ---: |
| Rank equals the alphabet | 22 |
| Level 0 builds a dictionary of rank entries | 9 |
| Level 1 builds a dictionary of rank + 1 entries, after level 0 rules rank out | 2 |
| Open | 2 |

- **Cairo headers (public):** rank 72, minimum exactly 73, with a 73-entry dictionary built here in 1.7 s.
  Before this the 73-entry dictionary came only from the Lagrangian baseline's integer-program fallback
  (24 s); a flow search of mine reached 74.
- **JS-2:** rank 64, minimum exactly 65, built here in 3.6 s. The Lagrangian baseline stalls at 64 on the
  rejection (exploratory run, 3 s, "stalled"), though a linear-program solver does certify 65.
- **PY-3:** lower bound 53 (rank 51; every one of the lines refuted, 379 s). Best dictionary known is 62.
- **B04:** lower bound 23 (rank 22). Level 1 was not attempted: 216,252 lines exceed the limit of 4,000.
  Best dictionary known is 60; the Lagrangian baseline's bound is 30.

With level 1 the three-arm race on the 12 public projects would read 34 of 34 for this method. That is a
statement about the stored corpora, not a rerun of the pre-registered race.

## Scale (exploratory, `scale_probe.py`)

Five large directories from this project's own repositories, files as programs, witness rule.

| Directory | Files | Bytes | Alphabet | Block rank | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| JavaScript sources | 400 | 3,378,529 | 103 | 103 | 0.9 |
| Zig sources | 400 | 4,451,901 | 116 | 116 | 1.2 |
| C headers | 384 | 1,503,113 | 97 | 97 | 0.5 |
| WGSL shaders | 400 | 2,476,655 | 107 | 107 | 0.7 |
| Python sources | 177 | 1,741,852 | 186 | 186 | 0.6 |

- In all five the block rank equals the alphabet, so the exact minimum is one entry per character.
- Taking the files in a shuffled order, the deficit is already zero at two files, in all five.
- So a deficit is a property of sibling files that share boilerplate, not of large code in general.
- No flow-based method was run at this size. Its graph would hold every eligible occurrence, which is
  hundreds of thousands at 6 KB; the comparison at megabytes is an expectation, not a measurement.

## What this changes, and what it does not

- The test is no longer limited to "+1": it proves rank + 2 and builds rank + 1.
- It removes the one case where another method was needed on outside code (Cairo at 73).
- It does not reach the two high-deficit corpora, where the minimum is far above the rank.
- At scale the interesting answer so far is the plain one: the alphabet is optimal, and a rank computation
  certifies that in about a second, although deciding it is co-NP-complete in the worst case.
