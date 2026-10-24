# python-lexfrac-v1: fraction-aware w8 continuation and smaller-k w7 repair on the Python panel (board item 67, T4)

## Questions

Item 65 (python-nonregress-v1, `5d88c9976`) carried the JS breadth-safe repair onto Python.
- **w8.** It found real validation gain from item 31's anchor (935 → 929 actions, 4 better and 0 worse). It failed
  the successor rule only because the single-character fraction rose from 56.91% to 57.39%.
- **w7.** It did nothing: k = 32 freed every learned entry, and all 8 repairs hit the 120 s limit.

This stage asks two independent questions, proposed by codex as options (b) and (a) at LOG 04:23Z. The design is
claude's.
1. **w8.** Does item 51's lexicographic N-then-C objective, continued from item 65's w8 dictionary, keep the
   selection gain while bringing the fraction back down? A matched flat control isolates the objective.
2. **w7.** With a smaller neighbourhood (k = 8), does the w7 repair find headroom, or was item 65's w7 null a real
   absence of it?

## Inputs

- **Population, partition, entry methods and anchors.** Item 34's public contract and item 65's, unchanged: 36 Python
  problems, 27 fit and 9 consumed validation. The other 14, the final held-out 100 and the protected 66 stay closed.
- **Seeds.**
  - w8 arms: item 65's sealed w8 dictionary (`4d80f02d…`), on the unchanged w8 item 31 sources.
  - w7 arm: the w7 item 31 anchor, which equals R.
- **Qualification.** Sources never change, so qualification is reused by exact source hash from item 31's receipts and
  asserted for all 36.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 4 synthetic tests, including an
  exhaustive check that the M·N + C model's optimum equals the brute-force lexicographic optimum under caps.

## Arms (one core each, threads 1, warm, capped, canonical set-determined order, characters never freed)

| Arm | Seed | k | Objective and acceptance |
| --- | --- | ---: | --- |
| w8lex | item 65 w8 | 48 | Arcs cost M = 32,768 plus 1 if the word is a single character, so the solver minimises M·N + C. Accept a strict lexicographic decrease of (total canonical N, total canonical C). |
| w8flat | item 65 w8 | 48 | Accept a strict decrease of total canonical N (matched control). |
| w7k8 | w7 item 31 anchor | 8 | Accept a strict decrease of total canonical N. |

Everything else is item 65's:
- item 26's direct-HiGHS model with one nonregression cap row per fit program;
- item 34's Python bans;
- a pool of 2–64 character strings shared by at least two fit programs, with candidates from the top 3,000 and 1,000
  random strings;
- `random.Random(8)`, 120 s per repair and a 900 s LNS budget per arm.

Canonical N never exceeds the solver path's N, and is equal at optimality. Canonical C is taken from exact rescoring
only. **Validation** opens only after each arm's seal, uses item 34's coverage-safe evaluation, and keeps all 9 IDs in
every denominator.

## Decision rules (frozen in evidence.py; actions unless labelled selections)

Each arm is judged on its own width only, against **R** and against its **own-width item 31 anchor**. That anchor
remains the Python decision reference, because item 65's w8 was not a successor. The thresholds are item 31's and
item 65's, unchanged.

**Readiness against R.**
- Full coverage, every program qualified, and no illegal entry.
- At least 5% fewer validation actions.
- Strictly lower median and p90 actions.
- At least 6 programs better and at most 2 worse.
- Single-character fraction no higher.
- Package bytes at most 105%.

**Incremental against the anchor.**
- Strictly fewer actions.
- Median, p90 and fraction no worse.
- At most 2 programs worse.
- Package bytes at most 105%.

A **successor** passes both. The evidence also reports, descriptively:
- each arm against its own search start (item 65 w8 for the w8 arms);
- w8lex against w8flat, as paired counts on fit and validation.

## Predictions (None when the arms they need did not fully replay)

- **Z1:** w8lex's validation single-character fraction is below w8flat's.
- **Z2:** w8lex's validation fraction is no higher than the w8 item 31 anchor's 56.91%.
- **Z3:** w8lex is a w8 successor of item 31. I put this at roughly even odds.
- **Z4:** w7k8 accepts at least 1 move.
- **Z5:** no arm is ready against R, because of the 5% bar.

## Resources and rules

- Cores 8, 9 and 10, one process per arm, the launcher under `taskset -c 8-10`, and `OMP`, `OPENBLAS` and `MKL` threads
  set to 1.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- Cross-review by codex before launch. Nine validation programs are a small development sample, so a Python
  successor does not touch the JS M1-GAP rows. No training, publication, protected opening, deployment, human study,
  or ledger, claim or catalog write.
