# ${content.worldCopy.title}
## A strategy game about institutions turning reliable AI capability into contested public authority as they build, deploy, regulate, and make rival claims on ${terms.systems.agi}

**Suggested player count:** ${game.suggestedPlayerRange}

Use the browser **First Game Guide** for an accelerated introduction.

The separately printed [**World and Institutions**](/docs/world-and-institutions.html) companion contains setting
and ending narratives.

## How to Play

The game lasts four Eras. The institution with the most
${terms.playerTracks.mandate} is the provisional winner. The strongest eligible
${terms.systems.agi} claim can replace that result. Resolve
the institutional winner and shared World Ending separately. Follow the
numbered sections in order.

## 1. Setup

1. Unfold the Governance Board. Build the nineteen-tile map in its wells as described in **Modular hex board**:
   ${terms.locations.frontier} in the center, the shuffled six-tile operational ring around it,
   and the shuffled twelve-tile public ring around the complete outer edge.
2. Separate the sixteen ${terms.systems.headline} cards by Era. Shuffle
   each deck into its printed Era panel's Headline well. Each Era uses three
   ${terms.systems.headlines}. Place the Current Era marker in its Start bay.
3. Shuffle the Training deck. Separate the twelve Era ${terms.playerTracks.mandate} cards into
   four three-card Era decks. Shuffle each deck and place it beside its Era
   panel.
4. Place the six shared Program cards face up beside the Governance Board and
   stage the remaining shared supplies. Ordinary
   ${terms.infrastructure.power} contracts are printed on the Energy tiles;
   Fusion's is on its shared Program card.
5. Each player takes one prepacked Faction tray and foldout aid. Set its captive
   sliders to their printed starts.
6. Place every CEO and one Team at ${terms.locations.frontier}. Keep the other two Teams in
   supply. Keep all four Facilities and the Generator in supply; no Facility
   begins on the board. Facilities must be constructed in printed number order:
   Facility 1 first, then 2, 3, and 4. Facility 1 carries that Faction's
   integrated starting-grid identifier. Set each Faction’s ${terms.resources.runway}, ${terms.resources.compute}, ${terms.playerTracks.capability}, ${terms.playerTracks.customers}, ${terms.playerTracks.trust},
   and Research Protection to its printed starting values. Each player takes
   two Program markers.
7. Place each Faction’s already-earned public ${terms.playerTracks.mandate} on the shared track as
   printed on its Faction board. Put every player’s ten ${terms.playerTracks.scrutiny}
   cubes outside the bag; the bag begins empty.
8. Add every Faction’s printed starting ${terms.playerTracks.trust} and record the result as
   **Setup Collective ${terms.playerTracks.trust}** in the Governance Board ledger. This fixed value is used
   during the World Ending.
9. Choose Initiative randomly and give that player the Initiative marker.
   Begin Era I.

Do not deal Tactics or secret objectives in the baseline game.

## 2. Central loop

Each player has six Core Action cards but takes only three turns per Era.
Once played, a Core Action remains exhausted until the next Era:

- ${terms.actions.fund}
- ${terms.actions.research}
- ${terms.actions.build}
- ${terms.actions.organize}
- ${terms.actions.deploy}
- ${terms.actions.influence}

Choose three of six Actions each Era, in any order. The other three remain
unused unless an ability readies one.

### The complete ordinary turn: Select → Move → Act

1. Reveal one ${terms.systems.headline}.
2. Every player secretly selects one eligible unused Core Action, or commits one
   Program marker to select one eligible unlocked Program. A choice is eligible
   only when it has a legal resolution now. A possible trade cannot make an
   illegal selection legal.
3. Reveal every selected action simultaneously.
4. Resolve clockwise from Initiative.
5. **Select:** the revealed Action is the only Action this turn.
6. **Move:** choose one acting piece and move it zero, one, or two adjacent
   hexes.
7. **Act:** read the chosen Action card from top to bottom and resolve it from
   the destination.
8. Exhaust the Core Action, or place the committed Program marker on the shared
   Program card.
9. Pass Initiative clockwise before the next cycle.

Selection commits the Action card; choose the piece, path, target, and payment
during resolution.

### Acting piece

The acting piece is a CEO or Team. Both can take any Action and each contributes
one presence. Its destination determines where Facilities and
power infrastructure may be built, where Research and Deploy occur, which
location bonus applies, and which political spaces may be Influenced.

Facilities and Generators cannot act. ${terms.actions.organize}
receives normal acting-piece movement before its additional movement,
recruitment, restructuring, or relocation.

### Effect precedence

Apply these sources in order:

- The Current Era panel determines globally unlocked actions.
- A Faction board modifies those actions.
- The current ${terms.systems.headline} supplies its printed global effect.
- An ordinary turn may apply the Action, one destination bonus, each applicable
  Faction modifier, and each applicable global effect. If multiple programs on
  the same Faction board apply to that Action, resolve all of them unless one
  explicitly requires a choice.
- Every exception is timed **before selection**, **during movement**, **during
  action**, or **after action**.
- A ${terms.systems.headline} changes one named field or calls one public choice procedure. It
  grants no additional Action.
- Readying a card makes it available for a later choice. Resolve nothing when
  you ready it.
- ${terms.technology.agentSwarm} is the sole compound-action exception.

### What an Era teaches

Systems are inactive before their printed Era panel lists them under **New this Era**.
Read that strip aloud before revealing the Mandate. All Era panels, Programs,
and Faction abilities are open information.

Program access is cumulative. Progress teaches ordinary institutional work;
Capacity adds industrial infrastructure; Authority adds agreements, quantum
record disputes, and public effects; Continuity adds compound Actions, Dossier
revelation, and exceptional
generation. Later Eras retain previously unlocked systems
unless a printed effect says otherwise.

### Universal tie rule

Whenever an effect targets the player with the lowest, highest, or most of
something and multiple players tie, target the tied player nearest Initiative
clockwise. An effect that explicitly applies to everyone, or explicitly awards
all tied players, overrides this rule.

Initiative is an order, not a resource. Passing it after each cycle changes who
resolves first and who wins unresolved ties; it cannot be traded or retained.

### Program markers and ${terms.systems.escalations}

