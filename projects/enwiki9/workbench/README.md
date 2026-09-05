# enwiki9 operating manual

PROJECT ROOT means `gamma/projects/enwiki9/`. Run every command below there.
Uppercase names such as `CANDIDATE`, `QUERY`, and `SCOPE` are placeholders;
resolve them from the actual records and frozen contract before execution.

**When the user says "go"**

Read [AGENTS.md](../AGENTS.md), inspect current work, and resume the recorded next
useful action. Preserve existing workers and observer ownership. If execution
is blocked, resolve the named dependency or advance independent research.

```bash
python3 tools/enwiki9_lab.py start
```

The read-only report shows ownership, environment gaps, pending work, and useful
read commands. It grants no launch permission or input-hash verification. A run
still needs its contract, lifecycle, ownership, and resource prerequisites.

**Find the records**

Browse [the ledger](../ledger/index.html) or query canonical records directly:

```bash
python3 tools/enwiki9_lab.py records --search 'QUERY' --view algorithms --limit 20
python3 tools/enwiki9_lab.py records --candidate CANDIDATE --limit 20
python3 tools/enwiki9_lab.py records --view runs --state running --limit 20
```

Views are `algorithms`, `runs`, `notes`, `mixes`, `proposals`, and `reviews`.
Search matches all words, ignoring case; use `--offset 20` for the next page.
Candidate detail includes source links, lineage, and bounded history. `reviews`
lists latest bound terminal jobs missing a reflection; add `--include-legacy`
for historical jobs without revisions. Presence alone is not validation.

| Question | Canonical record |
| --- | --- |
| What ideas were considered, and why? | [Research register](../docs/research_register.md) and `docs/*portfolio*.json` |
| What failed, and what remains unsettled? | [Exclusions](../operations/adaptive/exclusions/) and [reflections](../operations/adaptive/reflections/) |
| What hypothesis and comparison are frozen? | [Experiments](../operations/adaptive/experiments/) and [proposals](../operations/adaptive/proposals/) |
| Where is the implementation and its parent? | [Programs](../programs/), [revisions](../operations/adaptive/candidate-revisions/), [mutations](../operations/adaptive/mutations.jsonl) |
| What is mixed, and how do components interact? | [Composition graphs](../operations/adaptive/composition/) |
| What is queued, running, or finished? | `operations/adaptive/{pending,running,completed,failed,cancelled}/` and `run_logs/adaptive/` |
| What was measured? | [Results](../results/) and [run ledger](../results/run_ledger.jsonl) |

Follow evidence links before using a result. Recorded running state needs an
actual process-identity check; rebuilding the ledger does not establish liveness.

**Research, create, and mix**

Search prior findings and exclusions first. Compare the information a mechanism
adds, its expected savings, package cost, and uncertainty. Research papers and
external evidence retain their source attribution and measurement scope.
Use primary papers, authors' implementations, and the official prize rules.
Check current submissions before treating the research target as a winning score.
The `start` report links both authorities; changing the objective requires a new
version and revalidation, rather than rewriting historical targets.

Record every considered idea and decision in `docs/research_register.md`; use a
dated portfolio for a batch. A scientific miss belongs in a validated reflection
and its scoped exclusion. An infrastructure failure does not retire an algorithm.

For actionable work, freeze an experiment, then use `propose`, `claim`, `develop`,
and `seal` through `tools/enwiki9_lab.py`. Give mutations a new identity. A mix
needs a composition graph, explicit shared costs, and a new joint replay. See the
[adaptive workflow](../ADAPTIVE_WORKFLOW.md) for complete arguments.

**Benchmark an exact codec candidate**

Choose the smallest justified gate from the frozen experiment and prior
reflections. Verify the candidate revision, inputs, output paths, guards, and
ownership before queueing. Publish ownership before another worker can claim it.

```bash
python3 tools/enwiki9_lab.py enqueue CANDIDATE --gate-size SCOPE --purpose candidate \
  --mode discovery --cpu-set CPU_SET --memory-limit-bytes MEMORY_BYTES \
  --disk-limit-bytes SCRATCH_BYTES --wall-time-limit-seconds STOP_SECONDS \
  --cgroup-parent DELEGATED_CGROUP_PARENT
python3 tools/enwiki9_lab.py run --candidate CANDIDATE --max-workers 1
```

Supply `--archive-ceiling BYTES` when the contract declares that bound. Use the
runner's required resource envelope; worker count alone is not a memory guard.
The command above consumes one eligible pending job for the named candidate.
Read `enqueue --help` before filling the budget. Unknown ownership blocks admission;
legacy jobs without an explicit mode stay held. Qualification uses `--mode
qualification` with a bound calibration plan/receipt and an exclusive lease.
A candidate that already owns a nested guard declares that exact cgroup so the
job deadline covers every owned process. Its total budget includes coordination
overhead. The queue retains resource evidence and limitations explicitly.

