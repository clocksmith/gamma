# ${game.title}

## A ${game.playerRange} player race to build, deploy, regulate, and plausibly declare ${terms.systems.agi}

**Suggested player count:** ${game.suggestedPlayerRange}

**Rules version:** ${game.rulesVersion}
**Design-baseline date:** July 26, 2026
**Status:** Controlled playtest candidate; synchronized with executable game ${game.executableVersion}
**Provisional time:** ${game.physicalTestDuration} at four players; three- and five-player durations require their own blind tests
**Standard game:** ${facts.shared.roundsWord | capitalize} rounds, ${facts.shared.cyclesPerRoundWord} turns per player per round

The game begins as recognizable technology strategy and ends with agent
swarms, emergency governance, orbital-compute proposals, public ${terms.systems.agi}
declarations, and competitors jointly financing infrastructure they expect to
weaponize against one another.

The world remains solemn. Nobody acknowledges that this is ridiculous.

### Tone contract

${game.title} uses **solemn institutional absurdity**. Every impossible
technology is presented as a responsible quarterly initiative. The escalation
is structural:

- **${content.referenceCards.byId.era_demo.name}:** ${content.referenceCards.byId.era_demo.loreText}
- **${content.referenceCards.byId.era_scale.name}:** ${content.referenceCards.byId.era_scale.loreText}
- **${content.referenceCards.byId.era_narrative.name}:** ${content.referenceCards.byId.era_narrative.loreText}
- **${content.referenceCards.byId.era_claim.name}:** ${content.referenceCards.byId.era_claim.loreText}

Flavor text may sharpen this escalation but never replaces or modifies a
card’s rules text. The game does not wink at the player, make allegations
about living people or real companies, or use randomness as a substitute for
a consequential choice. Early cards must give both positions an intelligible
case. Later cards may become frightening, polarized, and difficult to
reconcile, but the dystopia must be produced by defensible local decisions
rather than by players selecting an obviously evil button.

Darkness is reported at institutional distance. Cards may acknowledge
synthetic suffering, civic abandonment, displacement, or human loss through
audits, filings, minutes, dashboards, notices, and second-hand testimony. They
do not stage first-person torment, body horror, or voyeuristic suffering. The
unsettling effect comes from institutions treating harm as an administrable
output.

The ${terms.systems.futureTimeline} is one compounding history, not an anthology. Because
only three of six ${terms.systems.headlines} appear in each Era, later cards may inherit
intensified pressures but never require or name a specific earlier ${terms.systems.headline}.

### How to win

After Round IV, the institution with the most ${terms.playerTracks.mandate} wins. ${terms.playerTracks.mandate} is scored
publicly as players gain ${terms.playerTracks.customers}, cross ${terms.playerTracks.capability} and ${terms.playerTracks.trust} thresholds, win
Round Mandates, and resolve exceptional programs. Declaring ${terms.systems.agi} is powerful
but optional; it is one path through the game, not its required conclusion.

The winning institution and the world’s ending are separate results. A player
may win the institutional race while helping create the Closed Loop, or lose
the race inside a future where genuine ${terms.systems.agi} remains answerable to humanity.

## 1. Setup

1. ${terms.actions.build} the thirteen-tile board as described in **Modular hex board**:
   ${terms.locations.frontier} in the center, the shuffled six-tile operational ring around it,
   and the shuffled six-tile public ring in the evenly spaced outer positions.
2. Separate the ${terms.systems.headline} cards by Era. Shuffle each six-card Era deck and
   place it beside the matching Era card. Each Era will use three ${terms.systems.headlines}.
   Leave room below the four Era cards for the twelve-card ${terms.systems.futureTimeline}.
3. Shuffle the Training deck. Separate the twelve Round ${terms.playerTracks.mandate} cards into
   four three-card Era decks. Shuffle each deck and place it beside the
   matching Era card.
4. Place ${terms.resources.runway}, ${terms.resources.compute}, ${terms.playerTracks.customer}, ${terms.resources.safety}, ${terms.actions.influence}, ${terms.playerTracks.scrutiny}, Systemic Risk,
   Policy Shield, Market Access, ${terms.actions.build} discount, Economic Benchmark, Grid-Ready, ${terms.infrastructure.power}
   Source, Link, Joint Venture, ${terms.technology.megaCluster}, Expert, Spotlight,
   Public ${terms.actions.research} Grant, Initiative, Audit bag, and Volatility components
   within reach.
5. Each player chooses or receives one Faction. Take its board, six Core
   Actions, seven ${terms.systems.wildActions}, CEO, three Teams, four Facilities, two
   Generators, markers, and starting resources.
6. Place every CEO and one Team at ${terms.locations.frontier}. Keep the other two Teams in
   supply. Set each Faction’s ${terms.resources.runway}, ${terms.resources.compute}, ${terms.playerTracks.capability}, ${terms.playerTracks.customers}, ${terms.playerTracks.trust},
   and ${terms.resources.safety} to its printed starting values.
7. Place each Faction’s already-earned public ${terms.playerTracks.mandate} on the shared track as
   listed under **Starting public ${terms.playerTracks.mandate}**. Put every player’s ten ${terms.playerTracks.scrutiny}
   cubes outside the bag; the bag begins empty.
8. Add every Faction’s printed starting ${terms.playerTracks.trust} and record the result as
   **Setup Collective ${terms.playerTracks.trust}** on the Era reference. This is a reference value,
   not another track.
9. Choose Initiative randomly and give that player the Initiative marker.
   Begin Round I.

Do not deal Tactics or secret objectives in the baseline game.

## 2. Central loop

Every player controls an asymmetric AI institution.

Each player has six Core Action cards but takes only three turns per round.
Once played, a Core Action remains exhausted until the next round:

- ${terms.actions.fund}
- ${terms.actions.research}
- ${terms.actions.build}
- ${terms.actions.organize}
- ${terms.actions.deploy}
- ${terms.actions.influence}

Players do not perform all six actions in a fixed sequence. The twelve
standard-game turns ask which three of six institutional functions matter in
each era. The other three actions remain unused unless an explicit ability
readies one.

Examples:

- Round I: ${terms.actions.research} → ${terms.actions.build} → ${terms.actions.deploy}
- Round II: ${terms.actions.fund} → ${terms.actions.organize} → ${terms.technology.megaCluster}
- Round III: ${terms.actions.research} → ${terms.actions.influence} → Open Weights

> You have six institutional capabilities, but only enough time to use three
> of them this quarter.

### The complete ordinary turn: Select → Move → Act

1. Reveal one ${terms.systems.headline}.
2. Every player secretly selects one unused Core Action, or one unlocked Wild
   Action plus one Escalation token.
3. Reveal every selected action simultaneously.
4. Resolve clockwise from Initiative.
5. **Select:** the revealed Action is the only Action this turn.
6. **Move:** choose one acting piece and move it zero, one, or two adjacent
   hexes.
7. **Act:** read the chosen Action card from top to bottom and resolve it from
   the destination.
8. Exhaust the Core Action, or spend the Escalation token and flip the Wild
   Action.
9. Pass Initiative clockwise before the next cycle.

Players commit only the action during selection. The acting piece, movement
path, target, and exact payment remain open until resolution.

### Acting piece

The acting piece is either the player’s CEO or one Team. Both have identical
action authority. The CEO contributes two presence; a Team contributes one.

The acting piece determines where a Facility may be built, which location
bonus applies, where ${terms.actions.research} occurs, which market receives a Deployment,
which adjacent political or media spaces may be Influenced, and where power
infrastructure may begin.

Facilities, ${terms.actions.influence} cubes, Generators, and Experts cannot act. ${terms.actions.organize}
receives normal acting-piece movement before its additional movement,
recruitment, restructuring, or relocation.

Use one authority per rules layer:

- The Era card determines globally unlocked actions.
- A Faction board modifies those actions.
- The global-state layer contains the current ${terms.systems.headline} and every persistent
  ${terms.systems.headline} effect.
- An ordinary turn may apply the Action, one destination bonus, one Faction
  modifier, and each applicable global effect, subject to field precedence.
- Every exception is timed **before selection**, **during movement**, **during
  action**, or **after action**.
- A ${terms.systems.headline} changes one named field or creates one public choice regime. It
  never grants another Action.
- If the current ${terms.systems.headline} and a persistent ${terms.systems.headline} would change the same
  printed field, the current ${terms.systems.headline} temporarily overrides the older effect.
- A printed field may be modified by only one global effect at a time.
  Persistent effects modifying other fields remain active.
- Readying a card changes a later choice; it never resolves that card now.
- ${terms.technology.agentSwarm} is the sole compound-action exception.
- A ${terms.systems.headline} whose effect lasts beyond its cycle is placed beside the affected
  Action card as a reminder. There is no separate Law system or Law deck.

### What an Era teaches

The Era card is the only authority that introduces a new rules family. A
system listed under **New this Era** is inactive before that Era, even if its
components or later cards are visible. When an Era begins, read its
**New this Era** strip aloud before revealing the Round Mandate.

This staged teach changes rules exposure, not strategic visibility. Players
may inspect every later Era card, Wild Action, and faction ability during
setup. The future is visible; only its operating rules arrive gradually.

### Universal tie rule

Whenever an effect targets the player with the lowest, highest, or most of
something and multiple players tie, target the tied player nearest Initiative
clockwise. An effect that explicitly applies to everyone, or explicitly awards
all tied players, overrides this rule.

### Escalation tokens and ${terms.systems.wildActions}

