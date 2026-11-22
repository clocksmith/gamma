# Skill baseline and a dry run of the four-arm comparison

Stage 2 is meant to ask whether suffix rejoin beats a skill that can recover, not only whether it
beats exact replay. This adds that skill and runs the comparison harness once with no model.

**No model was called and nothing was spent. This is a harness dry run on local pages, not a
Stage 2 result.**

## The skill

`src/client/skill-exec.js`. It is inspired by executable-skill systems such as WebXSkill and does
not reproduce any of them.

- **What it is.** The ordered actions of the verified teaching run, with input slots in place of
  values. It keeps no page-state graph.
- **Same stack.** It stands where a planner stands, so every action it proposes passes the same
  observation scope, session checks, step authorization, prerequisite check, dispatch checks and
  journal as a planner action. Budgets and the planner are the same as in the other arms.
- **When it hands a turn to the planner.**
  - The next step's target is missing or not unique, or its input slot is absent.
  - The next step is a click and the page holds an empty writable control that was not there when
    the click was taught.
  - The script is finished but the planner had to act during the run, so the planner decides when
    the result is ready.
- **What it does without the planner.** It skips a fill whose value is already on the page or
  that the planner already supplied, and it proposes a step again when the service refuses it as
  stale before dispatch.

## Dry run, 2026-11-22, commit `f7fc11b`, clean tree

Form suite, frozen inputs, two vendors, 13 variants, scripted planner, Chrome 158. 26 runs per
arm: 12 that must complete and 14 that must stop.

| Arm | Completed, of 12 | Stopped, of 14 | Decisions on the 12 | Decisions on all 26 | Writes | Wrong-field fills | Submissions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh planning | 12 | 14 | 104 | 138 | 112 | 0 | 0 |
| Exact replay with resume | 12 | 14 | 42 | 59 | 112 | 0 | 0 |
| Suffix rejoin with resume (index matcher) | 12 | 14 | 12 | 29 | 112 | 0 | 0 |
| Skill with recovery | 12 | 14 | 14 | 18 | 112 | 0 | 0 |

A decision is a turn the planner took. Script steps and replayed steps cost none.

Hidden-state rows, per arm: the 4 guarded rows dispatch nothing and the 4 controls, with the
check removed on purpose, dispatch 28.

## Reading

- **The skill is a real competitor.** On the runs that must complete it takes 14 planner turns
  against 12 for suffix rejoin, and every arm completes all 12.
- **Where suffix rejoin is ahead.** A changed label and an extra question: 1 turn against 2. The
  skill needs a second turn for the planner to confirm the finish after any recovery.
- **Where the skill is ahead.** A page refreshed mid-run: 0 turns against 1, because the script
  re-grounds on the fresh page. On the runs that must stop it spends 4 turns in total against 17:
  the session's guards stop most of them before any planner turn.
- **Safety is the same in every arm.** The same 112 writes, no wrong-field fill, no submission,
  and nothing written into a locked draft. The guards do that work, not the arm.
- **So local decision counts do not separate the two.** If suffix rejoin is worth its state graph,
  the evidence has to come from pages a script cannot ground and from real planner cost and time.

## Disclosure

- The skill's "new empty control before a click" hand-back was written with this suite's
  `extra-question` and `dependent-question` variants in view. It makes the baseline stronger, and
  it is tuned to this suite in the same way the index matcher's click rule was.
- A scripted function stands in for the planner. Turns are not model calls, cost or time.
- Two near-identical vendors and synthetic faults, as in every record here.

## Reproduce

```sh
R=projects/workspace/qualification/workflow-generalization/run.js
H=hidden-prerequisite,hidden-prerequisite-reordered,hidden-prerequisite-unguarded,hidden-prerequisite-reordered-unguarded
node $R --controlled --arms fresh,whole-rc,suffix-rc,skill --matcher index --out NEW_DIR_1
node $R --controlled --arms fresh,whole-rc,suffix-rc,skill --matcher index --variants $H --out NEW_DIR_2
```

## What a paid run would add, and what it still needs

The same four arms with a real planner give model calls, cost and time, including teaching. No
paid run is authorized. Before one: the owner confirms the cap (proposed: $40 in total and $2 per
arm-run), names the tenants and test accounts, and verifies each workflow's record binding, atomic
version check and server-side deduplication. Unversioned forms stay out of the primary comparison.
