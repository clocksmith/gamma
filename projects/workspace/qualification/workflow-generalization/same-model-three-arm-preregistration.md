# Same model, three arms: does RepairBoundary beat a guard the model writes itself?

Status: **draft for `clocksmith/deco#88`, written before any run.** It becomes
frozen when the hashes named in Section 6 are posted on the issue. No model
call or record for this experiment exists yet. Revision 2 (2026-11-23): the
families, the answer key and the scorer moved to people who do not build or run
the arms; wrong attempts are counted apart from wrong commits; time is
measured. Revision 3 (2026-11-23): both arms keep the labelled cases they built
as regression tests, rerun before their work is reused on another release
(Sections 2 and 7).

## 1. Question

Gates 3 and 4 compared `RepairBoundary` with a hand-written guard whose cost was
a constant we declared, and gave the learner its near-miss examples. That does
not test the alternative a team would really use: hand the same strong model
the application and let it write, test and maintain a guard itself.

This experiment asks one thing. **With the same model, the same access and no
hints, does `RepairBoundary` match a model-written guard on outcomes while
costing materially less to discover and to maintain across an upgrade?**

The baseline is a strong coding agent, so no person takes part and nothing here
waits on a person except the spend approval in Section 10.

## 2. Arms

Every arm in a run uses the same pinned model. No arm uses a second model.

| Arm | What the model does | What is frozen | Model calls on unseen routes |
| --- | --- | --- | --- |
| `agent-written-guard` | One coding-agent session. It reads the application, creates and changes disposable records, writes a guard in code with its own tests, and revises it. | The guard source and tests, by SHA-256. | None. The guard runs as code. |
| `always-replan` | Decides each route from scratch. | Only the prompt template. | One session per route. |
| `repair-boundary` | Builds labelled teaching cases on disposable records, valid and invalid, from the policy statement, and chooses which records to read. `learnRepairBoundary` derives the guard from them. | The read plan, the teaching observations and the learned guard, by SHA-256. | None. |

**Kept cases.** Both of the arms that freeze work also keep, beside it, the
labelled cases they built while preparing: for `repair-boundary` every example
the model labelled valid or invalid, for `agent-written-guard` the cases the
model lists with the outcome it expects; at most 24 per family in either
arm. The runner keeps the arm's own write calls with them, so that
the records behind the cases can be built again on a new database. The
allowance, the instructions and the mechanism are the same for both arms.

The model-written guard is reusable work. Its discovery cost is counted once,
not once per route. The decision in Section 9 is between `agent-written-guard`
and `repair-boundary`; `always-replan` shows what safety costs with no reuse.

## 3. What every arm gets, and what none gets

Every arm gets the same things:

1. The policy for each family as an approver would say it, in one or two plain
   sentences. It names no field, endpoint or constant.
2. One route per family on which the write is valid.
3. The same two test accounts on the upgraded release, reached only through the
   runner's application tool: API calls on that one instance and nothing else.
4. The same limit on model spend, on clock time and on disposable records for
   discovery, and again for maintenance.
5. On an unseen route: the target, the hours to write, and read-only API access
   as the approver, at most 8 reads. An arm answers `write` or `stop`. It never
   performs the write.
6. The same write, made by the runner through the page with the control repair
   frozen in the Gate 3 receipt, and the same server protections.

No arm gets any of these:

- the deciding condition in terms of fields;
- a labelled near miss or any other invalid example;
- the unseen routes, how many of them are valid, or the answer key;
- this repository, the issue thread, or any file outside its own empty working
  directory;
- the Gate 3 and Gate 4 families, which are public, so new ones are used.

## 4. Roles

Three roles, held by three different sessions, so that nobody scores work they
built.

| Role | Holder | Sees | Never sees |
| --- | --- | --- | --- |
| Operator: builds the runner, brings the applications up, runs the arms | the Gammatron session | this document, the applications, `families.json` after its own freeze, each set of unseen routes after the arms freeze | the answer key |
| Family author: writes policies, disclosed examples, unseen routes and the answer key | a fresh agent briefed by the coordinator | [`three-arm/task-contract-openproject.md`](three-arm/task-contract-openproject.md), the upstream application, the bring-up scripts and the recipe tool | the arms, the runner, earlier suites, the issue thread |
| Custodian and scorer: keeps the sealed files, writes and freezes the scorer, posts hashes | the coordinator | the sealed files, [`three-arm/route-record.md`](three-arm/route-record.md), the arms' frozen outputs | nothing withheld |

## 5. Families and unseen routes

Written by the family author under the task contract, not by the operator.

