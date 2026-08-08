# ${content.worldCopy.title}
## A strategy game about institutions turning reliable AI capability into contested public authority as they build, deploy, regulate, and race to declare ${terms.systems.agi}

**Suggested player count:** ${game.suggestedPlayerRange}

## Play profiles

**Default Game** is authoritative in this book, the browser, and simulation.
Use the browser **First Game Guide** for an accelerated Default Game.
[**Advanced Play**](/docs/advanced-play.html) is an extension layer with additional complexity.
**Advanced Play** is selected before setup and must be used for the entire game or not used at all.

The symbol **◆** marks a rule that changes in Advanced Play.
Use the base rule in Default Game, then apply the corresponding change from
the [**Advanced Play supplement**](/docs/advanced-play.html).

The separately printed [**World and Institutions**](/docs/world-and-institutions.html) companion contains setting
and ending narratives.

## How to Play

Default Game lasts four Eras. The institution with the most ${terms.playerTracks.mandate} wins; resolve that winner and the shared World Ending separately. Follow the numbered sections in order.

## 1. Setup

1. ${terms.actions.build} the thirteen-tile board as described in **Modular hex board**:
   ${terms.locations.frontier} in the center, the shuffled six-tile operational ring around it,
   and the shuffled six-tile public ring in the evenly spaced outer positions.
2. Separate the ${terms.systems.headline} cards by Era. **◆** Use only the
   Default-eligible cards: cards without an **Advanced Play** badge. Shuffle
   each eligible Era deck and place it beside its Era card. Each Era uses three
   ${terms.systems.headlines}.
   Leave room below the four Era cards for the twelve-card ${terms.systems.futureTimeline}.
3. Shuffle the Training deck. Separate the twelve Era ${terms.playerTracks.mandate} cards into
   four three-card Era decks. Shuffle each deck and place it beside the
   matching Era card.
4. Place ${terms.resources.runway}, ${terms.resources.compute}, ${terms.playerTracks.customer}, ${terms.resources.safety}, ${terms.actions.influence}, ${terms.playerTracks.scrutiny}, Systemic Risk,
   Policy Shield, Market Access, ${terms.actions.build} discount, Economic Benchmark, Grid-Ready, ${terms.infrastructure.power}
   Source, Joint Venture, ${terms.technology.megaCluster}, Expert, Spotlight,
   Public ${terms.actions.research} Grant, Initiative, and Audit bag components
   within reach.
5. Each player chooses or receives one Faction. Take its board, six Core
   Actions, seven ${terms.systems.escalations}, CEO, three Teams, four Facilities, two
   Generators, markers, and starting resources.
6. Place every CEO and one Team at ${terms.locations.frontier}. Keep the other two Teams in
   supply. Set each Faction’s ${terms.resources.runway}, ${terms.resources.compute}, ${terms.playerTracks.capability}, ${terms.playerTracks.customers}, ${terms.playerTracks.trust},
   and ${terms.resources.safety} to its printed starting values.
7. Place each Faction’s already-earned public ${terms.playerTracks.mandate} on the shared track as
   printed on its Faction board. Put every player’s ten ${terms.playerTracks.scrutiny}
   cubes outside the bag; the bag begins empty.
8. Add every Faction’s printed starting ${terms.playerTracks.trust} and record the result as
   **Setup Collective ${terms.playerTracks.trust}** on the Era reference. This fixed value is used
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
2. Every player secretly selects one unused Core Action, or spends one Escalation
   token to select one unlocked Escalation.
3. Reveal every selected action simultaneously.
4. Resolve clockwise from Initiative.
5. **Select:** the revealed Action is the only Action this turn.
6. **Move:** choose one acting piece and move it zero, one, or two adjacent
   hexes.
7. **Act:** read the chosen Action card from top to bottom and resolve it from
   the destination.
8. Exhaust the Core Action, or spend the Escalation token and flip the Escalation.
9. Pass Initiative clockwise before the next cycle.

Selection commits the Action card; choose the piece, path, target, and payment
during resolution.

### Acting piece

The acting piece is a CEO or Team. Both can take any Action; a CEO contributes
two presence and a Team one. Its destination determines where Facilities and
power infrastructure may be built, where Research and Deploy occur, which
location bonus applies, and which political spaces may be Influenced.

