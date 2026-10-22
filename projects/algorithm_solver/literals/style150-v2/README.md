# style150-v2: the style150 search arms with chosen-source proposals

Frozen design: [FREEZE.md](FREEZE.md), [contract.json](contract.json) (commit `172f9868d`, plus
the disclosed plumbing amendment `862b53d87`, before any arm ran). Public evidence:
[evidence/results.json](evidence/results.json). The single change from
[style150-v1](../style150-v1/README.md) is that candidate spans are scored on each problem's
chosen source only.

## Result

With the proposer fixed, the joint arm D (existing pool plus the 150 shared-style rewrites)
is the best representation of these 150 known programs: **9,337 eight-bit selections**,
median **53.5**, p95 **141**, **51.6%** single-character selections, **18,847** package bytes.
The previous best before style150 was 12,337, median 74, p95 198, 58.1% and 22,296 bytes:
that is 24.3% fewer selections and 15.5% fewer bytes. The rewrites-only arm E is unchanged
from v1 (9,538, 18,091 bytes; one source per problem, so the proposer change cannot affect
it) and stays the smaller-storage alternative.

| Arm, 256 entries / 8 bits | Selections | Median | p95 | Single-char | Package bytes | Style sources chosen | Trials |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C: existing pool | 11,490 | 64.5 | 192 | 54.0% | 21,065 | 0 | 21,745 |
| **D: pool + rewrites** | **9,337** | **53.5** | **141** | 51.6% | 18,847 | 135 | 38,897 |
| E: rewrites only | 9,538 | 55 | 151 | **50.1%** | **18,091** | 150 | 47,615 |
| CH: existing pool, fitted on 120 | 12,348 | 71.5 | 202 | 52.3% | 20,624 | 0 | 10,382 |
| DH: pool + rewrites, fitted on 120 | 10,033 | 56.5 | 171 | 53.2% | 18,435 | 145 | 12,095 |

| Arm, 128 entries / 7 bits | Selections | Median | p95 | Single-char | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| C | 19,559 | 115 | 283 | 77.0% | 24,483 |
| D | 16,284 | 91.5 | 249 | 77.0% | 21,509 |
| E | 16,577 | 94.5 | 242 | 77.0% | 21,558 |
| CH | 20,049 | 115 | 289 | 78.4% | 24,574 |
| DH | 16,374 | 92 | 239 | 77.9% | 21,376 |

Per problem, D against C at 256 entries: 119 programs need fewer selections, 7 the same and
24 more (median −7, range −154 to +25); [evidence/results.json](evidence/results.json) has every
count. Every packet in every arm decodes independently, through the canonical codec,
to a qualified source hash. All searches stopped at a local optimum, below the 100,000-trial cap.

## Held-out measure

CH and DH fit their dictionaries on the 120 training problems only, starting from the fallback
alphabet, and are measured unchanged on the 30 held-out problems:

| 30 held-out problems, 256 entries | Fitted without them | Fitted with them (C or D) | Cost of not having seen them |
| --- | ---: | ---: | ---: |
| Existing pool | 2,627 (CH) | 2,210 (C) | +18.9% |
| Pool + rewrites | 2,276 (DH) | 1,843 (D) | +23.5% |

The shared style still helps on programs the dictionary never saw: DH needs 13.4% fewer
held-out selections than CH. Unseen programs cost about a fifth more selections than fitted
ones. These held-out programs are exposed development data (their rewrites were written in this
experiment). The split holds them out of dictionary fitting, not out of the corpus; this is not
unseen solving.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| Q1 | D no more than E (256) | **Met**: 9,337 vs 9,538 |
| Q2 | D at least 10% below C (256) | **Met**: −18.7% (9,337 vs 11,490) |
| Q3 | DH at least 10% below CH on the held-out 30 (256) | **Met**: −13.4% (2,276 vs 2,627) |
| Q4 | CH and DH above 128 entries (256) | **Met**: both 256 |
| Q5 | D below v1's E (256) | **Met**: 9,337 vs 9,538 |

The fixed proposer also improves the existing pool alone: C moves from 12,334 (v1) to 11,490.
Part of style150's gain is therefore better search, not style. The style effect at matched
search is D against C: −18.7%.

## Distance to M1

On these 150 known programs, D's median of 53.5 and p95 of 141 are still above M1's 32 and 96,
and 51.6% single-character selections is far above 10%. M1 is measured only on the frozen 500
([admission500-v1](../admission500-v1/README.md)). Next, the at-scale vocabulary search on the 500
uses this proposer, with the rewrites as source alternatives for the first 150.
