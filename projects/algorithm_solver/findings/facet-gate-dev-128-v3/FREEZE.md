# facet-gate-dev-128-v3: frozen strict development candidate for the two wrong 1b acceptances

## Why a v3

This is gamma-team board item B (claude), from the owner direction of 2026-10-23: fix the two
wrong recognition acceptances as a separate correctness task.

This successor replaces [v2](../facet-gate-dev-128-v2/FREEZE.md) (`dca349353`), which was
superseded before it ran ([note](../facet-gate-dev-128-v2/NOTE-2026-10-23.md)). Codex's v2 review
(gamma-team LOG 17:38Z) found two gate-level false acceptances in the strict arm. Both are trade
semantics:
1. **Exactly one vs at most one.** "You must complete exactly one transaction ... even if it
   loses money" was accepted for best-time-to-buy-and-sell-stock. That source allows zero
   trades, and prices [5,4] tell 0 apart from −1.
2. **"Multiple" vs unlimited.** "Multiple trades, at most three transactions" was accepted for
   stock II, because `multiple` and `repeatedly` counted as an unlimited count. Prices
   [1,2,1,2,1,2,1,2] tell three trades apart from four.

The review also asked that readiness fail closed on drift, unqualified answers, infrastructure
errors and route-budget failures, not on zero wrong answers alone.

## Changes from v2

All other v2 rules are unchanged: strict candidate S, ablation D, 19 reviewed sources,
unreviewed sources abstain, clause-scoped uncertainty, double-negation handling, and the
pre-inference manifest check.

- **Trade count and zero trades are now separate.** `transactions` is an upper bound only:
  one, two, k, unlimited, or `bounded_other` for an explicit cap of three or more. A new
  never-default facet, `zero_trade`, is either allowed ("or do nothing", "including zero",
  "may skip trading") or forbidden ("must complete exactly one", "even if it loses money").
  It is required for all six stock sources.
- **"Unlimited" now needs explicit evidence**, such as "as many as I like", "any number of",
  "unlimited" or "no limit". `repeatedly`, `multiple` and `several` no longer prove it.
- **Fail-closed readiness.** [compare_real.py](compare_real.py) computes
  `readiness_strict_route`. Each of the following blocks it:
  - control drift;
  - any S wrong, unqualified or infrastructure-error answer;
  - any route over budget, in any arm;
  - any S answer where the control abstained;
  - a control infrastructure error.

## Files

| File | SHA-256 |
| --- | --- |
| [algsolve/facet_gate.py](../../algsolve/facet_gate.py) | `9d21f6a473a29961cae859d6f34af637871464a0e538480e7dd334044fc5112e` |
| [contracts/facet_gate_dev_128_v3_strict.json](../../contracts/facet_gate_dev_128_v3_strict.json) (candidate S) | `b757e10279f33318c50e2aa1da225abccd70ef59f9c3a32921eae7d26d6326d5` |
| [contracts/facet_gate_dev_128_v3_defaults.json](../../contracts/facet_gate_dev_128_v3_defaults.json) (ablation D, never eligible) | `8f0e81511e2d386349a26f13df5cb3a108ad7441ecab11fe608d5fee644b00b3` |
| [declarations.py](declarations.py) | `a153669f799f48d0c2ddc0941f82158d6380ce4212f38c0d9f1c7b3c09b1d92c` |
| [synthetic.py](synthetic.py) | `ea7cbf5f87c68b38272423dba584d3440907c8ddf71f45c0ed25f8fe039247c2` |
| [compare_real.py](compare_real.py) | `3ab4d63a67719011119042c8001859116db4c2c1471befc72b402b190a8e2fbf` |
| [tests/test_facet_gate.py](../../tests/test_facet_gate.py) | `cbb954b7fd54289d532e4b7ca20c736afe55bb98b8de662d4864493822c36e48` |

[manifest.json](manifest.json) lists these and the runtime copy at
`runs/facet-gate-approval-runtime-128-v3`, and the driver checks them before any inference.

## Development evidence before the freeze (developer-exposed, in-sample)

**Offline gate checks** on the 16 specified retained development statements, against their
expected sources:
- **S** accepts 11 of 16. It rejects:
  - stock-once (fee and cooldown unstated);
  - stock-repeat ("repeatedly" no longer proves an unlimited count);
  - islands-area;
  - short-positive-window;
  - best-sum-window.
- **D** accepts 15 of 16. It rejects stock-repeat.

**[synthetic.py](synthetic.py):** 43 requests and 68 decisions ([synthetic.json](synthetic.json)).
- S: 0 mismatches, 0 wrong acceptances, 18 accepted.
- D: 0 mismatches, 2 wrong acceptances by design (the unreadable cooldown and circular-street
  paraphrases), 23 accepted.

The cases include all four Codex counterexamples, a "repeatedly" case and a case that omits the
zero-trade option. Some v2 complete-request texts now state the zero-trade option, since it is a
newly required facet. This is a software check, not recognition evidence.

**Checks:** 18 unit tests in [tests/test_facet_gate.py](../../tests/test_facet_gate.py) pass with
the existing required-facet, filter and requirements tests (43 in total). The judge and lane
checks also pass (37).

## Frozen run: real-route development comparison

The protocol is v2's. It runs over the retained `recognition-rebuild-dev-suby-v1` control:
- 66 sources and cached source vectors;
- 24 requests;
- the original approval catalog and unchanged thresholds;
- the encoder in place.

The three arms run in rotating order (control, S, D). Each does its own real embedding and
retrieval, with identical vectors and candidates asserted per request. Decisions are sealed
before scoring. Limits: a systemd scope at 8 GiB and 400% CPU, 4 threads, 900 s.

**Predictions:**
- **F1:** the control reproduces its historical dispositions: 7 correct, 0 wrong, no drift.
- **F2:** S makes 0 wrong acceptances. It keeps exactly 4 of the 7 control-correct answers and
  loses stock-repeat, short-positive-window and best-sum-window.
- **F3:** D makes 0 wrong acceptances and keeps 6 of the 7, losing stock-repeat.
- **F4:** neither gated arm answers a request the control abstains on.
- **F5:** retrieval is identical across the three arms for every request.
- **F6:** the 8 requests without public examples stop before retrieval in all arms.

**Readiness rule (frozen).** S is ready for independent confirmation only if both of these hold:
- `readiness_strict_route.passed` is true (see Changes from v2);
- the frozen synthetic suite shows 0 S mismatches and 0 S wrong acceptances.

Coverage is reported with no threshold, and losses are kept as results. D is never eligible. A
failure is recorded without tuning on this cohort.

## Confirmation: owner gate (not done here)

The development set has no materially ambiguous request with an indexed answer. Confirmation
needs:
- a new set authored independently, by someone other than me, then reviewed, unopened and
  frozen before anyone sees it;
- materially ambiguous and complete requests in the reviewed families;
- requests whose best source is unreviewed.

I stop there and record it on the board as waiting on the owner.

## Not claimed

- No promotion and no 1b qualification.
- No change to the 1a or full-catalog absence gates.
- No training, downloads, protected data or fresh-36 replay.
- The contracts are implementer declarations under review. They are necessary conditions, not
  semantic equivalence.
