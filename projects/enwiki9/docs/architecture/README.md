# Architecture extraction

The lab CLI delegates to maintained services in `src/gamma_enwiki9/`.
Historical source is preserved in the existing content-addressed candidate
blob store; no original result, candidate or experiment hash is rewritten.

The extraction follows the audit's eight acceptance stages:

| Stage | Implementation and acceptance |
| --- | --- |
| Lease ownership | `execution/lease.py` retains directory and lock descriptors, process start ticks and file identities. Contention, partial publication, cancellation, stale recovery, PID reuse and live-codec refusal have regression tests. Queue admission uses the same runtime-directory lock before the queue lock. |
| Dependency closure | `evidence/source_closure.py` resolves declared roots, package initialization, relative imports, from-import submodules and local libraries. Schemas and non-source assets are explicit. Unresolved local imports, undeclared external modules and dynamic loading sites remain visible. |
| Architecture CI | `.github/workflows/ci.yml` selects project-local pure, codec, sanitizer and historical groups explicitly. Linux cgroup tests use a separately provisioned runner and a declared test parent. |
| Artifact and domain primitives | Distinct immutable publication, derived replacement and canonical event append operations; typed population, execution, evidence, decision, build and package records. Candidate creation uses immutable intent, idempotent reconciliation and a commit marker. |
| Execution extraction | Linux envelopes and cleanup moved out of the lab. A contextual native gate receives resolver, executor and writer capabilities. The existing P/K/D raw-reversal comparison exercises the new runtime and preserves original archive bytes and common witnesses on invented fixtures. |
| Historical closure | `verify-history` restores the original causal-wordcode negative result and bound validator. Restricted replay retains the original 99M objective and `retire` outcome while declaring current-launcher compatibility and new execution authority separately. |
| Codec delivery | `lib/coders/raw_reverse_bz2.py` contains the original numerical implementation. A delivery manifest declares its source, CLI, license and Python/bz2 runtime requirements. Restricted decoding has no checkout or observer mount. This is fixture evidence, not prize qualification. |
| Maintained source roles | `source_roles.json` labels migrated source, compatibility entrances and frozen copies. New framework imports use `gamma_enwiki9`; original recipes and their retained snapshots stay resolvable. |

## Reproduce

Use a provisioned Python with pytest and jsonschema; native fixtures additionally
require GCC and restricted replay requires bubblewrap. From the repository root:

```bash
python projects/enwiki9/tests/run_architecture_groups.py pure
python projects/enwiki9/tests/run_architecture_groups.py codec
python projects/enwiki9/tests/run_architecture_groups.py native
python projects/enwiki9/tests/run_architecture_groups.py historical
python projects/enwiki9/tools/enwiki9_lab.py verify-history \
  projects/enwiki9/operations/adaptive/framework-closures/causal-wordcode-original-verification.json \
  --output /tmp/enwiki9-original-verification
```

For Linux resource integration, set `GAMMA_ENWIKI9_TEST_CGROUP_PARENT` to an
empty, delegated test parent and run the `linux` group. It creates a unique
child cgroup and never adopts or kills an existing group.

## Contracts and limits

`operations/adaptive/framework-closures/47b4a181-pre-extraction.json` preserves
framework preimages and explicitly does **not** claim a complete experiment
runtime. The causal-wordcode manifest is a separate original verification
closure. Its paths and SHA-256 identities are independently checked, and
missing/corrupt blobs block restoration. Git recovery requires an exact match
to the original reference digest; a newer file is never substituted.

The historical verifier's external Python/jsonschema runtime is declared, not
claimed to reproduce the historical codec runtime or resource measurement.
Original artifacts, replayability, launcher compatibility and permission for a
new run are separate facts. Verification produces a new interpretation record.

Static Python analysis cannot prove arbitrary `exec`, native libraries or
runtime assets complete. New callers consume the structured report and explicit
declarations; the legacy list API makes no completeness claim. Restricted
filesystem tests complement that report.

`records` uses deterministic source projection. `start` explicitly attaches
live observations, including the existing HORIZON observer through the legacy
application adapter; no second observer is launched. Both remain browsing
surfaces. The source-role map is documentation, not a second source registry.

Recover interrupted creation through `lab reconcile-candidate CANDIDATE`.
Revision identity, mutation event identity and candidate index identity make
reconciliation idempotent. Once an intent is durable, failure preserves source;
the commit marker is required before candidate use.

The generic command executor enforces per-process limits for bounded synthetic
fixtures and keeps an unreaped leader until owned group cleanup to prevent PGID
reuse. Canonical research jobs retain the Linux cgroup envelope for aggregate
memory, scratch and descendant enforcement. Shared-host fixture timing is
diagnostic. No full-corpus compression, model download or live-job control is
part of this extraction.

## Functional ownership

- Codec: `lib/coders`, format equivalence and independent inversion.
- Execution: `execution`, lease, workspace, resource and cancellation tests.
- Evidence: `evidence`, original closure validation and scientific distinctions.
- Release: `packaging`, declared dependencies and restricted fixture decoding.

Cross-boundary acceptance is recorded in the linked test groups and
`acceptance.json`; fixture success never advances a research candidate.
