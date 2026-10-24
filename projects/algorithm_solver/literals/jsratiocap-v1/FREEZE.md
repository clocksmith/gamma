# jsratiocap-v1: item 69's binary-arc ratio-versus-lex repair, carried onto the JS current best (board item 72, T3)

## Question

On Python, item 69 (`397c5bbde`, amendment `ca57568bd`) gave the first exact repairs that lowered validation actions
with 0 programs worse **and** kept the single-character fraction at or below the anchor's. It had three ingredients:
- binary arcs in every arm;
- the lexicographic M·N + C objective;
- at w7, an aggregate fit-ratio row N_inc·C_new ≤ C_inc·N_new, also enforced on the canonical trial.

The JS current best, item 51 flat (`5389ce575`), has 8,283 dev-val actions and a 49.505% fraction. Its repair used
continuous arcs, and its lexicographic arm made no difference (both arms reached the same dictionary). This stage asks
whether item 69's corrected matched comparison, carried onto item 51, finds a JS gain that is safe for the fraction.
Codex proposed this transfer (LOG 05:34Z); the design is claude's.

## Inputs

- **Seed.** Item 51's selected flat dictionary (`75ff15af…`): 256 entries with the 92 characters kept.
- **Sources.** Its fixed sources, which are item 13's. `fit-sources.json` is pinned, and `sources.json` is read only
  after each seal.
- **Universe order.** Item 51's own fixed universe: item 43's dictionary order (`f53db5b5…`) followed by the sorted
  non-seed pool. The runner asserts that item 51's dictionary serializes to itself in that order. Every trial in every
  arm is serialized in it.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed-validation programs. This is adaptive development.
  The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No search on the corpus. [test_capped.py](test_capped.py) passes 8 synthetic tests, among them:
  - exhaustive optima with continuous and binary arcs, and with the ratio row;
  - item 69's fractional-mixture and shorter-canonical regressions;
  - the fixed universe order;
  - `measure_safe`;
  - the evidence invariants and the binding refusal;
  - the `-O` guard.
- **Planned after the freeze, before launch, both disclosed in the README.**
  - A fit-only runner smoke of each arm with `--smoke 1`: one move with a 1 s repair limit and no validation read. Its
    output is discarded and changes nothing.
  - One evidence stand-in: each arm carries item 51's unchanged dictionary, plus a one-line synthetic `moves.jsonl`.
    It re-measures existing results only.

## Arms (one core each, threads 1, warm-started, capped, every variable integral)

[capped.py](capped.py) is byte-identical to python-ratiocap-v1's. Every arm calls `solve(..., integral_arcs=True)`.
Every arm uses the lexicographic model:
- each arc costs M = 32,768, plus 1 if its word is a single character;
- acceptance needs a strict lexicographic decrease of (total canonical N, total canonical C);
- the per-program nonregression caps apply;
- only learned entries are freed.

| Arm | k | Additional constraint |
| --- | --- | --- |
| k40ratio | 40 | The aggregate fit-ratio row on the model, with N_inc and C_inc the incumbent's canonical fit totals; the same predicate on the canonical trial (`trial_check`, unchanged from item 69). |
| k40lex | 40 | None (matched control). |
| k24ratio | 24 | The ratio row, as above. |
| k24lex | 24 | None (matched control). |

- **k = 40** is item 51's.
- **k = 24** is a smaller neighbourhood. Binary arcs make each repair harder: item 69's w8ratio solved 4 of 10
  repairs to optimality. Item 51's continuous-arc k = 40 solved 16 of 17.

**Shared settings.** These are item 51's, unchanged:
- the top 3,000 shared fit strings of length 2–64 plus 1,000 random pool strings;
- 300 s per repair and a 3,000 s LNS budget.

The only changes are the LNS seed, now **9** (item 51 used 8), and the binary arcs. The seed drives both
`random.Random` and the HiGHS `random_seed`, so neighbourhoods are fresh rather than a replay of item 51's.

