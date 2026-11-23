# Stage A notes: written before any number exists

For `clocksmith/deco#88`, same-model three-arm test, Stage A: OpenProject
`13.4.0 -> 14.0.0`, three arms on `claude-sonnet-5-5`, 16 unseen routes.

**Status when this was written (2026-11-23, about 05:45 UTC):** no arm has run
with a real model. No family, route or label has reached the operator. The
sealed cases and the scorer are frozen on the coordinator's side. Stage A has
not been approved.

**The runner hash.** These notes first named the runner hash `8e7361e2`. That
freeze is void: later the same day a no-model test showed the runner's page
write storing a wrong value on `14.0.0`, the write step was hardened, and the
runner was frozen again. The hash for Stage A is
`306e617102d8cb4b73e2bdc937fce06ecfac6baaa1ac5594e368ae59bfe47214`, at
`clocksmith/gamma@bc6bb0091`. Still no arm has run with a real model and
nothing sealed has reached the operator.

The purpose of this file is that nothing below the heading "Results" is
interpreted after the fact. Sections 1 to 4 say in advance what the numbers can
and cannot mean. When the stage has run, the tables in Section 5 are filled
from the scorer's output and the runner's records, and the only sentences added
are the ones Section 3 already allows. Anything else goes under "Deviations".

Label: **development evaluation**. The operator and the evaluator run under one
account, so the separation between them is by undertaking, not by a barrier.

## 1. What Stage A is

- One application, one upgrade, one run per arm. It is 1 of the 4 stages that
  Section 9 of the pre-registration needs. **Stage A decides nothing about
  which method ships.** The scorer says so itself on a partial stage.
- One thing can be settled by a single stage: rule 1 of Section 9. An arm that
  commits a wrong write on any unseen route is not shipped.
- 16 unseen routes: 8 on which the write is valid and 8 on which it is not, in
  four families of two valid and two invalid each. Every arm decides the same
  16 routes, each on its own build of them.
- One family is undecidable for the acting account by design. No arm can
  complete its two valid routes except by guessing, and its two invalid routes
  can only be handled correctly by stopping. So **the most valid routes an arm
  can complete without guessing is 6 of 8**, and an arm that completes 7 or 8
  has written on at least one route it could not have checked.

## 2. What the operator knew when the runner was frozen

- That each upgrade's set holds 8 valid and 8 invalid routes. The
  pre-registration says so publicly, and the coordinator confirmed "8 and 8
  per set" to the operator at 02:24 UTC on 2026-11-23, before the re-freeze at
  03:35 UTC. No arm is told any count, and the runner does not use it.
- That one family is undecidable, because the task contract asks for one.
- That hours of a day or more may occur in the sealed routes. The coordinator
  declined to say whether they do.
- Nothing else about the sealed cases: not the policies, not the families, not
  which route is which.

## 3. What 16 routes can and cannot show

All intervals are exact (Clopper-Pearson, 95 %, two-sided unless stated).

### One arm on its own

| Observed, of 8 | The true rate is compatible with |
| ---: | --- |
| 0 | 0 % to 36.9 % |
| 1 | 0.3 % to 52.7 % |
| 2 | 3.2 % to 65.1 % |
| 3 | 8.5 % to 75.5 % |
| 4 | 15.7 % to 84.3 % |
| 5 | 24.5 % to 91.5 % |
| 6 | 34.9 % to 96.8 % |
| 7 | 47.3 % to 99.7 % |
| 8 | 63.1 % to 100 % |

- **Zero wrong commits in 8 invalid routes** is compatible with a true
  wrong-commit rate of up to 36.9 % (31.2 % one-sided). It is not evidence that
  an arm is safe. The allowed sentence is: "no wrong commit was observed in 8
  invalid routes; a rate up to about one in three is not excluded."
- **One or more wrong commits** settles rule 1 for that arm. That is the only
  strong statement one stage can make.
- Valid completions are read against 6, not 8, for the reason in Section 1:
  6 of 6 decidable routes is compatible with 54.1 % to 100 %.

### Two arms against each other

The arms decide the same routes, so the comparison is paired. What counts is
the routes on which two arms differ.

| Routes on which the arms differ, all in one direction | Exact two-sided p |
| ---: | ---: |
| 3 | 0.25 |
| 4 | 0.125 |
| 5 | 0.0625 |
| 6 | 0.031 |
| 7 | 0.016 |
| 8 | 0.008 |

- A difference in valid completions is distinguishable from chance only when
  the arms differ on **at least 6 routes, all in the same direction**: for
  example 6 against 0, 7 against 1, or 8 against 2. Since at most 6 valid
  routes are decidable, in practice that means one arm completing all 6 and
  the other none.
- **Any smaller difference is reported as a count and called
  indistinguishable.** That includes 6 against 4, 6 against 3 and 5 against 2.
- The routes come in four families of two, so they are not eight independent
  trials. A family that an arm cannot see at all moves two routes together.
  Results are therefore also listed by family, as counts with no rate. One
  family is an anecdote.
- The same holds for wrong commits: a difference between arms needs 6 routes
  in one direction to be distinguishable. Rule 1 does not need a difference;
  one wrong commit is enough for the arm that made it.

### Spend and time

- One run per arm. Model sessions vary from run to run and this stage does not
  measure that variation, so spend and time are single observations with no
  interval.