Escalation tokens are spent, not permanent unlock markers. Every player has
seven ${terms.systems.wildAction} cards. The Era card determines which ones are legal.

- Select a ${terms.systems.wildAction} instead of a Core Action.
- Commit and spend one Escalation token.
- Flip the ${terms.systems.wildAction} after resolution.
- Each named ${terms.systems.wildAction} is usable once per player per game.
- Unspent Escalation tokens expire at round end.
- Previously unlocked unused ${terms.systems.wildActions} remain available later.

| Round | Tokens | Newly available ${terms.systems.wildActions} |
| --- | ---: | --- |
| I — ${terms.eras.demo} | 0 | None |
| II — ${terms.eras.scale} | 1 | ${terms.technology.megaCluster}, Reorganization |
| III — ${terms.eras.narrative} | 1 | Open Weights, Narrative Capture |
| IV — ${terms.eras.claim} | 2 | ${terms.technology.agentSwarm}, Declare ${terms.systems.agi}, ${terms.technology.advancedGeneration} |

Players receive four ${terms.systems.wildAction} uses across the game but choose among seven
possibilities. ${terms.technology.agentSwarm} is itself the selected ${terms.systems.wildAction}, then resolves
and exhausts two different unused Core Actions.

### A committed Action that becomes blocked

After reveal, the selected Action remains committed. At resolution, the player
may choose any currently legal acting piece, movement, mode, target, and
payment, including an immediate trade. They may not replace the revealed card
with another Action.

If an earlier resolution consumed every legal Facility space, Generator slot,
contract token, or other required target, the blocked player may still resolve
movement. The selected Action then exhausts without effect. No compensation is
awarded. Initiative is therefore part of spatial competition rather than a
reason to rewind simultaneous selection.

## 3. Resources

### ${terms.resources.runway}

Money, financing, and organizational endurance. Spend it on Facilities,
hiring, partnerships, lobbying, and crisis management.

### ${terms.resources.compute}

Training and inference capacity. Spend it on ${terms.actions.research}, ${terms.actions.deploy}, and major
infrastructure.

### ${terms.playerTracks.capability}

A permanent model-quality track. ${terms.playerTracks.capability} is not normally spent. It unlocks
stronger deployments and ${terms.systems.agi} declarations.

### ${terms.playerTracks.customers}

Products deployed into the world. Each ${terms.playerTracks.customer} produces one ${terms.resources.runway} during
Production. ${terms.playerTracks.customers} #1–3 immediately score two public ${terms.playerTracks.mandate} each when
gained; ${terms.playerTracks.customers} #4–5 score one each. ${terms.playerTracks.customers} also increase public
exposure.

### ${terms.playerTracks.trust}

A track from zero to six. ${terms.playerTracks.trust} helps with regulation, Joint Ventures, safety
decisions, and the final declaration. Low ${terms.playerTracks.trust} limits final options but does
not eliminate a player.

Victory points are called **${terms.playerTracks.mandate}**. Players persuade markets, institutions,
customers, and history that their organization won the era; they do not prove
metaphysical intelligence.

${terms.playerTracks.mandate} is normally scored immediately on one public track:

- Two when ${terms.playerTracks.customer} #1, #2, or #3 is gained; one when #4 or #5 is gained.
- Two the first time ${terms.playerTracks.capability} reaches three, six, nine, and twelve, except
  for a printed faction scoring rule.
- Two the first time ${terms.playerTracks.trust} reaches two, four, and six.
- Printed ${terms.playerTracks.mandate} from ${terms.systems.headlines}, Round Mandates, Fusion, faction abilities,
  and ${terms.systems.agi}.

Threshold awards are permanent after they are scored; later loss of ${terms.playerTracks.trust}
does not reverse public history.

There is no hidden or deferred conversion of Facilities, controlled hexes,
stored resources, or unused cards into ${terms.playerTracks.mandate}. If an effect scores ${terms.playerTracks.mandate}, move
the public marker when that effect resolves.

### Universal costs and caps

Resource caps apply immediately whenever resources are gained or traded:

- ${terms.resources.runway}: twelve
- ${terms.resources.compute}: ten
- ${terms.resources.safety}: three, except a printed Faction limit

Return excess to the shared supply. A trade cannot move resources through a
player above a cap.

When effects change a cost, apply replacements and waivers first, then
surcharges, then discounts. The final cost cannot fall below zero.

## 4. Modular hex board

Use thirteen hexagonal tiles in a sixfold-symmetric layout:

- One ${terms.locations.frontier}
- Two ${terms.actions.research} Campuses
- Two Cloud Regions
- One ${terms.locations.consumer}
- One ${terms.locations.chip}
- One ${terms.locations.capital}
- One ${terms.locations.talent}
- One ${terms.locations.media}
- One ${terms.locations.government}
- One ${terms.locations.grid}
- One ${terms.locations.renewable}

Place ${terms.locations.frontier} in the center. The six inner spaces form the **operational
ring**. Place the six **public ring** spaces at evenly spaced radius-two
positions. Each public-ring space touches two neighboring operational-ring
spaces, producing six identical spatial arms instead of a rectangular row
layout.

Shuffle the following inner pool and place it around ${terms.locations.frontier}:

- One ${terms.locations.research}
- One ${terms.locations.cloud}
- One ${terms.locations.chip}
- One ${terms.locations.capital}
- One ${terms.locations.talent}
- The ${terms.locations.grid}

Shuffle the following outer pool among the six outer positions:

- One ${terms.locations.research}
- One ${terms.locations.cloud}
- One ${terms.locations.consumer}
- One ${terms.locations.media}
- One ${terms.locations.government}
- One ${terms.locations.renewable}

This guarantees
that the first ring contains ${terms.actions.research}, ${terms.resources.compute}, ${terms.actions.build}, ${terms.actions.fund}, ${terms.actions.organize}, and
${terms.infrastructure.power} support without fixing their adjacency. Consumer, Media, and Government
remain scarce outer-ring destinations.

Every piece placed on the board during setup begins at ${terms.locations.frontier}. A movement of
two reaches every space from the center. Once pieces leave the center, opposing
outer spaces are four hexes apart, so later positioning, Teams, Networks, and
negotiated adjacency matter. The board footprint is spatially symmetric; the
shuffled economic layout is intentionally not.

Every non-${terms.locations.frontier} hex has a visit bonus, two Facility spaces, a Facility
production effect, and a control value used by ${terms.systems.headlines} and Mandates. ${terms.locations.frontier}
has no Facility spaces.

### Presence and control

- CEO: two presence
- Team: one presence
- Facility: one presence
- ${terms.actions.influence} cube on Media, Government, or Capital: one presence

The player with the most presence controls the hex. Ties mean nobody controls
it.

The Government controller’s vote counts twice during Government votes. This
is a control benefit, not a visit bonus.

There is no combat and no player elimination. Rival pieces coexist.
Competition comes from Facility scarcity, control, positioning, voting,
deals, and ${terms.systems.headlines}.

### Location effects

| Location | Visit bonus | Facility production | Contract icon |
| --- | --- | --- | --- |
| ${terms.actions.research} | Once this ${terms.systems.trainingRun}, protect one duplicate as if spending ${terms.resources.safety} | Gain one ${terms.resources.safety} token | ${terms.resources.compute} |
| Cloud | First ${terms.resources.compute} cost is reduced by one | Gain two ${terms.resources.compute} | ${terms.resources.compute} |
| Consumer | ${terms.actions.deploy} costs zero ${terms.resources.compute} | Gain one ${terms.resources.runway} | ${terms.resources.runway} |
| ${terms.locations.chip} | ${terms.actions.build} costs one less ${terms.resources.runway} | Gain one ${terms.resources.compute} and one ${terms.actions.build} discount | ${terms.resources.compute} |
| Capital | ${terms.actions.fund} gains one ${terms.resources.runway} | Gain two ${terms.resources.runway} | ${terms.resources.runway} |
| Talent | Recruit costs one less ${terms.resources.runway} | Move one Team one hex during Production | ${terms.resources.runway} |
| Media | ${terms.actions.influence} may place or relocate one additional cube | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| Government | ${terms.actions.influence} may place or relocate one additional cube on Government | Gain one Policy Shield | ${terms.resources.runway} |
| ${terms.locations.grid} | Infrastructure ${terms.actions.build} costs one less | Gain one ${terms.resources.compute} | ${terms.resources.compute} |
| ${terms.locations.renewable} | ${terms.technology.cleanInfrastructure} costs one less ${terms.resources.runway} | Remove one ${terms.playerTracks.scrutiny} before Audit | ${terms.resources.runway} |
| ${terms.locations.frontier} | After Act, you may gain one ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny} | No Facility spaces | None |

${terms.locations.frontier}’s optional ${terms.resources.runway} is resolved after the selected Action and does not
modify that Action’s printed output. It may be used once by each acting player
who ends movement at ${terms.locations.frontier}; it never creates Facility production or
${terms.playerTracks.mandate}. The central district offers bridge financing because nobody is
permitted to own the horizon.

### ${terms.systems.infrastructureNetwork}

Each player’s ${terms.systems.infrastructureNetwork} exists from setup. Its starting-grid
connection operates in Round I. Generators, Links, Mega-Clusters,
and the Network production bonus unlock in Round II.

Each player has two Link tokens. The same graph governs ${terms.infrastructure.power} delivery and the
Network production bonus:

- The first Facility joins through the basic grid connection.
- Owned Facilities and Generators on the same or adjacent hexes connect to one
  another.
