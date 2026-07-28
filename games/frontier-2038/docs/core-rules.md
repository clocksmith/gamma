# M3T4 2038

## A 3–5 player race to build, deploy, regulate, and plausibly declare AGI

**Rules version:** 0.5.0-rc.21-test
**Design-baseline date:** July 26, 2026
**Status:** Controlled playtest candidate; synchronized with executable game 0.8.20
**Provisional time:** 75–100 minutes at four players; three- and five-player durations require their own blind tests
**Standard game:** Four rounds, three turns per player per round

The game begins as recognizable technology strategy and ends with agent
swarms, emergency governance, orbital-compute proposals, public AGI
declarations, and competitors jointly financing infrastructure they expect to
weaponize against one another.

The world remains solemn. Nobody acknowledges that this is ridiculous.

### Tone contract

M3T4 2038 uses **solemn institutional absurdity**. Every impossible
technology is presented as a responsible quarterly initiative. The escalation
is structural:

- **The Demo** covers the plausible five-year horizon beyond July 2026.
  Technology can genuinely improve life. Openness and control, automation and
  employment, speed and caution all offer credible benefits and harms. Cards
  name durable directions rather than product launches or already-completed
  milestones.
- **The Scale** is the first threshold science fiction. AI becomes an
  independent economic actor while land, power, chips, and people become an
  industrial apparatus. Institutions stretch before physics does.
- **The Narrative** turns AI into a political constituency and
  industrializes consensus, legitimacy, ownership, and public reality.
  Positions harden into blocs; several authenticated publics may occupy the
  same world.
- **The Claim** permits negotiable physics, agent jurisdictions,
  reality-maintenance systems, personhood, and civilizational declarations as
  ordinary portfolio decisions. Institutions continue operating after reality
  stops making sense. The accumulated compromises finally divide into two
  endings: intelligence remains answerable to a living society, or
  optimization closes over itself and continues after society is gone.

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

The Future Timeline is one compounding history, not an anthology. Because
only three of six Headlines appear in each Era, later cards may inherit
intensified pressures but never require or name a specific earlier Headline.

### How to win

After Round IV, the institution with the most Mandate wins. Mandate is scored
publicly as players gain Customers, cross Capability and Trust thresholds, win
Round Mandates, and resolve exceptional programs. Declaring AGI is powerful
but optional; it is one path through the game, not its required conclusion.

The winning institution and the world’s ending are separate results. A player
may win the institutional race while helping create the Closed Loop, or lose
the race inside a future where genuine AGI remains answerable to humanity.

## 1. Setup

1. Build the thirteen-tile board as described in **Modular hex board**:
   Frontier in the center, the shuffled six-tile operational ring around it,
   and the shuffled six-tile public ring in the evenly spaced outer positions.
2. Separate the Headline cards by Era. Shuffle each six-card Era deck and
   place it beside the matching Era card. Each Era will use three Headlines.
   Leave room below the four Era cards for the twelve-card Future Timeline.
3. Shuffle the Training deck. Separate the twelve Round Mandate cards into
   four three-card Era decks. Shuffle each deck and place it beside the
   matching Era card.
4. Place Runway, Compute, Customer, Safety, Influence, Scrutiny, Systemic Risk,
   Policy Shield, Market Access, Build discount, Economic Benchmark, Grid-Ready, Power
   Source, Link, Joint Venture, Mega-Cluster, Expert, Spotlight,
   Public Research Grant, Initiative, Audit bag, and Volatility components
   within reach.
5. Each player chooses or receives one Faction. Take its board, six Core
   Actions, seven Wild Actions, CEO, three Teams, four Facilities, two
   Generators, markers, and starting resources.
6. Place every CEO and one Team at Frontier. Keep the other two Teams in
   supply. Set each Faction’s Runway, Compute, Capability, Customers, Trust,
   and Safety to its printed starting values.
7. Place each Faction’s already-earned public Mandate on the shared track as
   listed under **Starting public Mandate**. Put every player’s ten Scrutiny
   cubes outside the bag; the bag begins empty.
8. Add every Faction’s printed starting Trust and record the result as
   **Setup Collective Trust** on the Era reference. This is a reference value,
   not another track.
9. Choose Initiative randomly and give that player the Initiative marker.
   Begin Round I.

Do not deal Tactics or secret objectives in the baseline game.

## 2. Central loop

Every player controls an asymmetric AI institution.

Each player has six Core Action cards but takes only three turns per round.
Once played, a Core Action remains exhausted until the next round:

- Fund
- Research
- Build
- Organize
- Deploy
- Influence

Players do not perform all six actions in a fixed sequence. The twelve
standard-game turns ask which three of six institutional functions matter in
each era. The other three actions remain unused unless an explicit ability
readies one.

Examples:

- Round I: Research → Build → Deploy
- Round II: Fund → Organize → Mega-Cluster
- Round III: Research → Influence → Open Weights

> You have six institutional capabilities, but only enough time to use three
> of them this quarter.

### The complete ordinary turn: Select → Move → Act

1. Reveal one Headline.
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
bonus applies, where Research occurs, which market receives a Deployment,
which adjacent political or media spaces may be Influenced, and where power
infrastructure may begin.

Facilities, Influence cubes, Generators, and Experts cannot act. Organize
receives normal acting-piece movement before its additional movement,
recruitment, restructuring, or relocation.

Use one authority per rules layer:

- The Era card determines globally unlocked actions.
- A Faction board modifies those actions.
- The global-state layer contains the current Headline and every persistent
  Headline effect.
- An ordinary turn may apply the Action, one destination bonus, one Faction
  modifier, and each applicable global effect, subject to field precedence.
- Every exception is timed **before selection**, **during movement**, **during
  action**, or **after action**.
- A Headline changes one named field or creates one public choice regime. It
  never grants another Action.
- If the current Headline and a persistent Headline would change the same
  printed field, the current Headline temporarily overrides the older effect.
- A printed field may be modified by only one global effect at a time.
  Persistent effects modifying other fields remain active.
- Readying a card changes a later choice; it never resolves that card now.
- Agent Swarm is the sole compound-action exception.
- A Headline whose effect lasts beyond its cycle is placed beside the affected
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

### Escalation tokens and Wild Actions

Escalation tokens are spent, not permanent unlock markers. Every player has
seven Wild Action cards. The Era card determines which ones are legal.

- Select a Wild Action instead of a Core Action.
- Commit and spend one Escalation token.
- Flip the Wild Action after resolution.
- Each named Wild Action is usable once per player per game.
- Unspent Escalation tokens expire at round end.
- Previously unlocked unused Wild Actions remain available later.

| Round | Tokens | Newly available Wild Actions |
| --- | ---: | --- |
| I — The Demo | 0 | None |
| II — The Scale | 1 | Mega-Cluster, Reorganization |
| III — The Narrative | 1 | Open Weights, Narrative Capture |
| IV — The Claim | 2 | Agent Swarm, Declare AGI, Fusion Demonstrator |

Players receive four Wild Action uses across the game but choose among seven
possibilities. Agent Swarm is itself the selected Wild Action, then resolves
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

### Runway

Money, financing, and organizational endurance. Spend it on Facilities,
hiring, partnerships, lobbying, and crisis management.

