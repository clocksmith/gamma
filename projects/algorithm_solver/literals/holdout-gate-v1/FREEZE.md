# holdout-gate-v1: gating fit-only repair on a held-aside fit subset (board item 75, T1/T3)

## Question

Three of the last four repair items gained on fit and lost on validation:
- **Item 72 (JS, `f6194beae`).** Capped repair from item 51 lowered fit selections by 16–22 with no fit program worse.
  Dev-val went from 8,283 to 8,286–8,290, with the median 62.5 → 63.5 and 2 programs worse.
- **Item 74 (Python, `98597484f`).** Relaxed caps lowered fit further, and validation got worse in every arm.
- **Item 73** found nothing at all.

The caps protect only the programs inside the model. A move can delete an entry that unseen programs relied on.

This stage asks whether that regression can be **detected without validation**. The 300 fit programs are split once
into 240 **search** programs, which the model sees, and 60 **gate** programs, which it never sees. A search-improving
move is accepted only if the gate subset does not get worse. The comparison is against the same search without the
gate. The design is claude's. Codex is out until 2026-10-30, and a Claude subagent reviews in its place.

## Inputs

- **Seed.** Item 51's selected flat dictionary (`75ff15af…`), with item 51's universe order: item 43's order first
  (`f53db5b5…`), then every other seed or search-pool entry sorted. The runner asserts that the seed serializes to
  itself.
- **Sources.** Item 13's. `fit-sources.json` is pinned, and `sources.json` is read only after each seal.
- **Split.** `run.split` puts in the gate the 60 fit IDs with the smallest SHA-256 of `holdout-gate-v1:<id>`; the
  other 240 form the search set. It is fixed before any run, and its ID list is pinned by SHA-256 in the contract.
  It uses no costs or texts.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed validation. This is adaptive development. The final
  held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No search on the corpus. [test_capped.py](test_capped.py) passes 8 synthetic tests:
  - capped and lexicographic exhaustive optima;
  - the split (a disjoint cover, order-independent, salt-dependent);
  - the gate rule;
  - the fixed universe order;
  - `measure_safe`;
  - the evidence invariants and the binding refusal;
  - the `-O` guard.

## Arms (one core each, threads 1, warm-started)

Shared settings:
- item 51's lexicographic M·N + C model on item 26's direct-HiGHS occurrence flow, with continuous arcs (item 26's
  `solve`, which suffices without a ratio row);
- item 51's loop;
- candidates: the top 3,000 strings plus 1,000 random strings;
- 300 s per repair and a 3,000 s LNS budget;
- characters never freed;
- LNS seed **11**, fresh relative to items 51 and 72.

**The pool, ranking, model and per-program nonregression caps use the 240 search programs only.** Legality bans cover
all 300 fit programs.

| Arm | k | Acceptance |
| --- | --- | --- |
| gate24 | 24 | A strict lexicographic decrease of the search set's canonical (N, C), **and** the gate subset's canonical (total N, total C) does not rise lexicographically (`gate_ok`). |
| free24 | 24 | The search decrease only (matched control). |
| gate40 | 40 | As gate24. |
| free40 | 40 | As free24. |

The gate subset is scored only for search-improving trials. A rejected trial is counted as `gate_rejected`. Accepted
moves therefore never raise the gate's (N, C) relative to the incumbent, and so never relative to the seed. A gated
arm whose end state breaks that is a retained failure.

## Validation, checks and costs

Validation opens after each seal, and it is never used in acceptance. The checks are those of jsratiocap-v1, adapted:
- **Contract first.**
- **Seed.** The seed's fresh replay must equal item 51's published per-program actions and aggregates, at 8,283.
- **Replay.** All 400 programs, coverage-safe.
- **Reconciliation.** These counters are reconciled with the replay and with `moves.jsonl`:
  - search N, C and objective;
  - gate (N, C) at start and end;
  - search programs better and worse;
  - moves, improving and accepted moves, gate rejections, statuses, and feasible and optimal counts.
- **Invariants.**
  - No search program may be worse than the seed.
  - A gated arm's gate (N, C) may not exceed the seed's.
- **Qualification.** Item 13's receipts are reused by exact source hash.

## Decision rules (unchanged from items 51 and 72)

**Readiness against R:**
- full coverage, qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 better and at most 25 worse;
- fraction no higher;
- package at most 105%.

**Successor of item 51:** ready, **and** against item 51:
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 25 worse;
- package at most 105%.

A **replacement** of the M1-GAP current-best row needs an explicit record-time binding. Ranking is by actions, then
package bytes, then name. Each gated arm is also reported against its free control.

## Predictions (keys G1–G6 in evidence.py, three-valued)

- **G1:** both gated arms accept at least 1 move.
- **G2:** some gated arm's dev-val actions are at most item 51's 8,283.
- **G3:** at both k, the gated arm reaches no more dev-val actions than its free control. This is the main question.
- **G4:** some free arm's dev-val actions exceed 8,283, reproducing item 72's regression on a 240-program search set.
- **G5:** some gated arm is a successor of item 51. I expect this to be false: even a perfect gate only blocks
  regressions, and item 72's gains were small.
- **G6:** full coverage, no failure.

## What it can and cannot show

- **Can show** whether a held-aside fit gate predicts and blocks the validation regression of fit-only repair. If it
  does, held-aside gating becomes a standard guard for later repair stages.
- **Cannot show** confirmation, transfer, or a material change to the M1 gap. A null here is bounded by these
  neighbourhoods and budgets.

## Resources and rules

- Cores 8–11, one process per arm, the launcher under `taskset -c 8-11`, and `OMP`, `OPENBLAS` and `MKL` threads set to
  1.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- **Disclosed after the freeze, before launch:**
  - a fit-only runner smoke (`--smoke 1`, one 1 s move per arm, output discarded);
  - one evidence stand-in, in which each arm carries item 51's dictionary.
- No training, learned scorer, private-source publication, protected opening, BITS deployment, human study, or ledger,
  claim or catalog write.
