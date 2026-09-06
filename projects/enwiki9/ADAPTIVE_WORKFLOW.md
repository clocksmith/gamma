# enwiki9 Adaptive Workflow

This is the command manual for enwiki9 research. Follow [AGENTS.md](AGENTS.md)
for permissions and evidence invariants, and the [record map](ledger/README.md#record-map)
for canonical storage. Run commands from `gamma/projects/enwiki9/`. Uppercase
names and angle-bracketed values are placeholders resolved from actual records.

The [active objective](contracts/research/v2/objective-contract.json) is
**99,000,000 complete bytes** with exact full-corpus reconstruction and independent
resource compliance. Preserve historical v1 bindings and its 105M milestone;
copied target values are not independent authority.

## Start And Find Records

```bash
python3 tools/enwiki9_lab.py start
python3 tools/enwiki9_lab.py records --search 'QUERY' --limit 20
python3 tools/enwiki9_lab.py records --candidate CANDIDATE --limit 20
python3 tools/enwiki9_lab.py records --view runs --state running
python3 tools/enwiki9_lab.py records --view reviews
python3 tools/enwiki9_lab.py records --view tools --search 'QUERY'
```

`start` reports local ownership, held work, record coverage, and next read
commands. These queries launch nothing and do not validate evidence or grant
execution authority. Follow source links and inspect actual host process
identities before source changes or resource-intensive work; a recorded running
state does not establish liveness.

Views are `algorithms`, `runs`, `notes`, `mixes`, `proposals`, `reviews`, and
`tools`. Algorithm/run lists focus on current work, retaining active queued jobs.
Use `--history` for retired, failed, rejected, or superseded candidates.
An explicit `--search`, `--candidate`, or `--state` also retrieves matching history.
Candidate detail retains lineage and run history. Search matches all words,
ignoring case; page with `--offset` and the returned `next_offset`.
Search also covers recorded reflection lessons, localized failure causes,
retired dimensions, uncertainties, and next actions. Before choosing a successor,
read the relevant candidate's reflection history and name the lesson being
applied or the uncertainty being tested. These are linked browsing projections;
validate the canonical reflection before using it to authorize a transition.
Reviews identify bound terminal jobs missing reflections; `--include-legacy`
also includes historical unbound jobs. Presence is not a scientific verdict.

The [tool catalogue](docs/tooling_inventory.md) indexes available utilities;
inspect a selected tool's source and `--help` before use. The
[ledger guide](ledger/README.md) covers browser navigation.

On “go”, find the next justified action and complete this loop:

```text
evidence -> frozen experiment -> proposal -> claim -> develop/seal
         -> bounded gate -> validated reflection -> recorded decision -> next action
```

A held gate or unrelated reflection backlog does not stop independent research.
Use this lifecycle rather than another launcher, queue, or chat-only notebook.

## Record The Discovery Boundary

Use the [canonical record map](ledger/README.md#record-map): considered ideas
and conclusions go in the research register, unmeasured batches in dated
portfolios, actionable experiments in adaptive proposals, and exact evidence
in results with its canonical run row.

Every algorithm that receives meaningful analysis must be recorded even when
it is rejected before implementation, merged into an existing lineage, parked,
or authorized only as an oracle. Such entries remain `idea`, `proxy`, `oracle`,
or `causal_shadow` and receive zero score credit.

A portfolio records evaluation and ranking; it does not create active work.
Promote only the selected bounded probes into adaptive proposals. Every
proposal must cite immutable predecessor receipts or other durable artifacts
through `--evidence`; changing narrative documents are linked from the register
but are not hash-bound proposal inputs.

After a decisive run, update both layers:

1. Preserve exact artifacts and the canonical run-ledger row.
2. Append the algorithm-level conclusion and next gate to
   `docs/research_register.md`.
3. Refresh generated inventories, frontier views, and operator status.

Process completion does not update scientific candidate status. Every terminal
revision-bound job must first receive one validated reflection:

```bash
python3 tools/enwiki9_lab.py reflect <job_id> \
  --validity valid \
  --validity-reason "<why the causal comparison is valid>" \
  --hypothesis-verdict supported \
  --hypothesis-rationale "<receipt-backed verdict>" \
  --failure-class algorithmic-gain \
  --localized-cause "<specific mechanism boundary>" \
  --causal-confidence high \
  --controls-equivalent true \
  --measurement 'netBytesSaved=results/<receipt>.json#/net_bytes_saved' \
  --lesson "<transferable mechanism lesson>" \
  --decision next-gate \
  --promotion-pass true \
  --kill-pass false \
  --next-gate-bytes 1000000 \
  --decision-rationale "<smallest justified successor gate>" \
  --evidence results/<receipt>.json
```

Measurements are accepted only through hash-linked JSON-pointer assertions.
Use the field matching the evidence unit: archive deltas use `netBytesSaved`,
teacher probability shadows use `idealBitsSaved`, transformed populations use
`scopeSymbols`, and transfer or segment measurements retain their explicit
fraction fields. Do not relabel ideal bits as archive bytes.
Invalid, infrastructure-failed, implementation-failed, or incomplete runs can
only be retried or held; they cannot promote or retire the algorithm. Promotion
requires valid controls, a supported hypothesis, an algorithmic-gain
attribution, and explicit promotion/kill predicate results. The receipt then
updates derived candidate status without changing semantic source identity.
Any explicit `--retired-dimension` is also projected into a deterministic OMEGA
exclusion whose evidence points back to the reflection. The reflection remains
authoritative; the exclusion is searchable mechanism memory and grants no
measurement or promotion credit. Backfill and audit the projection with
`enwiki9_lab.py sync-reflection-exclusions`.

### Record a closed comparison

Use `record_driver_result.py --terminal-index` to record a reviewed set of arms
in one command. Have the runner or terminal normalization step retain an index
before creating its reflection, then include the index in `reflect --evidence`.
The index is an evidence artifact alongside the results, not a separate registry.

Its format is `gamma.enwiki9.terminal-result-index.v1`: `job` and `guard` are
project-relative `{ "path": "...", "sha256": "..." }` references; `arms` is a
nonempty list of `{ "arm": "P", "result": REF, "artifacts": { ... } }` objects.
The optional `evidence` list binds additional files. Each result is a normalized
driver receipt carrying its arm, candidate revision, and canonical job path as
`run_source`. Artifacts named `archive`, `restored`, and `repeat` must substantiate
the corresponding size, exact-inverse, and deterministic-repeat claims. Every
claimed successful repeat needs a separately retained artifact. Missing optional
diagnostics remain missing; missing evidence needed for a claim rejects recording.

After the reflection validates:

```bash
python3 tools/record_driver_result.py CANDIDATE \
  --terminal-index results/CANDIDATE/terminal-index.json --check
python3 tools/record_driver_result.py CANDIDATE \
  --terminal-index results/CANDIDATE/terminal-index.json
python3 tools/enwiki9_normalize_receipts.py --profile routine --json
```

The recorder verifies the closed job and resource guard, existing reflection,
and exact artifact hashes. It writes distinct job-and-arm ledger identities and
a derived metadata projection; it does not choose a scientific verdict. A retry
can finish an interrupted row set or metadata update without duplicating rows.
Changed receipts and conflicting claims fail closed. A torn ledger line is
preserved for explicit repair. Calls to this recorder serialize with one another;
coordinate other ledger or metadata writers separately because they do not honor
its lock.
The legacy `--result`/`--label` metadata command remains available for historical
formats and does not provide these terminal-publication guarantees.

Diagnostic discovery guards are checked against their frozen cgroup allocation:
the recorder adjusts the prize schema's fixed memory constant in memory and
reports `discovery-budget-schema`. Qualification uses the unchanged validator.
Neither recording mode grants resource qualification or launch permission.

Rank actionable proposals after reflection with:

```bash
python3 tools/enwiki9_lab.py next-experiment
```

The ordering is versioned in `contracts/research/v1/search-policy.json`. It is
lexicographic and fail-closed: a valid frozen experiment and validated parent
evidence outrank unsupported activity; asserted net bytes, transfer retention,
runtime, and memory remain distinct; expected savings are reduced by maximum
package cost; lower uncertainty and interaction risk break later ties; manual
priority comes after evidence and cost. Ranking does not change measured values
or authorize a gate.

Before combining measured mechanisms, create a validated mechanism graph under
`operations/adaptive/composition/`. Mark shared probability boundaries,
overlapping costs, causal compatibility, closed-teacher dependencies, and the
exact joint replay required. Never add component forecasts or causal-shadow
ideal bits to an archive result.

## Compose prize-facing evidence

An exact gate result is not a prize-facing package receipt. After a candidate
reaches full-1G eligibility, stage a new dependency bundle with
`tools/enwiki9_dependency_closure.py`. Declare the build, compression, and
decompression command arrays, every dependency and license, all required option
bytes, and the exact package entry point. Missing closure state remains explicit
and cannot promote.

Replay that immutable bundle with `tools/enwiki9_clean_room_replay.py`. The
executor uses two independent fresh builds for deterministic compression and a
third fresh build for decode. The decode sandbox receives only the counted
package and archive, never the canonical corpus. All runtime phases are
single-core and carry wall-time, process-tree memory, and temporary-disk guard
receipts. The composed receipt remains below `objective-achieved` until a
different host reproduces the same candidate tree and archive and its complete
primary receipt is locally hash-bound.

Do not retrofit ordinary driver rows into package receipts. A clean-room replay
starts from the dependency manifest, and any package or command change requires
a new bundle and new receipts. Regenerate `docs/release_receipt_index.json` with
`tools/enwiki9_release_receipts.py` so the bundle is discoverable; the index is
a structural router, not proof that its large artifacts were rehashed.

## Discover And Propose Algorithms

Search prior results, lineage, and scoped exclusions before choosing a mechanism:

```bash
python3 tools/enwiki9_lab.py exclusions
python3 tools/enwiki9_lab.py productivity
```

Use primary papers, authors' implementations, and current official prize sources.
Pin source and asset identities, inspect licensing and model provenance, and
keep external results separate from Gamma's attributable modifications. The
[competitive frontier](operations/provenance/competitive_frontier_v1.json) records
dated sources; a changed objective needs a new version, not rewritten history.

OMEGA preserves negative mechanism knowledge and productive lineages; it is
search machinery with zero score credit. Record a scoped negative result with:

```bash
python3 tools/enwiki9_lab.py exclude <exclusion_id> \
  --mechanism "<information source or coding mechanism>" \
  --population "<exact measured population>" \
  --failure "<receipt-backed terminal failure>" \
  --retired-dimension "<dimension no longer worth sweeping>" \
  --unsettled-successor "<materially different successor>" \
  --evidence <receipt>
```

Do not rename retired Fiber-FOSSIL exact retrieval as a new experiment. HARM
causal edit alignment and compact MIDAS require their own measured comparisons.
Choose one challenger per lane and diagnose opportunity scarcity, parent
redundancy, calibration, state interference, or runtime before changing a mechanism.

Freeze the parent, hypothesis, changed mechanism, development budget, selection
population, sealed confirmation, package estimate, resources, and stop rule.
Budgeted parameter selection belongs on development data; freeze the candidate
before confirmation. Forecast-based stops are budget decisions, not impossibility
proofs. Smaller package-paying gains may remain components; combinations still
need fresh joint archives.

Algorithm discovery is separate from gate discovery. Freeze and validate
`operations/adaptive/experiments/<id>.json` before recording a proposal or
writing candidate source:

```bash
python3 tools/enwiki9_lab.py propose <proposal_id> \
  --title "<mechanism>" \
  --hypothesis "<falsifiable hypothesis>" \
  --mechanism-class endpoint \
  --expected-savings-bytes <bytes> \
  --max-program-bytes <bytes> \
  --promotion "<numeric promotion condition>" \
  --kill "<numeric kill condition>" \
  --experiment operations/adaptive/experiments/<id>.json \
  --mechanism-change change_coded_alphabet \
  --interface "<clean interface exposed to descendants>" \
  --retired-neighborhood "<negative neighborhood this does not repeat>" \
  --evidence <immutable-receipt>
```

Mechanism classes are `substrate`, `endpoint`, `representation`, and `coder`.
Keep orthogonal proposals active rather than collapsing search into one tuning
ladder.

The search policy favors deleting predictor work, changing the coded alphabet
or update schedule, replacing representation, adding a state coordinate,
compiling a state machine, and adding a macro family over parameter tuning or
mixture expansion. These priorities affect ordering only, never measured values
or promotion authority; see `contracts/research/v1/search-policy.json`.

For more than eight independently positive components, do not enumerate the
full subset lattice. Measure singles, screen pairs, use branch-and-bound,
select a small number of triples, and reserve the full lattice for the final
small set.

List and claim proposals:

```bash
python3 tools/enwiki9_lab.py proposals
python3 tools/enwiki9_lab.py claim <proposal_id> --owner <owner>
```

Dependency-gated proposals carry `operational_status: dormant_dependency` and
structured `activation_requirements`. They cannot be claimed or developed
until an operator verifies the required terminal receipts and records that
evidence explicitly:

```bash
python3 tools/enwiki9_lab.py activate-proposal <proposal_id> \
  --evidence results/<dependency>/decision.json
```

Claim is valid only from `proposed`; development is valid only from `claimed`.
Parked, blocked, and dormant proposals fail closed rather than relying on a
human remembering their prose ordering. A prospectively sealed recovery
candidate that already exists in `developed` state may be activated in place,
but only after the activation verifier binds both its terminal dependency
result and the unique valid reflection over that exact result. Enqueue
independently requires `operational_status: actionable`, so source availability
cannot bypass the receipt gate.

Materialize a claimed proposal as a candidate:

```bash
python3 tools/enwiki9_lab.py develop \
  <proposal_id> <candidate_id>
```

Proposal state is durable under `operations/adaptive/proposals/`. Developing a
proposal records its candidate ID and mutation lineage.

Do not create proposals for every brainstormed portfolio row. Create one only
when the hypothesis, causal contract, exact control, source budget, promotion
gate, and kill gate are concrete enough to run.

## Create

Create a blank candidate:

```bash
python3 tools/enwiki9_lab.py new <candidate_id> \
  --hypothesis "<falsifiable hypothesis>"
```

This creates:

```text
programs/<candidate_id>/program.py
programs/<candidate_id>/meta.json
```

Implement `compress(data)` and `decompress(archive)` in `program.py`.

`new`, `mutate`, and `develop` create a content-addressed candidate-revision
receipt. After implementing a new scaffold or making any pre-measurement edit,
seal the exact tree explicitly:

```bash
python3 tools/enwiki9_lab.py seal <candidate_id> \
  --hypothesis "<falsifiable mechanism claim>" \
  --change "<complete semantic change>" \
  --evidence <proposal-or-design-receipt>
```

The receipt stores immutable, deduplicated source blobs under
`operations/adaptive/candidate-blobs/`, binds the parent and previous revision,
and records normalized semantic metadata. Derived `meta.json` status and
measurement fields do not change algorithm identity. Once a candidate has any
queued or measured evidence, source drift is rejected and the edit must use a
new candidate ID.

## Mutate

Every mutation gets a new candidate ID. Never mutate an active or previously
measured candidate in place.

Clone a parent:

```bash
python3 tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<one changed mechanism and expected byte effect>"
```

For a small deterministic source mutation:

```bash
python3 tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<hypothesis>" \
  --replace 'OLD_TEXT=NEW_TEXT'
```

The clone removes inherited measurements and records the parent, hypothesis,
creation event, and source replacements in
`operations/adaptive/mutations.jsonl`.

V3 queue receipts bind the proposal identity and digest, prospectively frozen
experiment, sealed tree, candidate-revision receipt, and runner digest. Workers validate every
binding and execute a read-only materialization from immutable blobs, not the
mutable `programs/<id>/` working tree. A candidate with an unreflected terminal
v2/v3 job cannot enter another gate or produce a successor. Legacy unbound jobs
cannot execute; queue a revision-bound retry. A legacy candidate receives an explicit
`legacy-current-state` receipt, which captures its current source without
claiming retroactive identity for old measurements.

Guarded tool jobs that write candidate-owned artifacts declare each required
directory with `enqueue-tool --scratch-directory results/<candidate_id>/...`.
The executor validates that boundary and materializes the directory before the
guard preflight; the inner tool still declares the same path to the guard.

When a frozen experiment fails only in its implementation, create a new
candidate and use `tools/enwiki9_freeze_implementation_retry.py` to inherit the
scientific population, hypothesis, controls, metrics, and decision predicates.
The command permits only explicit rebinding of the parent revision, runner,
materializer, failure evidence, negative control, outputs, and implementation
delta; it refuses to overwrite an existing frozen contract.

## Queue

Queue an exact codec gate with its frozen discovery resource envelope:

```bash
python3 tools/enwiki9_lab.py enqueue CANDIDATE \
  --gate-size SCOPE --purpose candidate --tag LANE \
  --mode discovery --cpu-set CPU_SET \
  --memory-limit-bytes MEMORY_BYTES --disk-limit-bytes SCRATCH_BYTES \
  --wall-time-limit-seconds STOP_SECONDS --cgroup-parent DELEGATED_CGROUP_PARENT
```

Supply `--archive-ceiling BYTES` when the contract freezes an archive kill bound.
The first archive and repeat obey it; an exceeded bound skips decode/re-encode
and remains a budget decision. Worker count alone is not a memory guard.

Discovery may share the host under admission controls. Unknown ownership blocks
admission, and legacy jobs without an explicit mode remain held. Qualification
uses `--mode qualification` with a bound calibration plan/receipt and exclusive
lease; consult `enqueue --help` for their arguments. Concurrent timing remains
diagnostic. A candidate with a nested guard must declare its exact cgroup and
memory allocation; the aggregate budget includes coordination overhead and the
deadline covers all owned processes.

A simulation, proxy, infrastructure check, or oracle uses the same lifecycle:

```bash
python3 tools/enwiki9_lab.py enqueue-tool CANDIDATE \
  --tool tools/TOOL.py --purpose diagnostic --gate-size SCOPE \
  --mode discovery --cpu-set CPU_SET \
  --memory-limit-bytes MEMORY_BYTES --disk-limit-bytes SCRATCH_BYTES \
  --wall-time-limit-seconds STOP_SECONDS --cgroup-parent DELEGATED_CGROUP_PARENT
```

Pass arguments with repeated `--tool-arg=VALUE`. Declare required precreated
paths with `--scratch-directory results/CANDIDATE` and follow the selected tool's
output contract. Tool purposes are `diagnostic`, `infrastructure`, or `oracle`;
simulation describes the experiment, not a CLI purpose. These jobs get zero
score credit.

Tool paths are restricted to `projects/enwiki9/tools/`. Tool jobs cannot use a
score-bearing purpose and never update candidate lifecycle or frontier credit.
The tool digest is bound as the v3 runner, and the candidate's proposal-bound
experiment is inferred unless `--experiment` is supplied to assert the same
reference explicitly.

Only `candidate`, `proof`, and `adaptive_discovery` exact gates may update
scientific status after validated reflection. Infrastructure checks can prove
imports, compilation, inversion, or determinism; they cannot promote or retire
an algorithm without its frozen scientific comparison.

Jobs move atomically through `operations/adaptive/{pending,running,completed,
failed,cancelled}/`. Queue after source sealing and explicit resource binding.

Each candidate-and-scope pair runs once unless an operator explicitly uses
`--force`.

A pending job may be made durable but unclaimable without cancelling its queue
identity:

```bash
python3 tools/enwiki9_lab.py hold <job_id> --reason <reason>
python3 tools/enwiki9_lab.py release <job_id> --reason <evidence>
```

Workers always skip `held: true` jobs, including generic adaptive workers.
Release only when the recorded dependency or portfolio decision is satisfied.

## Adaptive Gate Discovery

Preview the next missing exact gate for eligible candidates:

```bash
python3 tools/enwiki9_lab.py discover-gates --dry-run
```

Queue those gates:

```bash
python3 tools/enwiki9_lab.py discover-gates
```

The exact gate ladder is:

```text
1K -> 250K -> 1M -> 10M -> 100M -> 1G
```

A scope counts as passed only with exact roundtrip and deterministic replay.
Choose diagnostic populations appropriate to the mechanism: opening and distant
populations can differ, and history-dependent tests need causal warmup through a
verified checkpoint or prefix replay. A cold 10M run cannot exercise matches
requiring over 100M transformed bytes. Frontend coordinates must agree before
reusing sealed parent traces; WRT and token traces are not interchangeable.
Adaptive discovery does not infer success from forecasts or process state.

## Run

After publishing ownership, run the named eligible gate:

```bash
python3 tools/enwiki9_lab.py run --candidate CANDIDATE --max-workers 1
```

Use `run --adaptive --continuous` only within the authorized ownership and
resource envelope; `--max-workers` and admission limits do not replace each
job's frozen guards.

The runner adapts to current one-minute system load and available memory before
claiming a batch. Independent gates may run concurrently up to the configured
worker and resource limits. Every job uses its own durable ID, log, and output
paths.

After each terminal batch, the runner refreshes the candidate inventory once,
then the routine views: upper-bound certificate, run ledger, release index,
evidence matrix, best results, status, and searchable ledger. Status consumes
the SHA-256-bound inventory snapshot instead of running the inventory scan
again. Snapshot identity does not establish current filesystem or host state.

Worker output is stored in `run_logs/adaptive/<job_id>.log`.

## Observe And Control

Show current jobs, recent outcomes, load, and available memory:

```bash
python3 tools/enwiki9_lab.py status
```

Cancel a pending job:

```bash
python3 tools/enwiki9_lab.py cancel <job_id>
```

Refresh generated views without launching a gate:

```bash
python3 tools/enwiki9_lab.py refresh
```

To update routine views using the existing inventory, or explicitly regenerate
and check all historical reports:

```bash
python3 tools/enwiki9_normalize_receipts.py --profile routine --json
python3 tools/enwiki9_normalize_receipts.py --profile full --json
```

Routine refresh leaves historical memory, residual, retrieval, fingerprint,
and tool-catalogue reports untouched. Its receipt lists omitted generators;
status labels those reports as potentially stale. Full refresh scans the
inventory once and reuses its exact snapshot for both status generation and
validation. Normalization stops and exits nonzero at the first failed command.
The legacy `lab refresh` wrapper prints child return codes; inspect them because
its own exit code does not propagate failures. For an automation success gate,
use the normalizer directly. `--skip-check` skips validation, not disclosure.

Stop a continuous runner with the normal process interrupt. Pending and
terminal job records remain durable.

## Cross-Device Operation

Git is the replication layer for algorithms and evidence. Active processes,
resource usage, and logs still being written are host-local.

Before work on another device, start from the project root:

```bash
cd ../../..
./rdpull.sh
cd gamma/projects/enwiki9
python3 tools/enwiki9_lab.py start
```

Before a resource-intensive run, pull, claim and queue the unique work, publish
ownership, then inspect the selected host's process identities and available
memory/storage. Do not infer cross-device liveness from committed status.

After a terminal result or decisive research conclusion:

```bash
python3 tools/enwiki9_lab.py refresh
cd ../../..
./rdpush.sh
```

The pushed handoff must contain the proposal transition, candidate metadata,
exact receipt, `results/run_ledger.jsonl` row, research-register conclusion,
and refreshed status. Logs that are still being written are not durable
evidence. A committed status receipt describes the producing host at its
timestamp; it is not proof that the process remains live elsewhere.

## Executable Comparison And Release Checks

[lib/predictor.py](lib/predictor.py) defines Q16 pre-truth bit probabilities,
decoded-bit updates, deterministic initialization, serialization, digests, and
frontend/trace identities. Its arithmetic codec is a correctness fixture.
Other frontends need explicit adapters.

The existing [driver](lib/driver.py) accepts `--comparison SPEC.json --limit BYTES
--output results/CANDIDATE/NEW_RUN`. A candidate supplies `compress_arm` and
`decompress_arm`; the specification binds parent, bookkeeping, treatment and
applicable controls, plus hypothesis, changed mechanism, development budget,
selection and sealed confirmation populations, and stop rule. Run comparisons
through the frozen queued candidate. Retain archives, restored bytes, repeats,
and first-divergence diagnostics before publishing an atomic decision. Missing
optional telemetry stays explicit; missing mandatory evidence blocks promotion.
Matching sizes alone do not establish encoder/decoder state agreement.

Exercise the existing predictor and packaging tools without installation:

```bash
python3 -m unittest discover -s tests -p test_enwiki9_predictor_driver.py -v
python3 -m unittest discover -s tests -p test_enwiki9_release_canary.py -v
python3 tools/enwiki9_clean_room_replay.py --verify-canary results/release_canary_rle_q0_v1/release/20260905_acceptance_v1/canary-receipt.json
```

For a fresh release canary, use `python3 tests/test_enwiki9_release_canary.py
--bundle results/release_canary_rle_q0_v1/release/NEW_RECEIPT`. This exercises three
independent builds, exact reconstruction, repeat archives, missing-file rejection,
and license reporting with zero objective credit. The
[prize-facing package procedure](#compose-prize-facing-evidence) remains separate.

Before submission, confirm the accepted reference and accounting with the
committee, prepare public source/package and an algorithm explanation, document
authorship and external contributions, and provide build/encode/decode commands.
The [committee inquiry](workbench/committee-inquiry.eml) is prepared but unsent;
sending it requires an authorized sender and email channel.