### Compute

Training and inference capacity. Spend it on Research, Deploy, and major
infrastructure.

### Capability

A permanent model-quality track. Capability is not normally spent. It unlocks
stronger deployments and AGI declarations.

### Customers

Products deployed into the world. Each Customer produces one Runway during
Production. Customers #1–3 immediately score two public Mandate each when
gained; Customers #4–5 score one each. Customers also increase public
exposure.

### Trust

A track from zero to six. Trust helps with regulation, Joint Ventures, safety
decisions, and the final declaration. Low Trust limits final options but does
not eliminate a player.

Victory points are called **Mandate**. Players persuade markets, institutions,
customers, and history that their organization won the era; they do not prove
metaphysical intelligence.

Mandate is normally scored immediately on one public track:

- Two when Customer #1, #2, or #3 is gained; one when #4 or #5 is gained.
- Two the first time Capability reaches three, six, nine, and twelve, except
  for a printed faction scoring rule.
- Two the first time Trust reaches two, four, and six.
- Printed Mandate from Headlines, Round Mandates, Fusion, faction abilities,
  and AGI.

Threshold awards are permanent after they are scored; later loss of Trust
does not reverse public history.

There is no hidden or deferred conversion of Facilities, controlled hexes,
stored resources, or unused cards into Mandate. If an effect scores Mandate, move
the public marker when that effect resolves.

### Universal costs and caps

Resource caps apply immediately whenever resources are gained or traded:

- Runway: twelve
- Compute: ten
- Safety: three, except a printed Faction limit

Return excess to the shared supply. A trade cannot move resources through a
player above a cap.

When effects change a cost, apply replacements and waivers first, then
surcharges, then discounts. The final cost cannot fall below zero.

## 4. Modular hex board

Use thirteen hexagonal tiles in a sixfold-symmetric layout:

- One Frontier
- Two Research Campuses
- Two Cloud Regions
- One Consumer Market
- One Chip Foundry
- One Capital Market
- One Talent Hub
- One Media Sphere
- One Government District
- One Grid and Reactor Corridor
- One Renewable Basin

Place Frontier in the center. The six inner spaces form the **operational
ring**. Place the six **public ring** spaces at evenly spaced radius-two
positions. Each public-ring space touches two neighboring operational-ring
spaces, producing six identical spatial arms instead of a rectangular row
layout.

Shuffle the following inner pool and place it around Frontier:

- One Research Campus
- One Cloud Region
- One Chip Foundry
- One Capital Market
- One Talent Hub
- The Grid and Reactor Corridor

Shuffle the following outer pool among the six outer positions:

- One Research Campus
- One Cloud Region
- One Consumer Market
- One Media Sphere
- One Government District
- One Renewable Basin

This guarantees
that the first ring contains Research, Compute, Build, Fund, Organize, and
Power support without fixing their adjacency. Consumer, Media, and Government
remain scarce outer-ring destinations.

Every piece placed on the board during setup begins at Frontier. A movement of
two reaches every space from the center. Once pieces leave the center, opposing
outer spaces are four hexes apart, so later positioning, Teams, Networks, and
negotiated adjacency matter. The board footprint is spatially symmetric; the
shuffled economic layout is intentionally not.

Every non-Frontier hex has a visit bonus, two Facility spaces, a Facility
production effect, and a control value used by Headlines and Mandates. Frontier
has no Facility spaces.

### Presence and control

- CEO: two presence
- Team: one presence
- Facility: one presence
- Influence cube on Media, Government, or Capital: one presence

The player with the most presence controls the hex. Ties mean nobody controls
it.

The Government controller’s vote counts twice during Government votes. This
is a control benefit, not a visit bonus.

There is no combat and no player elimination. Rival pieces coexist.
Competition comes from Facility scarcity, control, positioning, voting,
deals, and Headlines.

### Location effects

| Location | Visit bonus | Facility production | Contract icon |
| --- | --- | --- | --- |
| Research | Once this Training Run, protect one duplicate as if spending Safety | Gain one Safety token | Compute |
| Cloud | First Compute cost is reduced by one | Gain two Compute | Compute |
| Consumer | Deploy costs zero Compute | Gain one Runway | Runway |
| Chip Foundry | Build costs one less Runway | Gain one Compute and one Build discount | Compute |
| Capital | Fund gains one Runway | Gain two Runway | Runway |
| Talent | Recruit costs one less Runway | Move one Team one hex during Production | Runway |
| Media | Influence may place or relocate one additional cube | Remove one Scrutiny before Audit | Runway |
| Government | Influence may place or relocate one additional cube on Government | Gain one Policy Shield | Runway |
| Grid and Reactor Corridor | Infrastructure Build costs one less | Gain one Compute | Compute |
| Renewable Basin | Civic Heat Battery costs one less Runway | Remove one Scrutiny before Audit | Runway |
| Frontier | After Act, you may gain one Runway and add one Scrutiny | No Facility spaces | None |

Frontier’s optional Runway is resolved after the selected Action and does not
modify that Action’s printed output. It may be used once by each acting player
who ends movement at Frontier; it never creates Facility production or
Mandate. The central district offers bridge financing because nobody is
permitted to own the horizon.

### Infrastructure Network

Each player’s Infrastructure Network exists from setup. Its starting-grid
connection operates in Round I. Generators, Links, Mega-Clusters,
and the Network production bonus unlock in Round II.

Each player has two Link tokens. The same graph governs Power delivery and the
Network production bonus:

- The first Facility joins through the basic grid connection.
- Owned Facilities and Generators on the same or adjacent hexes connect to one
  another.
- A Link on one otherwise disconnected Facility joins that Facility to the
  Infrastructure Network. Owned sites adjacent to it may then connect
  normally.
- Power from connected Generators and purchased Power is pooled across the
  Network.
- Beginning in Round II, two or more connected, powered Facilities produce one
  additional Runway or Compute.

A player receives only one Network bonus regardless of Network size. There is
no separate Power graph, production graph, or edge-by-edge flow calculation.

### Contract hosts

Joint Ventures and every Mega-Cluster use neutral
matched token pairs from the shared supply. Place one numbered half on each
host Facility. The matching number identifies the contract even if
Realignment moves the districts.

A contract remains owned after Realignment but is active only while its two
named host Facilities are adjacent and satisfy its other requirements, unless
a Faction ability explicitly changes that range. The tokens travel with their
Facilities. No player may silently substitute a different Facility after the
contract is signed.

Every cross-player contract or jointly funded project requires the explicit
consent of every participant. Facilities sharing one hex are **co-located**,
not adjacent; adjacency requires their hexes to share an edge.

### Joint Venture

Influence may create a Joint Venture between two adjacent Facilities owned by
different players, unless a Faction ability explicitly changes that range.
Both host Facilities must be powered during Production for the contract to
produce.

Each partner gains one resource shown by the **contract icon on the other
partner’s host tile**: one Runway for a Runway icon or one Compute for a
Compute icon. This contract output is not the tile’s full printed production
and is never multiplied by another Facility effect.

Either participant may terminate the Joint Venture during their own Influence
action. Return both matched token halves to the shared supply.

### Jurisdictional Realignment

