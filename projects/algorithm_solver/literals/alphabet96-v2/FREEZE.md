# alphabet96-v2: repair from item 77's coverage-robust dictionary, with corrected solver checks (board item 78, T1/T3)

## Question

Item 77 (`bfd91e2a1`) restored B, P, R and `_` to item 51 by an exact drop. The result, dev-val 8,337, beats item 13
(8,504) on actions, median, p90 and package. It is **not robust-ready**, because its single-character fraction is
49.970% against item 13's 49.893%. Item 77's repair arm, the planned way to recover cost, was a retained failure. Item
26's inherited `solve()` checks the objective with an absolute 1e-6 tolerance, which float noise exceeds at item 77's
M = 131,072 scale.

This stage asks two things:
- What does the capped repair recover from item 77's dictionary, with the check corrected?
- Does the restored characters' **dictionary-ID placement** move the canonical fraction? Item 51 found that ID order
  alone changes canonical C at equal N, by about 0.05 points.

This is adaptive development. Item 77's fraction result is known, and these arms were chosen after it. The design is
claude's; codex is out until 2026-10-30, and a Claude subagent reviews in its place.

## Inputs

- **Seed.** Item 77's sealed drop dictionary (`6a4972f6…`): all 96 characters plus 160 learned entries, serialized in
  item 77's universe order (item 43's order, then the restored characters, then the sorted pool). The runner asserts
  that the seed serializes to itself in that order.
- **Sources.** Item 13's. `fit-sources.json` is pinned, and `sources.json` is read only after each seal.
- **References.**
  - Item 77's drop evidence (`alphabet96-v1/evidence/results.json`, pinned). Its replay must equal it, at 8,337.
  - Item 51's dictionary (`75ff15af…`), which must replay to its published 8,283.
  - Item 13's dictionary, which must give 8,504.
  - The pinned R baseline.
- **Data.** 300 fit and 100 consumed validation programs. The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No search on the corpus. [test_capped.py](test_capped.py) passes 9 synthetic tests, among them:
  - the corrected objective tolerance (`capped.close`), tested on item 77's actual failure scale;
  - exhaustive optima at a large lexicographic scale, with continuous and binary arcs.

## Arms (one core each, threads 1)

**The corrected solve.** `capped.solve` is item 26's model and procedure, unchanged in substance:
- activations are integer and arcs continuous;
- rows are checked on the returned point with item 26's 1e-6, valid for its ±1 rows;
- the objective and the warm-start bound use `close()`, which is relative 1e-9 with a floor of 1e-6.

M = 32,768, which exceeds any capped total N; that is item 51's value.

| Arm | Universe order (dictionary IDs) | Search |
| --- | --- | --- |
| lastdrop | the four restored characters moved to the **end** of the universe | none: item 77's entry set, re-serialized |
| repair43 | item 77's: restored characters right after item 43's entries | item 51's capped LNS |
| repairlast | restored characters at the end | item 51's capped LNS |

The **capped LNS** is item 51's loop:
- k = 24;
- the top 3,000 plus 1,000 random candidates;
- LNS seed **13**;
- 300 s per repair and a 3,000 s budget;
- per-program caps set to the incumbent's;
- acceptance on a strict decrease of canonical fit (N, C);
- **all 96 characters fixed**.

Re-serialization never changes per-program N, and the runner asserts this. It can change canonical C.

## Checks

- **Contract first.**
- **Fresh replays** of item 77's drop, item 51 and item 13, which must equal their published rows.
- **Alphabet.** Every sealed dictionary holds all 96 characters; otherwise the arm is a retained failure.
- **Coverage.** 400/400, guaranteed and asserted.
- **Reconciliation.** Counters are reconciled with the replay and `moves.jsonl`. The lastdrop arm has no moves, and
  its N equals the seed's.
- **Qualification.** Item 13's receipts are reused by exact source hash.

## Decision rules (thresholds unchanged)

- **Readiness against R**, as in items 51, 72 and 77.
- **Robust-ready** means ready **and** incremental against item 13, the 96-character frozen subject:
  - strictly fewer actions;
  - median, p90 and fraction no worse;
  - at most 25 worse;
  - package at most 105%.

  A robust-ready arm is recorded as the best coverage-robust development candidate, annotated on M1-GAP. Neither M1
  nor the row definitions change.
- **Successor of item 51:** ready, incremental against item 51, and an explicit record-time binding. Ranking is by
  actions, then package, then name.

## Predictions (keys H1–H5 in evidence.py)

- **H1:** lastdrop's dev-val fraction is below item 77's 49.970%. Moving the characters to higher IDs makes canonical
  ties prefer learned entries.
- **H2:** some arm is robust-ready.
- **H3:** both repair arms accept at least 1 move.
- **H4:** some repair arm reaches fewer dev-val actions than its start of 8,337.
- **H5:** all three arms complete with no failure.

## Resources and rules

- Cores 8, 9 and 10, one process per arm, the launcher under `taskset -c 8-10`, and `OMP`, `OPENBLAS` and `MKL`
  threads set to 1.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- **Disclosed after the freeze, before launch:**
  - a fit-only smoke (`--smoke 1`);
  - one evidence stand-in carrying the seed in every arm.
- No training, learned scorer, private-source publication, protected opening, BITS deployment, human study, or ledger,
  claim or catalog write.