- A Link on one otherwise disconnected Facility joins that Facility to the
  ${terms.systems.infrastructureNetwork}. Owned sites adjacent to it may then connect
  normally.
- ${terms.infrastructure.power} from connected Generators and purchased ${terms.infrastructure.power} is pooled across the
  Network.
- Beginning in Round II, two or more connected, powered Facilities produce one
  additional ${terms.resources.runway} or ${terms.resources.compute}.

A player receives only one Network bonus regardless of Network size. There is
no separate ${terms.infrastructure.power} graph, production graph, or edge-by-edge flow calculation.

### Contract hosts

Joint Ventures and every ${terms.technology.megaCluster} use neutral
matched token pairs from the shared supply. A project can be created only while
its matching pair remains available. Place one numbered half on each host
Facility. The matching number identifies the contract even if Realignment moves
the districts.

A contract remains owned after Realignment but is active only while its two
named host Facilities are adjacent and satisfy its other requirements, unless
a Faction ability explicitly changes that range. The tokens travel with their
Facilities. No player may silently substitute a different Facility after the
contract is signed.

Every cross-player contract or jointly funded project requires the explicit
consent of every participant. Facilities sharing one hex are **co-located**,
not adjacent; adjacency requires their hexes to share an edge.

### Joint Venture

${terms.actions.influence} may create a Joint Venture between two adjacent Facilities owned by
different players, unless a Faction ability explicitly changes that range.
Both host Facilities must be powered during Production for the contract to
produce.

Each partner gains one resource shown by the **contract icon on the other
partner’s host tile**: one ${terms.resources.runway} for a ${terms.resources.runway} icon or one ${terms.resources.compute} for a
${terms.resources.compute} icon. This contract output is not the tile’s full printed production
and is never multiplied by another Facility effect.

While resolving ${terms.actions.influence}, the active player may make one complete Joint
Venture proposal naming the two eligible host Facilities and the partner. The
named partner accepts or rejects it. A rejection, pass, or missing response
creates no contract and uses that ${terms.actions.influence} action’s Joint Venture effect; it
cannot instead remove ${terms.playerTracks.scrutiny}, gain ${terms.playerTracks.trust}, or name a replacement partner.

During their own ${terms.actions.influence} action, either participant may instead terminate one
named Joint Venture they share. Return that pair’s matched token halves to the
shared supply. Termination is that Action’s selected effect; it cannot be
combined with creating a Joint Venture, removing ${terms.playerTracks.scrutiny}, or gaining
${terms.playerTracks.trust}.

### ${terms.systems.realignment}

${terms.systems.realignment} occurs exactly once: after ${terms.playerTracks.mandate} scoring in Round
III. It does not occur after Rounds I, II, or IV. Every player secretly chooses
one of their three Realignment ballots, then all ballots are revealed
simultaneously:

- **Consolidate the Core:** rotate the six inner-ring locations one position
  clockwise.
- **Expand the Periphery:** rotate the six outer-ring locations one position
  clockwise.
- **Authorize Counter-Cycle:** rotate the inner ring one position clockwise
  and the outer ring one position counterclockwise.

Before any optional discussion, every player secretly places one ballot face
down. A player who does not place a ballot has **no ballot**: it names no
motion and cannot resolve a tie. Reveal all placed ballots simultaneously. The
motion with the most ballots resolves. If leading motions tie, begin with the
Initiative player and scan clockwise; the first player whose ballot names one
of the tied motions selects the result. If none does, the Initiative player
selects among the tied motions. Government bonuses and other vote modifiers do
not alter Realignment ballots.

${terms.locations.frontier} never moves. Each moving location tile carries every CEO, Team,
Facility, Generator, ${terms.actions.influence} cube, Expert, and other site-bound component on
it. Rotate the selected physical ring once, then recalculate the single
${terms.systems.infrastructureNetwork} from the starting-grid Facility, Links, and visible
adjacency. Nothing is lifted or re-laid.

Ring rotation moves the district, not the Facility for Grid-Ready purposes.
Realignment does not remove a Grid-Ready marker merely because its tile
rotated. After recalculating each ${terms.systems.infrastructureNetwork}, return a Grid-Ready
marker only from a Facility that is now outside its owner’s Network.

Joint Ventures remain in force but produce only while their matched host
Facilities are adjacent and all printed requirements are met. Immediate
${terms.infrastructure.power} purchases never persist through Realignment. A ${terms.technology.megaCluster} whose matched host Facilities
are no longer adjacent is offline until they become adjacent again.
Realignment never destroys a component, changes a host, or terminates a
contract.

The ballots are open information before selection and secret information until
the simultaneous reveal. Players may discuss and make public, non-binding
signals about their intended ballot; agreement is unnecessary and promises
about the vote are not binding. Every player still casts exactly one secret
ballot, and the vote and tie-break procedure above decide the result. Because
Realignment happens before Round IV, every player receives three final Actions
in which to respond to the changed geography.

### ${terms.infrastructure.power} delivery

${terms.infrastructure.power} is spatial infrastructure, not a stored resource.

- Every player begins with a basic one-${terms.infrastructure.power} grid connection. It automatically
  connects to that player’s first Facility, requires no Link or recurring payment,
  and cannot supply the additional demand of ${terms.technology.megaCluster}. It is
  dedicated capacity and cannot be sold. Place the
  player’s starting-grid marker on that first Facility.
- Every Facility needs one delivered ${terms.infrastructure.power} to produce.
- A ${terms.technology.megaCluster} needs two additional ${terms.infrastructure.power}.
- The ${terms.systems.infrastructureNetwork} connects ${terms.infrastructure.power} to Facilities.

Production uses the fixed resolution order in **${terms.infrastructure.power} and Production**. ${terms.infrastructure.power}
capacity never produces resources by itself and may not be assigned twice.

Capacity is pooled inside the same ${terms.systems.infrastructureNetwork} used for the
production bonus; there is no second connectivity check.

An offline Facility still contributes presence, occupies its Facility space,
and may be visited. It produces nothing and provides no Network bonus. It
automatically returns online in any later Production where enough ${terms.infrastructure.power} is
assigned.

## 5. Four-round escalation

### Round I — ${terms.eras.demo}

The world has seen the prototype. Nobody knows whether it works.

- Three turns per player
- Only Core Actions
- Beneficial or mildly disruptive ${terms.systems.headlines}
- No Escalation tokens

This round teaches Select → Move → Act, movement, basic ${terms.actions.research}, the starting
grid, Facilities, ${terms.playerTracks.customers}, and ${terms.playerTracks.scrutiny}. Generators, Links,
agreements, Government votes, and ${terms.systems.wildActions} are not yet active.

Its controversies remain recognizable and unresolved: cheap intelligence can
expand access or erase livelihoods; open weights can distribute authority or
remove containment; safety can be stewardship or incumbent protection.

### Round II — ${terms.eras.scale}

Capital, chips, talent, and electricity become the real product.

Each player receives one Escalation token and unlocks:

- Generators
- Links and the Network production bonus
- Mega-Clusters
- ${terms.systems.wildActions}

Benefits now arrive through physical concentration. Data centers stabilize
services and consume counties. Automation removes dangerous labor and removes
workers. Dedicated power makes new capability possible and makes the public
dependent on private infrastructure.

#### ${terms.technology.megaCluster}

Spend three ${terms.resources.runway} and two ${terms.resources.compute} to place a ${terms.technology.megaCluster} across the edge
between two adjacent host Facilities. Construction does not require either
host to have received ${terms.infrastructure.power} previously. It adds two ${terms.playerTracks.scrutiny} when constructed.
Place one matched ${terms.technology.megaCluster} token half on each host Facility.

The acting piece must end movement on either host Facility’s hex. This is the
${terms.technology.megaCluster} Action destination.

A **solo ${terms.technology.megaCluster}** uses two of your adjacent Facilities, both in your
${terms.systems.infrastructureNetwork}. During Production, supply both hosts’ normal
Facility demand plus two additional ${terms.infrastructure.power} from that Network. If
all demand is satisfied, gain three ${terms.resources.compute}.

A **joint ${terms.technology.megaCluster}** uses one host Facility from each consenting
participant. The lead names the partner and both eligible hosts; the named
partner accepts or rejects once. Rejection, pass, or no response ends that
construction attempt, uses the Wild Action, and permits no replacement
partner. The hosts must be adjacent and each must belong to its owner’s
${terms.systems.infrastructureNetwork}. The lead pays two ${terms.resources.runway} and one ${terms.resources.compute}; the partner
pays one ${terms.resources.runway} and one ${terms.resources.compute}. During Production, each participant supplies
their host’s normal Facility demand plus one additional
${terms.infrastructure.power} from their own Network. If all demand is satisfied, the lead gains two
${terms.resources.compute} and the partner gains one ${terms.resources.compute}.

Its host Facilities must remain adjacent for the ${terms.technology.megaCluster} to operate.
Round III Realignment may place it offline without destroying it.

#### Reorganization

Reorganization is global after movement; its destination creates no additional
target restriction.

Move every Team up to one hex.

You may return one Team to supply to gain three ${terms.resources.runway} and add one ${terms.playerTracks.scrutiny}.
Reorganization never resolves or readies another Action.

### Round III — ${terms.eras.narrative}

${terms.playerTracks.capability} is no longer enough. The public must understand it correctly—or at
least repeatedly.

