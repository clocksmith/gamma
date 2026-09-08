# Editing Mandate 2038

For human review of lore, voice, and rule clarity, begin with the
[creative writer's review guide](../components/README.md). It gives the reading
order and the questions to bring to each source.

Edit the sources below. The build produces one complete player rulebook, the
actual game components, and the browser game. Templates are internal assembly
code; writers do not need to navigate them to change prose or mechanics.

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

- All of `rules.md` becomes `dist/docs/core-rules.md`, including map instructions,
  component usage, and inventory. Nothing is split out of the player rulebook.
- Map, component, and inventory excerpts remain internal review outputs for
  focused inspection and compatibility with existing author tools. They are
  excluded from the public site and frozen player kit.
- Card and Board Reference is an internal catalog projecting component fields
  and selected rulebook passages. The final printed faces are the component masters.
  Duration and timing labels are selected from shared labels using the record's value.
- The optional World and Institutions companion uses an explicit layout selecting `world-setting` and
  `world-eras` passages, then the four compiled endings. The compiler exposes only
  those two world excerpts to templates. It never treats the whole author bible
  as a player document. Ending narratives live in Markdown; their conditions live
  in `components/game.json` under `worldEnding.$conditions`, beside the mechanical
  outcome configuration. They project into `world-copy.json`; the source-only map
  is stripped from game runtime data.
- The internal Rule Change Register combines the design ledger's `decision-register` introduction
  with the component change records.

`content/templates/` owns headings, field labels, and arrangement. It has no
independently authored rule paragraphs. The compiler and boundary check reject
unsourced paragraph text and numeric overrides; reference resolution rejects
missing fields, cycles, and invalid section markers. Layout checks do not judge
whether prose in its owning source describes the intended game correctly.

## Source and distribution map

[Generated content provenance](../dist/review/docs/content-provenance.md) lists
content inputs, destinations, and audiences from `content/graph.json` and the
references resolved during compilation. Shared variables are included when used.
This is content provenance, not a complete dependency graph: rendering code,
styles, image dependencies, and execution dependencies are outside its scope.
Run `npm run content:build` to regenerate it; `npm run content:check` rejects drift.

- `dist/docs/` contains the complete player rulebook.
- `dist/review/docs/` contains generated review catalogs, extracts, the optional
  lore companion, and the provenance map.
- `dist/site/docs/` and `dist/site/review/` render player and review documents
  separately. The local reader serves these at `/docs/` and `/review/`.
- `dist/firebase/public/` is the default player site; `dist/review/site/` is the
  separate local review package. Building it never replaces review sources.
- Each frozen physical kit keeps the rulebook, component masters, and printed
  track panel at its root. `observer/` contains the protocol, receipt schema, release
  evidence, and compiled reference data. Actual session observations remain in
  `evidence/playtests/`; kit creation never invents a completed receipt.

Templates and renderers assemble the declared outputs. Edit source content in
its owning files; do not maintain a second handwritten path diagram.

Generated outputs are not authoring locations. The public document list contains
only the complete rulebook; cards and boards are published as baseline component
masters. The browser uses the same compiled records. Internal review exposes the
supplementary extracts, card catalog, optional lore companion, and design records.
They do not appear in the default player package. The physical candidate bundle
contains the complete rulebook and printed Governance Board tracks. Authoring
sources remain bound by the release content manifest, separately from player copy.
Historical releases and frozen kits keep their original documents.

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
