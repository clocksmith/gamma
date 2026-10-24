# Item 53: fixed-potential tightening of every allowed occurrence

Prelaunch protocol,2026-10-24. This is a separate matched certificate
measurement following [the theorem](DRAFT.md), its preserved supplied-DAG
oracle, the [execution design](DRAFT-NEXT.md), and independently recorded
[item50](../potential-lift-certificate-v1/evidence/results.json), commit
`d7321954a`. No item50 file is changed. Pending-contract generation is blocked
until this item's supplied-input measurement and independent reporter are
stable and reviewed. No active contract or launch is authorized by this file.
After preparation, exact pending activation and Claude's cross-review remain
required before private inputs can be read.

## Population, target and fixed construction

Use exactly item28/35/50's R and naming300 fit sources. Evaluate aggregate
`F = 10 C - N`, where C counts singleton selections and N counts all selections
excluding Finish. The entry universe is every nonempty occurring exact
substring except the identical global whole-source, solve-definition and
solve-body bans, including primitive arrow bodies. At most256 entries may be
paid; characters are optional paid entries. For every k=0,...,256, at most k
paid entries may occur in exactly one distinct source ID. Repetition and
overlaps within one source do not create additional owners. Unused paid
entries and characters follow the same class/capacity rule.

Preserve item28's ordered old pool, denominator1,000,000 and exact original
signed-integer occurrence q in lexicographic string-PID/start/end order.
Compute its old suffix distances d at every position, with d(end)=0. On every
allowed edge i->j, including old edges, set

```
b = 9 for length1, otherwise -1
q53(i,j) = max(0, d(i)-d(j)-b*D)
```

Verify q53<=q28 on each old occurrence and equality on a retained old tight
successor at every suffix. All new edges satisfy the same Bellman inequality,
so every full-graph suffix distance remains exactly d and L remains exactly
L28. Item50 and53 new-only edges are identical. Every entry weight weakly
decreases, making every support-budget charge weakly smaller and every
integer lower bound weakly larger. No q search, source rewrite, potential
update, restart, proposal, validation selection or new vocabulary is performed.

This maximizes the fixed-L certificate under those Bellman inequalities and
the exact dual among assignments preserving the same actual suffix distances.
It is not an optimum over potentials or over a family permitting actual path
distances to increase. Strict gain and positivity are empirical outcomes,
not proof obligations.

## Exact input and accepted50 authority

The public-only binder verifies original28/33/35 contracts/evidence, original13
qualification receipts and the active50 contract plus accepted50 public
report. It pins50's complete public cohort rows and proof/top/input digests.
Require both50 cohorts complete, independently replayed, fixed300 fit only,
no validation/cases opened, no failure, and exact original parent/source/pool/
q/geometry identities. Its full257 rows must have exact integer arithmetic,
correct class/capacity semantics, ceilings and monotonicity. Embedded public
rows are compared back to the hash-bound original report during preflight.
No private file metadata or contents is read by pending generation.

Private inputs are exactly the same nine paths as50 under the approved work
root: two original control256/scope_joint256 `fit-sources.json` files and their
seed `dictionary.json` files; original
`all-length-fraction/run-v1/results.json`; and each R-flex256/naming-flex256
`pool.json` plus `certificate-q.npy`. Each worker reads its four cohort files
and the common original28 result. No private50 output is opened. No directory
inventory, validation source/hash,400-source carrier, oracle case, protected
population, item35 q or source execution is permitted.

Hash bytes before parsing. Preserve the original28 legacy result schema rather
than invent a `complete` field; verify its exact parent contract, both expected
arms, mode/capacity, validation=false and public certificate. The q loader
requires one-dimensional signed64, exact occurrence count and payload length,
no pickle/trailing data, nonnegative Python integers and no bool/float coercion.
Verify ordered pool, exact seed and96-character inclusion, source hashes,
learned shared entries and seed-extra counts/digest. An absent old character or
seed extra has zero occurrence weight and is omitted only from the occurring
entry classes; it is still retained in original pool accounting.