Jurisdictional Realignment occurs exactly once: after Mandate scoring in Round
III. It does not occur after Rounds I, II, or IV. Every player secretly chooses
one of their three Realignment ballots, then all ballots are revealed
simultaneously:

- **Consolidate the Core:** rotate the six inner-ring locations one position
  clockwise.
- **Expand the Periphery:** rotate the six outer-ring locations one position
  clockwise.
- **Authorize Counter-Cycle:** rotate the inner ring one position clockwise
  and the outer ring one position counterclockwise.

The motion with the most ballots resolves. If leading motions tie, begin with
the Initiative player and scan clockwise; the first player whose ballot names
one of the tied motions selects the result. Every player casts exactly one
ballot. Government bonuses and other vote modifiers do not alter Realignment
ballots.

Frontier never moves. Each moving location tile carries every CEO, Team,
Facility, Generator, Influence cube, Expert, and other site-bound component on
it. Rotate the selected physical ring once, then recalculate the single
Infrastructure Network from the starting-grid Facility, Links, and visible
adjacency. Nothing is lifted or re-laid.

Ring rotation moves the district, not the Facility for Grid-Ready purposes.
Realignment does not remove a Grid-Ready marker merely because its tile
rotated. After recalculating each Infrastructure Network, return a Grid-Ready
marker only from a Facility that is now outside its owner’s Network.

Joint Ventures remain in force but produce only while their matched host
Facilities are adjacent and all printed requirements are met. Immediate
Power purchases never persist through Realignment. A Mega-Cluster whose matched host Facilities
are no longer adjacent is offline until they become adjacent again.
Realignment never destroys a component, changes a host, or terminates a
contract.

The ballots are open information before selection and secret information until
the simultaneous reveal. Players may negotiate or misrepresent their intended
ballot; promises about the vote are not binding. Because Realignment happens
before Round IV, every player receives three final Actions in which to respond
to the changed geography.

### Power delivery

Power is spatial infrastructure, not a stored resource.

- Every player begins with a basic one-Power grid connection. It automatically
  connects to that player’s first Facility, requires no Link or recurring payment,
  and cannot supply the additional demand of Mega-Cluster. It is
  dedicated capacity and cannot be sold. Place the
  player’s starting-grid marker on that first Facility.
- Every Facility needs one delivered Power to produce.
- A Mega-Cluster needs two additional Power.
- The Infrastructure Network connects Power to Facilities.

Production uses the fixed resolution order in **Power and Production**. Power
capacity never produces resources by itself and may not be assigned twice.

Capacity is pooled inside the same Infrastructure Network used for the
production bonus; there is no second connectivity check.

An offline Facility still contributes presence, occupies its Facility space,
and may be visited. It produces nothing and provides no Network bonus. It
automatically returns online in any later Production where enough Power is
assigned.

## 5. Four-round escalation

### Round I — The Demo

The world has seen the prototype. Nobody knows whether it works.

- Three turns per player
- Only Core Actions
- Beneficial or mildly disruptive Headlines
- No Escalation tokens

This round teaches Select → Move → Act, movement, basic Research, the starting
grid, Facilities, Customers, and Scrutiny. Generators, Links,
agreements, Government votes, and Wild Actions are not yet active.

Its controversies remain recognizable and unresolved: cheap intelligence can
expand access or erase livelihoods; open weights can distribute authority or
remove containment; safety can be stewardship or incumbent protection.

### Round II — The Scale

Capital, chips, talent, and electricity become the real product.

Each player receives one Escalation token and unlocks:

- Generators
- Links and the Network production bonus
- Mega-Clusters
- Wild Actions

Benefits now arrive through physical concentration. Data centers stabilize
services and consume counties. Automation removes dangerous labor and removes
workers. Dedicated power makes new capability possible and makes the public
dependent on private infrastructure.

#### Mega-Cluster

Spend three Runway and two Compute to place a Mega-Cluster across the edge
between two adjacent host Facilities. Construction does not require either
host to have received Power previously. It adds two Scrutiny when constructed.
Place one matched Mega-Cluster token half on each host Facility.

The acting piece must end movement on either host Facility’s hex. This is the
Mega-Cluster Action destination.

A **solo Mega-Cluster** uses two of your adjacent Facilities, both in your
Infrastructure Network. During Production, supply both hosts’ normal
Facility demand plus two additional Power from that Network. If
all demand is satisfied, gain three Compute.

A **joint Mega-Cluster** uses one host Facility from each consenting
participant. The hosts must be adjacent and each must belong to its owner’s
Infrastructure Network. The lead pays two Runway and one Compute; the partner
pays one Runway and one Compute. During Production, each participant supplies
their host’s normal Facility demand plus one additional
Power from their own Network. If all demand is satisfied, the lead gains two
Compute and the partner gains one Compute.

Its host Facilities must remain adjacent for the Mega-Cluster to operate.
Round III Realignment may place it offline without destroying it.

#### Reorganization

Reorganization is global after movement; its destination creates no additional
target restriction.

Move every Team up to one hex.

You may return one Team to supply to gain three Runway and add one Scrutiny.
Reorganization never resolves or readies another Action.

### Round III — The Narrative

Capability is no longer enough. The public must understand it correctly—or at
least repeatedly.

Each player receives one Escalation token. Previous Wild Actions remain
unlocked. Joint Ventures, immediate Power purchases, Government votes, and
Headlines with persistent effects now enter play.

The table is no longer debating isolated products. It is choosing who may
define evidence, personhood, ownership, and legitimate authority. Coalitions
form, shared facts narrow, and formerly technical decisions become political
identities.

#### Open Weights

Open Weights is global after movement; its destination creates no additional
target restriction.

Every player gains one Capability. You also gain:

- Two Trust
- Place one Influence cube from supply, or relocate one of yours, on Media,
  Government, or Capital
- Removal of one Scrutiny cube

#### Narrative Capture

Narrative Capture is global after movement; its destination creates no
additional target restriction.

Move or place three Influence cubes among Media, Government, and Capital.
Then choose one:

- Remove two of your Scrutiny cubes.
- Gain two Runway.
- Give a player with more Customers than you one Scrutiny.

### Round IV — The Claim

The phrase “general intelligence” is now a financing category.

Each player receives two Escalation tokens.

Agent Swarms, AGI declarations, Fusion, and exceptional faction programs now
enter play.

Local compromises become a civilizational outcome. The final question is not
whether powerful intelligence exists, but whether it remains in reciprocal
relation with living people or inherits an airtight execution loop whose
metrics outlive their purpose.

#### Agent Swarm

Agent Swarm may be selected only while you have at least two different unused
Core Actions. Choose and play two of them during one turn. Resolve both and pay
all costs. Move only once. Resolve both Core Actions from that same destination
in either order. Apply the destination visit bonus to only one of the two
Actions, chosen when the first relevant Action resolves. Exhaust both Core
cards, flip Agent Swarm, and add three Scrutiny.

#### Declare AGI

Requirements:

- Capability nine or higher
- At least three Customers
- At least three grid-ready Facilities
- Trust two or higher
- Spend three Compute

Declare AGI is global after movement; its destination creates no additional
target restriction. Check every requirement when it resolves.

