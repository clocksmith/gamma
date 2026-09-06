# Three cuts implementation study — 2026-09-06

This is a development diagnostic for the user's selected redesign, not a balance
promotion, a human playtest, or a measured BGG complexity rating. The hypothesis is
that immediate Headlines, one construction procedure, and one permanent faction
ability remove remembered procedures while retaining infrastructure, risk, and AGI.

All runs used seed `2038-three-cuts-20260906`, the `weighted` deterministic backend,
variable Era Mandates, rotating fictional factions, no LLM calls, no scenario,
one worker, and ten sampled replays. Each invocation completed successfully.
The final candidate completed 24 four-player games and 12 each at three and five
players. Every sampled replay in every stage reaches the twelve-Headline timeline
and a World Ending. Counts are diagnostics; they do not establish strategic
viability, teachability, player enjoyment, or human completion time.

The order was Headlines → revised Build → factions. The Headline comparison is
isolated. The construction stage also removes Emergency Pause because its Program
target no longer exists. The final stage combines faction redesign with removal of
remaining old branches, correction of the obsolete Power-demand Mandate, project
packet/strategy compatibility, and source/projection synchronization. Consequently,
its difference from the construction stage cannot be attributed only to factions.
The stage reports carry their actual source fingerprints and dirty development
identities. None qualifies as the clean-source unified promotion audit.

## Aggregate observations

| Stage | Games × players | AGI declarations | Games recognizing AGI | Open ending | Systemic Risk created |
| --- | ---: | ---: | ---: | ---: | ---: |
| Previous 0.17.0 baseline | 24 × 4 | 1 | 1 | 24 | 2 |
| Immediate Headlines only | 24 × 4 | 0 | 0 | 20 | 65 |
| Build without Programs | 24 × 4 | 3 | 3 | 21 | 66 |
| Combined candidate, four players | 24 × 4 | 1 | 1 | 23 | 58 |
| Combined candidate, three players | 12 × 3 | 0 | 0 | 10 | 27 |
| Combined candidate, five players | 12 × 5 | 0 | 0 | 12 | 38 |

The final four-player sample built no Mega-Clusters or Fusion; the three- and
five-player samples each built one Mega-Cluster, with one and two Fusion projects
respectively. This leaves the frequency and attractiveness of advanced construction
unresolved. AGI remains rare in these policies. No AGI threshold or replacement risk
was added in response. All numerical faction values remain provisional.

A controlled engine test proves Facility I → Facility plus Generator II →
Mega-Cluster III, including Era III production, → Fusion IV is legal with the
required resources and sites. A mobile browser fixture confirms the combined Build
choice spends both costs and exhausts Build once. These prove implementation and
possible pacing, not that an economic strategy reliably affords or prefers it.

The browser also completed an ordinary four-Era game without page errors. At 390px
and 1440px, all seven requested stories are present in the World companion and card
reference and searchable in the gallery, with no clipping or horizontal overflow.
The seven supplied vignette paragraphs remain verbatim. No human playtest occurred.

## Audited surfaces and deltas

- Rules: only six Core selections; immediate Headline boundary; Facility then one
  project under Build; permanent faction ability/common scoring; revised inventory.
- Data: sixteen immediate Headlines; two project references plus four lore-only
  records; six single-ability factions with secondary fiction preserved; corrected
  current-connection infrastructure Mandate; no Program/temporary Compute supply.
- Simulator: removed Program execution/use history, delayed Headline branches,
  faction frequency windows and special scoring; validates combined price and
  post-Facility project requirements; supplier income uses visible rival Facilities
  and a cap of two. Construction and actual supplier income are recorded in metrics.
- Browser: loads projects, uses the same engine and ordinary assignment controls,
  and removes retired Program labels. Background SVG: no change.
- Reference/player aids and physical specification: one Build procedure, one
  faction ability, immediate events, 106 standard cards, no Program use record.
- Lore: original Era prose and all seven supplied vignettes remain; former Program
  flavor appears in its Era, secondary faction flavor remains in faction references.
  Scenario ownership and authorized mechanic-revision receipts follow those records.
- Tests: replaced assertions for retired procedures with current-contract tests;
  retained geography, construction ownership/supply, trade, scoring, deterministic
  replay, release, and inference checks. The matrix test now uses two supported
  resource levers instead of a retired Kestralyn scoring exception.
- Playtest documentation: measures reminders, construction's first productive Era,
  AGI/risk/endings, and sacrifices of immediate bonuses to preserve Agent presence.
- AGI qualification/payment/award, Research deck, six Core Actions, four Eras,
  starting faction assets, hex geometry, and separate World Ending: no change.

## Raw report identities

Raw JSON is retained in the local ignored simulation archive. Hashes below are
SHA-256 of the exact report bytes. Profiles and rules/engine fingerprints identify
the actual run inputs; source-dirty runs are explicitly non-promotional.

