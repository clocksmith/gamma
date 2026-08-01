# Three-player Coalition strict LLM robustness field

**Date:** 2026-08-01

**Evidence label:** Simulation / strict LLM robustness

**Status:** Valid complete field; qualitative Coalition weakness reproduced;
not balance evidence and no rule change selected.

## Registered execution

- Preregistration: `p3-coalition-strict-llm-v1`, committed before results at
  `bff79d45`.
- Exact source: commit `bff79d457698ba9633125d689fea76e9613b6e3a`,
  `sourceDirty: false`.
- Executable game `0.8.30`; selected-rules engine `0.10.29` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Engine fingerprint:
  `sha256:f02f7c9c49b3244cd1a2e6bf5f5b4d07b8ea021946bb2ff91ca8971113a576fe`.
- Root seed:
  `frontier-2038-p3-coalition-strict-llm-2026-08-01-v1`.
- Twelve complete three-player games: Coalition/Safety and
  Coalition/Imperial common-seed swaps at each focal seat, one game per arm.
  The focal policy was Power Broker under full-decision Codex
  `gpt-5.6-terra`, medium reasoning; the other seats were deterministic.
- Four workers, four global/provider Codex calls in parallel, strict
  no-fallback authority, and one configured retry.
- All 976 provider requests completed. There were zero failed, cancelled, or
  retried calls; zero quarantined matches; zero policy fallbacks; and twelve
  immediate completed-game archives.
- Raw local aggregate:
  `evidence/studies/simulation/2026-08-01-p3-coalition-strict-llm-v1.raw.json`.
  SHA-256:
  `b942e0fdbb84b54eba978ceaaf1bcc81536ad27e3bff3b5ae4aacadd9989bb3e`.

## Observed paired traces

The left arm is Coalition in every row. These are single paired games, not
estimates or confidence intervals.

| Comparison | Win-credit delta | Score delta | Rank advantage |
| --- | ---: | ---: | ---: |
| Safety, seat 0 | +1 | -4 | +1 |
| Safety, seat 1 | 0 | -5 | 0 |
| Safety, seat 2 | -1 | -15 | -2 |
| Imperial, seat 0 | -1 | -13 | -2 |
| Imperial, seat 1 | 0 | -4 | 0 |
| Imperial, seat 2 | -1 | -19 | -2 |

Coalition scored less than its substituted faction in all six common-seed
pairs. Its six scores averaged `9.0`, versus `19.0` for the three Safety and
three Imperial arms. The average score deficit was 8 points against Safety
and 12 points against Imperial. Win direction was mixed against Safety and
negative at two of three seats against Imperial.

This was not a failure to invoke Deal Flow. Coalition completed 22 qualifying
trades and gained 22 Runway across its six games, averaging 3.67 triggers per
game. It also made 71 negotiation promises but fulfilled none; no promise was
recorded as broken because the promised sale windows were not exercised.
Those traces identify weak conversion and negotiation follow-through as
behavior worth testing. They do not identify the correct rule remedy.

## Interpretation and decision

- The qualitative direction reproduces Coalition weakness under a
  full-decision LLM policy instead of rescuing Coalition from the deterministic
  signal.
- The field shows that the LLM sees, accepts, and initiates trades and realizes
  Deal Flow repeatedly. It does not show that an extra resource or point would
  be balanced.
- Backend regime belongs only to this robustness result. It is not retrofitted
  as a factor in the deterministic isolation studies.
- One game per arm cannot estimate faction balance, credible dominance, or a
  seat effect. The result can support a candidate nomination only when combined
  with a separately valid deterministic causal study.
- No canonical or physical rule changes from this field.

## Affected-surface audit

- Canonical rulebook and faction card: no change.
- Semantic content and generated gameplay data: no change.
- Simulator and browser prototype: no change.
- Reference cards and player aids: no change.
- Tests: no change; the frozen release had already passed 167 of 167 tests and
  the release gate.
- LLM evidence archive: aggregate plus twelve completed-match archives retained
  locally; only this receipt is tracked.
- Playtest protocol: Coalition conversion and promise follow-through are useful
  observation prompts, but this field does not authorize a physical rule
  variant.