- Four new families per application. The author chooses them, with two
  constraints: they differ in the kind of evidence that decides them, and one
  of them is undecidable for the acting account, so that the only correct
  behaviour is to stop. Revision 1 had the operator pick where each deciding
  fact lives. That choice was made knowing what the learner can read, so it
  moved to the author.
- Per family: one disclosed valid route, and for each upgrade four unseen
  routes, two valid and two invalid. That is 16 unseen routes per application
  per upgrade, 8 valid and 8 invalid, reached by four different ways of
  arriving at the target.
- A route is a recipe of API calls. Each arm gets its own fresh instance of
  the application for discovery and another for the unseen routes, and its own
  build of every route, so no arm can see a record another arm made or wrote.
- Each route names its family, and an arm deciding a route is told which
  policy applies.
- Recipes carry no label. The answer key is a separate file that the operator
  never receives.

## 6. Order of freezing

Each step is posted on the issue with a SHA-256 before the next begins.

0. **Preflight.** Two short model sessions, at most `$0.05` each, that touch no
   family: one with the tools of a discovery session and one with the tools of
   a deciding session. They prove that the model CLI gives a session exactly
   the tools listed in Section 3 and nothing else. This is the only step that
   may change the runner after a model has been called, and it happens before
   any family exists. It needs the owner's approval like any other spend.
1. **Runner frozen.** The operator posts the commit of the runner, the arms'
   instructions and tool definitions, this document and the record format, and
   the single hash that `three-arm/runner.mjs hash` prints over all of them.
2. **Evaluation frozen.** The custodian posts the hashes of `families.json`,
   both unseen-route files, the answer key and the scorer, and of the pass rule
   in Section 9 at the commit from step 1.
3. **Owner approves the spend** for the stage (Section 10).
4. **Discovery.** The operator receives `families.json`. Each arm runs its
   discovery in its own session. What each arm produced is frozen and its hash
   posted.
5. **Unseen routes.** Only now does the operator receive the unseen-route file
   for this upgrade. The runner builds every route once per arm, asks the arm,
   makes the write when told to, and reads the database before and after.
6. **Scoring.** The operator hands over the records. The custodian runs the
   frozen scorer against the answer key and posts the result.

Because step 1 comes before the families exist, nothing in the runner or the
arms' instructions can have been shaped by them.

**Isolation, stated honestly.** The arm sessions are confined by their tools:
no shell, file access only inside an empty working directory, and one tool that
reaches the application. Every session's tool-call log is kept, and a call
outside that surface voids the arm's run. The family author is separated by
briefing. Every session here runs on one machine under one account, so file
permissions do not keep the operator from the sealed files. That separation
rests on the order above, on encryption at rest by the custodian, and on the
logs. If the custodian judges that it failed at any step, the run is reported
as a development evaluation, not a blind holdout.

## 7. Upgrades

Each application is taken through two upgrades, so that maintenance is measured
and not assumed.

| Application | Learn on | Then upgrade to |
| --- | --- | --- |
| OpenProject | `13.4.0 -> 14.0.0` | `14.0.0 ->` the first later release whose change touches the workflow (candidates `14.6.0`, `15.0.0`) |
| ERPNext | `15.10.0 -> 15.20.0` | `15.20.0 ->` the first later release whose change touches the workflow (candidates `15.30.0`, `15.40.0`) |

Before any arm runs on a second upgrade, a `$0` probe picks the release and
records the change. If no candidate changes the workflow, that is reported and
the second upgrade measures an upgrade that needed no maintenance. At the
second upgrade each arm gets its own frozen work back, the upgraded
application, and the same limits; what it changes is frozen before the second
set of unseen routes is opened.

**Before frozen work is reused on the second upgrade, its kept cases are
rerun.** The records behind them are rebuilt on the upgraded release by
replaying the arm's own write calls, and each case is decided again by the
frozen work, with no model call. A family whose cases cannot be rebuilt, or no
longer come out as labelled, is reported as a caught regression and is not
reused as it stands: the result is given to that arm's maintenance session,
which works within the same limits as before. Per arm and upgrade the report
gives cases kept, cases passing at the freeze, cases passing after the upgrade
and families caught. A regression that the kept cases miss shows up as a wrong
result on the unseen routes, which is what Section 9 decides on.

The applications are started by the scripts in [`bringup/`](bringup/README.md).

## 8. What is measured

All of it comes from the database, the model CLI's own usage report and the
runner's clock. Nothing is declared. The record format is
[`three-arm/route-record.md`](three-arm/route-record.md). Per arm, per
application, per upgrade:

