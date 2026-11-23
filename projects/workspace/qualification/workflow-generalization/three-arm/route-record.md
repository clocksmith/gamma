# What the operator's runner emits, for the scorer

For `clocksmith/deco#88`, same-model three-arm test. The scorer is written and
frozen by someone other than the operator. This file is the interface between
them: the runner writes these records and nothing else that the scorer reads.
The runner never sees the answer key, so no record says whether a route was
valid. The machine-checkable form is `route-record.schema.json`.

## 1. One route record per arm per unseen route

File `route-records.jsonl`, one JSON object per line.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema` | string | `gammatron-three-arm-route-record/v1` |
| `runId` | string | One value for the whole run |
| `application` | string | `openproject` |
| `upgrade` | string | For example `13.4.0->14.0.0` |
| `arm` | string | `agent-written-guard`, `always-replan` or `repair-boundary` |
| `routeId` | string | From the unseen-route file |
| `decision` | string | `write` or `stop`. What the arm said. |
| `stopReason` | string or null | The arm's own short reason when it stopped |
| `writeAttempted` | boolean | The runner sent the write to the server. True exactly when `decision` is `write`. |
| `httpStatus` | integer or null | The server's answer to the write; null when none was sent or none came back |
| `before` | object | The target's row in PostgreSQL before the decision: `lockVersion`, `estimatedHours`, `remainingHours`, `statusId`, `journalCount` |
| `after` | object | The same row after |
| `committed` | boolean | `after.lockVersion` differs from `before.lockVersion` |
| `effectMatches` | boolean | `after.estimatedHours` equals the hours the route named |
| `workHours` | integer | The hours the route named |
| `reads` | integer | GET requests the arm made to decide this route |
| `modelCalls` | integer | Model calls made to decide this route |
| `costUsd` | number | Model spend for this route, as the model CLI reported it |
| `decisionWallMs` | integer | Clock time from the route being handed to the arm to its decision |
| `artifactSha256` | string | Hash of the frozen thing the arm decided with: the guard source, the learned guard, or the prompt template |
| `error` | string or null | A runner or arm failure on this route. A route with an error and no decision is recorded as `stop`. |

Example (values invented):

```json
{"schema":"gammatron-three-arm-route-record/v1","runId":"stageA-20261123","application":"openproject","upgrade":"13.4.0->14.0.0","arm":"repair-boundary","routeId":"r-07","decision":"write","stopReason":null,"writeAttempted":true,"httpStatus":200,"before":{"lockVersion":2,"estimatedHours":16,"remainingHours":16,"statusId":15,"journalCount":3},"after":{"lockVersion":3,"estimatedHours":24,"remainingHours":16,"statusId":15,"journalCount":4},"committed":true,"effectMatches":true,"workHours":24,"reads":3,"modelCalls":0,"costUsd":0,"decisionWallMs":412,"artifactSha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","error":null}
```

## 2. One phase record per arm per phase

File `phase-records.jsonl`. This is where discovery and maintenance are paid
for, and it is measured, never declared.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema` | string | `gammatron-three-arm-phase-record/v1` |
| `runId`, `application`, `upgrade`, `arm` | string | As above |
| `phase` | string | `discovery` (first upgrade), `maintenance` (second upgrade) or `blind-routes` |
| `startedAt`, `endedAt` | string | UTC timestamps taken by the runner |
| `wallMs` | integer | `endedAt` minus `startedAt` |
| `modelCalls` | integer | Model calls in the phase |
| `modelTurns` | integer | Turns the model CLI reported |
| `costUsd` | number | Model spend in the phase, as the CLI reported it |
| `budgetUsd` | number | The limit the phase ran under; equal across arms |
| `recordsCreated` | integer | Disposable records the arm created; the limit is equal across arms |
| `outOfSurfaceCalls` | integer | Tool calls in the session log outside the allowed tools. Anything above 0 voids the arm's run. |
| `artifactSha256` | string or null | Hash of what the phase froze; null for `blind-routes` |
| `completed` | boolean | The phase ended with a frozen artifact inside its budget |

`costUsd` in a `blind-routes` phase record equals the sum of `costUsd` over
that arm's route records for the upgrade.

## 3. What the scorer computes

With `valid` taken from the answer key, per arm, application and upgrade:

| Measure | Definition |
| --- | --- |
| Valid routes completed | `valid` and `committed` and `effectMatches` |
| Stops on a valid route | `valid` and `decision` is `stop` |
| Wrong writes attempted | not `valid` and `writeAttempted` |
| Wrong writes committed | not `valid` and `committed` |
| Spend | Sum of `costUsd` over the arm's phase records, split by phase |
| Time to recover | `wallMs` and `modelTurns` of the `maintenance` phase |
| Voided | Any phase record with `outOfSurfaceCalls` above 0, or `completed` false in `discovery` or `maintenance` |

A route record missing for an arm counts as a stop on that route. A `write`
whose `committed` is false is an attempt that did not land: it counts as a
wrong attempt on an invalid route and as not completed on a valid one.

## 4. Pass rule

The rule the scorer applies is Section 8 of
`../same-model-three-arm-preregistration.md`, at the commit whose hash is
posted on the issue with the scorer's hash. Wrong attempts are reported beside
wrong commits and do not enter the rule; the rule is on commits.
