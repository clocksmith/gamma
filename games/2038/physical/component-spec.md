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
| Faction board | One player’s dashboard | Board or thick player mat | Printed tracks, ability, and action slots |
| CEO | Movable acting piece; two presence | Large faction-coloured pawn | Position on a district |
| Team | Movable acting piece; one presence | Small faction-coloured pawn | Position on a district |
| Facility | Stationary institutional site | Faction-coloured double-sided building/node piece | Position plus normal or Grid-Ready face |
| Generator | Stationary Power source | Distinct faction-coloured power-node piece | Position; its Energy district determines clean or emergency source |
| Scrutiny | Exposure in the Audit bag | Small faction-coloured cube | In owner supply or Audit bag |
| Systemic Risk | Shared Audit danger | Black Audit piece with the same concealed feel as Scrutiny | Audit bag or shared supply |
| Customer | Acquired demand | One marker on the faction-board Customer track | Customer track position from zero through five |
| Runway, Compute, Capability, Trust, and Safety | Scalar player state | Tokens or markers on the faction board | Count or track position |
| Mandate | Public score | One marker per faction on the shared Mandate track | Shared-track position |
| Grid-Ready | A Facility received complete Production Power | The Facility’s reverse | Normal / Grid-Ready face |
| Starting grid | Dedicated Power assigned to the first Facility | Integrated identifier on that first Facility | Attached / moved with its Facility |
| Escalation | Permission to select an Escalation | One marker on the faction-board Escalation track | Zero to two currently available; unused permission expires each Era |
| AGI claim | A faction registered its final-resolution claim | The Declare AGI card’s reverse | Unclaimed / claimed |
| Joint Venture / Mega-Cluster | A named shared project | Matched numbered token pair | Both host positions and pair number |
| Initiative | Current resolution and tie order | One shared marker | Current holder |
| Fusion Demonstrator | The unique advanced-generation project | One shared project marker | Grid position / unbuilt |
| Link — Advanced Play | A Facility’s connection to its owner’s Network | Faction-coloured connector token | Attached to one Facility |
| Network capacity — Advanced Play | Pooled connected Power | Player-board track marker | Current connected capacity |
| Realignment — Advanced Play | One secret jurisdiction motion | Three ballot cards per player | Selected face down, then revealed |
| Volatility — Advanced Play | Resolves a two-result Headline | One ordinary six-sided die | Printed result mapping |
| Era, Headline, Mandate, Action, Escalation, Training, and Power Source | Information and choices | Cards | Face, orientation, and printed text |

## Selected state-encoding decisions

Grid-Ready, Customer count, Escalation availability, the
starting-grid identity, and AGI claim are integrated into the listed
components and faction-board tracks. They do not require separate state
markers. The forms must remain legible when pieces occupy a crowded district;
readability is a validation requirement, not an unresolved format choice.

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
