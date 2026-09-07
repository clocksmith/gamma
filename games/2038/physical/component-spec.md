# Component specification

This is the canonical physical-form record for Mandate 2038. It specifies what
players manipulate and how components express state. Mechanical quantities and
limits remain authoritative in `components/game.json`.

## Three component families

| Family | Job | Forms |
| --- | --- | --- |
| Cards, including flat chips | Explain rules, identify infrastructure, and record constructed projects | Standard cards, foldout aids, and compact durable cards/chips with printed identities |
| Agent position tokens | Locate institutional assignments | One consistent shape in each faction's colour; Agents only |
| Cubes | Count quantities and mark numerical tracks | Faction track and Mandate cubes; individual Scrutiny and Systemic Risk Audit cubes |

The map and faction boards are printed surfaces, not extra movable-piece
families. The Audit bag and shared writing pen are accessories. Current Era
and Initiative use labelled flat chips from the card family. Named gameplay
systems do not each require a different sculpted shape.

Use the same flat chip format for Facilities, Generators, and project records.
Printed symbols, faction colours, stable IDs, and pair numbers distinguish their
jobs. Never rely on colour alone. Shared Fusion uses a writable owner field,
set on construction; ordinary faction infrastructure prints its owner identity.

## Colour allocation

The six saturated RGB colours are reserved for player ownership. Every Agent, Facility, Generator, track cube, Scrutiny cube, and Mandate cube uses
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
| Era | Progressive rules unlock | Four panels printed on the Governance Board plus one Current Era chip | Chip position; panel text is open information |
| Faction board | One institution's dashboard | Board with five numbered tracks, one cube per track | Runway, Compute, Capability, Customers, and Trust |
| Player aid | Turn and scoring reminder | One three-panel foldout per faction tray | Three authored aid topics in one object |
| Agent | Persistent institutional assignment; one presence | Four identical faction-coloured position tokens, two starting | Assigned district; no separate movement procedure |
| Facility | Stationary institutional site | Flat faction-coloured chip, visibly numbered 1–4 | Stable Facility ID and district position |
| Generator | Stationary Power source | Flat faction-coloured chip with a distinct Power symbol | Its Energy-tile position selects the printed contract |
| Starting grid | Dedicated Power for Facility 1 | Identifier integrated into Facility 1 | Travels with that Facility |
| Scrutiny | Exposure in the Audit bag | Small faction-coloured cube | Owner supply or Audit bag |
| Systemic Risk | Shared Audit danger | Black cube matching Scrutiny's concealed feel | Audit bag or shared supply |
| Mandate | Public institutional score | One faction-coloured cube per faction | Shared Mandate-track position |
| Current Mandate ledger | Shared short-term counting aid and ending record | Writable panel integrated into Governance Board; one shared dry-erase pen | Revealed criterion, six faction values, Setup Collective Trust, and final resolution |
| AGI recognition | Public scored achievement | Final public ledger field | Paid declarations; no separate cards |
| Joint Venture / Mega-Cluster | Named shared project | Matched numbered flat chip pair | Host positions and pair number; Mega-Clusters have one owner |
| Initiative | Resolution and tie order | One labelled shared chip | Current holder |
| Fusion Demonstrator | Unique advanced-generation project | One shared flat chip with an owner field | Grid position and owner, or unbuilt supply |
| Quantum | Personal completed project | Permanent faction-board checkbox | Empty at setup, marked once constructed; no extra chip |
| Headline, Mandate, Action, project reference, Training | Information and choices | Cards | Face, orientation, and printed text; shared project references remain face up |
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
  chips and Agent position tokens without obscuring district text.

No district identity is printed in a ring well. Tile identity, visit text,
production, Facility spaces, category, and ordinary Generator contract remain
on the shuffled tile.

### Era and card field

Four printed Era panels run in order from I to IV. Each panel contains:

- Era name and strapline;
- ready / cycle / Audit summary;
- complete **New this Era** unlock text;
- one Headline-deck well;
- one Mandate-deck well; and
- three numbered Future Timeline positions.

One pre-Era Start bay holds the Current Era chip during setup. The chip then
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
- paid AGI recognitions;
- final institutional winner;
- AGI Recognized / Not Recognized;
- Open / Closed continuity; and
- World Ending.

The writable panel retains only state needed later. A resolved Mandate card
stays face up in its Era panel as public history; prior per-player criterion
values are not mechanically reused.

### Contract and supply field

Provide three project-reference positions, six numbered Joint Venture pair
bays, six numbered Mega-Cluster pair bays, one Fusion bay, and open labelled staging for shared components, the Audit bag, Scrutiny, and Systemic Risk. The board has no Power
Source reference slots. Emergency and Clean Infrastructure are printed on
their Energy tiles; Fusion is printed on its project reference.

