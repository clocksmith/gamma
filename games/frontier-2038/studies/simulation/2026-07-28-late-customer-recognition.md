# Late Customer recognition — isolated one-lever probe

Date: 2026-07-28  
Evidence label: preregistered fresh-seed causal one-lever simulation matrix  
Verdict: correct path-diversity direction, but not independently
promotion-eligible because faction-range and five-player entropy bounds remain
red

## Identity

- Raw local report:
  `20260728T081320017Z-unified-matrix-audit-0-8-16-ab3289f35527-m3t4-late-customer-recognition-v1-fresh-20260728-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `98dd934ff1081553ae71b1109050d23d11bb753c99a1639bb7ddbee36cc99220`
- Source commit:
  `f73286a412e8cc5b5f5f32c8108a55bbe49a4e89`
- Source dirty: `false`
- Executable: `0.8.16`
- Engine: `selected-rules` `0.10.16`
- Physical candidate: `0.5.0-rc.17-test`
- Ruleset fingerprint:
  `sha256:ab3289f3552743367e0fa43d804f6621a424fedf22185b2a084f6ee53afcb7be`
- Preregistration: `late-customer-recognition-v1`
- Root seed: `m3t4-late-customer-recognition-v1-fresh-20260728`
- Matrix matches: `11,998`
- Complete common-seed pairs: `5,964`
- LLM calls: `0`

## Candidate

Canonical Customers each score two Mandate. The isolated candidate changes one
structured lever:

> Customers one through three score two Mandate each. Customers four and five
> score one Mandate each.

Customer requirements, Capability thresholds, Deploy costs, Customer income,
Customer pieces, and Mark Zuckerberg's starting Customer are unchanged.

## Integrity

- Integrity violations: `0`
- Policy fallbacks: `0`
- Registered or diagnostic dominance cells: `0`
- Registered or diagnostic pairwise dominance cells: `0`
- Forced-no-op rate: `0.372%`
- Registered precision reached: `false`
- Maximum core confidence-sequence half-width: `0.2523`
- Test suite before execution: `107/107`
- Content and immutable-release gate before execution: green

## Targeted result

The candidate changed winner composition in the intended direction at every
supported player count:

| Players | Canonical Adoption | Candidate Adoption | Delta | Canonical path entropy | Candidate path entropy |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 42.97% | 40.57% | -2.40 pp | 0.5975 | 0.6068 |
| 4 | 43.68% | 40.95% | -2.73 pp | 0.6089 | 0.6184 |
| 5 | 47.55% | 43.46% | -4.10 pp | 0.5712 | 0.5877 |

Research rose from `30.93%→32.89%`, `30.70%→33.20%`, and
`28.64%→32.23%`. Action entropy stayed effectively identical
(`0.936/0.935/0.934`), declaration rates were unchanged, and every path
top-share bound passed.

This supports the causal diagnosis: late Customer Mandate contributes to
Adoption concentration. It does not show that Customer acquisition or Deploy
itself is too available.

## Failed registered bounds

The candidate did not satisfy the full preregistered selection rule:

| Players | Candidate faction range | Bound | Candidate path entropy | Bound |
| --- | ---: | ---: | ---: | ---: |
| 3 | 32.42 pp | ≤15 pp | 0.6068 | ≥0.60 |
| 4 | 19.13 pp | ≤15 pp | 0.6184 | ≥0.60 |
| 5 | 17.38 pp | ≤15 pp | 0.5877 | ≥0.60 |

The isolated canonical arm was already outside the faction bound
(`31.33/18.31/15.98` points). The candidate slightly widened those ranges
rather than repairing them. Mark's win share moved by `-1.25/-0.62/-1.42`
points at three, four, and five players. Demis remained the principal
unadjusted outlier.

Therefore this arm is not independently promotion-eligible and authorizes no
physical rule change.

## Interpretation and next evidence

The separately selected faction-conversion package previously kept all faction
ranges inside `15` points but exposed excessive Adoption concentration. This
one-lever probe improves that exact concentration but cannot repair the
canonical faction outliers by itself.

The only justified next simulation is an explicitly preregistered
package-interaction diagnostic combining:

1. the three independently selected faction-conversion levers; and
2. this late-Customer recognition schedule.

That interaction must use fresh common seeds and pass the enforced
configuration-by-player-count bounds. It remains diagnostic rather than causal
evidence for any individual lever. A failure rejects the combined package; a
pass still requires explicit user approval and physical testing.

## Surface audit

- Canonical rulebook and faction cards: no mechanical change.
- Semantic content graph and generated player-facing data: no mechanical
  change.
- Simulator: one structured `customerMandateSchedule` overlay.
- Browser prototype and reference aids: canonical gameplay unchanged.
- Tests: canonical two-point awards and the candidate `2/2/2/1/1` schedule are
  both covered.
- Playtest documentation: unchanged; no simulation candidate was promoted.
- Evidence: raw report archived locally; this tracked receipt records its
  identity, result, limits, and next admissible comparison.

## Validity boundary

This study is deterministic-policy evidence about score conversion. It does
not establish human strategy, negotiation quality, perceived fairness,
duration, or fun.