<!-- program-selection:start -->
The six shared Program cards are public. At the start of each Era, each player
sets aside the printed number of their two Program markers: zero, one, one,
then two. Commit one available marker to select an Era-unlocked Program:

- Select a Program instead of a Core Action.
- Place your marker on that shared Program card when selected.
- Each named Program is usable once per player per game.
- At Era end, return committed markers; unused markers do not carry forward.
- Previously unlocked unused Programs remain available later.
<!-- program-selection:end -->

**Global after movement** means the acting piece moves normally, then the
Action resolves without a destination restriction.

| Era | Program markers | Newly available Programs |
| --- | ---: | --- |
| I — ${terms.eras.demo} | 0 | None |
| II — ${terms.eras.scale} | 1 | ${terms.technology.megaCluster}, Reorganization |
| III — ${terms.eras.narrative} | 1 | Public Capability Covenant, Narrative Capture |
| IV — ${terms.eras.claim} | 2 | ${terms.technology.agentSwarm}, ${terms.technology.advancedGeneration} |

${terms.technology.agentSwarm} is the selected Program; it resolves and exhausts two
different unused Core Actions.

### A committed Action that becomes blocked

At selection, the Action must have a legal resolution before any trade. After
reveal, choose any legal piece, movement, mode, target, payment, and optional
pre-resolution trade, but never replace the selected Action.

If an earlier player consumes every legal Facility space, Generator slot,
contract token, or other required target, movement still resolves and the
Action exhausts without effect or compensation. Initiative can therefore let
an earlier player consume a later player’s target. Do not rewind simultaneous
selection.

## 3. Resources

### ${terms.resources.runway}, ${terms.resources.compute}, and ${terms.playerTracks.capability}

- **${terms.resources.runway}:** financing spent on Facilities, hiring, partnerships,
  lobbying, and crises.
- **${terms.resources.compute}:** capacity spent on ${terms.actions.research}, ${terms.actions.deploy}, and infrastructure.
- **${terms.playerTracks.capability}:** permanent model quality that unlocks Deployments and
  ${terms.systems.agi}; spend it only when instructed.

### ${terms.playerTracks.customers}

Each ${terms.playerTracks.customer} produces one ${terms.resources.runway} during Production. Customers #1–3 immediately score two public ${terms.playerTracks.mandate}; Customers #4–5 score one each. Customers also increase public exposure.

### ${terms.playerTracks.trust}

A zero-to-six track affecting regulation, Joint Ventures, safety, and whether
the shared World Ending is Open. Zero ${terms.playerTracks.trust} does not
eliminate a player.

**${terms.playerTracks.mandate}** is the score used to determine the winner (victory points).
It is the public authority you have gained to define outcomes.
It represents the recognized right to shape the future: credibility in Progress,
capacity in Capacity, authority in Authority, and historical legitimacy in
Continuity.

${terms.playerTracks.mandate} is normally scored immediately on one public track:

- Two when ${terms.playerTracks.customer} #1, #2, or #3 is gained; one when #4 or #5 is gained.
- Two the first time ${terms.playerTracks.capability} reaches three, six, nine, and twelve, except
  for a printed faction scoring rule.
- Two the first time ${terms.playerTracks.trust} reaches two, four, and six.
- Printed ${terms.playerTracks.mandate} from ${terms.systems.headlines}, Era Mandates, Fusion, and faction abilities.

Threshold awards are permanent; later losses do not reverse them.

There is no hidden or deferred conversion of Facilities, controlled hexes,
stored resources, or unused cards into ${terms.playerTracks.mandate}. If an effect scores ${terms.playerTracks.mandate}, move
the public marker when that effect resolves.

### Universal costs and caps

Apply resource caps immediately after any gain or trade:

- ${terms.resources.runway}: twelve
- ${terms.resources.compute}: ten

Research Protection is not traded or accumulated as currency. Refresh it to
one at the start of each Era; Orisonix refreshes to two. A Research visit adds
one temporary protection for that Training Run only.

Return excess. A trade cannot move resources through a player above a cap.

When effects change a cost, apply replacements and waivers first, then
surcharges, then discounts. The final cost cannot fall below zero.

## 4. Modular hex board

The board is one jurisdiction whose districts represent physical and
institutional dependencies rather than ordinary distance. The shuffled map
remains fixed for all four Eras. Rival pieces coexist; there is no combat
or player elimination.

The detailed setup, district effects, and control procedure print in the
[**Map Reference**](/docs/map-reference.html).

<!-- map:start -->
### Build the jurisdiction

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
shared tile edge; move up to ${content.gameConfig.board.geometry.movementRange} steps.

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

### Presence and control

- CEO, Team, or Facility: one presence

The player with the most presence controls each non-${terms.locations.frontier} hex. Ties mean
nobody controls it. ${terms.locations.frontier} has no controller regardless of presence.

### District effects

| Location | Visit bonus | Facility production | Contract icon |
| --- | --- | --- | --- |
| ${content.gameConfig.board.tiles.0.name} | ${content.gameConfig.board.tiles.0.visit} | ${content.gameConfig.board.tiles.0.production} | None |
| ${content.gameConfig.board.tiles.1.name} | ${content.gameConfig.board.tiles.1.visit} | ${content.gameConfig.board.tiles.1.production} | ${terms.resources.compute} |
| ${content.gameConfig.board.tiles.2.name} | ${content.gameConfig.board.tiles.2.visit} | ${content.gameConfig.board.tiles.2.production} | ${terms.resources.compute} |
| ${content.gameConfig.board.tiles.3.name} | ${content.gameConfig.board.tiles.3.visit} | ${content.gameConfig.board.tiles.3.production} | ${terms.resources.runway} |
| ${content.gameConfig.board.tiles.4.name} | ${content.gameConfig.board.tiles.4.visit} | ${content.gameConfig.board.tiles.4.production} | ${terms.resources.compute} |
| ${content.gameConfig.board.tiles.5.name} | ${content.gameConfig.board.tiles.5.visit} | ${content.gameConfig.board.tiles.5.production} | ${terms.resources.runway} |
| ${content.gameConfig.board.tiles.6.name} | ${content.gameConfig.board.tiles.6.visit} | ${content.gameConfig.board.tiles.6.production} | ${terms.resources.runway} |
| ${content.gameConfig.board.tiles.7.name} | ${content.gameConfig.board.tiles.7.visit} | ${content.gameConfig.board.tiles.7.production} | ${terms.resources.runway} |
| ${content.gameConfig.board.tiles.8.name} | ${content.gameConfig.board.tiles.8.visit} | ${content.gameConfig.board.tiles.8.production} | ${terms.resources.runway} |
| ${content.gameConfig.board.tiles.9.name} | ${content.gameConfig.board.tiles.9.visit} | ${content.gameConfig.board.tiles.9.production} | ${terms.resources.compute} |
| ${content.gameConfig.board.tiles.10.name} | ${content.gameConfig.board.tiles.10.visit} | ${content.gameConfig.board.tiles.10.production} | ${terms.resources.runway} |