### Retention and materials

Use recessed tile wells and low card rails. Low-profile magnets may retain the
Current Era and Initiative chips, Mandate cubes, and contract chips only if physical testing
shows that pieces remain easy to move and states remain unambiguous. Do not add
magnets merely as decoration or use them to encode an unprinted state.

The ledger must erase cleanly after repeated use without allowing casual table
contact to erase it. Its single fine-tip marker is shared and returns to a
labelled board or insert channel.

## Faction board and tray

Each faction board provides:

- faction identity, starts, and one permanent ability;
- five numbered tracks for Runway, Compute, Capability, Customers, and Trust,
  with one faction-coloured cube per track;
- three labelled Trust award checkboxes beside the Trust track: 2, 4, and 6;
- one permanent-for-the-game Quantum completed checkbox, empty at setup;
- six Core Action positions;
- supply wells for four Agents, Facilities, Generator, Scrutiny, and
  track and Mandate cubes; and
- the CEO name and character introduction, without a separate playing piece.

Tracks must expose exact integer positions with enough clearance to read the
occupied value. Recesses may resist accidental cube movement; captive sliders
are not required. Track cubes stay on their tracks and never enter the Audit bag.
Record balances by cube position, not by piles of currency. Caps are unchanged.

Each board and its faction-specific pieces, cards, and foldout aid are packed
as one labelled tray.

## State encoding

### Shared references and project chips

All three project references remain face up and readable for every player.
They explain requirements, costs, and benefits; they are never flipped to record
one institution's construction. Their shared supply is not a completion limit.

Mega-Cluster uses a matched chip pair on its two hosts. Print **Available** on
the supply face and **Built** on the host face, with the project name and matching
pair number visible on both. The Built face identifies the hosts' relationship;
the shared reference retains the complete production and connection rules.
Flip and place both chips together only after legal construction. Keep the Built
faces up if a host later loses Power; adjacency determines operation directly.

Fusion uses the same Available/Built convention on its single shared chip.
The Built face identifies Fusion and its owner at the occupied Generator slot.
Its reference remains visible to everyone. Uniqueness comes from the rules and
single shared supply, not a special shape. Quantum uses its existing personal
checkbox and needs neither a shared completion flip nor a personal duplicate card.

Facilities, Generators, and Joint Venture chips need no additional flip state.
If printed on both sides, repeat their identity and identifiers. Never put a
Facility and Generator on opposite faces of one chip: both can exist at once.
Do not introduce powered/unpowered faces. Ordinary shuffled decks retain
indistinguishable backs within each deck; their backs do not record completion.

### Current connections

Facility 1 carries an integrated starting-grid identifier and is always powered.
All other Facilities are connected by an own Generator on the same or an adjacent
district. Evaluate current positions; use no Power cubes, capacity tracks, or
retained allocation. A Mega-Cluster operates while both hosts remain adjacent
and connected.

### Permanent Trust award record

Print three writable checkboxes beside the Trust track, labelled 2, 4, and 6.
Premark every threshold at or below the faction's printed starting Trust: its
award is already included in starting Mandate. Mark each remaining box when
that threshold first scores. Never erase a marked box during the game, including
after a Trust loss, Audit, or Era change. Clear only for a new game, then restore
the starting marks. Use the shared dry-erase pen; no additional token is required.

Example: after Trust reaches four and scores, a fall to three leaves the four
box marked. Returning to four earns no second award. Keep these boxes physically
separate from the erasable Current Mandate ledger.

### Current Mandate ledger

When a Mandate is revealed, erase the previous faction rows and write the new
criterion and minimum. For a criterion that counts activity **this Era**, start
each faction at zero or No and update only that value. For a current-state
criterion, record the visible value at scoring. The printed Mandate remains the
qualification and scoring authority.

This one ledger replaces six four-Era score sheets. It retains the exact
short-lived value players would otherwise have to remember without preserving
unused historical arithmetic.

### AGI recognition

The final ledger records every paid AGI recognition, final Mandate winner, final
Collective Trust, and unresolved Systemic Risk. No Dossier cards or folio are
part of this candidate.

## Packaging and setup order

The insert has six faction trays, four Era packets, one Training deck well,
and one shared-component well. The Era I–IV packets hold `6 / 6 / 6 / 6`
Headlines respectively and three Mandates each.

Labels must match the board's Era numerals and canonical component names. Trays
and packets organize setup but create no hidden game state and need not remain
on the table.

## Physical constraints

- No component may conceal a district name, Facility slot, host relationship,
  connection, or piece count.
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