### Previous 0.17.0 baseline

- Archive: [20260906T200627920Z-tournament-0-17-0-b9140fd15c56-2038-three-cuts-20260906-24x4-cli-04c7739e-36d8-4c78-8042-e8fe068ffed9.json](../../evidence/studies/simulation/20260906T200627920Z-tournament-0-17-0-b9140fd15c56-2038-three-cuts-20260906-24x4-cli-04c7739e-36d8-4c78-8042-e8fe068ffed9.json)
- Report SHA-256: `df7573c4f2ae9badc90d37218f55d6a730bf819d5e0bc5d79da26a021a0646a6`
- Generated: `2026-09-06T20:06:27.920Z`; source `1cb2ac913d5413ab3695cb2c0f68788399f218e6`; dirty `false`.
- Game `0.17.0`; engine `0.19.0`.
- Ruleset: `sha256:b9140fd15c56c8be5e0398da65a80f874f6a166adebb17ff3a89ee9a30d63689`
- Engine: `sha256:0cf38827c58b76bff98dcf2917eca94cd06b1abf98e51b31432f889b2f4ec5d3`
- Rules variant: canonical overlay `{}`; effective `sha256:84cb16aca3bc2205be1536af03dcdffa11a94f602e916339ea734fe0f40985cd`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`.
- Strategy set: `sha256:f8156311cdc9eb00a820b9ff9195c116f969f0761709af7be36745250ef8caad`
- Validity: `outside_provisional_bounds`; no balance promotion.

### Immediate Headlines only

- Archive: [20260906T201156990Z-tournament-0-17-0-3ab05ce082ce-2038-three-cuts-20260906-24x4-cli-a75009cf-a158-4722-8bf3-934ebb108d07.json](../../evidence/studies/simulation/20260906T201156990Z-tournament-0-17-0-3ab05ce082ce-2038-three-cuts-20260906-24x4-cli-a75009cf-a158-4722-8bf3-934ebb108d07.json)
- Report SHA-256: `91859c18d54ea11defa3a7623ec86be6be31f54d7806a6fbf7962d0bc705b437`
- Generated: `2026-09-06T20:11:56.990Z`; source `1cb2ac913d5413ab3695cb2c0f68788399f218e6`; dirty `true`.
- Game `0.17.0`; engine `0.19.0`.
- Ruleset: `sha256:3ab05ce082ce4e640febabf4b3a1e43096d0d967524ec5864d02604d62fc7219`
- Engine: `sha256:4b3f6f3b7a89ba811358abd95daeddbc8dee894190311dd3f9360e5d0bdd7e6f`
- Rules variant: canonical overlay `{}`; effective `sha256:84cb16aca3bc2205be1536af03dcdffa11a94f602e916339ea734fe0f40985cd`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`.
- Strategy set: `sha256:f8156311cdc9eb00a820b9ff9195c116f969f0761709af7be36745250ef8caad`
- Validity: `outside_provisional_bounds`; no balance promotion.

### Build without Programs

- Archive: [20260906T202132945Z-tournament-0-17-0-3ab05ce082ce-2038-three-cuts-20260906-24x4-cli-d34aa4b3-9884-4fe4-83ca-d497c47fb3cb.json](../../evidence/studies/simulation/20260906T202132945Z-tournament-0-17-0-3ab05ce082ce-2038-three-cuts-20260906-24x4-cli-d34aa4b3-9884-4fe4-83ca-d497c47fb3cb.json)
- Report SHA-256: `b01c38c06a2d9ad28a6258b6b05e4cf1f83e14289f43c234531edc71ed97884c`
- Generated: `2026-09-06T20:21:32.945Z`; source `1cb2ac913d5413ab3695cb2c0f68788399f218e6`; dirty `true`.
- Game `0.17.0`; engine `0.19.0`.
- Ruleset: `sha256:3ab05ce082ce4e640febabf4b3a1e43096d0d967524ec5864d02604d62fc7219`
- Engine: `sha256:a4060246bb6f76675b13ac9729abf891c3924f906aae189aab0d75ce89edcd57`
- Rules variant: canonical overlay `{}`; effective `sha256:84cb16aca3bc2205be1536af03dcdffa11a94f602e916339ea734fe0f40985cd`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`.
- Strategy set: `sha256:f8156311cdc9eb00a820b9ff9195c116f969f0761709af7be36745250ef8caad`
- Validity: `outside_provisional_bounds`; no balance promotion.

### Combined candidate, four players

- Archive: [20260906T204931639Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-24x4-cli-e40f649f-5006-488c-9097-49808d23c5ac.json](../../evidence/studies/simulation/20260906T204931639Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-24x4-cli-e40f649f-5006-488c-9097-49808d23c5ac.json)
- Report SHA-256: `9486306b75581f5d3f633238deca4e39168db2964281e30012c2fe56cbff657e`
- Generated: `2026-09-06T20:49:31.639Z`; source `27623994de362a282b235f2d245f3bf936a29b7e`; dirty `true`.
- Game `0.18.0`; engine `0.20.0`.
- Ruleset: `sha256:1fdd9d51a2877de2c24eaf07799ceb9d0ea4d2c91a29b4e7265600660f0d71b7`
- Engine: `sha256:45bab778803912148858a65caa11c81e4dccde8d016eb859c3a3ac2ab2d8ad9b`
- Rules variant: canonical overlay `{}`; effective `sha256:5872f3fed039367732b204482e9138257cf64d2da8df3db29399c7fe22c997e7`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`.
- Strategy set: `sha256:84bb428266c5b25140bcb825496c69c7468e53781ce491644fe4c4a054ee0432`
- Validity: `outside_provisional_bounds`; no balance promotion.