Facilities, ${terms.actions.influence} cubes, Generators, and Experts cannot act. ${terms.actions.organize}
receives normal acting-piece movement before its additional movement,
recruitment, restructuring, or relocation.

### Effect precedence ◆

Apply these sources in order:

- The Era card determines globally unlocked actions.
- A Faction board modifies those actions.
- The current ${terms.systems.headline} supplies its printed global effect.
- An ordinary turn may apply the Action, one destination bonus, one Faction
  modifier, and each applicable global effect.
- Every exception is timed **before selection**, **during movement**, **during
  action**, or **after action**.
- A ${terms.systems.headline} changes one named field or calls one public choice procedure. It
  grants no additional Action.
- Readying a card makes it available for a later choice. Resolve nothing when
  you ready it.
- ${terms.technology.agentSwarm} is the sole compound-action exception.

### What an Era teaches

Systems are inactive before their Era card lists them under **New this Era**.
Read that strip aloud before revealing the Mandate. All Era cards,
Escalations, and Faction abilities are open information.

Escalation is cumulative. Progress teaches ordinary institutional work;
Capacity adds industrial infrastructure; Authority adds agreements, quantum
record disputes, and public effects; Continuity adds compound Actions, declarations, and exceptional
generation. Later Eras retain previously unlocked systems
unless a printed effect says otherwise.

### Universal tie rule

Whenever an effect targets the player with the lowest, highest, or most of
something and multiple players tie, target the tied player nearest Initiative
clockwise. An effect that explicitly applies to everyone, or explicitly awards
all tied players, overrides this rule.

Initiative is an order, not a resource. Passing it after each cycle changes who
resolves first and who wins unresolved ties; it cannot be traded or retained.

### Escalation tokens and ${terms.systems.escalations}

Spend one token to select an Era-unlocked Escalation:

- Select an ${terms.systems.escalation} instead of a Core Action.
- Commit and spend one Escalation token.
- Flip the ${terms.systems.escalation} after resolution.
- Each named ${terms.systems.escalation} is usable once per player per game.
- Unspent Escalation tokens expire at Era end.
- Previously unlocked unused ${terms.systems.escalations} remain available later.

**Global after movement** means the acting piece moves normally, then the
Action resolves without a destination restriction.

| Era | Tokens | Newly available ${terms.systems.escalations} |
| --- | ---: | --- |
| I — ${terms.eras.demo} | 0 | None |
| II — ${terms.eras.scale} | 1 | ${terms.technology.megaCluster}, Reorganization |
| III — ${terms.eras.narrative} | 1 | Open Weights, Narrative Capture |
| IV — ${terms.eras.claim} | 2 | ${terms.technology.agentSwarm}, Declare ${terms.systems.agi}, ${terms.technology.advancedGeneration} |

${terms.technology.agentSwarm} is the selected Escalation; it resolves and exhausts two
different unused Core Actions.

### A committed Action that becomes blocked

After reveal, choose any legal piece, movement, mode, target, payment, and
immediate trade, but never replace the selected Action.

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

A zero-to-six track affecting regulation, Joint Ventures, safety, and the
final declaration. Zero ${terms.playerTracks.trust} does not eliminate a player.

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
- Printed ${terms.playerTracks.mandate} from ${terms.systems.headlines}, Era Mandates, Fusion, faction abilities,
  and ${terms.systems.agi}.

Threshold awards are permanent; later losses do not reverse them.

There is no hidden or deferred conversion of Facilities, controlled hexes,
stored resources, or unused cards into ${terms.playerTracks.mandate}. If an effect scores ${terms.playerTracks.mandate}, move
the public marker when that effect resolves.

### Universal costs and caps

Apply resource caps immediately after any gain or trade:

- ${terms.resources.runway}: twelve
- ${terms.resources.compute}: ten
- ${terms.resources.safety}: three, except a printed Faction limit

Return excess. A trade cannot move resources through a player above a cap.

When effects change a cost, apply replacements and waivers first, then
surcharges, then discounts. The final cost cannot fall below zero.

## 4. Modular hex board

The board is one jurisdiction whose districts represent physical and
institutional dependencies rather than ordinary distance. The [**Map reference**](/map-reference.html)
is authoritative for its thirteen-tile setup, adjacency, ring pools, tile
effects, Facility spaces, presence, and control. The shuffled map remains
fixed for all four Eras. **◆**

