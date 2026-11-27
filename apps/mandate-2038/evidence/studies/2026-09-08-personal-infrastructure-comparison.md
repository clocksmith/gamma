# Personal infrastructure comparison and print correction

Date: 2026-09-08. Evidence class: controlled **strategy diagnostic** and browser
print walkthrough. No human playtest, balance promotion, or price change.

## Frozen comparison

Source commit `b35b16f9`; executable 0.20.2; engine 0.23.2; physical candidate
0.12.0-rc.3-test. All 96 raw reports name clean source provenance. Seed:
`2038-construction-personal-20260908-v2`, suffixed `-block-N` per paired block.

Run: `node lab/cli/construction-study.mjs personal`.

48 paired blocks / 96 games: all six factions, 2–5 players, greedy and weighted
backends. Twelve pairs per player count. Focal seats rotate by faction index,
not a complete faction-by-seat factorial. All players in a game use its named
backend; opponents retain the same profiles within each pair. Focal profile:
`infrastructure_compounder`, treatment `personal_infrastructure_v1` versus
`research_deploy_plan_v1`. Rivals: balanced_operator, capability_rusher,
market_maximalist, trust_governor, truncated to available seats. Negotiation on,
variable Mandates, canonical rules variant `{}`, no LLM calls, no cost overrides.

The new treatment deliberately considers all personal upgrades using the public
project rules. Unlike the old paired-cluster plan, it does not require a Generator
and two hosts before Mega-Cluster. It prefers adding a second Facility with Fusion
when legal. It is not an optimized policy; the retained control is not optimal play.

## Observations

| Players | Pairs | Mean focal score difference, infrastructure minus control | Positive / negative / tied | Mega-Cluster / Fusion / Quantum built |
| --- | ---: | ---: | --- | --- |
| 2 | 12 | -2.75 | 2 / 9 / 1 | 12 / 12 / 9 |
| 3 | 12 | -0.67 | 4 / 6 / 2 | 12 / 10 / 10 |
| 4 | 12 | -1.25 | 4 / 7 / 1 | 12 / 10 / 10 |
| 5 | 12 | +1.17 | 8 / 4 / 0 | 12 / 11 / 9 |

Across 48 infrastructure-policy games: 48 Mega-Clusters, 43 Fusion projects,
38 Quantum projects. Mega-Clusters supplied 218 accepted Compute from 270 nominal
output; Quantum supplied 31 Capability from 38 nominal output. Seven Quantum
Production gains were clipped entirely at the cap. This exposes a policy/timing
question, not evidence that Quantum's price should be changed. Infrastructure
players declared AGI 18 times; controls declared none. This does not establish
that a particular project caused any declaration or that the strategy is superior.

The four-player mean difference is -1.25 Mandate across only 12 pairs. Five-player
results favor this treatment; 2–4-player means do not. No confidence or dominance
claim is made from these thin cells. Two-player evidence remains exploratory.
These policies change several action priorities, so the comparison cannot isolate
the marginal value of one project. Fusion construction alone is not proof of
useful extra Power: the current aggregate does not causally attribute its
connections and downstream yields. That remains a question for recorded decisions
and physical observation. No unified balance promotion is claimed.

## Concrete corrections and surface audit

- **Rules / numeric component data:** no change to prices, unlocks, yields, AGI,
  Build, Generator limits, or Audit. Mechanics fingerprint remains unchanged.
- **Simulator:** exposes existing project prices and effects to the diagnostic
  policy through public observations; adds a named policy treatment. Default
  personas and the retained control are unchanged.
- **Browser game:** no rules or interaction change; existing public record display
  remains. **Physical component masters:** project faces now both carry name and
  faction; a dashed centre fold produces a 75 × 85 mm chip at 100% print scale.
  Eighteen strips / 36 faces were checked in Chrome print media, without overflow.
  The supplied PDF is a prototype print proof, not manufactured handling evidence.
- **Player aids:** project chip faces implement the common presentation; no
  change to other aid mechanics.
- **Observer preparation:** removes the obsolete Fusion construction award and
  paired-host language; asks about missed yields, cap clipping, alternatives,
  visibility, relocation and attempted handwritten records. No human session or
  completed playtest receipt was fabricated.
- **Tests:** 318/318 pass, zero failures/skips, plus content and release checks.
  No positive game-balance conclusion is inferred from these checks.

## Rejected collection and recovery

The v1 collection stopped on ENOSPC after printing result 53. Its non-atomic
checkpoint retained 52 rows. All earlier raw reports remain in the local archive.
The runner now checkpoints every accepted game atomically; resume validates report
and outcome hashes, duplicates, scheduled options and game/engine identity.
It writes to a new lineage-named file and leaves its parent unchanged. It rejects
completed or incompatible checkpoints. Unit tests exercise tampered artifacts,
duplicates and completed-run rejection.

The collector change creates a new identity, so v2 was a fresh comparison, not
pooled with v1. During v2, a real 90-game checkpoint was copied and resumed via:

```sh
node lab/cli/construction-study.mjs personal --resume evidence/studies/simulation/2038-construction-personal-20260908-v2-resume-proof-input.json
```

The six resumed games completed. All 96 outcome hashes matched the uninterrupted
run, and every resumed report/outcome file hash verified. This proves recovery for
that captured checkpoint; it does not erase the original storage failure.

## Retained evidence

[Per-game paths, hashes and summaries](../maintenance/2026-09-08-personal-infrastructure/project-comparison-index.json)
link every completed report and outcome in the local raw archive.
[Print proof](../maintenance/2026-09-08-personal-infrastructure/project-fold-proof.pdf),
[print measurements](../maintenance/2026-09-08-personal-infrastructure/project-print-report.json),
[full tests](../maintenance/2026-09-08-personal-infrastructure/follow-up-tests.log),
[interrupted collector](../maintenance/2026-09-08-personal-infrastructure/interrupted-study.log),
and [actual resume log](../maintenance/2026-09-08-personal-infrastructure/resume-proof.log)
retain the software and adverse evidence separately.

Original incomplete aggregate: `evidence/studies/simulation/2038-construction-personal-20260908-v1.json`, SHA-256 `d2e9c44e19b8cd143d43fd8cbfadeee846858a9c5ab9296913fa604e0c5a2f5c`.

Completed aggregate: `evidence/studies/simulation/2038-construction-personal-20260908-v2.json`, SHA-256 `11a39095212bf145278ff9863aad29ee33243bda0d6b229e54b48df91fa76584`.

Resumed aggregate: `evidence/studies/simulation/2038-construction-personal-20260908-v2-resume-343b20b4b713.json`, SHA-256 `11bb0315532d8b2336883742ae531adb99c3289b33adea9c42c794c71691acdc`.

An intermediate focused check during a concurrent merge failed on an extra
`governanceLedgers: undefined` expectation; the merge resolution replaced it with
a direct absence check. Its log is retained separately as
`intermediate-merge-test-failure.log`; the final suite includes the resolved test.

The next external proof is unfamiliar players using the frozen kit without
designer explanations. No publication or manufacturing action was performed.
