# Mandate 2038 Semantic Content Graph

The content graph composes separately owned mechanics and player copy.

## Edit here

- `copy/` owns component, box, player-aid, and player-document prose.
- `copy/core-rules.md`, `copy/map-reference.md`,
  `copy/component-reference.md`, and `copy/card-reference.md` are the
  required Default Game Play Kit. `copy/advanced-play.md` and
  `copy/world-and-institutions.md` are separate Advanced Play and setting
  companions; `copy/rule-change-register.md` records the profile decisions.
- The JSON files under `data/` own mechanics and stable identity.
- `runtime/` owns browser UI, simulation, and player-strategy copy.
- `graph.json` declares every generated artifact.
- `player-copy-contract.json` binds every player-copy subtree to its actual
  box, document, component, or browser surface.

Player-copy JSON is a sparse overlay. IDs bind the prose to a mechanical
record; all other values in its `content` object are player-facing. The
compiler performs a fail-closed keyed merge and rejects unknown identities or
incompatible shapes. Every player-copy file must be declared by a generated
artifact.

## Player documents

Author a printable player document in `copy/<name>.md`, then declare a text
artifact in `graph.json` with target `dist/docs/<name>.md`. The compiler owns
that target. `npm run docs:html` discovers every Markdown projection in
`dist/docs/` and renders it into the Documentation reader and deployed review
site. Do not create or edit Markdown directly in `dist/docs/`. The artifact
declaration is the authoritative inventory of generated player documents.

References use deterministic `${path.to.value}` interpolation. The compiler
does not know any Mandate 2038-specific names or fields.

For example, changing:

```json
"advancedGeneration": "Fusion Demonstrator"
```

updates every source that contains:

```text
${terms.technology.advancedGeneration}
```

The stable mechanical IDs remain unchanged, so a lore rename does not alter
saved games, strategy policies, or balance unless the underlying mechanics are
also deliberately edited.

## Generate and verify

```bash
npm run content:build
npm run content:check
npm run content:validate
npm run content:lint:provenance
```

Never hand-edit generated files listed as targets in `graph.json`. The release
gate rejects drift between the semantic sources and those outputs.

The fictional institutions and fictional CEO characters are canonical. Stable
faction IDs remain internal compatibility keys, while player-facing names live
in `data/variables.json` and `copy/factions.json`.

Numbers with design or balance implications are registered in
`provenance/numbers.json` as either a hypothesis or evidence attributed to a
study receipt. The provenance lint prevents player-facing prose from presenting
an untested hypothesis as balanced evidence.

Numeric presentation follows the single writing contract in
[`docs/thematic-content-bible.md`](../docs/thematic-content-bible.md#numeric-typography).
The compiler preserves exact component rules text; it does not convert digits
to spelled-out words for individual projections.

An exact placeholder may resolve to a scalar, array, or object. A placeholder
embedded inside prose must resolve to a scalar. Unknown references, circular
references, duplicate targets, project-root escapes, and unresolved
placeholders fail closed.

`npm run content:check:boundaries` rejects player-copy fields without a
declared player surface, internal-only fields in mechanics or player copy, and
internal-only fields leaked into generated component data.
