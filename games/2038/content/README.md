# Editing Mandate 2038

For human review of lore, voice, and rule clarity, begin with the
[creative writer's review guide](../components/README.md). It gives the reading
order and the questions to bring to each source.

Start here to find a source. The printed play kit has several documents, but
those documents are generated views of the sources below.

| Change | Author here |
| --- | --- |
| Game procedures, map setup/control, component states, inventory prose | [rules.md](../rules.md) |
| A card, faction, action, ending, or district's exact effect | [components/](../components/) |
| Board geometry and component supply records | [components/game.json](../components/game.json) |
| Shared terminology and numeric variables | [data/variables.json](data/variables.json) |
| Lore, endings, token/box copy, research, and all scenario definitions | [world.md](../world.md) |
| Browser labels and first-game tutorial | [ui.json](../ui.json) |
| Component form, dimensions, and state encoding | [physical/](../physical/README.md) |
| Rationale and open design questions | [docs/design-decisions.md](../docs/design-decisions.md) |

Each component record owns its mechanics, rule wording, title, and scenario
references. One `loreRef` selects its labeled player copy in the internal `world.md` bible.
The resolver merges that copy into the complete generated record and removes
`loreRef`. It rejects missing IDs and fields authored in both places. No parallel
copy file or overlay is maintained. Change a quantity where it is defined;
references such as `${content.gameConfig.playerSupply.facilities}` reuse that
value in prose. Simulation and strategy copy remain in `content/runtime/`;
deferred modules remain in `experimental/`.

## References are layouts

`content/graph.json` declares all sources and generated targets. Its `excerpts`
map exposes named Markdown sections, such as `<!-- map:start -->` through
`<!-- map:end -->` in `rules.md`. A reference layout includes that passage with
`${excerpts.rules.map|headings-up}`. The formatter promotes heading levels for a
standalone document; it changes no prose.

- `rules.md` becomes `dist/docs/core-rules.md`. The graph's `excludeSections`
  keeps detailed map and component sections out of this compact booklet.
- The `map` and `components` excerpts become Map Reference and Component Reference.
  The nested `inventory` excerpt also produces Supported Box Inventory.
- Card and Board Reference projects component fields and selected rulebook passages.
  Duration and timing labels are selected from shared labels using the record's value.
- World and Institutions uses an explicit layout selecting `world-setting` and
  `world-eras` passages, then the four compiled endings. The compiler exposes only
  those two world excerpts to templates. It never treats the whole author bible
  as a player document. Ending narratives live in Markdown; their conditions live
  in `components/game.json` under `worldEnding.$conditions`, beside the mechanical
  outcome configuration. They project into `world-copy.json`; the source-only map
  is stripped from game runtime data.
- Rule Change Register combines the design ledger's `decision-register` introduction
  with the component change records.

`content/templates/` owns headings, field labels, and arrangement. It has no
independently authored rule paragraphs. The compiler and boundary check reject
unsourced paragraph text and numeric overrides; reference resolution rejects
missing fields, cycles, and invalid section markers. Layout checks do not judge
whether prose in its owning source describes the intended game correctly.

## Build paths

```text
rules.md / world.md / components/ / ui.json / content/data/
  + content/graph.json + reference layouts
  -> tasks/content/compile.mjs
  -> dist/runtime/ (JSON consumed by lab/ and web/)
  -> dist/docs/ (generated player documents)
  -> dist/site/ (base site templates)

dist/docs/ + docs/*.md + physical/component-spec.md
  -> tasks/render-docs.mjs -> dist/site/docs/ (Documentation reader)

runtime content -> tasks/render-gallery.mjs -> dist/site/ (Gallery)
dist/site/ + public-playtest allowlist -> dist/firebase/public/
dist/site/ + internal-review profile -> dist/review/
```

Generated outputs are not authoring locations. The former thematic-content-bible
projection is retired; writing guidance is read directly in `world.md`. Core Rules
and World and Institutions retain distinct procedural and setting purposes. Existing reader routes, including
`/docs/core-rules.html`, `/docs/map-reference.html`, and
`/docs/component-inventory.html`, stay stable. `docs/` contains rationale,
evidence contracts, and research; it is not another player rulebook.

```bash
npm run build:all
npm test
npm run check
```

Builds remain local. `npm run check` validates the current authoring tree without
requiring a new immutable release for each edit. `npm run game:release:verify`
verifies frozen identity; public site generation and physical-kit freezing call
that verifier before producing releasable output. Publication requires the
separate deployment action.
`versions/current-release.json` declares current release identities;
`npm run game:release` records a new identity and refuses to overwrite historical
bundles. `versions/<version>/` and frozen `dist/physical-kit/` artifacts are evidence,
not current sources. Historical bundles retain their original source layout.

## Scenario notes

The marked `scenario-canon` section in `world.md` defines every scenario once,
with five required fields: ID, Era, policy, public benefit, and institutional
consequence, followed by ordinary narrative paragraphs. Concepts default to the
heading and causal threads to none; specify either only when needed. Seven shared
policies in the same Markdown source supply disposition, mechanic qualification,
and deployment profiles without repeating those declarations on every record. Components use
`{"$scenario": {"ref": "cheap-token-rebound"}}` to share it. Later expressions
also set `"eraRelation": "later-expression"`; Era cards own `$era` metadata.
The compiler generates the scenario index and
`dist/contracts/era-situation-ledger.json`. Never maintain source-path bindings
or copy overlays separately. Validation rejects missing or duplicate definitions,
unknown references, Era mismatches, omitted surfaces, and deferred scenarios
entering baseline play. Lore-only entries carry no dedicated game binding and do
not assert implemented mechanics. The former combined water/weather entry is split
so its adopted and deferred dispositions remain distinct. `$scenario` and `$era` never enter playable JSON or
reference contexts.

Component IDs remain stable for saved games and strategy policies. Numeric
provenance remains in `content/provenance/numbers.json`; moving a source does
not turn a design hypothesis into balance evidence.

## A component's lore reference

A mechanical component can contain `"loreRef": "headline-ten-dollar-intelligence"`.
Its actual player copy lives once in `world.md`:

```markdown
### The Token Price Reaches Zero

<!-- lore-headline-ten-dollar-intelligence:start -->

#### Newswire

[The authored newswire paragraph.]

#### Quote

[The authored quotation.]

#### Author notes

[Optional context for writers; excluded from compiled copy.]

<!-- lore-headline-ten-dollar-intelligence:end -->
```

Allowed labels map directly to runtime fields: Flavor text, Newswire, Quote,
Motto, Introduction, Agi declaration, Strapline, Public claim, and Tagline.
Labels must be unique and player fields nonempty. Unknown labels fail instead
of silently publishing an author note or dropping intended player copy.
A second component may reuse the same entry; each use is discovered from its
record. Scenario links remain separate because several different cards can
express one scenario with different text and mechanics.

Run `npm run build:all` to resolve runtime JSON, books, and gallery cards. Change
copy once and rebuild to update every consumer. `npm test` exercises propagation,
missing references, override rejection, and exclusion of internal sentinel text.
Historical release bundles remain evidence of their original source layout.
