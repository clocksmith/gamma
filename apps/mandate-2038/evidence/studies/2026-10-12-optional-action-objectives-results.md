# Optional destination Actions and public objectives — 2026-10-12

Study: `2026-10-12-optional-action-public-objectives-v1`
Evidence: deterministic simulation and exact replay controls only. No human playtest, balance promotion, publication, or deployment.

## Decision and bounded result

Implement the two user-selected mechanics as the **0.25.0 playtest candidate**: an Org stays or moves one edge before performing or skipping its destination Action; one objective from each Era is visible from setup. Final scoring and all economic numbers remain unchanged. The study checks this selected candidate; it does not independently select or promote a balance change.

The registered comparison completed **576 matched scenarios / 2,304 games** across three, four, and five players. Every arm completed four Eras, twelve turns per player, four Productions, twelve Headlines, and four final objectives. Resource bounds, exact Production accounting, and reconstructed final Mandate passed in every game. There were no policy fallbacks. **48 separate control games** established original-versus-integrated baseline policy parity and candidate rich-versus-batch parity. **576 exact candidate replay controls** attributed skip availability without adding independent balance observations.

All 576 objective-only pairs have identical decisions, final holdings, score components, winners, and World Endings to baseline. Optional-Action-only and combined outcomes likewise match in all 576 pairs. The authored deterministic profiles do not inspect objective visibility. This is an information-timing invariance result under those policies, not evidence that advance objectives have no human strategic value.

The candidate produced 594 legal skips in 28,800 turns: 185 with an executable destination Action available and 409 without one. All 35 greedy skips had no executable destination Action; weighted policies account for the 185 affordable declines. The candidate has zero engine-blocked turns because every legal move has a skip resolution. Baseline had 47 blocked turns. These differently defined counts must not be presented as proof of less human frustration or improved action quality.

## Frozen frame and hypotheses

The [preregistration](2026-10-12-optional-action-objectives-preregistration.json) was saved before comparison outcomes. SHA-256: `76db59ec4c2b68370cb999efc446ec62a12852ed2253023f4a6fc0b10fb298c1`.

