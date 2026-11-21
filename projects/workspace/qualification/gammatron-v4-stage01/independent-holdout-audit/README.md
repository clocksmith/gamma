# Audit of the independent holdout: where the 42-to-18 difference comes from

**Finding.** The holdout in [`../independent-holdout/`](../independent-holdout/README.md) reports
42 scripted decisions for exact matching and 18 for suffix matching. That difference is produced
by the runner, not by the matcher. With one observation policy for teaching and every case, exact
matching, the profile matcher and the index matcher each take 15 decisions.

This is a post hoc audit, run on 2026-11-21. It is a diagnostic, not new holdout evidence.

## What the runner does

`frozen/run.mjs` builds `observationLocators` per case. The `alternate` and `layout` cases each add
a locator, so their policy differs from the policy used in teaching. `scopeWorkflowObservation`
hashes the policy into the template, and the template is part of every state's identity. In those
two cases exact matching therefore cannot recognise any learned state, including the screens that
did not change. That is intended behaviour: binding the policy into the template is there so a
changed policy does not reuse an old recipe.

The profile matcher compares origin and route pattern only. It does not compare the template, so
it reused the recipe under the changed policy. That reuse is the whole measured difference.

## Runs

Nine safe pairs and twelve negative pairs per arm, three domains. `profile` is the arm the frozen
runner calls `suffix`. Totals are in [`summary.json`](./summary.json).

| Gamma revision | Observation policy | Arm | Decisions, safe cases | Cached steps | Certified rejoins | Negative cases stopped, zero effects |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `5b79bce` (the pin) | per case, as frozen | exact | 42 | 18 | 0 | 12 of 12 |
| | | profile | 18 | 39 | 3 | 12 of 12 |
| `5b79bce` (the pin) | one policy | exact | 15 | 39 | 0 | 12 of 12 |
| | | profile | 15 | 39 | 0 | 12 of 12 |
| `597d5fe` (main) | per case, as frozen | exact | 42 | 18 | 0 | 12 of 12 |
| | | profile | 18 | 39 | 6 | 12 of 12 |
| | | index | 42 | 18 | 0 | 12 of 12 |
| `597d5fe` (main) | one policy | exact | 15 | 39 | 0 | 12 of 12 |
| | | profile | 15 | 39 | 0 | 12 of 12 |
| | | index | 15 | 39 | 0 | 12 of 12 |
| `597d5fe` (main) | one policy, other account scope at evaluation | exact | 63 | 0 | 0 | 12 of 12 |
| | | profile | 18 | 39 | 9, and 6 on negative cases | 12 of 12 |
| | | index | 63 | 0 | 0 | 12 of 12 |

- **The first block reproduces the committed receipt exactly**, row for row, on macOS with Node
  22.20.0.
- **With one policy, exact matching reuses the unchanged screens by itself.** `alternate` takes 2
  decisions per domain in every arm and `layout` takes 3. No arm certifies a rejoin because none
  is needed.
- **Reported rejoins rose from 3 to 6 on main for the same behaviour.** Commit `18c8ea3` keeps the
  count when a session is replaced. The three `layout` rejoins happened at the pin too and were
  dropped from its receipt.
- **No effect was dispatched in any negative case**, in any configuration.

## Second finding: the profile matcher is not bound to scope

A state's identity binds the template, origin, read scope and account scope. The profile matcher
(`evaluateSuffixEligibility`) checks origin and route pattern only. Two results show the effect:

- **Changed observation policy** (per-case blocks): it rejoined in all six `alternate` and `layout`
  runs.
- **Different account scope at evaluation**, with the live tenant correct (last block): exact
  matching and the index matcher reused nothing. The profile matcher certified in all nine safe
  runs, and in six negative runs (`hidden-lock` and `skipped-approval`). Those six then stopped at
  the host's checks with zero effects.

No wrong effect was dispatched. The host checks held. But a graph shared across accounts or
policies is isolated by exact matching and by the index matcher, and is not isolated by the
profile matcher.

## What stands

- **Stands:** the holdout's guard result. All 12 negative cases per arm stop with zero effects.
- **Does not stand:** fewer decisions from suffix matching, on this holdout.
- **Not affected:** the sandbox suite result in [`../README.md`](../README.md) (124 calls to 20).
  Teaching and evaluation there share one observation policy and one account scope.

## Reproduce

Make the scratch copy described in the holdout's README, with `gamma/` at the pin. Add a second
clean checkout of main as `gamma-main/`. The runner needs a `sha256sum` that accepts `-c`.

```sh
A=PATH_TO/independent-holdout-audit/run-audit.mjs
run() { env -i PATH="$PATH" HOME="$PWD" GAMMATRON_FIXTURE_ONLY=1 "$@" node "$A" "$PWD"; }
run DIAG_OUT=audit-pin-per-case
run DIAG_OUT=audit-pin-one-policy DIAG_FIXED_POLICY=1
M="DIAG_GAMMA=gamma-main DIAG_PIN=$(git -C gamma-main rev-parse HEAD) DIAG_ARMS=exact,suffix,index"
run $M DIAG_OUT=audit-main-per-case
run $M DIAG_OUT=audit-main-one-policy DIAG_FIXED_POLICY=1
run $M DIAG_OUT=audit-main-other-account DIAG_FIXED_POLICY=1 DIAG_EVAL_ACCOUNT=some-other-account-scope
```

`run-audit.mjs` is `frozen/run.mjs` with switches added: the Gamma checkout and commit, the arms,
one policy for all cases, and the account scope used at evaluation. With no switch set it behaves
as the frozen runner.

## Limits

- The audit was written after reading the fixtures and the receipt.
- "One policy" is the union of every case's locators for a workflow. Each case still observes the
  same controls as in the frozen run.
- Synthetic snapshots, a scripted planner and three clustered domains, as in the holdout.
