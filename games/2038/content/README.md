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
| Lore, tone, research, World companion, deferred scenario backlog | [world.md](../world.md) |
| Browser labels and first-game tutorial | [ui.json](../ui.json) |
| Component form, dimensions, and state encoding | [physical/](../physical/README.md) |
| Rationale and open design questions | [docs/design-decisions.md](../docs/design-decisions.md) |

Each component record keeps its own mechanics and wording together. For example,
`components/headlines.json` holds each Headline's Era, timing, effect, title,
newswire, quote, and scenario notes. Change a quantity where it is defined;
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
- The `player-world` excerpt becomes World and Institutions: four concise
  Era overviews authored in `world.md`, followed by component-owned ending narratives.
  Era names and epigraphs resolve from Era panels, which contain no extended lore
  summaries. Writing notes and backlog follow the fiction in its source and stay
  outside the companion.
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

Generated outputs are not authoring locations. Existing reader routes, including
`/docs/core-rules.html`, `/docs/map-reference.html`, and
`/docs/component-inventory.html`, stay stable. `docs/` contains rationale,
evidence contracts, and research; it is not another player rulebook.

```bash
npm run build:all
npm test
npm run check
```

Builds remain local. Publication requires the separate deployment action.
`versions/current-release.json` declares current release identities;
`npm run game:release` records a new identity and refuses to overwrite historical
bundles. `versions/<version>/` and frozen `dist/physical-kit/` artifacts are evidence,
not current sources. Historical bundles retain their original source layout.

## Scenario notes

A component's `$scenario` defines its scenario once. Other records use
`{"$scenario": {"ref": "cheap-token-rebound"}}` to share it. Later expressions
also set `"eraRelation": "later-expression"`; Era cards own `$era` metadata.
The compiler generates the scenario index and
`dist/contracts/era-situation-ledger.json`. Never maintain source-path bindings
or copy overlays separately. Validation rejects missing or duplicate definitions,
unknown references, Era mismatches, omitted surfaces, and deferred scenarios
entering baseline play. `$scenario` and `$era` never enter playable JSON or
reference contexts.

Component IDs remain stable for saved games and strategy policies. Numeric
provenance remains in `content/provenance/numbers.json`; moving a source does
not turn a design hypothesis into balance evidence.