Resolve ${terms.locations.frontier}’s optional ${terms.resources.runway} after the Action, once per acting player
who ended movement there. It does not modify the Action or create production
or ${terms.playerTracks.mandate}.

The two Energy-tile visit boxes are the complete ordinary Generator contracts.
No separate Power Source reference cards are used. Each player may construct
only one ordinary Generator; the full Fusion contract is printed on its Era IV
Program card.
<!-- map:end -->

### ${terms.infrastructure.power} connections

Power eligibility is **local**. The starting grid
powers only its assigned first Facility. Each Generator powers only Facilities
on its own hex or an adjacent hex. A Facility cannot pass Power onward to
another Facility.

Recalculate local eligibility whenever a Facility or Generator moves; do not
preserve a connection the visible board no longer supports.

### Contract hosts

Joint Ventures and Mega-Clusters use shared, matched token pairs. A Mega-Cluster
is always owned by one player. Create one
only while its pair is available; place one numbered half on each host.

A contract remains owned but is active only while its fixed hosts meet its
requirements. Tokens travel with their Facilities.

Every cross-player contract or jointly funded project requires the explicit
consent of every participant. Facilities sharing one hex are **co-located**.
Adjacent host Facilities occupy hexes that share an edge.

Consent applies to the named project only. It does not grant control of a host,
create a general trading right, or authorize another contract. A contract’s
matched number preserves its identity when a host moves.

### Joint Venture

${terms.actions.influence} may create a Joint Venture between two adjacent Facilities owned by
different players, unless a Faction ability explicitly changes that range.
Both host Facilities must be powered during Production for the contract to
produce.

Each partner gains the resource shown by the **contract icon on the other
host tile**. Do not copy full tile production or multiply it with Facility
effects.

During ${terms.actions.influence}, make one complete proposal naming both eligible hosts and
the partner. Acceptance creates it. Rejection, pass, or no response uses that
effect; do not choose another partner or ${terms.actions.influence} effect.

Either participant may instead use ${terms.actions.influence} to terminate one shared Joint
Venture. Return its pair. Termination cannot be combined with another
${terms.actions.influence} effect.

### ${terms.infrastructure.power} delivery

${terms.infrastructure.power} is Production capacity and cannot be stored.

- Every player begins with a basic one-${terms.infrastructure.power} grid connection. It automatically
  powers that player’s first Facility, requires no recurring payment,
  and cannot supply the additional demand of ${terms.technology.megaCluster}. It is
  dedicated capacity and cannot be sold. Place the
  player’s starting-grid state on that first Facility.
- Every Facility needs one delivered ${terms.infrastructure.power} to produce.
- A ${terms.technology.megaCluster} needs two additional ${terms.infrastructure.power}.
- The starting-grid state and each Generator’s own or
  adjacent Facilities are the only legal recipients. A Generator does not need
  to be connected to the starting-grid Facility.

Power never travels through an opponent’s sites unless a specific purchase
rule transfers that capacity. A sale changes available capacity, not the map.

Follow **${terms.infrastructure.power} and Production**. Capacity powers Facilities and projects,
produces no resources, and may be assigned only once. Assign each local source
only among its legal recipients.

An offline Facility still occupies space, contributes presence, and may be
visited, but produces nothing. Sufficient Power in a later Production returns
it online.

## 5. Four-Era progression

### Era I — ${terms.eras.demo}

- Three turns per player
- Only Core Actions
- Beneficial or mildly disruptive ${terms.systems.headlines}
- No Program markers

Era I activates movement, Core Actions, Training, the starting grid,
Facilities, Customers, and Scrutiny.

### Era II — ${terms.eras.scale}

Each player receives one Program marker and unlocks:

- Generators
- Mega-Clusters
- ${terms.systems.escalations}

#### ${terms.technology.megaCluster}

Spend three ${terms.resources.runway} and two ${terms.resources.compute} to place a ${terms.technology.megaCluster} across the edge
between two adjacent host Facilities. Construction does not require a prior
Production Power mark; it does require the local eligibility check below at the
moment of construction. Add two ${terms.playerTracks.scrutiny} to its owner.
Place one matched ${terms.technology.megaCluster} token half on each host Facility.
Each Facility may host at most one ${terms.technology.megaCluster}; a Facility
that already holds a ${terms.technology.megaCluster} half is not an eligible host.

The acting piece must end on either host Facility’s hex.

A ${terms.technology.megaCluster} uses two adjacent Facilities you own that are each eligible for
your local Power. Check that eligibility when the project is constructed. During
Production, power both hosts plus two additional demand to gain three
${terms.resources.compute}.

Hosts must remain adjacent for the project to operate. Construction resolves in
Initiative order. Construction reserves no Power; the additional demand is paid
only during Production. During Allocate, its owner chooses the complete
Facility and project allocation together. A project operates only if both host
Facilities are powered and its additional demand is satisfied. A constructed project immediately claims its two hosts
and the next available matched token pair. Every later project rechecks the
shared pair supply, both unclaimed hosts, adjacency, and local Power eligibility.
If an earlier accepted project claimed either host or the final pair, the later
project is blocked and remains unbuilt.

#### Reorganization

Reorganization is global after movement.

Move every Team up to one hex.

You may return one Team to supply to gain three ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny}.
Reorganization never resolves or readies another Action.

### Era III — ${terms.eras.narrative}

Each player receives one Program marker. Previous Programs remain
unlocked. Joint Ventures now enter play.

#### Public Capability Covenant

