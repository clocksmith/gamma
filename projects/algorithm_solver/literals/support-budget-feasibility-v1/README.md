# Item 59: minimum feasible one-owner budget is exactly three

2026-10-24 UTC. Combining existing public records establishes that **three is
the minimum one-owner-entry budget for coverage under the 256-entry cap**, for
each original R/naming 300-source fit cohort. This is a cross-record inference,
not another experiment, private-input audit or packet decode.

| Cohort | Existing item 13 seed | Paid entries | Matching fit sources covered/qualified | One-owner entries, inferred | Minimum feasible budget |
| --- | --- | ---: | ---: | ---: | ---: |
| R | control, width 8 | 256 | 300/300 | 3 | 3 |
| Naming | scope_joint, width 8 | 256 | 300/300 | 3 | 3 |

The proof combines three accepted facts:

1. [Item 13](../binding-descent-v1/README.md) records exact decoding and coverage
   of all 300 matching fit sources using each identified 256-entry dictionary.
2. [Item 50](../potential-lift-certificate-v1/README.md) verifies those exact
   dictionary hashes are legal subsets of the original pools, for the same
   source and ban identities. [Item 56](../support-coverage-floor-v1/README.md)
   finds exactly three one-owner entries in each pool. Each seed therefore
   contains at most three one-owner entries.
3. Item 56 proves every covering dictionary needs at least three. The existing
   covering seeds must therefore contain exactly three and attain that floor.

The same seed makes every **at-most-k** class nonempty for k=3,...,256; this is
not a claim about dictionaries containing exactly k one-owner entries. Item 56's
floor alone did not prove sufficiency. The additional upper bound comes from
existing exact-hash covering dictionaries.

Budgets k=0,1,2 remain coverage-infeasible, so the positive fraction exclusions
from items 50 and 53 remain vacuous for covering dictionaries. For k>=3, coverage
is now established, while **C/N<=10% remains unresolved**. The recorded seeds'
fit character fractions are 54.063888% (R) and 49.810101% (naming), well above
10%; their existence establishes coverage, not the fraction target.

The [public-lineage artifact](evidence/public-lineage.json) records 15 exact
public-file hashes, 16 verified existing pin links, aggregate coverage and
qualification counts, and seed/source/pool/ban commitments. Its SHA256 is
`1a126e65656a228110c763900a2981718d9806fa04b7dc46229e19f88a6d5342`.
It contains no source text, dictionary entries, per-source identities or cases.
Root and a separate agent verified the lineage; Claude review was requested
and is not represented here as an approval. See the [review](REVIEW.md).

No new source execution, qualification, private read, dictionary, packet or
multiplier calculation occurred. Original item 13 qualification is reused by
exact source identity; item 23's later unchanged-source exit 137 remains separate.
No M1, semantic-reuse, minimum dictionary-size, global dual-optimum, current-best
change or promotion claim follows. The exact minimum concerns one-owner budget
at capacity 256 on these fixed sources only.
