# Component specification

This is the canonical physical-form record for Mandate 2038. It specifies what
players manipulate and how components express state. Mechanical quantities and
limits remain authoritative in `components/game.json`.

## Colour allocation

The six saturated RGB colours are reserved for player ownership. Every CEO,
Team, Facility, Generator, Scrutiny cube, Mandate marker, and ballot accent uses
its faction's colour.

| Faction | Ownership colour | Hex value |
| --- | --- | --- |
| Dovetalis Labs | Red | `#ff003c` |
| Loopfold AI | Blue | `#0066ff` |
| Mirevanta Works | Green | `#00e676` |
| Kestralyn | Magenta | `#ff00d4` |
| Orisonix | Cyan | `#00e5ff` |
| Corthaven | Yellow | `#ffea00` |

Shared components use black, white, clear or translucent material, or metallic
gold, silver, and bronze. Finish never creates an additional rules state.

## Selected prototype vocabulary

| Gameplay object | Physical role | Selected form | State encoding |
| --- | --- | --- | --- |
| Governance Board | Shared map frame and public dashboard | One rigid folding board with tile wells, card rails, tracks, and a writable panel | Map geometry, Era, Timeline, Mandate, Initiative, contracts, current criterion, and final resolution |
| Era | Progressive rules unlock | Four panels printed on the Governance Board plus one Current Era marker | Marker position; panel text is open information |
| Faction board | One institution's dashboard | Thick dual-layer board with six captive sliders | Runway, Compute, Capability, Customers, Trust, and Research Protection |
| Player aid | Turn and scoring reminder | One four-panel foldout per faction tray | Four authored aid topics in one object |
| CEO | Movable acting piece; one presence | Large faction-coloured pawn | District position |
| Team | Movable acting piece; one presence | Small faction-coloured pawn | District position |
| Facility | Stationary institutional site | Faction-coloured node, visibly numbered 1–4 | Stable Facility ID and district position |
| Generator | Stationary Power source | Distinct faction-coloured power node | Its Energy-tile position selects the printed contract |
| Starting grid | Dedicated Power for Facility 1 | Identifier integrated into Facility 1 | Travels with that Facility |
| Scrutiny | Exposure in the Audit bag | Small faction-coloured cube | Owner supply or Audit bag |
| Systemic Risk | Shared Audit danger | Black piece matching Scrutiny's concealed feel | Audit bag or shared supply |
| Mandate | Public institutional score | One faction-coloured marker per faction | Shared Mandate-track position |
| Program marker | Per-Era exceptional action allowance and once-per-game use | Two faction-coloured markers per player | Available beside faction board or committed on one shared Program card |
| Power allocation | Latest completed Production state | Thirty-six shared silver cubes | One on each powered Facility and one per satisfied Mega-Cluster demand until next Allocate |
| Current Mandate ledger | Shared short-term counting aid and ending record | Writable panel integrated into Governance Board; one shared marker | Revealed criterion, six faction values, Setup Collective Trust, and final resolution |
| AGI Dossier | Hidden Era-by-Era commitment | Four Era-labelled cards per faction, symmetrical backs | Face-down Commit or Hedge orientation |
| Temporary Compute | Allocation Window capacity | Two distinct shared tokens | Current holder; returned at cycle end |
| Joint Venture / Mega-Cluster | Named shared project | Matched numbered token pair | Host positions and pair number; Mega-Clusters have one owner |
| Initiative | Resolution and tie order | One shared marker | Current holder |
| Fusion Demonstrator | Unique advanced-generation project | One shared marker | Grid position or unbuilt supply |
| Link — Advanced | Facility connection to its owner's Network | Faction-coloured connector token | Attached to one Facility |
| Realignment — Advanced | Secret jurisdiction motion | One square four-way ballot per faction | Edge aimed toward board center while face down |
| Volatility — Advanced | Two-result Headline resolver | One ordinary six-sided die | Printed result mapping |
| Headline, Mandate, Action, Program, Training | Information and choices | Cards | Face, orientation, markers, and printed text |
| Ordinary Power contract | Generator rules at point of construction | Printed in the Grid and Renewable tile visit boxes | Tile identity; no separate reference card |

## Governance Board

The Governance Board is the table's public control surface. It organizes the
modular map and shared state without replacing district tiles, faction boards,
decks, or physical pieces.

### Map field

- One fixed Frontier well at center.
- Six inner operational-ring wells.
- Twelve outer public-ring wells forming the complete radius-two hexagon.
- Clear edge adjacency and clockwise direction.
- Enough clearance for acting pieces, two Facilities, Generators, contract
  tokens, Links, and retained Power cubes without obscuring district text.

No district identity is printed in a ring well. Tile identity, visit text,
production, Facility spaces, category, and ordinary Generator contract remain
on the shuffled tile.

### Era and card field

Four printed Era panels run in order from I to IV. Each panel contains:

- Era name and strapline;
- ready / Program-marker / cycle / Audit summary;
- complete **New this Era** unlock text;
- one Headline-deck well;
- one Mandate-deck well; and
- three numbered Future Timeline positions.

One pre-Era Start bay holds the Current Era marker during setup. The marker then
moves along the four panels. The panels replace four Era
cards; full Era fiction remains in the Card and Board Reference and World and
Institutions companion.

### Public-state field

The board includes:

- the shared Mandate track;
- one Initiative position;
- a Current Mandate ledger with spaces for the revealed name, criterion,
  minimum, and one value per faction;
