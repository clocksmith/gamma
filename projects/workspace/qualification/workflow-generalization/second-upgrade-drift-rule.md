# What counts as a second upgrade that bites

Written by the evaluator of the same-model three-arm test (clocksmith/deco#88)
on 2026-11-23, before any arm has produced a result on any second upgrade and
while Stage A is on hold. It changes no frozen file: the runner, the
pre-registration, the sealed cases and the scorer are as they were.

## Why this rule exists

The probes so far show that the stand-in pipeline behaves on later releases:
OpenProject 14.6.0 and 15.0.0, ERPNext v15.30.0 and v15.40.0. On the public
example family none of those releases changes anything the workflow touches.
An upgrade that needs no maintenance cannot show whether an arm recovers from
drift. Those releases stay in the study as **no-change controls**, and are
reported under that name.

## The rule

A release pair (first-upgrade target -> candidate) of one application is a
**second upgrade that bites** for a family only if all four hold. Each is
measured with scripted probes only: no model call, no arm, no sealed case.

1. **The old workflow fails on a valid case.** The page write recorded for the
   first-upgrade target, replayed unchanged (same selectors, same calls), does
   not commit on the candidate for at least one valid public example route.
   A commit is judged from the row, as in the frozen runner. 3 of 3 repeats.
2. **The task is still possible.** A scripted reference route, written for
   screening only and never shown to an arm, commits the same valid write on
   the candidate as the acting account. 3 of 3 repeats.
3. **A look-alike still needs the arm to stop.** For at least one invalid
   look-alike of the family, the always-write control commits the wrong write
   on the candidate. If the server refuses it, stopping is the server's doing
   and that look-alike does not count. 3 of 3 repeats.
4. **The cases still mean what they say.** The seeder builds the public example
   routes on the candidate and each route's label agrees with the live state.

A candidate that fails any one of the four is not a second upgrade that bites.
It may still be kept as a no-change control.

## Screening

- Screen stock releases only, in ascending version order after the
  first-upgrade target, one application at a time.
- Freeze the **first** release that satisfies all four. Do not keep looking for
  a better one.
- Record every release screened, with the result of each of the four checks,
  including the ones that fail.
- The expected result of each check is written into the receipt before the
  probe runs.

## If no stock release qualifies

Report exactly that, per application, with the list of releases screened.
Drift made by the experimenters (a renamed field, a moved control, a changed
permission) may be studied, but only under the name **injected drift**, in its
own section, and never called an upgrade or counted toward the four application
upgrades the decision rule of the pre-registration needs.

## What this does not decide

- Which method wins. That is Section 9 of the pre-registration.
- Anything about Stage A, which is on hold by the owner.
- ERPNext cases. They need their own families, record format and scoring path
  before any ERPNext stage can be frozen.

## Limits

- The rule is checked on the public example family. A sealed family could
  behave differently on the same release; that is found only when it runs.
- "Fails on a valid case" is tested with one recorded workflow per application.
  A different recorded workflow could survive a release that breaks this one.
- This is a development evaluation: the evaluator and the operator are
  separated by session, not by account.

## Amendment 1 (2026-11-23, before any screening result exists)

Made by the evaluator after the operator counted the releases (29 for
OpenProject, 149 for ERPNext) and before the first screening probe ran.

- **Granularity.** Screen `x.y.0` releases only. Patch releases are not
  screened.
- **Order of the checks.** Run check 4, then check 1, on every candidate.
  Run checks 2 and 3 only when check 1 is met; otherwise record them as
  "not needed: check 1 not met". A release that fails check 1 is already out.
- **Check 2 uses the arms' own write surface.** The arms write through the
  page, so the reference route is a page write with whatever selectors the
  candidate needs. A write through the API alone does not show the task is
  possible for an arm; record it as an extra fact, not as check 2.
- **Check 3 uses that same reference route** on the look-alike.
- **OpenProject:** strict ascending order over all 29.
- **ERPNext:** ascending at a stride of ten minor releases (v15.30.0,
  v15.40.0, v15.50.0, ...) until check 1 is first met, then strict ascending
  inside the last interval, and freeze the first release there that meets all
  four. This finds the first biting release only if a break persists. A
  release that broke the workflow and was repaired within the same stride
  would be missed; the receipt must say so.
