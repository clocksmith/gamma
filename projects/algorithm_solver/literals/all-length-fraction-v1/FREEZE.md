# All-length shared-pool character-fraction certificate

Board item28, goal2a diagnostic. Extend item25's two flex256 models to remove the
64-character ceiling from the shared learned pool. Keep item25's objective,
dual optimizer, certificate/replay, witnesses and source identities unchanged.
No corpus contents, costs or pool statistics were inspected for this draft.
Only synthetic texts were used to test the new pool enumerator.

## Exact population and pool

Only item13's control256 R and scope_joint256 naming fit300 sources and seed
dictionaries, inherited by hash from fraction-capacity-v1/contract.json. Load no
validation sources or cases, final heldout100 or protected66. Item13 qualification
is reused only after checking each exact fit source hash against its receipt.
Naming remains adaptively selected development material. Item23's later unchanged
source exit137 failure is preserved and is not revised by this diagnostic.

For each source cohort, enumerate **every distinct substring of length at least
2, without a maximum length, occurring in at least two distinct fit programs**.
Exclude the exact strings in the inherited fit complete-source/solve-definition/
body ban set. Union all pinned seed learned entries, even if a seed entry is
one-owner or otherwise absent from the shared pool; report the extra count/hash.
Assert seed and final pool disjoint from the bans. Add all96 ASCII/newline
characters as optional entries, with no mandatory alphabet. Select at most256
entries total. No reserved-unseen-character rule, rank cutoff, top-pool sampling,
length truncation, source rewriting or one-owner learned additions beyond seed
extras. The seed therefore remains a feasible complete-cohort primal witness.

The source alphabet is asserted ASCII, so substring character lengths equal byte
lengths. A two-owner condition means two distinct problem IDs, not two positions
in one program. Distinct programs with identical bytes count as distinct owners.

## Pool algorithm and completeness argument

Concatenate the source character codes with a distinct separator for each owner.
Prefix-doubling sorts all suffixes using integer rank pairs. Kasai computes
adjacent LCP values. Ignore separator-start suffixes and retain the minimum LCP
across skipped positions. The maximum common prefix with any differently owned
suffix is attained at the nearest differently owned suffix on the left or right:
LCP of nonadjacent suffixes is the minimum adjacent LCP along their interval, and
moving farther cannot increase that minimum. Forward/reverse running minima
inside same-owner runs compute both values.

For each suffix, lengths2 through that maximum are exactly its shared prefixes.
Emit only lengths exceeding its immediate predecessor's LCP. Any shorter prefix
already appeared earlier; the lexicographically first occurrence of every shared
prefix has a differently owned match and emits it. Thus every eligible distinct
string is produced once. Exact bans remove only themselves, not longer strings
containing them. Unique separators prevent document-boundary crossings.

For N total characters plus separators, S bytes in all shared strings before
exact bans, and B bytes in the ban set, the pool stage uses
O(N log²N + S + B) time and O(N + S + B) memory. Rank sorting compares
integer pairs, not materialized suffix strings. The output itself can have
quadratically many entries and cubically many bytes on adversarial input; no
claim of universally small output is made. The unchanged dual graph builder and
independent replay enumerate lengths through the pool's maximum and may dominate
runtime. If limits prevent construction/replay, record a resource failure and
no complete certificate; never silently shorten the pool.

## Objective, certificate and witnesses

Reuse fraction-capacity-v1/dual.py unchanged. For C single-character selections
and N total selections, F=10C-N. With8-bit selections, F>0 is equivalent to C/N>10%.
An occurrence edge costs9 for a character and-1 otherwise. Nonnegative occurrence
multipliers relax activation constraints; shortest DAG paths minus the256 largest
entry multiplier sums lower-bound F for every dictionary and segmentation in
this exact source/pool/capacity model. Negative edges are safe in the acyclic graph.

Quantize the best multiplier vector down to denominator1,000,000 and recompute
with Python integers. A separately enumerated forward DAG must reproduce the
exact numerator. A positive integer lower bound excludes10% for the complete
fixed fit300 cohort under this enlarged pool. It does not exclude arbitrary
one-owner literals, other sources, subsets, unseen problems, quantile targets or
all M1 representations. Even this all-length shared pool is a restricted pool.
A nonpositive bound is inconclusive unless a decoded feasible witness reaches
F<=0. MinF is not minimum ratio. No candidate promotion or M1 threshold change.

Starting at zero multipliers, use the inherited Polyak update, theta1 halved after
30 stalled iterations, and three primal proposals every25iterations. Uncovered
flex proposals fail; no partial objective or repair. Keep seed, best feasible and
best generated (if any) separate. All available final witnesses must decode all
300 unchanged fit sources through the canonical codec, with clean body bans and
fully charged256-entry storage,8-bit selections, Finish and41-byte frames. Report
C,N,fraction,actions,quantiles,package,decoder-source inventory and failures.

## Budgets and execution

Two concurrent processes: R pinned to core0; naming pinned to core1. Each
optimizer gets at most2000iterations or1200seconds after graph construction;
a final iteration may cross its guard. All pool/graph construction and final
replay count toward the2400-second overall guard. Each worker applies8GiB
RLIMIT_AS before corpus loading. Parent kills workers on the overall timeout or
worker failure and records failure.json; no partial result is promoted. Launch
under an outer2400-second timeout as an additional guard for parent preflight.
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1. Pinned Python3.14.4/NumPy2.4.4, no GPU,
installation or model. Inputs, runtime, inherited dual and new code hashes must
match before launch. Log every optimizer iteration privately; seal all outputs.

## Predictions fixed before measurement

- A1: both exact integer certificates pass independent forward replay and do not
  exceed their decoded best feasible witness objectives.
- A2: both final optional pools strictly exceed their item25 flex256 pools in
  entry count, after seed union and optional characters in both. Reporting
  compares recorded counts without changing construction or search.
- A3: at least one all-length flex256 exact bound is nonpositive.
- A4: no generated complete feasible witness reaches F<=0.
- A5: every available final witness decodes all300 sources with clean bans.

A2 uses the committed item25 flex256 pool counts during reporting; the run does
not load or adapt to that pool.
All predictions score failures/incomplete runs explicitly. Report exact sign,
gap, pool size/max length/seed extras, iterations, elapsed phases, stop reason,
coverage and witness costs. Reporting is separate and must not rerun optimization.
Before reporting a certificate, independently rebuild the exact pool from the
pinned fit texts, bans, seed extras and alphabet; compare its order/hash to the
sealed pool, then replay the stored integer multipliers with the forward-DAG
verifier. Rebuilding uses only fit sources and never opens validation.

Six synthetic tests cover300 exhaustive suffix-array/LCP instances and500
exhaustive shared-pool instances, plus repeated same-owner suffixes, duplicate
programs, empty inputs, Unicode/separator collisions, prefix bans, boundary
crossing and entries longer than64. Existing dual tests remain unchanged.
Compile/import/help and contract identity verification precede any launch.
Root and Claude review, commit and push of this freeze precede measurement.

Component: algorithm-solver literal diagnostics. Intent and authority boundaries
preserved. No training, protected opening, publication, BITS deploy, human study,
independent confirmation, catalog/claim/ledger writes or M1 claim.
