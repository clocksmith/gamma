# 42: Proposed execution freeze (unbound draft)

2026-10-23. Not active. Root and Claude review plus an explicitly activated
contract are required before any private input access. This proposed freeze
selects the exact method proved in [DRAFT.md](DRAFT.md).

## Named target and inputs

Two independent fixed-300-fit questions: original R and item-13 naming sources,
each bound to item 35's source hashes, exact global bans, full substring pool,
and sealed final length-binned multipliers. Capacity is at most 256 paid entries,
including any singleton; there is no implicit fallback. No validation or
held-out source, private case, source alternative, new witness, or qualification
is accessed or generated. No source contents, entry keys, q arrays, or path
strings are public outputs.

The target is existence of encodings with aggregate F=10C-N <=0, arithmetic
even-population median N<=32, and nearest-rank p95 N<=96 **on these same 300
sources**. Positive independently verified bounds exclude only this joint
fixed-300 target. They exclude neither the 400-program M1 target nor any
500-program target. The 150/285 fit counts are not necessary conditions for
those larger populations, and validation F can offset fit F.

N counts dictionary selections (path edges), excluding Finish. Total actions
are N+1 per program; the corresponding action median/p95 limits would be
33/97. All caps below are selection caps; no threshold is changed.

## Fixed computation

For each cohort evaluate, in order, scales 0, 1/4, 1/2, 1, 2, 4 of item-35 q,
using exact integer floor and its unchanged denominator. No data-adaptive
choice, search, restart, truncation, scale omission, or silent fallback occurs.
Compute the same exact top-256 dictionary term as item 35 at each scaled q.
Compute unrestricted shortest-path costs and exact minimum costs at every
selection cap 1..96 with rolling cardinality layers and heap window minima.

For each a=1..32 solve the exact integer four-category assignment with caps
a,64-a,96,unrestricted and quotas 150,1,134,15. Retain all assignments and
integer dual potentials. The smallest case cost minus the dictionary term is
the bound numerator; ceiling division by D gives the integer F lower bound.
Retain the strongest of the six complete conditional bounds per cohort, with
earliest scale winning ties. No upper bound or gap to the generally
quantile-infeasible item-35 seed is computed.

Separately report the necessary three-class diagnostic (caps32/96/unrestricted,
quotas150/135/15) using exact capped costs and an exact integer assignment.
It is weaker than the exact median union and cannot replace the main bound.
The finite-penalty synthetic option is not a production arm.

## Independent verification and failure policy

Replay verifies all source/q/code/runtime hashes, source qualification bindings,
fit identities, all full-pool pieces and their multiplicities, exact bans,
dictionary top capacity, and the item-35 scale-one unrestricted certificate.
It recomputes every capped cost using a segment tree over the previous
cardinality layer, independently of the production heap. It verifies every
assignment's exact quotas and total, integer dual feasibility, and equality
of primal and dual objectives. Infeasible median cases require an independently
verified Hall cut: for one of the 15 nonempty subsets of four categories, its
total quota exceeds the number of programs with a finite cost in any category
in that subset. A program with no finite category is covered by the all-category
cut. Cases are never silently skipped. If all 32 cases are infeasible, that
certifies an empty quantile-feasible relaxed path family, reported separately
from a finite positive F bound, with no invented infinite numerical value.

All twelve points and both cohorts must complete and replay to publish a
complete result. Any timeout, input mismatch, uncovered full pool, invalid
assignment, missing point, or verifier failure retains a failure receipt and
produces no accepted overall certificate. Partial values may be retained
privately, not promoted. Reporting must overwrite any stale successful report
with an explicit incomplete/no-verdict result on failure.

## Proposed resource contract

Production: two cohort workers, R core4 and naming core5, one core and 8 GiB
address-space limit per process; whole-job wall cap1,200 s including preflight,
index construction and output. Independent replay receives a separate whole-job
1,200 s cap under the same bounded two-core allocation. One numerical-thread
environment throughout. Supervision kills worker process groups on failure or
deadline; cleanup time is recorded separately with a bounded tolerance. No
automatic rerun, enlargement, or partial-success promotion.
Each phase requires a fresh output directory. A refused report invocation into
an existing output archives its prior summary/report and replaces them with an
explicit incomplete/no-verdict report; it does not reuse stale worker outputs.

## Falsifiable predictions and reporting

1. Both cohorts and all six points complete and independently replay within
   the frozen resource caps (expected true).
2. At scale one, the exact median/p95 path restriction strictly increases the
   path term over unrestricted item 35 in both cohorts (expected true).
3. At least one fixed scale in at least one cohort yields a positive integer
   conditional lower bound (expected false; no probability assigned).

Report measured runtime and peak memory; source count and hash; q and contract
hashes; each scale's unrestricted, necessary-relaxation, and exact joint lower
bounds; unchanged-at-that-q dictionary term; path-term increase; selected scale;
and prediction outcomes. Report no representative source or dictionary content.
Nonpositive bounds are inconclusive; the experiment makes no source-independent
impossibility, feasibility, M1, or qualification claim.

Activation must match the reviewed pending contract exactly before changing
only its active flag. No private file is opened to prepare the pending contract.
