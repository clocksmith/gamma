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
- The six Core Actions are the only selections. Build places up to one Facility, then one project from one assignment. Programs and use records are retired.
- The deck contains six Headlines per Era and reveals three per Era. Headlines finish all choices before selection and leave no continuing modifiers.
- Each faction has one permanent ability and common scoring. Former abilities and Programs retain their fiction in lore-only records projected into the existing companion and references.
- Generated graph targets are never hand-edited. Authoring checks validate current
  sources; publication and kit freezing additionally verify immutable release identity.
- Game procedures and inventory prose have one authored home in `rules.md`;
  exact component effects remain in `components/`. Reference layouts may arrange
  sourced excerpts and fields, but cannot independently author rule paragraphs
  or numeric overrides. The complete Core Rules include map, components, and
  inventory. Supplementary extracts and the card catalog are internal review
  outputs, not required player books. Default public output is the rulebook,
  actual game components, and browser game; the lore companion is optional.
  Physical candidate files exclude authoring documents and deferred modules.
  Source provenance remains in the executable release content manifest.
  Generated review documents live in `dist/review/docs/` and render separately
  into `dist/site/review/`. Each kit keeps observer support under `observer/`.
  The content graph declares audiences and destinations and generates its own
  content provenance map; that map does not claim complete code dependencies.
- `world.md` is the sole authored source for world lore, World Endings, token
  microcopy, box copy, component creative prose, and scenario canon, projecting `dist/runtime/world-copy.json`
  and the selected `dist/review/docs/world-and-institutions.md` companion. It is an internal
  author bible organized into setting/Eras, institutions and component copy,
  scenarios, endings, publishing copy, and editorial notes. Only explicitly selected
  passages and labeled player fields enter player projections. Ending conditions
  belong beside the mechanical outcome configuration in `components/game.json`.
  Era panels own their name, rules, and unlocks and reference Markdown epigraphs. Shared identities resolve
  from their existing owners. The overview preserves lore in accessible past-tense
  narration from 2038, without a character plot or mandatory events.
- The public homepage presents final game materials first and a separate Sources
  list below. Only explicitly selected mechanical and interface authoring files
  are published; the author world bible and internal review documents remain
  excluded. Release identity remains in build receipts.
- Physical specifications own form and state encoding; supported inventory
  prose is projected from the rulebook, not maintained in a second physical file.
- Every admitted lore situation has one structured Era placement, and every
  governed lore surface is bound exactly once with copy and mechanic receipts.
- World Markdown owns all scenario definitions and shared qualification policies.
  Components use one `loreRef` per record to select labeled player copy. Missing
  references, duplicate fields, and overrides fail compilation. Author notes and
  unselected lore are unavailable to player templates.
  Components retain mechanical text and own scenario
  references and surface-specific Era relations; Era panels retain `$era` metadata.
  Lore-only scenarios assert no dedicated mechanic or game binding. The Era-situation index and its
  source-path bindings are derived outputs; there are no separate copy overlays
  or hand-maintained binding registries. Editorial metadata never enters play.
- Only the public-playtest publication profile is deployable; internal-review
  artifacts remain local evidence.
- Playable counts are two through five. Six factions remain available choices; six-player requests are rejected. Historical evidence retains its original identity.
- Fictional identities remain fictional and simulated sessions remain labeled.
- Canonical rule changes update every affected authority and evidence surface together.

## Acceptance

- Content, runtime, deterministic simulation, balance, and generated projections pass the package checks.
- Evidence: [package scripts](package.json), [content boundary checks](tasks/content/check-boundaries.mjs), and [project instructions](AGENTS.md).

## Non-goals

- Authorizing retail publication or treating exploratory player counts as promoted balance evidence.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
