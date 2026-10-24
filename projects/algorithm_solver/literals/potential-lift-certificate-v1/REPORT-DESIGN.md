# Item 50 independent production report design

2026-10-24. **Unpinned auxiliary design only.** This file is outside the measured
synthetic specification. It authorizes no private access, implementation,
activation, or execution. The measured prototype, checker, tests and synthetic
specification remain unchanged. Root review of the production design and the
public synthetic record precedes any implementation authorization.

The proposed reporter independently checks the certificate described in
[DRAFT.md](DRAFT.md), using the frozen supplied-input
[checker](independent.py). It does not optimize multipliers, choose source
alternatives, search for dictionaries, or execute programs. Its proof target is
the exact fixed-source lower-bound curve for F=10C-N under at most 256 paid
entries and at most k one-owner entries, for **every k from 0 through 256**.

## Input authority and ordering

The future contract must explicitly enumerate all permitted paths and expected
hashes. A recursive private-directory inventory is not allowed. Public binding
preparation may read public contracts and evidence only. Private paths below
are opened only after a frozen, reviewed, active contract and successful
production receipt have been verified.

1. Pin the exact item 28 public
   [contract](../all-length-fraction-v1/contract.json) and accepted
   [evidence](../all-length-fraction-v1/evidence/results.json). Verify the public
   evidence's `contract_sha256`, its exact two R/naming flex256 arms, 300 fit
   IDs, zero mandatory entries, capacity 256, denominator, and accepted
   `pool_rebuilt`, `body_audit_clean`, `certificate_replayed` and qualification
   identity flags. These flags establish which parent record is intended; they
   do not replace the new scalar replay.
2. Pin item 28's private top-level `results.json` to the public
   `private_results_sha256`. Bind the selected arm metadata exactly to the
   corresponding raw parent arm. If the arm's separate `results.json` is also
   read, require its parsed value to equal that raw arm; do not accept a second
   independent arm record merely because its cohort label matches. Preserve
   original parent hashes separately from any normalized report serialization.
3. Read only each permitted `fit-sources.json` and original `dictionary.json`
   identified by item 28's `cohorts` and `private_files`. Hash exact file bytes
   against those pins before parsing. Verify unique 300-ID membership and
   exact per-ID UTF-8 hashes against the pinned original item 13 control or
   scope_joint qualification evidence. Seed dictionary order and file hash
   remain unchanged even though old-pool construction uses a sorted set.
4. Read the parent's exact `pool.json` and `certificate-q.npy` from the selected
   arm. Check their byte hashes against parent `pool_sha256` and certificate
   `q_sha256`, plus metadata length/count. Load q with `allow_pickle=False`;
   require one-dimensional signed 64-bit integer storage, nonnegative values,
   and the exact occurrence count. Convert to Python integers only after those
   checks. There is no float conversion, new quantization, q scaling, or repair.
5. Bind the accepted item 35 public
   [contract](../length-sensitive-fraction-v1/contract.json) and
   [evidence](../length-sensitive-fraction-v1/evidence/results.json). Verify its
   contract identity, accepted complete R/naming arms, fixed cohort IDs, source
   file pins, full-pool definition, and exact geometry counts. No private item
   35 q, witness, validation source, or packet file is needed or permitted.
6. Bind item 50's active contract, production top-level and arm results, retained
   certificate metadata, and production supervisor receipt. Require both arms
   complete, exact expected hashes and cohort identities, no failure artifact,
   and exactly two integer-zero child return codes. `False` is not an exit code
   zero. A missing, partial, mismatched, or failed production result stops replay
   before loading any parent private input.

Original item 28 q ordering is **lexicographically sorted string source ID,
increasing start, increasing end**, with sorted-pool entry ID. It is not numeric
source-ID order. The fresh checker's Aho–Corasick end-order matches are regrouped
at each start without changing end order; it produces the same canonical
occurrence digest as production. Original public
`per_program_path_numerators` is a list in this sorted source-ID order. The
reporter must compare it to that explicit ordered list, retaining the ID-keyed
reconstruction separately. A dictionary iteration order is not an authority.

## Source, ban and pool reconciliation

The item 28, 33 and 35 public contracts currently pin the same fit IDs, R/naming
source-file hashes, and exact `lagrange-select-v2/selection.py` plus
`tail-search-v1/structure.cjs` files. Verify this equality from the frozen
contracts; do not infer it from matching names.