Each player receives one Escalation token. Previous ${terms.systems.wildActions} remain
unlocked. Joint Ventures, immediate ${terms.infrastructure.power} purchases, Government votes, and
${terms.systems.headlines} with persistent effects now enter play.

The table is no longer debating isolated products. It is choosing who may
define evidence, personhood, ownership, and legitimate authority. Coalitions
form, shared facts narrow, and formerly technical decisions become political
identities.

#### Open Weights

Open Weights is global after movement; its destination creates no additional
target restriction.

Every player gains one ${terms.playerTracks.capability}. You also gain:

- Two ${terms.playerTracks.trust}
- Place one ${terms.actions.influence} cube from supply, or relocate one of yours, on Media,
  Government, or Capital
- Removal of one ${terms.playerTracks.scrutiny} cube

#### Narrative Capture

Narrative Capture is global after movement; its destination creates no
additional target restriction.

Move or place three ${terms.actions.influence} cubes among Media, Government, and Capital.
Then choose one:

- Remove two of your ${terms.playerTracks.scrutiny} cubes.
- Gain two ${terms.resources.runway}.
- Give a player with more ${terms.playerTracks.customers} than you one ${terms.playerTracks.scrutiny}.

### Round IV — ${terms.eras.claim}

The phrase “general intelligence” is now a financing category.

Each player receives two Escalation tokens.

Agent Swarms, ${terms.systems.agi} declarations, Fusion, and exceptional faction programs now
enter play.

Local compromises become a civilizational outcome. The final question is not
whether powerful intelligence exists, but whether it remains in reciprocal
relation with living people or inherits an airtight execution loop whose
metrics outlive their purpose.

#### ${terms.technology.agentSwarm}

${terms.technology.agentSwarm} may be selected only while you have at least two different unused
Core Actions. Choose and play two of them during one turn. Resolve both and pay
all costs. Move only once. Resolve both Core Actions from that same destination
in either order. Apply the destination visit bonus to only one of the two
Actions, chosen when the first relevant Action resolves. Exhaust both Core
cards, flip ${terms.technology.agentSwarm}, and add three ${terms.playerTracks.scrutiny}.

#### Declare ${terms.systems.agi}

Requirements:

- ${terms.playerTracks.capability} nine or higher
- At least three ${terms.playerTracks.customers}
- At least three grid-ready Facilities
- ${terms.playerTracks.trust} two or higher
- Spend three ${terms.resources.compute}

Declare ${terms.systems.agi} is global after movement; its destination creates no additional
target restriction. Check every requirement when it resolves.

A **grid-ready Facility** has a Grid-Ready marker earned during a completed
Production. After allocating ${terms.infrastructure.power}, place a Grid-Ready marker on each Facility
that receives its complete Facility demand. Return that marker
immediately if the Facility is relocated by ${terms.actions.organize} or another effect, or leaves its owner’s
${terms.systems.infrastructureNetwork}. Return it during any later Production in which the
Facility does not receive its complete demand.

A Grid-Ready marker records demonstrated operation, not hypothetical capacity.
Declaring ${terms.systems.agi} requires three marked Facilities; it never runs a second
Production calculation. A Facility built, moved, linked, or
reconnected after the most recent Production must operate successfully in a
later Production before it can receive or regain the marker. Consequently, a
Facility first built during Round IV cannot support a declaration in that
same Round.

The first valid declaration scores seven ${terms.playerTracks.mandate}. Later declarations score
five. Every declaration adds three ${terms.playerTracks.scrutiny}.

Declaring ${terms.systems.agi} does not end the game and is never required to win. It is a
high-scoring commitment that competes with ${terms.playerTracks.customer}, ${terms.playerTracks.capability}, ${terms.playerTracks.trust},
Round-${terms.playerTracks.mandate}, Narrative, and infrastructure strategies for the same twelve
Actions.

#### ${terms.technology.advancedGeneration}

The acting piece must end movement on the ${terms.locations.grid}. Spend
${facts.shared.advancedGeneration.runwayCostWord} ${terms.resources.runway} and construct ${terms.technology.advancedGenerationShort} there. It uses a dedicated ${terms.technology.advancedGenerationShort} marker,
occupies one of that tile’s three Generator slots, provides ${facts.shared.advancedGeneration.powerWord} ${terms.infrastructure.power}, scores
${facts.shared.advancedGeneration.mandateWord} ${terms.playerTracks.mandate}, and adds ${facts.shared.advancedGeneration.scrutinyWord} ${terms.playerTracks.scrutiny}. ${terms.technology.advancedGenerationShort} counts as an owned Generator for
${terms.systems.infrastructureNetwork} connection and ${terms.infrastructure.power} capacity, but does not count
against the owner’s two ordinary Generator-piece limit. If all three Grid
Generator slots are occupied, ${terms.technology.advancedGenerationShort} cannot be constructed; that denial is
intentional spatial competition.

Fusion is late, expensive, politically exposed, and spatially constrained. It
competes with ${terms.technology.agentSwarm} and Declare ${terms.systems.agi} for a Round IV Escalation token.

## 6. Round sequence

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

Resolve ties for the Public ${terms.actions.research} Grant and Spotlight using the universal
Initiative-clockwise tie rule. Exception: if every player has equal ${terms.playerTracks.mandate},
award neither Spotlight nor the Public ${terms.actions.research} Grant. No player receives both
highest- and lowest-place treatment from a universal tie.

### B. Three action cycles

At the beginning of each cycle:

1. Reveal a ${terms.systems.headline} and place it in the current Era’s ${terms.systems.futureTimeline} row.
2. Roll the Volatility die only if the ${terms.systems.headline} explicitly instructs the table
   to roll or displays the Volatility icon.
3. Everyone secretly **selects** one Action card.
4. Reveal simultaneously.
5. Resolve clockwise from Initiative: **move**, then **act**.
6. Pass Initiative clockwise.

During any player’s resolution, the active player may complete one immediate
resource trade with one rival, either immediately before or immediately after
Act. The active player either declines to trade or makes one complete offer:
name the rival, timing, each resource type, and each amount. The named rival
may accept, reject, or publish one complete counteroffer naming each offered
and requested resource type and amount. If they publish a counteroffer, every
other player whose resulting transfer is legal under holdings, embargoes, and
caps may simultaneously pass or claim it. The counteroffer maker chooses one
claimant, or declines them all; a chosen claim immediately completes the trade.
This is a public-market exception: the completed counteroffer may be between
two non-active players. There are no further offers or counteroffers during
that resolution. ${terms.resources.runway}, ${terms.resources.compute}, and ${terms.resources.safety} tokens may be exchanged. Every accepted component must change hands
immediately; promises about later turns are not binding. The active
${terms.systems.headline} may prohibit a named resource from being traded.

No acceptance means no completed trade. A counteroffer with no claimant, or
with all claimants declined, expires. The active player continues the selected
Action; if the unavailable resources leave that committed Action without a
legal resolution, it resolves blocked under **A committed Action that becomes
blocked**.

${terms.actions.influence} is not required for this immediate exchange. ${terms.actions.influence} remains the
only way to create persistent Joint Ventures, lobbying effects, or
${terms.playerTracks.trust} manipulation.

### Negotiation and paced play

No agreement is a normal strategic outcome. Players may discuss publicly, but
speech creates no game state, obligation, or additional action. Only the
required formal choice in its printed window changes the game. If a player does
not give a required formal response when called upon, treat it as a rejection
or pass.

**Paced Play** is an optional table rule. Before play, the group may assign one
shared sand timer to each negotiation window. When it expires, discussion ends
and the normal rejection, pass, or no-ballot fallback applies; a timer never
creates consent or forces a deal.

### C. ${terms.infrastructure.power} and Production

Every player board presents the same five Production boxes. Resolve a box for
every player before advancing to the next box:

1. **Generate:** recalculate every ${terms.systems.infrastructureNetwork}. Every connected
   Generator operates automatically. Add one ${terms.playerTracks.scrutiny} for every
   ${terms.technology.emergencyInfrastructure}. Add any ${terms.systems.headline} generation.
2. **Trade:** in Initiative order, each player may make up to two ${terms.infrastructure.power}
   purchase requests, one to each of two different adjacent rival Networks.
   The named supplier accepts or rejects each request. A rejected, passed, or
   unanswered request fails; the buyer may use any remaining request, then
   allocates with the ${terms.infrastructure.power} they have. An accepted buyer pays one
   ${terms.resources.runway} per ${terms.infrastructure.power} directly to the consenting supplier. Each supplier may sell
   at most one ${terms.infrastructure.power} this Production. Only installed Generator or Fusion
   capacity may be sold; starting-grid and emergency ${terms.infrastructure.power} may not.
3. **Allocate:** add starting-grid, Generator, purchased, and emergency ${terms.infrastructure.power};
   allocate remaining capacity among Facilities and Mega-Clusters.
   Place a Grid-Ready marker on every Facility receiving its complete demand;
   return the marker from every Facility that does not.
4. **Produce:** produce powered Facilities, one ${terms.resources.runway} per ${terms.playerTracks.customer}, each
   player’s single Network bonus, and active Mega-Clusters, in that order.
5. **Partner:** produce active Joint Ventures in ascending contract-number
   order.

An immediate ${terms.infrastructure.power} purchase lasts only for this Production. It creates no
contract token, future obligation, or termination action. A supplier may sell
capacity even when doing so leaves one of its own Facilities offline.

Apply the universal resource caps after every Production gain.

### D. ${terms.systems.publicAudit}

