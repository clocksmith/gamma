# Physical specification

`physical/` owns the game’s physical embodiment: component form, state
encoding, and dimensions. It is neither player-facing copy nor
machine-enforced game data.

## Ownership

- `component-spec.md` defines what each component physically is, how a player
  reads its state at the table, and how the shared Governance Board organizes
  the map and public information.
- [Supported box inventory](../dist/docs/component-inventory.md) is generated
  from the `inventory` section of [rules.md](../rules.md). It separates Default
  requirements and deferred content. Edit the rulebook or
  its referenced component records, then build; there is no second authored inventory here.
- `governance-ledger.md` specifies the single writable board panel for the
  current Mandate, permanent Program-use history, Setup Collective Trust, and
  final public resolution. Read Power directly from current infrastructure positions.
- `production/` is reserved for printer-ready specifications, dielines, and
  vendor-facing files once those are deliberately approved.

The numeric rules limits remain in `components/game.json`. A physical
specification may describe a double-sided Facility or a track cube, but may
not quietly change how many Facilities a player owns, a resource cap, or a
legal game state. Change the owning component record or shared variable and
the affected rulebook procedure together.

`dist/physical-kit/` is generated frozen output. Do not edit it.

The authored Markdown specifications are included in the Documentation reader
by `npm run docs:html`. They remain physical specifications, not
`dist/docs/` projections, because they are not player-facing game copy.

`docs/manufacturing-and-publishing-study.md` is research and planning only.
It may discuss materials, suppliers, and costs, but it does not define the
game’s component format.
