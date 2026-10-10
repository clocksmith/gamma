# Physical specification

`physical/` owns the game’s physical embodiment: component form, state
encoding, and dimensions. It is neither player-facing copy nor
machine-enforced game data.

The selected forms are Customer cards, double-sided Facility cards, Agent tokens,
faction identity cards, six shared action areas, and five interchangeable player
mats. Kit colour and symbol identify ownership independently of faction.
Four numerical tracks use cubes. The Governance Board retains four objectives
for final scoring and an AGI recognition space.
## Ownership

- `component-spec.md` defines what each component physically is, how a player
  reads its state at the table, and how the shared Governance Board organizes
  the map and public information.
- The supported box inventory is included in the complete
  [rulebook](../dist/docs/core-rules.md). An internal
  [inventory extract](../dist/review/docs/component-inventory.md) selects that same
  `inventory` section of [rules.md](../rules.md). It separates Default
  requirements and deferred content. Edit the rulebook or
  its referenced component records, then build; there is no second authored inventory here.
- `governance-tracks.md` specifies the printed cube-track panel for the
  four resource tracks, AGI recognition, and final public resolution.
- `production/` is reserved for printer-ready specifications, dielines, and
  vendor-facing files once those are deliberately approved.

The numeric rules limits remain in `components/game.json`. A physical
specification may describe a double-sided Facility or a track cube, but may
not quietly change how many Facilities a player owns, a resource cap, or a
legal game state. Change the owning component record or shared variable and
the affected rulebook procedure together.

`dist/physical-kit/` is generated frozen output. Do not edit it. The rulebook,
component masters, and printed track panel sit at the kit root; protocols, receipt
schemas, release manifests, and compiled reference data live under `observer/`.

The authored Markdown specifications are included in the review reader
by `npm run docs:html`. They remain physical specifications, not
`dist/docs/` projections, because they are not player-facing game copy.

`docs/manufacturing-and-publishing-study.md` is research and planning only.
It may discuss materials, suppliers, and costs, but it does not define the
game’s component format.