Re-derive bans from the exact permitted fit sources with the pinned structure
helper, under the report deadline and process-group guard. Include complete
sources, complete top-level solve definitions, block bodies, trimmed block
interiors, and exact expression bodies as the helper specifies. **Primitive
arrow bodies are included**, even if they are single characters. Empty or
unsupported solve structures fail closed. The ban universe is a global union
over the cohort: an entry forbidden by one source is forbidden everywhere.
Do not filter bans by minimum length or classify a short body as harmless.

The parser/helper is a shared, explicitly disclosed dependency. The reporter
recomputes its output from source bytes; it does not claim an independently
implemented JavaScript parser. It compares the derived sorted-ban digest to
production, verifies that the parent and full-pool contracts bind the same
helper and source identities, and independently checks each exclusion in the
full substring index. A newly incompatible ban is a failure, not permission to
delete an old edge or reinterpret the potential proof.

Reconstruct the exact old item 28 pool as all allowed length>=2 strings present
in at least two distinct source IDs, union pinned seed learned extras, union
all 96 optional ASCII/newline characters. Check complete equality to the
parent's sorted pool and the original cardinality, maximum length, shared count,
seed-extra count and seed-extra digest. Check ban disjointness **after** adding
all 96 characters. A banned primitive body that collides with a character must
fail; it cannot become a free character edge. Both recorded parent arms report
zero seed learned extras, but retain the general reconstruction and check that
recorded zero rather than hard-coding it.

Absent old characters or seed entries keep their original old-pool IDs and have
zero occurrence weight. They do not become fictitious full-pool entries. Omitting
these zero-weight entries from the full occurring-substring universe does not
alter a maximum charge under an at-most-256 capacity. Every occurring singleton
remains a paid entry, and its actual owner count participates in the support
constraint. No coverage shortcut supplies free characters.

Rebuild the full item 35 substring geometry from these exact sources and bans.
Reconcile source characters, distinct allowed words, compressed group count,
and exact banned-occurrence count against accepted item 35 public metadata and
item 50 production. There is no length cutoff, owner cutoff, or omitted
one-owner suffix range. The source geometry and ban policy are reused from 35;
the lifted arbitrary occurrence multipliers are **not** restricted to its
start/length-bin parameter family.

## Independent scalar replay

Each report worker constructs fresh checker state from authenticated inputs.
It must not reuse production potentials, entry weights, support classes,
interval selection, range-minimum results, or previously cached certificate
rows. Production values are comparison targets only.

The measured checker shares item 33's compressed index and accepted suffix
order/LCP/interval-partition/ban verifier. It then uses Aho–Corasick old matching,
forward end-order path calculation, reversed-DAG relaxation for all suffix
potentials, contiguous owner-run endpoints for support classification, and an
exact traversal of **every allowed group depth**, including unique occurrences.
It sums each new occurrence penalty and retains bounded sorted top lists. This
is separate from production's unique-occurrence range-minimum extraction;
shared index/parser dependencies remain visible in the public report.

Reconcile the following without tolerances or floating arithmetic:

- Original old occurrence count and order digest; every nonnegative q value is
  assigned by that order. Preserve old penalties even when larger than the new
  edge potential formula.
- All 300 old source-start path numerators, their sum L, old entry top-256 charge,
  old numerator, denominator and integer ceiling against the original item 28
  public certificate terms. Check every old Bellman inequality and a tight
  terminating suffix path at every source position. New-edge penalties establish
  the same inequality, so all lifted suffix distances equal their old values.
- Complete one-owner/shared class sizes; bounded top entries including exact
  weights, deterministic `(group ID, length)` identities and tie order. The
  cardinality in each retained list is `min(256, class size)`. Zero-weight and
  unused paid entries are included where their rank requires them. Ownership is
  distinct source-ID presence, not selected-path use or occurrence count.
- All 257 exact allocation rows: k, maximum charge, one-owner/shared slot counts,
  numerator, denominator and integer ceiling. Match production exactly,
  including its fewer-one-owner allocation tie rule. Require monotonicity and
  equality of k256 to the unrestricted full-pool top-256 charge.
