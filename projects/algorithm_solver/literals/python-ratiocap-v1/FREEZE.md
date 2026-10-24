# python-ratiocap-v1: an aggregate fit-fraction constraint for the Python repair (board item 69, T4)

## Question

Items 65 and 67 showed that on Python, breadth-safe exact repair lowers validation actions with 0 programs worse:
- w8: 935 → 927 actions (item 67);
- w7: 1,420 → 1,402, with all 9 programs better (item 67).

Every arm failed the successor rule only on the single-character fraction, which rose because the removed selections
were mostly multi-character. Item 67's lexicographic C objective cut the drift but did not reverse it.

This stage adds an explicit **fraction constraint** and asks whether actions can still fall while the aggregate fit
fraction does not rise.

Codex corrected my earlier suggestion of per-program C caps (LOG 04:49Z): C_new ≤ C_old beside N_new ≤ N_old does not
imply C_new/N_new ≤ C_old/N_old. The constraint here is the cross-multiplied one, at aggregate fit scope.

## Inputs

- **Population, partition, entries, bans, evaluation and qualification.** As in items 65 and 67, unchanged:
  36 Python problems, 27 fit and 9 consumed validation. Qualification is reused by exact source hash from item 31's
  receipts; sources never change.
- **Seeds.** **Every arm starts from its own-width item 31 anchor**: w8 is scope_joint at 935 actions, and w7 is R at
  1,420. Items 65 and 67 are descriptive only.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 5 synthetic tests. One of them
  is an exhaustive check that the model's optimum with the ratio row equals the brute-force optimum over every
  dictionary and every path combination, under per-program N caps and the aggregate ratio constraint. One disclosed
  seed stand-in may exercise evidence.py and would be recorded in an amendment.

## Arms (one core each, threads 1, warm, per-program N caps, canonical set-determined order, characters never freed)

All four arms use item 67's lexicographic model:
- each arc costs M = 32,768, plus 1 if its word is a single character;
- acceptance needs a strict lexicographic decrease of (total canonical N, total canonical C).

| Arm | Width / k | Additional constraint |
| --- | --- | --- |
| w8ratio | 8 / 48 | The aggregate ratio row (below), enforced on the solver path and on the canonical trial. |
| w8lex | 8 / 48 | None (matched control). |
| w7ratio | 7 / 8 | The aggregate ratio row. |
| w7lex | 7 / 8 | None (matched control). |

**The ratio row.** N_inc and C_inc are the current incumbent's canonical total fit selections and single-character
selections. The model gets one row:

`sum over arcs of (N_inc · [single character] − C_inc) ≤ 0`

This is exactly N_inc · C_path ≤ C_inc · N_path for the solver's path.

**Canonical enforcement.** Canonical decoding breaks ties by smaller ID, not by C, so a canonical trial's C can exceed
the path's. Acceptance therefore also requires N_inc · C_canon ≤ C_inc · N_canon. A solver-feasible, lex-improving
trial that fails this is rejected and counted as `ratio_rejected`. That rejection is not evidence that no feasible
canonical dictionary exists.

Each accepted move is thus canonically fraction-nonincreasing at aggregate fit scope, so a ratio arm's final fit
fraction is at most the anchor's. evidence.py rejects any ratio arm whose end state breaks this.

**Shared settings.** Item 65's settings: item 34's Python bans, a pool of 2–64 character strings shared by at least
two fit programs, candidates from the top 3,000 and 1,000 random strings, `random.Random(8)`, 120 s per repair and a
900 s LNS budget per arm. **Validation** opens only after each seal, and it is never used in acceptance.

## Decision rules (frozen in evidence.py; actions unless labelled selections; thresholds unchanged)

**Readiness against own-width R** (item 31's rule).
- Full coverage, every program qualified, and no illegal entry.
- At least 5% fewer validation actions.
- Strictly lower median and p90 actions.
- At least 6 programs better and at most 2 worse.
- Single-character fraction no higher.
- Package bytes at most 105%.

**Incremental against the own-width item 31 anchor.**
- Strictly fewer actions.
- Median, p90 and fraction no worse.
- At most 2 programs worse.
- Package bytes at most 105%.

A **successor** needs both. The 5% readiness bar is part of every successor requirement; meeting the fraction
condition alone is not enough. Each ratio arm is also reported against its matched lexicographic control.

## Predictions (three-valued; None when the arms they need did not fully replay)

- **R1:** some ratio arm accepts at least 1 move.
- **R2:** some ratio arm's validation fraction is no higher than its anchor's. The fit fraction is constrained;
  validation is not.
- **R3:** some ratio arm passes every incremental check against its anchor.
- **R4:** at both widths, the matched lexicographic control reaches no more validation actions than the ratio arm.
  This is the cost of the constraint.
- **R5:** no arm is ready against R.

## Resources and rules

- Cores 8–11, one process per arm, the launcher under `taskset -c 8-11`, and `OMP`, `OPENBLAS` and `MKL` threads set
  to 1.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- Cross-review by codex before launch. Nine validation programs are a small development sample, so a Python
  successor does not touch the JS M1-GAP rows. No training, publication, protected opening, deployment, human study,
  or ledger, claim or catalog write.
