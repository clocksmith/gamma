# J/K boundary-repaired qualification lane

This lane holds the five J/K problems whose mandatory review set `independent_references_and_boundaries` to false: 3820, 3821, 3825, 3835 and 3850, each in Python and JavaScript. See the [J/K rejection results](../continuation-jk-rejection-20261028-v1/RESULTS.md). The case set is every original J/K case for those problems plus new boundary cases from [boundary_cases.py](boundary_cases.py). Boundary rows that repeat an original row are dropped.

Each new expected value comes from a method different from the candidates', and no candidate source is read:

| Problem | New cases | Independent expected values |
|---|---|---|
| 3820 | 100,000-node paths and spiders, relabelled and not, with nonzero and zero answers. Includes a true triple that 32-bit squares summed as doubles miss, and a non-triple that consistent 32-bit wraparound counts. Small paths. | Closed-form distances: index differences on a path, and sums through the center of a spider |
| 3821 | Every k from 1 to 50 at n = 1, at C(50,k), at C(49,k) and C(49,k)+1, and at a random n; large n near 2^31, 2^32 and C(50,25) | Least y whose count of k-one numbers at or below y reaches n, by binary search |
| 3825 | Bit 29 as the only shared bit; 100,000-value chains, one with about 20 set bits per value; random 3,000-value arrays weighted toward values of 2^29 and above | Fenwick-tree prefix-maximum longest subsequence per bit, or analytic chains |
| 3835 | 100,000-value spikes forcing multi-step shrinks; alternating values with costs equal to k and k-1 near 5·10^13; increasing values; a 100,000-value valley; random arrays of up to 1,500 values | Closed-form window counts, sparse-table range minimum/maximum with binary search, or quadratic brute force |
| 3850 | Length 19 with real values: uniform arrays with k = 4^19, 4^17, 6^19, 6^17 and 5^19; k = 10^15; random arrays whose k is the product of a random subset, so counts above 1 are common | Per-value net-count combinatorics instead of sign enumeration or meet-in-the-middle |

[test_boundary.py](test_boundary.py) checks each new reference against the cohort's own reference on small inputs, and checks that every case validates and fits the unchanged transport envelope.

The protocol, the verifier, the limits, the observers, the gate, the runtime binding and the review gates are the J/K lane's, restricted to these ten programs. Comparison is exact for all five problems, which all have exact return policies. The lane reuses the existing J/K refetched definitions.

Run on the Linux executor:

```
protocol.py review-template --gate G --gate-sha256 H --review NEW_REVIEW
protocol.py freeze --gate G --gate-sha256 H --statements JK_STATEMENTS --preflight LOG --preflight-sha256 H --review REVIEW --freeze NEW_FREEZE
protocol.py run ... --freeze FREEZE --freeze-sha256 H --output NEW_OUTPUT
protocol.py replay ...
```

Scope: exposed development finite cases only. There is no native wrapper, held-out, adoption or full-domain claim, and this lane changes no catalogue status.