- The k0 numerator is at least the freshly replayed old numerator. The public
  old arithmetic currently gives ceilings 22196 for R and 13725 for naming;
  recompute them from the pinned terms. These are conditional proof checks,
  not a substitute for a newly computed k0 row.

Compare work counters only when their definitions agree. Production RMQ query
counts and independent all-depth contribution counts intentionally differ.
Record each method's actual work, elapsed time and peak memory separately;
never infer a corpus runtime from synthetic elapsed time.

The public report may show the fixed display ladder
0,1,2,4,8,16,32,64,128,256, but its machine-readable evidence must retain all 257
rows and the full numerical reconciliation. Public entry diagnostics may expose
group/depth IDs, lengths, weights and hashes, never source strings, q vectors,
or entry text. All source/hash keys are selected metadata under the existing
evidence policy.

## Proposed resource and failure contract

This is a **separate report phase**, queued by root after production releases
its cores. Proposed fixed limits are one R worker on core 6 and one naming
worker on core 7, 8 GiB address space per process, and 600 wall-clock seconds
per worker. The supervisor has a 1200-second acceptance deadline for the whole
phase, including setup, validation, child cleanup, combination and publication.
The supervisor itself also has an 8 GiB address-space limit and affinity within
cores 6/7. There are no nested worker pools or more than two cohort workers.

Install a hard deadline raising a dedicated `BaseException` and the memory cap
before contract/filesystem preflight in each worker and the supervisor. Account
for imports and input hashing within those guards. Structure-parser children
inherit the cohort worker's separate process group and remaining deadline;
subprocess calls must not replenish the worker budget. Prevent optimized Python
before relying on assertions. Freeze the interpreter, runtime and code
inventories separately from the synthetic specification.

The supervisor owns both worker process groups, including parser descendants.
On timeout, child failure, parent setup failure, or cleanup failure it terminates
the groups and escalates to killing them within a fixed **10-second emergency
cleanup allowance**. This allowance is not extra successful report time: no
success can be accepted after 1200 seconds. Retain process outcomes, elapsed
time, memory, phase and cleanup receipt. Catch `BaseException` at the outer
failure boundary so the hard timer cannot bypass failure publication.

Workers write fresh private staging artifacts. Only after both complete replays,
zero child return codes, successful process-group cleanup and remaining deadline
checks may the supervisor combine and publish. Check exact cohort multiplicity,
finite nonnegative times, positive peak memory within the declared limit, and
worker elapsed time within 600 seconds. There is no silent partial success,
one-cohort summary presented as complete, automatic retry, skipped check, or
smaller substitute population.

Guard the entire publication path, including JSON serialization, prose creation,
atomic replacement and final cleanup. Stage both success files first; replace
the complete machine-readable result last. Recheck the whole deadline around
replacement. Any failure withdraws stale success independently for each public
artifact and writes an explicit incomplete receipt with null verdicts. Preserve
partial private artifacts for diagnosis. Failure to write one receipt must not
leave the other public success artifact accepted.

## Claim boundaries and implementation review

A positive bound rules out aggregate F<=0 only for the fixed 300-source cohort
and the stated support-constrained dictionary class. A nonpositive result is
inconclusive. Small-k infeasibility can be caused by a unique required character;
report that possibility rather than implying a causal semantic-reuse finding.
The k256 row is a valid unrestricted full-pool certificate at this constructed
q, not the best possible multiplier certificate. No equality-to-primal or
optimality claim is available because this phase constructs no primal witness.

The reporter loads no cases, produces no new qualification observations,
searches no feasible dictionary, and reads or decodes no packets. Existing
source-qualification hashes identify unchanged inputs only. There is no witness
quality, action-count improvement, canonical-policy result, package-cost result,
M1 promotion, causal semantic-reuse result, or protected-population claim.

Before implementation authorization, root reviews this input inventory, the
production retention schema, shared dependencies and resource/failure contract.
Implementation then needs focused invented fixtures for complete replay and
corrupted parent identities/terms, q order/dtype, primitive-body incompatibility,
top lists/allocation rows, missing/failed production, deadline/publication
failure and actual process-group cleanup. No production launch follows merely
from those development tests; the separate freeze and Claude review remain.

Component intent is preserved: fixed-source literal evidence, exact paid-entry
constraints, independent reporting and explicit failure retention. No component
boundary changes are proposed.
