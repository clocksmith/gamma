# Matched 80, iteration 2: ranking and shortlist width

Goal v2:2a/2b. Frozen in [contract.json](contract.json) before any arm ran; it pins
this runner, its tests, [BITS_PROMOTION.md](../BITS_PROMOTION.md) and the
[matched80-v1](../matched80-v1/README.md) runner and contract, whose inputs it reuses.

## Why

Iteration 1 found that the shortlist ranking it froze for pool comparability is
weaker than scale-v2's own, so no arm beat the live BITS joint80 profiles (6,413
selections at 8 bits, 10,155 at 7 bits), and that adding designed pieces helped by
1.6-5.6% under equal ranking. Both scale-v2 runs also used nearly all 2,200 trials.

## Arms (80 compact sources)

| Arm | Candidate source | Shortlist | Trial cap |
| --- | --- | ---: | ---: |
| span-12 | scale-v2 order (control: should reproduce stored results) | 12 | 2,200 |
| span-48, span-192 | scale-v2 order | 48, 192 | 8,800, 35,200 |
| hybrid-12/48/192 | 3/4 scale-v2 order + 1/4 designed compact pieces | 12, 48, 192 | as span |
| polish-128, polish-256 | joint-v1 improve() from each size's best fixed arm | - | 1,200 per start |

Each fixed trajectory yields 128- and 256-entry snapshots. Everything else (charged
ASCII fallback, admission, swaps, codec verification, scoring) is matched80-v1's.
Compute grows with shortlist width and is reported, not equalized.

## Predictions

1. span-12 reproduces 10,155 and 6,413 exactly.
2. Wider shortlists use fewer selections than span-12.
3. Hybrid uses no more selections than span at the same width.

A result reaches BITS only through [BITS_PROMOTION.md](../BITS_PROMOTION.md): at least
2% fewer selections than the live profile, package bytes at most 5% higher, a verified
guide package and passing BITS checks.

## Outcome (2026-10-21)

All 8 jobs completed on Mars in 136 s; no arm reached its time limit; every packet
decodes to its qualified source hash ([RESULTS.md](RESULTS.md)).

1. **Holds.** span-12 reproduces 10,155 and 6,413 exactly.
2. **Mostly fails.** Wider shortlists change nothing at 128 entries and save at most
   8 selections (0.12%) at 256, at up to 16x the trials.
3. **Holds.** The designed hybrid beats span at every width: 10,034 vs 10,155 at 128
   (-1.2%) and 6,361-6,368 vs 6,405-6,413 at 256 (-0.7 to -0.8%).

The joint polish from each size's best fixed arm reaches **9,910 selections at
7 bits** (-2.41%, package -1.57%; all 80 compact sources are the ones already
published) and 6,360 at 8 bits (-0.83%). Under [BITS_PROMOTION.md](../BITS_PROMOTION.md)
the 7-bit result qualifies to replace `bits-literal-joint80-7-v1`; the 8-bit result
does not reach the 2% bar, so the live 8-bit profile stays.

## Reproduce

```sh
python3 -B -m unittest test_run -v
python3 -B run.py --output run-v1
```