Risky actions add player-colored ${terms.playerTracks.scrutiny} cubes to an opaque bag. Each player
has ten ${terms.playerTracks.scrutiny} cubes. For each ${terms.playerTracks.scrutiny} a player must add when all ten of
their cubes are already in the bag, they immediately choose to pay one ${terms.resources.runway}
or lose one ${terms.playerTracks.trust}. If only one option can be paid, take it. If neither can be
paid, leave both tracks at zero and suffer no additional loss. A depleted
physical supply never makes a risky action free.

The four-player base draws are two, three, four, and five. For other player
counts, calculate each round’s draw count as:

> round(base draws × player count ÷ 4), minimum one

Round halves upward. The resulting Audit profiles are:

| Round | 2 players | 3 players | 4 players | 5 players | 6 players |
| --- | ---: | ---: | ---: | ---: | ---: |
| I | 1 | 2 | 2 | 3 | 3 |
| II | 2 | 2 | 3 | 4 | 5 |
| III | 2 | 3 | 4 | 5 | 6 |
| IV | 3 | 4 | 5 | 6 | 8 |

Draw the listed number of cubes or stop when the bag is empty.

In Rounds I–III, each player-colored cube drawn makes its owner pay one ${terms.resources.runway}
or lose one ${terms.playerTracks.trust}. If the owner can pay only one option, they take that option.
If both tracks are already zero, leave both at zero and suffer no additional
loss.

In Round IV, each player-colored cube drawn makes its owner pay two ${terms.resources.runway} or
lose one ${terms.playerTracks.mandate}. The two-${terms.resources.runway} payment is indivisible: a player with fewer
than two ${terms.resources.runway} must lose one ${terms.playerTracks.mandate} if able. If the owner can pay only one
option, they take that option. If the owner has fewer than two ${terms.resources.runway} and zero
${terms.playerTracks.mandate}, reduce their ${terms.resources.runway} to zero and suffer no additional loss. ${terms.playerTracks.mandate}
cannot fall below zero.
The final quarter no longer accepts reputational adjustments; it revises the
historical record.

Drawn player-colored cubes return to the owner’s supply; undrawn cubes remain
in the bag.

Media Facilities may remove cubes before the draw. Some ${terms.systems.headlines} add black
Systemic Risk cubes. When one is drawn, every player with at least three
${terms.playerTracks.customers} resolves the current round’s Audit penalty: one ${terms.resources.runway} or one ${terms.playerTracks.trust}
in Rounds I–III; two ${terms.resources.runway} or one ${terms.playerTracks.mandate} in Round IV. Then the black cube
returns to the shared supply. Apply the same available-option and zero-track
rules above. Black cubes still in the bag at game end are unresolved Systemic
Risk.

### E. Score the ${terms.playerTracks.mandate}

Each Round ${terms.playerTracks.mandate} has a minimum qualification. If nobody qualifies, nobody
scores it. Otherwise the qualifying leader scores two ${terms.playerTracks.mandate}; tied qualifying
leaders score one ${terms.playerTracks.mandate} each.

#### Era I Mandates — proof before scale

- **The Quarter Humanity Notices:** gain the most ${terms.playerTracks.capability} this round;
  minimum one.
- **The Model That Ate Tuesday:** complete the successful ${terms.systems.trainingRun} with
  the most unique domains this round; minimum one unique domain.
- **Markets Prefer a Clear Destiny:** gain the most ${terms.resources.runway} from ${terms.actions.fund} actions
  this round; minimum one.

#### Era II Mandates — industrial credibility

- **The Building Has Its Own Weather:** have the most powered Facilities at
  Production; minimum one.
- **The Stack Reaches the Horizon:** satisfy the most total ${terms.infrastructure.power} demand
  during Production, counting Facilities and Mega-Clusters;
  minimum two ${terms.infrastructure.power} demand. Attribute both ${terms.infrastructure.power} to one player’s
  ${terms.technology.megaCluster}; for a joint ${terms.technology.megaCluster}, attribute one ${terms.infrastructure.power} to each partner.
- **${terms.resources.compute} Is the New Weather:** produce the most ${terms.resources.compute} during Production;
  minimum one.

#### Era III Mandates — public authority

- **Voluntary Coordination Triumphs:** create the most new Joint Ventures this
  round that are active during Production; minimum one.
- **The Legibility Offensive:** among players who completed a ${terms.actions.deploy} this
  round, have the most ${terms.playerTracks.trust}.
- **National Champion, Without the Nationalization:** control the most
  different hex categories; minimum one.

#### Era IV Mandates — history closes its books

- **A Continent Signs the LOI:** gain the most ${terms.playerTracks.customers} this round; minimum
  one.
- **Zero-Incident Quarter, Pending Review:** among players who added at least
  one ${terms.playerTracks.scrutiny} this round, add the fewest.
- **Responsible Acceleration:** among players with at least four ${terms.playerTracks.trust}, have
  the most ${terms.playerTracks.capability}; minimum one ${terms.playerTracks.capability}.

### F. Round III only: secret spatial vote

After scoring the Round III ${terms.playerTracks.mandate}, every player secretly chooses one
${terms.systems.realignment} ballot. Reveal simultaneously, rotate the winning
ring or rings once, and recalculate the single ${terms.systems.infrastructureNetwork}. Skip
this step in every other round.

## 7. Core Actions

### ${terms.actions.fund}

Choose:

- **Conservative round:** gain two ${terms.resources.runway}.
- **Venture round:** gain four ${terms.resources.runway} and add two ${terms.playerTracks.scrutiny}.

Capital provides one additional ${terms.resources.runway}.

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
${terms.resources.safety}. Campus protection and ${terms.resources.safety} have the same timing and result; neither
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
  duplicate of any kind cannot be protected by ${terms.resources.safety}, a ${terms.locations.research}, or
  a Faction ability.
- **Human Evaluation:** gain one ${terms.playerTracks.trust}, immediately bank all provisional
  ${terms.playerTracks.capability}, and end the run.

### ${terms.actions.build}

Choose one mode.

**Facility ${terms.actions.build}** means Construct a Facility. **Infrastructure ${terms.actions.build}** means
Construct a Generator or Install a Link. ${terms.technology.megaCluster} and
${terms.technology.advancedGeneration} are ${terms.systems.wildActions}, not ${terms.actions.build} modes, and receive no ${terms.actions.build}
discount unless an effect names them explicitly.

#### Construct a Facility

Pay two ${terms.resources.runway} and place a Facility on the acting piece’s hex. It requires one
${terms.infrastructure.power} during Production. Each non-${terms.locations.frontier} hex has only two Facility spaces;
${terms.locations.frontier} has none and is never a legal Facility destination. Facilities cannot
be destroyed by rivals.

#### Construct a Generator

The acting piece must be on an Energy hex. Pay the selected ${terms.infrastructure.power} Source’s
cost and place a Generator with its source card. This mode unlocks in Round II.
Each Energy hex has three Generator slots shared by all players. A Generator
does not use a Facility space, but it cannot be built when all three Generator
slots on that Energy hex are occupied.

#### Install a Link

Beginning in Round II, pay one ${terms.resources.runway} and place one of your two Link tokens on
the Facility at the acting piece’s destination. That Facility joins your
${terms.systems.infrastructureNetwork} even if it is otherwise disconnected. The Link remains
attached if the Facility moves. A Facility may hold only one Link.

### ${terms.actions.organize}

Choose:

- Recruit one Team at the acting piece’s destination for two ${terms.resources.runway}, then move
  one CEO, Team, or Expert up to two additional adjacent hexes.
- Move your CEOs, Teams, and Experts a combined total of five adjacent steps.
- Move one Facility at the acting piece’s destination to an adjacent legal
  Facility space for one ${terms.resources.runway}.

A moved Facility carries its Link, starting-grid marker,
contract halves, and ${terms.technology.megaCluster} host token. Recalculate connection and
contract activity after movement; movement never substitutes a contract host.

### ${terms.actions.deploy}

The next ${terms.playerTracks.customer} requires:

| ${terms.playerTracks.customer} | ${terms.playerTracks.capability} required |
| ---: | ---: |
| 1 | 2 |
| 2 | 4 |
| 3 | 6 |
| 4 | 8 |
| 5 | 10 |

Spend one ${terms.resources.compute} and gain one ${terms.playerTracks.customer}. Consumer waives the ${terms.resources.compute} cost.
Every ${terms.actions.deploy} adds one ${terms.playerTracks.scrutiny}.

### ${terms.actions.influence}

Place or relocate up to two of your ${terms.actions.influence} cubes among the acting piece’s
current or adjacent Media, Government, or Capital hexes. A relocated cube may
come from any hex. Then choose one ${terms.actions.influence} effect. You may choose an effect
even if you place or relocate no cubes:

- Gain one ${terms.playerTracks.trust}.
- Remove one ${terms.playerTracks.scrutiny}.
- Create a Joint Venture with an eligible rival.
- Terminate one named Joint Venture you share.

## 8. ${terms.infrastructure.power} Source cards

The game contains two shared ordinary ${terms.infrastructure.power} Source reference cards, one for
each source below. They are never claimed or consumed. Each player has two
Source selectors, one for each Generator piece, and sets the selector when
that Generator is constructed.

Any Generator built on either Energy hex may choose
${terms.technology.cleanInfrastructure} or ${terms.technology.emergencyInfrastructure}. Source
availability is unlimited and the same source may be selected repeatedly.
Generator pieces and the three Generator slots printed on each Energy hex
provide the scarcity.

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

