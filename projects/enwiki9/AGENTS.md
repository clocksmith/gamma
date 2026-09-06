# enwiki9 agent rules

Applies throughout `projects/enwiki9/`, including `ledger/` and `workbench/`.
Obey [Gamma's instructions](../../AGENTS.md) and the applicable `CATSCAN.md`
chain; a nearer instruction file may narrow these rules. Boundary changes
require the affected charter to change with the implementation.

Use [ADAPTIVE_WORKFLOW.md](ADAPTIVE_WORKFLOW.md) as the command manual and
`tools/enwiki9_lab.py` as the operational entrance. [README.md](README.md) is the
directory map; [ledger/README.md](ledger/README.md#record-map) maps canonical records.
On “go”, inspect ownership and relevant evidence, carry the next justified action
to a recorded result, and continue independent work when one gate is held.
At each decision boundary, use the manual's [test/mutate/explore rules](ADAPTIVE_WORKFLOW.md#choose-testing-mutation-or-exploration)
and the [creative prompts](workbench/PROMPTS.md#creative-discovery) when changing direction.

## Authority and permissions

- Standing permission covers source inspection, research, synthetic fixtures,
  targeted regression tests, the release canary, and independently bounded
  discovery gates on assigned resources. Large launches and dependency/model
  installation require explicit user authorization; never auto-install them.
- Inspect actual host occupancy before source changes or resource-intensive work.
  Run `python3 tools/enwiki9_lab.py start` for sampled CPU use, available RAM,
  affinity/cgroup limits, job starts, budgets, and available progress estimates.
  Use the manual's [resource planning instructions](ADAPTIVE_WORKFLOW.md#resources-parallel-work-and-event-timing)
  to size the next move; prefer admitted independent parallel work when capacity
  permits. Refresh the sample before launching; available capacity is not a claim.
  Preserve claims, leases, workers, and existing sole observers, including
  HORIZON's observer. Missing controllers and unknown occupancy grant no launch
  permission. Committed status is a timestamped host snapshot.
- Publish ownership before launching a resource-intensive gate. Give every job
  a unique identity, output path, and explicit CPU, memory, scratch, and elapsed
  stop. Independent discovery may share a host; concurrent timing is diagnostic.
  Qualification requires isolated timing, calibration, and complete resource
  evidence. Its future certificate does not block implementing the candidate.
- Assume other agents may pursue the same objective. Search current proposals,
  claims, running jobs, and relevant lineage for the same mechanism and population
  before implementing or launching. An owned experiment calls for a distinct
  path or explicitly coordinated contribution; a new name does not make duplicate
  work independent. Recheck published ownership before execution.
- Do not distribute `docs/atlas_clockwork_seal_problem_set.md` to candidates
  unless `tools/atlas_clockwork_seal.py verify --require-bound` reports
  `VALID_BOUND`. Expert review of an `UNBOUND` draft is allowed.
- Follow [the Unicode policy](../../EMOJI.md); do not add emojis.

## Scientific invariants

- The [active v2 objective](contracts/research/v2/objective-contract.json) is
  exact, deterministic reconstruction of 1,000,000,000 bytes with a fully counted
  score at or below **99,000,000 bytes**. Preserve historical objective digests
  and experiment bindings, including the v1 105M milestone. Consult
  [competitive provenance](operations/provenance/competitive_frontier_v1.json)
  before treating engineering economics as an accepted prize threshold.
- Every semantic mutation gets a new candidate. Never edit running, sealed, or
  measured source in place. Use the canonical lifecycle, not ad hoc launchers.
- Freeze hypothesis, parent, changed mechanism, development budget, selection
  population, sealed confirmation, controls, and stop rule. Budgeted development
  tuning is allowed; freeze before confirmation. A failed configuration does
  not disprove its entire information source. Economic stops are budget decisions;
  certified futility needs a proved bound.
- Compare identical populations and coordinates. History-dependent mechanisms
  need causal warmup. Reuse builds or traces only when frontend, source, state,
  and coordinate identities match; differing frontends need explicit adapters.
- HORIZON's frozen scientific threshold remains unchanged. Recovered
  probabilities cannot restore missing continuous runtime or memory evidence.
- Missing alignment, causality, inversion, determinism, provenance, resource, or
  accounting evidence blocks promotion. Quarantine broken evidence; never
  fabricate or silently discard missing artifacts. Optional diagnostics remain
  explicitly missing rather than becoming invented codec failures.
- Validate the terminal reflection before scientific transitions or selecting
  descendants. Review selected ancestry first; unrelated historical backlog
  does not block independent work. Preserve failures and scoped exclusions.
- Before a larger gate, account for archive, required program/source/model/table
  and option bytes, measured resources, target debt, and numeric kill conditions.
  Forecasts, prefixes, partial archives, teachers, oracles, and shadows receive
  no full-corpus score credit. A composition needs a fresh joint replay; never
  add component forecasts or savings as an earned combined gain.

## Durable records and handoff

Record every meaningfully evaluated algorithm and decisive conclusion, including
rejections before implementation, merges, parked ideas, and oracle-only work.
Keep considered ideas in the research register, batches in dated portfolios,
actionable experiments in the existing adaptive lifecycle, and exact artifacts
and run rows in results. Portfolios create no queue or score authority.

Follow immutable evidence links before using a claim. Keep commands, hashes,
outcomes, and next actions in canonical records; do not create another registry,
queue, or device-local notebook. Regenerate disposable views after changes.
Complete cross-device handoff by publishing source, ownership, receipts, run
rows, conclusions, and generated status through the
[manual's handoff procedure](ADAPTIVE_WORKFLOW.md#cross-device-operation).

When explicitly asked for Hutter status, include the `99,000,000` byte and
`9.9000000%` targets, the verified full-1G score or `unknown`, the best counted
forecast and signed target distance, and the active gate's receipt-backed scope,
progress, guard state, and terminal status. Historical detailed instructions are
preserved at `docs/reference/legacy_instructions/AGENTS_20260724.md`.
