# enwiki9 Candidate Organization

This project treats every compressor attempt as a candidate program with a
tracked source contract, tracked metadata, and measured evidence. The goal is to
make the candidate pool ready for open-ended search without allowing abandoned
or undocumented experiments to pollute the active set.

## Directory Contract

Active candidates live under:

```text
projects/enwiki9/programs/<candidate_id>/
```

Every active candidate must have:

- `program.py`: defines `compress(data: bytes) -> bytes` and `decompress(data: bytes) -> bytes`.
- `meta.json`: declares the candidate identity, provenance, dependencies, and genotype hints.
- An entry in `index.json`.
- At least one valid roundtrip result before it can be used as training signal for search.

Generated and local-only artifacts stay outside the tracked candidate contract:

- `projects/enwiki9/data/enwik9`
- `projects/enwiki9/data/enwik9.zip`
- `projects/enwiki9/build/`
- `projects/enwiki9/results/`
- `__pycache__/`

Benchmark evidence is summarized in tracked reports and inventories instead of
tracking every generated result file.

## External Source Boundary

External compressor code must not remain as an undocumented untracked checkout.
Use one of these boundaries:

- Direct vendoring: track the raw source files in the parent repository.
- Submodule: track a fetchable commit through `.gitmodules`.
- Patch overlay: track the upstream commit plus a patch file that reconstructs
  local modifications.

`external/fx2-cmix/` currently uses the patch overlay boundary:

- `external/fx2-cmix.vendor.json` records upstream provenance.
- `external/fx2-cmix.local.patch` records local source modifications.

This is a non-destructive holding pattern. It preserves local changes while
leaving the nested checkout metadata intact. Convert it to direct vendoring only
after deciding that the parent repository should own every raw `fx2-cmix` file.

## Lifecycle

| State | Meaning | Required action |
|---|---|---|
| `draft` | Source exists but the contract is incomplete. | Add metadata and registry entry, or retire it. |
| `candidate` | Contract is complete but benchmark evidence is missing. | Run a same-scope roundtrip benchmark. |
| `active` | Contract is complete and valid measured evidence exists. | Eligible for search and crossover. |
| `measured_negative` | Valid roundtrip loses on score but preserves distinct mechanism evidence. | Keep as evidence; do not use as a winner. |
| `blocked_dependency` | Contract exists but the local substrate is missing or broken. | Fix dependency or retire. |
| `track_source_before_evolution` | Source exists outside the safe Git boundary. | Track or document source boundary before scoring. |
| `retired` | Contract fails, roundtrip fails, or measured value is absent after audit. | Keep only if documented as a negative result. |

## Lane 0 Evidence Hygiene

Lane 0 is the shared intake gate for the existing cleanup queue and every new
Lane B candidate. It answers one question before a program can become a parent,
control, or frontier point: does the candidate have a complete contract and
valid same-scope evidence?

Use the dry-run view first:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --limit-candidates 10
```

The dry-run reads `candidate_inventory.json`, selects `benchmark_or_retire`
candidates by default, and prints the locked gate plan. It does not score or
write metadata.

Scoring requires an explicit bounded run:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --run --limit-candidates 1
```

To let the script update each candidate's `meta.json` with `lane0_triage`
measurements and a proposed lifecycle status:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --run --update-meta --limit-candidates 1
```

Do not wrap `candidate_triage.py` in another `flock`. The script runs each
`lib/driver.py` gate through:

```text
flock -n -E 75 /tmp/enwiki9-heavy.lock python3 projects/enwiki9/lib/driver.py ...
```

It also runs a process preflight before every gate using the heavy-process
pattern `bench.py|lib/driver.py|cmix|qm_context|enwik9`. If another scoring
process is visible or the non-blocking lock is already owned, triage stops
without launching a benchmark. A busy lock is treated as a transient scheduler
block; `--update-meta` does not write candidate lifecycle changes for that
lock-only outcome.

Default gates are:

- 1 KiB deterministic roundtrip against `baseline_lzma`.
- 250000-byte deterministic roundtrip against the same baseline.

Outcomes:

- Import, contract, roundtrip, or determinism failure: `retired`.
- Missing local substrate: `blocked_dependency`.
- Busy scoring slot: stop without changing candidate status.
- Valid deterministic score win: `active`.
- Valid deterministic loser with useful evidence: `measured_negative`.

This is the pruning path for the `benchmark_or_retire` queue. It should run
before any naming cleanup. Renaming should only touch candidates that Lane 0 has
classified as `active`, `measured_negative`, or explicitly useful controls.

## Retire Criteria

Retire or repair a candidate when any of these are true:

- `program.py` is missing.
- `meta.json` is missing or its `id` does not match the directory name.
- The candidate is absent from `index.json`.
- Source files are untracked.
- No valid `roundtrip_ok == true` result exists after an explicit benchmark.
- It duplicates another candidate without a measured improvement or a distinct mechanism.

Deletion is not the first step. First classify the candidate, preserve useful
negative evidence in documentation, then remove or move the source only when the
audit has a concrete reason.

## PGSG Mapping

The Polymorphic Graph-Schema Genotype (PGSG) layer maps each compressor attempt
onto a DAG-like candidate schema:

- Nodes represent functional units: parser, transform, sort, sidecar, entropy
  model, backend codec, dictionary, or parameter controller.
- Edges represent byte streams, token streams, sidecars, receipts, dictionaries,
  or execution dependencies.
- Payloads carry continuous parameters, discrete options, and structural
  subgraphs.

Recommended `meta.json` extension:

```json
{
  "id": "example_candidate_v1",
  "description": "short mechanism description",
  "added": "2026-06-07",
  "deps": [],
  "status": "candidate",
  "family": "fx2_sidecar",
  "pgsg": {
    "nodes": [
      {
        "id": "preprocess",
        "type": "transform",
        "payload": {
          "discrete": {"mode": "byte_split"},
          "continuous": {},
          "structural": {}
        }
      },
      {
        "id": "backend",
        "type": "codec",
        "payload": {
          "discrete": {"codec": "xz"},
          "continuous": {"preset": 9},
          "structural": {}
        }
      }
    ],
    "edges": [
      {"from": "preprocess", "to": "backend", "stream": "payload"}
    ]
  }
}
```

The PGSG block is descriptive until the search runner consumes it. The audit
tool does not require it yet, but every new candidate should include enough
family and mechanism metadata to let a future graph search compare structure
rather than just directory names.

## Lane B Intake

Lane B is reserved for novel mechanisms such as macro-residual edit scripts,
layout grammar templates, page-order selectors, VM-trace sidecars, and online
prefix dictionaries. Each new Lane B program starts with:

- `status: "candidate"`
- a complete `program.py`/`meta.json` contract
- a `pgsg` block that names the mechanism and backend
- registration in `index.json`

After creation, Lane B candidates use Lane 0 triage before promotion:

```bash
python3 projects/enwiki9/tools/candidate_triage.py --candidate <id>
python3 projects/enwiki9/tools/candidate_triage.py --run --update-meta --candidate <id>
```

Only `active` or `measured_negative` Lane B outputs should become named
frontier points or parents for later search.

## Audit Command

Run:

```bash
python3 projects/enwiki9/tools/candidate_audit.py --write
```

This refreshes:

- `projects/enwiki9/candidate_inventory.json`
- `projects/enwiki9/CANDIDATE_INVENTORY.md`

Use the inventory before staging or deleting candidates. The action list tells
you which candidates are active, which need benchmark evidence, which have
untracked source, and which should be retired or repaired.