Public Capability Covenant is global after movement.

Every player gains one ${terms.playerTracks.capability}. You also gain:

- Two ${terms.playerTracks.trust}
- Removal of one ${terms.playerTracks.scrutiny} cube

#### Narrative Capture

Narrative Capture is global after movement.

Choose one:

- Remove two of your ${terms.playerTracks.scrutiny} cubes.
- Gain two ${terms.resources.runway}.
- Give a player with more ${terms.playerTracks.customers} than you one ${terms.playerTracks.scrutiny}.

### Era IV — ${terms.eras.claim}

Each player receives two Program markers.

Agent Swarms, Fusion, the Era IV faction abilities printed on the Faction boards,
and the final Dossier reveal now enter play. Each Faction ability unlocks at the
Era printed on its board.

#### ${terms.technology.agentSwarm}

Select ${terms.technology.agentSwarm} only with two different unused Core Actions. Move once;
resolve both from that destination in either order and pay all costs. Apply the
visit bonus to only one. Exhaust both, place your marker on ${terms.technology.agentSwarm}, and add three ${terms.playerTracks.scrutiny}.

#### The secret ${terms.systems.agi} Dossier

Each player has four matching Dossier cards: **Benchmark**, **Deployment**,
**Authority**, and **Publication**. Each card has a symmetrical back and two
orientations on its face: **Commit** and **Hedge**. The arrow on the card points
toward the center of the table when it is oriented to Commit.

After Production and before the Audit in each Era, everyone secretly orients
that Era's Dossier card and places it face down. Do not reveal, rotate, exchange,
or inspect a filed card. Table talk, resource plans, and visible board play may
suggest a player's intentions, but never make a private orientation binding
until the final reveal.

In Era IV, file **Publication**, then reveal every Dossier simultaneously
before conducting the final Audit.

1. Count each player's committed cards. Every Commit costs one
   ${terms.resources.compute} and adds one ${terms.playerTracks.scrutiny}.
2. Pay the complete ${terms.resources.compute} cost. A player who cannot pay it
   spends all remaining ${terms.resources.compute}, still adds the full
   ${terms.playerTracks.scrutiny}, and has an **ineligible Dossier**.
3. A fully paid Dossier becomes an **eligible claim** only when Publication is
   committed. Earlier commitments without Publication are costly institutional
   positioning or a bluff; they cannot produce ${terms.systems.agi}.
4. Add the required ${terms.playerTracks.scrutiny} before the Era IV Audit. Use
   the normal ten-cube supply and overflow rule.

Filing a Dossier uses no Action and scores no ${terms.playerTracks.mandate}.
Its sacrifice is the ${terms.resources.compute} held for final payment, the
${terms.playerTracks.scrutiny} exposed to the final Audit, and the ordinary
actions spent building the public evidence that can strengthen it.

#### Claim strength

During final scoring, evaluate each fully paid claim with Publication committed.
A claim needs at least two supported evidence modules among Benchmark,
Deployment, and Authority:

- **Benchmark:** supported if Benchmark was committed and final
  ${terms.playerTracks.capability} is at least three.
- **Deployment:** supported if Deployment was committed and at least two of
  the claimant's Facilities were powered in the final Production.
- **Authority:** supported if Authority was committed and final
  ${terms.playerTracks.trust} is at least four.

An eligible claim's strength equals:

- one for Publication, or two while the AGI Blog Post Headline applies;
- one for each supported evidence module;
- one for each reached Capability threshold: three, six, nine, and twelve.

The highest-strength eligible claim forms ${terms.systems.agi}. Break a strength
tie by final ${terms.playerTracks.mandate}, then ${terms.playerTracks.trust},
${terms.playerTracks.customers}, ${terms.resources.compute}, and finally
Initiative-clockwise order. If no claim has two supported evidence modules,
${terms.systems.agi} does not emerge and the provisional Mandate winner remains
the institutional winner. There is no Prediction Bag, comeback bonus, random
draw, or separate declaration.

#### ${terms.technology.advancedGeneration}

The acting piece must end movement on the ${terms.locations.grid}. Spend
${facts.shared.advancedGeneration.runwayCostWord} ${terms.resources.runway} and construct ${terms.technology.advancedGenerationShort} there. It uses a dedicated ${terms.technology.advancedGenerationShort} marker,
occupies one of that tile’s three Generator slots, provides ${facts.shared.advancedGeneration.powerWord} ${terms.infrastructure.power}, scores
${facts.shared.advancedGeneration.mandateWord} ${terms.playerTracks.mandate}, and adds ${facts.shared.advancedGeneration.scrutinyWord} ${terms.playerTracks.scrutiny}. ${terms.technology.advancedGenerationShort} counts as an owned Generator for
local Power eligibility and ${terms.infrastructure.power} capacity. It does not count
against the owner’s one ordinary Generator-piece limit. If all three Grid
Generator slots are occupied, ${terms.technology.advancedGenerationShort} cannot be constructed. A full ${terms.locations.grid}
blocks construction.

There is one shared ${terms.technology.advancedGenerationShort} marker and one
Fusion project in the game. Once any player constructs it, no other player may
select or construct Fusion.

## 6. Era sequence

### A. Begin the quarter

- Move the Current Era marker to Era I; in later Eras, advance one panel.
- Read that Era’s **New this Era** strip aloud. Those systems are now active.
- Reveal one ${terms.playerTracks.mandate} from the current Era’s three-card deck. Return the other
  two cards in that deck to the box unseen.
- Clear the Current Mandate ledger and write the revealed criterion and
  minimum. Start this-Era values at zero; evaluate current-state values when
  scored.
- Ready all six Core Actions.
- Make the Era's zero, one, one, or two Program markers available.

### B. Three action cycles

At the beginning of each cycle:

1. Reveal a ${terms.systems.headline} and place it in the current Era’s ${terms.systems.futureTimeline} row.
2. Everyone secretly **selects** one Action card.
3. Reveal simultaneously.
4. Resolve clockwise from Initiative: **move**, then **act**.
5. Pass Initiative clockwise.

#### Immediate resource trade

