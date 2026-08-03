# Content Source Map

Mandate 2038 keeps player-visible writing separate from mechanics and from
generated output. Edit the source that owns the kind of change you are making.

| Source | Owns | Do not put here |
| --- | --- | --- |
| `content/copy/` | Printable component, box, card, and player-aid copy | Numeric mechanics, IDs, or internal notes |
| `content/data/` | Stable IDs, timing, quantities, mechanics, and machine contracts | Flavor, tone rules, art briefs, or player-facing prose |
| `content/runtime/` | Browser labels, instructions, messages, simulation labels, and guide copy | Printed card copy or mechanical rules |
| `experimental/copy/` and `experimental/data/` | Deferred optional-module copy and mechanics | Baseline-game material |
| `content/graph.json` | Source-to-output declarations and semantic contexts | Authored game prose |
| `dist/` | Compiler-produced runtime JSON, printable documents, site pages, and kits | Any hand edits |

`content/copy/` is a sparse copy overlay: its IDs bind player-facing fields to
their mechanical record in `content/data/`. The compiler performs a fail-closed
keyed merge and rejects unknown identities or incompatible shapes.

| Copy source | Player-facing surface | Mechanical source |
| --- | --- | --- |
| `content/copy/world-copy.json` | Box, world primer, tokens, declarations, endings | `content/data/world-copy.json` |
| `content/copy/reference-cards.json` | Era cards and player aids | `content/data/reference-cards.json` |
| `content/copy/factions.json` | Faction boards and abilities | `content/data/factions.json` |
| `content/copy/game-config.json` | Actions, Eras, map, resources, Training, and Power | `content/data/game-config.json` |
| `content/copy/mandates.json` | Era Mandates | `content/data/mandates.json` |
| `content/copy/headlines.json` | Headline cards | `content/data/headlines.json` |
| `content/copy/escalations.json` | Escalation cards | `content/data/escalations.json` |
| `experimental/copy/*.json` | Deferred modules | matching `experimental/data/*.json` |

The player-readable document templates are `content/copy/core-rules.md` and
`content/copy/world-and-institutions.md`. They compile to `dist/docs/` and are
then rendered into the site reader. Begin a broad lore pass with
`content/copy/world-copy.json`; revise the world companion once the short
premise is settled; revise the rulebook for play instruction rather than lore
or internal rationale.

`content/player-copy-contract.json` records the player surface that consumes
each copy subtree. After changing content, run:

```bash
npm run content:build
npm run content:check
npm run content:validate
```

Never edit `dist/runtime/`, `dist/docs/`, `dist/site/`, or `dist/physical-kit/`
by hand.
