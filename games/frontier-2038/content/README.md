# M3T4 2038 Semantic Content Graph

Everything a player reads is authored under this directory. Files outside this
directory are generated projections or implementation code.

## Edit here

- `variables.json` owns shared names, terminology, and reusable facts.
- `game/` owns structured entities: cards, factions, tiles, strategies, world
  copy, UI copy, and simulation descriptions.
- `templates/` owns long-form rulebook and HTML composition.
- `graph.json` declares every generated artifact.

References use deterministic `${path.to.value}` interpolation. The compiler
does not know any M3T4-specific names or fields.

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
npm run content:validate:editions
npm run content:lint:provenance
```

Never hand-edit generated files listed as targets in `graph.json`. The release
gate rejects drift between the semantic sources and those outputs.

The named parody vocabulary is canonical. To prove that the institutional
alias is a text-only projection over identical mechanics, the edition gate
compiles and validates both:

```bash
node scripts/content/compile.mjs --edition=named --validate
node scripts/content/compile.mjs --edition=institutional --validate
```

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