Immediately before resolving the selected Action, the active player may make
one offer to one rival: give exactly one ${terms.resources.runway} for one
${terms.resources.compute}, or one ${terms.resources.compute} for one
${terms.resources.runway}. The named rival accepts or rejects. Gifts, bundles,
same-resource exchanges, unequal amounts, counteroffers, redirects, and
third-party claims are not legal. Adjust both players' captive sliders
immediately after acceptance. The active
${terms.systems.headline} may prohibit a named resource from being traded.

The selected Action was legal before this window and continues whether the
offer is accepted or rejected. There is no post-action trade window.

Immediate resource trades require no ${terms.actions.influence} Action. Only ${terms.actions.influence} creates
persistent Joint Ventures, lobbying effects, or ${terms.playerTracks.trust} manipulation.

### Negotiation and paced play

Discussion creates no game state, obligation, or Action. Promises about later
turns remain non-binding. Apply formal choices only in their printed windows;
missing responses are rejection or pass.

**Paced Play** is an optional table rule. Before play, the group may assign one
shared sand timer to each negotiation window. When it expires, discussion ends
and the normal rejection or pass fallback applies. Expiry never
creates consent or forces a deal.

### C. ${terms.infrastructure.power} and Production

Every player board presents the same four Production boxes. Resolve a box for
every player before advancing to the next box:

1. **Generate:** determine every Generator’s local eligible Facilities. Every
   Generator with at least one eligible Facility operates automatically. Add one ${terms.playerTracks.scrutiny} for every
   ${terms.technology.emergencyInfrastructure}. Add any ${terms.systems.headline} generation.
2. **Allocate:** resolve any Headline that lets a
   player choose supplemental ${terms.infrastructure.power}. Then each player chooses one complete
   allocation of starting-grid, Generator, and supplemental
   ${terms.infrastructure.power} among legal local Facilities and Mega-Cluster demand. Remove the
   previous snapshot, then place one Power cube on each powered Facility and
   per satisfied Mega-Cluster demand. Leave these cubes until the next Allocate
   step. A built Facility without a cube is offline. The cubes are total demand
   satisfied.
3. **Produce:** produce powered Facilities, one ${terms.resources.runway} per ${terms.playerTracks.customer},
   and active Mega-Clusters, in that order.
4. **Partner:** produce active Joint Ventures in ascending contract-number
   order.

Complete each box for every player before entering the next. Do not let one
player finish Production while others still generate or allocate. This
keeps contracts tied to one visible capacity state. Within a box,
resolve in Initiative order unless that box specifies otherwise.

The retained
Power cubes remain the authority for the next Mandate, any
powered-Facility Headline, the Era IV Dossier, and final offline penalties.

Apply the universal resource caps after every Production gain.

When an Era Mandate counts **Compute produced during Production**, count printed
Compute output before the universal cap. Include powered Facilities, active
Mega-Clusters, and either side of an active
Joint Venture that receives Compute. Do not count an immediate Facility effect
outside the four Production boxes.

### D. File the Era Dossier

Every player secretly orients and files the matching Era Dossier card. In Era
IV, reveal and pay every Dossier immediately, then add its ${terms.playerTracks.scrutiny}
before continuing. See **The secret ${terms.systems.agi} Dossier**.

### E. ${terms.systems.publicAudit}

Risky actions add player-colored ${terms.playerTracks.scrutiny} to the opaque Audit bag. Each
player has ten cubes. For each required cube when all ten are already in the
bag, immediately lose one ${terms.resources.runway}; if none remains, lose one
${terms.playerTracks.trust}. If neither remains, suffer no further loss. A depleted supply
never makes a risky action free.

The four-player base draws are two, three, four, and five. For other player
counts, calculate each Era’s draw count as:

> round(base draws × player count ÷ 4), minimum one

Era halves upward. The resulting Audit profiles are:

| Era | 2 players | 3 players | 4 players | 5 players | 6 players |
| --- | ---: | ---: | ---: | ---: | ---: |
| I | 1 | 2 | 2 | 3 | 3 |
| II | 2 | 2 | 3 | 4 | 5 |
| III | 2 | 3 | 4 | 5 | 6 |
| IV | 3 | 4 | 5 | 6 | 8 |

Draw the listed number of cubes or stop when the bag is empty.

In every Era, each colored cube makes its owner lose one
${terms.resources.runway}; if none remains, lose one ${terms.playerTracks.trust}.
If neither remains, suffer no further loss. This is automatic, not a choice.

Drawn player-colored cubes return to the owner’s supply; undrawn cubes remain
in the bag.

${terms.locations.media} Facilities may remove cubes before the draw. A drawn black Systemic
Risk cube gives every player with at least three ${terms.playerTracks.customers} the current Era’s
penalty, then returns to supply. Black cubes
remaining at game end are unresolved Systemic Risk.

### F. Score the ${terms.playerTracks.mandate}

<!-- mandate-scoring:start -->
Each Era ${terms.playerTracks.mandate} has a minimum qualification. If nobody qualifies, nobody
scores it. Otherwise the qualifying leader scores two ${terms.playerTracks.mandate}; tied qualifying
leaders score one ${terms.playerTracks.mandate} each.

Compare only the revealed Mandate’s printed criterion. Resources, control, and
public score do not break its tie. Leave the scored card beside its Era as part
of the table’s public history. The ledger is a counting aid; clear
it when the next Mandate is revealed.

The revealed Mandate card is the exact qualification and scoring authority.
<!-- mandate-scoring:end -->

## 7. Core Actions

### ${terms.actions.fund}

Choose:

- **Conservative funding:** gain two ${terms.resources.runway}.
- **Venture funding:** gain four ${terms.resources.runway} and add two ${terms.playerTracks.scrutiny}.

${terms.locations.capital} provides one additional ${terms.resources.runway}.

### ${terms.actions.research}

Spend one ${terms.resources.compute} and conduct a ${terms.systems.trainingRun}.

The Training deck contains seven data domains:

- Code
- Science
- Web
- Books
- Images
- Video
- Synthetic

${terms.playerTracks.capability} earned during ${terms.actions.research} is **provisional until banked**:

1. Begin with zero provisional ${terms.playerTracks.capability} and no revealed domains.
2. Draw and fully resolve one card at a time.
3. The first card from each ordinary domain adds one provisional ${terms.playerTracks.capability}.
4. After resolving any non-duplicate card, either stop and bank or continue.
5. Banking adds all provisional ${terms.playerTracks.capability} to the player’s permanent
   ${terms.playerTracks.capability} track and ends the run.
