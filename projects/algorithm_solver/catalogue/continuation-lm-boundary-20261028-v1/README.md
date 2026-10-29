# L/M boundary-repaired qualification lane

This lane holds the eleven L/M problems whose independent review found case-set gaps: 3855, 3859, 3862 and 3869 from L, and 3872, 3873, 3876, 3877, 3878, 3881 and 3885 from M, each in Python and JavaScript (22 programs). The case set is every original L/M case for those problems plus new boundary cases from [boundary_cases.py](boundary_cases.py). Boundary rows that repeat an original row are dropped.

Each new expected value comes from a method different from the cohort's reference, and no candidate source is read:

| Problem | New cases | Independent expected values |
|---|---|---|
| 3855 | 485: every (l, r) at k = 5, 10 and 10^9 plus two random k; seven digit ranges, including c > 1, at 31 k values from 6 to 10^9 (2^29, primes, 10^9-1) | Block-concatenation doubling of (total, count, 10^length), not the repunit-times-inverse-of-9 formula |
| 3859 | 59: 100,000-value arrays with 50,000 distinct pairs, a 100,000-value permutation, random arrays over 50 to 100,000 values, a 20,000-value period repeated five times; k up to 100,000 and m up to 100; 40 random arrays of 200 to 2,000 values | Left-end sweep: the window must end before the (k+1)-th distinct value's first position and at or after each of the first k values' m-th occurrence (segment tree over first occurrences) |
| 3862 | 35: planted balances with left sums of 2^31, 5·10^13 and about 10^14 and products above 2^31; a left sum of 2^32+6 against a product of 6 (int32 wraparound would match); near misses of ±1; huge suffix products; 30 random planted balances | Construction, confirmed by a right-to-left exact scan that stops once the suffix product exceeds the total |
| 3869 | 247: [1, 10^15], [1, 10^k], whole digit lengths, windows across powers of ten, windows of width 101 to 10^9 around 40 monotone numbers of 6 to 10 digits, 40 random windows spanning digit lengths | Inclusion-exclusion counts of digit sums plus explicit enumeration of monotone numbers |
| 3872 | 43: thirteen 100,000-value arrays (one or two changed elements in a long progression, odd and even interior joins, zigzags, values 1 to 3, block-structured progressions) and 30 smaller block arrays | Two-pointer window feasibility over difference-change positions, not run extension |
| 3873 | 42: 100,000 points as constructed components (40k/30k/20k/10k, two halves, 99,999+1, 50,000 pairs, many random sizes, three thirds), a staircase, a 316×316 grid with singletons, four random row/column pools; 30 random grids | Constructed component sizes, confirmed by breadth-first search on the bipartite row/column graph |
| 3876 | 49: 100,000 distinct values with an odd or even minimum, one odd that is or is not the minimum, mixed halves, random samples from 1 to 10^9; 40 small arrays | Closed form: all even, or the minimum is odd |
| 3877 | 21: n = 40 with values up to 10,000, reachable and unreachable targets, zeros, powers of two, a restricted span; n = 19, 21, 33 and 39 | Meet in the middle over explicit subset enumerations of each half, not a DP over XOR states |
| 3878 | 38: eight 100,000-value arrays (random to 10^9, values 0 to 7, submasks of five masks, nested low-bit masks, mostly zeros, single bits, 2^29 plus low bits); 30 mixed arrays of 100 to 3,000 values | Each window counted at its leftmost maximum: every value must be a submask of that maximum |
| 3881 | 195: n = 100,000, 99,999, 65,537, 50,001 and 1,000 at nine k each; 150 random (n, pos, k) with n from 17 to 100,000 | Exact integer binomial 2·C(n-1, k) reduced afterwards, not modular inverses |
| 3885 | 47: traces of 50,000 events and calls; the domain maximum of 100,000 events and 100,000 calls; priorities 1 to 3 for ties; an update-heavy trace; drains followed by empty polls; consecutive ids with reused priorities; 40 small traces. Updates include the same priority, an earlier priority and the current top priority | A segment tree over compressed ids holding (priority, -id), not the active-event scan |

[test_boundary.py](test_boundary.py) checks each new reference against the cohort's own reference on small inputs. Its plumbing tests check that every case validates against the cohort's domain check, that the original cases are all kept, that every batch fits the unchanged transport envelope, and that the limits, argv, batch policy and review flags equal the L/M lane's.

**Totals:** 2,750 distinct cases per language, 1,261 of them new, in 188 batches per language with no transport blockers. The largest planned input is 4,971,752 bytes and the largest projected output is 12,481,302 bytes, both from the domain-maximum 3885 trace. Every 100,000-element boundary row is declared isolated, so the large-repeat policy never runs a heavy row twice inside one 3-second batch.

**CPU estimate.** I wrote my own correct programs, not candidates: an O(n log n) heap EventManager, an O(n log n) segment-tree count for 3859, an O(31n) count for 3878, union-find for 3873 and an O(n) run solution for 3872. I ran them on every isolated heavy row through the lane's observers on a Mac with `node --jitless --single-threaded --max-old-space-size=256` and `python3 -I -S`. All results matched.

| Program | Heaviest row | CPU used |
|---|---|---|
| JavaScript 3885 | 100,000-event, 100,000-call trace | 1.19 s |
| JavaScript 3859, 3878, 3873, 3872 | Each problem's heaviest row | 0.52 s or less |
| Python 3859 | Heaviest row | 1.36 s |
| Python 3878 | Heaviest row | 1.02 s |
| Python 3885 | Domain-maximum trace | 0.95 s |

My estimate is that an O(n log n) or better correct program needs about 40% to 45% of the 3-second limit on its heaviest row. The Linux executor's speed relative to this Mac has not been measured. The 3885 domain-maximum trace has the least margin.

**Owner check for M.** The L/M comparison is unchanged, including the M owner's `matches` recheck. That recheck now uses this module's owner. It recomputes with the M cohort's reference and falls back to this lane's independent reference only where the cohort reference refuses an input as over its budget. Problem 3885 still goes through the M cohort's unchanged `native_protocol.py`.

**Two balanced indices (3862).** The review asked for a case with two balanced indices, but the domain cannot produce one. Every value is at least 1, so the left sum strictly increases with the index and the suffix product never increases. At most one index can balance, so a largest-index program agrees with a smallest-index program on every valid input. The new cases instead target the int32 left-sum and large-product gaps.

The protocol, the verifier, the limits, the observers, the gate, the native 3885 route and native review flags, the transport and the batch policy are the L/M lane's, restricted to these 22 programs. Review bindings name `boundary_cases.py` as the reference and case generator. The host builds all cases in about 50 seconds.

Run on the Linux executor:

```
protocol.py prepare --gate G --gate-sha256 H --statements NEW_DIR
protocol.py review-template --gate G --gate-sha256 H --review NEW_REVIEW
protocol.py freeze --gate G --gate-sha256 H --statements DIR --preflight LOG --preflight-sha256 H --review REVIEW --freeze NEW_FREEZE
protocol.py run ... --freeze FREEZE --freeze-sha256 H --output NEW_OUTPUT
protocol.py replay ...
```

Scope: exposed development finite cases only. There is no held-out, adoption or full-domain claim, and this lane changes no catalogue status. No candidate has been executed for this lane.
