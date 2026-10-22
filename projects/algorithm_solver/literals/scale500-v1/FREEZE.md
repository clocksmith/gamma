# scale500-v1: frozen design

Vocabulary search at scale on the frozen 500 ([population-500.json](../admission500-v1/evidence/population-500.json)),
with shared-style rewrites of the 350 problems outside the first 150 and a held-out slice.
Owner-approved steps 3b and 3c ([MILESTONES.md](../MILESTONES.md#owner-decision-2026-10-22)).
[contract.json](contract.json) pins inputs, budgets, seeds and predictions. It was committed
before any of the 350 rewrites was written and before any arm ran.

## Treatment

One shared-style rewrite per problem for the 350 outside the first 150, under the same procedure
as [style150-v1](../style150-v1/FREEZE.md): [STYLE.md](../style150-v1/STYLE.md), at most 8 parity
checks, one submission, strict parity with the admitted source on all frozen corpus cases,
failures recorded and not replaced. Rewriters see no dictionary or measurement output.

## Sources and arms (each at 128/7 and 256/8)

- P1: the first 150's style150 pool (998 alternatives plus 150 rewrites) and every other
  problem's admitted source. P2: P1 plus the qualified rewrites of the 350.
- W1, W2: matched80-v3 local search on P1, P2 from the style150-v2 D dictionary; 120,000-trial cap.
- I2-s1..s5: seeded iterated local search from W2 (kick 4 at 128, 8 at 256; refill shortlist 24);
  60,000 trials per seed.
- H1, H2: P1, P2 fitted on the 400 training problems only (fallback alphabet, greedy refill, local
  search; 60,000 trials), then measured unchanged on the 100 held-out problems. Held-out split:
  sha256(`scale500-v1-heldout` + id), lowest 100.

The proposer is style150-v2's chosen-source hybrid (3/4 spans, 1/4 designed forms). The safety
limit is 6 hours per arm. Every packet is decoded independently. Every arm reports the M1
metrics on all 500 and per cohort.

## M1 gates (unchanged)

400 of 500; at most 256 entries; median at most 32 and p95 at most 96 selections; at most 10% of
selection bits from single-character entries; zero whole-solution entries; 128/7 and 256/8 compared.

## Predictions

- S1: at 256 entries, W2 uses at least 25% fewer selections than W1 on all 500.
- S2: on the held-out 100 at 256 entries, H2 uses at least 15% fewer selections than H1.
- S3: at least 4 of 5 ILS seeds at 256 entries improve on W2, with spread at most 1% of the median.
- S4: no arm meets M1 (median above 32 on all 500).
- S5: at least 300 of the 350 rewrites qualify.

## Disclosure

The runner was smoke-tested end to end with a 200-trial cap and no rewrites, for plumbing and
timing (about 120 ms per exact trial on Jupiter). Those outputs were discarded. Only the trial
caps were set after that run.