One movement step crosses one shared tile edge; an acting CEO or Team may move
zero, one, or two steps. Every piece placed during setup begins at
${terms.locations.frontier}. Rival pieces coexist; there is no combat or player
elimination.

### ${terms.infrastructure.power} connections ◆

Default Game uses **local Power**, not a Network graph. The starting grid
powers only its assigned first Facility. Each Generator powers only Facilities
on its own hex or an adjacent hex. A Facility cannot pass Power onward to
another Facility.

Recalculate local eligibility whenever a Facility or Generator moves; do not
preserve a connection the visible board no longer supports.

### Contract hosts

Joint Ventures and Mega-Clusters use shared, matched token pairs. Create one
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

### ${terms.infrastructure.power} delivery ◆

${terms.infrastructure.power} is Production capacity and cannot be stored.

- Every player begins with a basic one-${terms.infrastructure.power} grid connection. It automatically
  powers that player’s first Facility, requires no recurring payment,
  and cannot supply the additional demand of ${terms.technology.megaCluster}. It is
  dedicated capacity and cannot be sold. Place the
  player’s starting-grid marker on that first Facility.
- Every Facility needs one delivered ${terms.infrastructure.power} to produce.
- A ${terms.technology.megaCluster} needs two additional ${terms.infrastructure.power}.
- The starting-grid marker and each Generator’s own or
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

## 5. Four-Era escalation

### Era I — ${terms.eras.demo}

- Three turns per player
- Only Core Actions
- Beneficial or mildly disruptive ${terms.systems.headlines}
- No Escalation tokens

Era I activates movement, Core Actions, Training, the starting grid,
Facilities, Customers, and Scrutiny.

### Era II — ${terms.eras.scale} ◆

Each player receives one Escalation token and unlocks:

- Generators
- Mega-Clusters
- ${terms.systems.escalations}

#### ${terms.technology.megaCluster}

Spend three ${terms.resources.runway} and two ${terms.resources.compute} to place a ${terms.technology.megaCluster} across the edge
between two adjacent host Facilities. Construction does not require either
host to have received ${terms.infrastructure.power} previously. It adds two ${terms.playerTracks.scrutiny} when constructed.
Place one matched ${terms.technology.megaCluster} token half on each host Facility.

The acting piece must end on either host Facility’s hex.

A **solo ${terms.technology.megaCluster}** uses two adjacent Facilities that are each eligible for
your local Power. During Production, power both hosts plus two additional demand
to gain three ${terms.resources.compute}.

A **joint ${terms.technology.megaCluster}** uses one adjacent, locally powered Facility from each
consenting participant. The lead names the partner and hosts. Rejection,
pass, or no response uses the Escalation; no replacement partner. The lead
pays two ${terms.resources.runway} and one ${terms.resources.compute}; the partner pays one of each. During Production,
each powers its host plus one additional demand. If all demand is met, the
lead gains two ${terms.resources.compute} and the partner one.

Hosts must remain adjacent for the project to operate.

#### Reorganization

Reorganization is global after movement.

Move every Team up to one hex.

You may return one Team to supply to gain three ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny}.
Reorganization never resolves or readies another Action.

### Era III — ${terms.eras.narrative}

Each player receives one Escalation token. Previous ${terms.systems.escalations} remain
unlocked. Joint Ventures and immediate ${terms.infrastructure.power} purchases now enter play.

#### Open Weights

Open Weights is global after movement.

Every player gains one ${terms.playerTracks.capability}. You also gain:

- Two ${terms.playerTracks.trust}
- Place one ${terms.actions.influence} cube from supply, or relocate one of yours, on ${terms.locations.media},
  ${terms.locations.government}, or ${terms.locations.capital}
- Removal of one ${terms.playerTracks.scrutiny} cube

#### Narrative Capture

Narrative Capture is global after movement.

Move or place three ${terms.actions.influence} cubes among ${terms.locations.media}, ${terms.locations.government}, and ${terms.locations.capital}.
Then choose one:

- Remove two of your ${terms.playerTracks.scrutiny} cubes.
- Gain two ${terms.resources.runway}.
- Give a player with more ${terms.playerTracks.customers} than you one ${terms.playerTracks.scrutiny}.

### Era IV — ${terms.eras.claim}

Each player receives two Escalation tokens.

Agent Swarms, ${terms.systems.agi} declarations, Fusion, and exceptional faction programs now
enter play.

#### ${terms.technology.agentSwarm}

