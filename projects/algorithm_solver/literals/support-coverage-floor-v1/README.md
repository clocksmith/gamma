# Item 56: every positive small-support bound has an empty coverage class

2026-10-24 UTC. The accepted [independent report](evidence/REPORT.md) finds a
coverage floor of **three one-owner entries in both original 300-source fit
cohorts**. Items 50 and 53 have positive fraction bounds only at budgets
k=0,1,2. Those budgets cannot cover the sources at all. Their positive fraction
exclusions are therefore **vacuous for covering dictionaries**: the inequalities
remain valid, but they exclude no realizable covering dictionary.

| Cohort | Coverage floor r | Sources containing a private character | Distinct private characters | Sources coverable using all shared entries | Positive 50/53 budgets | Positive budgets not ruled out by coverage |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| R | 3 | 3 | 3 | 297 | 0, 1, 2 | None |
| Naming | 3 | 3 | 3 | 297 | 0, 1, 2 | None |

At k>=3, this floor no longer rules out coverage. It proves neither that a
256-entry covering dictionary exists nor that C/N<=10% is possible. The fraction question remains unresolved there; item 53's next bounds at k=3 are
-393 for R and -6,137 for naming. The floor is not a proof that the minimum
achievable one-owner budget under the capacity constraint is three.

The [design](DRAFT.md) allows all shared entries simultaneously, relaxing the
256-entry capacity. Every source failing shared-only reachability needs a
one-owner entry, and one such entry cannot serve another source. On these
accepted item 50 inputs all 96 paid alphabet singletons are allowed, so the
floor equals the private-character-source count exactly. Forward and backward
reachability independently verify that equality; they cannot provide a stronger
floor on this population.

| Cohort | Source characters | Original pool entries | Shared entries, including singletons | One-owner pool entries | Absent pool entries | Occurrences replayed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R | 76,107 | 308,304 | 308,294 | 3 | 7 | 1,370,583 |
| Naming | 76,033 | 291,196 | 291,186 | 3 | 7 | 1,319,319 |

These are counts in the original item 28 pool. The one-owner pool count is not
the number of one-owner strings in the full substring universe. Shared-pool
completeness is inherited from accepted item 50 for the exact source/pool/ban
hashes; ownership, occurrence ordering and every reachability recurrence are
recomputed. All per-source flags, identities, strings and vectors remain private.

P1 (required identity and independent agreement) and P2 (floor exceeds item
50's largest positive budget in both cohorts) are true. The
[machine-readable result](evidence/results.json) has SHA256
`67e9b08b7ad4515a9dce64624c3bc84c57911fb1a90ceb0899b54a66f08fb12d`.
It retains the aggregate counts, proof/input commitments and complete budget
classification. No positive budget remains after the coverage floor.

[Production supervision](evidence/production-supervisor.json) completed in
4.094459321 seconds and [independent-report supervision](evidence/supervisor.json)
in 6.868958006 seconds, both with actual integer worker exits [0,0] and completed
cleanup. Production worker peaks were 269,680/259,380 KiB (R/naming), and report
peaks were 428,540/411,712 KiB. These are separate per-process peaks. All 43 code
and 20 runtime pins were rehashed unchanged after completion.

Exactly four authorized private files were available: each cohort's original
fit sources and original pool. No q, seed, 400-source carrier, validation or cases
were opened. There were zero new multiplier searches, zero fresh qualification
jobs and zero witness packets. Reuse is limited to original item 13 source-hash
qualification; item 23's later unchanged-source exit 137 remains separate.
No source execution, M1, semantic-reuse, minimum-support, global dual-optimality,
current-best change or promotion claim follows. See the [review](REVIEW.md) for
lineage, bounded execution and the record-only audit.

## 2026-10-24 later cross-record coverage witness: minimum budget exactly three

[Item 59's public-lineage audit](../support-budget-feasibility-v1/README.md)
combines the item 56 lower bound with the existing exact-hash item 13 covering
seeds. Item 50 verifies those 256-entry seeds are subsets of the same old pools;
item 56 finds only three one-owner pool entries. Each seed thus uses at most
three, while the floor forces at least three. **The minimum feasible one-owner
budget under capacity 256 is exactly three**, and the same seeds witness every
at-most-k covering class for k>=3.

This resolves coverage using additional cross-record witness evidence; the
item 56 floor alone still proves only necessity. Earlier floor-only uncertainty
statements are superseded by this later inference. The vacuity at k=0,1,2 is
unchanged. C/N<=10% remains unresolved in the now-known nonempty classes k>=3;
the existing witnesses do not achieve that fraction. No new private read,
packet decode, source execution or qualification was performed.
