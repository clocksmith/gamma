# enwiki9 Adaptive Workflow

This is the primary operating workflow for enwiki9 research.

All proposal, mutation, gate, and promotion decisions are subordinate to the
versioned objective in `contracts/research/v1/objective-contract.json`.
Receipts must eventually bind its canonical SHA-256; copied target values are
not independent authority.

The loop is:

```text
analyze evidence
-> freeze a structured experiment contract
-> propose and rank a mechanism against that contract
-> claim and develop
-> create or mutate
-> queue
-> run the smallest missing exact gate
-> record result and lifecycle state
-> refresh inventories and reports
-> promote, retry explicitly, mutate, or retire
```

OMEGA is the archive-search layer inside this loop. It does not compress data
and receives no score credit. It preserves negative mechanism knowledge,
prioritizes mechanism changes over parameter changes, and retains productive
lineages even when an ancestor is not an immediate score leader.

Before proposing a successor in a measured neighborhood, inspect exclusions:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py exclusions
python3 projects/enwiki9/tools/enwiki9_lab.py productivity
```

Record a decisive negative result:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py exclude <exclusion_id> \
  --mechanism "<information source or coding mechanism>" \
  --population "<exact measured population>" \
  --failure "<receipt-backed terminal failure>" \
  --retired-dimension "<dimension no longer worth sweeping>" \
  --unsettled-successor "<materially different successor>" \
  --evidence <receipt>
```

Use `tools/enwiki9_lab.py` for this loop. Do not build separate ad hoc launchers
or keep experiment state only in chat.

## Record The Discovery Boundary

The project has four distinct durable layers. Do not collapse them:

```text
considered idea or conclusion
    -> docs/research_register.md

ranked batch of unmeasured ideas
    -> dated docs/*portfolio*.md and docs/*portfolio*.json

actionable falsifiable experiment
    -> operations/adaptive/proposals/

completed exact evidence
    -> results/<candidate_id>/ and results/run_ledger.jsonl
```

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
python3 projects/enwiki9/tools/enwiki9_lab.py reflect <job_id> \
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

Rank actionable proposals after reflection with:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py next-experiment
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
a new bundle and new receipts.

## Discover And Propose Algorithms

Algorithm discovery is separate from gate discovery. Freeze and validate
`operations/adaptive/experiments/<id>.json` before recording a proposal or
writing candidate source:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py propose <proposal_id> \
  --title "<mechanism>" \
  --hypothesis "<falsifiable hypothesis>" \
  --mechanism-class endpoint \
  --expected-savings-bytes <bytes> \
  --max-program-bytes <bytes> \
  --promotion "<numeric promotion condition>" \
  --kill "<numeric kill condition>" \
  --experiment projects/enwiki9/operations/adaptive/experiments/<id>.json \
  --mechanism-change change_coded_alphabet \
  --interface "<clean interface exposed to descendants>" \
  --retired-neighborhood "<negative neighborhood this does not repeat>" \
  --evidence <immutable-receipt>
```

Mechanism classes are `substrate`, `endpoint`, `representation`, and `coder`.
Keep orthogonal proposals active rather than collapsing search into one tuning
ladder.

Mechanism-change classes receive an explicit search bonus or penalty:

```text
favor:
  delete_predictor_work
  change_coded_alphabet
  change_update_schedule
  replace_representation
  add_state_coordinate
  compile_state_machine
  add_macro_family

penalize:
  parameter_tuning
  mixture_expansion
```

The bonus changes search ordering only. It never changes measured archive
bytes, counted package bytes, runtime, memory, or promotion gates.

For more than eight independently positive components, do not enumerate the
full subset lattice. Measure singles, screen pairs, use branch-and-bound,
select a small number of triples, and reserve the full lattice for the final
small set.

List and claim proposals:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py proposals
python3 projects/enwiki9/tools/enwiki9_lab.py claim <proposal_id> --owner <owner>
```

Dependency-gated proposals carry `operational_status: dormant_dependency` and
structured `activation_requirements`. They cannot be claimed or developed
until an operator verifies the required terminal receipts and records that
evidence explicitly:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py activate-proposal <proposal_id> \
  --evidence results/<dependency>/decision.json
```

Claim is valid only from `proposed`; development is valid only from `claimed`.
Parked, blocked, and dormant proposals fail closed rather than relying on a
human remembering their prose ordering.

Materialize a claimed proposal as a candidate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py develop \
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
python3 projects/enwiki9/tools/enwiki9_lab.py new <candidate_id> \
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
python3 projects/enwiki9/tools/enwiki9_lab.py seal <candidate_id> \
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
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<one changed mechanism and expected byte effect>"
```

For a small deterministic source mutation:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
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

Queue an explicit gate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py enqueue <candidate_id> \
  --gate-size 1000000 \
  --archive-ceiling <exact-kill-bytes> \
  --purpose candidate \
  --tag <lane>
```

Use `--archive-ceiling` whenever the proposal has a frozen archive kill bound.
The runner forwards it to both the first archive and deterministic-reencode
checks. Exceeding the ceiling skips decompression and re-encode rather than
spending the serialized lane on a result that is already terminal.

Queue a receipt-producing diagnostic, infrastructure, or oracle tool through
the same durable lifecycle:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py enqueue-tool <candidate_id> \
  --tool tools/<tool.py> \
  --tool-arg <argument> \
  --purpose oracle \
  --gate-size 1000000
```