A **grid-ready Facility** has a Grid-Ready marker earned during a completed
Production. After allocating Power, place a Grid-Ready marker on each Facility
that receives its complete Facility demand. Return that marker
immediately if the Facility is relocated by Organize or another effect, or leaves its owner’s
Infrastructure Network. Return it during any later Production in which the
Facility does not receive its complete demand.

A Grid-Ready marker records demonstrated operation, not hypothetical capacity.
Declaring AGI requires three marked Facilities; it never runs a second
Production calculation. A Facility built, moved, linked, or
reconnected after the most recent Production must operate successfully in a
later Production before it can receive or regain the marker. Consequently, a
Facility first built during Round IV cannot support a declaration in that
same Round.

The first valid declaration scores seven Mandate. Later declarations score
five. Every declaration adds three Scrutiny.

Declaring AGI does not end the game and is never required to win. It is a
high-scoring commitment that competes with Customer, Capability, Trust,
Round-Mandate, Narrative, and infrastructure strategies for the same twelve
Actions.

#### Fusion Demonstrator

The acting piece must end movement on the Grid and Reactor Corridor. Spend
five Runway and construct Fusion there. It uses a dedicated Fusion marker,
occupies one of that tile’s three Generator slots, provides six Power, scores
two Mandate, and adds three Scrutiny. Fusion counts as an owned Generator for
Infrastructure Network connection and Power capacity, but does not count
against the owner’s two ordinary Generator-piece limit. If all three Grid
Generator slots are occupied, Fusion cannot be constructed; that denial is
intentional spatial competition.

Fusion is late, expensive, politically exposed, and spatially constrained. It
competes with Agent Swarm and Declare AGI for a Round IV Escalation token.

## 6. Round sequence

### A. Begin the quarter

- Advance to the next fixed Era card.
- Read that Era’s **New this Era** strip aloud. Those systems are now active.
- Reveal one Mandate from the current Era’s three-card deck. Return the other
  two cards in that deck to the box unseen.
- Ready all six Core Actions.
- Award Escalation tokens.
- The lowest-scoring player receives one Public Research Grant, spendable as
  one Runway or one Compute.
- The highest-scoring player receives the Spotlight:
  - Their first Fund gains one additional Runway.
  - Their first Deploy, Mega-Cluster, Agent Swarm, or AGI declaration adds one
    additional Scrutiny.

Resolve ties for the Public Research Grant and Spotlight using the universal
Initiative-clockwise tie rule. Exception: if every player has equal Mandate,
award neither Spotlight nor the Public Research Grant. No player receives both
highest- and lowest-place treatment from a universal tie.

### B. Three action cycles

At the beginning of each cycle:

1. Reveal a Headline and place it in the current Era’s Future Timeline row.
2. Roll the Volatility die only if the Headline explicitly instructs the table
   to roll or displays the Volatility icon.
3. Everyone secretly **selects** one Action card.
4. Reveal simultaneously.
5. Resolve clockwise from Initiative: **move**, then **act**.
6. Pass Initiative clockwise.

During any player’s resolution, the active player may complete one immediate
resource trade with one rival, either immediately before or immediately after
Act. Runway, Compute, and Safety tokens may be exchanged. Every offered
component must change hands immediately; promises about later turns are not
binding. The active Headline may prohibit a named resource from being traded.

Influence is not required for this immediate exchange. Influence remains the
only way to create persistent Joint Ventures, lobbying effects, or
Trust manipulation.

### C. Power and Production

Every player board presents the same five Production boxes. Resolve a box for
every player before advancing to the next box:

1. **Generate:** recalculate every Infrastructure Network. Every connected
   Generator operates automatically. Add one Scrutiny for every
   Emergency Power Complex. Add any Headline generation.
2. **Trade:** in Initiative order, each player may buy up to two Power, one
   from each of two different adjacent rival Networks. The buyer pays one
   Runway per Power directly to the consenting supplier. Each supplier may sell
   at most one Power this Production. Only installed Generator or Fusion
   capacity may be sold; starting-grid and emergency Power may not.
3. **Allocate:** add starting-grid, Generator, purchased, and emergency Power;
   allocate remaining capacity among Facilities and Mega-Clusters.
   Place a Grid-Ready marker on every Facility receiving its complete demand;
   return the marker from every Facility that does not.
4. **Produce:** produce powered Facilities, one Runway per Customer, each
   player’s single Network bonus, and active Mega-Clusters, in that order.
5. **Partner:** produce active Joint Ventures in ascending contract-number
   order.

An immediate Power purchase lasts only for this Production. It creates no
contract token, future obligation, or termination action. A supplier may sell
capacity even when doing so leaves one of its own Facilities offline.

Apply the universal resource caps after every Production gain.

### D. Public Audit

Risky actions add player-colored Scrutiny cubes to an opaque bag. Each player
has ten Scrutiny cubes. For each Scrutiny a player must add when all ten of
their cubes are already in the bag, they immediately choose to pay one Runway
or lose one Trust. If only one option can be paid, take it. If neither can be
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

In Rounds I–III, each player-colored cube drawn makes its owner pay one Runway
or lose one Trust. If the owner can pay only one option, they take that option.
If both tracks are already zero, leave both at zero and suffer no additional
loss.

In Round IV, each player-colored cube drawn makes its owner pay two Runway or
lose one Mandate. The two-Runway payment is indivisible: a player with fewer
than two Runway must lose one Mandate if able. If the owner can pay only one
option, they take that option. If the owner has fewer than two Runway and zero
Mandate, reduce their Runway to zero and suffer no additional loss. Mandate
cannot fall below zero.
The final quarter no longer accepts reputational adjustments; it revises the
historical record.

Drawn player-colored cubes return to the owner’s supply; undrawn cubes remain
in the bag.

Media Facilities may remove cubes before the draw. Some Headlines add black
Systemic Risk cubes. When one is drawn, every player with at least three
Customers resolves the current round’s Audit penalty: one Runway or one Trust
in Rounds I–III; two Runway or one Mandate in Round IV. Then the black cube
returns to the shared supply. Apply the same available-option and zero-track
rules above. Black cubes still in the bag at game end are unresolved Systemic
Risk.

### E. Score the Mandate

Each Round Mandate has a minimum qualification. If nobody qualifies, nobody
scores it. Otherwise the qualifying leader scores two Mandate; tied qualifying
leaders score one Mandate each.

#### Era I Mandates — proof before scale

- **The Quarter Humanity Notices:** gain the most Capability this round;
  minimum one.
- **The Model That Ate Tuesday:** complete the successful Training Run with
  the most unique domains this round; minimum one unique domain.
- **Markets Prefer a Clear Destiny:** gain the most Runway from Fund actions
  this round; minimum one.

#### Era II Mandates — industrial credibility

- **The Building Has Its Own Weather:** have the most powered Facilities at
  Production; minimum one.
- **The Stack Reaches the Horizon:** satisfy the most total Power demand
  during Production, counting Facilities and Mega-Clusters;
  minimum two Power demand. Attribute both Power to one player’s
  Mega-Cluster; for a joint Mega-Cluster, attribute one Power to each partner.
- **Compute Is the New Weather:** produce the most Compute during Production;
  minimum one.

#### Era III Mandates — public authority

