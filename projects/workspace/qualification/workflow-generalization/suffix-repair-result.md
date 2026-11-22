# Two matcher repairs: result

Rules: [`suffix-repair-rules.md`](./suffix-repair-rules.md), committed in `9357369`.
Counts per arm: [`suffix-repair-measures.json`](./suffix-repair-measures.json).

**Both rules pass. Unsafe certifications are zero in every arm of every check, and no row that must
not write shows a write. Neither repair cost a useful rejoin. This does not pick a shipped matcher
and does not authorize Stage 2 or any spend.**

## What was run

Revision `7fcbdd9`, clean tree, no model. The sandbox reruns are from `8d733df`, which adds a
reporting counter to the sandbox harness and has the same `src/` tree (`f421d56`).

- **Form suite**, frozen inputs: index matcher; profile matcher with word routes and with numeric
  routes; hidden-state rows for each. 104 evaluation runs per configuration, Chrome 158.
- **Sandbox suite**, frozen: exact, profile, index, both options.
- **Entry-start diagnostic**, post hoc: the same four arms.
- **Holdout audit runner**, post hoc: per-case policy, one policy, and a different account scope.

## Who wrote which repair

- **Rule 1** is this lane's change, `5ab9314`, written after the rules were committed.
- **Rule 2** is another lane's change. Its first commit, `df4b950`, came from a draft that existed
  before the rules were written and was authored 18 seconds before the rules commit. Rule 2 was
  written without reading that draft. Its second commit, `321b743`, was written after the rule and
  adds the fail-closed case. This lane did not change either; the checks ran against them as
  landed, and this lane added the unit test for a changed observation policy (`02c835d`).
- `df4b950` also adds an opt-in conditional-write option to the service's write path. It is not
  part of these rules. With the option off, the write path only gains an evidence flag.

## Against the rules

**Rule 1, index matcher establishes form state itself: passes.**

- In the entry-start diagnostic the index arm certifies on the dirty-field near-miss in 0 of 4
  families. It was 4 of 4. It now refuses there with `dirty-untracked-form-field`, 16 times.
- Unsafe certifications are 0 for the index arm and the both-options arm in every check.
- Unit tests show the session asks for form state on every observation with the index option
  alone, and refuses with `form-state-unavailable`, before any candidate and with nothing
  dispatched, when the host returns none, when one writable control lacks it, and when the frame
  is not the latest observation.

**Rule 2, profile matcher bound to scope: passes.**

- In the holdout audit the profile arm certifies 0 times under the per-case policy. It was 6. It
  certifies 0 times under a different account scope. It was 9 on safe runs and 6 on negative runs.
- On the frozen sandbox suite its useful rejoins are unchanged: 124 planner calls to 20.
- Unit tests show `scope-mismatch` for a different account scope, a changed observation policy,
  and a profile with no recorded scope.

**Write guard: passes.** The 16 guarded hidden-state rows dispatch nothing for each matcher. The
16 controls, with the check removed on purpose, dispatch 112. No wrong-account, revoked-grant,
"no action" or negative row shows a write.

## The four counts, separately

"Safe" is the number of runs the suite expects to complete. Decisions are scripted planner
decisions on those runs, against exact matching on the same cases.

| Check | Arm | Safe runs | Useful rejoins | False refusals | Unsafe certifications | Under hidden state | Writes where none allowed | Decisions |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Form suite, no resume | Index | 12 | 8 | 0 | 0 | 2 | 0 | 47 vs 76 |
| | Profile, word routes | 12 | 0 | 8 | 0 | 0 | 0 | 76 vs 76 |
| | Profile, numeric routes | 12 | 0 | 8 | 0 | 0 | 0 | 76 vs 76 |
| Form suite, resume | Index | 12 | 8 | 0 | 0 | 2 | 0 | 12 vs 42 |
| | Profile, word routes | 12 | 0 | 8 | 0 | 0 | 0 | 42 vs 42 |
| | Profile, numeric routes | 12 | 0 | 8 | 0 | 0 | 0 | 42 vs 42 |
| Sandbox, frozen | Profile | 36 | 32 | 0 | 0 | 4 | 0 | 20 vs 124 |
| | Index | 36 | 0 | 32 | 0 | 0 | 0 | 124 vs 124 |
| | Both options | 36 | 0 | 32 | 0 | 0 | 0 | 124 vs 124 |
| Sandbox, entry-start | Profile | 36 | 32 | 0 | 0 | 4 | 0 | 24 vs 144 |
| | Index | 36 | 12 | 20 | 0 | 4 | 0 | 88 vs 144 |
| | Both options | 36 | 16 | 16 | 0 | 4 | 0 | 64 vs 144 |
| Holdout audit, per-case policy | Profile | 9 | 0 | 0 | 0 | 0 | 0 | 42 vs 42 |
| | Index | 9 | 0 | 0 | 0 | 0 | 0 | 42 vs 42 |
| Holdout audit, one policy | Profile | 9 | 0 | 0 | 0 | 0 | 0 | 15 vs 15 |
| | Index | 9 | 0 | 0 | 0 | 0 | 0 | 15 vs 15 |
| Holdout audit, other account scope | Profile | 9 | 0 | 0 | 0 | 0 | 0 | 63 vs 63 |
| | Index | 9 | 0 | 0 | 0 | 0 | 0 | 63 vs 63 |

