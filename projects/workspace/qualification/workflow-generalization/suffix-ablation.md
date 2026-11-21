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
