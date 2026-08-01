# Preregistered LLM holdout caller-failure receipt

Date: 2026-07-27  
Evidence label: failed provider-boundary probe  
Verdict: invalid as LLM behavioral evidence; valid as a reproduced caller defect

## Identity

- Raw local report:
  `20260727T165746969Z-llm-negotiation-holdout-0-6-0-6715b70a972b-m3t4-llm-negotiation-holdout-20260727-1x4-llm-holdout-cli.json`
- Report SHA-256:
  `69b626288035adf4383ed055b2a5099c119a9f5668e2ce6960a6fda2f40a3b34`
- Source commit:
  `071c401ed63e8e4dd82022da6a3033be30ef0de1`
- Source dirty: `false`
- Executable game: `0.6.0`
- Physical candidate: `0.4.0-rc.7-test`
- Engine: `selected-rules` `0.8.0`
- Coverage: `lean-grid-ready-v6`
- Report schema: `6`
- Preregistration:
  `llm-negotiation-fresh-holdout-2026-07-27-v1`
- Registration commit:
  `d5c51c4d0c35dbfe45543c291922610703567d94`
- Root seed:
  `m3t4-llm-negotiation-holdout-20260727`
- Backend roster:
  `hybrid-codex`, `weighted`, `greedy`, `weighted`
- Requested provider/model:
  Codex CLI `0.145.0` / `gpt-5.6-sol`
- Decision cap:
  `16`

## Results

- Matches: `1`.
- Provider-stage attempts: `13`.
- Successful Codex decisions: `0`.
- Deterministic fallbacks: `13`.
- Recorded decision provider: `weighted-policy` for every receipt.
- Recorded fallback reason: `codex exited with code 1.` for all 13 attempts.
- Declarations: `0`.
- Power trades: `1`, not causally necessary for a declaration.
- World ending: Closed Loop.

The game completed, but every metered provider decision was made by the
fallback policy. No behavioral conclusion about Codex, LLM negotiation,
promise formation, betrayal, supplier viability, or competitive placement is
valid from this report.

## Reproduction and cause

The same caller boundary was reproduced directly with:

```bash
npm run strategy:codex -- \
  --input simulation/fixtures/decision-packet.example.json \
  --model gpt-5.6-sol
```

Codex rejected `decision-response.schema.json` because strict structured output
requires every property to appear in the schema's `required` array. The schema
declared `rationale` and `confidence` as properties but required only
`decisionId`.

The report exposed a second evidence defect: fallback receipts retained the
weighted-policy provider but discarded attempted Codex model, request, prompt
hash, exit status, duration, and stderr identity.

## Implemented repair

- Make every provider-output property required by the strict schema.
- Keep rationale and confidence semantically optional by accepting `null` and
  removing null commentary during response normalization.
- Attach attempted provider, model, request ID, prompt SHA-256, error class,
  safe error message, exit code, duration, and stderr SHA-256 to caller errors.
- Preserve those fields through deterministic fallback and match receipts.
- Distinguish successful fresh decisions from total provider attempts in the
  Simulation Lab.
- Add regression coverage for strict-schema shape, null normalization, and
  failure-provenance preservation.
- Add caller utilities, response schema, and process runner to the engine
  fingerprint.

## Surface audit

- Canonical rulebook: version attribution only; no rule or value changed.
- Semantic game graph: UI/provenance wording only; no mechanic changed.
- Machine-readable game data: regenerated copy/version identity only.
- Simulator: strict provider schema and failure-receipt repair.
- Browser prototype and Simulation Lab: provider-attempt count added.
- Reference cards and player aids: no mechanical change.
- Report schema: remains version 6; optional receipt fields are additive inside
  preserved observations.
- Automated tests: strict schema and fallback provenance added.
- Physical playtest protocol: synchronization/version note only.
- Immutable releases: create executable `0.6.1` and physical candidate
  `0.4.0-rc.8-test`; do not overwrite `0.6.0` or rc.7.

## Hypothesis disposition

Hypothesis: the preregistered holdout would produce a fresh, attributable Codex
negotiation trace.

Disposition: rejected for v1 because the provider never reached a decision.
The caller repair must be committed before a new preregistered seed is run.
That new holdout remains a pipeline and behavioral probe, not balance evidence.
