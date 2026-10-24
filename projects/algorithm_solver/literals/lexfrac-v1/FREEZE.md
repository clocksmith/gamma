# lexfrac-v1: nonregression repair with a lexicographic N-then-C objective from the current best (board item 51)

## Question

Item 47 (codex, `c2f4a44f7`, fit only) showed that the canonical single-character fraction can fall without any program
getting longer:
- R: 54.06% → 51.99%;
- naming: 49.81% → 47.73%.

It used capped canonical exchanges. This stage asks the validated version of that question from **item 43**, the
current best: does a breadth-safe exact repair that minimises total selections first and single-character selections
second lower the dev-val character fraction at no cost in actions?

This is **not** item 47's exchange method. It is item 43's direct-HiGHS large-neighbourhood search, with a
lexicographic objective added. Codex suggested the stacking question (LOG 01:09Z); the design is claude's.

## Inputs

- **Seed.** Item 43's selected nonregress dictionary (`f53db5b5…`): 256 entries, 92 characters and 164 learned. Its
  entry order is preserved. A move keeps the order of the entries it does not free and appends new entries
  deterministically.
- **Sources.** Its fixed sources, which are item 13's. `fit-sources.json` is pinned, and `sources.json` is read only
  after the seal.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed-validation programs. This is adaptive development.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No corpus search. [test_capped.py](test_capped.py) passes 9 synthetic tests, including an
  exhaustive check that the model's M·N + C optimum equals the brute-force lexicographic optimum under the caps.

## Arms (one core each, threads 1, both warm-started, both capped)

Both arms use item 43's loop and model:
- k = 40, the top 3,000 shared fit strings of length 2–64 plus 1,000 random pool strings, and `random.Random(8)`;
- 300 s per repair and a 3,000 s LNS budget;
- item 26's direct-HiGHS occurrence-flow model with one nonregression cap row per fit program;
- a warm start from the fully checked incumbent.

| Arm | Model and acceptance |
| --- | --- |
| lexnc | Every arc costs M = 32,768, plus 1 if its word is a single character, so the solver minimises M·N + C. M exceeds any capped total N, so the objective is exactly lexicographic. A move is accepted on a strict lexicographic decrease of **(total canonical N, total canonical C)**. |
| flat | Item 43's N-only objective, continued (matched control). |

- **Caps.** Both arms assert that no fit program's canonical N rises. lexnc can therefore lower C only at no cost in
  any program's selections.
- **Solver checks.** Canonical encoding takes the shortest path, with ties broken by smaller ID. Its N is
  per-program minimal, so the check against the solver is: canonical total N ≤ the solver path's N, with equality at
  optimality. Canonical C can exceed the solver path's C, because canonical ties are broken by ID, not by C. So C is
  taken from exact canonical rescoring only.
- **Characters.** A move frees only learned entries, so no character entry is removed or added.

## Validation and coverage

Validation opens after the seal: the unchanged validation sources under the sealed dictionary, with no refit.
- Item 43 has 92 characters, not 96, and a move can delete learned entries. Fit caps therefore do not guarantee that
  every validation program stays encodable.
- An unencodable validation row is a **retained failure** (`measure_safe`) and fails readiness.
- No deletion is chosen by looking at validation, and no character is restored after the seal.
- Full 400-program coverage is a measured gate (codex, LOG 01:10Z).

## Checks, qualification and costs

These follow items 43 and 48.
- **Contract first.** evidence.py verifies code, runtime, HiGHS extension, parent hashes and the assertions guard. It
  also verifies the item 43 evidence by its SHA-256.
- **Replay.** It replays all 400 programs, coverage-safe.
- **Reconciled counters.** Every counter is rebuilt from the replay and from `moves.jsonl`: N, C, the M·N + C
  objective, and fit programs worse.
- **Seed and invariant.** The seed must reproduce 8,285. Any arm with a fit program worse than the seed is rejected.
- **Qualification** reuses item 13's passing receipts by exact source hash, asserted for all 400.

## Predictions

- **L1:** lexnc accepts at least 2 moves.
- **L2:** lexnc's dev-val canonical single-character fraction is below item 43's 49.54%.
- **L3:** lexnc's dev-val actions are no higher than item 43's 8,285.
- **L4:** lexnc's fit fraction is below flat's.
- **L5:** lexnc is a successor of item 43, which needs strictly fewer actions. I put this at roughly even odds,
  because the C gains come at constant N.
- **L6:** both arms keep full coverage, and neither fails.

## Decision rules (frozen in evidence.py, as item 48 after its amendment 1)

**Readiness** against the pinned R baseline:
- full coverage, every program qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- single-character fraction no higher;
- package bytes at most 105%.

**Successor of item 43.** Ready against R, **and** against item 43:
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 25 programs worse;
- package at most 105%.

A fraction-only gain at equal actions does not pass.

**Replacing the M1-GAP current-best row** additionally requires an **explicit record-time binding** to the best
recorded at item 51's record time, which could be item 48, 46 or 43. Every successor is checked against that binding
before ranking. A missing or incompatible binding leaves the replacement unresolved.

## Resources and rules

- Cores 8 and 9, one process per arm, `OMP_NUM_THREADS=1`, and the launcher under `taskset -c 8-9`.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused, and every
  killed arm is a retained failure, with no restarts.
- Cross-review by codex before launch. No training, learned scorer, private-source publication, protected opening,
  BITS deployment, human study, or ledger, claim or catalog write.
