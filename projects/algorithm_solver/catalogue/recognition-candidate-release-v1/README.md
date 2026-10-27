# Recognition candidate: inventory first, no activation

This checkpoint prepares a separate development candidate. It is **not a built,
calibrated, published, or deployed recognition release**. The original dirty
checkout, frozen vectors, source receipts, protected populations, and encoder
remain unchanged. Component intent is preserved; production hosting and source
qualification authority are not expanded.

## Current inventory

A fresh metadata recount against all six authenticated boundary-policy v3 inputs
retains **4,081 identities**: **2,872 statement-acquisition authorized**, **482
reserved**, and **727 unresolved/exterior**. The 727 is a new recount, not an
assumed historical constant. There are no duplicate canonical IDs or collisions
among established aliases. Complete global alias closure is still not claimed.
Of 724 identities lacking metadata slugs, 718 are exterior and six reserved;
nine exterior identities have metadata slugs but remain unauthorized.
Canonical IDs, not guessed slugs, preserve all competitors.

Statement permission, source availability, qualification, and publication are
separate fields. Source availability does not authorize a description read or
select a recognition identity.

The verified development baseline has **102 enriched descriptions and 3,979 title
rows**. Its permitted description backlog is **2,770**, not 727. A private
projection supplies **51 additional development-authored descriptions**, distinct
from normative statement authority and implementation qualification. Candidate
coverage is therefore **153 enriched / 3,928 title-only**, leaving **2,719
permitted descriptions unresolved**. Among 312 newly authored source-candidate
identities inspected for description availability, 139 are excluded because
manifests mix case/example fields with contract metadata, and 122 lack useful
problem semantics. A field named `result` that reports passing tests is not a
problem description.

Metadata inspection encountered development manifests combining contract metadata
with case/example fields. Those raw-file opens are recorded rather than described
as case-free. Case/example values were not inspected, selected, or used; mixed
artifacts were excluded from description acquisition pending a separately scoped
statement-only source. Protected payloads and separate case/source files remained
closed.

## Reuse and candidate identity

Candidate preparation identity:
`42be9586497bda4b6800a804ec19061bc5c3623ad0ad7c538d281f0d498fc851`.
This is not a deployed release ID.

The increment contains **0 added identities, 51 changed documents, 4,030 unchanged,
0 removed**. Exactly **4,030 existing vectors are reusable**; **51 new vectors
remain pending and zero were generated**. The 482 reserved and 727 exterior
competitors retain exact frozen title documents/vectors, without new payload
access or use expansion.

Reuse proof checks every ordered canonical identity, exact UTF-8 document hash,
original vector-file and row binding, full model/tokenizer/adapter/preprocessing
identity, and execution manifest. Dimension equality alone is insufficient.
The assembled 4,081-by-1,024 baseline is finite float32 with unit norms; all six
model assets, the Python binary, 34 package versions, and 19,425 installed wheel
payload files were verified. Installer-generated metadata/entrypoints, bytecode,
and unrecorded historical OS-library identity remain explicit limits. No fresh
numerical equivalence experiment is claimed.

This separately named 4,081-row development baseline is **not** retrospectively
identified with the historical 3,353-corpus or 3,273-research index. Missing
historical provenance is not fabricated. Encoder/model/adapter/tokenizer/pooling,
normalization, instruction, truncation, and runtime remain unchanged; reranker-only
changes do not request document embeddings.

## Implemented mechanisms

- [`recognition_inventory.py`](../recognition_inventory.py): source-free access,
  duplicate/ambiguity inventory and exact incremental reuse plan.
- [`recognition_search.py`](../recognition_search.py): full-population ranking,
  population-bound development calibration, independent target identity, exact
  post-ranking implementation lookup, and no qualified-neighbor substitution.
- [`recognition_candidate.py`](../recognition_candidate.py): pinned incremental
  runner, boundary-before-open checks, batch receipts and resumption, validation,
  and owned-process-group cleanup. It fails before model launch when requested
  hard aggregate memory containment is unavailable. Sampled RSS and per-process
  RLIMIT_AS are never described as a kernel aggregate cap.
- [`recognition_bundle.py`](../../algsolve/recognition_bundle.py): exact index/BITS
  identities and file hashes, external asset-specific publication grants, an
  atomic complete-release pointer and one-operation rollback. See the
  [bundle contract](../../algsolve/RECOGNITION-RELEASE.md).

Private documents, vector arrays, alias inventories, source locators, cases,
model assets and BITS packets are not part of this source checkpoint. Matching
private BITS identity metadata was prepared; solution guides remain separate.

## Blocking conditions and next authorized steps

The list below preserves the original checkpoint's conditions. On 2026-10-27,
the runner gained cgroup-v2 preflight: it resolves `/proc/self/cgroup` through
the actual mount root, checks finite `memory.max` values throughout the visible
ancestry, and includes each ancestor's remaining headroom. A required cap fails
closed unless an inherited limit is no larger than the plan's memory budget.
The supervisor rechecks that cap while the worker runs and retains group cleanup
on failure. It never sets machine or cgroup policy itself.

A model-free Jupiter probe inside an explicitly capped systemd service verified
an 8 GiB kernel limit for both supervisor and child, more than 5 GiB remaining
headroom, normal child completion and no live owned-group members afterward.
This resolves the runner's blanket rejection of an existing cap; it is not an
encoder run, an OOM stress test or evidence that the pending 51 vectors exist.
Any resumed run still needs its authentic private plan and assets, updated runner
code pins, unchanged encoder identity and an adequately capped execution envelope.

1. The existing CPU envelope needs at least 5 GiB available memory. Observed
   capacity was below that floor. No worker or model was launched.
2. No existing approved kernel-hard aggregate-memory runner/cgroup was established.
   The historical launcher supplies process-group wall cleanup and per-process
   address-space limits only. Do not silently weaken the new hard aggregate
   requirement or provision a new remote/credential.
3. After a permitted bounded execution route exists, resume only the 51 changed
   documents, verify full matrix/document/order/runtime bindings, and recalibrate
   the changed population on authorized development data. Target recall, variant
   coverage, ranking, ambiguity, truncation, and cold/warm latency remain separate
   pending numerical results. Synthetic mechanism tests are not confirmation.
4. Public description/packet asset grants and an established deployment target
   remain unverified. The legacy documented loopback endpoint was unavailable.
   It does not consume the new release pointer or enforce the new client release
   identity. No public deployment, live lookup, or coherent real activation was
   verified.
5. Before activation, the serving owner must integrate one snapshot for both
   index and BITS, reject a mismatching client identity before model execution,
   and retain a verified previous **complete** bundle. Only the previous index
   baseline is presently established here; a previous complete deployed index+BITS
   release is not invented. `rollback_release(...)` restores both components in
   one atomic operation; current evidence is synthetic tests, not a deployed
   rollback rehearsal.

Run the focused mechanism and regression checks from the repository root:

```sh
PYTHONPATH=.:projects/algorithm_solver python -m unittest \
  projects.algorithm_solver.catalogue.test_recognition_inventory \
  projects.algorithm_solver.catalogue.test_recognition_search \
  projects.algorithm_solver.catalogue.test_recognition_candidate \
  projects.algorithm_solver.tests.test_recognition_bundle
```

[STATUS.json](STATUS.json) records source-free counts, hashes, and evidence scope.