Select ${terms.technology.agentSwarm} only with two different unused Core Actions. Move once;
resolve both from that destination in either order and pay all costs. Apply the
visit bonus to only one. Exhaust both, flip ${terms.technology.agentSwarm}, and add three ${terms.playerTracks.scrutiny}.

#### Declare ${terms.systems.agi}

Requirements:

- ${terms.playerTracks.capability} nine or higher
- At least three ${terms.playerTracks.customers}
- At least three grid-ready Facilities
- ${terms.playerTracks.trust} two or higher
- Spend three ${terms.resources.compute}

Declare ${terms.systems.agi} is global after movement. Check every requirement when it
resolves.

A **grid-ready Facility** has a Grid-Ready marker earned during a completed
Production. After allocating Power, place one on each Facility receiving its
complete Facility demand. Return it immediately if that Facility relocates or
loses its legal Power connection, or during any Production when it lacks full
Power.

To declare ${terms.systems.agi}, check three existing markers. Do not run a second Production
calculation. A Facility built, moved, linked, or reconnected after the most
recent Production must operate successfully in a later Production before
receiving or regaining one. A Facility built in Era IV cannot support a
declaration that Era.

The first valid declaration scores seven ${terms.playerTracks.mandate}. Later declarations score
five. Every declaration adds three ${terms.playerTracks.scrutiny}.

Play continues after a declaration; victory does not require one.

#### ${terms.technology.advancedGeneration}

The acting piece must end movement on the ${terms.locations.grid}. Spend
${facts.shared.advancedGeneration.runwayCostWord} ${terms.resources.runway} and construct ${terms.technology.advancedGenerationShort} there. It uses a dedicated ${terms.technology.advancedGenerationShort} marker,
occupies one of that tile’s three Generator slots, provides ${facts.shared.advancedGeneration.powerWord} ${terms.infrastructure.power}, scores
${facts.shared.advancedGeneration.mandateWord} ${terms.playerTracks.mandate}, and adds ${facts.shared.advancedGeneration.scrutinyWord} ${terms.playerTracks.scrutiny}. ${terms.technology.advancedGenerationShort} counts as an owned Generator for
local Power eligibility and ${terms.infrastructure.power} capacity. It does not count
against the owner’s two ordinary Generator-piece limit. If all three Grid
Generator slots are occupied, ${terms.technology.advancedGenerationShort} cannot be constructed. A full ${terms.locations.grid}
blocks construction.

## 6. Era sequence

### A. Begin the quarter

- Advance to the next fixed Era card.
- Read that Era’s **New this Era** strip aloud. Those systems are now active.
- Reveal one ${terms.playerTracks.mandate} from the current Era’s three-card deck. Return the other
  two cards in that deck to the box unseen.
- Ready all six Core Actions.
- Award Escalation tokens.
- The lowest-scoring player receives one Public ${terms.actions.research} Grant, spendable as
  one ${terms.resources.runway} or one ${terms.resources.compute}.
- The highest-scoring player receives the Spotlight:
  - Their first ${terms.actions.fund} gains one additional ${terms.resources.runway}.
  - Their first ${terms.actions.deploy}, ${terms.technology.megaCluster}, ${terms.technology.agentSwarm}, or ${terms.systems.agi} declaration adds one
    additional ${terms.playerTracks.scrutiny}.

Use the universal tie rule. If everyone has equal ${terms.playerTracks.mandate}, award neither
marker; no player receives both from a universal tie.

### B. Three action cycles

At the beginning of each cycle:

1. Reveal a ${terms.systems.headline} and place it in the current Era’s ${terms.systems.futureTimeline} row.
2. Everyone secretly **selects** one Action card.
3. Reveal simultaneously.
4. Resolve clockwise from Initiative: **move**, then **act**.
5. Pass Initiative clockwise.

#### Immediate resource trade ◆

Immediately before or after Act, the active player may make one complete
resource offer to one rival, naming each type and amount. That rival accepts
or rejects, or publishes one complete counteroffer. The original offer-maker
accepts or rejects that counteroffer. Rejection, pass, or no response ends the
window; do not redirect or renegotiate. A counteroffer cannot receive another
counteroffer.
${terms.resources.runway}, ${terms.resources.compute}, and ${terms.resources.safety} tokens may be exchanged. Every accepted component changes hands
immediately; promises about later turns are not binding. The active
${terms.systems.headline} may prohibit a named resource from being traded.

