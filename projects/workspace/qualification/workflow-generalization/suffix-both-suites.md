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

## Result

Pending.
