# facet-gate-dev-128-v4: results on the retained development requests

**The strict candidate S is ready for independent confirmation under its frozen rule. It is not
promoted, and 1b is not qualified.**

Frozen design: [FREEZE.md](FREEZE.md) (`919dbc603`), inheriting
[v3](../facet-gate-dev-128-v3/FREEZE.md)'s protocol. Codex reviewed and approved it (gamma-team
LOG 17:46Z) after four review rounds; v1, v2 and v3 were each superseded before running. Results
are in [results.json](results.json): per-request decisions, selected sources, gate reasons and
the hashes of the raw receipts in `runs/facet-gate-real-dev-128-v4/`, with no request text.

Run conditions:
- one launch, about 27 s wall;
- 4 CPU threads under a systemd scope (8 GiB, 400%);
- a peak sampled resident set of 4.84 GB;
- the encoder loaded in 4.2 s;
- no training, download, protected data or fresh-36 replay.

## Result

| 24 retained development requests | Correct | Wrong | Unqualified | Infrastructure errors | Abstained | Route p50 / p95 / max |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Control (unchanged route) | 7 | 0 | 0 | 0 | 17 | 0.27 / 0.59 / 0.64 s |
| **S, strict candidate** | **4** | **0** | 0 | 0 | 20 | 0.26 / 1.23 / 1.95 s |
| D, defaults ablation (never eligible) | 6 | 0 | 0 | 0 | 18 | 0.26 / 0.60 / 0.85 s |

**Predictions, all met:**
- **F1:** the control reproduces its history, with no drift.
- **F2:** S keeps exactly 4 of the 7 and loses the three predicted: stock-repeat,
  short-positive-window and best-sum-window.
- **F3:** D keeps 6 and loses stock-repeat.
- **F4:** no gated answer beyond the control.
- **F5:** retrieval is identical across the three arms; the driver asserts it.
- **F6:** all 8 requests without public examples stop before retrieval.

**Readiness.** The frozen `readiness_strict_route` passes:
- no drift;
- zero wrong, unqualified or infrastructure-error S answers;
- every route in every arm within budget;
- nothing answered beyond the control.

The synthetic condition holds too (S: 0 mismatches and 0 wrong acceptances on 70 decisions). S
is therefore *ready for independent confirmation* under the frozen rule. That is the owner gate,
not a result.

## What the gate did on real retrieval

- **Wrong siblings rejected on semantic grounds.** In three requests, retrieval selected a sibling
  that does not fit, and the gate named the contradiction:
  - two-sum-ii for an unsorted, zero-based request: ordering and indexing contradict;
  - stock II for a one-trade request: trade count contradicts;
  - a no-cooldown source for the cooldown request: cooldown contradicts.

  The control also abstained on all three, through a failed public example or low identity
  confidence. So no wrong acceptance was blocked in this cohort, because the control had none.
- **Losses.** All were predicted and are kept:
  - **stock-repeat:** it says "repeatedly", which no longer proves an unlimited count. Its
    zero-trade wording sits in an "if" clause.
  - **short-positive-window:** it never states that the array is not repeated.
  - **best-sum-window:** it never states non-circular and no deletion.

  The last two are the coverage cost of refusing to treat silence as evidence. D keeps them, but
  D accepts unreadable add-on paraphrases in the synthetic suite, so it is not a candidate.
- **The route-time tail.** S's p95 (1.23 s) and maximum (1.95 s) are higher than the control's.
  The gate itself is microseconds of regex. The tail was measured on a shared host with Reploid
  workloads running, and every route stayed inside the unchanged 2 s budget. This is not an
  exclusive-host latency claim.

## What this does and does not show

This development set contains no materially ambiguous request with an indexed answer. So it can
show only that the gate keeps a known, limited coverage on real retrieval and introduces no wrong
answer. It cannot show that the two consumed failures are fixed. That evidence exists only as
developer-authored synthetic cases, written with Codex's counterexamples, and the grammar was
written with these development statements visible.

**Confirmation needs the owner.** It needs a new request set, authored independently by someone
other than me, reviewed and kept unopened until its own freeze. It should cover:
- materially ambiguous requests in the reviewed families, such as an omitted trade count, an
  omitted duplicate policy, or exactly vs at most;
- complete requests in those families;
- requests whose best source is unreviewed.

The consumed fresh 36 stay consumed.

Not claimed: promotion, 1b qualification, phrase-grammar completeness, latency qualification, or
any change to the 1a and full-catalog gates.
