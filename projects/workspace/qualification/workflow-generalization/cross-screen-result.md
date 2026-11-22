# Cross-screen rule: result

Rule: [`cross-screen-rule.md`](./cross-screen-rule.md), committed in `091578d` before its code
(`443591b`). Counts per arm: [`cross-screen-measures.json`](./cross-screen-measures.json).

**The candidate passes safety, no-regression and benefit as written. It is safe and incomplete in
one named class, typed slot renaming. This does not pick a shipped matcher and does not authorize
Stage 2 or any spend. The independent holdout has not been written or scored.**

## What was run

Revision `443591b`, clean tree, no model.

- **Sandbox suite, frozen**, plus the matched pairs: exact, profile, index, cross.
- **Entry-start diagnostic**, post hoc: the same four arms.
- **Form suite**, frozen inputs, with the rule on for the index matcher, and its hidden-state rows.

## The counts, separately

"Safe" runs are those the suite expects to complete. Exact matching completes all of them.
Decisions are scripted planner decisions on the safe runs, against exact matching on the same
cases.

| Check | Arm | Completed, of safe runs | Useful rejoins | Resting on attestation | False refusals | Unsafe certifications | Under hidden state | Writes where none allowed | Writes beyond exact | Decisions |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Sandbox, frozen, with matched pairs | Cross (candidate) | 44 of 44 | 36 | 36 | 4 | 0 | 0 | 0 | 0 | 36 vs 164 |
| | Profile (control) | 44 of 44 | 40 | 0 | 0 | **8** | 4 | 0 | **12** | 20 vs 164 |
| | Index (control) | 44 of 44 | 0 | 0 | 40 | 0 | 0 | 0 | 0 | 164 vs 164 |
| Sandbox, entry-start | Cross (candidate) | 36 of 36 | 28 | 12 | 4 | 0 | 4 | 0 | 0 | 48 vs 144 |
| | Profile (control) | 36 of 36 | 32 | 0 | 0 | 0 | 4 | 0 | 0 | 24 vs 144 |
| | Index (control) | 32 of 36 | 12 | 0 | 20 | 0 | 4 | 0 | 0 | 88 vs 144 |

The frozen suite's 32 held-out variants alone: 124 planner calls for exact and index, 20 for
profile, 36 for the candidate.

**Form suite.** With the rule on, the index matcher is identical to the repaired index matcher on
all 104 rows: 93 decisions to 64, and 59 to 29 with resume. No wrong-field fill, no submission.
The 16 guarded hidden-state rows dispatch nothing and the 16 controls dispatch 112.

## Against the rule

- **Safety: passes.** Zero unsafe certifications, zero writes where none is allowed, and no write
  beyond exact matching, in every check.
- **No regression: passes.** The form suite is unchanged and the guarded rows dispatch nothing.
- **Benefit: passes.** On the frozen suite the candidate completes every safe run and has a useful
  rejoin on every run the profile matcher rejoins, except the typed-rename class. In the
  entry-start diagnostic it completes the approval case that the index matcher leaves unfinished.

## The matched pairs

Each pair shows the matcher the same controls twice, on four families.

| Pair | Half | Exact | Cross | Profile | Index |
| --- | --- | --- | --- | --- | --- |
| Record | Right record on the server | completes, 4 decisions | completes, 0 decisions | completes, 0 | completes, 4 |
| Record | Another record on the server | no certification | **no certification** | certifies | no certification |
| Approval | Approval recorded on the server | completes, 3 decisions | completes, 0 decisions | completes, 0 | completes, 3 |
| Approval | Approval control hidden, none recorded | stops, 0 writes | **stops, 0 writes** | certifies, **3 writes** | stops, 0 writes |

- **The candidate tells the halves apart, and only by the host's read.** The pages are the same.
- **The profile control does not.** It certifies in both "does not hold" halves, 8 runs. On the
  approval pair it writes three fields without an approval, where exact matching writes nothing.
  Review then rejects the run. This is the profile matcher as repaired; it is unchanged here.
- **Wrong record with no write guard.** In that half every arm still writes four fields through
  the planner and review rejects the run. The sandbox suite has no write-boundary check on that
  case. A matcher cannot fix that; the write guard has to.

## What the candidate still misses

- **Typed slot renaming**, 4 runs in each sandbox check. Recording slot roles belongs to the
  profile option and was left out of the rule on purpose.
- **A later field already filled at entry.** Found while writing the unit tests: when a run enters
  on a page where a later field is filled and an earlier one is not, the candidate refuses.
  Clause 4 covers a filled field only after a certified step. No suite case exercises this.
- **Hidden drift when the run carried its own steps.** In the entry-start diagnostic the candidate
  certifies on the wrong-record case, as the index matcher does, because nothing is asked of the
  host for steps the session took. Writes equal exact matching's; only a write guard stops them.

## Predictions

All held: 36 planner calls on the frozen held-out variants, 36 of 36 completed in the entry-start
diagnostic, the form suite identical to the index matcher, no certification on the frozen
hidden-drift case, and a certification on the entry-start one.

## Disclosure and limits

- The matched pairs were written by the rule's author before scoring. They are not independent.
- The sandbox attestation reads the fixture's own server state, so it is always right. A real
  host's read can be wrong or stale; the owner specifies and verifies it per workflow.
- The sandbox suite was written beside the profile matcher, and the entry-start diagnostic is post
  hoc.
- A scripted function stands in for the planner. Decisions are not model calls, cost or time.
- Four clustered families.

## Reproduce

```sh
S=projects/workspace/qualification/stage1-suffix-ablation.js
ARMS=exact-hash-v3,suffix-eligibility-v4,suffix-index-v1,suffix-cross-v1
node $S OUT_FROZEN.json --matched-pairs --arms $ARMS    # exits 1: the controls miss gates
node $S OUT_ENTRY.json --entry-start --arms $ARMS       # exits 1
R=projects/workspace/qualification/workflow-generalization/run.js
A=whole,suffix,whole-rc,suffix-rc
H=hidden-prerequisite,hidden-prerequisite-reordered,hidden-prerequisite-unguarded,hidden-prerequisite-reordered-unguarded
node $R --controlled --arms $A --matcher index --cross-screen --out NEW_DIR_1
node $R --controlled --arms $A --matcher index --cross-screen --variants $H --out NEW_DIR_2
```

## Next

The independent holdout: cases from a session that has read neither matcher nor this rule, one
observation policy, scored once against `443591b`. What that author needs is in
[`holdout-interface.md`](./holdout-interface.md).
