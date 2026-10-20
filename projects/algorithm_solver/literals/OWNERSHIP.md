# Ownership split and corpus handoff

Owner direction on2026-10-20: the human user takes goals1a and1b; this task
investigates3a and publishes only its scoped work.

The literals task owns `projects/algorithm_solver/literals/`,
`contracts/literal_composition_goals_v1.json`, and scoped additions to
`GOALS.md` and this component's `CATSCAN.md`. It does not own recognition code,
stored-answer selection, corpus claims, ledger mutation, or new corpus runs.
Macros2a/2b remain separate. No256one deployment is part of this change.

The handoff snapshot is ledger revision1810:

- 546 accepted implementations:274 Python and272 JavaScript;272 complete pairs.
- Private local Gamma `main` was `37690d87a4ee3c42dac8991f37900d2c07c63f6f`,
  also preserved on Suby and Mac. That private ancestry is not published here.
- Public `origin/main` before this change was
  `6a86e9ea34f1bad7349dc11a02e52282fbe722e6`.
- Rounds25/26/27 each retain64 claims. Round27 has not launched.
- Round25 exited1 at its reserved96MiB evidence budget after2,031/2,344
  boundaries. Its summary is absent and authoritative final proof is false.
- Round26 exited0 with final-boundary verification passed and2,574 boundary
  records. Its result scoring, independent replay and admission are deferred.
- Neither native runner remains active after its recorded exit. Do not relaunch
  either uncertain operation or reuse its completed attempt directory.
- The generation3 scheduling barrier remains in qualification phase.
  No claims, admissions or barrier transitions were made for this handoff.

Private host128 continuation files are retained in the existing task directory,
not included in this public source commit:

- `corpus-to-literals-priority-handoff-v2.json`: exact hash-bound handoff.
- `corpus-campaign-v1/checkpoints/revision-1810-v16/summary.json`: accepted snapshot.
- `ledger-phase-state-v1.json`: authoritative current scheduling barrier.
- `corpus-batch-round25-runtime-v1/lifecycle-attempt-001/runner-exit.json`.
- `round26-priority-pause-handoff-v2/handoff.json`.
- `coordinator-nested-module-closure-independent-review-v2/handoff.json`:
  reviewed intakeV5 and plan-builderV3, not a bound live intake plan.
- `corpus-batch-round27-runtime-v1/preliminary-cpu-successor-v2/handoff.json`:
  prepared futureCPU8 runtime, no execution authority.
- `corpus-675-qualification-runtime-preparation-v1/handoff.json`:
  source-only repair preparation, no fresh claims or run.
- `public-comparison-1125-host-replay-source-v3/handoff.json`:
  unreviewed/unbound saved-evidence replay source, not executed.

Safe first steps on128 are read-only: verify `hostname`, `whoami`,
`git -C /home/x/deco/gamma status --short`, and inspect the handoff plus both
terminal receipts. Confirm the ledger and barrier still match before any action.
Round25 needs an independently reviewed recovery/closure plan preserving the
partial evidence. Round26 needs closed-evidence assembly and independent replay
before any intake. Neither a forced barrier transition nor a new qualification
launch is an authorized substitute for those checks.

The retained corpus push cadence starts at684 accepted implementations, then
every additional200 and the final remainder. The user separately authorized this
3a goal/pilot commit immediately. Public publication excludes private audit
ancestry, checkpoints, run archives, protected cases and unrelated changes.
