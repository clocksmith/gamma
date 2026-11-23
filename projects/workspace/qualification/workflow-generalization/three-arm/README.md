# Same-model three-arm test: shared pieces

For `clocksmith/deco#88`. The plan is
[`../same-model-three-arm-preregistration.md`](../same-model-three-arm-preregistration.md).
Nothing here calls a model.

| File | For whom | What it is |
| --- | --- | --- |
| `task-contract-openproject.md` | the family author | The whole brief for writing policies, routes and the answer key |
| `provision.mjs`, `example-recipes.json` | the family author and the runner | The route-recipe format and the tool that checks and builds recipes |
| `route-record.md`, `route-record.schema.json` | the scorer | The records the runner emits, and what the scorer computes from them |
| `app-surface.mjs` | the runner | The one tool an arm session reaches the application through, its call log, and the audit of a session's tool calls |
| `write-step.mjs` | the runner | The one write every arm shares, made through the page, and the database read before and after |

Not built yet: the runner itself (discovery, freezing, building routes per arm,
asking each arm), the sandbox a model-written guard runs in, and the arms'
instructions. Until those are committed and their hash is posted on the issue,
step 1 of the freezing order has not happened.

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
- Unit tests, from `projects/workspace`:
  `node --test test/unit/three-arm-provision.test.mjs test/unit/three-arm-app-surface.test.mjs`
