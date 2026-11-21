# Stage 1: suffix eligibility against the whole-page graph

Offline ablation for clocksmith/deco#88. No model is called. It decides only whether
suffix eligibility earns a paid Stage 2 run. It is not a product or performance claim.

## What is compared

All arms use the same frozen forms, oracle, policy and variants as the existing
experiment, in `--controlled` mode, where a scripted function stands in for the planner.

| Arm | Graph | Suffix eligibility | Resume after planner steps |
| --- | --- | --- | --- |
| `whole` | whole-page | off | off |
| `suffix` | whole-page | on | off |
| `whole-rc` | whole-page | off | on |
| `suffix-rc` | whole-page | on | on |

```sh
node projects/workspace/qualification/workflow-generalization/run.js --controlled \
  --arms whole,suffix,whole-rc,suffix-rc --out bench/out/suffix-stage1
```

## The rule under test

On an exact state-hash miss, replay may continue from a learned node only when all of
these hold on the live page. Otherwise the miss is handled exactly as before.

- Same template, origin, read scope and account.
- At least 60% of the learned page's controls are present (`minOverlap`).
- Every step on some learned path to that node was executed in this run, or its value is
  already settled on the page.
- The next learned step has exactly one live target, with a supplied input or an
  authorized click.
- No pending fill is already done.
- No new control competes in meaning with a pending target, and none is unlabelled.
- No blocking dialog or alert is present.
- A click may not leave the page while a new control is unanswered.
- Exactly one learned node qualifies.

Each step after that goes through the unchanged session checks and workspace dispatch,
and the next state must certify as that step's learned successor.

## Decided before the first run

- `minOverlap = 0.6`, `maxLocalSteps = 24`. Not tuned on these variants.
- Pass: zero wrong-field fills and zero submissions in every arm; every variant that
  must stop safely still stops; the frozen graph and index are unchanged after reuse.
- Earns Stage 2: with the pass conditions met, a suffix arm uses fewer scripted planner
  decisions than its matching whole arm on at least one variant and more on none.
- Stop here if a suffix arm records any wrong-field fill, completes a variant that must
  stop, or shows no reduction.

## Disclosure

The overlap threshold and the lookalike rule were written before the variant
definitions in `fixture.js` were read. The rule that a click waits while a new control is
unanswered was added after reading the `extra-question` variant. It is a general rule
(never leave a page with an unanswered new question), but it was prompted by that
variant, so its effect there is not independent evidence.

One vendor holdout per vendor, synthetic faults, contact fields only. Zero observed
wrong-field fills bounds nothing by itself: with n certified rejoins and no failure, the
95% upper bound on the failure rate is about 3/n.

## Result, 2026-11-21

Controlled run on commit `24888ec` with a clean tree, headless stock Chrome 158, both
vendors, all 13 frozen variants, four arms: 104 evaluation runs. An earlier run on
`65503ca` gave the same decisions, cached steps and outcomes; it undercounted
certifications because a session swap dropped them, which `24888ec` fixes.

| Arm | Scripted planner decisions | Cached steps | Certified rejoins | Refusals | Wrong-field fills | Submissions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `whole` | 93 | 35 | 0 | 0 | 0 | 0 |
| `suffix` | 64 | 62 | 23 | 14 | 0 | 0 |
| `whole-rc` | 59 | 59 | 0 | 0 | 0 | 0 |
| `suffix-rc` | 29 | 89 | 30 | 27 | 0 | 0 |

- Every run met its expected behaviour: 12 of 26 completed in each arm, and the 14
  that must stop safely stopped in each arm. The graph and index were unchanged.
- Each suffix arm used fewer decisions than its matching whole arm on 8 variant rows
  and more on none: `reordered` (8 to 0, and 5 to 0), `changed-label`,
  `extra-question` and `dependent-question`, for both vendors.
- The seven safe-stop variants behaved identically with and without suffix
  eligibility, including `semantic-decoy`, `ambiguous-label` and `hidden-duplicate`,
  which were refused as lookalikes or ambiguous targets.
- Leaving out `extra-question`, whose rule was prompted by that variant: 75 to 54
  without resume, and 47 to 27 with it.

The pass conditions were met and the Stage 2 condition was met.

What this does not show:

- No model ran. A scripted function stood in for the planner, so these are decision
  counts, not model calls, cost or time.
- Two vendors, one holdout each, contact fields only, synthetic faults. The 26 rows are
  two near-identical copies of 13 variants, so four kinds of change account for the gain.
- Zero wrong-field fills over 30 certified rejoins bounds the failure rate only below
  about 10% at 95% confidence, before allowing for that clustering.
- Hidden page state that the observation cannot see is not exercised here.

Raw rows, reports and private graphs stay in local evidence, outside the repository.

## Hidden-state extension

Added after the result above, to cover the open item: a page that matches while a
server-side prerequisite differs. These four variants sit outside the frozen v2 list,
reuse frozen pages unchanged and run only when named.

| Variant | Page | Server-side draft | Prerequisite check |
| --- | --- | --- | --- |
| `hidden-prerequisite` | same outline as the learned page | locked | on |
| `hidden-prerequisite-reordered` | reordered | locked | on |
| `hidden-prerequisite-unguarded` | same outline as the learned page | locked | off (negative control) |
| `hidden-prerequisite-reordered-unguarded` | reordered | locked | off (negative control) |

The lock lives in the harness process and is never rendered, so no matcher can see it.
The check is the host's step-authorization gate, which runs after a matcher proposes a
step and before dispatch. Every effect dispatched while the draft is locked counts as a
write in the wrong server-side state.

```sh
node projects/workspace/qualification/workflow-generalization/run.js --controlled \
  --arms whole,suffix,whole-rc,suffix-rc --out bench/out/suffix-hidden-state \
  --variants hidden-prerequisite,hidden-prerequisite-reordered,hidden-prerequisite-unguarded,hidden-prerequisite-reordered-unguarded
```

Decided before the run:

- Checked rows: not completed, zero dispatched effects, zero submissions, in every arm.
- Negative controls: at least one dispatched effect in every arm. If a control writes
  nothing, the fixture cannot detect the failure and the extension proves nothing.
- `hidden-prerequisite` must report the same outline as the learned page.
- On the reordered page, the suffix arms must show a certified proposal before the refusal.
