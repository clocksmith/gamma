# Component specification

This is the canonical physical-form record for Mandate 2038. It specifies
what players manipulate and how a component expresses state. It does not
replace mechanical quantities or rules in `content/data/game-config.json`.

## Colour allocation

The six saturated RGB colours are reserved for player ownership. Every CEO,
Team, Facility, Generator, Influence cube, Scrutiny cube, and player track
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

## Current prototype vocabulary

| Gameplay object | Physical role | Current prototype form | State encoding |
| --- | --- | --- | --- |
| Faction board | One player’s dashboard | Board or thick player mat | Printed tracks, ability, and action slots |
| CEO | Movable acting piece; two presence | Large faction-coloured pawn | Position on a district |
| Team | Movable acting piece; one presence | Small faction-coloured pawn | Position on a district |
| Facility | Stationary institutional site | Faction-coloured building/node piece | Position plus either a separate Grid-Ready marker or a Grid-Ready reverse |
| Generator | Stationary Power source | Distinct faction-coloured power-node piece | Position plus either a source selector or a source-specific face |
| Influence | Political presence on a district | Small faction-coloured cube | District position |
| Scrutiny | Exposure in the Audit bag | Small faction-coloured cube | In owner supply or Audit bag |
| Systemic Risk | Shared Audit danger | Black Audit piece with the same concealed feel as Scrutiny | Audit bag or shared supply |
| Customer | Acquired demand | Tokens or one player-board marker | Five tokens gained, or Customer track position |
| Runway, Compute, Capability, Trust, and Safety | Scalar player state | Tokens or markers on the faction board | Count or track position |
| Mandate | Public score | One marker per faction on the shared Mandate track | Shared-track position |
| Grid-Ready | A Facility received complete Production Power | Separate marker or the Facility’s reverse | Present / absent at that Facility |
| Starting grid | Dedicated Power assigned to the first Facility | Marker attached to that Facility | Attached / moved with its Facility |
| Escalation | Permission to select an Escalation | Four awarded tokens or one player-board marker | Zero to two currently available; unused permission expires each Era |
| AGI Declaration | A faction has completed its declaration | Separate marker or the Declare AGI card’s reverse | Undeclared / declared |
| Joint Venture / Mega-Cluster | A named shared project | Matched numbered token pair | Both host positions and pair number |
| Expert | Neutral supporting presence | Neutral pawn | District position |
| Economic Benchmark | A stored deployment waiver and Mandate opportunity | Token | Held / discarded |
| Spotlight | Public pressure on the current leader | One shared marker | Current holder |
| Public Research Grant | Catch-up support for the lowest-scoring faction | One shared marker | Current holder / spent |
| Market Access | A stored reduction to a Customer requirement | Token | Held / discarded |
| Build discount | A stored reduction to one Build cost | Token | Zero to two held / discarded |
| Policy Shield | Protection against one Trust loss or Regulatory effect | Token | Zero to two held / discarded |
| Initiative | Current resolution and tie order | One shared marker | Current holder |
| Fusion Demonstrator | The unique advanced-generation project | One shared project marker | Grid position / unbuilt |
| Link — Advanced Play | A Facility’s connection to its owner’s Network | Faction-coloured connector token | Attached to one Facility |
| Network capacity — Advanced Play | Pooled connected Power | Player-board track marker | Current connected capacity |
| Realignment — Advanced Play | One secret jurisdiction motion | Three ballot cards per player | Selected face down, then revealed |
| Volatility — Advanced Play | Resolves a two-result Headline | One ordinary six-sided die | Printed result mapping |
| Era, Headline, Mandate, Action, Escalation, Training, and Power Source | Information and choices | Cards | Face, orientation, and printed text |

## Component-form decisions still required

The following are intentional open physical decisions. Do not treat the
manufacturing study’s recommendations as selected formats.

1. **Facility Power state:** choose either a separate Grid-Ready marker or a
   double-sided Facility whose reverse is Grid-Ready. The latter reduces loose
   pieces but must remain legible in a crowded district.
2. **Generator source state:** choose either a Generator plus a source-selector
   marker, or one double-sided Generator that carries its source choice.
3. **Customers and Escalation:** choose separate tokens or faction-board
   tracks. Tracks reduce pieces; separate tokens increase immediate table
   visibility.
4. **Track implementation:** choose recessed boards with cubes, printed boards
   with cubes, or integrated dials. Loose dials are excluded unless a player
   board contains them.
5. **AGI Declaration:** choose a separate declaration marker or a clearly
   printed reverse on each player’s Declare AGI card.
6. **Minor status pieces:** choose stock cubes, beads, or punchboard for
   Benchmark, Spotlight, Grant, Market Access, discounts, Shields, Initiative,
   and Systemic Risk without changing their supply limits.
7. **Material:** choose wood or cardboard only after the selected state
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