### Combined candidate, three players

- Archive: [20260906T204931712Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-12x3-cli-34dad1fc-1166-40ff-b6d2-c3f4c5951798.json](../../evidence/studies/simulation/20260906T204931712Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-12x3-cli-34dad1fc-1166-40ff-b6d2-c3f4c5951798.json)
- Report SHA-256: `2b4efc20b587c115b4433221308b7e06b2b751cc1fbbf04d9971b1693b31d04a`
- Generated: `2026-09-06T20:49:31.712Z`; source `27623994de362a282b235f2d245f3bf936a29b7e`; dirty `true`.
- Game `0.18.0`; engine `0.20.0`.
- Ruleset: `sha256:1fdd9d51a2877de2c24eaf07799ceb9d0ea4d2c91a29b4e7265600660f0d71b7`
- Engine: `sha256:45bab778803912148858a65caa11c81e4dccde8d016eb859c3a3ac2ab2d8ad9b`
- Rules variant: canonical overlay `{}`; effective `sha256:5872f3fed039367732b204482e9138257cf64d2da8df3db29399c7fe22c997e7`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`.
- Strategy set: `sha256:0ed8925906ba76b779fb66954fa7e21ce52c8585412c1b6610e476c451a4fafb`
- Validity: `outside_provisional_bounds`; no balance promotion.

### Combined candidate, five players

- Archive: [20260906T204932377Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-12x5-cli-93e6830b-bb62-4076-b973-765951064d35.json](../../evidence/studies/simulation/20260906T204932377Z-tournament-0-18-0-1fdd9d51a287-2038-three-cuts-20260906-12x5-cli-93e6830b-bb62-4076-b973-765951064d35.json)
- Report SHA-256: `e83919c2e6508dffbe1f399e0ab66f0acea3741502c1f75d97f26cc326365ca7`
- Generated: `2026-09-06T20:49:32.377Z`; source `27623994de362a282b235f2d245f3bf936a29b7e`; dirty `true`.
- Game `0.18.0`; engine `0.20.0`.
- Ruleset: `sha256:1fdd9d51a2877de2c24eaf07799ceb9d0ea4d2c91a29b4e7265600660f0d71b7`
- Engine: `sha256:45bab778803912148858a65caa11c81e4dccde8d016eb859c3a3ac2ab2d8ad9b`
- Rules variant: canonical overlay `{}`; effective `sha256:5872f3fed039367732b204482e9138257cf64d2da8df3db29399c7fe22c997e7`.
- Profiles: `balanced_operator`, `capability_rusher`, `infrastructure_compounder`, `market_maximalist`, `trust_governor`.
- Strategy set: `sha256:752795fe25c010f944709b222fcd977e3fa13b74b67ee5c9da874106e0e064d7`
- Validity: `outside_provisional_bounds`; no balance promotion.

Reproduction command (use the matching frozen/source identity above):

```sh
node lab/cli/monte-carlo.mjs --runs 24 --players 4 --seed 2038-three-cuts-20260906 --workers 1 --sample-replays 10 --output /tmp/2038-three-cuts-report.json
```

Use `--runs 12 --players 3` and `--runs 12 --players 5` for the corresponding
completion diagnostics. The intermediate dirty stages are not frozen releases and cannot be reproduced
from a Git commit alone. Their hashes identify the actual development inputs;
current source implements only the selected combined ruleset.

## Release validation

Executable `0.18.0`, engine `0.20.0`, and rules candidate `0.11.0-rc.1-test`
are frozen in `versions/`. `npm test` passed all 277 tests; `npm run check`
verified content, boundaries, provenance, project contracts, and both immutable
release bundles. `git diff --check` passed. Browser checks covered a complete
game, a combined Build on mobile, and all seven stories on desktop/mobile.
The final release also rejects removal of the required local Generator rule
at the option boundary. No human playtest or promotion audit is claimed.
