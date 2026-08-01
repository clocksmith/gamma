# Claude Sonnet provider quarantine — 2026-08-01

## Status

Quarantined before the first game decision. This is provider-access evidence,
not a game result, balance observation, or simulator defect.

## Registered attempt

- Preregistration: `llm-agi-power-claude-sonnet-medium-v1`, locked and
  committed at `902368b0`.
- Source at launch: clean `902368b0`.
- Requested provider: `claude-cli`, model alias `sonnet`, effort `medium`.
- Strict full-seat authority, write-only fresh cache, no numeric LLM decision
  cap, and the `choice-alias-v1` response protocol.
- First request: `m3t4-2038:r1:c1:s0:public_research_grant:1`.
- Prompt SHA-256:
  `105a3f61ae08486e5f4227ecaf7709c7665fc8474d13492f0c260ef6b7024b36`.

## Containment

`claude` exited with code 1 before returning a decision. Strict evidence
quarantined the attempt; no weighted or rulebook fallback, cache entry,
completed-match archive, or holdout report was created.

The local `claude auth status` result was:

```json
{"loggedIn":false,"authMethod":"none","apiProvider":"firstParty"}
```

The provider receipt records `claude-cli`, `sonnet`, `medium`, exit code 1,
and a 1,383 ms attempted-call duration. No stderr was emitted, so its stderr
hash is null.

## Required follow-up

Authenticate the local Claude CLI or provide an authorized Anthropic provider
configuration, then register and run a new fresh field. Do not replay or
promote this attempt. Its blocker does not affect completed Codex evidence or
deterministic balance studies.
