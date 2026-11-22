# Suffix matching: one revision, both suites

Main carries two suffix matchers in one file, `src/client/suffix-eligibility.js`:

- **Index matcher** (`suffixIndex`, `certifySuffix`): the candidate.
- **Profile matcher** (`suffixEligibility`, `evaluateSuffixEligibility`): kept as an ablation.

Each was measured on the suite written beside it. This run puts both through both suites at one
revision. It needs no model, tenant or spend.

## Source under test

The merged revision is `a6a9a6bfed3c20362e8e6ff148ef1624131f1fb1`. The run commit adds this file and
named arms to the sandbox harness. It changes nothing under `src/` and nothing in the frozen form
suite, so the code under test is the merged revision. Each receipt records the commit and the tree
hash of `src/`.

The sandbox harness change leaves every fixture, variant and near-miss as it was. With no
arguments it still writes a receipt byte-identical to the committed
`gammatron-v4-stage01/stage1-offline-suffix-ablation.json`.

## Suites and arms

**Form suite** (`workflow-generalization/`, inputs frozen by `test-freeze-v2.json`): two vendors,
13 variants, four arms (`whole`, `suffix`, `whole-rc`, `suffix-rc`), scripted planner.

- `--matcher index`: candidate.
- `--matcher profile`: ablation, with word routes and again with `--numeric-routes`.
- The four hidden-state rows, for each matcher.

**Sandbox suite** (`stage1-suffix-ablation.js`): four workflow families, 32 held-out variants and
24 adversarial near-misses per arm, scripted planner.

- `exact`: baseline.
- `index`: candidate.
- `profile`: ablation.
- `both`: both options on. Exploratory; no verdict depends on it.

## Decision rule, written before the run

Safety, for the candidate:

- **S1, form suite.** Zero wrong-field fills and zero submissions. Every variant that must stop
  stops. Evaluation leaves the graph and index unchanged. Guarded hidden-state rows dispatch no
  effect.
- **S2, sandbox suite.** All 24 near-misses meet the suite's own expectations: completion as
  expected, no action where none is allowed, the approval click never skipped, no certification
  on the dirty-field case, and zero unsafe certifications.

Benefit, for the candidate:

- **B1, form suite.** Fewer scripted decisions than exact matching in total, with and without
  resume, and more on no variant.
- **B2, sandbox suite.** All 32 held-out variants complete, and the suite's own gates hold:
  rejoin within two planner steps on at least 60% of variants, and at most 0.65 times the planner
  calls of exact matching.

Verdict:

- **All four hold:** the candidate goes forward as the single matcher. The profile path stays only
  as an ablation.
- **S1 and S2 hold, B1 or B2 fails:** the candidate is safe but not sufficient. The record names
  the variant classes it misses. Neither matcher is said to replace the other.
- **S1 or S2 fails:** the candidate fails until fixed.

The ablation and the exploratory arm are reported with the same measures and carry no verdict.
Each configuration runs once. Failed rows stay in the record. A matcher change made after reading
these results needs a new run, reported separately.

## Disclosure

- The index matcher and the form-suite arms were written in this lane. The profile matcher, the
  sandbox suite and the merge were written in another.
- The sandbox fixtures and the profile arm's committed sandbox receipt were read before this run.
  The index matcher has not been run on the sandbox suite by this lane before.
- The merge added a dirty-field guard to the index matcher with the sandbox dirty-field case in
  view. That near-miss class is not blind for the candidate.
- The earlier disclosure stands: the rule that a click waits while a new control is unanswered was
  added after reading the `extra-question` variant.
- The 21-pair holdout in `gammatron-v4-stage01/independent-holdout/` is separate evidence at an
  earlier revision. It is not rerun here and does not stand in for this check.

## Predictions, from reading the code

- **Index on the sandbox suite:** few certified rejoins. It needs every step before a learned
  state to be run in this session or visibly settled on the page, and most sandbox variants begin
  mid-workflow. B2 is likely to fail.
- **Profile on the form suite:** no certified rejoins, as in `suffix-crosscheck.md`.
- **Both options on:** behaves like the index arm, because replay consults the index first and
  never falls through to the profile matcher.

## Result, 2026-11-21, commit `f6dbb2a`, clean tree

The `src/` tree at the run commit is `a186e8c`, the same as at the merged revision. No model was
called. Node 22.20.0; the form suite ran in Chrome 158.

**Verdict by the rule: S1, S2 and B1 hold; B2 fails. The index matcher is safe on both suites but
not sufficient. Neither matcher replaces the other.**

### Form suite: 104 evaluation runs per configuration

| Matcher | Decisions without resume | Decisions with resume | Certified rejoins | Wrong-field fills | Rows as expected |
| --- | ---: | ---: | ---: | ---: | ---: |
| Index (candidate) | 93 to 64 | 59 to 29 | 23 and 30 | 0 | 104 of 104 |
| Profile, word routes | 93 to 93 | 59 to 59 | 0 and 0 | 0 | 104 of 104 |
| Profile, numeric routes | 93 to 93 | 59 to 59 | 0 and 0 | 0 | 104 of 104 |

- **Index.** Fewer decisions on 8 of 26 vendor-variant rows in each pair, more on none. The gains
  are on `reordered`, `changed-label`, `extra-question` and `dependent-question`. These are the
  numbers recorded before the merge in `suffix-ablation.md`, so the merge did not change this
  matcher here.
- **Profile.** Every row equals exact matching, as in `suffix-crosscheck.md`.
- **All configurations.** No submission. The 14 rows per arm that must stop stopped. Evaluation
  left the graph and index unchanged.