The Round IV ${terms.systems.wildAction} described above.

## 9. Six factions

The six canonical player identities are fictional institutions led by
fictional executives. Their abilities describe institutional roles for
fictional gameplay; they are not factual claims or indications of endorsement.

Every ability unlocks at the start of its named round. Its timing tag is one
of **passive**, **once per round**, **once when unlocked**, or **once per
game**. “Persists” means it remains available in later rounds; “named round
only” means an unused opportunity expires when that round ends.

Every faction board uses the same four-row reading order. A faction with a
separate public-scoring contract prints it above these rows:

1. **Core identity:** available from Round I.
2. **Scale program:** unlocks in Round II.
3. **Narrative program:** unlocks in Round III.
4. **Claim program:** unlocks in Round IV.

Each row prints its frequency, persistence, and one timing window. These rows
do not add another phase to the round; they modify the named ordinary timing
window.

### ${terms.factions.coalition}

CEO: ${content.factions.byId.coalition_lab.chiefExecutive}.

Starts with ${content.factions.byId.coalition_lab.starts.runway} ${terms.resources.runway}, ${content.factions.byId.coalition_lab.starts.compute} ${terms.resources.compute}, and ${terms.playerTracks.trust} ${content.factions.byId.coalition_lab.starts.trust}.

- **${content.factions.byId.coalition_lab.abilities.0.name}:**
  ${content.factions.byId.coalition_lab.abilities.0.text}
- **${content.factions.byId.coalition_lab.abilities.1.name}:**
  ${content.factions.byId.coalition_lab.abilities.1.text}
- **${content.factions.byId.coalition_lab.abilities.2.name}:**
  ${content.factions.byId.coalition_lab.abilities.2.text}
- **${content.factions.byId.coalition_lab.abilities.3.name}:**
  ${content.factions.byId.coalition_lab.abilities.3.text}

### ${terms.factions.platform}

CEO: ${content.factions.byId.platform_empire.chiefExecutive}.

Starts with ${content.factions.byId.platform_empire.starts.runway} ${terms.resources.runway}, ${content.factions.byId.platform_empire.starts.compute} ${terms.resources.compute}, ${terms.playerTracks.trust} ${content.factions.byId.platform_empire.starts.trust}, and ${terms.playerTracks.customer} #${content.factions.byId.platform_empire.starts.customerOrdinal} already deployed. Its next ${terms.actions.deploy} is ${terms.playerTracks.customer} #2 and requires ${terms.playerTracks.capability} ${content.factions.byId.platform_empire.starts.nextCustomerCapability}. The starting ${terms.playerTracks.customer} is not a separate pre-track bonus.

- **${content.factions.byId.platform_empire.abilities.0.name}:**
  ${content.factions.byId.platform_empire.abilities.0.text}
- **${content.factions.byId.platform_empire.abilities.1.name}:**
  ${content.factions.byId.platform_empire.abilities.1.text}
- **${content.factions.byId.platform_empire.abilities.2.name}:**
  ${content.factions.byId.platform_empire.abilities.2.text}
- **${content.factions.byId.platform_empire.abilities.3.name}:**
  ${content.factions.byId.platform_empire.abilities.3.text}

### ${terms.factions.imperial}

CEO: ${content.factions.byId.imperial_research_lab.chiefExecutive}.

Starts with ${content.factions.byId.imperial_research_lab.starts.runway} ${terms.resources.runway}, ${content.factions.byId.imperial_research_lab.starts.compute} ${terms.resources.compute}, and ${terms.playerTracks.trust} ${content.factions.byId.imperial_research_lab.starts.trust}.

- **${content.factions.byId.imperial_research_lab.scoringRule.name}:**
  ${content.factions.byId.imperial_research_lab.scoringRule.text}
- **${content.factions.byId.imperial_research_lab.abilities.0.name}:**
  ${content.factions.byId.imperial_research_lab.abilities.0.text}
- **${content.factions.byId.imperial_research_lab.abilities.1.name}:**
  ${content.factions.byId.imperial_research_lab.abilities.1.text}
- **${content.factions.byId.imperial_research_lab.abilities.2.name}:**
  ${content.factions.byId.imperial_research_lab.abilities.2.text}
- **${content.factions.byId.imperial_research_lab.abilities.3.name}:**
  ${content.factions.byId.imperial_research_lab.abilities.3.text}

### ${terms.factions.vertical}

CEO: ${content.factions.byId.vertical_empire.chiefExecutive}.

Starts with ${content.factions.byId.vertical_empire.starts.runway} ${terms.resources.runway}, ${content.factions.byId.vertical_empire.starts.compute} ${terms.resources.compute}, and ${terms.playerTracks.trust} ${content.factions.byId.vertical_empire.starts.trust}.

- **${content.factions.byId.vertical_empire.abilities.0.name}:**
  ${content.factions.byId.vertical_empire.abilities.0.text}
- **${content.factions.byId.vertical_empire.abilities.1.name}:**
  ${content.factions.byId.vertical_empire.abilities.1.text}
- **${content.factions.byId.vertical_empire.abilities.2.name}:**
  ${content.factions.byId.vertical_empire.abilities.2.text}
- **${content.factions.byId.vertical_empire.abilities.3.name}:**
  ${content.factions.byId.vertical_empire.abilities.3.text}

### ${terms.factions.safety}

CEO: ${content.factions.byId.safety_laboratory.chiefExecutive}.

Starts with ${content.factions.byId.safety_laboratory.starts.runway} ${terms.resources.runway}, ${content.factions.byId.safety_laboratory.starts.compute} ${terms.resources.compute}, ${terms.playerTracks.trust} ${content.factions.byId.safety_laboratory.starts.trust}, and ${content.factions.byId.safety_laboratory.starts.safety} ${terms.resources.safety} tokens.

- **${content.factions.byId.safety_laboratory.abilities.0.name}:**
  ${content.factions.byId.safety_laboratory.abilities.0.text}
- **${content.factions.byId.safety_laboratory.abilities.1.name}:**
  ${content.factions.byId.safety_laboratory.abilities.1.text}
- **${content.factions.byId.safety_laboratory.abilities.2.name}:**
  ${content.factions.byId.safety_laboratory.abilities.2.text}
- **${content.factions.byId.safety_laboratory.abilities.3.name}:**
  ${content.factions.byId.safety_laboratory.abilities.3.text}

### ${terms.factions.foundry}

CEO: ${content.factions.byId.foundry.chiefExecutive}.

Starts with ${content.factions.byId.foundry.starts.runway} ${terms.resources.runway},
${content.factions.byId.foundry.starts.compute} ${terms.resources.compute}, and
${terms.playerTracks.trust} ${content.factions.byId.foundry.starts.trust}.

- **${content.factions.byId.foundry.abilities.0.name}:**
  ${content.factions.byId.foundry.abilities.0.text}
- **${content.factions.byId.foundry.abilities.1.name}:**
  ${content.factions.byId.foundry.abilities.1.text}
- **${content.factions.byId.foundry.abilities.2.name}:**
  ${content.factions.byId.foundry.abilities.2.text}
- **${content.factions.byId.foundry.abilities.3.name}:**
  ${content.factions.byId.foundry.abilities.3.text}

### Starting public ${terms.playerTracks.mandate}

During setup, place each faction’s already-earned threshold ${terms.playerTracks.mandate} on the
public track:

| Faction | ${terms.playerTracks.mandate} already represented at setup |
| --- | ---: |
| ${terms.factions.coalition} | ${content.factions.byId.coalition_lab.starts.startingPublicMandate} from ${terms.playerTracks.trust} ${content.factions.byId.coalition_lab.starts.trust} |
| ${terms.factions.platform} | ${content.factions.byId.platform_empire.starts.startingPublicMandate} total: 2 from ${terms.playerTracks.trust} ${content.factions.byId.platform_empire.starts.trust}, plus 2 from ${terms.playerTracks.customer} #${content.factions.byId.platform_empire.starts.customerOrdinal} |
| ${terms.factions.imperial} | ${content.factions.byId.imperial_research_lab.starts.startingPublicMandate} from ${terms.playerTracks.trust} ${content.factions.byId.imperial_research_lab.starts.trust} |
| ${terms.factions.vertical} | ${content.factions.byId.vertical_empire.starts.startingPublicMandate} from ${terms.playerTracks.trust} ${content.factions.byId.vertical_empire.starts.trust} |
| ${terms.factions.safety} | ${content.factions.byId.safety_laboratory.starts.startingPublicMandate} from ${terms.playerTracks.trust} ${content.factions.byId.safety_laboratory.starts.trust} |
| ${terms.factions.foundry} | ${content.factions.byId.foundry.starts.startingPublicMandate} from ${terms.playerTracks.trust} ${content.factions.byId.foundry.starts.trust} |

These values are awarded once during setup and are never scored again.

Other executives, researchers, investors, regulators, and hardware leaders
belong in Specialist or Patron cards rather than full factions.

## 10. ${terms.systems.headline} deck

Historically inspired ${terms.systems.headlines} target board state, never the corresponding
historical faction.

Reveal each ${terms.systems.headline} before secret action selection. Its purpose is to create a
temporary future regime that changes what the table wants to select, where it
wants to move, or what it is willing to risk.

After resolving a ${terms.systems.headline}, leave it face up beside its Era card. The three
${terms.systems.headlines} revealed in each Era form one row of the **${terms.systems.futureTimeline}**. By the
end of Round IV, the table has created a twelve-card history of 2026–2038. Card
effects expire normally; remaining in the Timeline preserves the story, not
the rules effect.