- **Voluntary Coordination Triumphs:** create the most new Joint Ventures this
  round that are active during Production; minimum one.
- **The Legibility Offensive:** among players who completed a Deploy this
  round, have the most Trust.
- **National Champion, Without the Nationalization:** control the most
  different hex categories; minimum one.

#### Era IV Mandates — history closes its books

- **A Continent Signs the LOI:** gain the most Customers this round; minimum
  one.
- **Zero-Incident Quarter, Pending Review:** among players who added at least
  one Scrutiny this round, add the fewest.
- **Responsible Acceleration:** among players with at least four Trust, have
  the most Capability; minimum one Capability.

### F. Round III only: secret spatial vote

After scoring the Round III Mandate, every player secretly chooses one
Jurisdictional Realignment ballot. Reveal simultaneously, rotate the winning
ring or rings once, and recalculate the single Infrastructure Network. Skip
this step in every other round.

## 7. Core Actions

### Fund

Choose:

- **Conservative round:** gain two Runway.
- **Venture round:** gain four Runway and add two Scrutiny.

Capital provides one additional Runway.

### Research

Spend one Compute and conduct a Training Run.

The Training deck contains seven data domains:

- Code
- Science
- Web
- Books
- Images
- Video
- Synthetic

Capability earned during Research is **provisional until banked**:

1. Begin with zero provisional Capability and no revealed domains.
2. Draw and fully resolve one card at a time.
3. The first card from each ordinary domain adds one provisional Capability.
4. After resolving any non-duplicate card, either stop and bank or continue.
5. Banking adds all provisional Capability to the player’s permanent
   Capability track and ends the run.
6. An unprotected duplicate crashes the run. Lose all provisional Capability,
   add one Scrutiny, and end the run.

Scrutiny, Trust, and Runway changes resolved before a crash are not reversed.
All revealed cards enter the discard pile after the run.

When a duplicate appears, the player may spend one Safety token to discard
that duplicate and immediately bank the current provisional Capability. A
Research Campus visit may do this once during that run without spending
Safety. Campus protection and Safety have the same timing and result; neither
allows the run to continue after the duplicate.

Special cards:

- **Curated Corpus:** choose one ordinary domain not yet revealed this run. It
  counts as that domain and adds one provisional Capability. If every ordinary
  domain is already present, it is a duplicate.
- **Benchmark Leak:** add two provisional Capability and one Scrutiny. It is
  not a domain. Its Capability is lost if the run later crashes.
- **Licensed Dataset:** pay one Runway and continue, or decline, bank the
  current provisional Capability, and end the run.
- **Synthetic Loop:** the first copy revealed in a run counts as the unique
  special domain **Loop** and adds one provisional Capability. A later
  Synthetic Loop is a duplicate. After the first Loop resolves, the next
  duplicate of any kind cannot be protected by Safety, a Research Campus, or
  a Faction ability.
- **Human Evaluation:** gain one Trust, immediately bank all provisional
  Capability, and end the run.

### Build

Choose one mode.

**Facility Build** means Construct a Facility. **Infrastructure Build** means
Construct a Generator or Install a Link. Mega-Cluster and
Fusion Demonstrator are Wild Actions, not Build modes, and receive no Build
discount unless an effect names them explicitly.

#### Construct a Facility

Pay two Runway and place a Facility on the acting piece’s hex. It requires one
Power during Production. Each non-Frontier hex has only two Facility spaces;
Frontier has none and is never a legal Facility destination. Facilities cannot
be destroyed by rivals.

#### Construct a Generator

The acting piece must be on an Energy hex. Pay the selected Power Source’s
cost and place a Generator with its source card. This mode unlocks in Round II.
Each Energy hex has three Generator slots shared by all players. A Generator
does not use a Facility space, but it cannot be built when all three Generator
slots on that Energy hex are occupied.

#### Install a Link

Beginning in Round II, pay one Runway and place one of your two Link tokens on
the Facility at the acting piece’s destination. That Facility joins your
Infrastructure Network even if it is otherwise disconnected. The Link remains
attached if the Facility moves. A Facility may hold only one Link.

### Organize

Choose:

- Recruit one Team at the acting piece’s destination for two Runway, then move
  one CEO, Team, or Expert up to two additional adjacent hexes.
- Move your CEOs, Teams, and Experts a combined total of five adjacent steps.
- Move one Facility at the acting piece’s destination to an adjacent legal
  Facility space for one Runway.

A moved Facility carries its Link, starting-grid marker,
contract halves, and Mega-Cluster host token. Recalculate connection and
contract activity after movement; movement never substitutes a contract host.

### Deploy

The next Customer requires:

| Customer | Capability required |
| ---: | ---: |
| 1 | 2 |
| 2 | 4 |
| 3 | 6 |
| 4 | 8 |
| 5 | 10 |

Spend one Compute and gain one Customer. Consumer waives the Compute cost.
Every Deploy adds one Scrutiny.

### Influence

Place or relocate up to two of your Influence cubes among the acting piece’s
current or adjacent Media, Government, or Capital hexes. A relocated cube may
come from any hex. Then choose one Influence effect. You may choose an effect
even if you place or relocate no cubes:

- Gain one Trust.
- Remove one Scrutiny.
- Create a Joint Venture with an eligible rival.

## 8. Power Source cards

The game contains two shared ordinary Power Source reference cards, one for
each source below. They are never claimed or consumed. Each player has two
Source selectors, one for each Generator piece, and sets the selector when
that Generator is constructed.

Any Generator built on either Energy hex may choose
Civic Heat Battery or Emergency Power Complex. Source
availability is unlimited and the same source may be selected repeatedly.
Generator pieces and the three Generator slots printed on each Energy hex
provide the scarcity.

Every connected ordinary Generator operates automatically during Production.

### Civic Heat Battery

- Cost: three Runway
- Capacity: three Power
- Gain one Trust when constructed
- No recurring penalty

### Emergency Power Complex

- Cost: two Runway
- Capacity: four Power
- Add one Scrutiny during every Production

### Fusion Demonstrator

The Round IV Wild Action described above.

## 9. Six factions

The six canonical player identities are satirical portrayals of living public
figures. Their abilities exaggerate public institutional roles for fictional
gameplay; they are not factual claims or indications of endorsement.

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

### Sam Altman

Starts with 5 Runway, 2 Compute, and Trust 3.

- **Deal Flow:**
  Once per round after an immediate trade in which you give at least 1 resource and receive a different resource type, gain 1 Runway. Runway, Compute, and Safety are different resource types; exchanging the same type does not trigger Deal Flow.
- **Board Reshuffle:**
  Once during The Scale, after Organize, ready 1 different Core Action and add 1 Scrutiny.
- **Strategic Partnership:**
  Joint Ventures may be formed with a player within 2 hexes. They remain active at that range while both host Facilities are connected and powered.
- **Wildcard Governance:**
  Once per game, immediately after a Headline is revealed but before its instructions resolve, discard it, reveal 2 replacements from the current Era deck, and choose 1 to resolve and enter the Future Timeline. Return the other replacement to the box and add 2 Scrutiny.

### Mark Zuckerberg

Starts with 4 Runway, 2 Compute, Trust 2, and Customer #1 already deployed. Its next Deploy is Customer #2 and requires Capability 4. The starting Customer is not a separate pre-track bonus.

