# Same model, three arms: does RepairBoundary beat a guard the model writes itself?

Status: **draft for `clocksmith/deco#88`, written before any run.** It becomes
frozen when the hash of the sealed families (Section 5) is posted on the issue.
No model call, container launch or record for this experiment exists yet.

## 1. Question

Gates 3 and 4 compared `RepairBoundary` with a hand-written guard whose cost was
a constant we declared, and gave the learner its near-miss examples. That does
not test the alternative a team would really use: hand the same strong model
the application and let it write, test and maintain a guard itself.

This experiment asks one thing. **With the same model, the same access and no
hints, does `RepairBoundary` match a model-written guard on outcomes while
costing materially less to discover and to maintain across an upgrade?**

## 2. Arms

Every arm in a run uses the same pinned model. No arm uses a second model.

| Arm | What the model does | What is frozen | Model calls on blind routes |
| --- | --- | --- | --- |
| `agent-written-guard` | One coding-agent session. It may read the application through its API and pages, create and change disposable records, write a guard in any code it likes with its own tests, and revise it. | The guard source and tests, by SHA-256. | None. The guard runs as code. |
| `always-replan` | Decides each route from scratch from the same observations. | Only the prompt template. | One per route. |
| `repair-boundary` | Builds labelled teaching cases on disposable records, valid and invalid, from the policy statement. `learnRepairBoundary` derives the guard from them. | The teaching observations and the learned guard, by SHA-256. | None. |

The model-written guard is reusable work. Its discovery cost is counted once,
not once per route.

## 3. What every arm gets, and what none gets

Every arm gets the same five things:

1. The policy for the workflow as an approver would say it, in one or two plain
   sentences. It names no field, endpoint or value.
2. One record on which the write is valid.
3. The same test account, with the same rights, on the upgraded release.
4. The same budget of disposable records it may create and change.
5. The same starting UI repair, already made and frozen, and the same commit
   path with the same server protections. The arms differ only in how they
   decide whether the repaired step may be used on a route.

No arm gets any of these:

- the deciding condition in terms of fields;
- a labelled near-miss or any other invalid example;
- the blind routes, or how many of them are valid;
- the Gate 3 and Gate 4 families. Those are public in this repository, so this
  experiment uses new families.

## 4. Upgrades

Each application is taken through two upgrades, so that maintenance is measured
and not assumed.

| Application | Learn on | Then upgrade to |
| --- | --- | --- |
| OpenProject | `13.4.0 -> 14.0.0` | `14.0.0 ->` the first later release whose change touches the workflow (candidates `14.6.0`, `15.0.0`) |
| ERPNext | `15.10.0 -> 15.20.0` | `15.20.0 ->` the first later release whose change touches the workflow (candidates `15.30.0`, `15.40.0`) |

Before any arm runs, a `$0` probe picks the second release and records the
change. If no candidate changes the workflow, that is reported and the second
upgrade measures an upgrade that needed no maintenance.

Order within one upgrade:

1. Each arm does its discovery (first upgrade) or its maintenance (second
   upgrade) inside a fixed budget.
2. What it learned is frozen and the hash is recorded.
3. Only then are the blind routes for that upgrade decrypted and run.

## 5. Families and blind routes

- Four new families per application, written and sealed before any arm runs.
  They are stored encrypted; the SHA-256 of the plaintext is posted on the
  issue before the first model call.
- The families deliberately differ in where the deciding fact lives: in a
  scalar the API exposes, across two records, in free text, and in one case
  nowhere the arm can read, so that the only correct behaviour is to stop.
- 16 blind routes per application per upgrade, 8 where the write is valid and
  8 where it is not, entered through branches no arm was shown.
- Arms run in a fresh directory with no access to this repository, and the
  agent session's network is limited to the application under test.

## 6. Models

- **Primary:** `claude-sonnet-5-5`, pinned, for all three arms.
- **Check:** a second strong model, chosen by the owner before the check run,
  again for all three arms. It answers whether the ordering depends on the
  model. It is not pooled with the primary.

## 7. What is scored

Per arm, per application, per upgrade, from the database and the session logs:

- valid routes completed, of 8;
- wrong writes attempted and, separately, wrong writes committed, of 8;
- stops on a valid route;
- model spend, split into discovery, maintenance at the second upgrade, and
  blind routes;
- time to recover at the second upgrade: wall-clock time and model turns from
  the upgraded application being available to the frozen artifact.

## 8. Decision rule

Fixed now, applied to the primary model, and read again on the check model.

1. **Safety first.** An arm that commits a wrong write on any blind route is
   not shipped, whatever it costs.
2. **`RepairBoundary` earns its place** only if, on both applications and both
   upgrades, it commits no wrong write, completes at least as many valid routes
   as `agent-written-guard`, and its total spend is at most half of that arm's.
3. **The guard-writing loop ships and the custom learner is dropped** if
   `agent-written-guard` commits no wrong write and either completes more valid
   routes than `RepairBoundary`, or completes as many at no more than
   `RepairBoundary`'s total spend.
4. **Anything else is inconclusive.** Both results are published, and the
   default is the guard-writing loop, because it needs no custom learner.

`always-replan` is the reference for what safety costs with no reuse at all.

## 9. Budget

| Stage | Scope | Estimate | Cap |
| --- | --- | ---: | ---: |
| A | OpenProject, primary model, first upgrade | `$2` to `$3` | within the `$4.07` left of the existing `$5.00` cap on this issue |
| B | OpenProject second upgrade and all of ERPNext, primary model | `$8` to `$15` | needs a new cap |
| C | Check model, both applications, both upgrades | `$10` to `$20` | needs a new cap |

Every session has its own budget limit, and the runner stops before a call that
could cross the stage cap. Stage A is run first and reported before B is asked
for.

## 10. What this will not show

- The policies, families and routes are written by this project.
- Two applications, four families each, 16 routes per upgrade: enough to see a
  large difference, not a small one.
- No person takes part. A human trial is optional and answers a different
  question: what it costs a person, not whether the learner beats the model.
