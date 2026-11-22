# Results: the deficit ladder

Run on 2026-11-22 (UTC) by `claude-bits-1`. **Not pre-registered.** The ladder was written after the unseen
race of `capacity-deficit-race-v1` had been scored, so all 59 corpora below had been seen by then. Everything
here is checked against exhaustive search, replayed dictionaries or independently verified certificates, but
none of it is a prediction that could have failed on fresh data.

**The ladder proves bounds past rank + 1 as trees that a separate checker of about 120 lines accepts. On the 59 real
corpora it settles the same 56 as the level-1 method, and it tightens all three that stay open.**

## Against exhaustive search (`audit_ladder.py`, seeds 1 and 2, levels up to 3)

| Minimum | Checks | Exact |
| --- | ---: | ---: |
| rank | 8,912 | 8,912 |
| rank + 1 | 3,361 | 3,359 |
| rank + 2 | 1,149 | 849 |
| rank + 3 | 373 | 72 |
| rank + 4 | 1 | 0 |
| **All** | **13,796** | **13,192** |

- No lower bound above the true minimum and no illegal dictionary, in 13,796 checks under both rules.
- 367 certificates were emitted under the witness rule; the independent checker accepted all of them and each
  certified bound was at most the true minimum.
- The inexact cases stop at a fixed-space search that finds fragments covering every free occurrence but
  cannot show whether the single characters around them can be thinned. Unions of independent hard pieces are
  the typical example.

## On the 59 real corpora (`real_corpora.py`, 300 seconds each, three at a time)

Witness rule, threshold 2, 160-byte cap. Every dictionary is replayed with the capped checker of
`capacity-boundary-v1`.

| What settles the minimum | Corpora |
| --- | ---: |
| Rank equals the alphabet | 38 |
| A dictionary of rank entries is built | 15 |
| Rank is ruled out by a certificate, and rank + 1 is built | 3 |
| Open | 3 |

The three settled above the rank each come with a one-node certificate: JS-2 (65), the Cairo headers (73) and
A15 (79), in 0.7, 1.7 and 0.2 seconds.

The three open ones:

| Corpus | Rank | Level-1 method | Ladder | Certificate | Other evidence |
| --- | ---: | --- | --- | --- | --- |
| A08 (three.js, 6 files) | 67 | 69 to 73 | **71 to 72** | 12 nodes, 12 KB, checked in 2 s | The Lagrangian baseline also stops at 69 |
| PY-3 | 51 | 53 to 68 | **55** to 68 | 4,141 nodes, checked; too large to store, its SHA-256 is in `real-corpora.json` | A 62-entry dictionary from another method replays, so 55 to 62 |
| B04 | 22 | 23 to 65 | **25** to 65 | 86 nodes, 121 KB, checked | The baseline's bound is 30 and a 60-entry dictionary is known |

- **A08** is the clearest gain. Levels 0 to 3 are refuted by a tree of 12 nodes with no search at all, and a
  72-entry dictionary is built. Both earlier methods left 69 to 73.
- **B04** shows the limit. Its minimum is far above its rank, the tree needs one level per entry, and at one
  position 1,512 spaces arise. The linear-program bound of the baseline is better there.
- No new corpus became exact: the level-1 method already settled the same 56.

## What the certificates buy

Before this, a refutation above the rank rested on a search that had to be trusted or rerun. A defect tree is
data: `check_certificate.py` recomputes blocks, rank and eligible entries with the code of
`capacity-boundary-v1`, redoes the arithmetic, and accepts or rejects. It rejects a changed kernel entry, a
dropped kernel row, a dropped child and a tree that claims one level more than it proves.

## Limits

- Times are single runs with three corpora at a time, not benchmarks.
- A bound marked "defect tree and search" in `real-corpora.json` is not a certificate.
- Whether a small tree exists is not predicted by anything here.
- The exhaustive audit covers levels up to 3 on corpora of a few short words. Deeper trees on real corpora
  rest on the theorem and on the checker, not on comparison with a known minimum.