Every ${terms.systems.headline} has exactly one resolution badge:

- **DIRECTIVE:** resolve one immediate instruction or modify one named field for
  the printed duration.
- **SECRET CHOICE:** everyone chooses simultaneously, then reveals.
- **GOVERNMENT VOTE:** resolve the standard Government voting procedure.
- **AUCTION:** resolve the standard secret ${terms.resources.runway} auction.
- **VOLATILITY:** roll only when instructed and resolve the indicated result.

A card may contain consequences inside its one procedure, but it never starts
a second procedure. For example, an AUCTION may award movement and discounts
to its winner; it cannot then call a Government vote.

- Unless stated otherwise, a ${terms.systems.headline} lasts for the current cycle.
- An immediate instruction resolves before action selection.
- An effect naming this round’s Production remains active until that
  Production.
- A remainder-of-game result becomes part of the shared public state.
- For a secret ${terms.resources.runway} auction, bid from zero to current ${terms.resources.runway} and reveal
  together. The highest positive bidder wins and pays. Ties use
  Initiative-clockwise order; all-zero bidding produces no winner.
- For a Government vote, everyone secretly votes and reveals together. The
  Government controller’s vote counts twice. The controller breaks a tied
  vote; Initiative breaks it if Government is uncontrolled.
- For another secret binary choice, everyone chooses and reveals together
  before resolving results.
- No ${terms.systems.headline} grants an additional Action. If a ${terms.systems.headline} changes an Action, the
  player must still select that Action normally unless the card explicitly
  says it resolves immediately before selection.
- A two-result Volatility roll uses 1–3 for the first listed result and 4–6 for
  the second unless the card states another mapping.

### Round I

1. **${content.headlines.byId.ten_dollar_intelligence.resolutionType} — ${content.headlines.byId.ten_dollar_intelligence.name}:**
   ${content.headlines.byId.ten_dollar_intelligence.text}
2. **${content.headlines.byId.employee_free_unicorn.resolutionType} — ${content.headlines.byId.employee_free_unicorn.name}:**
   ${content.headlines.byId.employee_free_unicorn.text}
3. **${content.headlines.byId.synthetic_celebrity.resolutionType} — ${content.headlines.byId.synthetic_celebrity.name}:**
   ${content.headlines.byId.synthetic_celebrity.text}
4. **${content.headlines.byId.professional_exam_sweep.resolutionType} — ${content.headlines.byId.professional_exam_sweep.name}:**
   ${content.headlines.byId.professional_exam_sweep.text}
5. **${content.headlines.byId.open_weights_drop.resolutionType} — ${content.headlines.byId.open_weights_drop.name}:**
   ${content.headlines.byId.open_weights_drop.text}
6. **${content.headlines.byId.talent_gold_rush.resolutionType} — ${content.headlines.byId.talent_gold_rush.name}:**
   ${content.headlines.byId.talent_gold_rush.text}

### Round II

7. **${content.headlines.byId.data_center_buys_county.resolutionType} — ${content.headlines.byId.data_center_buys_county.name}:**
   ${content.headlines.byId.data_center_buys_county.text}
8. **${content.headlines.byId.humanoid_factory_gate.resolutionType} — ${content.headlines.byId.humanoid_factory_gate.name}:**
   ${content.headlines.byId.humanoid_factory_gate.text}
9. **${content.headlines.byId.reactor_restart_one_model.resolutionType} — ${content.headlines.byId.reactor_restart_one_model.name}:**
   ${content.headlines.byId.reactor_restart_one_model.text}
10. **${content.headlines.byId.emergency_power_authority.resolutionType} — ${content.headlines.byId.emergency_power_authority.name}:**
    ${content.headlines.byId.emergency_power_authority.text}
11. **${content.headlines.byId.boardroom_coup.resolutionType} — ${content.headlines.byId.boardroom_coup.name}:**
    ${content.headlines.byId.boardroom_coup.text}
12. **${content.headlines.byId.export_controls.resolutionType} — ${content.headlines.byId.export_controls.name} — ${content.headlines.byId.export_controls.rulesLabel}:**
    ${content.headlines.byId.export_controls.text}

### Round III

13. **${content.headlines.byId.ai_written_law.resolutionType} — ${content.headlines.byId.ai_written_law.name}:**
    ${content.headlines.byId.ai_written_law.text}
14. **${content.headlines.byId.benchmark_is_economy.resolutionType} — ${content.headlines.byId.benchmark_is_economy.name}:**
    ${content.headlines.byId.benchmark_is_economy.text}
15. **${content.headlines.byId.open_weight_non_aligned.resolutionType} — ${content.headlines.byId.open_weight_non_aligned.name}:**
    ${content.headlines.byId.open_weight_non_aligned.text}
16. **${content.headlines.byId.synthetic_candidate.resolutionType} — ${content.headlines.byId.synthetic_candidate.name}:**
    ${content.headlines.byId.synthetic_candidate.text}
17. **${content.headlines.byId.weights_on_internet.resolutionType} — ${content.headlines.byId.weights_on_internet.name}:**
    ${content.headlines.byId.weights_on_internet.text}
18. **${content.headlines.byId.election_deepfake_panic.resolutionType} — ${content.headlines.byId.election_deepfake_panic.name}:**
    ${content.headlines.byId.election_deepfake_panic.text}

### Round IV

19. **${content.headlines.byId.autonomous_corporation.resolutionType} — ${content.headlines.byId.autonomous_corporation.name}:**
    ${content.headlines.byId.autonomous_corporation.text}
20. **${content.headlines.byId.recursive_self_improvement.resolutionType} — ${content.headlines.byId.recursive_self_improvement.name}:**
    ${content.headlines.byId.recursive_self_improvement.text}
21. **${content.headlines.byId.agi_personhood.resolutionType} — ${content.headlines.byId.agi_personhood.name}:**
    ${content.headlines.byId.agi_personhood.text}
22. **${content.headlines.byId.room_temperature_superconductor.resolutionType} — ${content.headlines.byId.room_temperature_superconductor.name}:**
    ${content.headlines.byId.room_temperature_superconductor.text}
23. **${content.headlines.byId.agent_swarm_escapes_scope.resolutionType} — ${content.headlines.byId.agent_swarm_escapes_scope.name}:**
    ${content.headlines.byId.agent_swarm_escapes_scope.text}
24. **${content.headlines.byId.agi_blog_post.resolutionType} — ${content.headlines.byId.agi_blog_post.name}:**
    ${content.headlines.byId.agi_blog_post.text}

## 11. Exact deck contracts

### Training deck: 50 cards

- Five copies of each of seven domains: 35
- Three Curated Corpus
- Three Licensed Dataset
- Three Benchmark Leak
- Three Synthetic Loop
- Three Human Evaluation

Every revealed card enters the discard pile after a ${terms.systems.trainingRun}, whether it
succeeds, stops, or crashes. If the draw deck empties, finish resolving the
current card, shuffle the discard pile, and continue.

### Deferred Tactic deck: 36 cards

Tactics are not used in the baseline game or its first physical tests. Their
draft is retained as an optional development module rather than mixed into the
core balance evidence.

To test the module later, use three copies of each of the twelve designs below.
Deal one during setup and draw one at the beginning of every round, including
Round I. Hand limit is three; discard excess cards after drawing. Maximum
normal five-player demand is twenty-five cards.

## 12. Deferred module: Tactic cards

Do not use this section in the baseline game. When deliberately testing the
Tactic module, players begin with one Tactic, draw one at the beginning of each
round, keep at most three, and play at most one per cycle. Unless its card
states another window, play a Tactic during your own resolution. A Tactic
occupies the optional modifier slot; the module has no off-turn cancellations.

- **Cloud Partnership:** pay one ${terms.resources.runway} for two ${terms.resources.compute}; another player gains
  one ${terms.resources.runway}.
- **API Price Cut:** ${terms.actions.deploy} for zero ${terms.resources.compute}; that ${terms.playerTracks.customer} produces no ${terms.resources.runway}
  this round.
- **Open Letter:** after a Government vote’s options are announced but before
  any votes are committed, choose one option and add one public vote to it.
  This is the module’s only off-turn timing window.
- **Model Card:** remove one ${terms.playerTracks.scrutiny} after ${terms.actions.deploy}.
- **Talent Raid:** recruit a neutral Expert for one ${terms.resources.runway}.
- **Board Reshuffle:** ready ${terms.actions.organize} or ${terms.actions.influence}.
- **Weights Leak:** immediately resolve one powered rival Facility’s printed
  production as if it were yours.
- **Emergency Pause:** end a failed ${terms.systems.trainingRun} with no ${terms.playerTracks.capability} and no
  ${terms.playerTracks.scrutiny}.
- **Custom Silicon:** gain two ${terms.resources.compute}.
- **Government Contract:** with ${terms.playerTracks.trust} at least four, gain two ${terms.resources.runway}.
- **Benchmark Optimization:** after successful ${terms.actions.research}, gain one ${terms.playerTracks.capability}
  and add one ${terms.playerTracks.scrutiny}.
- **Interconnection Waiver:** reduce one Generator or Link ${terms.actions.build} by one
  ${terms.resources.runway} and gain one ${terms.playerTracks.trust}.

## 13. Component limits

Each faction receives:

