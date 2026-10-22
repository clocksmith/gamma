# Matched 80, iteration 3: frozen design

Goal v2:2a, with compression-first and human-readable policies kept as separate
scorecards. [contract.json](contract.json) pins every input by SHA-256 and states every
budget, seed and rule; this page summarizes it. It was committed before any arm ran.
Results will be added in a separate commit (README.md, RESULTS.md, results.json, run-v1/).

## Why

[matched80-v2](../matched80-v2/README.md) reached 9,910 selections at 7 bits (promoted)
and 6,360 at 8 bits (-0.83%, not promoted). Its polish tested a small neighborhood
(12 additions, 4 removals, about 500 trials) and stopped at the first round without
improvement. [matched80-v1](../matched80-v1/README.md) found that a designed-only
readable menu spells out names (`result`, `items`, `values`) and statement tails
(`) {`, `];`) one character at a time.

## Literal scorecard (compression policy, 80 compact sources)

The 80 compact sources are the published BITS joint80 cohort. Only compact sources are
searched: every v1/v2 joint arm chose compact for all 80 problems, and a compact-only
trial is about 4.6x cheaper. Codec, fallback, scoring and verification are matched80-v1's.

| Arm | Start | Search | Trial cap per run |
| --- | --- | --- | ---: |
| wide-v2polish-128/256 | v2 polish result (9,910 / 6,360) | deterministic local search | 600,000 |
| wide-scalev2-128/256 | scale-v2 compact marginal (10,155 / 6,413, the live 8-bit) | same | 600,000 |
| ils-128/256-s1..s5 | better wide arm of that size | seeded iterated local search, seeds 1-5 | 400,000 per seed |

Local search round: exact deletion harm of every learned entry, exact gain of 96
hybrid additions (3/4 joint-v1 span order, 1/4 designed pieces ranked by the v1
estimator), then exact tests of the 500 best-estimated swaps and the 150 best-estimated
double swaps (16 additions, 8 lowest-harm removals). The best exact (selections, package
bytes) improvement is accepted; a round without one ends the search. ILS kicks remove 4
(128) or 8 (256) learned entries chosen by `random.Random(seed)`, refill greedily from a
24-entry shortlist, search again and keep only improvements.

## Readable scorecard (readable-units-v1)

Every non-fallback entry must be a unit from [units.py](units.py) (name, member name,
keyword head, statement tail, operator run or indentation run; witnessed in at least two
problems of that style; at most 32 bytes) or, in pool `units-designed`, an approved
matched80-v1 designed piece. No mined fragment is admitted; the runner asserts this on
every final dictionary. Arms: pools `units` and `units-designed` x canonical and compact
x 128 and 256. Each style/pool runs the matched80-v1 learner (shortlist 48, 8,800
trials), then each size is polished with readable candidates only (100,000 trials).
Reference: the matched80-v1 designed-only arm of the same style and size. Also reported:
the token-aligned selection fraction (selections that do not split a name, number,
string or multi-character operator).

## Accounting and reporting

Package bytes = LTD1 dictionary + every LTV1 packet with its 41-byte header, reported as
dictionary, packets and total; the shared decoder is unchanged and listed separately.
Every arm reports per-problem min / median / p90 / max and per-problem deltas against its
reference (better / same / worse, largest increase). All seeds are reported with
min / median / max. Trial caps bind; time limits (5,400 s) are safety limits and are
flagged if reached. Children run with `PYTHONHASHSEED=0`.

## Predictions

- L1: wide-v2polish beats its start at both sizes.
- L2: the best 8-bit literal arm meets the unchanged 8-bit bar.
- L3: at each size, at least 4 of 5 seeds improve on their start, with spread at most 1% of the median.
- L4: at each size, wide-scalev2 ends within 1% of wide-v2polish.
- R1: units-designed uses fewer selections than designed-only at each style and size.
- R2: units-designed uses no more selections than units at each style and size.
- R3: units-designed is more token-aligned than designed-only at each style and size.

## Promotion (unchanged [BITS_PROMOTION.md](../BITS_PROMOTION.md))

Per size the candidate is the literal arm (wide or any seed) with the fewest selections,
then package bytes, then name; every seed is reported. 8-bit: at most 6,284 selections and
12,370 package bytes. 7-bit: at most 9,711 selections and 13,437 package bytes. A
qualifying result still needs an independently verified guide package and passing BITS
checks. No joint80 readable slot is live; the empty-slot rule (fewer total presses than
6,413 x 9 = 57,717) is reported, not relaxed.

## Disclosure

Before freezing, the runner was smoke-tested end to end with 800-trial caps (and 200/300
for readable arms) in a scratch directory to check plumbing and timing (about 3 ms per
exact trial on Mars, 1.5 ms on Jupiter). Those outputs are not results and were
discarded; no budget or rule was changed after that smoke run.

## Reproduce

```sh
python3 -B -m unittest test_run -v
python3 -B run.py --output run-v1 --parallel 18
python3 -B report.py
```
