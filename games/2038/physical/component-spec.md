# Component specification

This is the canonical physical-form record for Mandate 2038. It specifies
what players manipulate and how a component expresses state. It does not
replace mechanical quantities or rules in `content/data/game-config.json`.

## Colour allocation

The six saturated RGB colours are reserved for player ownership. Every CEO,
Team, Facility, Generator, Scrutiny cube, and player track
marker uses its faction's colour. No shared or neutral component uses one of
these six colours.

| Faction | Ownership colour | Hex value |
| --- | --- | --- |
| Dovetalis Labs | Red | `#ff003c` |
| Loopfold AI | Blue | `#0066ff` |
| Mirevanta Works | Green | `#00e676` |
| Kestralyn | Magenta | `#ff00d4` |
| Orisonix | Cyan | `#00e5ff` |
| Corthaven | Yellow | `#ffea00` |

Shared and neutral components use black, white, clear/translucent material,
or metallic gold, silver, and bronze. Gold can denote a singular public
distinction, silver ordinary shared infrastructure, and bronze a persistent
shared project. Material or finish never creates an additional rules state.

## Selected prototype vocabulary

| Gameplay object | Physical role | Current prototype form | State encoding |
| --- | --- | --- | --- |
| Shared Governance Board | Shared public dashboard and modular map frame | Rigid foldable board with recessed tile wells, card rails, and marked public-state bays | Tile positions, Era order, Headline history, Mandate, Initiative, contracts, Power references, and supply staging |
| Faction board | One player’s dashboard | Dedicated board or thick player mat | Printed tracks, ability, action slots, and faction supply areas |
| CEO | Movable acting piece; two presence | Large faction-coloured pawn | Position on a district |
| Team | Movable acting piece; one presence | Small faction-coloured pawn | Position on a district |
| Facility | Stationary institutional site | Faction-coloured building/node piece visibly numbered 1–4 | Stable printed Facility ID and board position |
| Generator | Stationary Power source | Distinct faction-coloured power-node piece | Position; its Energy district determines clean or emergency source |
| Scrutiny | Exposure in the Audit bag | Small faction-coloured cube | In owner supply or Audit bag |
| Systemic Risk | Shared Audit danger | Black Audit piece with the same concealed feel as Scrutiny | Audit bag or shared supply |
| Customer | Acquired demand | One marker on the faction-board Customer track | Customer track position from zero through five |
| Runway, Compute, Capability, Trust, and Safety | Scalar player state | Tokens or markers on the faction board | Count or track position |
| Mandate | Public score | One marker per faction on the shared Mandate track | Shared-track position |
| Starting grid | Dedicated Power assigned to the first Facility | Integrated identifier on that first Facility | Attached / moved with its Facility |
| Escalation | Permission to select an Escalation | One marker on the faction-board Escalation track | Zero to two currently available; unused permission expires each Era |
| AGI Dossier | A hidden Era-by-Era institutional commitment | Four Era-labelled cards per faction with symmetrical backs | Face-down Commit / Hedge orientation; revealed together before the final Audit |
| Prediction token | A claimant's contribution to final AGI resolution | Existing faction-coloured Scrutiny cube | Added only after Audit state is recorded; never counts as Scrutiny |
| Joint Venture / Mega-Cluster | A named shared project | Matched numbered token pair | Both host positions and pair number |
| Initiative | Current resolution and tie order | One shared marker | Current holder |
| Fusion Demonstrator | The unique advanced-generation project | One shared project marker | Grid position / unbuilt |
| Link — Advanced Play | A Facility’s connection to its owner’s Network | Faction-coloured connector token | Attached to one Facility |
| Network capacity — Advanced Play | Pooled connected Power | Player-board track marker | Current connected capacity |
| Realignment — Advanced Play | One secret jurisdiction motion | Three ballot cards per player | Selected face down, then revealed |
| Volatility — Advanced Play | Resolves a two-result Headline | One ordinary six-sided die | Printed result mapping |
| Era, Headline, Mandate, Action, Escalation, Training, and Power Source | Information and choices | Cards | Face, orientation, and printed text |
| Production and Era score sheet | Public retained state for scoring and later effects | One laminated sheet and fine-tip dry-erase marker per faction | Four Era rows plus one clearly boxed latest Production snapshot |

## Shared Governance Board

The shared Governance Board is the table’s public control surface. It gives the
modular map a stable frame and gives Era progression, public scoring, contracts,
and retained Headline history dedicated positions. It does not replace the 13
district tiles, faction boards, card decks, or Production and Era score sheets.

### Board zones

