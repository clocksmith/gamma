# Physical Playtest Copy

This directory is the canonical component-specific copy source for the
baseline physical playtest candidate. It excludes browser UI, simulation
prompts, and deferred modules.

Shared terminology is in `variables.json` in this directory, so a renamed
resource, action, or identity stays consistent across physical and digital
projections. All physical component-specific prose lives here.

| File | Physical surface |
| --- | --- |
| `core-rules.md` | Baseline How to Play and complete mechanical reference |
| `world-and-institutions.md` | Setting, tone, Era fiction, and ending narratives |
| `content-manifest.json` | Baseline component inventory and copy status |
| `variables.json` | Canonical names, terms, and shared game facts |
| `game-config.json` | Core Actions, Training deck, map, resources, and components |
| `factions.json` | Faction boards and abilities |
| `headlines.json` | Headline cards |
| `mandates.json` | Round Mandates |
| `reference-cards.json` | Era cards and player aids |
| `wild-actions.json` | Wild Action cards |
| `world-copy.json` | Box, world, token, declaration, and ending copy |
| `optional/tactics-rules.md` | Deferred Tactic setup, timing, and card-rule projection |

Run `npm run content:build` after editing. The compiler projects these files
to the rulebook and runtime data; do not edit those generated outputs directly.
