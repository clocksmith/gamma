# Editing Mandate 2038

| Change | Author here |
| --- | --- |
| Base lore, tone, research, World companion | [world.md](../world.md) |
| How to play | [rules.md](../rules.md) |
| Advanced Play | [advanced.md](../advanced.md) |
| A card, faction, action, or ending | [components/](../components/) |
| Browser labels and first-game tutorial | [ui.json](../ui.json) |

Each component record contains its own wording and mechanics. For example,
`components/headlines.json` contains each Headline's Era, timing, effect,
title, newswire, quote, and scenario notes together. Shared terminology and
counts remain in `content/data/variables.json`; simulation and strategy copy
remain in `content/runtime/`. Deferred modules live in `experimental/components/`.

## Scenario notes

A component's `$scenario` object defines its scenario once. Other components
can use `{"$scenario": {"ref": "cheap-token-rebound"}}` to share that definition.
An explicitly later expression also sets `"eraRelation": "later-expression"`.
The four Era cards own `$era` metadata. Unadopted scenarios live in the marked
`scenario-backlog` section of `world.md`.

The scenario index is generated from those records. Do not write source paths,
surface IDs, or reverse binding lists by hand. Validation rejects missing or
duplicate definitions, unknown references, Era mismatches, omitted surfaces,
and deferred scenarios entering baseline play. `$scenario` and `$era` never
enter runtime JSON, printed components, or template contexts.

## Build

```bash
npm run build:all
npm test
npm run check
```

`content/graph.json` declares inputs, outputs, and deployment profiles.
`content/templates/` assembles the card, map, component, and rule-change
references. The marked `player-world` section of `world.md` becomes the World
companion; editorial guidance and backlog remain outside that player document.

The compiler resolves `${terms.…}` and `${content.…}` references and generates
`dist/runtime/`, `dist/docs/`, and site templates. It also generates
`dist/contracts/era-situation-ledger.json`. Never hand-edit these outputs.
The docs and gallery renderers create their HTML from the generated content.

Component IDs remain stable for saved games and strategy policies. Numeric
provenance remains in `content/provenance/numbers.json`; moving a source does
not turn a design hypothesis into balance evidence. Historical releases under
`versions/` retain their original source layout and are never migrated.