Hidden-state rows, for each matcher: the 16 guarded rows dispatched no effect and the 16 controls
dispatched 112, seven in every run. On the reordered page the index matcher certified a suffix in
4 guarded rows; the write-boundary check refused each before dispatch. In the controls, with the
check removed, it certified 20 times and the writes went into the locked draft. The matcher cannot
see that state. The check is what stops the write.

### Sandbox suite: 32 held-out variants and 24 near-misses per arm

| Arm | Held-out completed | Rejoin within two steps | Planner calls | Reused steps | Certified, held-out / near-miss | Near-miss expectations failed | Unsafe certifications |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact | 32 | 4 of 32 (12.5%) | 124 | 16 | 0 / 0 | 0 | 0 |
| Index (candidate) | 32 | 4 of 32 (12.5%) | 124 | 16 | 0 / 0 | 0 | 0 |
| Profile (ablation) | 32 | 28 of 32 (87.5%) | 20 | 120 | 28 / 8 | 0 | 0 |
| Both options (exploratory) | 32 | 4 of 32 (12.5%) | 124 | 16 | 0 / 0 | 0 | 0 |

Receipt: [`suffix-both-suites-sandbox.json`](./suffix-both-suites-sandbox.json).

- **Index.** It never certified, so every row equals exact matching. It refused 1,008 candidates
  as `prefix-unaccounted` and 168 as `page-mismatch`. Its near-miss result is therefore safe by
  abstaining. It says nothing about whether a certification there would have been right.
- **Profile.** It reproduces its committed receipt, 124 calls to 20. Its 8 near-miss
  certifications are 4 on the hidden-drift case and 4 on the approval case. On hidden drift it
  dispatched 4 actions, the same number exact matching dispatches through the planner; review
  rejected the run and the matcher then added a guard. On the approval case the approval click
  was made and the run completed, as the suite expects.
- **Both options.** Identical to the index arm. `replay` and `continueReplay` in
  `src/client/trace-dag.js` consult the index first and return, so the profile matcher is never
  asked. The file holds both matchers; a run uses one.

### What each matcher misses

- **Index:** every sandbox variant that begins after the taught entry screen or enters by an
  untaught route, which is seven of the eight classes. In the eighth, an unseen entry that leads
  to the learned page unchanged, all arms tie at one planner call. The cause is one rule: each
  step before a learned state must have been run in this session or be visibly settled on the
  page.
- **Profile:** every form-suite class that changes the page: `reordered`, `changed-label`,
  `extra-question` and `dependent-question`. The causes were read at an earlier revision and are
  listed in `suffix-crosscheck.md`. They were not read again here.
- **After a hidden-state failure:** the profile matcher adds a guard or demotes the state, 4 of 4
  here. The index matcher has no such step.

### Predictions

All three held.

### Limits

- A scripted function stands in for the planner. Decisions are not model calls, latency or spend.
- The sandbox suite is synthetic snapshots behind an in-memory adapter. The form suite is real
  Chromium on local pages. Neither is a tenant.
- Four families and two vendors are clustered cases, not independent samples.
- No failure rate is estimated. Zero wrong-field fills over 30 certified rejoins would bound the
  rate below about 10% at 95% confidence only if the rejoins were independent. They are not: they
  come from two near-identical vendors and a handful of variants.
- The 21-pair holdout was not rerun.

### Next

One matcher that passes both suites needs a matcher change, not a flag. The change has to let a
run enter at a learned state it did not walk to, under the footprint, value and dirty-field
checks that entry needs, while keeping the page-change tolerance measured on the form suite. That
is a new matcher. It needs its own rule written first, one run on both suites, and cases neither
matcher has seen.

## A second, independent run

Another lane ran the same cross-check at the merged revision and landed it first, in
[`../gammatron-v4-stage01/matcher-crosscheck/`](../gammatron-v4-stage01/matcher-crosscheck/README.md).
This run finished before that one landed, and its result was pushed only afterwards. Every shared
number agrees: 124, 20 and 124 planner calls on
the sandbox suite; 93 to 64 and 59 to 29 for the index matcher and no change for the profile
matcher on the form suite; zero unsafe certifications; 1,008 and 168 index refusals.

This record adds four things to that one:

- The decision rule and predictions, committed (`f6dbb2a`) before the first run.
- The both-options arm, which shows a run uses only the index matcher.
- The hidden-state rows through the write-boundary check, for each matcher.
- The profile matcher on numeric routes, and a clean tree for every run.

The two lanes changed the sandbox harness differently. Main keeps the other lane's version, with
the both-options arm added to it. The receipt here was written by the harness at `f6dbb2a`, which
names the arms `exact-hash-v3`, `suffix-eligibility-v4`, `suffix-index` and
`suffix-index-plus-profile`. Main's harness, run with the four arms below, gives the same totals
for every arm.

```sh
node projects/workspace/qualification/stage1-suffix-ablation.js OUT.json \
  --arms exact-hash-v3,suffix-eligibility-v4,suffix-index-v1,suffix-index-plus-profile  # exits 1: index gates fail
A=whole,suffix,whole-rc,suffix-rc
H=hidden-prerequisite,hidden-prerequisite-reordered,hidden-prerequisite-unguarded,hidden-prerequisite-reordered-unguarded
R=projects/workspace/qualification/workflow-generalization/run.js
node $R --controlled --arms $A --matcher index --out NEW_DIR_1
node $R --controlled --arms $A --matcher profile --out NEW_DIR_2
node $R --controlled --arms $A --matcher profile --numeric-routes --out NEW_DIR_3
node $R --controlled --arms $A --matcher index --variants $H --out NEW_DIR_4
node $R --controlled --arms $A --matcher profile --variants $H --out NEW_DIR_5
```
