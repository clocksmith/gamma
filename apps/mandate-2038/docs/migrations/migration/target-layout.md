# Target Layout

This is the approved one-sweep layout. Every move is literal and recorded in
`path-map.json`; `versions/` is deliberately unchanged.

| Destination | Owns |
| --- | --- |
| `physical/` | Authored copy and specifications shipped with the baseline physical game. `physical/optional/` holds excluded optional modules. |
| `content/` | Shared authored runtime copy, the content graph, and numeric provenance. |
| `generated/` | Regenerated machine-readable runtime projections. |
| `web/` | Browser implementation and HTML templates. |
| `lab/` | Deterministic simulator, LLM policies, experiment runners, and contracts. |
| `tasks/` | Project and content command implementations. |
| `build/` | Rendered docs, galleries, and physical-kit build output. |
| `evidence/studies/` | Simulation, probability, and analysis evidence. |
| `evidence/playtests/` | Observed human-playtest evidence. |
| `release/` | The authored declaration for the current release. |
| `versions/` | Immutable historical release snapshots. |

## Atomic Contract

The compiler source-root policy changes with the moves: canonical sources may
live in `content/`, `physical/`, or `web/`. The migration runner rewrites live
references only. It excludes `versions/`, build outputs, and evidence files so
their historical path text remains reconstructable. Generated outputs are then
rebuilt and release artifacts are issued under a new version.
