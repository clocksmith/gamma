# Terra legal-choice alias quarantine — 2026-08-01

## Status

Quarantined LLM robustness attempt. This is a caller-interface defect record,
not a game result, balance observation, or playtest.

## Triggering attempt

- Preregistration: `llm-agi-power-terra-medium-v2`
- Source commit: `f0ea97a6`; source was clean at launch.
- Seed: `frontier-2038-llm-agi-power-terra-medium-2026-08-01`
- Seats: AGI Candidate / Codex, Power Broker / weighted, Trust Governor /
  weighted, Infrastructure Compounder / weighted.
- Provider: `codex-cli`, `gpt-5.6-terra`, reasoning effort `medium`.
- Evidence mode: strict, full-seat authority, fresh write-only cache; no
  numeric LLM decision cap.
- Last request: `m3t4-2038:r4:c3:s0:resolve:315`.
- Canonical prompt SHA-256:
  `49f4ac1d5b05eb82a0e2f62af65524c7dd3dba054eb12155db48688f8a0ccad9`.
- The provider selected
  `organize_redistribute_s0-ceo_grid_reactor-1_s0-team-1_grid_reactor-1`,
  which was not among the packet's legal decisions. The captured legal set
  contained similarly shaped canonical IDs, including the valid
  `organize_redistribute_s0-ceo_frontier-1_s0-team-1_grid_reactor-1`.
- 88 preceding successful fresh receipts are retained in the local ignored
  cache at `studies/simulation/cache/llm-agi-power-terra-medium-v2/`.
  The failing response is not cached, and no completed-game archive exists.

## Containment and repair

Strict evidence quarantined the match and did not select a weighted or
rulebook-default fallback. The defect boundary is the provider-facing action
identifier protocol: long composite canonical IDs made copy-exact selection
fragile despite a complete legal decision set.

The caller now presents every legal action with its full label, parameters, and
consequences but replaces its response identifier with a stable short alias
(`choice-01`, `choice-02`, and so on). The caller resolves a selected alias to
the unchanged canonical ID before the environment mutates state; an unknown
alias still fails closed. The decision-cache key includes the provider protocol
version, preventing old canonical-ID responses from being reused under the new
prompt contract.

## Validation and closure

- Focused alias-resolution and illegal-alias regressions: passed in
  `tests/cli-callers.test.mjs`.
- Full `npm test`: passed.
- `npm run game:release`, `npm run check`, and `git diff --check`: passed.

Closure level: source-fixed and release-verified. A new committed strict LLM
field is still required before claiming controlled LLM simulation verification.