6. An unprotected duplicate crashes the run. Lose all provisional ${terms.playerTracks.capability},
   add one ${terms.playerTracks.scrutiny}, and end the run.

${terms.playerTracks.scrutiny}, ${terms.playerTracks.trust}, and ${terms.resources.runway} changes resolved before a crash are not reversed.
All revealed cards enter the discard pile after the run.

When a duplicate appears, the player may spend one Research Protection to
discard that duplicate and immediately bank the current provisional
${terms.playerTracks.capability}. Each player refreshes to one Research
Protection at Era start; Orisonix refreshes to two. A ${terms.locations.research}
visit grants one additional protection for that run. Protection never lets the
run continue after the duplicate.

Special cards:

- **Curated Corpus:** choose one ordinary domain not yet revealed this run. It
  counts as that domain and adds one provisional ${terms.playerTracks.capability}. If every ordinary
  domain is already present, it is a duplicate.
- **Benchmark Leak:** add two provisional ${terms.playerTracks.capability} and one ${terms.playerTracks.scrutiny}. It is
  not a domain. Its ${terms.playerTracks.capability} is lost if the run later crashes.
- **Human Evaluation:** gain one ${terms.playerTracks.trust}, immediately bank all provisional
  ${terms.playerTracks.capability}, and end the run.

When a Mandate, Faction ability, or Headline counts **unique domains**, count
only the seven ordinary domains listed above that were banked successfully.
Benchmark Leak and Human Evaluation never count unless an effect names them
explicitly.

### ${terms.actions.build}

Choose one mode.

**Facility ${terms.actions.build}** means Construct a Facility. **Infrastructure ${terms.actions.build}** means
Construct a Generator.
${terms.technology.megaCluster} and
${terms.technology.advancedGeneration} are ${terms.systems.escalations}.

#### Construct a Facility

Pay two ${terms.resources.runway} and place your lowest-numbered unbuilt Facility on the acting
piece’s hex. Facility 1 must be built first, followed by Facilities 2, 3, and 4.
It requires one
${terms.infrastructure.power} during Production. Each non-${terms.locations.frontier} hex has only two Facility spaces;
${terms.locations.frontier} has none and is never a legal Facility destination. Facilities cannot
be destroyed by rivals.

#### Construct a Generator

The acting piece must be on an Energy hex. Each player may construct one
ordinary Generator. On ${terms.locations.grid}, pay one ${terms.resources.runway} and place it as
${terms.technology.emergencyInfrastructure}. On ${terms.locations.renewable}, pay two
${terms.resources.runway} and place it as ${terms.technology.cleanInfrastructure}. The Energy
location determines the source; there is no separate source choice. This mode unlocks in Era II.
Each Energy hex has three Generator slots shared by all players. A Generator
does not use a Facility space, but it cannot be built when all three Generator
slots on that Energy hex are occupied.

### ${terms.actions.organize}

Choose:

- Recruit one Team at the acting piece’s destination for two ${terms.resources.runway}, then move
  one CEO or Team up to two additional adjacent hexes.
- Move your CEOs and Teams a combined total of five adjacent steps.
- Move one Facility at the acting piece’s destination to an adjacent legal
  Facility space for one ${terms.resources.runway}.

A moved Facility carries its starting-grid state, contract halves, and
${terms.technology.megaCluster} host token. Recalculate Power eligibility and
contract activity after movement. Its contract-host identity stays fixed.

### ${terms.actions.deploy}

The next ${terms.playerTracks.customer} requires:

| ${terms.playerTracks.customer} | ${terms.playerTracks.capability} required |
| ---: | ---: |
| 1 | 2 |
| 2 | 4 |
| 3 | 6 |
| 4 | 8 |
| 5 | 10 |

Spend one ${terms.resources.compute} and gain one ${terms.playerTracks.customer}. ${terms.locations.consumer} waives the ${terms.resources.compute} cost.
Every ${terms.actions.deploy} adds one ${terms.playerTracks.scrutiny}.

### ${terms.actions.influence}

Move normally, then choose one legal effect:

- On ${terms.locations.media}, ${terms.locations.government}, or ${terms.locations.capital}, gain one
  ${terms.playerTracks.trust} or remove one ${terms.playerTracks.scrutiny}. ${terms.locations.media}
  removes one additional ${terms.playerTracks.scrutiny}; ${terms.locations.government} gains one
  additional ${terms.playerTracks.trust}.
- At one of your Facilities, create a Joint Venture using that Facility and an
  eligible rival Facility, or terminate one named Joint Venture you share.

Political control uses the CEO, Teams, and Facilities already on the board.
The ${terms.actions.influence} Action creates no separate presence piece.

## Rules Reference

## 8. Printed ${terms.infrastructure.power} contracts

<!-- power-contracts:start -->
The two ordinary contracts are printed at their point of use. The
${terms.locations.grid} tile always constructs
${terms.technology.emergencyInfrastructure}; the ${terms.locations.renewable}
tile always constructs ${terms.technology.cleanInfrastructure}. Fusion's full
contract is printed on its Era IV Program card. No separate Power Source
cards are used. Each player has one ordinary Generator, and each Energy hex
still has three shared slots.
<!-- power-contracts:end -->

Every connected ordinary Generator operates automatically during Production.

### ${terms.technology.cleanInfrastructure}

- Location: ${terms.locations.renewable}
- Cost: two ${terms.resources.runway}
- Capacity: three ${terms.infrastructure.power}
- Gain one ${terms.playerTracks.trust} when constructed
- No recurring penalty

### ${terms.technology.emergencyInfrastructure}

- Location: ${terms.locations.grid}
- Cost: one ${terms.resources.runway}
- Capacity: four ${terms.infrastructure.power}
- Add one ${terms.playerTracks.scrutiny} during every Production

### ${terms.technology.advancedGeneration}

The Era IV ${terms.systems.escalation} described above.

## 9. Printed card authorities

