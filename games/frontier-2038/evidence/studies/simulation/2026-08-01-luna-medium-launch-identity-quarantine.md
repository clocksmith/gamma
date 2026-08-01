# Luna medium launch-identity quarantine

## Status

Invalid attempt. This is not simulation evidence and must not be pooled with
deterministic or LLM balance results.

## Registered field

- Preregistration: `llm-agi-power-luna-medium-v1`
- Intended configuration: four players; full-seat Codex `gpt-5.6-luna` at
  medium reasoning; strict authority; write-only fresh cache; no numeric LLM
  decision cap.

## What happened

The run made 96 fresh, uncached decisions. Every retained receipt identifies
`codex-cli`, `gpt-5.6-luna`, medium reasoning, and `fallback: false`.

Before final report identity verification, the source worktree was edited for
the Lab archive viewer. The runner compared its launch snapshot
`sha256:2d39fc0845f30532147999ba6a32591a023e50ca0f5f9451e4039c2f32bab899`
with the then-current identity
`sha256:8635966a72e2d48d8be739bc9d5add6aba77c36bc467a2d28e62f3e9f97f08e9`
and rejected finalization with `launch_identity_mismatch`.

No aggregate report, standings, winner, or replay was published. The raw
decision cache was preserved locally at
`studies/simulation/cache/incomplete/llm-agi-power-luna-medium-launch-identity-invalid-2026-08-01/`.
The registered cache path has been recreated empty for any future clean rerun.

## Required next step

Rerun only from a clean committed source with no edits until final report
identity verification completes. Register a new field if the locked
preregistration is no longer the intended model study.