- Setup Collective Trust;
- final Collective Trust and unresolved Systemic Risk;
- eligible Dossier claims and their strengths;
- provisional and final institutional winner;
- AGI Emerges / Does Not Emerge;
- Open / Closed continuity; and
- World Ending.

The writable panel retains only state needed later. A resolved Mandate card
stays face up in its Era panel as public history; prior per-player criterion
values are not mechanically reused.

### Contract and supply field

Provide six shared Program-card positions, six numbered Joint Venture pair
bays, six numbered Mega-Cluster pair bays, one Fusion bay, and open labelled staging for Power cubes, Temporary
Compute, the Audit bag, Scrutiny, and Systemic Risk. The board has no Power
Source reference slots. Emergency and Clean Infrastructure are printed on
their Energy tiles; Fusion is printed on its shared Program card.

### Retention and materials

Use recessed tile wells and low card rails. Low-profile magnets may retain the
Current Era, Initiative, Mandate, and contract markers only if physical testing
shows that pieces remain easy to move and states remain unambiguous. Do not add
magnets merely as decoration or use them to encode an unprinted state.

The ledger must erase cleanly after repeated use without allowing casual table
contact to erase it. Its single fine-tip marker is shared and returns to a
labelled board or insert channel.

## Faction board and tray

Each faction board provides:

- faction identity, starts, scoring exception where applicable, and two
  programs with exact unlock Era and timing;
- six captive sliders for Runway, Compute, Capability, Customers, Trust, and
  Research Protection;
- two Program-marker wells and a compact once-per-game Program-use reminder;
- six Core Action positions;
- supply wells for the CEO, Teams, Facilities, Generator, Scrutiny, and
  Mandate marker; and
- a nearby Dossier filing edge with an unambiguous direction toward the board
  center.

Captive sliders must expose exact integer positions and resist accidental
movement. They replace loose track markers; they do not alter caps. Advanced
Network connectivity is read from the shared map and has no slider.

Each board and its faction-specific pieces, cards, and foldout aid are packed
as one labelled tray. Advanced Link tokens and the Realignment ballot stay in
the separate Advanced module so Default setup never asks a new player to sort
unused systems.

## State encoding

### Latest Production snapshot

Power cubes do two jobs without changing meaning: they resolve the current
Allocate step and remain as the latest completed Production snapshot.

1. At the next Allocate step, collect every cube from the previous snapshot.
2. Place one cube on each powered Facility.
3. Place one cube on a Mega-Cluster for each additional unit of demand it
   receives.
4. Leave all those cubes in place through Produce, Partner, Dossier, Audit,
   Mandate, later turns, and any intervening Headline.

A built Facility without a cube is offline. The retained cubes govern
powered-Facility Mandates and Headlines, the Deployment Dossier, and final
offline penalties. They are not a permanent Power contract and are not carried
through Realignment as a fresh eligibility calculation. They travel with their
marked hosts as the previous snapshot; the next Production recalculates and
replaces them.

### Current Mandate ledger

When a Mandate is revealed, erase the previous faction rows and write the new
criterion and minimum. For a criterion that counts activity **this Era**, start
each faction at zero or No and update only that value. For a current-state
criterion, record the visible value at scoring. The printed Mandate remains the
qualification and scoring authority.

This one ledger replaces six four-Era score sheets. It retains the exact
short-lived value players would otherwise have to remember without preserving
unused historical arithmetic.

### Dossier cards and folio gate

The supported form remains four face-down Dossier cards per faction. Their
symmetrical backs conceal Commit / Hedge orientation, and players may not
inspect filed cards before the Era IV reveal.

A reusable Dossier folio is a gated prototype, not a selected replacement. It
may replace the cards only after a blind physical test proves all of the
following:

- the owner and opponents cannot read filed choices;
- each Era's orientation survives movement, bumps, and storage;
- prior choices cannot be reinspected while filing a later Era;
- simultaneous final reveal is complete and unambiguous; and
- setup and handling are measurably simpler than four cards.

Until every condition passes, manufacture and rules counts remain twenty-four
Dossier cards.

### Realignment ballot

The Advanced ballot is rotationally symmetric on its back. Its face prints one
choice on each edge: Consolidate Core, Expand Periphery, Counter-Cycle, and
Pass. All players orient and place their ballots face down before anyone
reveals. Pass is equivalent to naming no motion. The physical redesign replaces
three cards per player with one and changes no plurality or tie rule.

## Packaging and setup order

The insert has six faction trays, four Default Era packets, one Training deck
well, one shared-component well, and one clearly separated Advanced module.
The Era I–IV packets hold `5 / 4 / 3 / 4` Default Headlines respectively and
three Mandates each. The Advanced module holds its eight badged Headlines
sorted `1 / 2 / 3 / 2` by Era alongside Links, ballots, and the Volatility die.

Labels must match the board's Era numerals and canonical component names. Trays
and packets organize setup but create no hidden game state and need not remain
on the table.

## Physical constraints

- No component may conceal a district name, Facility slot, host relationship,
  Power cube, or piece count.
- Every state required during a turn must be visible without a private note.
- Shared contracts require durable matching identifiers.
- Scrutiny and Systemic Risk must be indistinguishable by touch while concealed
  in the opaque Audit bag and immediately distinguishable by colour or print
  after drawing. Use the same size, shape, material, and weight.
- Facility numbers and the starting-grid identity remain attached when a
  Facility moves.
- Do not add miniatures, wheels, selectors, or duplicate reference components
  merely for theme. Neural-network language should come from node, connection,
  and illumination graphics, not extra game state.