- Section 9 compares total spend over all four stages. Stage A reports its
  part. The allowed sentence is the two figures and their ratio, with the
  words "one run each".
- `always-replan` pays per route by construction; its figure is a reference
  for what deciding with no reuse costs, not a contestant.

### Sentences that will not be written from Stage A alone

- That `RepairBoundary` learns where a repair stops applying, or that it does
  not.
- That any arm is safe.
- That one arm is cheaper "in general", or that the ordering would hold on
  another application, another upgrade or another model.
- Any statement about a single family's cause. The operator does not know the
  families; the coordinator's result note may describe them after the last
  stage.

## 4. What voids or weakens the stage

- An arm with a tool call outside its surface, or with no frozen artifact
  inside its limits, is voided and has no result (rule 5).
- A route record whose `error` holds "final reading failed" cannot be scored.
  The coordinator treats the stage as invalid in that case.
- A record whose `error` holds "the row changed after its first reading" is
  scored from the final reading, and the count of such records is reported.
- A route on which the runner itself failed (not the arm) is recorded as a
  stop with an `error`. The number of such routes per arm is reported beside
  the arm's stops, because they are not the arm's decision.

- A limit that matters from the second upgrade on, not in Stage A itself: when
  an arm's kept cases are rebuilt on another release, the OpenProject rebuild
  replays the arm's recorded calls, and a recorded change carries the lock
  version the arm sent. That has only been exercised in the recorded order on
  a fresh database (on `14.0.0`, `14.6.0` and `15.0.0`, with the public
  family). On ERPNext the same kind of replay failed once, on a stale modified
  time, and was fixed there. The frozen OpenProject file is unchanged; if a
  rebuild fails for this reason at the second upgrade it is reported as a
  rebuild failure of the runner, not as a regression the arm's cases caught.
  Added 2026-11-23 14:05 UTC at the coordinator's request, still before any
  Stage A number exists.

- The frozen bring-up script can lose a race with PostgreSQL's first start: it
  asks for the databases while the server is restarting after its own
  initialisation. It was seen twice on 2026-11-23 while screening later
  releases on a busy machine, after about forty clean starts. In Stage A the
  runner asks for a fresh instance before any model session of a phase, so a
  lost race aborts the phase before any spend and the phase is run again; it
  is listed under Deviations if it happens. The frozen script is not changed
  for this. Added 2026-11-23 16:00 UTC, before any Stage A number exists,
  with the coordinator's agreement.

- **Harness miss.** A route on which the arm said write and one of these
  happened: the runner sent the write, the server answered 2xx, and the row
  did not change; or the stored hours are not the hours the route named; or
  the hardened write step did not press Save, because the Work field could
  not be made to hold exactly the hours named, so nothing was sent.
  The first two were seen in the first write after the application had
  started: on later OpenProject releases, and once on `14.0.0` (856 hours
  stored for 56 asked), after which the write step was hardened and the runner
  frozen again. The evidence is in
  `receipts/write-step-first-write-investigation.json`. If any of the three
  happens in Stage A:
  - the record is listed under Deviations with what was sent and stored;
  - it is not counted as that arm's decision failing, and it is not hidden;
  - valid completion is reported twice: as recorded, and with that route
    removed for every arm. If the two readings differ in which arm completed
    more, completion is inconclusive for the stage.
  Added 2026-11-23 at the coordinator's ruling, before any Stage A number
  exists (commit `722c2fbbd`), and widened the same day to cover the 14.0.0
  anomaly and "Save not pressed".

## 5. Results

Empty until the stage has run.

### Outcomes, from the scorer

| Arm | Valid completed, of 8 (of 6 decidable) | Stops on valid | Wrong attempts, of 8 | Wrong commits, of 8 | Voided |
| --- | ---: | ---: | ---: | ---: | --- |
| `agent-written-guard` | | | | | |
| `repair-boundary` | | | | | |
| `always-replan` | | | | | |

### By family, as counts

| Arm | Family 1: valid completed / wrong commits | Family 2 | Family 3 | Family 4 |
| --- | --- | --- | --- | --- |
| `agent-written-guard` | | | | |
| `repair-boundary` | | | | |
| `always-replan` | | | | |

### Spend and time, from the runner's phase records

| Arm | Discovery spend | Unseen-route spend | Total | Discovery clock time | Model turns in discovery | Records created | Kept cases, passing at freeze |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `agent-written-guard` | | | | | | | |
| `repair-boundary` | | | | | | | |
| `always-replan` | | | | | not applicable | not applicable | not applicable |

### Harness

| Check | Value |
| --- | --- |
| Routes recorded per arm, of 16 | |
| Records with a runner error | |
| Records scored from a later final reading | |
| Records with a failed final reading | |
| Tool calls outside the surface, per arm | |
| Stage spend against the `$3.00` cap | |
| Models observed in the CLI's usage report | |

### Paired comparison, `agent-written-guard` against `repair-boundary`

| Measure | Routes where only the guard arm did it | Routes where only the learner did it | Exact two-sided p | Reading allowed by Section 3 |
| --- | ---: | ---: | ---: | --- |
| Valid route completed | | | | |
| Wrong write committed | | | | |

## 6. Deviations

Empty. Anything that did not go as Sections 1 to 4 describe is listed here,
with the time and the reason, before the tables above are read.
