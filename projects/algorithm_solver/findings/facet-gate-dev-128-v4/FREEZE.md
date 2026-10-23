# facet-gate-dev-128-v4: frozen strict development candidate for the two wrong 1b acceptances

This is gamma-team board item B (claude), from the owner direction of 2026-10-23: fix the two
wrong recognition acceptances as a separate correctness task. It succeeds
[v3](../facet-gate-dev-128-v3/FREEZE.md) (`9e50356c8`), which was superseded before it ran
([note](../facet-gate-dev-128-v3/NOTE-2026-10-23.md)). Every v3 rule, the protocol, the inputs, the
limits, the readiness rule and the confirmation gate stay as written there, except the change
below.

## The one change (Codex, gamma-team LOG 17:42Z)

**Zero profit is not zero trades.** v3 read "return zero …" and "including zero" as permission to
skip trading. So it accepted "complete exactly one transaction … return zero if all prices are
equal" for best-time-to-buy-and-sell-stock, and prices [5,4] tell −1 apart from 0. In v4:
- **No longer evidence of `zero_trade=allowed`:** bare "return / answer is / profit is / should
  return zero" and "including zero".
- **Still evidence:** explicit optionality ("or do nothing", "doing nothing is allowed", "may skip
  trading", "may choose not to trade", "zero trades are allowed"), and any upper bound
  ("at most / up to / no more than N trades").
- **`zero_trade=forbidden`:** "exactly N trades", with or without "must"; "must complete one";
  "at least one trade"; "even if it loses money".

## Files

| File | SHA-256 |
| --- | --- |
| [algsolve/facet_gate.py](../../algsolve/facet_gate.py) | `8e7ffec539cbe5fdbc1d69cfec44b55266ab376538dd42b1d791f40538f2ddde` |
| [contracts/facet_gate_dev_128_v4_strict.json](../../contracts/facet_gate_dev_128_v4_strict.json) (candidate S) | `e9b29759f90bffd1803bfefb6c279c2395ce47673d8f33a1613df786572b9f14` |
| [contracts/facet_gate_dev_128_v4_defaults.json](../../contracts/facet_gate_dev_128_v4_defaults.json) (ablation D, never eligible) | `3360ceb409f51e1dffc2c13a49eb835a112f859784a7982aaa8a7a7d1f08dc2e` |
| [declarations.py](declarations.py) | `4e71dc56ab3a10980083013d301d38a1ec1e504142082b8f85c8413a5360ba42` |
| [synthetic.py](synthetic.py) | `9ee0794d74f595f123b85f542f439dee833338e73f085e244960dec33aa2f3bd` |
| [compare_real.py](compare_real.py) (run `runs/facet-gate-real-dev-128-v4`) | `89c8ec13ff4f45cab19c5130a02dccdbe5ce88242988fa1a23bb9ea289c08fad` |
| [tests/test_facet_gate.py](../../tests/test_facet_gate.py) | `b2092f15342648b0a666469423456c62a77c01e646812b32b0a5a99ec9d3b76c` |

[manifest.json](manifest.json) lists these and the runtime copy at
`runs/facet-gate-approval-runtime-128-v4`, and the driver checks them before any inference.

## Development evidence before the freeze (developer-exposed, in-sample)

- **Offline gate checks** on the 16 specified retained development statements, against their
  expected sources: unchanged from v3. S accepts 11 of 16 and D accepts 15 of 16. None of
  those statements relied on the removed phrases.
- **[synthetic.py](synthetic.py):** 45 requests and 70 decisions ([synthetic.json](synthetic.json)),
  including all five Codex counterexamples and a zero-profit case.
  - S: 0 mismatches, 0 wrong acceptances, 18 accepted.
  - D: 0 mismatches, 2 wrong acceptances by design, 23 accepted.
- **Checks:** 18 unit tests in [tests/test_facet_gate.py](../../tests/test_facet_gate.py) pass with
  the existing gate tests (43 in total). The judge and lane checks also pass (37).

## Predictions (unchanged from v3)

- **F1:** the control reproduces its historical dispositions: 7 correct, 0 wrong, no drift.
- **F2:** S makes 0 wrong acceptances and keeps exactly 4 of the 7 control-correct answers. It
  loses stock-repeat, short-positive-window and best-sum-window.
- **F3:** D makes 0 wrong acceptances and keeps 6 of the 7, losing stock-repeat.
- **F4:** no gated arm answers a request the control abstains on.
- **F5:** retrieval is identical across the three arms.
- **F6:** the 8 requests without public examples stop before retrieval in all arms.

**Readiness (fail closed, unchanged).** S is ready for independent confirmation only if both
hold:
- `readiness_strict_route.passed` is true. It blocks on control drift, any S wrong, unqualified
  or infrastructure-error answer, any route over budget, any S answer beyond the control, and a
  control infrastructure error;
- the frozen synthetic suite shows 0 S mismatches and 0 S wrong acceptances.

D is never eligible. Confirmation is an owner gate: a request set authored independently by
someone other than me, reviewed, unopened and frozen before anyone sees it. Nothing here claims
promotion or 1b qualification.
