# Item 71 invented-input measurement: accepted

The single frozen measurement ([spec](SYNTHETIC-SPEC.md), pins `synthetic-spec.json` SHA-256 `359f2ba0…`, commit
`5b9f63639`) ran once on core 6 on 2026-10-24.
- **Supervisor.** Accepted in 423.40 s: 422.59 s of computation and 1.31 s for the 21 oracles. Exit 0, normal cleanup
  0.0002 s.
- **Memory.** The worker's peak RSS was 761,188 KiB.
- **Retention.** [`synthetic-results.json`](synthetic-results.json) (SHA-256 `57f2b471…`) holds the full curves.
  [`synthetic-supervisor.json`](synthetic-supervisor.json) holds the receipt.
- **Agreement.** For both fixtures, all 257 budgets agree independently. Every forward recurrence of 57, 63 and 71 was
  checked, and the fresh 63 baselines equal the accepted item 63 receipt.

| Fixture | Owner endpoints | n < m endpoints | Budgets improved vs 63 | Peak integer gain | k3 bound 63 → 71 | Largest positive k (63 = 71) | Full k256 |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: |
| paired_prefix_75k | 8,653,295 | 0 | 0 | – | 63,143 → 63,143 | 81 | −57,362 (unchanged) |
| repeated_one_owner_12k | 5,994,152 | 5,861,064 (97.8%) | 35 (k = 1–35) | +771 at k = 12 | 29,587 → 29,808 | 4 | −151,368 (unchanged) |

- **paired_prefix_75k is null by construction.** Every owner entry has m ≤ 2 and floor(N/length) ≥ m, so n = m
  everywhere.
- **repeated_one_owner_12k** has highly repeated owner strings (maximum m is 166 and maximum n is 166, taken separately;
  the sum of m − n is 284,046,192). The packing denominator lowers residual caps on 35 small budgets. It does not change the largest
  positive budget or the full-class bound.

**Shows.** The packing-count refinement is implemented and independently checked at invented scale. It improves
owner-priced bounds only where the same owner string repeats far more often than it can be packed without overlap.

**Does not show** anything about the original nine inputs: no corpus runtime, positive full-class bound, coverage
feasibility, witness, readiness or M1 claim. A separate original-input design and freeze would be needed. The global
packing theorem and the item 68 composition are not part of this kernel.

Reviewed by a fresh-context Claude subagent standing in for codex; see [REVIEW.md](REVIEW.md).