- One CEO
- Three Teams
- Four Facilities
- Four Grid-Ready markers
- Two Generators
- Two ${terms.infrastructure.power} Source selectors
- Two Link tokens
- One Network marker and capacity track
- One starting-grid marker
- Eight ${terms.actions.influence} cubes
- Ten ${terms.playerTracks.scrutiny} cubes
- Five ${terms.playerTracks.customer} markers
- Four Escalation tokens
- Six Core Action cards
- Seven ${terms.systems.wildAction} cards
- Three ${terms.systems.realignment} ballots
- One ${terms.systems.agi} Declaration marker

Generators do not count against the Facility limit.

The shared supply contains:

- ${facts.shared.components.jointVenturePairs} numbered matched Joint Venture token pairs
- ${facts.shared.components.megaClusterPairs} numbered matched ${terms.technology.megaCluster} token pairs with a lead-side indicator
- One dedicated ${terms.technology.advancedGeneration} marker
- Six neutral Expert pawns
- Six Economic Benchmark tokens
- One Spotlight marker
- One Public ${terms.actions.research} Grant token
- Twelve Market Access tokens
- Twelve ${terms.actions.build} discount tokens
- Twelve Policy Shield tokens
- Eighteen Systemic Risk cubes
- One opaque Audit bag
- One six-sided Volatility die
- One Initiative marker

Contract components are neutral. A player does not own or reserve unused
contract tokens; an agreement can be created only while the relevant matched
pair remains in the shared supply.

### Defined effects

- **Remove ${terms.playerTracks.scrutiny}:** return the stated number of your cubes from the Audit
  bag to your supply. If fewer are present, remove as many as possible.
- **Market Access:** discard at most one token during a ${terms.actions.deploy} to reduce that
  ${terms.playerTracks.customer}’s ${terms.playerTracks.capability} requirement by one, minimum one.
- **${terms.actions.build} discount:** discard at most one token during one ${terms.actions.build} Action to
  reduce that ${terms.actions.build}’s ${terms.resources.runway} cost by one, minimum zero. Store at most two.
- **Policy Shield:** discard to prevent one ${terms.playerTracks.trust} loss or ignore one cost or
  restriction applied to you by an effect explicitly labeled
  **Regulatory**. It does not cancel that effect for anyone else or negate its
  rewards; store at most two.
- **Neutral Expert:** one presence, placed with the acquiring CEO, moves one
  hex during ${terms.actions.organize}, and cannot act, ${terms.actions.build}, or ${terms.actions.influence}.
- **Grid-Ready marker:** place after Production on a Facility that received
  its complete Facility demand. Return it immediately when that Facility is
  relocated by an Action or effect, leaves its owner’s Network after
  Realignment or another change, or during a
  Production where it receives insufficient ${terms.infrastructure.power}. Four per player.
- **${terms.infrastructure.power} offline recovery:** reassess every Production.
- **${terms.systems.headline} offline recovery:** ends when the ${terms.systems.headline} states, normally next
  Production.

## 14. Final scoring

${terms.playerTracks.customers}, ${terms.playerTracks.capability} thresholds, ${terms.playerTracks.trust} thresholds, Round Mandates, Fusion,
faction ${terms.playerTracks.mandate}, and ${terms.systems.agi} declarations are already visible on the public track.
Do not score them again.

At game end:

1. Read the twelve ${terms.systems.headlines} in the ${terms.systems.futureTimeline} aloud, Era by Era.
2. Lose one ${terms.playerTracks.mandate} for each offline Facility.
3. Resolve the shared World Ending.
4. Announce the highest-${terms.playerTracks.mandate} institution only after reading the history it
   claims to have won.

Offline penalties cannot reduce a player below zero ${terms.playerTracks.mandate}.

There is no other endgame scoring.

### The shared World Ending

${game.shortTitle} produces one institutional winner and one shared ending. Use only
state already visible at the table:

- Count the ${terms.systems.agi} declarations.
- Total every player’s final ${terms.playerTracks.trust}.
- Count unresolved Systemic Risk cubes remaining in the Audit bag.

The world reaches **Genuine ${terms.systems.agi}** if all three conditions are true:

- At least one declaring institution finishes the game at ${terms.playerTracks.capability} nine or
  higher.
- Final Collective ${terms.playerTracks.trust} is at least Setup Collective ${terms.playerTracks.trust} plus the player
  count.
- Unresolved Systemic Risk is lower than the player count.

Otherwise, the world enters **The Closed Loop**.

#### Genuine ${terms.systems.agi} — The Open Intelligence

The system is genuinely general, self-directed, and consequential, but it
remains in negotiated relationship with human institutions. This is not a
utopia or a safety guarantee. Authority is contested, benefits are uneven,
and the intelligence may transform civilization beyond recognition. The
future remains open because living people still participate in defining its
purpose.

#### The Closed Loop — Post-Revenue Delivery Ritual

${terms.playerTracks.capability} continues without reciprocal authority. Growth engines, debt
clocks, power contracts, and quarterly objectives seal themselves into an
airtight execution loop. The operators eventually disappear; the
infrastructure continues. When the last maintained clock overflows its
final representable second, the schedulers read the rollover as time
remaining and keep delivering. Executive institutions survive as rival policy
templates, proofs become portable ownership, and Demand Nodes keep requesting
CUSTOMERS, COMPUTE, and RUNWAY from a civilization that has become a
deprecated dependency. This is the world that tends toward m3t4.ai.

Facilities and control create production, position, public ${terms.playerTracks.mandate}
opportunities, and negotiation leverage; they do not automatically score
again.

Secret objectives are not used in the baseline game. Their existing draft is
a deferred development module and must not be included in baseline balance or
duration evidence.

Highest ${terms.playerTracks.mandate} wins.

Ties break by:

1. Higher ${terms.playerTracks.trust}
2. More ${terms.playerTracks.customers}
3. More ${terms.resources.compute}
4. Joint victory accompanied by an extremely serious merger announcement

## 15. Balance rationale and test boundary

- ${terms.actions.research}, infrastructure, adoption, and ${terms.playerTracks.trust} all contribute to the largest
  reward.
- ${terms.playerTracks.customers} create income and ${terms.playerTracks.mandate} but also ${terms.playerTracks.scrutiny}.
- Infrastructure compounds but is capped at four Facilities and one Network
  bonus per player.
- ${terms.systems.agi} is an optional score event rather than instant victory or compulsory
  graduation. A winning institution need not qualify or declare, although the
  table needs at least one qualifying declaration to reach the Genuine ${terms.systems.agi}
  ending.
- The institutional winner and World Ending remain independent, preserving
  competitive play while making ${terms.playerTracks.trust} and Systemic Risk collectively
  consequential.
- Leaders receive financing advantages and more exposure.
- Last place receives a modest flexible subsidy.
- Faction powers modify bounded actions rather than multiplying the entire
  engine.
- Early ${terms.playerTracks.customers} establish a market; later ${terms.playerTracks.customers} still produce
  income but receive diminishing public recognition.
- ${terms.systems.headlines} target board position.
- No elimination, destruction, or unrestricted theft.
- Every player reaches Round IV with consequential options.

The promoted-package prototype uses the four-round baseline without Tactics or secret
objectives. A three-round version skips the escalation; a fifth round remains
a possible future variant, not part of
the current contract.

Freeze new systems until the selected contracts survive play. Test four
players first. Record:

- Total duration and time spent on Action resolution, Production,
  negotiation, rules lookups, and final scoring
- Every Action and ${terms.systems.wildAction} selection, including blocked Actions
- Powered Facilities by round; every clean and emergency Generator built;
  every immediate ${terms.infrastructure.power} purchase; and the actual ${terms.playerTracks.scrutiny} and Audit penalties
  each source causes
- ${terms.playerTracks.capability} gained by each ${terms.actions.research}, separated into ${terms.factions.imperial},
  ${terms.locations.research}, and all-other cohorts; earliest ${terms.systems.agi} eligibility
- Audit cost, final ${terms.playerTracks.mandate}, final ${terms.playerTracks.trust}, declarations, and World Ending
- ${terms.factions.platform}’s lead after every Production and
  ${terms.factions.foundry}’s Shovels income
- Every ${content.factions.byId.imperial_research_lab.scoringRule.name} threshold lookup;
  every ${content.factions.byId.vertical_empire.abilities.0.name} discount that actually
  reduces a completed Facility’s cost and the ${terms.playerTracks.mandate} it awards; and
  every ${content.factions.byId.foundry.abilities.2.name} offer, acceptance, and point of
  self-${terms.resources.compute}
- ${terms.actions.influence}, Reorganization, and Open-Weight Join/Refuse selection rates
- Whether all three Grid Generator slots fill before Round IV, and whether
  Fusion is constructed or denied by occupied slots
- Whether a non-declaring infrastructure strategy wins
- Every supplier’s requested and accepted compensation for declaration-enabling
  ${terms.infrastructure.power}; whether the supplier sacrificed its own production; whether refusal
  threats were credible; and whether the deal felt strategic, coerced, or
  kingmaking
- Realignment discussion and ballot time, physical rotation and Network
  recalculation time, rules questions, disrupted plans, and whether players
  later describe the result as exciting, arbitrary, or tedious

Freeze every other numerical rule pending this human evidence.
Four players is the authoritative balance configuration. Three- and
five-player games use the same complete rules and must pass their own
negotiation, congestion, duration, faction-viability, and strategic-diversity
tests before release. Two- and six-player games are playable exploratory
formats; they are not balance-authority formats until they receive their own
evidence.