**Run a simulation, proxy, or diagnostic**

Freeze a bounded question, controls, input population, and zero-score evidence
class. Register and seal its candidate before using the same canonical queue:

```bash
python3 tools/enwiki9_lab.py enqueue-tool CANDIDATE \
  --tool tools/TOOL.py --purpose diagnostic --gate-size SCOPE \
  --mode discovery --cpu-set CPU_SET --memory-limit-bytes MEMORY_BYTES \
  --disk-limit-bytes SCRATCH_BYTES --wall-time-limit-seconds STOP_SECONDS \
  --cgroup-parent DELEGATED_CGROUP_PARENT
python3 tools/enwiki9_lab.py run --candidate CANDIDATE --max-workers 1
```

Inspect the selected tool's `--help` and code first. Pass its arguments with
repeated `--tool-arg=VALUE`; declare paths it expects precreated with
`--scratch-directory results/CANDIDATE`. Follow its exact output contract.
Tool purposes are `diagnostic`, `infrastructure`, or `oracle`; simulation is the
experiment's description, not a CLI purpose. These jobs receive zero score credit.

**Review and close the loop**

Inspect terminal artifacts, recheck bindings and accounting, and evaluate the
frozen predicates. Record or validate the job's `reflect` receipt before changing
scientific status. Use `python3 tools/enwiki9_lab.py reflect --help` and the
[reflection instructions](../ADAPTIVE_WORKFLOW.md#record-the-discovery-boundary).

Keep measured units explicit: ideal bits, finite payload bytes, package bytes,
and full-corpus score. Preserve each exact run in `results/` and
`results/run_ledger.jsonl`, then record the conclusion in the research register.

```bash
python3 tools/enwiki9_lab.py refresh
python3 tools/enwiki9_ledger.py
```

**Executable comparison and release checks**

[lib/predictor.py](../lib/predictor.py) defines Q16 pre-truth bit probabilities,
decoded-bit updates, deterministic initialization, state serialization/digests,
and strict frontend/trace identities. Its context-count arithmetic codec is a
test fixture. A WRT or token frontend needs an explicit adapter.

The existing [driver](../lib/driver.py) accepts `--comparison SPEC.json --limit
BYTES --output results/CANDIDATE/NEW_RUN`. A candidate supplies `compress_arm`
and `decompress_arm`; the specification names parent, bookkeeping, treatment and
applicable controls, plus hypothesis, parent, changed mechanism, development
budget, selection population, sealed confirmation and stop rule. The queued
runner calls this driver from one frozen candidate build. It retains arm archives,
restored outputs, repeats and first-divergence diagnostics before an atomic
decision. Optional telemetry is marked missing; missing mandatory proof still
blocks promotion. Its mode flag alone does not certify qualifying timing.

Run the bounded infrastructure fixtures without installing dependencies:

```bash
python3 -m unittest discover -s tests -p test_enwiki9_predictor_driver.py -v
python3 -m unittest discover -s tests -p test_enwiki9_release_canary.py -v
python3 tools/enwiki9_clean_room_replay.py --verify-canary results/release_canary_rle_q0_v1/release/20260905_acceptance_v1/canary-receipt.json
```

For a fresh release canary, use `python3 tests/test_enwiki9_release_canary.py
--bundle results/release_canary_rle_q0_v1/release/NEW_RECEIPT`. This exercises the
existing closure and clean-room tools with three independent builds, exact
reconstruction, repeat archives, missing-file rejection and license reporting.
It grants zero objective credit. The full-corpus replay continues to require
exact billion-byte reconstruction, complete package/options, phase calibration,
resource evidence and a separately built cross-host archive match.

Before submission, confirm the current reference/accounting with the committee,
prepare the public source/package and algorithm explanation, document authorship
and external contributions, and provide exact build/encode/decode instructions.
The [committee inquiry](committee-inquiry.eml) is prepared but unsent; delivery
needs a sender and an email channel. The public-submission audit and
[competitive frontier](../operations/provenance/competitive_frontier_v1.json)
retain source hashes and distinguish external results from Gamma modifications.

The [objective contract](../contracts/research/v2/objective-contract.json) defines
exact reconstruction and the fully counted 99,000,000-byte target. Follow
[AGENTS.md](../AGENTS.md) for operating rules and use [PROMPTS.md](PROMPTS.md) for
copyable tasks. The [ledger guide](../ledger/README.md) explains the generated view.