Rebuild exact bans with the pinned Node/Acorn parser; parsing does not execute
sources. Banned characters cannot be rescued by discarding a primitive-body
ban. Require source and ban digests plus accepted35 structural geometry:
R76,107 characters/13,553,771 entries; naming76,033/13,561,646;
both111,543 groups and966 banned occurrences. Exact suffix/interval/ban checks
support identity; matching counts alone do not.

Every original28 path term, L, old top256 charge, numerator and ceiling must
replay before completion. Old28 bounds are22,196(R) and13,725(naming). Original
qualification is the exact original13 control/scope_joint width8 receipt by
source hash, with no fresh jobs. Item23's later unchanged-source exit137 remains
a separately inherited failure; no new behavior or witness is claimed.

## Production, independent replay and exact reuse

`tighten.py` is an isolated adaptation of50's trie/backward reconstruction and
range helpers. It retains entry IDs on old occurrences, computes old d and
original weights, then sums q53 on those occurrences once. No rematching or
substring allocation is required to identify an old entry. Full-index interval
mapping proves exact old shared-pool completeness; `production.py` verifies
that mapped shared strings plus exact seed extras and alphabet equal the old
pool. This avoids redundantly rebuilding the same shared string pool.

Partition occurring entries into disjoint old and new-only sets, each classified
by actual source owners. All shared strings and occurring characters must be
old; seed extras may also be old. Aggregate new-only weights once per phase:
production uses exact endpoint-minimum range splitting for unique occurrences
and streams every depth/occurrence for repeated one-owner entries. Exclude
exact banned and old-entry depths. Zero-weight ranges choose the earliest
length. Keep separate new-only top256 lists by class and then merge them with
old original weights and old tightened weights separately.

Each subset's top256 suffices for selection of at most256 from its union. The
combined50 top list alone is insufficient after old weights fall and must
never be used as the candidate universe for53. Tie order is descending weight,
then ascending item33 `(group ID,length)`. Count all allowed entries, including
zeros, independently of heap contents.

For each variant compute both class prefixes and every support allocation:
`T_k=max_j[A(j)+B(min(256-j,m_shared))]`,
`0<=j<=min(k,256,m_one_owner)`. Equal charges choose fewer one-owner slots.
Bound=`ceil((L-T_k)/D)` uses exact integer division, including negative inputs.
Check the unrestricted k256 charge separately, monotonicity and old28 k0
dominance. Retain both257-row arrays, exact top identities privately, input/
occurrence/potential/old-weight/new-only-top digests and reduction counts.

The independent checker reconstructs occurrences via Aho-Corasick, computes
start-to-end paths with incoming/end-order relaxation and all suffix potentials
on the reversed DAG, and checks every old Bellman edge and tight continuation.
Support uses same-owner-run endpoints instead of production change prefixes.
It streams every allowed group depth, including unique entries, using its own
old/tightened occurrence sums and exact new-only penalties. It uses bounded
sorted lists and an independent allocation loop; no production RMQ, heap,
potentials or selected top entries determine its answer. Identical new-only
terms may feed the two variants in that independent pass.

Shared dependencies are disclosed: exact input/ban binding and parser,
item33 Index and accepted suffix/partition/ban verifier, and canonical integer
serialization. This independently verifies scalar certificate calculations;
it is not a second parser or independently implemented suffix-array proof.

Rebuilt50 must equal its accepted public input/source/ban/parent/path/order
digests, shape, class counts, all old terms, all257 rows, full proof digest and
top-entry digest. This reconciles top identities without opening private50
results or publishing entry IDs. Production and independent53 must agree on
both scientific proofs, every suffix-potential digest, old/tightened weight
digests, new-only class tops/counts, all reductions and514 row values. Work
counters differ by algorithm and remain separately labeled.

## Registered outcomes and interpretation

The observed50 baseline is disclosed: largest positive k=2 in both cohorts;
k0 bounds22,197/13,727 and unrestricted k256 bounds-1,903,184/-1,679,219 for
R/naming. This follow-up's fixed-d dominance theorem predates that measurement;
the execution design explicitly conditions on the accepted50 baseline.

- P1: exact28/50 replay, fixed potentials and all257 dominance in both cohorts;
  required true. Failure invalidates the run.
