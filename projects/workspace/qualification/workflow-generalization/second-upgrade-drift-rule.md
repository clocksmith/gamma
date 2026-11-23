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

## Amendment 2 (2026-11-23, after 16 OpenProject releases were screened)

This amendment is **not** blind to screening results. It was written after
16 releases (14.1.0 to 16.3.0) had been screened with none biting, and after
the operator found that from 16.4.0 the frozen seeder cannot create a project
("Workspace type is not set to one of the allowed values"). No arm has
produced any result on any second upgrade.

By the letter, check 4 is not met on 16.4.0 with the frozen seeder, and that
is recorded as such. But a set-up tool that a newer data model rejects says
nothing about whether the cases still mean what they say, or whether the old
workflow fails, which is what the rule is for. So screening may continue from
16.4.0 with a **screening seeder**, under these conditions:

1. It is a separate file. The frozen seeder is not changed.
2. It differs from the frozen seeder only by supplying values the newer
   release requires in order to create the same records. It adds no record,
   removes none, and changes no value an arm or a label depends on.
3. Its full difference from the frozen seeder is committed and shown to the
   evaluator before any release is screened with it, and its hash is recorded
   in the receipt.
4. Check 4 is then judged as written: the routes are built and each label
   agrees with the live state. Every entry screened this way says
   "screened with the screening seeder" and also records "check 4 not met with
   the frozen seeder".
5. A release that meets all four checks this way is reported as a second
   upgrade that bites **with adapted set-up**. A stage that uses it needs its
   own freeze, including that seeder, before any arm runs.
6. If a later release needs a further set-up change, screening stops and the
   evaluator is asked again. Changes are not stacked without a ruling.

If no release qualifies even so, the report says: no stock OpenProject release
from 14.1.0 to 17.9.0 qualifies; 14.1.0 to 16.3.0 do not break the workflow,
and from 16.4.0 the result holds only with adapted set-up.

## Amendment 3 (2026-11-23, after 5 ERPNext and 28 OpenProject releases were screened)

This amendment is **not** blind. It was written after 28 OpenProject releases
and the first 5 ERPNext stride points had been screened, none of which bites.
No arm has produced any result on any second upgrade. It records the owner's
direction to the operator: keep the search bounded, and do not widen it after
seeing results in order to manufacture a test.

- **The ERPNext search is the 17 stride points already listed in the receipt**
  (v15.30.0 to v16.60.0). If none meets check 1, the search ends there. No
  further points are added.
- If one of the 17 does meet check 1, the strict ascending search inside that
  last interval applies, as amendment 1 already says. That is not a widening.
- **Injected drift is not substituted for a second upgrade.**
- **Correction to amendment 2.** Its closing sentence named 17.9.0. What ran
  is: OpenProject 14.1.0 to 17.8.0 screened through check 1 (28 of 29), none
  bites; from 16.4.0 only with adapted set-up; 17.9.0 not screened, because it
  cannot be seeded without rewriting how the seeder grants status transitions.
- **If no release qualifies, the second upgrade is a no-change control**, fixed
  now, before any arm result: OpenProject 15.0.0 and ERPNext v15.40.0.
- **What a no-change control can and cannot show.** It can catch a wrong commit
  and a needless change to a workflow that still works. It gives no evidence
  about which method repairs a second break better. Section 9 of the
  pre-registration stays byte-identical, and its words "both applications and
  both upgrades" are met mechanically by a no-change control; so any report of
  a rule 2 or rule 3 outcome must say, beside that outcome, that the second
  upgrade was a no-change control and that only one upgrade per application
  needed repair.

**Note on amendment 3, added the same hour.** When amendment 3 was committed
(gamma 2bb553eaf) the ERPNext receipt already held a sixth entry, v15.80.0.
The evaluator had seen that six releases were listed and that none was marked
as biting, and had not read the sixth entry, which records check 1 as met (the
old write committed 0 of 3, by timeout, cause not yet examined). So amendment 3
was written after six ERPNext results, one of them possibly a break, and not
after five clean ones as its heading says. Its content stands: the search stays
bounded at the 17 points, and a release that meets check 1 is followed up
inside its interval as amendment 1 requires.

## Amendment 4 (2026-11-23, after ERPNext v15.80.0 was examined)

This amendment is **not** blind. It was written after the evaluator saw that
v15.80.0 fails the old page write 3 of 3 because the Terms tab changed from
`<a>` to `<button>` (receipt at gamma a2cabb292). No arm has produced a result
on any second upgrade. The evaluator confirmed in `three-arm-erpnext/` that the
arms have only `erp_request` and `erp_get`, and that the runner performs the
write through `erp-write-step.mjs`.

- **Check 1 tested a layer the arms do not own.** A break in the runner's page
  write fails every arm alike and cannot show which arm repairs better.
- **For ERPNext, check 1 now reads:** on the three labelled cases, a scripted
  run of the REST reads the frozen work depends on reaches the wrong decision,
  on 3 of 3 repeats. No model, and no page write.
- **v15.80.0 is recorded as "breaks the shared write only".** It does not bite
  on this evidence unless the new check 1 is met. The same label applies to any
  release that breaks only the page write.
- **The runner's write step is not changed.** The no-change control, v15.40.0,
  predates the tab change and needs no selector fix.
- **The ascending search inside v15.70.0 to v15.80.0 is dropped**, because it
  was locating a page-only change. The bound stays at the 17 stride points:
  each one, including those already screened, gets the new check 1 once.
- If none meets it, the ERPNext second upgrade is the no-change control, as
  amendment 3 says.