- Root seed: `mandate-20261012-optional-action-objectives-v1`.
- Counts: three/four/five, with four-player primary and separate three/five guards.
- Backends: homogeneous greedy and weighted; no provider, remote-model, GPU, model-download, or paid LLM calls.
- Objective modes: fixed and variable, analyzed together within each backend/field table below but retained separately in raw scenario identities.
- Fields: circular windows of all seven authored profiles; a separate identical `balanced_operator` field for seat diagnostics.
- Schedule: all six circular faction-window starts and every seat rotation. There are 18/24/30 scenarios per count/backend/objective-mode/field cell, hence 36/48/60 after combining the two objective modes. This does not cover all institution subsets.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`, `trust_governor`, `agi_candidate`, `power_broker`, using unchanged 0.24.4 profile bytes.
- Arms: executable 0.24.4; objective-reveal-only; optional-Action-only; combined candidate. Study-only subclasses isolate reveal timing outside the public game. No selectable retired rules profile was added.
- Hypotheses: finite complete execution and correct Production/scoring; objective-ignorant policy outcome invariance; legal skip availability and measurable uptake; no unexplained interaction between the two selected changes.

All arms execute the same frozen 0.24.4 compiled mechanical input bytes and the same candidate-integrated policy implementation. Original-policy baseline parity controls pass. The candidate's input changes were inspected: they alter turn/visit/reveal wording and retire stale Headline terminology, without changing numerical effects. Every actual input file hash is retained in each report.

The optional-Action engine changes the decision interface from Action-first selection to committed Org/destination selection. The same action weights now encounter a different number of movement choices and may consume different seeded decision streams. Its isolated arm therefore measures the rule together with necessary policy-interface integration; it is not a pure causal estimate of the skip option alone. The early-objective-only contrast remains isolated. Shared seeds couple scenarios but do not force identical histories after legal choices diverge.

## Mixed authored field

Means below are per player. Production is realized Compute per player per Era, after resource-cap clipping. Every row combines fixed and variable objective modes.

| Players / backend | Matched scenarios | Mean Mandate, baseline → candidate | Realized Compute Production, baseline → candidate | Candidate skip rate |
| --- | ---: | ---: | ---: | ---: |
| 3 / greedy | 36 | 14.056 → 14.620 | 1.956 → 2.201 | 0.231% |
| 3 / weighted | 36 | 13.917 → 14.259 | 1.826 → 2.035 | 4.861% |
| 4 / greedy | 48 | 13.677 → 14.536 | 1.909 → 2.078 | 0.217% |
| 4 / weighted | 48 | 13.833 → 13.922 | 1.898 → 1.980 | 5.425% |
| 5 / greedy | 60 | 13.670 → 13.437 | 2.127 → 2.217 | 0.222% |
| 5 / weighted | 60 | 14.320 → 13.497 | 1.913 → 1.914 | 4.250% |

Four-player mixed-field scores rise descriptively, but five-player scores fall under both backends. This does not support a blanket performance improvement. The same profile family can behave differently after its movement-choice interface changes.

### Four-player final-score reconstruction

Each Mandate equals Capability points + Customer points + Reputation points + AGI points + final objective points after Era IV Production, Reputation Review, and recognition.

| Backend / arm | Capability | Customers | Reputation | AGI | Objectives | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| greedy / baseline | 6.875 | 1.719 | 2.510 | 0.229 | 2.344 | 13.677 |
| greedy / candidate | 7.234 | 2.083 | 2.474 | 0.354 | 2.391 | 14.536 |
| weighted / baseline | 6.286 | 1.938 | 3.062 | 0.125 | 2.422 | 13.833 |
| weighted / candidate | 6.807 | 2.073 | 2.589 | 0.042 | 2.411 | 13.922 |

### Four-player Production accounting

Gross yields include placed Org production, equipped doubling, Customer Runway, and eligible Shovels income. Realized yields equal the observed holding change; clipped yields are gross minus realized. All resource-by-resource equalities passed in every arm. Values are per player per Era in the mixed field.

| Backend / arm | Runway gross / realized / clipped | Compute gross / realized / clipped | Reputation gross / realized / clipped |
| --- | ---: | ---: | ---: |
| greedy / baseline | 2.792 / 1.154 / 1.638 | 1.924 / 1.909 / 0.016 | 0.319 / 0.059 / 0.260 |
| greedy / candidate | 2.846 / 1.214 / 1.633 | 2.109 / 2.078 / 0.031 | 0.293 / 0.059 / 0.234 |
| weighted / baseline | 3.243 / 1.310 / 1.934 | 1.982 / 1.898 / 0.083 | 0.375 / 0.182 / 0.193 |
| weighted / candidate | 3.066 / 1.247 / 1.819 | 2.043 / 1.980 / 0.062 | 0.292 / 0.160 / 0.132 |

No Capability or Customer holding is produced directly. Final Org/equipment counts, all holdings, every Era's actual Production rows, action counts, objectives, and winners remain in the raw reports.

## Seat diagnostics and limits

Identical-policy fields separate seat questions from deliberately different persona strengths. These small descriptive ranges are not equivalence intervals or a balance verdict.

| Players / backend | Matched scenarios | Seat winner-credit range, baseline → candidate |
| --- | ---: | ---: |
| 3 / greedy | 36 | 8.33 → 8.33 pp |
| 3 / weighted | 36 | 8.33 → 6.94 pp |
| 4 / greedy | 48 | 14.58 → 10.42 pp |
| 4 / weighted | 48 | 12.50 → 14.58 pp |
| 5 / greedy | 60 | 11.67 → 10.00 pp |
| 5 / weighted | 60 | 11.67 → 6.67 pp |

Both four-player candidate point ranges exceed the existing 10 pp provisional seat tolerance. The cells are too small to establish either fairness or a credible regression; thresholds are unchanged and these observed values are not hidden. Mixed-persona seat ranges are also retained in the raw summary and must not be substituted for the identical-policy comparison.

This study supplies no confidence-sequence precision, independently competent strategy field, metered LLM holdout, human negotiation, blind teaching, or enjoyment evidence. It cannot promote faction/seat balance or establish the absence of dominant plans. A separate unified audit remains required and must keep its own source identity and limits.

## Source and release identities

Baseline is a preserved external copy of clean commit `aba758ac6f4b6eb597856c553d91d3d157d9e884`, game 0.24.4. Generated runtime was rebuilt from that copy before execution. Candidate sources were frozen externally after the selected engine and policy passed targeted tests. The isolated copies have no Git checkout identity; their report provenance therefore has null source commit/dirty fields, supplemented by the explicit baseline commit and full file hashes. They must not be called clean committed candidate evidence.

- Baseline ruleset fingerprint: `sha256:90bdf0467b9b2e54b709bd4cdd679c59bfc8761ab4f9dd35824ff09762013ab5`.
- Baseline frozen engine fingerprint: `sha256:949bca8e54cf47d9bd1a3ed34ac40c122e9681cb48f383aedd424173f84c121e`.
- Candidate ruleset fingerprint: `sha256:142c7601978d8dbb8a3aac818e4e35afce578996df742abb49cbfb71032ca2f4`.
- Candidate frozen engine fingerprint: `sha256:e8c7ec60d998f78d9985cbe44c8e27fcda62e2c2d44044d3d01ac346d5a2ef34`.
- Final sealed 0.25.0 / engine 0.28.0 / rules 0.14.0-rc.6-test ruleset fingerprint: `sha256:142c7601978d8dbb8a3aac818e4e35afce578996df742abb49cbfb71032ca2f4`.
- Final sealed engine fingerprint: `sha256:394851dc15d295b18ad7565fb0dbe8514b7265ba22792d651248b4ee22dbb7a8`.

The final sealed engine differs from the frozen comparison identity only in `web/app.js`: the movement heading/hint now reads authored `ui.json` copy instead of duplicating prose. A file-hash comparison verifies this display-only delta; the executable match engine and deterministic policy are byte-identical. Simulation behavior was not changed, and frozen reports retain their original identity rather than being relabeled as final-release executions.

- Match-engine SHA-256: `527fdbb293298cfd4ee03e895b2cb5416d1f0962fce202f25f1a9aa8eaa2af65`.
- Candidate deterministic-policy SHA-256: `e5ef75c280b92de16c23d8ec92ab1bfde55654b89172ffc0ffbb7d4eb888f5e8`.
- Executed study runner SHA-256: `cf157998faf93bb57d4d17c6e14213b9d9fd353e5218fd720fa9e680ed3ac3e4`.
- Runtime: Node 24.19.0, Linux, deterministic CPU execution. RNG: mulberry32 version 1; normal game report/replay/decision contracts remain 8/4/2. The study's raw envelope also carries its own study identifier and all source/input hashes.

## Affected-surface audit

| Surface | Delta or explicit no change |
| --- | --- |
| Rulebook and design record | Optional destination Action after committed Org movement; all four objectives revealed at setup. Final current-state scoring remains unchanged. |
| Mechanical records | Turn, visit, reveal, reference, and rule-change wording synchronized. No economic cost, yield, score, cap, faction ability, or deck-composition change. |
| Simulator and shared engine | Movement commitment and locked destination resolution; legal skip; setup objective selection; turn/skip telemetry. |
| Deterministic policy | Movement packets remain legal independently of affordability; skip receives low positive weight instead of inheriting Action rewards. Original baseline-policy parity verified. |
| Browser and authored interface | Movement-first builder and skip resolution use shared engine; heading/hint read authored UI copy. Browser qualification belongs to separate walkthrough evidence. |
| Player aids and generated projections | Regenerated from owning rule/data/UI sources. No hand-edited graph targets. |
| Physical specification and inventory | No change to component forms, counts, dimensions, or ownership encoding. |
| Lore and fiction | No lore change. Stale player terminology/reveal descriptions synchronized without adding fiction. |
| Tests | Movement-before-resolution, destination lock, skip affordability, Research single assignment, full skipped games, objective timing, Production, and final scoring covered by candidate regressions; study adds cross-count invariants/parity. |
| Existing early-recruitment runner | `2026-10-11-early-recruitment.mjs` receives an API adaptation: planned Action selection now matches committed Org/destination. Historical raw reports and receipts retain their original commit/script identity; they are not reinterpreted as current balance evidence. |
| Evidence and playtest protocol | This registered comparison, raw archive, exact skip attribution, limits, and ordinary-rules human observation requirements are recorded. No human result is fabricated. |
| AGENTS/CATSCAN | User-selected movement/reveal contracts synchronized. No acceptance check or qualification threshold weakened. |
| Release/history | New 0.25.0 / engine 0.28.0 / rc.6 identity; previous sealed releases unchanged. |
| Deployment/manufacturing | No deployment or manufacturing action. |

## Reproduction

Preserve two source directories: `BASELINE` from commit `aba758ac6f4b6eb597856c553d91d3d157d9e884` and `CANDIDATE` from this candidate's matching match-engine/policy bytes. Run `npm run content:build` in each. Do not use a different release to recreate old outcomes. The command expects absolute directories whose top level is `games/2038`'s content.

From `games/2038`, for each `PLAYERS` in 3, 4, 5 and `BACKEND` in greedy, weighted:

```bash
node evidence/studies/2026-10-12-optional-action-objectives.mjs   baseline="$BASELINE" candidate="$CANDIDATE"   players="$PLAYERS" backend="$BACKEND" output="$REPORT"
```

`REPORT` must be a new file; an existing output is rejected. Every cohort runs disjoint smoke controls before its comparison scenarios. No results-dependent stopping or profile optimization occurs.

```bash
node evidence/studies/2026-10-12-optional-action-objectives-analysis.mjs SUMMARY REPORTS...
node evidence/studies/2026-10-12-optional-action-objectives-replay.mjs   "$BASELINE" "$CANDIDATE" REPLAY_REPORT REPORTS...
```

Replay attribution reruns each saved candidate scenario, verifies final holdings, pieces, scores, actions, winner, and World Ending against its archive, and then separates skips with versus without an executable destination Action. These repeats are controls, not additional independent samples.

## Retained raw artifacts

Raw JSON files are retained in the local ignored archive `evidence/studies/simulation/`, using the filename prefix `2026-10-12-optional-action-objectives-`. Progress logs are retained in its same-named subdirectory. Summary and all source/report identities are retained below; this tracked receipt does not imply ignored raw files are published in Git.

| Artifact | SHA-256 |
| --- | --- |
| `2026-10-12-optional-action-objectives-3-greedy.json` | `6b650ce131475b12d846d16623f2f2e890554b2f8f52d62119c88347e560391f` |
| `2026-10-12-optional-action-objectives-3-skip-attribution.json` | `a1f2cbe302b354af4932b0ccf064fae9cdd6373ba13c324815c12b683976d77b` |
| `2026-10-12-optional-action-objectives-3-weighted.json` | `e169371ff23b35093e8785afe4c590e748441f1507f4e2632b89bd1070d3d781` |
| `2026-10-12-optional-action-objectives-4-greedy.json` | `0c3cc80c9b25281a89d1024954f427efb0157220dc1af429cf4b7f8b13d5a69b` |
| `2026-10-12-optional-action-objectives-4-skip-attribution.json` | `06f8d4625a8844e3dc3b9cba2e9bdc72d1c7427c577427f651c2b85ea139e302` |
| `2026-10-12-optional-action-objectives-4-weighted.json` | `9b763a40dcd69bca2975d59ad197e054da2d692503d9589ef2ead3992c16fbb8` |
| `2026-10-12-optional-action-objectives-5-greedy.json` | `eb8dd74e8b1e659e43215359c634c755a1ab3b7b626a2c430c810a9303448fe3` |
| `2026-10-12-optional-action-objectives-5-skip-attribution.json` | `a67e08f1f19a9a18a4ab8ccafcd4b32048efefc2795bd399cdf53a4f30598513` |
| `2026-10-12-optional-action-objectives-5-weighted.json` | `23d37512f2d5922327da412ace6145ee6f1b9804af3a1ec7d3d6d21a2fa2cff5` |
| `2026-10-12-optional-action-objectives-comparison-summary-v1.json` | `195393ebb3989e0342849160929720fc0af68c5dfbe4b378db6685283bbe55c7` |