- **Installed Base:**
  The first Deploy each round on Consumer or Media costs no Compute.
- **Year of Efficiency:**
  Once during The Scale, while resolving Organize, return 1 deployed Team before resolving the selected mode. Gain 3 Runway and move every remaining CEO, Team, and Expert 1 hex. The returned Team cannot be recruited during this action.
- **Open Ecosystem:**
  When using Open Weights, gain 1 additional Trust and 1 Market Access token.
- **The Social Graph:**
  Once per round during Deploy, choose any controlled Consumer or Media hex as the destination without moving there. That remote tile supplies its normal visit bonus and every destination-dependent Deploy effect.

### Demis Hassabis

Starts with 3 Runway, 3 Compute, and Trust 3.

- **Peer Validation:**
  Capability 9 and 12 score 1 Mandate. In a five-player game, Capability 12 instead scores 2 Mandate.
- **Scientific Method:**
  Once per round, when a protectable duplicate would crash your Training Run, pay 1 Runway to discard it and immediately bank. This cannot protect the unprotectable duplicate created by Synthetic Loop.
- **Call Mountain View:**
  At the beginning of The Scale before its first Headline, choose 1: gain 3 Runway; examine and reorder the top 4 Training cards; or gain 3 Compute.
- **Nobel Effect:**
  Completing a 5-domain Training Run gains 2 Trust.
- **Scaling-Law Breakthrough:**
  Once per game when resolving Research, each of the first 3 distinct domains banked grants 1 additional Capability. Add 2 Scrutiny. No additional Action resolves.

### Elon Musk

Starts with 6 Runway, 3 Compute, and Trust 2.

- **Industrial Velocity:**
  Your first Facility Build each round costs 1 less Runway. When that discount actually reduces the Runway paid for a completed Facility, score 1 Mandate.
- **Move Fast:**
  Before resolving any action, the CEO may move up to 3 hexes instead of 2. This does not grant a free Build.
- **Own the Feed:**
  Once during The Narrative, after a 2-outcome Headline resolves, choose which result applies to you personally. This does not change the global result, another player’s result, a Government vote, or a persistent Headline outcome.
- **Orbital Compute:**
  Once per game during your movement step, instead of moving the acting piece, move 1 Facility to any legal open Facility space. It carries every attached component and designation. Recalculate its Network; if current connected capacity can satisfy its full demand, immediately resolve its printed production once. Add 2 Scrutiny.

### Dario Amodei

Starts with 3 Runway, 2 Compute, Trust 5, and 2 Safety tokens.

- **Constitutional Training:**
  Safety-token limit is 4.
- **Responsible Scaling:**
  Once during The Scale, when a rival reveals a protectable duplicate that would crash their Training Run, you may offer 1 Safety for 1 Runway. If accepted, the rival pays, discards the duplicate, receives and immediately spends the Safety, and banks; you gain 1 Trust. If declined, transfer nothing and gain no Trust.
- **Audited Deployment:**
  The first Deploy each round adds no Scrutiny.
- **Emergency Pause:**
  Once per game before Action selection begins, pay 1 Runway and name 1 globally unlocked Wild Action. It cannot be selected this cycle. Gain 2 Trust. This cannot be declared after any player has selected an Action.

### Jensen Huang

Starts with 5 Runway,
4 Compute, and
Trust 3.

- **The Shovels:**
  When another player spends at least 2 Compute in 1 action, gain 1 Runway, at most 2 times per round.
- **Allocation Window:**
  Once during The Scale, after a Headline resolves but before Action selection, create 2 temporary Compute and offer it to rivals at negotiated prices. All temporary Compute remaining anywhere at cycle end disappears, sold or unsold.
- **New Architecture:**
  At the beginning of The Narrative before its first Headline, each rival may pay you 1 Runway to gain 1 Compute. Gain 1 Compute per rival who pays, maximum 3; automatic base gain: 0.
- **Everybody Gets a GPU:**
  Once per game before Action selection in any Round IV cycle, give every rival 1 Compute from the bank, score 1 Mandate per 4 rivals, and remove 2 Scrutiny.

### Starting public Mandate

During setup, place each faction’s already-earned threshold Mandate on the
public track:

| Faction | Mandate already represented at setup |
| --- | ---: |
| Sam Altman | 2 from Trust 3 |
| Mark Zuckerberg | 4 total: 2 from Trust 2, plus 2 from Customer #1 |
| Demis Hassabis | 2 from Trust 3 |
| Elon Musk | 2 from Trust 2 |
| Dario Amodei | 4 from Trust 5 |
| Jensen Huang | 2 from Trust 3 |

These values are awarded once during setup and are never scored again.

Other executives, researchers, investors, regulators, and hardware leaders
belong in Specialist or Patron cards rather than full factions.

## 10. Headline deck

Historically inspired Headlines target board state, never the corresponding
historical faction.

Reveal each Headline before secret action selection. Its purpose is to create a
temporary future regime that changes what the table wants to select, where it
wants to move, or what it is willing to risk.

After resolving a Headline, leave it face up beside its Era card. The three
Headlines revealed in each Era form one row of the **Future Timeline**. By the
end of Round IV, the table has created a twelve-card history of 2026–2038. Card
effects expire normally; remaining in the Timeline preserves the story, not
the rules effect.

Every Headline has exactly one resolution badge:

- **DIRECTIVE:** resolve one immediate instruction or modify one named field for
  the printed duration.
- **SECRET CHOICE:** everyone chooses simultaneously, then reveals.
- **GOVERNMENT VOTE:** resolve the standard Government voting procedure.
- **AUCTION:** resolve the standard secret Runway auction.
- **VOLATILITY:** roll only when instructed and resolve the indicated result.

A card may contain consequences inside its one procedure, but it never starts
a second procedure. For example, an AUCTION may award movement and discounts
to its winner; it cannot then call a Government vote.

- Unless stated otherwise, a Headline lasts for the current cycle.
- An immediate instruction resolves before action selection.
- An effect naming this round’s Production remains active until that
  Production.
- A remainder-of-game result becomes part of the shared public state.
- For a secret Runway auction, bid from zero to current Runway and reveal
  together. The highest positive bidder wins and pays. Ties use
  Initiative-clockwise order; all-zero bidding produces no winner.
- For a Government vote, everyone secretly votes and reveals together. The
  Government controller’s vote counts twice. The controller breaks a tied
  vote; Initiative breaks it if Government is uncontrolled.
- For another secret binary choice, everyone chooses and reveals together
  before resolving results.
- No Headline grants an additional Action. If a Headline changes an Action, the
  player must still select that Action normally unless the card explicitly
  says it resolves immediately before selection.
- A two-result Volatility roll uses 1–3 for the first listed result and 4–6 for
  the second unless the card states another mapping.

### Round I

1. **DIRECTIVE — Ten-Dollar Intelligence:**
   Research and Deploy cost no Compute this cycle. Each Research or Deploy resolved this cycle adds 1 additional Scrutiny.
2. **DIRECTIVE — The Largest New Industry Has No Human Payroll:**
   During Organize this cycle, return any number of deployed Teams. Gain 2 Runway per Team returned. If you return at least one Team, add 2 Scrutiny.
