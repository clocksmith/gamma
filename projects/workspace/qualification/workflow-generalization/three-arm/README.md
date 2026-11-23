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
  family (2026-11-23, no model call). First run: every arm stopped on every
  route, valid ones included, because OpenProject returns 24 hours as `P1D`
  and 40 as `P1DT16H`. The stand-in guard compared text, which was the
  stand-in's fault; the `repair-boundary` arm's fact for the requested hours
  was written `PT40H`, which was the runner's fault and would have made that
  arm stop on any route of a day or more. Fixed in `repair-boundary-arm.mjs`;
  the stand-in application in the tests now answers as the real one does.
  The rerun is pending.