Without acceptance, continue the selected Action; resolve it as blocked if no
legal resolution remains.

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

Every player board presents the same five Production boxes. Resolve a box for
every player before advancing to the next box:

1. **Generate:** determine every Generator’s local eligible Facilities. Every
   Generator with at least one eligible Facility operates automatically. Add one ${terms.playerTracks.scrutiny} for every
   ${terms.technology.emergencyInfrastructure}. Add any ${terms.systems.headline} generation.
2. **Trade ◆:** in Initiative order, each player may make one ${terms.infrastructure.power}
   purchase request to one adjacent rival Power connection. The named supplier accepts
   or rejects. A rejected, passed, or unanswered request fails; the buyer then
   allocates with the ${terms.infrastructure.power} they have. An accepted buyer pays one
   ${terms.resources.runway} per ${terms.infrastructure.power} directly to the consenting supplier. Each supplier may sell
   at most one ${terms.infrastructure.power} this Production. Only installed Generator or Fusion
   capacity may be sold; starting-grid and emergency ${terms.infrastructure.power} may not.
3. **Allocate:** add starting-grid, Generator, purchased, and emergency ${terms.infrastructure.power};
   allocate it only to legal local Facilities and Mega-Clusters.
   Place a Grid-Ready marker on every Facility receiving its complete demand;
   return the marker from every Facility that does not.
4. **Produce:** produce powered Facilities, one ${terms.resources.runway} per ${terms.playerTracks.customer},
   and active Mega-Clusters, in that order.
5. **Partner:** produce active Joint Ventures in ascending contract-number
   order.

Complete each box for every player before entering the next. Do not let one
player finish Production while others still generate, trade, or allocate. This
keeps sales and contracts tied to one visible capacity state. Within a box,
resolve in Initiative order unless that box specifies otherwise.

Purchased ${terms.infrastructure.power} lasts only this Production and creates no contract or
future obligation. A supplier may leave its own Facility offline.

Apply the universal resource caps after every Production gain.

### D. ${terms.systems.publicAudit}

Risky actions add player-colored ${terms.playerTracks.scrutiny} to the opaque Audit bag. Each
player has ten cubes. For each required cube when all ten are already in the
bag, immediately pay one ${terms.resources.runway} or lose one ${terms.playerTracks.trust}; take the available option if
only one exists. If neither exists, suffer no further loss. A depleted supply
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

In Eras I–III, each colored cube makes its owner pay one ${terms.resources.runway} or lose one
${terms.playerTracks.trust}. Take the available option if only one exists; if neither exists, suffer
no further loss.

In Era IV, each colored cube makes its owner pay two ${terms.resources.runway} or lose one
${terms.playerTracks.mandate}. The payment is indivisible. With fewer than two ${terms.resources.runway}, lose one
${terms.playerTracks.mandate} if possible; at zero ${terms.playerTracks.mandate}, reduce ${terms.resources.runway} to zero. ${terms.playerTracks.mandate} cannot fall
below zero.

Drawn player-colored cubes return to the owner’s supply; undrawn cubes remain
in the bag.

${terms.locations.media} Facilities may remove cubes before the draw. A drawn black Systemic
Risk cube gives every player with at least three ${terms.playerTracks.customers} the current Era’s
penalty, then returns to supply. Apply the same availability rules. Black cubes
remaining at game end are unresolved Systemic Risk.

### E. Score the ${terms.playerTracks.mandate}

Each Era ${terms.playerTracks.mandate} has a minimum qualification. If nobody qualifies, nobody
scores it. Otherwise the qualifying leader scores two ${terms.playerTracks.mandate}; tied qualifying
leaders score one ${terms.playerTracks.mandate} each.

Compare only the revealed Mandate’s printed criterion. Resources, control, and
public score do not break its tie. Leave the scored card beside its Era as part
of the table’s public history.

The revealed Mandate card is the exact qualification and scoring authority.
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

When a duplicate appears, the player may spend one ${terms.resources.safety} token to discard
that duplicate and immediately bank the current provisional ${terms.playerTracks.capability}. A
${terms.locations.research} visit may do this once during that run without spending
${terms.resources.safety}. ${terms.locations.research} protection and ${terms.resources.safety} have the same timing and result; neither
allows the run to continue after the duplicate.

Special cards:

