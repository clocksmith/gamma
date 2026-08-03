# ${content.worldCopy.title} — Map Reference

Use this aid beside the board. It owns the map’s setup, spatial vocabulary,
district effects, Facility spaces, presence, and control.

## Build the jurisdiction

Use thirteen tiles in a sixfold-symmetric layout:

- One ${terms.locations.frontier}
- Two ${terms.locations.research}
- Two ${terms.locations.cloud}
- One each of ${terms.locations.consumer}, ${terms.locations.chip}, ${terms.locations.capital}, ${terms.locations.talent}, ${terms.locations.media},
  ${terms.locations.government}, ${terms.locations.grid}, and ${terms.locations.renewable}

Place ${terms.locations.frontier} at the center. Six operational districts form a cycle around
it. Each operational district touches ${terms.locations.frontier}, its two neighboring operational
districts, and the two public districts in the adjoining wedges. Each public
district touches exactly two operational districts and never another public
district. One movement step crosses one shared tile edge; move up to two steps.

Shuffle this operational ring around ${terms.locations.frontier}:

- One ${terms.locations.research}
- One ${terms.locations.cloud}
- One ${terms.locations.chip}
- One ${terms.locations.capital}
- One ${terms.locations.talent}
- The ${terms.locations.grid}

Shuffle this public ring among the outer positions:

- One ${terms.locations.research}
- One ${terms.locations.cloud}
- One ${terms.locations.consumer}
- One ${terms.locations.media}
- One ${terms.locations.government}
- One ${terms.locations.renewable}

These ring pools are fixed; shuffle tiles only within their listed ring. The
inner and outer copies of ${terms.locations.research} are mechanically identical, as are the
inner and outer copies of ${terms.locations.cloud}. Names, art, and flavor may distinguish a
copy, but its visit effect, production, Facility spaces, and contract icon must
remain identical.

Every piece placed on the board during setup begins at ${terms.locations.frontier}, the jurisdiction’s
standing civic exception rather than property to be controlled. Two movement
reaches any tile from the center; opposing outer tiles are four hexes apart.

Every non-${terms.locations.frontier} hex has a visit bonus, two Facility spaces, Facility
production, and a control value used by Headlines and Mandates. ${terms.locations.frontier} has
no Facility spaces. Once pieces leave it, positioning, Teams, local Power, and
negotiated adjacency matter.

## Presence and control

- CEO: two presence
- Team: one presence
- Facility: one presence
- ${terms.actions.influence} cube on ${terms.locations.media}, ${terms.locations.government}, or ${terms.locations.capital}: one presence

The player with the most presence controls the hex. Ties mean nobody controls
it.

## District effects

| Location | Visit bonus | Facility production | Contract icon |
| --- | --- | --- | --- |
| ${terms.locations.research} | Once this ${terms.systems.trainingRun}, protect one duplicate as if spending ${terms.resources.safety} | Gain one ${terms.resources.safety} token | ${terms.resources.compute} |
| ${terms.locations.cloud} | First ${terms.resources.compute} cost is reduced by one | Gain two ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.consumer} | ${terms.actions.deploy} costs zero ${terms.resources.compute} | Gain one ${terms.resources.runway} | ${terms.resources.runway} |
| ${terms.locations.chip} | ${terms.actions.build} costs one less ${terms.resources.runway} | Gain one ${terms.resources.compute} and one ${terms.actions.build} discount | ${terms.resources.compute} |
| ${terms.locations.capital} | ${terms.actions.fund} gains one ${terms.resources.runway} | Gain two ${terms.resources.runway} | ${terms.resources.runway} |
| ${terms.locations.talent} | Recruit costs one less ${terms.resources.runway} | Move one Team one hex during Production | ${terms.resources.runway} |
| ${terms.locations.media} | ${terms.actions.influence} may place or relocate one additional cube | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| ${terms.locations.government} | ${terms.actions.influence} may place or relocate one additional cube on ${terms.locations.government} | Gain one Policy Shield | ${terms.resources.runway} |
| ${terms.locations.grid} | Infrastructure ${terms.actions.build} costs one less | Gain one ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.renewable} | ${terms.technology.cleanInfrastructure} costs one less ${terms.resources.runway} | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| ${terms.locations.frontier} | After Act, you may gain one ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny} | No Facility spaces | None |

Resolve ${terms.locations.frontier}’s optional ${terms.resources.runway} after the Action, once per acting player
who ended movement there. It does not modify the Action or create production
or ${terms.playerTracks.mandate}.
