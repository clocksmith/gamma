# ${content.worldCopy.title} — Map Reference

Use this aid beside the board. It owns the map’s setup, spatial vocabulary,
district effects, Facility spaces, presence, and control.

## Build the jurisdiction

Use nineteen tiles in a complete radius-two hexagon:

- One ${terms.locations.frontier}
- Three ${terms.locations.research}
- Three ${terms.locations.cloud}
- Two each of ${terms.locations.consumer}, ${terms.locations.media},
  ${terms.locations.government}, and ${terms.locations.renewable}
- One each of ${terms.locations.chip}, ${terms.locations.capital},
  ${terms.locations.talent}, and ${terms.locations.grid}

Place ${terms.locations.frontier} at the center. Six operational districts form
the complete inner ring. Twelve public districts form the complete outer ring.
Every outer district touches its two outer neighbors and either one or two
inner districts according to the printed wells. One movement step crosses one
shared tile edge; move up to two steps.

Shuffle this operational ring around ${terms.locations.frontier}:

- One ${terms.locations.research}
- One ${terms.locations.cloud}
- One ${terms.locations.chip}
- One ${terms.locations.capital}
- One ${terms.locations.talent}
- The ${terms.locations.grid}

Shuffle this public ring among the twelve outer positions:

- Two ${terms.locations.research}
- Two ${terms.locations.cloud}
- Two ${terms.locations.consumer}
- Two ${terms.locations.media}
- Two ${terms.locations.government}
- Two ${terms.locations.renewable}

These ring pools are fixed; shuffle tiles only within their listed ring.
All copies of one named district are mechanically identical. Names, art, and
flavor may distinguish copies, but visit effects, production, Facility spaces,
and contract icons must remain identical.

Every piece placed on the board during setup begins at ${terms.locations.frontier}, the jurisdiction’s
standing civic exception rather than property to be controlled. Two movement
reaches any tile from the center; opposing outer tiles are four hexes apart.

Every non-${terms.locations.frontier} hex has a visit bonus, two Facility spaces, Facility
production, and a control value used by Headlines and Mandates. ${terms.locations.frontier} has
no Facility spaces and is never controlled. It is not a category for the hex-category
Mandate. Once pieces leave it, positioning, Teams, local Power, and negotiated adjacency
matter.

## Presence and control

- CEO, Team, or Facility: one presence

The player with the most presence controls each non-${terms.locations.frontier} hex. Ties mean
nobody controls it. ${terms.locations.frontier} has no controller regardless of presence.

## District effects

| Location | Visit bonus | Facility production | Contract icon |
| --- | --- | --- | --- |
| ${terms.locations.research} | Gain one additional ${terms.resources.researchProtection} for this ${terms.systems.trainingRun} | Gain one ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.cloud} | First ${terms.resources.compute} cost is reduced by one | Gain two ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.consumer} | ${terms.actions.deploy} costs zero ${terms.resources.compute} | Gain one ${terms.resources.runway} | ${terms.resources.runway} |
| ${terms.locations.chip} | ${terms.actions.build} costs one less ${terms.resources.runway} | Gain one ${terms.resources.compute} and one ${terms.resources.runway} | ${terms.resources.compute} |
| ${terms.locations.capital} | ${terms.actions.fund} gains one ${terms.resources.runway} | Gain two ${terms.resources.runway} | ${terms.resources.runway} |
| ${terms.locations.talent} | Recruit costs one less ${terms.resources.runway} | Move one Team one hex during Production | ${terms.resources.runway} |
| ${terms.locations.media} | ${terms.actions.influence} may remove one additional ${terms.playerTracks.scrutiny} | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| ${terms.locations.government} | ${terms.actions.influence} may gain one additional ${terms.playerTracks.trust} | Gain one ${terms.playerTracks.trust} | ${terms.resources.runway} |
| ${terms.locations.grid} | Build ${terms.technology.emergencyInfrastructure} here for one ${terms.resources.runway}: capacity four local ${terms.infrastructure.power}; add one ${terms.playerTracks.scrutiny} each Production it operates | Gain one ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.renewable} | Build ${terms.technology.cleanInfrastructure} here for two ${terms.resources.runway}: capacity three local ${terms.infrastructure.power}; gain one ${terms.playerTracks.trust} when constructed; no recurring penalty | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| ${terms.locations.frontier} | After Act, you may gain one ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny} | No Facility spaces | None |

Resolve ${terms.locations.frontier}’s optional ${terms.resources.runway} after the Action, once per acting player
who ended movement there. It does not modify the Action or create production
or ${terms.playerTracks.mandate}.

The two Energy-tile visit boxes are the complete ordinary Generator contracts.
No separate Power Source reference cards are used. Each player may construct
only one ordinary Generator; the full Fusion contract is printed on its Era IV
Program card.
