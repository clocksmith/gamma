# Matched 80, iteration 3: wide polish, seeded search and readable units

Goal v2:2a, compression-first and human-readable policies on separate scorecards. The
design, budgets, seeds and predictions were frozen in [FREEZE.md](FREEZE.md) and
[contract.json](contract.json) at `a24b8c0f3` before any arm ran. Generated tables are in
[RESULTS.md](RESULTS.md); every per-problem count is in [results.json](results.json).

## Outcome (2026-10-22)

All 18 jobs completed on Jupiter in 919 s wall time with 18 jobs in parallel. Trial caps
bound every ILS seed; no arm reached a time limit. Every packet decodes, through the
canonical codec, to its qualified source hash.

### Literal scorecard (80 compact sources, the published BITS cohort)

| Size | Live | Wide search (from v2 polish / from scale-v2) | ILS seeds 1-5 | Best | Change | Package B |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| 8-bit (256) | 6,413 | 6,280 / 6,302 | 6,167, 6,161, 6,163, 6,161, 6,171 | **6,161** (`ils-256-s2`) | **-3.93%** | 11,750 (-0.26%) |
| 7-bit (128) | 9,910 | 9,867 / 9,897 | 9,784, 9,795, 9,784, 9,829, 9,829 | 9,784 (`ils-128-s1`) | -1.27% | 12,709 (-0.70%) |

- **8-bit qualifies for promotion.** Every seed (6,161-6,171) is below the unchanged bar
  of 6,284 selections, and every package (11,750-11,794 bytes) is below 12,370. The seed
  spread is 0.16% of the median, so the result is not a lucky seed. The candidate is
  `ils-256-s2` by the frozen rule (fewest selections, then bytes): dictionary 2,309 B,
  packets 9,441 B. Per problem: min 10, median 60 (live 63), p90 136, max 537. Against
  live, 55 problems improve, 11 tie and 14 get worse; the largest increase is +20 on
  #1046 (517 to 537), and the largest decrease is -19 on #748.
- **7-bit does not qualify.** The best seed is 9,784 (-1.27%) against a bar of 9,711; the
  live 7-bit profile stays.
- The deterministic wide search alone reached a local optimum within 2,335-9,061 trials
  (6,280 at 8 bits, which is just below the bar). The seeded kicks found the rest: 22-24
  of 207-244 kicks per 8-bit seed were accepted.
- Negative or mixed: the hardest programs barely move. #1046 (the hand-written heap) is
  the costliest in every arm and gets worse in the 8-bit candidate. #4, #824 and #976
  follow it, as in iterations 1 and 2. Lower totals come from the middle of the
  distribution, not from the long tail.

### Readable scorecard (readable-units-v1)

Every entry is fallback ASCII, a readable unit from [units.py](units.py) (name, member,
keyword head, statement tail, operator run or indentation run) or, in `units-designed`,
an approved designed piece. The reference is the matched80-v1 designed-only menu.

| Style, size | Designed-only (v1) | Units | Units + designed | Change | Token-aligned (v1 to units + designed) |
| --- | ---: | ---: | ---: | ---: | --- |
| canonical, 128 | 28,607 | 16,346 | 16,167 | -43.5% | 40.4% to 66.6% |
| canonical, 256 | 25,720 | 11,201 | 9,705 | -62.3% | 41.4% to 87.3% |
| compact, 128 | 11,794 | 10,484 | 9,974 | -15.4% | 67.2% to 79.0% |
| compact, 256 | 11,593 | 9,170 | 8,167 | -29.6% | 68.0% to 88.3% |

- Finer units are the missing readable vocabulary that iteration 1 identified. The
  admitted entries start with `value`, `    `, `index`, `) {\n`, `const `, ` = `,
  `return ` (canonical) and `const `, `function `, `return `, `.length`, `let `, `){`
  (compact). Designed pieces still add value on top of units at every style and size.
- The readable result costs more than compression: compact 256 at 8,167 selections is
  27% above the live literal 8-bit profile (6,413). No joint80 readable slot is live, and
  under the empty-slot rule a first readable profile would need fewer than 57,717 total
  presses; no readable arm meets it (best: 8,167 x 9 = 73,503). Nothing readable is
  promoted.
- Negative: readable polish found no improving move after the learner in 6 of 8 arms,
  and found 4 and 1 moves in canonical 256 and compact 256 (units + designed). The pools
  are small (171-288 candidates). The compact 256 arms stop at 221 and 234 entries with
  free slots, because no remaining unit has a positive measured gain. A larger readable
  result needs new unit classes, not more search.
- Context, not a same-slot comparison: canonical units + designed at 256 (9,705) uses
  fewer selections than the iteration 1 mined canonical arm (10,906). That mined arm used
  the weaker shared ranking, so this does not show that readable units beat mining.

### Predictions

All seven held: L1 (wide search beats its start), L2 (8-bit bar met), L3 (at least 4 of
5 seeds improve; spread 0.46% at 128 and 0.16% at 256), L4 (starts within 1%), R1, R2 and
R3.

## Promotion

The 8-bit candidate meets [BITS_PROMOTION.md](../BITS_PROMOTION.md)'s selection and
package rules. It is packaged and independently verified in
[guides-joint80-8-v2](../guides-joint80-8-v2/README.md) as `bits-literal-joint80-8-v2`
(superseding `bits-literal-joint80-8-v1`). BITS export, focused BITS checks and
deployment remain separate steps.

It is an improved representation of the same 80 already-published, qualified compact
programs: not broader problem coverage, autonomous solving, human fluency or
generalization. All 80 problems are exposed development material.

## Reproduce

```sh
python3 -B -m unittest test_run -v
python3 -B run.py --output run-v1 --parallel 18
python3 -B report.py
```