- **Curated Corpus:** choose one ordinary domain not yet revealed this run. It
  counts as that domain and adds one provisional ${terms.playerTracks.capability}. If every ordinary
  domain is already present, it is a duplicate.
- **Benchmark Leak:** add two provisional ${terms.playerTracks.capability} and one ${terms.playerTracks.scrutiny}. It is
  not a domain. Its ${terms.playerTracks.capability} is lost if the run later crashes.
- **Licensed Dataset:** pay one ${terms.resources.runway} and continue, or decline, bank the
  current provisional ${terms.playerTracks.capability}, and end the run.
- **Synthetic Loop:** the first copy revealed in a run counts as the unique
  special domain **Loop** and adds one provisional ${terms.playerTracks.capability}. A later
  Synthetic Loop is a duplicate. After the first Loop resolves, the next
duplicate of any kind cannot be protected by ${terms.resources.safety}, a ${terms.locations.research} visit, or
  a Faction ability.
- **Human Evaluation:** gain one ${terms.playerTracks.trust}, immediately bank all provisional
  ${terms.playerTracks.capability}, and end the run.

### ${terms.actions.build} ◆

Choose one mode.

**Facility ${terms.actions.build}** means Construct a Facility. **Infrastructure ${terms.actions.build}** means
Construct a Generator.
${terms.technology.megaCluster} and
${terms.technology.advancedGeneration} are ${terms.systems.escalations}. A ${terms.actions.build} discount applies to them only when an
effect names them explicitly.

#### Construct a Facility

Pay two ${terms.resources.runway} and place a Facility on the acting piece’s hex. It requires one
${terms.infrastructure.power} during Production. Each non-${terms.locations.frontier} hex has only two Facility spaces;
${terms.locations.frontier} has none and is never a legal Facility destination. Facilities cannot
be destroyed by rivals.

#### Construct a Generator

The acting piece must be on an Energy hex. Pay the selected ${terms.infrastructure.power} Source’s
cost and place a Generator with its source card. This mode unlocks in Era II.
Each Energy hex has three Generator slots shared by all players. A Generator
does not use a Facility space, but it cannot be built when all three Generator
slots on that Energy hex are occupied.

### ${terms.actions.organize}

Choose:

- Recruit one Team at the acting piece’s destination for two ${terms.resources.runway}, then move
  one CEO, Team, or Expert up to two additional adjacent hexes.
- Move your CEOs, Teams, and Experts a combined total of five adjacent steps.
- Move one Facility at the acting piece’s destination to an adjacent legal
  Facility space for one ${terms.resources.runway}.

A moved Facility carries its starting-grid marker, contract halves, and
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

Place or relocate up to two of your ${terms.actions.influence} cubes among the acting piece’s
current or adjacent ${terms.locations.media}, ${terms.locations.government}, or ${terms.locations.capital} hexes. A relocated cube may
come from any hex. Then choose one ${terms.actions.influence} effect. You may choose an effect
even if you place or relocate no cubes:

- Gain one ${terms.playerTracks.trust}.
- Remove one ${terms.playerTracks.scrutiny}.
- Create a Joint Venture with an eligible rival.
- Terminate one named Joint Venture you share.

## Rules Reference

## 8. ${terms.infrastructure.power} Source cards

Two shared ordinary Power Source reference cards are never claimed or consumed.
Set one Source selector when each Generator is built.

Any Energy-hex Generator may use either source, without limit. Generator pieces
and each Energy hex’s three slots provide scarcity.

Every connected ordinary Generator operates automatically during Production.

### ${terms.technology.cleanInfrastructure}

- Cost: three ${terms.resources.runway}
- Capacity: three ${terms.infrastructure.power}
- Gain one ${terms.playerTracks.trust} when constructed
- No recurring penalty

### ${terms.technology.emergencyInfrastructure}

- Cost: two ${terms.resources.runway}
- Capacity: four ${terms.infrastructure.power}
- Add one ${terms.playerTracks.scrutiny} during every Production

### ${terms.technology.advancedGeneration}

The Era IV ${terms.systems.escalation} described above.

## 9. Printed card authorities

Faction boards, Core Action cards, Escalation cards, Era cards, Mandate cards,
Training cards, Power cards, and Headline cards are rules components. The
[**Card reference**](/card-reference.html) projects every card face in one document; resolve that text
or the matching physical card. Card text changes only the field or timing it
names; it does not create an unprinted phase or additional Action.

