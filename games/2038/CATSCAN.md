# CATSCAN: Mandate 2038

Parent: [Gamma games](../CATSCAN.md)

## Target

Deliver a coherent, replayable institutional strategy game whose authored rules, browser runtime, physical specification, and evidence agree.

## Authority

- Owns Mandate 2038 mechanics, authored copy, runtime projections, simulation, physical specification, balance evidence, and release records.
- Does not own manufacturing, publication, legal approval, or claims about real institutions.

## Scope

- Applies to Mandate 2038 mechanics, copy, projections, simulation, physical specification, and release evidence.

## Contracts

- Input: Complete records in `components/`, `world.md`, `rules.md`, `ui.json`, the build declarations in `content/graph.json`, and the [balance contract](lab/contracts/balance-contract.json).
- Output: Generated runtime, rules, site, physical-kit artifacts, and versioned evidence.

## Invariants

- Mandate 2038 has one ruleset. The map stays fixed; Power eligibility is local.
  Setup, components, references, runtime options, and publication expose no
  alternate rules mode. Retired mode selectors and module overrides are rejected.
- The current candidate uses four identical Agents per faction, two starting.
  Agents are persistent district assignments; CEOs remain characters, not pieces.
- Core selections commit available cards without advance affordability proofs.
  ReAct is Reason, Act, Observe; assignment is part of Act.
- Research has no universal Protection quantity. Power is a current-board local
  connection condition. Recognized AGI is a fixed Mandate achievement before the
  final Audit; it never overrides the Mandate winner. The World Ending remains separate.
- User-selected mechanic revisions retain scenario placement and require an
  explicit design-decision receipt; they must not be labelled retained mechanics.
- Generated graph targets are never hand-edited.
- Game procedures and inventory prose have one authored home in `rules.md`;
  exact component effects remain in `components/`. Reference layouts may arrange
  sourced excerpts and fields, but cannot independently author rule paragraphs
  or numeric overrides. Named excerpts produce the compact Core Rules and the
  detailed references without copying their source prose.
- `world.md` opens with the four concise Era overviews and ending references;
  concise editorial notes follow the fiction. Era panels own their name, epigraph,
  rules, and unlocks. Shared identities resolve from their existing owners.
  The overview preserves lore in accessible past-tense narration from 2038,
  without a character plot or mandatory events.
- Site home pages present one flat list of linked titles without section groups,
  subtitles, or duplicated navigation. Release identity remains in build receipts.
- Physical specifications own form and state encoding; supported inventory
  prose is projected from the rulebook, not maintained in a second physical file.
- Every admitted lore situation has one structured Era placement, and every
  governed lore surface is bound exactly once with copy and mechanic receipts.
- Component records own their scenario notes. The Era-situation index and its
  source-path bindings are derived outputs; there are no separate copy overlays
  or hand-maintained binding registries. Editorial metadata never enters play.
- Only the public-playtest publication profile is deployable; internal-review
  artifacts remain local evidence.
- Fictional identities remain fictional and simulated sessions remain labeled.
- Canonical rule changes update every affected authority and evidence surface together.

## Acceptance

- Content, runtime, deterministic simulation, balance, and generated projections pass the package checks.
- Evidence: [package scripts](package.json), [content boundary checks](tasks/content/check-boundaries.mjs), and [project instructions](AGENTS.md).

## Non-goals

- Authorizing retail publication or treating exploratory player counts as promoted balance evidence.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
