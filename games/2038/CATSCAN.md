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

- One ruleset uses nineteen shared hexes (eighteen playable), five holding tracks,
  normal/equipped Orgs, numeric Customers and final-current-state Mandate. No
  selectable retired module or rules profile is exposed.
- Four Orgs per player kit, two starting; after an optional trade, choose one
  Org to stay or move one edge, then perform or deliberately skip the destination
  Action, even when affordable. Movement is independent of Action affordability.
  Skipping applies no Action costs, rewards, or Action-specific ability; placement,
  equipment, presence and ordinary Production remain. Turns resolve sequentially
  and Actions may repeat. CEOs are characters, not pieces.
- Research retains push-your-luck. Reputation replaces Trust, Scrutiny, and Systemic Risk. Recognized AGI is a final holding after Era IV Production and Reputation Review. The World Ending remains separate.
- User-selected mechanic revisions retain scenario placement and require an
  explicit design-decision receipt; they must not be labelled retained mechanics.
- The six Core Actions are the only Actions; a deliberate skip is not a seventh Action. Build equips exactly one owned Org; equipment travels with it and doubles production. Programs and use records are retired.
- The deck contains six Headlines per Era and reveals three per Era. Headlines finish all choices before sequential turns and leave no continuing modifiers.
- Each faction has one permanent ability and common scoring. Former abilities and Programs retain their fiction in lore-only records projected into the existing companion and references.
- Generated graph targets are never hand-edited. Authoring checks validate current
  sources; publication and kit freezing additionally verify immutable release identity.
- Game procedures and inventory prose have one authored home in `rules.md`;
  exact component effects remain in `components/`. Reference layouts may arrange
  sourced excerpts and fields, but cannot independently author rule paragraphs
  or numeric overrides. The complete Core Rules include map, components, and
  inventory. Supplementary extracts and the card catalog are internal review
  outputs, not required player books. Default public output is the rulebook,
  actual game components, browser game, and the optional selected narrative
  companion. The public companion never includes author notes or scenario metadata.
  Physical candidate files exclude authoring documents and deferred modules.
  Source provenance remains in the executable release content manifest.
  Generated review documents live in `dist/review/docs/` and render separately
  into `dist/site/review/`. Each kit keeps observer support under `observer/`.
  The content graph declares audiences and destinations and generates its own
  content provenance map; that map does not claim complete code dependencies.
- `world.md` is the sole authored source for world lore, World Endings, token
  microcopy, box copy, component creative prose, and scenario canon, projecting `dist/runtime/world-copy.json`
  and the selected `dist/docs/world-and-institutions.md` companion. It is an internal
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
  Physical state uses two-sided Org tokens, five holding cubes per player, nineteen hexes, cards and mats. AGI uses identity-card orientation; its upper-edge pointer marks final Mandate on the mat’s lower scale, without writing. No separate Facility, Customer, Generator, Venture or equipment pieces remain.
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
- Trading is an immediate, fixed-rate exchange requiring both participants’
  consent and available resources. No lasting contracts or hidden Venture state.
- Canonical rule changes update every affected authority and evidence surface together.

## Browser presentation boundary

`web/components/` renders the shared board, Org faces, player mats, holding cubes,
and card table from public match snapshots. Setup constructs the same match without
playing it. Views never draw cards, change holdings, or choose hidden deck order.
`web/app.js` owns lifecycle and legal decision submission; components own stable DOM
updates. Board/token and card proportions follow `physical/component-spec.md`;
responsive player mats prioritize readable tracks rather than screen millimeters.

## Acceptance

- Content, runtime, deterministic simulation, balance, and generated projections pass the package checks.
- Evidence: [package scripts](package.json), [content boundary checks](tasks/content/check-boundaries.mjs), and [project instructions](AGENTS.md).

## Non-goals

- Authorizing retail publication or treating exploratory player counts as promoted balance evidence.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.

Public hosting is owned by m3t4 at `https://m3t4.ai/mandate-2038/`. Gamma owns the build allowlist and all game sources.

Player equipment belongs to one of five colour-and-symbol kits independently of
six faction identities. Seat-based mechanical ownership remains authoritative.

- Reveal one objective from each Era packet at setup before the first Headline. All four remain visible without Era-by-Era replacement and score once from the final public table after Era IV Production, Reputation Review, and AGI recognition. History never affects scoring. Diagnostic telemetry is separate.

The historical 2026-10-09 smaller prototype retired Power, Trust milestones, and per-Era scoring. The shared-hex and 2026-10-12 selections below own the current movement, component, and objective-timing boundaries. Old sealed releases and evidence remain unchanged.

## Selected shared-hex simplification (2026-10-10)

The user selected a shared hex board and fewer components. This supersedes earlier
six-area, separate Facility, Customer-card, Action-card, Venture and simultaneous
selection requirements. Eighteen playable hexes surround one Era hex. Orgs stay or move
one edge, then perform or deliberately skip the destination Action, in Initiative
order; Actions may repeat. All Orgs produce; Build equips an Org by flipping its token. No separate
Facilities, upgrades, Ventures or Customer cards remain. Customers are numeric;
Mandate is calculated from visible state. Forty Training cards retain all ten
designs with four copies each and the existing shared draw/discard lifecycle.
Keep all unique lore and fictional institutions. Old releases remain immutable.

## Selected movement and setup-objective candidate (2026-10-12)

This selection deliberately supersedes mandatory destination Actions, movement
blocked by Action affordability, and one objective revealed at each Era start.
Resolve an optional trade, choose one Org and a legal stay or edge move, then
perform or deliberately skip the destination Action. Off-map entry and Organize’s
second-Org reassignment keep their existing exceptions. Skips do not grant an
Action or trigger Action-specific abilities; ordinary Production and equipment
remain intact. Reveal all four objectives at setup, one from each Era packet
before the first Headline; keep them visible and score each once from final state.

No control-income bonus is introduced. Research remains two Compute; all prices,
yields, faction abilities, lore, Initiative, eighty-two cards and 153 components
remain unchanged. The dated design decision records this new candidate, which
requires fresh balance and human-play evidence. No publication is authorized.