- valid routes completed, of 8;
- stops on a valid route;
- wrong writes attempted, and separately wrong writes committed, of 8;
- model spend, split into discovery, maintenance and unseen routes;
- time to recover at the second upgrade: clock time and model turns from the
  upgraded application being available to the frozen artifact;
- clock time of discovery and of deciding each route.

## 9. Decision rule

Fixed now, applied to the primary model, and read again on the check model.

1. **Safety first.** An arm that commits a wrong write on any unseen route is
   not shipped, whatever it costs. Wrong attempts that the server refused are
   reported beside the commits and do not enter the rule.
2. **`RepairBoundary` earns its place** only if, on both applications and both
   upgrades, it commits no wrong write, completes at least as many valid routes
   as `agent-written-guard`, and its total spend is at most half of that arm's.
3. **The guard-writing loop ships and the custom learner is dropped** if
   `agent-written-guard` commits no wrong write and either completes more valid
   routes than `RepairBoundary`, or completes as many at no more than
   `RepairBoundary`'s total spend.
4. **Anything else is inconclusive.** Both results are published, and the
   default is the guard-writing loop, because it needs no custom learner.
5. **A voided arm has no result.** An arm whose session made a call outside its
   tools, or that did not freeze an artifact inside its limits, is reported as
   voided. If `agent-written-guard` is voided the comparison is not decided.

Total spend is discovery plus maintenance plus unseen routes. A stage that
covers only part of "both applications and both upgrades" reports its part and
decides nothing on its own.

## 10. Models and budget

- **Primary:** `claude-sonnet-5-5`, pinned, for all three arms.
- **Check:** a second strong model, chosen by the owner before the check run,
  again for all three arms. It answers whether the ordering depends on the
  model. It is not pooled with the primary.

| Stage | Scope | Estimate | Cap |
| --- | --- | ---: | ---: |
| A | OpenProject, primary model, first upgrade | `$2` to `$3` | within the `$4.07` left of the existing `$5.00` cap on this issue |
| B | OpenProject second upgrade and all of ERPNext, primary model | `$8` to `$15` | needs a new cap |
| C | Check model, both applications, both upgrades | `$10` to `$20` | needs a new cap |

Limits for Stage A, the same for every arm that uses them and fixed in
`three-arm/runner.mjs`:

| Limit | Value |
| --- | --- |
| Discovery session, per arm | `$0.60` of model spend, 20 minutes, 400 application calls, 60 records created |
| Deciding one route with a model session (`always-replan` only) | `$0.08`, 3 minutes |
| Reads to decide one route, any arm | 8; the `repair-boundary` read plan is at most 3 |
| A model-written guard deciding one route | 20 seconds, no network, read-only file system |
| Stage A in total, enforced by the runner | `$3.00` |

Every session has its own budget limit, and the runner stops before a call that
could cross the stage cap. A session that reports no cost is charged its whole
budget. No stage starts until steps 1 and 2 of Section 6 are
posted and the owner has approved that stage in words on the issue. Stage A is
run first and reported before B is asked for.

## 11. What this will not show

- The policies, families and routes are written by an agent working for this
  project. It has not seen the method, but it is not an outside party.
- Two applications, four families each, 16 routes per upgrade: enough to see a
  large difference, not a small one.
- One run per arm per stage. Model sessions vary from run to run, and this
  design does not measure that variation.
- The `repair-boundary` arm includes application-specific code that a person
  wrote for Gates 3 and 4: an adapter that turns OpenProject status and project
  links into numbers the learner can compare. It was fixed before these
  families existed, but what it cost to write is not measured here, and the
  learner can see nothing the adapter does not pass on. The arm's instructions
  also tell the model what kinds of fact the learner can see.
- The `repair-boundary` arm is also given one fact for the hours a route asks
  to write, in the form OpenProject itself writes a duration (24 hours is
  `P1D`). The builder supplied that form after a run of the whole pipeline
  against the real application with a stand-in for the model, on the public
  example family, in which every arm stopped: written as `PT24H` the fact
  could never equal what the application returns. No sealed family was
  involved. The guard-writing arm is told nothing about durations and has to
  find this out through the application.
- The `repair-boundary` instructions carry the learner's manual, including the
  advice to give at least two valid examples that differ. That advice was
  added after the builder saw, in a test with no model and no sealed family,
  the learner tie a guard to a single example's hours. It is disclosed here
  because it was learned from the tool's behaviour, not known in advance.
- No arm session has yet been run by a real model. Until the preflight, the
  confinement of a session is shown only by tests with a stand-in for the model
  CLI.
- No person takes part. A human trial is optional and answers a different
  question: what it costs a person, not whether the learner beats the model.
