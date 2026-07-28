# Selected faction plus late-Customer package

Date: 2026-07-28  
Evidence label: preregistered fresh-seed package-interaction simulation matrix  
Verdict: authoritative four-player package passes; full supported package is
not yet eligible because five-player winning-path entropy remains below its
registered floor

## Identity

- Raw local report:
  `20260728T083053827Z-unified-matrix-audit-0-8-16-ab3289f35527-m3t4-selected-faction-late-customer-package-v1-fresh-20260728-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `6b79e7f88220c962d5fdb3a00b89ee1e3489870a777ba12f5de21a07d7a7393d`
- Source commit:
  `39e0afa645742091703b5fbab5068995f02165c9`
- Source dirty: `false`
- Executable: `0.8.16`
- Engine: `selected-rules` `0.10.16`
- Physical candidate: `0.5.0-rc.17-test`
- Ruleset fingerprint:
  `sha256:ab3289f3552743367e0fa43d804f6621a424fedf22185b2a084f6ee53afcb7be`
- Preregistration: `selected-faction-late-customer-package-v1`
- Root seed:
  `m3t4-selected-faction-late-customer-package-v1-fresh-20260728`
- Matrix matches: `11,998`
- Complete common-seed pairs: `5,964`
- LLM calls: `0`

## Package

The interaction arm combines four separately identified conversions:

1. Demis scores one Mandate at Capability 9 and 12, with the final point
   restored at Capability 12 in a five-player game when four rivals validate.
2. Elon scores one Mandate when Industrial Velocity actually discounts a
   completed Facility.
3. Jensen's New Architecture produces one Compute per accepted rival license,
   maximum three, with no base production.
4. Customers one through three score two Mandate; Customers four and five
   score one.

This is package-interaction evidence, not a new causal estimate for any member.

## Integrity

- Integrity violations: `0`
- Policy fallbacks: `0`
- Registered or diagnostic dominance cells: `0`
- Registered or diagnostic pairwise dominance cells: `0`
- Registered precision reached: `false`
- Maximum core confidence-sequence half-width: `0.2523`
- Source clean: `true`

## Enforced result

Exactly one candidate outcome check failed:

| Players | Faction range | Action entropy | Opening entropy | Path entropy | Path top share |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 12.61 pp | 0.9372 | 0.7626 | 0.6108 | 43.80% |
| 4 | 12.60 pp | 0.9380 | 0.7448 | 0.6151 | 43.85% |
| 5 | 12.84 pp | 0.9343 | 0.7539 | **0.5731** | 47.04% |

The path-entropy floor is `0.60`; all other declared bounds passed. The package
therefore receives `outside_provisional_bounds`, not a balance pass.

## Faction result

Four-player win shares form a compact band:

| Faction | Win share | Mean Mandate | Mean rank |
| --- | ---: | ---: | ---: |
| Dario | 31.59% | 18.40 | 2.27 |
| Elon | 26.72% | 17.70 | 2.46 |
| Jensen | 25.23% | 17.48 | 2.53 |
| Mark | 24.18% | 17.25 | 2.56 |
| Demis | 22.94% | 17.77 | 2.44 |
| Sam | 18.98% | 16.54 | 2.75 |

At three players the range is `12.61` points; at five it is `12.84`.
Every faction remains viable at every supported count. Mark remains
competitive after diminishing late Customer recognition, and the Demis, Elon,
and Jensen corrections do not reverse at a supported count.

## Remaining path concentration

| Players | Adoption | Research | Research–Adoption hybrid | Legitimacy | Infrastructure |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 43.80% | 29.96% | 10.54% | 5.37% | 2.39% |
| 4 | 43.85% | 29.55% | 13.99% | 4.28% | 0.81% |
| 5 | 47.04% | 29.12% | 14.72% | 2.96% | 0.37% |

At five players, those first three labels account for `90.88%` of winner
credit. The late-Customer schedule reduces Adoption pressure, but the remaining
failure is not another late-Customer pricing question. Infrastructure and
Legitimacy almost never appear as primary winner labels, especially as the
table grows.

The current classifier assigns exactly one lane unless two computed lane scores
tie exactly. It may therefore hide mixed infrastructure or legitimacy support
inside Research and Adoption. Before adding Facility or Trust scoring, the
next evidence must test whether the failure is a classifier artifact or a real
absence of alternative winning play.

## Decision

1. Do not promote the four-lever package yet.
2. Do not change Customer scoring again.
3. Do not add automatic Facility scoring, alter Trust, or tune a global system
   from this report.
4. Preregister a classifier-validity diagnostic that replays the existing
   complete winner states under stable fractional lane attribution.
5. If the diagnostic still shows no infrastructure or legitimacy contribution,
   test policy validity before proposing one new scoring lever.

## Surface audit

- Physical rulebook, cards, semantic graph, generated content, prototype, and
  reference aids: unchanged.
- Simulator: no new mechanic in this step; it executed the preregistered
  four-lever overlay.
- Tests: individual lever semantics remained covered by `107/107` tests from
  the executable release.
- Evidence: raw report archived locally; this tracked receipt records the full
  enforced result and its validity boundary.
- Playtest documentation: unchanged because no physical candidate was
  promoted.

## Validity boundary

The package is statistically healthy at four players and preserves supported
faction viability, but it has not satisfied the declared full-product balance
contract. Simulation cannot establish human negotiation, perceived strategic
freedom, timing, or fun.