- P2: at least one cohort/k has a strict raw charge reduction; uncertain.
- P3: at least one cohort's largest positive k increases; uncertain.
- P4: at least one cohort has positive unrestricted k256; uncertain.

Report all257 raw charge reductions and integer-bound gains separately; a
strict raw gain can be hidden by ceiling. A zero-gain result tests this fixed
potential construction only. Nonpositive bounds are inconclusive about an
actual representation. Positive bounds exclude aggregate C/N<=10% only in
the fixed300-source paid-entry/support class. They do not prove coverage at
that k or at a larger budget; singleton ownership can make small-k classes
infeasible. No M1, semantic-reuse,400/500-source, held-out, canonical-action,
package, witness, dictionary or global-dual-optimality claim is authorized.

## Runtime, failures and publication

Separate production and independently invoked reporting phases each have
1200seconds total and600seconds per cohort worker. R/core6, naming/core7;
each process8GiB RLIMIT_AS and OMP/OpenBLAS/MKL threads1. Root determines
nonoverlap with other work. Fixed literal signal guards and resource limits
start before local imports, argument parsing, contract reads or input hashing.
Absolute parent deadlines only reduce worker time. Ordinary Exception handlers
must not swallow BaseException deadline signals.

All hashing, parsing, pool/index reconstruction, paired calculation, comparison,
serialization and final publication count. Parser descendants stay inside
worker process groups. Normal cleanup has at most10seconds within the original
phase deadline. On first failure, one emergency deadline is the earlier of
failure time+10seconds and phase deadline+10seconds; if normal cleanup fails,
its start anchors that allowance. Kill/wait, log closing, success withdrawal
and failure writes share it. Every subsequent operation checks remaining time;
a hard deadline stops later writes. Reporter withdrawal receives this same
deadline rather than creating another allowance.

Fresh output directories are required. Completion requires actual integer-zero
worker exits, finished group cleanup/log closing, complete cohort receipts and
independent replay under the original successful-phase deadline. Remove stale
success markers independently of failure-receipt I/O. Preserve incomplete
artifacts and no verdict after time/memory/parser/proof/publication failure.
Never retry a cohort, extend its cap, drop entries/budgets, change q or promote
one completed arm after another fails.

Repeated-new depth/occurrence streaming can require quadratic work; independent
reporting also visits every allowed depth. This is an honest cost of the chosen
exact algorithms, not a universal lower bound. Avoid quadratic stored strings
or a full new-edge graph; retain only original pool/occurrences, source/index/
ban data and bounded top lists. Account old trie transitions and extra entry-ID
storage. The separately pinned invented measurement is a complexity check,
not a corpus ETA or permission to alter these bounds after private access.

Public output contains only hashes, counts, phase time/RSS, original terms,
all numeric rows/deltas/reduction statistics and outcome flags. Source/q/
potential values, entry IDs/strings and source-derived diagnostics stay private.
No packets or cases are needed for this certificate-only result.

## Checks and remaining prelaunch gates

Focused tests cover explicit full-graph suffix equality, exhaustive dictionary
weak duality, all257 allocation rules, new-only top replacement, unchanged
charges despite slack reduction, raw gain hidden by ceiling, zero ties, absent
entries, support-one characters, old-pool/primitive-body incompatibility and
input/order/type corruption. Execution tests exercise accepted50 public drift
before private reads, exact-five-file invented loading, independent paired
worker output, post-proof failure and exact activation drift. Supervisor tests
cover real worker/child/grandchild groups and expired/slow failure operations.

Before binding: finish and record the separately approved supplied-input
measurement, stabilize independent reporting and focused integration tests,
then inspect code/runtime/public pins. Before launch: root/Claude cross-review,
commit/push, exact inactive-to-active transformation and explicit queue release.
The binder pins execution/replay code/tests, this freeze, measured synthetic
artifacts and parent/public/runtime identities. DRAFT-NEXT.md is a measured
design dependency and remains pinned by the synthetic specification;
README/REVIEW are unpinned recording documents. Preserved theorem files remain unchanged.
Component intent and owner promotion authority are preserved.
