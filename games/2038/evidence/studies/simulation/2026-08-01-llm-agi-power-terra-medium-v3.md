# Terra AGI-and-Power robustness field — 2026-08-01

## Registration and identity

- Preregistration: `llm-agi-power-terra-medium-v3`, locked and committed at
  `5e6d1ac1`.
- Source at launch: `5e6d1ac117d4d0703df01df7616c34ad28f1fea3`, clean.
- Seed: `frontier-2038-llm-agi-power-terra-medium-2026-08-01`.
- Four seats: Dovetalis Labs / AGI Candidate / Codex; Loopfold AI / Power
  Broker / weighted; Mirevanta Works / Trust Governor / weighted; Kestralyn /
  Infrastructure Compounder / weighted.
- Model seat: `codex-cli`, `gpt-5.6-terra`, reasoning effort `medium`.
- Protocol: full-seat strict authority (`llmStages: null`), no numeric LLM
  decision cap, write-only fresh cache, and `choice-alias-v1` provider
  response aliases. Every legal action's complete label, parameters, and
  consequences remained visible; the caller resolved the chosen alias to its
  canonical action ID before resolution.

## Raw evidence

- Holdout report:
  `20260801T170555061Z-llm-negotiation-holdout-0-8-27-fc8bd0450b92-frontier-2038-llm-agi-power-terra-medium-2026-08-01-1x4-llm-holdout-cli.json`
  — SHA-256
  `7c8139b1719bd673803f438cbfb820841d3b900e320dad708ce659f376757c17`.
- Immediate completed-match archive:
  `20260801T170555057Z-tournament-0-8-27-fc8bd0450b92-frontier-2038-llm-agi-power-terra-medium-2026-08-01-run-0-1x4-llm-match-0.json`
  — SHA-256
  `f4e49add4e7e7fe4becd35df5e56e07f9cbb0296d4082a937d2131f328d713e0`.

## Result

- 103 fresh Codex decisions; all receipts identify Terra/medium; none are
  cached or fallback decisions.
- Integrity: zero violations, zero policy fallbacks, and zero forced no-ops.
- Dovetalis / AGI Candidate won the 17–17 tiebreak over Mirevanta / Trust
  Governor; Loopfold scored 9 and Kestralyn 7.
- The model seat accepted one Power sale from Loopfold in Round 4. The report
  marks that trade causally necessary. It had three Facilities, but only two
  Customers; no player reached the AGI core requirements, Grid-Ready progress,
  legal declaration window, or declaration.
- Negotiation produced 18 superseded and 16 unexercised Power promises. This
  is a single field observation, not a rate estimate.

## Interpretation and audited surfaces

This validates the repaired model-response protocol on a complete strict game:
the prior raw-composite-ID failure did not recur. It does not prove balance,
model superiority, AGI-route viability rates, or a rule change. It is not a
human playtest.

- Canonical rulebook, semantic content, generated data, browser, player aids:
  no change; this study found no rulebook/simulation divergence.
- Simulator and caller: the completed run exercises the alias repair committed
  in `11555a19`.
- Tests and release: focused caller regressions, full test suite, release
  generation, project check, and whitespace validation passed before this
  evidence run.

Next evidence: add an independently configured strict Claude field and the
remaining preregistered model-policy robustness cells. Keep all LLM fields
separate from deterministic balance aggregates.
