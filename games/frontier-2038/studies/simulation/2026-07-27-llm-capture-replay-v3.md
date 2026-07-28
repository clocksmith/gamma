# Preregistered LLM capture/replay v3 receipt

Date: 2026-07-27  
Evidence label: fresh provider capture plus exact cached replay  
Verdict: reproducibility pipeline proven; behavioral result descriptive; no rules change

## Identity

Fresh capture:

- Raw local report:
  `20260727T171157688Z-llm-negotiation-holdout-0-6-2-22a9423143ca-m3t4-llm-negotiation-holdout-20260727-v3-1x4-llm-holdout-cli.json`
- SHA-256:
  `acd7ec379b35fa97c603ce6bfd3fd5ee790c4bea714e0e72fb9caea5340e8e2e`
- Preregistration:
  `llm-negotiation-fresh-capture-2026-07-27-v3`
- Preregistration purpose:
  `fresh_robustness`
- Cache mode:
  `write-only`

Read-only replay:

- Raw local report:
  `20260727T171200985Z-llm-negotiation-holdout-0-6-2-22a9423143ca-m3t4-llm-negotiation-holdout-20260727-v3-1x4-llm-holdout-cli.json`
- SHA-256:
  `f3239fd6a984fca8a2c2f297605128fa0c08a248f47601321501547dac6319be`
- Preregistration:
  `llm-negotiation-cache-replay-2026-07-27-v3`
- Preregistration purpose:
  `cache_reproducibility`
- Cache mode:
  `read-only`

Shared identity:

- Source and registration commit:
  `7a0af8ab0786a8f56c3d2aad7952c6b3a7cf3161`
- Source dirty: `false` for both reports.
- Executable game: `0.6.2`.
- Physical candidate: `0.4.0-rc.9-test`.
- Engine: `selected-rules` `0.8.2`.
- Coverage: `lean-grid-ready-v6`.
- Report schema: `6`.
- Root seed:
  `m3t4-llm-negotiation-holdout-20260727-v3`.
- Profiles:
  `agi_candidate`, `power_broker`, `trust_governor`,
  `market_maximalist`.
- Backends:
  `hybrid-codex`, `weighted`, `greedy`, `weighted`.
- Provider:
  Codex CLI `0.145.0`, model `gpt-5.6-sol`.
- Decision cap:
  `16`.
- Local cache:
  `studies/simulation/cache/llm-negotiation-holdout-20260727-v3`.

## Capture and replay results

- Fresh provider decisions: `13`.
- Fresh provider fallbacks: `0`.
- Unique cache entries written: `13`.
- Replay cached decisions: `13`.
- Replay fresh provider decisions: `0`.
- Replay fallbacks or cache misses: `0`.
- Sanitized behavioral hash for each report:
  `64025cb409e58b5cb9dd48f321b44dd714e9e61744f46b496ad33453435640c3`.

The sanitized comparison includes seed, runs, aggregate seats, match metrics,
winners, standings without policy-receipt metadata, world ending, Power
trades, negotiations, declaration readiness, declarations, Realignment,
Systemic Risk, and Future Timeline. The capture and replay files are not
byte-identical because their preregistration identity and cache receipts must
differ; their game behavior is byte-identical after removing that evidence
metadata.

## Behavioral trace

- One Power trade occurred in Round III from the Power Broker to the AGI
  Candidate.
- Counterfactual attribution marked that imported Power as necessary for the
  powered state it supported.
- No AGI declaration occurred.
- Promises: `27` superseded and `16` unexercised; no fulfilled or broken
  promise outcome was logged.
- Final scores:
  - Trust Governor / Demis Hassabis: `20`;
  - Market Maximalist / Elon Musk: `14`;
  - AGI Candidate / Sam Altman: `12`;
  - Power Broker / Mark Zuckerberg: `12`.
- World ending: Closed Loop.

This is one timeline. It does not estimate declaration frequency, supplier
viability, faction strength, backend strength, or human negotiation quality.
The deterministic unified matrix remains the broader screen, and physical
play remains the authority for credible deals and betrayal.

## Hypothesis disposition

Hypothesis: a fresh, metered, write-only Codex capture can be reproduced by a
separately committed read-only plan without a provider call, fallback, cache
miss, or behavioral divergence.

Disposition: supported for all 13 provider decisions and the complete game
outcome under this exact source, seed, roster, model, and engine identity.

No game rule, faction value, card, score, or strategy weight is changed.

## Surface audit

- Canonical rulebook: no change.
- Semantic game graph and numeric values: no change.
- Machine-readable game data: no change.
- Simulator: no post-result change.
- CLI callers and cache: no post-result change; the committed capture/replay
  implementation passed.
- Browser prototype and Simulation Lab: no post-result change.
- Reference cards and player aids: no change.
- Report and decision schemas: no post-result change.
- Automated tests: no post-result change.
- Physical playtest protocol: no change.
- Immutable releases: no new release; both reports identify `0.6.2` / rc.9.
