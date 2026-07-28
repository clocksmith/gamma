# Preregistered LLM negotiation holdout v2 receipt

Date: 2026-07-27  
Evidence label: fresh provider-pipeline and behavioral trace  
Verdict: caller boundary proven; behavioral result descriptive; no rules change

## Identity

- Raw local report:
  `20260727T170633753Z-llm-negotiation-holdout-0-6-1-c6f464943d61-m3t4-llm-negotiation-holdout-20260727-v2-1x4-llm-holdout-cli.json`
- Report SHA-256:
  `749d7193e4258f0349262a598d004c3fba2513da69d476699ae9bcd7fa5b55a2`
- Source and registration commit:
  `975d1dfeecff79ef3f12243da9afd92c2af203b7`
- Source dirty: `false`
- Executable game: `0.6.1`
- Physical candidate: `0.4.0-rc.8-test`
- Engine: `selected-rules` `0.8.1`
- Engine fingerprint:
  `sha256:0197e4966d2941f7d64dcf625254d7da8b1ce1276adbc2d45cd1fca3474161ea`
- Coverage: `lean-grid-ready-v6`
- Report schema: `6`
- Preregistration:
  `llm-negotiation-fresh-holdout-2026-07-27-v2`
- Preregistration fingerprint:
  `sha256:4b8d902c5f3d11563918b4669a972a679d168b41ce4def48b0b43ebc3f6d9da9`
- Root seed:
  `m3t4-llm-negotiation-holdout-20260727-v2`
- Profiles:
  `power_broker`, `agi_candidate`, `market_maximalist`, `trust_governor`
- Backends:
  `hybrid-codex`, `weighted`, `greedy`, `weighted`
- Provider:
  Codex CLI `0.145.0`, model `gpt-5.6-sol`
- Decision cap:
  `16`

## Results

- Matches: `1`.
- Fresh Codex decisions: `12`.
- Provider fallbacks: `0`.
- Every Codex receipt contains model, request ID, legal decision ID, prompt
  SHA-256, duration, and cache status.
- The Codex-backed Power Broker repeatedly proposed one-Power promises.
- Promise outcomes: `29` superseded and `16` unexercised.
- Fulfilled or broken promises: `0`.
- Power trades: `0`.
- AGI declarations: `0`.
- Final scores:
  - Power Broker / Sam Altman: `14`;
  - AGI Candidate / Mark Zuckerberg: `17`;
  - Market Maximalist / Demis Hassabis: `19`;
  - Trust Governor / Elon Musk: `12`.
- World ending: Closed Loop.

## Interpretation

The strict Codex schema, live process call, legal-decision validation, prompt
hashing, and receipt path work from a clean committed source. This repairs the
v1 caller failure.

The match is not a balance estimate and does not show that LLM negotiation
creates viable cooperation. It contains proposals but no accepted or broken
deal. It cannot compare Codex with Claude, deterministic backends, or humans.
No game rule or numeric value is justified by this trace.

## Pipeline follow-up

The run also confirms a pre-existing reproducibility gap: fresh holdouts use
cache mode `off`, while replay holdouts require an existing read-only cache.
No preregistered surface currently writes a fresh result without first reading
the cache. The evidence pipeline must add write-only capture and prove a
separately preregistered read-only replay before claiming cached
reproducibility.

## Surface audit

- Canonical rulebook: no change.
- Semantic game graph and numeric values: no change.
- Machine-readable game data: no game-content change.
- Simulator: no post-result game-mechanic change.
- CLI caller: successful repair confirmed; write-only cache follow-up required.
- Browser prototype and Simulation Lab: no game-rule change.
- Reference cards and player aids: no change.
- Report and decision schemas: no post-result change.
- Automated tests: existing strict-schema regression passed.
- Physical playtest protocol: no change.
- Immutable releases: report identifies `0.6.1` / rc.8 exactly.

## Hypothesis disposition

Hypothesis: the repaired fresh Codex boundary produces attributable legal
decisions without fallback.

Disposition: supported for this preregistered pipeline probe. The behavioral
negotiation outcome remains inconclusive and no balance claim is promoted.
