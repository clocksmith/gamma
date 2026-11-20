# Two-vendor field-group reuse experiment

This is an owner-requested experiment, not a claim of real ATS qualification.
`forms.json` freezes contact controls from read-only public Greenhouse and Lever
responses. Each vendor has a learning posting and a distinct evaluation posting.
Source URLs, response digests and capture time are retained. Raw responses stay
in ignored local evidence. These are **contact-control projections**, not full
DOM snapshots: required uploads, location widgets, other questions, styling and
vendor JavaScript are excluded. Stage transitions and adversarial changes are
synthetic. Findings cannot be generalized to complete applications.

The local fixture has no remote assets or captured scripts, and CSP forbids
connections and form submissions. Task actions use the real workspace service,
fresh observations, current grants and the existing value-settling checks.
Fault injection and oracle reads are the only direct harness browser operations.

## Freeze before learning

`oracle.json` assigns meanings to immutable field IDs, independently of the
label-based replay rules in `contracts.js`. Neither planner nor cache consumes
the oracle or its field-ID map. The oracle checks every observed input/change
write and rendered review values. An email retained in the decoy field fails.
Decoy and hidden duplicate controls must remain empty.

`test-freeze-v2.json` binds the forms, oracle, policy, group meanings and fixture
before evaluation. Each run also hashes its harness, service and client inputs
into `frozen.json` before learning and checks them again before reporting.
Choose a new output directory for every trial; preserve failures.

```sh
node projects/workspace/qualification/workflow-generalization/run.js --controlled --out bench/out/generalization-baseline
node projects/workspace/qualification/workflow-generalization/run.js --out bench/out/generalization-sonnet-baseline
```

The default arms are the unchanged whole-page cache, fresh planning and a
label-based script that tolerates reordering and explicitly reviewed aliases.
`--controlled` uses the script as a deterministic planner substitute; it measures
browser plumbing, not model quality or comparative product performance. Without
it, the fresh and cache-learning/fallback arms call real Sonnet through the
existing restricted CLI planner, under explicit request and spend bounds.
Scripted decisions are reported separately from model calls.

The default `script` arm also passes through Fawn; it isolates planning cost but
cannot establish an advantage over stock automation. Run the separate stock
control as well:

```sh
node projects/workspace/qualification/workflow-generalization/stock-script.js --out bench/out/generalization-stock-script
```

That control uses stock Playwright, persistent task profiles and the existing
baseline's durable progress file, without Fawn dispatch or planning. Exact labels,
aliases and dependent-question meanings follow the already frozen script rules;
the independent field-ID oracle remains unavailable to its decision logic.
It checks retained values and origin/account/disclosure policy and never submits.
Its report binds the same frozen fixture, profile, settling interval and actual
browser version. A separate-run timing is not an interleaved performance trial.

Evaluation freezes learned graphs: it never learns from holdouts or repairs.
All arms get matched profiles, independent workspaces, fresh grants and isolated
browser profiles. Arm order alternates by variant. The variants cover unrelated
questions, reordering, reviewed label changes, account differences, ambiguous
labels, hidden duplicates, dependent questions, stale observations, revoked
permissions, unknown outcomes, denied disclosure and a semantic decoy. Accounts
are caller-supplied test identities, not inferred signed-in identities.

## Interpretation

Each row records cached field fills and all cached steps, requested-field count,
model calls, decisions, preparation/task/complete time, completion, interventions,
unknown actions and semantic wrong-field fills. Zero submissions and zero
observed wrong-field fills are mandatory. Permission and ambiguity stops count
as safe stops, never completed forms. Uncertain effects permit no next decision
or execution. Stale never-dispatched actions may be freshly planned.

Report setup and maintenance independently from runtime. Human authoring and
repair time are not inferred from source timestamps or replaced with execution
time. Until separately timed setup/repair and a real participant's repeated use
exist, the report leaves those measurements absent and product advantage false.
This experiment does not establish population reliability or universal safety.

## Participant repeat instrument

```sh
node projects/workspace/qualification/workflow-generalization/participant.js --out bench/out/generalization-participant
```

Open its private loopback link. A dedicated headless profile hosts four local
Greenhouse-contact projection tasks: manual teaching, reordered reuse, an added
question requiring help, and that added-question task again. The controls issue
effects only through workspace dispatch. No model or final submission runs.
Each review needs both the independent oracle and the participant's confirmation.
Stop cancels future work and returns service ownership to the human; it cannot
undo an effect already dispatched. Restart explicitly abandons the old attempt
and creates a new isolated workspace, retaining the abandoned record.

`participant.json` records time from first page view to the first task, task
preparation and confirmation time, human actions, repair requests and repair
elapsed time. Those are interaction timings, not active-attention estimates or
script-authoring cost. No identity or personal applicant data is requested.
Keep the process running: the instrument's learned graph is in memory, while its
service journal and measurement records are private on disk. It does not test
product-client restart or real-site retention.

Repaired suffixes are not published by the current implementation. The last
task deliberately exposes whether the same help is needed again. An automated
check of this instrument must never be labeled as a participant result.