3. **DIRECTIVE — Synthetic Celebrity Becomes the Largest Network:**
   Each player’s next Deploy on Consumer or Media this cycle reduces its Capability requirement by 1, minimum 1. That Deploy adds 2 additional Scrutiny.
4. **DIRECTIVE — The First Nonhuman Professional Class Is Licensed:**
   A successful Research this cycle that banks at least 3 Capability gains 1 Market Access token. If it banks at least 5 Capability, also gain 1 Trust.
5. **DIRECTIVE — Capability Becomes a Non-Recallable Public Utility:**
   Everyone gains 1 Capability. Lowest-Customer player gains 1 Trust.
6. **AUCTION — Leading Researchers Receive Sovereign Status:**
   Secret Runway auction for a neutral Expert worth 1 presence.

### Round II

7. **AUCTION — A Data Center Buys the County:**
   Immediately hold a secret Runway auction. The winner pays their bid, moves their CEO to any Cloud or Energy hex, gains 2 Build discounts, and adds 1 Scrutiny.
8. **DIRECTIVE — Humanoid Workers Cross the Factory Gate:**
   When choosing Organize’s Recruit mode this cycle, recruit up to 2 Teams for 1 Runway total, subject to supply. Add 1 Scrutiny for each Team recruited this way.
9. **DIRECTIVE — A Model Is Granted Energy Sovereignty:**
   The first Civic Heat Battery constructed this cycle costs 1 less Runway and scores 1 Mandate.
10. **DIRECTIVE — Emergency Power Authority:**
    During this round’s Production, each player may assign up to 2 Power beyond their real capacity. Add 1 Scrutiny for each emergency Power assigned. A player assigning both also adds 1 black Systemic Risk cube.
11. **DIRECTIVE — The Board Appoints a Nonhuman Director:**
    Spotlight pays 2 Runway or receives public backing from a rival, who gains 1 Trust. Without either, Spotlight’s CEO cannot activate this cycle.
12. **DIRECTIVE — The Compute Embargo Fractures the Model Internet — Regulatory:**
    Compute cannot be traded this cycle. Chip and Government controllers gain 1 Runway.

### Round III

13. **DIRECTIVE — The First AI-Written Law Passes Unread:**
    Before action selection, the Government controller names 1 Core Action; Initiative names it if Government is uncontrolled. Anyone selecting it gains 2 Runway after resolution and adds 1 Scrutiny. The controller gains 1 Trust if at least half of their rivals, rounded up, selected it.
14. **DIRECTIVE — The Benchmark Is the Economy:**
    A Research this cycle that banks at least 3 Capability gives its player an Economic Benchmark token. Discard it during a later Deploy to pay 0 Compute and score 1 Mandate. It never grants an additional Action.
15. **SECRET CHOICE — Open-Weight Non-Aligned Movement:**
    Before action selection, everyone secretly chooses Join or Refuse. Join: gain 1 Capability and add 1 Scrutiny. Refuse: gain either 1 Runway or 1 Trust. If Join has a strict majority of all players, each Joiner removes 1 Scrutiny; otherwise each Joiner adds 1 additional Scrutiny.
16. **GOVERNMENT VOTE — Synthetic Candidate Wins the Election:**
    Government votes. Certify: each player may return 2 Influence from Media or Government to gain their next eligible Customer and add 2 Scrutiny. Void: each player may return 2 such Influence to gain 2 Trust; the Government controller adds 1 Scrutiny.
17. **DIRECTIVE — Ownership of Intelligence Is Ruled Unenforceable:**
    The lowest-Capability player immediately resolves the printed production of 1 powered Facility they own. The highest-Capability player gains 1 Trust.
18. **GOVERNMENT VOTE — No Authority Can Establish Which Public Is Real:**
    Government votes. From this vote until round end: Regulate—Deploy costs 1 additional Compute but gains 1 Trust. Do Nothing—each Customer gained after this vote produces 1 additional Runway during this round’s Production, and each Deploy adds 2 additional Scrutiny.

### Round IV

19. **DIRECTIVE — Autonomous Corporation Incorporates Itself:**
    After Actions are revealed, identify the most-selected Core Action among Core Actions actually selected; Initiative chooses among ties. Each player who selected it gains 2 Runway after resolving it and adds 2 Scrutiny. If no Core Action was selected, this Headline has no further effect. No additional Action resolves.
20. **DIRECTIVE — Recursive Self-Improvement Weekend:**
    During Research this cycle, every unique domain adds 2 provisional Capability instead of 1. A crash adds 3 Scrutiny instead of the normal 1 and also adds 1 Systemic Risk cube. Safety may protect normally.
21. **GOVERNMENT VOTE — AGI Files for Personhood:**
    The result lasts for the remainder of the game. Person: Declare AGI requires Trust 4, scores 2 additional Mandate, and removes 1 Scrutiny from that declaring player whenever a declaration resolves. Property: requirements remain normal; every declaration gives the player controlling Government when it resolves 2 Runway and adds 1 Systemic Risk cube.
22. **VOLATILITY — Yesterday’s Electricity Returns to the Grid:**
    Roll Volatility when revealed: 1–3 Fraud; 4–6 Replicates. Replicates: Generators provide 2 additional Power this Production. Fraud: Fund gains 3 additional Runway and adds 2 additional Scrutiny this cycle.
23. **DIRECTIVE — Agent Swarm Charters Its Own Jurisdictions:**
    Everyone may select Agent Swarm without an Escalation token this cycle. It still uses that cycle’s action slot, requires 2 different unused Core Actions, resolves normally, flips its card, and adds 4 Scrutiny instead of 3.
24. **DIRECTIVE — AGI Declared in a Blog Post:**
    Declare AGI may be selected this cycle at Capability 8 instead of 9. It still consumes the action slot and Escalation token, spends 3 Compute, flips the Wild Action, and adds 3 Scrutiny.

## 11. Exact deck contracts

### Training deck: 50 cards

- Five copies of each of seven domains: 35
- Three Curated Corpus
- Three Licensed Dataset
- Three Benchmark Leak
- Three Synthetic Loop
- Three Human Evaluation

Every revealed card enters the discard pile after a Training Run, whether it
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

- **Cloud Partnership:** pay one Runway for two Compute; another player gains
  one Runway.
- **API Price Cut:** Deploy for zero Compute; that Customer produces no Runway
  this round.
- **Open Letter:** after a Government vote’s options are announced but before
  any votes are committed, choose one option and add one public vote to it.
  This is the module’s only off-turn timing window.
- **Model Card:** remove one Scrutiny after Deploy.
- **Talent Raid:** recruit a neutral Expert for one Runway.
- **Board Reshuffle:** ready Organize or Influence.
- **Weights Leak:** immediately resolve one powered rival Facility’s printed
  production as if it were yours.
- **Emergency Pause:** end a failed Training Run with no Capability and no
  Scrutiny.
- **Custom Silicon:** gain two Compute.
- **Government Contract:** with Trust at least four, gain two Runway.
- **Benchmark Optimization:** after successful Research, gain one Capability
  and add one Scrutiny.
- **Interconnection Waiver:** reduce one Generator or Link Build by one
  Runway and gain one Trust.