| Zone | Physical provision | What remains visible there |
| --- | --- | --- |
| Modular map frame | One Frontier well, six inner-ring wells, and six outer-ring wells | The 13 district tiles and all pieces currently occupying them |
| Era rail | Four upright Era-card positions | The current Era, prior Era cards, and each Era’s Headline deck position |
| Headline row | One deck/discard position beneath each Era | The current Headline and resolved Headlines for that Era |
| Public-state rail | Mandate track and Initiative position | Every faction’s public Mandate and the current resolution order |
| Future Timeline | Twelve numbered or sequential card positions | Every resolved Headline, kept face up after resolution |
| Contract bays | Six matched Joint Venture bays and six matched Mega-Cluster bays | Active numbered pairs, host relationships, and lead-side indicators |
| Advanced-generation bay | One Fusion Demonstrator position and three Power Source reference positions | Whether Fusion is unbuilt or constructed and the available Power contracts |
| Audit and supply staging | Clearly labelled open areas beside the Audit bag | Scrutiny, Systemic Risk, unused contract pairs, and shared markers before use |

The operational and public ring wells must remain visually distinct, but no
district name is permanently assigned to a well. The six operational tiles are
shuffled among the inner wells and the six public tiles among the outer wells.
The board’s geometry supplies the map; the tiles supply the district identity,
visit bonus, Facility spaces, production, and control value.

### Retention and materials

Use recessed wells for district tiles and card rails or shallow wells for Era
cards and Headlines. Low-profile magnetic retention may be used for the
Initiative marker, Mandate markers, contract markers, and Era cards if a
physical test confirms that pieces remain easy to move and their states remain
unambiguous. Magnetic backing is not required for every card, tile, or resource.

The board must fold for storage, accept the complete 13-tile map without tile
overlap, and leave enough clearance for CEO, Team, Facility, and Generator
pieces to occupy a district. The final dimensions, fold pattern, material, and
magnet specification remain manufacturing decisions; they do not change the
rules or component limits.

### Table organization

The Governance Board holds public state and map-facing pieces. Use separate
labelled trays around it for:

- Training cards and their discard;
- Era Mandate decks;
- Runway, Compute, and Safety supplies;
- unused CEOs, Teams, Facilities, and Generators;
- unused Joint Venture and Mega-Cluster pairs; and
- Scrutiny and Systemic Risk supplies.

The trays remain open and countable. The Audit bag is the only opaque supply.
The board and trays must not introduce a second hidden state or require a
private note to reconstruct a turn.

## Faction board arrangement

Each faction board remains a separate player station. Its visible areas should
provide:

- a faction identity and ability panel;
- Runway, Compute, Capability, Customer, Trust, Safety, and Escalation tracks;
- six Core Action card slots and six Escalation card slots;
- supply positions for the CEO, Teams, Facilities, and Generator; and
- a clearly marked temporary Power area for the current Production.

AGI Dossier cards remain face down beside or beneath the faction board. They do
not go into a shared board slot, because their orientation is private until
the final reveal.

## Selected state-encoding decisions

Customer count, Escalation availability, the starting-grid identity, and AGI
Dossier choices are integrated into the listed components and faction-board
tracks. They do not require separate state markers. The forms must remain
legible when pieces occupy a crowded district;
readability is a validation requirement, not an unresolved format choice.

Facility 1 carries the integrated starting-grid identifier. Facility numbers
remain attached to their pieces when those Facilities move. The score sheet’s
latest Production snapshot records its Era, final Power supply, total demand
satisfied, and the powered/offline status of Facilities 1–4. Its four Era rows
also record every historical value named by an Era Mandate: Capability gained,
Customers gained, Fund Runway gained, new Joint Ventures active in Production,
Deploy completion, best successful Training Run unique domains, Compute
produced during Production, and Scrutiny added. All entries are public.

The following minor physical decisions remain open. They do not change rules or
state limits:

1. **Track implementation:** choose recessed boards with cubes, printed boards
   with cubes, or integrated dials. Loose dials are excluded unless a player
   board contains them.
2. **Minor status pieces:** choose stock cubes, beads, or punchboard for
   Initiative and Systemic Risk without changing their supply limits.
3. **Material:** choose wood or cardboard only after the selected state
   encoding, crowding, and blind-play readability have been tested.

## Physical constraints

- No component may conceal a district name, Facility slot, host relationship,
  or piece count.
- Every state required during a turn must be visible without consulting a
  private note.
- Shared contracts need durable matching identifiers.
- Scrutiny and Systemic Risk must be indistinguishable by touch while concealed
  in the opaque Audit bag. They must be immediately distinguishable by colour
  or printed identity after drawing. Use the same size, shape, material, and
  weight; never use a differently shaped Systemic Risk token.
- Do not add miniatures, custom plastic, or loose rotating wheels merely for
  theme. The neural-network language should come from node, connection, and
  illumination graphics, not extra game state.
