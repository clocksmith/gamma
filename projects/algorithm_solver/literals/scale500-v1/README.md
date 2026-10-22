# scale500-v1: vocabulary search at scale on the frozen 500

Frozen design: [FREEZE.md](FREEZE.md) and [contract.json](contract.json) (commit `2a6d77b80`,
before any of the 350 rewrites was written and before any arm ran). Public evidence:
[evidence/results.json](evidence/results.json), written by [evidence.py](evidence.py). It holds
per-arm aggregates, per-cohort and held-out M1 metrics, per-problem counts, dictionary and
manifest hashes, and the rewrite qualification rows. Sources, cases, dictionaries and sequences
stay private. All 18 arms ran on Jupiter in 6,897 s with no amendment.

## Result

The best representation of the frozen 500 is ILS seed 4 at 256 entries / 8 bits. It uses
**43,065 selections**, median **63.5**, p95 **191**, worst 933, and **54.2%** single-character
selections, in 65,951 package bytes. **M1 is not met.** Median and p95 are about twice the 32
and 96 gates, and the single-character fraction is five times the 10% gate. 77 of 500
programs are within 32 selections and 362 are within 96. No dictionary in any arm contains a
whole-program literal, and none contains an entry that is a near-whole copy of one program.

| Arm, 256 entries / 8 bits | Sources | Selections | Median | p95 | Single-char | Bytes / selection | Package bytes | Trials, stop |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| W1 | P1: 350 admitted sources | 128,877 | 199 | 626 | 51.6% | 2.67 | 151,496 | 68,857, local optimum |
| W2 | P2: + 350 rewrites | 43,436 | 64 | 194 | 54.3% | 2.97 | 66,580 | 24,463, local optimum |
| I2-s1..s5 | P2, ILS from W2 | 43,065–43,165 | 63–64 | 191–193 | 53.9–54.5% | 2.98 | 65,951–66,044 | 60,000 each, trial cap |
| H1 (fit on 400) | P1 | 130,299 | 199 | 613 | 50.5% | 2.64 | 152,779 | 8,446, local optimum |
| H2 (fit on 400) | P2 | 44,676 | 65.5 | 202 | 54.6% | 2.88 | 67,351 | 10,233, local optimum |

| Arm, 128 entries / 7 bits | Selections | Median | p95 | Single-char | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| W1 | 210,253 | 318.5 | 1,034 | 80.0% | 205,468 |
| W2 | 69,845 | 104 | 319 | 77.3% | 82,658 |
| I2-s1..s5 | 69,410–69,428 | 103.5 | 315–319 | 77.3% | 82,282–82,292 |
| H1 | 212,286 | 322.5 | 1,027 | 80.2% | 207,239 |
| H2 | 70,277 | 107 | 318 | 78.8% | 83,031 |

Eight bits remains the cheaper input. W2 needs 347,488 selection bits at 8 bits against
488,915 at 7. Every packet in every arm (500 per arm) was decoded independently through the
canonical codec to its qualified source hash.

## What the gain is made of (read before citing −66%)

W2 needs 66.3% fewer selections than W1. Most of that comes from shorter sources, not from
denser selections. The 350 admitted sources total 313,146 bytes and their rewrites 97,703, so
the chosen text falls from 343,907 to 128,883 bytes (−62.5%). Bytes per selection rise only
from 2.67 to 2.97 (+11%), and the single-character fraction does not fall (51.6% to 54.3%).
The first 150 already had compact alternatives in their pool. On that cohort, W2 needs 39.6%
fewer selections than W1 (9,849 vs 16,304; 148 of 150 programs improve). Their source pools are
the same in both arms, so this reduction comes from the dictionary no longer being spent on
the verbose 350.

So this run does not separate shared style from plain compaction for the 350. A successor
that wants that attribution needs a compaction-only control: the admitted sources minified
without the style rules, under the same parity gate.

By cohort at 256 (W2): first-150 9,849 (median 58.5), admitted-213 20,900 (median 75),
gap-137 12,687 (median 56). Sharing a dictionary with the other 350 costs the first 150 about
5%: style150-v2 D, fitted on the 150 alone, reached 9,337.

## Held-out measure

H1 and H2 fit their dictionaries on the 400 training problems only, starting from the fallback
alphabet, and are measured unchanged on the 100 held-out problems (sha256 split, seed
`scale500-v1-heldout`).

| 100 held-out problems, 256 entries | Fitted without them (H) | Fitted with them (W) | Cost of not having seen them |
| --- | ---: | ---: | ---: |
| P1 | 27,161 | 26,781 | +1.4% |
| P2 | 9,526 | 9,277 | +2.7% |

At 128 entries the costs are +1.7% (P1) and +0.4% (P2). With 400 training programs, the
dictionary carries over to the unseen 100 almost without loss. On the 30 held out of 150 in
[style150-v2](../style150-v2/README.md), unseen programs cost about a fifth more. The H arms
also start from the alphabet rather than from the style150-v2 dictionary, and they stop at a
local optimum in fewer trials. Their totals on all 500 still land within 1.1% (P1) and 2.9%
(P2) of the W arms. These held-out programs are exposed development data: their rewrites were
written in this experiment, and the split holds them out of dictionary fitting only. This is
not unseen solving.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| S1 | W2 at least 25% below W1 on all 500 (256) | **Met**: −66.3% (43,436 vs 128,877); mostly shorter sources, see above |
| S2 | H2 at least 15% below H1 on the held-out 100 (256) | **Met**: −64.9% (9,526 vs 27,161) |
| S3 | at least 4 of 5 ILS seeds improve on W2 (256), spread at most 1% | **Met**: 5 of 5, best −0.85%, spread 0.23% |
| S4 | no arm meets M1 | **Met**: best median 63 |
| S5 | at least 300 of 350 rewrites qualify | **Met**: 350 |

ILS adds less than 1% at either width. At 128 entries the five seeds converge to two
dictionaries: seeds 1, 3 and 5 reach 69,428, and seeds 2 and 4 reach 69,410. Every ILS arm used
its full 60,000 trials. Every W and H arm stopped at a local optimum below its cap.

## Rewrites

All 350 rewrites qualify on every frozen corpus case, with strict parity against the admitted
source. They used 356 parity checks: 346 passed on the first check and none needed more than
3. The rewrites total 97,703 bytes, against 313,146 for the admitted sources.
Rewriters reported these deviations:
- #1099 replaces a hand-written heapsort with the built-in sort.
- #1015 keeps `i+=1` (`i++` measured slower under `--jitless`).
- #1464 and #1748 drop domain checks after parity confirmed them.
Each rewrite is listed by hash in the evidence.

## Distance to M1 and next

Gates against the best arm:
- Median: 32 vs 63.5.
- p95: 96 vs 191.
- Single-character selection bits: 10% vs 54%.
- Per program: 77 of 500 need at most 32 selections and 362 need at most 96.

At 256 literal entries, about 3 bytes per selection is where this search settles on every
pool. More search does not move it (ILS adds less than 1%). The remaining gap would need a
different representation, not more trials on this one.

Not claimed: M1, autonomous assembly, unseen solving, or a BITS profile. A BITS candidate
would need [BITS_PROMOTION.md](../BITS_PROMOTION.md) on its own 500-problem primitive slot,
with a guide package and a deploy receipt.