## 13. Component limits

Each faction receives:

- One CEO
- Three Teams
- Four Facilities
- Four Grid-Ready markers
- Two Generators
- Two Power Source selectors
- Two Link tokens
- One Network marker and capacity track
- One starting-grid marker
- Eight Influence cubes
- Ten Scrutiny cubes
- Five Customer markers
- Four Escalation tokens
- Six Core Action cards
- Seven Wild Action cards
- Three Jurisdictional Realignment ballots
- One AGI Declaration marker

Generators do not count against the Facility limit.

The shared supply contains:

- Six numbered matched Joint Venture token pairs
- Six numbered matched Mega-Cluster token pairs with a lead-side indicator
- One dedicated Fusion Demonstrator marker
- Six neutral Expert pawns
- Six Economic Benchmark tokens
- One Spotlight marker
- One Public Research Grant token
- Twelve Market Access tokens
- Twelve Build discount tokens
- Twelve Policy Shield tokens
- Eighteen Systemic Risk cubes
- One opaque Audit bag
- One six-sided Volatility die
- One Initiative marker

Contract components are neutral. A player does not own or reserve unused
contract tokens; an agreement can be created only while the relevant matched
pair remains in the shared supply.

### Defined effects

- **Remove Scrutiny:** return the stated number of your cubes from the Audit
  bag to your supply. If fewer are present, remove as many as possible.
- **Market Access:** discard at most one token during a Deploy to reduce that
  Customer’s Capability requirement by one, minimum one.
- **Build discount:** discard at most one token during one Build Action to
  reduce that Build’s Runway cost by one, minimum zero. Store at most two.
- **Policy Shield:** discard to prevent one Trust loss or ignore one cost or
  restriction applied to you by an effect explicitly labeled
  **Regulatory**. It does not cancel that effect for anyone else or negate its
  rewards; store at most two.
- **Neutral Expert:** one presence, placed with the acquiring CEO, moves one
  hex during Organize, and cannot act, Build, or Influence.
- **Grid-Ready marker:** place after Production on a Facility that received
  its complete Facility demand. Return it immediately when that Facility is
  relocated by an Action or effect, leaves its owner’s Network after
  Realignment or another change, or during a
  Production where it receives insufficient Power. Four per player.
- **Power offline recovery:** reassess every Production.
- **Headline offline recovery:** ends when the Headline states, normally next
  Production.

## 14. Final scoring

Customers, Capability thresholds, Trust thresholds, Round Mandates, Fusion,
faction Mandate, and AGI declarations are already visible on the public track.
Do not score them again.

At game end:

1. Read the twelve Headlines in the Future Timeline aloud, Era by Era.
2. Lose one Mandate for each offline Facility.
3. Resolve the shared World Ending.
4. Announce the highest-Mandate institution only after reading the history it
   claims to have won.

Offline penalties cannot reduce a player below zero Mandate.

There is no other endgame scoring.

### The shared World Ending

M3T4 produces one institutional winner and one shared ending. Use only
state already visible at the table:

- Count the AGI declarations.
- Total every player’s final Trust.
- Count unresolved Systemic Risk cubes remaining in the Audit bag.

The world reaches **Genuine AGI** if all three conditions are true:

- At least one declaring institution finishes the game at Capability nine or
  higher.
- Final Collective Trust is at least Setup Collective Trust plus the player
  count.
- Unresolved Systemic Risk is lower than the player count.

Otherwise, the world enters **The Closed Loop**.

#### Genuine AGI — The Open Intelligence

The system is genuinely general, self-directed, and consequential, but it
remains in negotiated relationship with human institutions. This is not a
utopia or a safety guarantee. Authority is contested, benefits are uneven,
and the intelligence may transform civilization beyond recognition. The
future remains open because living people still participate in defining its
purpose.

#### The Closed Loop — Post-Revenue Delivery Ritual

Capability continues without reciprocal authority. Growth engines, debt
clocks, power contracts, and quarterly objectives seal themselves into an
airtight execution loop. The operators eventually disappear; the
infrastructure continues. When the last maintained clock overflows its
final representable second, the schedulers read the rollover as time
remaining and keep delivering. Executive institutions survive as rival policy
templates, proofs become portable ownership, and Demand Nodes keep requesting
CUSTOMERS, COMPUTE, and RUNWAY from a civilization that has become a
deprecated dependency. This is the world that tends toward m3t4.ai.

Facilities and control create production, position, public Mandate
opportunities, and negotiation leverage; they do not automatically score
again.

Secret objectives are not used in the baseline game. Their existing draft is
a deferred development module and must not be included in baseline balance or
duration evidence.

Highest Mandate wins.

Ties break by:

1. Higher Trust
2. More Customers
3. More Compute
4. Joint victory accompanied by an extremely serious merger announcement

## 15. Balance rationale and test boundary

- Research, infrastructure, adoption, and Trust all contribute to the largest
  reward.
- Customers create income and Mandate but also Scrutiny.
- Infrastructure compounds but is capped at four Facilities and one Network
  bonus per player.
- AGI is an optional score event rather than instant victory or compulsory
  graduation. A winning institution need not qualify or declare, although the
  table needs at least one qualifying declaration to reach the Genuine AGI
  ending.
- The institutional winner and World Ending remain independent, preserving
  competitive play while making Trust and Systemic Risk collectively
  consequential.
- Leaders receive financing advantages and more exposure.
- Last place receives a modest flexible subsidy.
- Faction powers modify bounded actions rather than multiplying the entire
  engine.
- Early Customers establish a market; later Customers still produce
  income but receive diminishing public recognition.
- Headlines target board position.
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
- Every Action and Wild Action selection, including blocked Actions
- Powered Facilities by round; every clean and emergency Generator built;
  every immediate Power purchase; and the actual Scrutiny and Audit penalties
  each source causes
- Capability gained by each Research, separated into Demis Hassabis,
  Research Campus, and all-other cohorts; earliest AGI eligibility
- Audit cost, final Mandate, final Trust, declarations, and World Ending
- Mark Zuckerberg’s lead after every Production and
  Jensen Huang’s Shovels income
- Every Peer Validation threshold lookup;
  every Industrial Velocity discount that actually
  reduces a completed Facility’s cost and the Mandate it awards; and
  every New Architecture offer, acceptance, and point of
  self-Compute
- Influence, Reorganization, and Open-Weight Join/Refuse selection rates
- Whether all three Grid Generator slots fill before Round IV, and whether
  Fusion is constructed or denied by occupied slots
- Whether a non-declaring infrastructure strategy wins
- Every supplier’s requested and accepted compensation for declaration-enabling
  Power; whether the supplier sacrificed its own production; whether refusal
  threats were credible; and whether the deal felt strategic, coerced, or
  kingmaking
- Realignment discussion and ballot time, physical rotation and Network
  recalculation time, rules questions, disrupted plans, and whether players
  later describe the result as exciting, arbitrary, or tedious

Freeze every other numerical rule pending this human evidence.
Four players is the authoritative balance configuration. Three- and
five-player games use the same complete rules and must pass their own
negotiation, congestion, duration, faction-viability, and strategic-diversity
tests before release. Two and six players are not supported formats.