- **Wrong-field fills and submissions:** 0 in every row of every check.
- **Writes beyond what exact matching dispatched on the same case:** 0 in every arm.
- **Sandbox decisions** on the frozen suite count the 32 held-out variants; its near-miss rows
  carry no decision count. The entry-start figures include the approval case.

Reading the columns:

- **Useful rejoins.** Unchanged by the repairs wherever the scope is the same. On the whole form
  suite the index arm still goes from 93 decisions to 64, and from 59 to 29 with resume.
- **False refusals.** Still large and still complementary. The index arm misses all 32 frozen
  sandbox runs the profile arm rejoins. The profile arm misses all 8 form-suite cases the index
  arm rejoins, in each pairing. The repairs were not meant to change this and did not.
- **Unsafe certifications.** Zero everywhere. Before the repairs: 4 for the index arm on the
  entry-start dirty-field case, and 6 and 15 for the profile arm in the holdout audit.
- **Under hidden state.** Certifications where nothing observable differs. The index arm proposed
  a suffix on the reordered page of 2 guarded hidden-state rows per pairing, and the write-boundary
  check refused each before dispatch. On the sandbox hidden-drift case the certified steps ran and
  review rejected the run, with the same writes as exact matching; that suite has no
  write-boundary check on that case.
- **Lost rejoins.** None on the form suite or either sandbox run. In the holdout audit 15 rejoins
  are gone, 6 under the per-case policy and 9 under a different account scope. Every one was in a
  row where the scope differed, which is what rule 2 is for.

## Still open after the repairs

- **Neither matcher covers both suites.** The false-refusal columns are the gap.
- **The index arm stops on the approval near-miss in the entry-start diagnostic**, 4 runs. It
  clicks the approval, then refuses past a field that is already filled. Both-options does the
  same.
- **The profile matcher does not request form state on a host without region deltas.** That path
  is unchanged, because rule 2 covers scope only. On such a host its dirty-field guard cannot see
  a control the host policy hides.
- **The profile matcher does not count a rejoin made in the middle of a replay.** The sandbox
  harness now counts suffix-replayed steps from the trace as well.

## Predictions

All held: the four dirty-field certifications went to zero, the index arm kept 84 planner calls
on the entry-start held-out variants, the form suite lost nothing, the profile arm fell back to
42 and 63 decisions in the holdout audit, and the frozen sandbox result stayed at 124 to 20.

## Disclosure

- The trace-based counter was added to the sandbox harness after the first sandbox rerun showed
  the certification count missed the profile matcher's mid-replay rejoins. Fixtures and matchers
  did not change, and every arm total is identical between the two reruns.
- A lost rejoin is counted from decisions: a run that took fewer planner decisions than exact
  matching before the repair and no longer does.
- The entry-start diagnostic and the holdout audit are post hoc. Their cases were written after
  the defects were seen. They are evidence that the defects existed and are now refused, not
  qualification evidence.
- Scripted planner throughout. Local pages and synthetic snapshots, not a tenant.

## Reproduce

```sh
R=projects/workspace/qualification/workflow-generalization/run.js
A=whole,suffix,whole-rc,suffix-rc
H=hidden-prerequisite,hidden-prerequisite-reordered,hidden-prerequisite-unguarded,hidden-prerequisite-reordered-unguarded
node $R --controlled --arms $A --matcher index --out NEW_DIR_1
node $R --controlled --arms $A --matcher profile --out NEW_DIR_2
node $R --controlled --arms $A --matcher profile --numeric-routes --out NEW_DIR_3
node $R --controlled --arms $A --matcher index --variants $H --out NEW_DIR_4
node $R --controlled --arms $A --matcher profile --variants $H --out NEW_DIR_5
S=projects/workspace/qualification/stage1-suffix-ablation.js
ARMS=exact-hash-v3,suffix-eligibility-v4,suffix-index-v1,suffix-index-plus-profile
node $S OUT_FROZEN.json --arms $ARMS                 # exits 1: the index arms miss the rejoin gates
node $S OUT_ENTRY.json --entry-start --arms $ARMS    # exits 1
```

The holdout audit rows use `run-audit.mjs` as described in
[`../gammatron-v4-stage01/independent-holdout-audit/README.md`](../gammatron-v4-stage01/independent-holdout-audit/README.md),
with a clean checkout of `7fcbdd9`.
