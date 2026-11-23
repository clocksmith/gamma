# Same-model three-arm test: shared pieces

For `clocksmith/deco#88`. The plan is
[`../same-model-three-arm-preregistration.md`](../same-model-three-arm-preregistration.md).
Nothing here calls a model.

| File | For whom | What it is |
| --- | --- | --- |
| `task-contract-openproject.md` | the family author | The whole brief for writing policies, routes and the answer key |
| `provision.mjs`, `example-recipes.json` | the family author and the runner | The route-recipe format and the tool that checks and builds recipes |
| `route-record.md`, `route-record.schema.json` | the scorer | The records the runner emits, and what the scorer computes from them |
| `write-step.mjs` | the runner | The one write every arm shares, made through the page, and the database read before and after |

Not built yet: the runner itself, the application tool each arm session is
confined to, and the arms' instructions. Until those are committed and their
hash is posted on the issue, step 1 of the freezing order has not happened.

Checked so far, all against a local OpenProject `14.0.0` started by
`../bringup/openproject-up.sh`:

- `provision.mjs run example-recipes.json --try-write` builds both example
  routes and the server accepts the write on each.
- `write-step.mjs` saved Work through the page in Chrome and the row version
  moved in PostgreSQL. Saving the value already stored returned `200` and
  changed no row, which is why a recipe's target must differ from the hours it
  names; `provision.mjs` refuses a recipe that breaks this.
- Unit tests: `node --test test/unit/three-arm-provision.test.mjs` from
  `projects/workspace`.
