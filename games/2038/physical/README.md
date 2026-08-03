# Physical specification

`physical/` owns the game’s physical embodiment: component form, state
encoding, dimensions, and box inventory. It is neither player-facing copy nor
machine-enforced game data.

## Ownership

- `component-spec.md` defines what each component physically is and how a
  player reads its state at the table.
- `component-inventory.md` is the human-readable supported-box inventory. It
  separates Default Game requirements, the Advanced Play addendum, and
  excluded deferred content without selecting an unresolved physical format.
- `production/` is reserved for printer-ready specifications, dielines, and
  vendor-facing files once those are deliberately approved.

The numeric rules limits remain in `content/data/game-config.json`. A physical
specification may describe a double-sided Facility or a track cube, but may
not quietly change how many Facilities a player owns, a resource cap, or a
legal game state. Make that rules change in `content/data/` first.

`dist/physical-kit/` is generated frozen output. Do not edit it.

The two authored Markdown specifications are included in the Documentation
reader by `npm run docs:html`. They remain physical specifications, not
`dist/docs/` projections, because they are not player-facing game copy.

`docs/manufacturing-and-publishing-study.md` is research and planning only.
It may discuss materials, suppliers, and costs, but it does not define the
game’s component format.
