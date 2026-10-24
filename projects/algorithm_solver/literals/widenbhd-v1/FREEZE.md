# widenbhd-v1: larger nonregression neighbourhoods from the current best (board item 55)

## Question

Item 48 (tailcap-v1, `4a4fba9a9`) ran from item 43, the current best, with item 43's capped direct-HiGHS repair:
k = 40 learned entries freed per move and 300 s per repair. Only 2 of about 15 repairs improved anything (−5 fit
selections, −2 dev-val actions), so that neighbourhood looks nearly exhausted under the nonregression caps.

This stage asks whether **larger neighbourhoods**, freeing more entries per move with longer repairs, unlock further
breadth-safe gains from item 43.

## Inputs

- **Seed.** Item 43's nonregress dictionary (`f53db5b5…`): 256 entries, 92 characters, order preserved as in item 43.
- **Sources.** Item 13's. `fit-sources.json` is pinned, and `sources.json` is read only after the seal.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed validation. This is adaptive development.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No corpus search. [test_capped.py](test_capped.py) passes 8 synthetic tests; the model is
  unchanged from item 48.

## Arms (one core each, threads 1, warm-started, capped, flat N objective)

Both arms run item 48's flat arm unchanged, apart from two per-arm overrides:

| Arm | Learned entries freed per move (k) | Seconds per repair |
| --- | ---: | ---: |
| k80 | 80 | 600 |
| k120 | 120 | 600 |

Everything else is shared:
- the top 3,000 shared fit strings of length 2–64 plus 1,000 random pool strings, and `random.Random(8)`;
- a 3,000 s LNS budget per arm;
- item 26's direct-HiGHS model with one nonregression cap row per fit program;
- a warm start from the fully checked incumbent;
- acceptance on a strict decrease of exact rescored total fit selections, with no program worse (asserted).

Item 48's recorded flat arm (k = 40, 300 s, `4a4fba9a9`) is the **narrow reference**. It is reported descriptively; it
is a separate run, not a matched arm of this freeze. The two arms here are matched to each other.

**Validation** opens after the seal: the unchanged sources under the sealed dictionary, with no refit. An unencodable
row is a retained failure.

## Checks, qualification and costs

These are as in item 48 after its amendment 1.
- The contract is verified first, and the seed must reproduce 8,285.
- All 400 programs are replayed, coverage-safe, and every counter is reconciled with `moves.jsonl`.
- An arm that breaks the nonregression invariant is rejected.
- Replacement needs an **explicit record-time binding**, and every successor is checked against it before ranking.
- Qualification reuses item 13's receipts by exact source hash.
- In addition, k80 is compared with k120 as paired counts.

## Predictions

- **K1:** at least one arm accepts at least 3 moves.
- **K2:** k120 has more time-limited repairs than k80.
- **K3:** at least one arm lowers fit selections by more than item 48's 5.
- **K4:** at least one arm is a successor of item 43. I put this at low odds: item 48 shows how little room
  is left.
- **K5:** both arms end with 0 fit programs worse and at most 5 dev-val programs worse than the seed.
- **K6:** both arms keep full coverage, and neither fails.

## Decision rules (frozen in evidence.py; standing rules)

**Readiness** against R:
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

Replacing the M1-GAP row additionally needs the explicit record-time binding, which may name item 51's result if
item 51 records first. A successor only motivates an owner-approved confirmation, and M1 is unchanged.

## Resources and rules

- Cores 10 and 11, the launcher under `taskset -c 10-11`.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Repairs of 600 s within a 3,000 s budget
  can overrun the budget by one repair, which the cap covers.
- Optimized Python is refused. A killed arm is a retained failure, with no restarts.
- Cross-review by codex before launch. No training, publication, protected opening, deployment, human study, or
  ledger, claim or catalog write.