Tool paths are restricted to `projects/enwiki9/tools/`. Tool jobs cannot use a
score-bearing purpose and never update candidate lifecycle or frontier credit.
The tool digest is bound as the v3 runner, and the candidate's proposal-bound
experiment is inferred unless `--experiment` is supplied to assert the same
reference explicitly.

Job purpose controls lifecycle mutation:

```text
candidate, proof, adaptive_discovery
    -> exact triage may update candidate status

infrastructure, diagnostic, oracle
    -> preserve receipts but never update candidate status
```

An infrastructure smoke may prove imports, compilation, roundtrip, or
determinism. It cannot retire or promote the underlying algorithm unless a
separate candidate gate covers the proposal's frozen population and metric.

Create or mutate and immediately queue:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<hypothesis>" \
  --enqueue
```

Jobs move atomically through:

```text
operations/adaptive/pending/
operations/adaptive/running/
operations/adaptive/completed/
operations/adaptive/failed/
operations/adaptive/cancelled/
```

Each candidate-and-scope pair runs once unless an operator explicitly uses
`--force`.

A pending job may be made durable but unclaimable without cancelling its queue
identity:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py hold <job_id> --reason <reason>
python3 projects/enwiki9/tools/enwiki9_lab.py release <job_id> --reason <evidence>
```

Workers always skip `held: true` jobs, including generic adaptive workers.
Release only when the recorded dependency or portfolio decision is satisfied.

## Adaptive Gate Discovery

Preview the next missing exact gate for eligible candidates:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py discover-gates --dry-run
```

Queue those gates:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py discover-gates
```

The exact gate ladder is:

```text
1K -> 250K -> 1M -> 10M -> 100M -> 1G
```

A scope counts as passed only when candidate metadata records exact roundtrip
and deterministic replay. Adaptive discovery selects the next larger scope; it
does not infer success from forecasts, partial archives, or process state.

## Run

Run one available batch:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py run --max-workers 4
```

Continuously discover and run work on demand:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py run \
  --adaptive \
  --continuous \
  --max-workers 4 \
  --min-free-mib 4096
```

The runner adapts to current one-minute system load and available memory before
claiming a batch. Independent gates may run concurrently up to the configured
worker and resource limits. Every job uses its own durable ID, log, and output
paths.

After each terminal batch, the runner serially refreshes:

```text
candidate_inventory.json
CANDIDATE_INVENTORY.md
results/run_ledger.jsonl-derived views
evidence and best-result views
memory and residual reports
artifact fingerprint audit
status receipt
```

Worker output is stored in `run_logs/adaptive/<job_id>.log`.

## Observe And Control

Show current jobs, recent outcomes, load, and available memory:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py status
```

Cancel a pending job:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py cancel <job_id>
```

Refresh generated views without launching a gate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py refresh
```

Stop a continuous runner with the normal process interrupt. Pending and
terminal job records remain durable.

## Cross-Device Operation

Git is the replication layer for algorithms and evidence. Active processes,
resource usage, and logs still being written are host-local.

Before work on a device:

```bash
cd /home/clocksmith/deco
./rdpull.sh
cd gamma
python3 projects/enwiki9/tools/enwiki9_lab.py status
```

Before a resource-intensive run:

1. Pull current state.
2. Claim the proposal and queue a unique candidate-and-scope gate.
3. Push the ownership record before another host begins related work.
4. Inspect the selected host's process table and available memory and storage.

After a terminal result or decisive research conclusion:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py refresh
cd /home/clocksmith/deco
./rdpush.sh
```

The pushed handoff must contain the proposal transition, candidate metadata,
exact receipt, `results/run_ledger.jsonl` row, research-register conclusion,
and refreshed status. Logs that are still being written are not durable
evidence. A committed status receipt describes the producing host at its
timestamp; it is not proof that the process remains live elsewhere.

## Promotion And Kill Rules

- Start with the smallest decisive gate.
- State the hypothesis, baseline, expected byte leverage, promotion condition,
  and kill condition in candidate metadata.
- Promote only exact roundtrip and deterministic evidence at the measured
  scope.
- Before a larger gate, include counted program cost and remaining target debt.
- A failed implementation retires that candidate, not the entire algorithm
  family.
- A retry requires `--force` and a recorded reason; a source change requires a
  new candidate ID.
- Never edit candidate source underneath a running job.
- Never treat a partial archive, forecast, oracle, teacher, or shadow result as
  a full official score.

## Source Of Truth

| Question | Source |
|---|---|
| What algorithms have been considered, merged, parked, or rejected? | `docs/research_register.md` |
| What unmeasured batches and rankings were recorded? | The dated `docs/*portfolio*.md` and `docs/*portfolio*.json` named by the research register |
| What algorithms are proposed or claimed? | `operations/adaptive/proposals/` |
| What work is queued or running? | `operations/adaptive/<state>/` |
| How was a candidate derived? | `operations/adaptive/mutations.jsonl` and `programs/<id>/meta.json` |
| What did a worker emit? | `run_logs/adaptive/<job_id>.log` |
| What exact run was recorded? | `results/<id>/` and `results/run_ledger.jsonl` |
| What is each candidate's lifecycle? | `candidate_inventory.json` |
| What source-bound evidence affects the target? | `docs/hutter_frontier.json` and `docs/hutter_run_ledger.json` |
| What is the current proof boundary? | `docs/status_receipt.md` and `UPPER_BOUND_CERTIFICATE.md` |
