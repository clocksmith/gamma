# alphabet96-v1: restoring item 51's four missing characters at an exactly minimal cost (board item 77, T1/T3)

## Question

The coverage audit (team REPORT, 2026-10-24) found that the current-best ladder is missing four of the 96 alphabet
characters: B, P, R and `_`. That covers item 24, which made characters optional, and items 43 and 51. Fourteen
development programs (11 fit and 3 validation) are encodable only because particular learned entries contain those
characters. Item 75's k24 arms lost three of them. Item 13, the frozen confirmation subject, has all 96 characters.

The 400/400 coverage of the current-best row is therefore specific to development. Any unseen program that uses one
of those characters outside the covering entries is unencodable.

This stage asks what coverage robustness costs:
- restore the four characters to item 51;
- drop exactly four learned entries, chosen to minimise the fit cost exactly;
- optionally repair;
- compare against item 13, the robust reference, and item 51, the fragile current best.

## Inputs

- **Seed.** Item 51's selected flat dictionary (`75ff15af…`) with item 51's universe order. The restored characters
  go right after item 43's entries. The seed must serialize to itself.
- **Sources.** Item 13's, as in items 51 and 72. `fit-sources.json` is pinned, and `sources.json` is read only after
  each seal.
- **References.** Item 13's dictionary (`e3cb3e3c…`) is replayed fresh and must reproduce 8,504 dev-val actions. Item
  51 must reproduce 8,283, and the pinned R baseline is replayed.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed validation. This is adaptive development. The final
  held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No search on the corpus. [test_capped.py](test_capped.py) passes 8 synthetic tests, among them a
  new exhaustive check of the drop step: all characters fixed, candidates the incumbent's learned entries, capacity
  reduced, no caps. It checks that the MILP optimum equals the best subset by brute force.

## Arms (one core each, threads 1)

**Step 1, in both arms: the exact drop.**
- The four characters are added, and **one** exact MILP chooses which learned entries to keep.
- Settings: item 26's occurrence-flow model and solve, with continuous arcs. All 96 characters are fixed. The
  candidates are item 51's 164 learned entries only, with no new strings. Capacity is 256 − 96 = 160, and there are
  **no** caps, since dropping entries can only lengthen programs.
- The objective is lexicographic M·N + C with M = 131,072. That exceeds the fit character total, which bounds every N
  and C, so the objective stays lexicographic without caps.
- The solve has a 1,200 s limit. Its warm start drops the last 4 learned entries in item 51's order.
- The solver's N is checked against exact canonical rescoring, with equality at optimality.

| Arm | After the drop |
| --- | --- |
| drop | Sealed as is. |
| repair | Item 51's capped LNS repair with **all 96 characters fixed** (never freed): k = 24, top 3,000 plus 1,000 random candidates, LNS seed **12**, 300 s repairs, 3,000 s. Per-program caps are the incumbent's, and acceptance needs a strict lex decrease of the canonical fit (N, C). |

## Validation, checks

Validation opens after each seal, and it is never used in acceptance. The evidence:
- **Contract first.**
- **Fresh replays.** Item 51 must give 8,283 and equal its published per-program rows. Item 13 must give 8,504.
- **Alphabet invariant.** A sealed dictionary must hold all 96 characters; otherwise the arm is a retained failure.
- **Coverage.** All 400 programs must decode; with all 96 characters this is guaranteed and asserted.
- **Reconciliation.** Counters are reconciled with the replay and with `drop.json` / `moves.jsonl`. The drop arm must
  equal its drop result, and the repair arm's start must equal its drop result.
- **Qualification.** Item 13's receipts are reused by exact source hash.

## Decision rules (thresholds unchanged from items 51 and 72)

- **Readiness against R** is unchanged:
  - full coverage, qualified, clean and 400 decoded;
  - at least 5% fewer actions;
  - median and p90 strictly lower;
  - at least 60 better and at most 25 worse;
  - fraction no higher;
  - package at most 105%.
- **Robust-ready** means ready **and** incremental against item 13, which also holds all 96 characters:
  - strictly fewer actions;
  - median, p90 and fraction no worse;
  - at most 25 worse;
  - package at most 105%.
  A robust-ready arm is the best **coverage-robust** development candidate. It is recorded as an annotation on the
  M1-GAP rows. Neither M1 nor the row definitions change; changing them is the owner's decision.
- **A successor of item 51** (ready plus incremental against item 51) is also evaluated, and it needs an explicit
  record-time binding to replace the current-best row. I do not expect one, since restoring characters costs actions.

## Predictions (keys F1–F5 in evidence.py)

- **F1:** the exact drop solves to optimality in both arms.
- **F2:** the drop arm's dev-val actions are at most item 51's + 20, that is at most 8,303.
- **F3:** some arm is robust-ready, beating item 13's 8,504 under every incremental check.
- **F4:** the repair arm reaches fewer dev-val actions than the drop arm.
- **F5:** both arms complete with no failure.

## Resources and rules

- Cores 8 and 9, one process per arm, the launcher under `taskset -c 8-9`, and `OMP`, `OPENBLAS` and `MKL` threads set
  to 1.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- **Disclosed after the freeze, before launch:**
  - a fit-only smoke (`--smoke 1`);
  - one evidence stand-in, recorded in the README. It cannot carry item 51's dictionary, which lacks the characters,
    so it carries the smoke's sealed dictionaries.
- **Cross-review.** A fresh-context Claude subagent stands in for codex, who is out until 2026-10-30.
- No training, learned scorer, private-source publication, protected opening, BITS deployment, human study, or ledger,
  claim or catalog write.
