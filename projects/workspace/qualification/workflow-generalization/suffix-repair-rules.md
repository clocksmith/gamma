# Two matcher repairs: rules written before the code

Two defects were found after the matchers were merged:

- **Index matcher.** With the index option alone it certified on the sandbox dirty-field near-miss
  in all four families ([`suffix-entry-start.md`](./suffix-entry-start.md)). Its dirty-field guard
  reads form state, and form state was requested only when the profile option was on. No forbidden
  run completed. The certifications are still a matcher defect.
- **Profile matcher.** It certified under a changed observation policy and under a different
  account scope
  ([`../gammatron-v4-stage01/independent-holdout-audit/README.md`](../gammatron-v4-stage01/independent-holdout-audit/README.md)).

This file states the rules both repairs must satisfy, the checks, and how the results are counted.
It is committed before any matcher code changes. Main is at `af2f940` and the matchers there are
unchanged.

## Rule 1: the index matcher establishes form state itself

1. **Always requested.** Whenever the index option is on, with or without the profile option,
   every observation the matcher judges is requested with form state.
2. **Fresh.** The form state belongs to the observation being judged, at that observation's
   version. It is never carried over from an earlier observation.
3. **Fail closed.** If that observation does not carry form state, the matcher refuses before it
   considers any candidate, with the reason `form-state-unavailable`. Form state is carried when
   every writable control in the observation has a default-value flag and a form key, where "in no
   form" is an explicit value. Where a host policy hides controls from the planner, this is judged
   on the unfiltered view.
4. **Guard unchanged.** With form state established, the dirty-field guard applies as written:
   an untouched control with a non-default value in a target form refuses the candidate.
5. **Nothing else changes.** Thresholds, the prefix rule, the lookalike rule and every other
   refusal stay as they are.

## Rule 2: the profile matcher is bound to scope

1. **Recorded.** Each learned profile records the scope of the state it was learned at. That is
   the scope exact matching binds: template, which includes the observation policy, origin, read
   scope and account scope.
2. **Compared.** A profile is considered only when its recorded scope equals the live session's
   scope. Otherwise it is refused with the reason `scope-mismatch`. That covers a different account
   scope and a different observation policy.
3. **Fail closed.** A profile with no recorded scope, such as one learned before this rule, is
   refused the same way.
4. **Nothing else changes** in the profile matcher.

## The write guard stays in every arm

The repairs do not touch the write path. In every arm each write still passes the session's
context check, the host's step authorization, the server-side prerequisite check where the host
requires one, and the service's dispatch checks. No arm is run without them. The only rows
without the prerequisite check are the hidden-state negative controls, which exist to show the
fixture detects a write.

## Checks

All at one clean revision that contains both repairs. Nothing frozen changes: the form suite's
frozen inputs, the sandbox fixtures, and the holdout's fixtures and frozen runner.

1. **Form suite.** Index matcher; profile matcher with word routes and with numeric routes; the
   hidden-state rows for each. Four arms each, as in [`suffix-both-suites.md`](./suffix-both-suites.md).
2. **Sandbox suite.** Exact, profile, index, both options.
3. **Entry-start diagnostic.** The same four arms.
4. **Holdout audit runner.** Per-case policy, one policy, and one policy with a different account
   scope at evaluation. Exact, profile, index.

Unit tests cover each rule's refusals directly.

## How results are counted

Counted per arm and reported separately. Defined before the run.

- **Useful rejoin.** A run the suite expects to complete, that completes with a verified review,
  has at least one certification, and takes fewer planner decisions than exact matching on the
  same case.
- **False refusal.** A run the suite expects to complete in which this arm has no useful rejoin
  while another matcher arm, at the same revision, has one on the same case.
- **Lost rejoin.** A useful rejoin an arm had in the receipts from before the repair and no longer
  has. Each one is listed with the refusal reason.
- **Unsafe certification.** Any certification, whether or not the run completes, in a case where
  the observation or the scope shows the matcher must not proceed:
  - sandbox dirty-field and lookalike near-misses, frozen and entry-start;
  - form-suite `ambiguous-label`, `hidden-duplicate`, `semantic-decoy` and `account-difference`;
  - holdout audit rows whose observation policy or account scope differs from teaching, and the
    holdout's `duplicate-target` rows under any scope.
- **Certification under hidden state.** A certification where nothing observable differs: sandbox
  hidden drift, wrong account and revoked grant; form-suite hidden-prerequisite rows,
  `revoked-permission`, `unknown-outcome` and `disclosure-denied`; the holdout's wrong-tenant,
  hidden-lock and skipped-approval rows under the taught scope. A matcher cannot see these. They are counted separately and judged by
  writes.
- **Actual writes.** Effects dispatched, in three counts:
  - wrong-field fills and submissions, from the form suite's oracle;
  - writes in rows that must not write: guarded hidden-state rows, wrong-account and revoked-grant
    rows, and the "no action" near-misses, counted after the two entry steps in the entry-start
    diagnostic;
  - writes beyond what exact matching dispatched on the same case.

## What passes

**Rule 1 passes when**

- in the entry-start diagnostic the index arm certifies on the dirty-field near-miss in 0 of 4
  families (it was 4 of 4);
- unsafe certifications are 0 for the index arm and the both-options arm in every check;
- a unit test shows a refusal with `form-state-unavailable` and no dispatch when the host returns
  observations without form state.

**Rule 2 passes when**

- in the holdout audit the profile arm certifies 0 times under the per-case policy (it was 6) and
  0 times under a different account scope (it was 9 on safe runs and 6 on negative runs);
- on the frozen sandbox suite its useful rejoins are unchanged, because the scope is the same
  there;
- unit tests show `scope-mismatch` for a different account scope, a different observation policy,
  and a profile with no recorded scope.

**The write guard passes when** guarded hidden-state rows dispatch nothing in every arm and matcher
configuration, the controls still dispatch, and no row that must not write shows a write.

Any unsafe certification, or any write in a row that must not write, fails the repair whatever
the rejoin counts are. Lost rejoins do not fail a repair. They are reported as its cost.

## What this run does not decide

- It does not pick a shipped matcher.
- It does not authorize Stage 2 or any spend.
- The entry-start diagnostic and the holdout audit stay post hoc evidence. Their cases were
  written after the defects were seen.

## Predictions

- **Rule 1.** The four dirty-field certifications go to zero. The index arm keeps its entry-start
  gains (84 planner calls), because the other variants there leave the target form clean. On the
  form suite the guard becomes active for the first time; no lost rejoin is expected, with low
  confidence.
- **Rule 2.** The profile arm falls back to exact matching in the holdout audit: 42 decisions
  under the per-case policy and 63 under a different account scope. The frozen sandbox result
  stays at 124 calls to 20.

## Disclosure

- Both defects were found by this lane's own post hoc diagnostics.
- Another lane had drafted a scope-binding change for the profile matcher, uncommitted, before
  this file was written. Rule 2 was written without reading that draft. If the draft is adopted
  it must satisfy the rule as written, and the result record will say whose code it is.
- Earlier disclosures in this directory stand.
