# Three-player Coalition competent-negotiation isolation

**Date:** 2026-08-01

**Evidence label:** Simulation / strict LLM paired policy isolation

**Status:** Valid completed Look 1 with one quarantined task; mixed and
insufficiently precise; no rule candidate and no canonical rule change.

## Registered execution

- Preregistration: `p3-coalition-competent-negotiation-v1`, committed before
  results at `d4389e34`.
- Exact frozen source: commit
  `d4389e34b8d7d50c71fdd8abbd73c6fa2de92b75`, `sourceDirty: false`.
- Executable game `0.8.32`; physical rules candidate
  `0.5.0-rc.32-test`; selected-rules engine `0.10.31`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Engine fingerprint:
  `sha256:59291cbb2eb776c63e4329db23b29c46d22f3ffc3590484d5c6e97198cbdb83c`.
- Root seed:
  `frontier-2038-p3-coalition-competent-negotiation-2026-08-01-v1-look-1`.
- The field scheduled 60 strict three-player LLM games: five comparator
  factions by three Coalition seats by baseline/follow-through policy by
  Coalition/comparator faction arm. Every LLM-controlled focal seat used
  Codex `gpt-5.6-terra` at `xhigh` reasoning. Opponents used the frozen
  deterministic profiles and backends in the preregistration.
- Eight worker threads and eight global/provider Codex calls were permitted
  concurrently. Peak active provider calls was eight.
- The provider broker issued 4,971 requests. It completed 4,970, failed one
  after its registered retry, cancelled none, and reported no throttling.
  All completed games had zero policy fallbacks.
- One right-arm game in
  `platform_empire:seat:1:follow_through` failed strictly and was quarantined.
  The run therefore retained 59 clean completed games, 58 paired-evidence
  games, 29 complete faction pairs, and 14 complete baseline/follow-through
  seed-group contrasts. The successful counterpart of the failed task is
  archived but excluded from paired inference.
- Raw local report:
  `evidence/studies/simulation/2026-08-01-p3-coalition-competent-negotiation-v1.look-1.raw.json`.
  SHA-256:
  `d5dabd7e90c14379dcf5ac230e4f7cfa1cf93f8a16ecad78521e00c1e8abfe03`.
- Immutable local archive:
  `evidence/studies/simulation/20260802T004943278Z-balance-audit-0-8-32-fc8bd0450b92-frontier-2038-p3-coalition-competent-negotiation-2026-08-01-v1-l-59x3-faction-swap-cli.json`.
  SHA-256:
  `d5dabd7e90c14379dcf5ac230e4f7cfa1cf93f8a16ecad78521e00c1e8abfe03`.

## Frozen primary analysis

The registered unit is the comparator-by-seat seed group. For each of the 14
groups with both policy treatments, the estimator subtracts the baseline
Coalition-minus-comparator result from the follow-through
Coalition-minus-comparator result. Two-sided 98% Student-t intervals use 13
degrees of freedom, matching Look 1's preassigned alpha of `0.02`.

| Outcome | Baseline Coalition minus comparator | Follow-through Coalition minus comparator | Follow-through effect | 98% interval | Required half-width |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mandate | -1.857 | -2.214 | -0.357 | [-6.479, +5.765] | <= 2.000 |
| Rank advantage | -0.357 | -0.357 | 0.000 | [-0.786, +0.786] | <= 0.250 |

The Mandate interval half-width is `6.122`; the rank interval half-width is
`0.786`. Both precision gates fail. The Mandate interval intersects zero and
the positive 4-Mandate practical threshold. The mean treatment effect also
changes sign by seat: `-1.0` at seat 0, `-2.75` at seat 1, and `+2.2` at seat
2. Comparator-family mean effects range from `-2.0` against Vertical Empire
to `+2.5` against Platform Empire. These families are descriptive and are not
multiplicity-adjusted claims.

The practical-effect gate fails: baseline Coalition was behind on average,
but follow-through did not improve its comparator-relative Mandate by at
least 4, did not bring the follow-through contrast to at least `-1`, and
produced no rank improvement. The mixed gate applies because the effect
changes sign by seat and comparator and misses both precision requirements.

## Negotiation and conversion traces

The following descriptive telemetry uses only the same 14 complete treatment
groups and the Coalition-controlled left games.

| Coalition trace | Baseline | Follow-through |
| --- | ---: | ---: |
| Absolute final score, mean | 15.000 | 16.786 |
| Promises made | 67 | 52 |
| Promises fulfilled | 2 | 1 |
| Fulfillment per promise | 2.99% | 1.92% |
| Deal Flow triggers / completed trades | 55 | 51 |
| Deal Flow Runway gained | 55 | 51 |
| Recorded Mandate-event points, mean | 15.357 | 17.357 |

The explicit prompt reduced promise volume but did not increase promise
fulfillment. It also did not increase Deal Flow activation. Absolute Coalition
score and recorded Mandate events rose descriptively, while the registered
comparator-relative outcome slightly worsened because the independently
controlled comparator arms also varied. The report preserves offers,
promises, terminal promise status, Deal Flow value, action traces, Mandate
sources, and final outcomes. It does not uniquely attribute fungible Runway to
a later resource spend, so a full transaction-level
Deal-Flow-to-spend-to-Mandate causal chain is not identifiable from this
artifact.

The persistent-weakness gate therefore cannot pass: follow-through did not
measurably improve fulfillment, and the outcome is far too imprecise to show
an aggregate deficit of at least 4 Mandate. This study does not establish that
Coalition rules are weak, nor does it establish that improved prompting fixes
Coalition conversion.

## Decision and version boundary

- Look 1 is **mixed and inconclusive**. It supports no Coalition rule change.
- The registered confirmation trigger fired, but its original analysis plan
  would pool Look 2 with this source population. After this run launched, the
  documentation-only release was published as commit `5ba48511`, executable
  `0.8.33`, physical candidate `0.5.0-rc.33-test`. Per the version boundary,
  no new simulation may be silently pooled with this `d4389e34` population.
- Any continued LLM isolation must launch from the published post-update
  source, use a tracked preregistration that treats this Look 1 as prior
  evidence rather than pooled evidence, and preserve a disjoint seed.
- Four- and five-player LLM guards do not trigger because the practical-effect
  gate did not pass.
- Deterministic evidence remains the primary balance instrument. This strict
  LLM field is robustness evidence only and cannot promote a physical rule.

## Affected-surface audit

- Canonical rulebook and faction card: no change.
- World/lore and optional Tactics documentation: no change.
- Physical semantics, balance constants, setup, and scoring: no change.
- Semantic content and generated gameplay data: no change.
- Simulator and deterministic policies: no change.
- Browser prototype: no change.
- Reference cards and player aids: no change.
- Tests: no gameplay implementation changed in response to this study; the
  current project validation is recorded with the receipt commit.
- LLM evidence archive: the aggregate raw report, immutable aggregate archive,
  and 59 completed-game archives are retained locally; only this receipt is
  tracked.
- Playtest protocol: continue recording Coalition trades, promise fulfillment,
  and resource-to-Mandate conversion, but do not introduce a Coalition rule
  variant from this field.
