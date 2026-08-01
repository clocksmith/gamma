# AGI route coverage with existing deterministic policies

**Date:** 2026-08-01  
**Evidence label:** Simulation  
**Status:** Valid policy-coverage diagnostic; no rules change selected.

## Execution

- Registered protocol: `agi-route-coverage-v1`.
- Exact source: `b85a3fbdcfd7adfd8807d5744cdc647f8d8b78db`,
  `sourceDirty: false`; canonical ruleset fingerprint
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Four-player canonical rules, variable Mandate, negotiation enabled, batch
  projection, seven deterministic workers, 100 matches in each field.
- All four reports have zero integrity violations, policy fallbacks, and forced
  no-ops.

| Field | Core requirements | Power offers accepted | Grid-ready | Legal declaration | Declared |
| --- | ---: | ---: | ---: | ---: | ---: |
| AGI Candidate + Power Brokers, greedy | 192 | 42 | 2 | 1 | 1 |
| AGI Candidate + Power Brokers, weighted | 86 | 62 | 2 | 0 | 0 |
| All AGI Candidates, greedy | 202 | 0 | 0 | 0 | 0 |
| All AGI Candidates, weighted | 129 | 24 | 4 | 0 | 0 |

Raw-report hashes:

- `broker_field_greedy`: `3b6830ed5f1cd7b23455243c8b2ac3e59cb0b633b3cfcd17d968aa8c87309ab2`
- `broker_field_weighted`: `1dbe3145c92414f47f097948209d86497daad37835e3dcf3504467bf87be6f97`
- `claimant_field_greedy`: `b2fbbd6d0f7c17a2a05c98bac5c8e3cbb20077a2cf6d429bf1f4d6d300ac1235`
- `claimant_field_weighted`: `9f232708a32a98ef52989216bd8fc3127627d5ea8b1b29f2863bf715ab3f9a33`

The four raw reports are archived under `evidence/studies/simulation/` with
the `frontier-2038-agi-route-coverage-2026-08-01` seed prefix.

## Interpretation

The canonical engine can produce a legal AGI declaration: the greedy broker
field reached one legal window and declared once. Therefore the earlier
zero-window unified matrix does not demonstrate a declaration-rule bug or
impossibility.

Coverage is nevertheless thin. A claimant-only greedy field generated 41
external-Power needs and zero offers; adding Power Brokers created accepted
offers and the only declaration. Weighted fields reached Grid-Ready states but
not the remaining simultaneous readiness requirements. This is evidence that
the broad deterministic roster under-samples the cooperative Power route.

Do not change AGI requirements or rewards from this result. The next testing
step is a separately registered policy-coverage field that makes the
Power-offer and acceptance decision contract deliberately competitive, then a
strict zero-fallback LLM negotiation robustness sample. Neither is a balance
authority by itself.

## Affected surfaces

- Canonical rulebook, semantic content, generated data, simulator, browser,
  player aids, and tests: no change.
- This receipt records simulation evidence only; no human-play claim is made.
