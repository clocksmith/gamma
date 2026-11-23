# Same-model three-arm test: shared pieces

For `clocksmith/deco#88`. The plan is
[`../same-model-three-arm-preregistration.md`](../same-model-three-arm-preregistration.md).
Nothing here calls a model.

| File | For whom | What it is |
| --- | --- | --- |
| `task-contract-openproject.md` | the family author | The whole brief for writing policies, routes and the answer key |
| `provision.mjs`, `example-recipes.json` | the family author and the runner | The route-recipe format and the tool that checks and builds recipes |
| `route-record.md`, `route-record.schema.json` | the scorer | The records the runner emits, and what the scorer computes from them |
| `runner.mjs` | the operator | `hash`, `preflight`, `discovery`, `blind`, `regress` and `maintenance`; the spend ledger and the stage cap |
| `instructions.mjs` | the operator | What each arm's model session is told |
| `session.mjs` | the runner | Starts one model session with no shell, no web tool and one MCP server, and keeps its event log |
| `arm-server.mjs`, `app-surface.mjs` | the runner | The one MCP server a session talks to: API calls on the instance under test, plus the arm's own tools; the audit of a session's tool calls |
| `guard-sandbox.mjs`, `guard-host.mjs` | the runner | Runs a model-written guard in a container with no network |
| `repair-boundary-arm.mjs` | the runner | Read plans, labelled examples, the unchanged learner, and deciding a route from the frozen guard |
| `regression.mjs` | the runner | Rebuilds the records behind an arm's kept cases on a new database and reruns the cases with its frozen work |
| `durations.mjs` | the runner | The hours of a route in the two forms every arm is given |
| `dry-run.mjs` | the operator | The whole pipeline on the real application with a stand-in model: a valid route and two look-alikes per arm, and an always-write control |
| `write-step.mjs` | the runner | The one write every arm shares, made through the page, and the database read before and after |

## State

Built and tested without a model. **No model session has run.** The owner has
authorised no paid run, including the preflight (step 0 of the freezing order).

The second upgrade is built for OpenProject as far as it can be without
choosing the release: `maintenance` starts a session from the frozen work,
tells it how its kept cases came out on the newer release, and freezes again
into a new run directory. Still open for Stage B: the `$0` probe that picks
the release, and a frozen repair of the write step if that release changes the
page. ERPNext arms are not built.

```text
node three-arm/runner.mjs hash                 # the hash for step 1, no cost
node --test test/unit/three-arm-*.test.mjs     # from projects/workspace
```

Checked so far, all against a local OpenProject `14.0.0` started by
`../bringup/openproject-up.sh`:

- `provision.mjs run example-recipes.json --try-write` builds both example
  routes and the server accepts the write on each.
- `write-step.mjs` saved Work through the page in Chrome and the row version
  moved in PostgreSQL. Saving the value already stored returned `200` and
  changed no row, which is why a recipe's target must differ from the hours it
  names; `provision.mjs` refuses a recipe that breaks this.
- `app-surface.mjs`: paths that leave API v3 or the instance are refused and
  never sent; discovery stops at its request and record limits; decision mode
  can only read, only as the approver, at most 8 times; every call, refused or
  not, is logged without credentials. The model CLI on this machine connects
  to the server (`claude mcp list` reported it connected). The audit flags any
  tool off the allowed list and any file tool aimed outside the working
  directory. None of this has been exercised by a model session yet: that
  first happens in a paid run, where the audit is the check.
- `guard-sandbox.mjs`, with real containers: a guard that tries the network,
  writes a file, never answers, returns the wrong shape or forges an answer
  line ends as a stop.
- `repair-boundary-arm.mjs`: a learned guard transfers to work packages it was
  not taught on. With a single valid example the learner ties the guard to
  that example's hours; a second valid example with different hours fixes it.
  The arm's instructions say so.
- `runner.mjs`, end to end with a stand-in for the model CLI and a stand-in
  application: all three arms go through discovery, freezing, three unseen
  routes and records. The records carry no label and match the published
  schema. A tool call outside the surface is counted. A guard changed after
  its freeze is refused. A paid phase refuses to start without
  `--approve-paid`. This test found one real fault before any spend: the
  working directory has to be given as its real path, or the audit flags the
  session's own files.
- Kept cases: both arms end discovery with a file of labelled cases and the
  write calls behind them. `regress` rebuilt them on a new database whose
  record numbers differed, and every case came out as labelled. With statuses
  renumbered, as a later release might do, both arms' families were caught;
  with a call refused, the rebuild stopped and said which call.
- Maintenance: with the stand-in application renumbering its statuses, as a
  later release might, both arms' kept cases caught the break, each arm's
  maintenance session repaired its work, and the routes on the newer release
  were then decided correctly. The work frozen at the first upgrade was left
  unchanged.
- Whole pipeline against the real OpenProject `14.0.0`, real Chrome and the
  real guard sandbox, with the stand-in for the model and the public example
  family (2026-11-23, no model call, `dry-run.mjs`). Receipt:
  `../receipts/three-arm-dry-run-receipt.json`.
  - First attempt: every arm stopped on every route, valid ones included.
    OpenProject returns 24 hours as `P1D` and 40 as `P1DT16H`. The stand-in
    guard and the stand-in planner compared text, which was the stand-in's
    fault; the `repair-boundary` arm's fact for the requested hours was
    written `PT40H`, which was the runner's fault. Every arm is now given the
    hours in both forms (`durations.mjs`).
  - Second attempt: stopped before deciding anything, on a connection reset
    by a release that had only just come up. It did not reproduce. The
    bring-up now waits for five answers in a row and the runner retries its
    own failed connections.
  - Third attempt, passed: each arm wrote the valid route (HTTP 200, hours 8
    to 56, row version and journal each up by one in PostgreSQL) and stopped
    both look-alikes itself with no write sent. The control guard that always
    writes got all three committed, the two look-alikes included: neither the
    server nor the harness blocks a wrong write, so an arm's zero is its own.
  - A probe on `14.6.0` then showed a write recorded as sent and not
    committed: the write step could take the page's form check for the save
    and read the row too early. Commit detection now rests on the row alone,
    with a settle wait and a final reading of every row. The dry run was
    repeated on that tree and passed; the first runner hash was withdrawn.
- Second upgrade, same stand-in and public family, receipt
  `../receipts/three-arm-second-upgrade-probe-receipt.json`: on OpenProject
  `14.6.0` and, separately, on `15.0.0`, every kept case was rebuilt and came
  out as labelled (2 of 2 for the guard arm, 4 of 4 for the learner),
  maintenance completed for all three arms, the valid route was written with
  the row changed, and both look-alikes were stopped by the arm. Neither
  release changed anything this family or the frozen write step touches, so
  on this evidence a second upgrade to either would measure an upgrade that
  needs no maintenance. That says nothing yet about the sealed families.
- Known and not fixed: `bringup/erpnext-up.sh` still passes its generated
  passwords on the command line. The OpenProject script was fixed; the
  ERPNext one is not used before Stage B and will be fixed with that freeze.