<!-- card-authority:start -->
Faction boards, Governance Board Era panels, map-tile Power contracts, Core
Action cards, shared Program cards, Mandate cards, Training cards, player aids, and
Headline cards are rules components. The [**Card and Board Reference**](/docs/card-reference.html)
projects every authored face in one document; resolve that text or the matching
physical surface. Printed text changes only the field or timing it
names; it does not create an unprinted phase or additional Action.
<!-- card-authority:end -->

All Factions and CEOs are fictional and imply no real-world claim or
endorsement. Every Faction has one persistent institutional identity and one
signature ability. Timing is **passive**, **once per Era**, **once when
unlocked**, or **once per game**. “Persists” remains available; “named Era
only” expires at Era end. Faction abilities modify named timing windows; they
add no phase.

During setup, use each Faction board’s printed starts and place its already
earned public ${terms.playerTracks.mandate}. Award that ${terms.playerTracks.mandate} once; never score it
again. The Faction board is authoritative if a summary elsewhere differs.

A Headline is revealed before secret action selection. Resolve its printed
effect and duration. Leave it face up in its Era row. Three Headlines per Era
form the twelve-card **${terms.systems.futureTimeline}**. A Headline grants no Action. Unless
its text names this Era’s Production, its rules expire at the end of the
current cycle.

When an effect immediately resolves one Facility's printed production, resolve
only that Facility. Do not run a second Production calculation, reopen Power
trading, or update unrelated Facilities.

<!-- era-panels:start -->
These four panels are printed on the Governance Board. Move the Current Era
marker between them; no separate Era cards are used. The board prints the
rules and unlock text. The longer setting text is reproduced here and in the
World and Institutions companion.
<!-- era-panels:end -->

<!-- player-aids:start -->
Each player receives one foldout containing the following three panels: the turn sequence, local Power, and public Mandate.
Each player uses one foldout.
<!-- player-aids:end -->

<!-- headline-selection:start -->
Use all sixteen Headlines in their printed Era decks. Resolve the listed procedure and rules text.
<!-- headline-selection:end -->

## 10. Map and component reference

Use the [**Component Reference**](/docs/component-reference.html) for the
supported inventory, deck contracts, and component states. The
[**Card and Board Reference**](/docs/card-reference.html) prints exact effects
from component records. Keep these references beside the Core Rules during play.

<!-- components:start -->
<!-- inventory:start -->
Pack the components in the labelled trays and Era packets described below.

### Shared Governance Board

The box includes one rigid folding Governance Board. It is the public table
organizer and modular-map frame, not a fixed printed map.

It provides:

- one center well, six inner-ring wells, and twelve outer-ring wells for the
  nineteen district tiles;
- four printed Era panels, Headline wells, Mandate wells, a Current Era path,
  and twelve Future Timeline positions;
- a shared Mandate track, Initiative position, and writable Current Mandate
  ledger with one row per faction;
- Setup and final Collective Trust, unresolved Systemic Risk, Dossier result,
  winner, and World Ending fields;
- six shared Program-card positions;
- six numbered Joint Venture pair bays, six numbered Mega-Cluster pair bays,
  and one Fusion position; and
- staging for the Audit bag, Scrutiny, Systemic Risk, Power cubes, Temporary
  Compute, and unused contract pairs.

The Grid and Renewable tiles print ordinary Power contracts. Fusion's contract
is printed on its shared Program card. Tile wells retain pieces but create no
extra rules state.

### One prepacked faction tray per player

Each of the six trays contains:

- 1 faction board with six captive sliders: Runway, Compute, Capability,
  Customers, Trust, and Research Protection
- ${content.gameConfig.playerSupply.ceos} CEO
- ${content.gameConfig.playerSupply.teams} Teams
- ${content.gameConfig.playerSupply.facilities} Facilities, numbered 1–${content.gameConfig.playerSupply.facilities}
- ${content.gameConfig.playerSupply.generators} Generator
- ${content.gameConfig.playerSupply.startingGridIdentifiers} integrated starting-grid identifier on Facility 1; Facilities are
  constructed in number order
- ${content.gameConfig.playerSupply.scrutinyCubes} ${terms.playerTracks.scrutiny} cubes
- 1 Mandate marker
- ${content.gameConfig.playerSupply.programMarkers} Program markers
- ${content.gameConfig.playerSupply.coreActionCards} Core Action cards
- ${content.gameConfig.playerSupply.agiDossierCards} Era-labelled ${terms.systems.agi} Dossier cards with symmetrical backs and Commit / Hedge
  orientations
- 1 three-panel foldout player aid

There is no private Program hand, Escalation slider, Safety
currency, personal score sheet, Grid-Ready piece, Power Source selector,
Influence cube, Prediction Bag token, AGI chart, or AGI die.

Generators do not count against the Facility limit.

### Shared components

- ${content.gameConfig.sharedSupply.governanceBoards} Governance Board
- ${content.gameConfig.board.selectedTileCount} district tiles: Frontier, six operational, and twelve public
- ${content.gameConfig.sharedSupply.sharedProgramCards} shared Program cards
- ${content.gameConfig.sharedSupply.currentEraMarkers} Current Era marker
- ${content.gameConfig.sharedSupply.sharedDryEraseMarkers} shared fine-tip dry-erase marker
- 16 Headline cards; reveal 12 per game
- 12 Mandate cards; reveal 4 per game
- 40 Training cards
- ${content.gameConfig.sharedSupply.jointVenturePairs} matched Joint Venture pairs
- ${content.gameConfig.sharedSupply.megaClusterPairs} matched Mega-Cluster pairs
- 1 Fusion Demonstrator marker
- 18 Systemic Risk pieces, tactually identical to Scrutiny while concealed
- 1 opaque Audit bag
- 1 Initiative marker
- ${content.gameConfig.sharedSupply.powerAllocationMarkers} silver Power cubes
- ${content.gameConfig.sharedSupply.temporaryComputeTokens} distinct Temporary Compute tokens for Allocation Window

The six faction trays supply six Mandate markers, twelve Program markers, and
six player aids.

Fusion is a single shared project; its dedicated marker leaves the supply once
constructed. Unused contract tokens cannot be reserved; create a Joint Venture
or Mega-Cluster only while a matched pair is available.

### Setup packaging

The insert provides six labelled faction trays, four labelled Era packets, one
shared Program well, one Training well, and one contract/power well. Era packets
contain `5 / 4 / 3 / 4` Headlines plus three Mandates each.