**Canonical enforcement.** As in item 69:
- canonical N must never exceed the solver path's N;
- equality is required only at optimality and when the canonical trial meets the ratio;
- a lex-improving trial that breaks the ratio canonically is rejected and counted as `ratio_rejected`.

## Validation and coverage

Validation opens after each seal, and it is never used in acceptance.
- An unencodable validation row is a retained failure (`measure_safe`) and fails readiness.
- Full 400-program coverage is a measured gate.

## Checks (evidence.py)

- **Contract first.** Code, runtime, the HiGHS extension, the parent contract and the assertions guard. Item 51's
  evidence is pinned by SHA-256 (`c287fe48…`).
- **Seed reproduction.** The seed's fresh replay must reproduce 8,283 actions and equal item 51's published
  per-program actions and aggregates.
- **Replay.** All 400 programs, coverage-safe, re-read from each sealed dictionary.
- **Reconciliation.** Every counter is reconciled with the replay and with `moves.jsonl`: N, C, the M·N + C objective,
  moves, accepted moves, ratio rejections, statuses, feasible and optimal counts. Every move must be warm, feasible and
  run with integral arcs.
- **Invariants.**
  - Any arm with a fit program worse than the seed is a retained failure.
  - A ratio arm whose final fit fraction exceeds the seed's (N_seed·C_final > C_seed·N_final) is a retained failure.
- **Qualification.** Item 13's receipts are reused by exact source hash for all 400 programs.

## Decision rules (thresholds unchanged from item 51)

**Readiness against the pinned R baseline:**
- full coverage, every program qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- single-character fraction no higher;
- package bytes at most 105%.

**Successor of item 51.** Ready against R, **and** against the seed (item 51 flat):
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 25 programs worse;
- package at most 105%.

A fraction-only gain at equal actions does not pass. Ranking is by actions, then package bytes, then arm name.

**Replacing the M1-GAP current-best row** additionally needs an explicit record-time binding
(`--record-time-best/--record-time-arm/--record-time-sha256`) to the current best at record time. Every successor is
checked against it before ranking. A missing or unresolvable binding leaves the replacement unresolved.

The evidence also reports each ratio arm against its matched lex control, on validation and on fit.

## Predictions (keys J1–J6 in evidence.py; three-valued, None when no needed arm fully replayed)

- **J1:** some ratio arm accepts at least 1 move.
- **J2:** some ratio arm's dev-val fraction is no higher than item 51's 49.505%.
- **J3:** some ratio arm is a successor of item 51. I expect this to be false: item 51's own repair found only 2
  accepted moves from item 43, and binary arcs make repairs harder.
- **J4:** at both k, the lex control reaches no more dev-val actions than the ratio arm. This is the cost of the
  constraint; it was false at Python w7.
- **J5:** all four arms keep full coverage, and none fails.
- **J6:** every ratio arm solves fewer than half of its repairs to optimality. This is the cost of binary arcs plus
  the ratio row; item 69's w8ratio solved 4 of 10.

## What it can and cannot show

- **Can show** whether the fraction-safe Python mechanism transfers to JS at item 51's budgets, and whether the ratio
  row costs or gains actions there.
- **Cannot show:**
  - confirmation or transfer, because this is consumed-development evidence;
  - any material change to the M1 gap: median 61.5 against 32, p95 195 against 96, fraction 49.5% against 10%;
  - that no gain exists, since a null here is bounded by these neighbourhoods, budgets and repair time limits.

## Resources and rules

- Cores 8–11, one process per arm, the launcher under `taskset -c 8-11`, and `OMP`, `OPENBLAS` and `MKL` threads set
  to 1.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- **Cross-review.** Codex is out until 2026-10-30, so a fresh-context Claude subagent reviews this freeze; the record
  will say so.
- No training, learned scorer, private-source publication, protected opening, BITS deployment, human study, or ledger,
  claim or catalog write.