All Factions and CEOs are fictional and imply no real-world claim or
endorsement. Faction abilities unlock in their named Era. Timing is
**passive**, **once per Era**, **once when unlocked**, or **once per game**.
“Persists” remains available; “named Era only” expires at Era end. Every
faction board uses the same four-row reading order: Core identity, Scale
program, Narrative program, then Claim program. Those rows modify named timing
windows; they add no phase.

During setup, use each Faction board’s printed starts and place its already
earned public ${terms.playerTracks.mandate}. Award that ${terms.playerTracks.mandate} once; never score it
again. The Faction board is authoritative if a summary elsewhere differs.

A Headline is revealed before secret action selection. Resolve its printed
effect and duration. Leave it face up in its Era row. Three Headlines per Era
form the twelve-card **${terms.systems.futureTimeline}**. A Headline grants no Action. Unless
its text names this Era’s Production, its rules expire at the end of the
current cycle.

## 10. Map and component reference

Use [**Map reference**](/map-reference.html) for setup, adjacency, location effects, presence, and
control. Use [**Component reference**](/component-reference.html) for deck contracts, component limits, and
defined markers. Use [**Card reference**](/card-reference.html) for every card face. Those references
are part of the Default Game, not optional background.
## 11. Final scoring

All earned ${terms.playerTracks.mandate} is already on the public track. Do not score it again.

At game end:

1. Read the twelve ${terms.systems.headlines} in the ${terms.systems.futureTimeline} aloud, Era by Era.
2. Lose one ${terms.playerTracks.mandate} for each offline Facility.
3. Resolve the shared World Ending.
4. Announce the highest-${terms.playerTracks.mandate} institution only after reading the history it
   claims to have won.

Offline penalties cannot reduce a player below zero ${terms.playerTracks.mandate}.

There is no other endgame scoring.

### The shared World Ending

Determine one institutional winner and one shared ending from visible state:

- Count the ${terms.systems.agi} declarations.
- Total every player’s final ${terms.playerTracks.trust}.
- Count unresolved Systemic Risk cubes remaining in the Audit bag.

First determine whether ${terms.systems.agi} emerges. It emerges if:

- At least one declaring institution finishes the game at ${terms.playerTracks.capability} nine or
  higher.

Then determine whether the ending is **Open**. It is Open only if both
conditions are true:

- Final Collective ${terms.playerTracks.trust} is at least Setup Collective ${terms.playerTracks.trust} plus the player
  count.
- Unresolved Systemic Risk is lower than the player count.

Collective ${terms.playerTracks.trust} is every player’s total; individuals need not exceed their
own starting value.

If either Open condition fails, the ending is **Closed**. A qualified ${terms.systems.agi}
declaration does not by itself make the ending Open.

Cross the two results to find the shared World Ending:

| | Open | Closed |
| --- | --- | --- |
| ${terms.systems.agi} emerges | **The Singularity** | **The Closed Loop** |
| ${terms.systems.agi} does not emerge | **The Plural Future** | **Assured Continuity** |

Read its narrative from [**World and Institutions**](/docs/world-and-institutions.html). Facilities and control
score no separate endgame ${terms.playerTracks.mandate}.

Keep the draft secret objectives out of the baseline game, balance evidence,
and duration evidence.

Highest ${terms.playerTracks.mandate} wins.

Ties break by:

1. Higher ${terms.playerTracks.trust}
2. More ${terms.playerTracks.customers}
3. More ${terms.resources.compute}
4. Joint victory accompanied by an extremely serious merger announcement

Find design rationale and balance qualification in
[**Balance and Exploitability**](/docs/balance-and-exploitability.html). Find observation
protocols in [**Playtesting and Evidence**](/docs/playtesting-and-evidence.html).

## Advanced Play

The separate [**Advanced Play supplement**](/docs/advanced-play.html) is the complete authority for the
bundled Advanced profile. Do not import one Advanced procedure into Default
Game.
## Document record

**Rules version:** ${game.rulesVersion}
**Design-baseline date:** July 26, 2026
**Status:** Controlled playtest candidate; synchronized with executable game ${game.executableVersion}
**Provisional time:** ${game.physicalTestDuration} at four players; three- and five-player durations require their own blind tests
**Standard game:** ${facts.shared.roundsWord | capitalize} Eras, ${facts.shared.cyclesPerRoundWord} turns per player per Era