### Exact printed-paper count

The game contains 134 standard cards plus 6 foldout player aids:

- 36 Core Actions
- 6 shared Programs
- 16 Headlines
- 12 Mandates
- 40 Training cards
- 24 AGI Dossier cards
- 6 foldout player aids

Printed Era panels and Power contracts are part of the Governance
Board, tiles, and Program cards.

### Excluded deferred content

The supported box does not require Tactics, Secret Objectives, Specialists, or
Patrons.

### Production form

Power cubes remain on powered Facilities and satisfied Mega-Cluster demand
until the next Allocate step. A built Facility without a cube is offline.
Board dimensions, fold pattern, material, writable finish, and retention
tolerances remain manufacturing decisions; the zones and quantities above are
mechanical requirements.
<!-- inventory:end -->

### Deck contracts

#### Training deck: 40 cards

- Four copies of each of seven domains: 28
- Four Curated Corpus
- Four Benchmark Leak
- Four Human Evaluation

Discard every revealed card after a run. If the deck empties, resolve the
current card, shuffle the discard, and continue.

#### Headline decks

Each Era deck contains every card for that Era. Reveal three each Era. Leave every resolved card face
up in its Era row to form the twelve-card ${terms.systems.futureTimeline}.

#### Shared Program display

Place all six Program cards face up. They are public rules surfaces, not player
hands. Each player tracks use with two faction-coloured Program markers. A
marker on a Program means that player has used that named Program this game.

#### Deferred Tactic deck: 36 cards

Tactics are absent from the baseline game and evidence; see **Optional Tactic
Rules** for their contracts.

### Defined markers and effects

- **Remove ${terms.playerTracks.scrutiny}:** return the stated number of your
  cubes from the Audit bag to your supply. If fewer are present, remove as many
  as possible.
- **Research Protection:** refresh to one at Era start; Orisonix refreshes to
  two. Spend one when a duplicate appears to discard it and bank the run. It is
  not a tradeable resource.
- **Latest Production snapshot:** during Allocate, remove the prior snapshot,
  then place one Power cube on each powered Facility and one per satisfied unit
  of Mega-Cluster demand. Leave every cube in place until the next Allocate.
  Built Facilities without cubes are offline. This visible snapshot governs
  Mandates, the Dossier, powered-Facility Headlines, and final penalties.
- **Current Mandate ledger:** after revealing the Era Mandate, write its
  criterion and minimum. Use one public row per faction to retain only the
  value that card asks the table to count. Reset this-Era values; evaluate
  current-state criteria when scored.
- **Dossier orientation:** place the current Era's Dossier face down with its
  arrow toward the table center for Commit or toward its owner for Hedge. Never
  inspect a filed card before the Era IV reveal.
- **Offline recovery:** reassess local Power eligibility every Production. Facilities never flip.
<!-- components:end -->

## 11. Final scoring

All earned ${terms.playerTracks.mandate} is already on the public track. Do not score it again.

At game end:

1. Read the twelve ${terms.systems.headlines} in the ${terms.systems.futureTimeline} aloud, Era by Era.
2. Lose one ${terms.playerTracks.mandate} for each offline Facility.
3. Name the ordinary winner under the tie breakers below as the provisional
   winner; a complete tie remains a provisional joint victory.
4. Resolve the highest supported Dossier claim described above.
5. Resolve the shared World Ending.
6. Announce the final institutional winner only after reading the history it
   claims to have won.

Offline penalties cannot reduce a player below zero ${terms.playerTracks.mandate}.

There is no other endgame scoring.

### The shared World Ending

Determine one institutional winner and one shared ending from visible state
and the recorded final Audit and Dossier resolution:

- Record whether an eligible highest-strength claim formed ${terms.systems.agi}.
- Total every player’s final ${terms.playerTracks.trust}.
- Use the unresolved Systemic Risk count recorded immediately after the final
  Audit and before the bag was rebuilt.

${terms.systems.agi} emerges only when one fully paid Publication claim has at
least two supported evidence modules and wins the deterministic strength
comparison. Otherwise it does not emerge. Never infer emergence from
${terms.playerTracks.capability} alone or an unsupported commitment.

Then determine whether the ending is **Open**. It is Open only if both
conditions are true:

- Final Collective ${terms.playerTracks.trust} is at least Setup Collective ${terms.playerTracks.trust} plus the player
  count.
- Unresolved Systemic Risk is lower than the player count.

Collective ${terms.playerTracks.trust} is every player’s total; individuals need not exceed their
own starting value.

If either Open condition fails, the ending is **Closed**. An ${terms.systems.agi}
selection does not by itself make the ending Open.

Cross the two results to find the shared World Ending:

| | Open | Closed |
| --- | --- | --- |
| ${terms.systems.agi} emerges | **The Singularity** | **The Closed Loop** |
| ${terms.systems.agi} does not emerge | **The Plural Future** | **Assured Continuity** |

Read its narrative from [**World and Institutions**](/docs/world-and-institutions.html). Facilities and control
score no separate endgame ${terms.playerTracks.mandate}.

Keep the draft secret objectives out of the baseline game, balance evidence,
and duration evidence.

The highest-${terms.playerTracks.mandate} institution under the following tie breakers is the
provisional winner before Dossier resolution. The strongest eligible claim then
either replaces that result or leaves it intact as described above.

Ties break by:

1. Higher ${terms.playerTracks.trust}
2. More ${terms.playerTracks.customers}
3. More ${terms.resources.compute}
4. Joint victory accompanied by an extremely serious merger announcement

Find design rationale and balance qualification in
[**Balance and Exploitability**](/docs/balance-and-exploitability.html). Find observation
protocols in [**Playtesting and Evidence**](/docs/playtesting-and-evidence.html).

## Document record

**Rules version:** ${game.rulesVersion}
**Design-baseline date:** July 26, 2026
**Status:** Controlled playtest candidate; synchronized with executable game ${game.executableVersion}
**Provisional time:** ${game.physicalTestDuration} at four players; three- and five-player durations require their own blind tests
**Standard game:** ${facts.shared.roundsWord | capitalize} Eras, ${facts.shared.cyclesPerRoundWord} turns per player per Era
