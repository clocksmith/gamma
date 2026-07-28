# rc.4 synchronization validation

**Evidence type:** simulation  
**Generated:** July 26, 2026 at 8:15:14 PM EDT  
**Purpose:** executable synchronization validation; not a balance-selection study

## Identity

- Executable game: `0.3.0`
- Physical rules candidate: `0.3.0-rc.4-test.2`
- Engine coverage: `rc4-baseline-v1`
- Ruleset: `sha256:08937daeb3385ca7abcb43d2e531c65b567008867b42cbd1c22cbd08b465c211`
- Mechanics: `sha256:60b70a5ceec571d5f62338b3134ea1287b266ac9b8267272a734eae155ee9b4e`
- Engine: `sha256:4d0023dd960a00cc4f8e151228bf8d72cdb469d0aabf64f4e01d566a0501afe3`
- Seed: `rc4-sync-release-final-optional-tokens`
- Runs: 100
- Players: 4
- Backends: four seeded weighted policies
- Profiles: Balanced Operator, Capability Rusher, Infrastructure Compounder,
  and Market Maximalist
- LLM decisions: none
- Raw report:
  `20260727T001514401Z-tournament-0-3-0-08937daeb338-rc4-sync-release-final-optional-tokens-100x4-cli.json`
- Raw report SHA-256:
  `df99c070dbdb7e1bd43487ca3ef5cde367dfc2c87ce86c89f111565a68678660`

## Aggregate result

- Seat win-share range: `0.030`
- Faction win-share range: `0.338`
- Profile win-share range: `0.170`
- Action diversity: `0.933`
- AGI eligibility rate: `0`
- AGI declaration rate: `0`
- Genuine AGI ending rate: `0`
- Non-declaring winner rate: `1.00`
- Mean Systemic Risk created: `0.61`
- Realignment outcomes: Expand Periphery 38, Consolidate Core 24,
  Counter-Cycle 38
- Tactic use: zero, as required by the baseline exclusion

## Interpretation and validity limits

The run proves that the synchronized engine can deterministically complete
100 four-player games across all factions, all Headlines, all era Mandates,
the thirteen-district board, Round III Realignment, infrastructure Production,
Audits, Wild Actions, and the shared ending. It does not prove physical
teachability or numerical balance.

The faction spread is high and the sampled policies never became AGI-eligible.
Those are open hypotheses for strategy improvement and controlled comparison,
not authority to alter rules. The declaration-readiness complexity counters
remain zero because no declaration occurred; a targeted eligibility strategy
study is required before those counters become informative.

## Surface audit and resulting deltas

- Canonical rulebook: no change; the optional-token rules were already printed
  in the frozen baseline.
- Semantic game graph: corrected Power-allocation copy to describe player
  choice instead of falsely claiming maximization; all structured balance
  numbers remain `hypothesis`.
- Machine-readable data: regenerated from that semantic source.
- Simulation engine: Build discounts and Market Access now expose explicit
  spend/keep choices, including affordability unlocked by the token. Immediate
  trades now apply the receiver's Safety cap when enumerating legal offers.
- Browser game and replay: inherit those same legal decisions from the shared
  selected-rules engine.
- Reference cards and player aids: no change.
- Tests: added optional Build-discount, optional Market Access, and asymmetric
  receiver-cap regressions.
- Playtest documentation: this receipt was added to preserve the result and
  its limits.
- Rule values: no change.

No commit is attributed to a simulation-motivated rules change because this
validation run selected no rule change.
