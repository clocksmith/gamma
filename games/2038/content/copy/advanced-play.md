# ${content.worldCopy.title} — Advanced Play Supplement

Advanced Play is one bundled profile. Apply every change below; do not select
individual modules. All unlisted rules remain exactly as written for Default
Game. The **◆** symbol in the Default Rules identifies a rule this supplement
extends or replaces.

${content.ruleChangeRegister.profileComparison}

## Setup

Each player takes two Link tokens, one Network marker and capacity track, and
three ${terms.systems.realignment} ballots in addition to their Default Game components. Add the
six-sided Volatility die to the shared supply. Build each Headline deck from
every card for its Era, including cards with an **Advanced Play** badge.

## Connected infrastructure

Advanced Play replaces local Power with a connected ${terms.systems.infrastructureNetwork}.
The same graph governs ${terms.infrastructure.power} delivery and the Network production bonus:

- The first Facility joins through the basic grid connection.
- Owned Facilities and Generators on the same or adjacent hexes connect to one
  another.
- A Link on one otherwise disconnected Facility joins that Facility to the
  Network. Owned sites adjacent to it may then connect normally.
- ${terms.infrastructure.power} from connected Generators and purchased ${terms.infrastructure.power} is pooled across the
  Network.
- Beginning in Era II, two or more connected, powered Facilities produce one
  additional ${terms.resources.runway} or ${terms.resources.compute}.

Award at most one Network bonus per player. Use this graph for Power delivery
and production; do not calculate edge-by-edge flow. Recalculate the whole
Network when a Facility or Link moves or changes.

Beginning in Era II, **Infrastructure Build** may Install a Link: pay one
${terms.resources.runway} and place one of your Link tokens on the Facility at the acting piece’s
destination. That Facility joins your Network even if otherwise disconnected;
owned sites adjacent to it may then connect normally. A Facility holds at most
one Link and carries it when moved.

A solo Mega-Cluster requires both hosts in its owner’s Network. A joint
Mega-Cluster requires each host in its owner’s Network. When a Facility moves,
recalculate its owner’s Network and every affected contract. Flip a Facility
back to its normal face when it leaves its owner’s Network.

## Immediate resource trades

After the named rival publishes a counteroffer, every eligible player other
than the counteroffer maker—including the original offer maker—may
simultaneously pass or claim it instead of giving the original maker the sole
accept-or-reject decision. The counteroffer maker chooses one claimant or
declines them all. A chosen claim completes immediately, even if neither party
is the active player.

There are no further offers or counteroffers in that resolution. A
counteroffer with no claimant, or with all claimants declined, expires. The
active player then continues the selected Action under the normal blocked-Action
rule if necessary.

## Production ${terms.infrastructure.power} requests

In Advanced Play, each player may make up to two Production Power purchase
requests, each to a different adjacent rival Network. A rejection does not
consume the second request. Supplier limits, price, eligible capacity, and all
other Production rules remain unchanged.

## Headline procedures

Every Headline card is eligible. Resolve exactly one printed badge procedure
per card:

- **DIRECTIVE:** resolve an instruction or modify one field for its duration.
- **SECRET CHOICE:** everyone chooses simultaneously, then reveals.
- **CIVIC PERMISSION AUTHORITY VOTE:** everyone secretly votes and reveals
  together. The ${terms.locations.government} controller’s vote counts twice and breaks a tie;
  Initiative breaks it if ${terms.locations.government} is uncontrolled.
- **AUCTION:** everyone secretly bids from zero to their current
  ${terms.resources.runway}, then reveals. The highest positive bidder pays and wins. Ties use
  Initiative-clockwise order; all-zero bidding has no winner.
- **VOLATILITY:** roll only when instructed. A two-result roll uses 1–3 for the
  first result and 4–6 for the second unless the card states otherwise.

An immediate instruction resolves before action selection. Unless stated
otherwise, an effect lasts for the current cycle; an effect naming this Era’s
Production remains until Production, and a remainder-of-game result becomes
shared public state. Place a persistent Headline beside the affected Action as
a reminder. The current Headline overrides an older persistent Headline on the
same field; effects on other fields remain active. There is no separate Law
system or Law deck.

## Era III ${terms.systems.realignment}

Resolve ${terms.systems.realignment} exactly once, after Era III Mandate scoring. Skip it in
every other Era. Each player secretly chooses and simultaneously reveals one
ballot:

- **Consolidate the Core:** rotate the six inner-ring locations one position
  clockwise.
- **Expand the Periphery:** rotate the six outer-ring locations one position
  clockwise.
- **Authorize Counter-Cycle:** rotate the inner ring one position clockwise
  and the outer ring one position counterclockwise.

A player who places no ballot names no motion and cannot break a tie. The motion
with the most ballots wins. If leading motions tie, scan clockwise from
Initiative; the first player whose ballot names a tied motion chooses it. If
none does, Initiative chooses. Government bonuses and other vote modifiers do
not apply.

${terms.locations.frontier} never moves. Each moving tile carries every CEO, Team, Facility,
Generator and other site-bound component. Rotate the
selected physical ring once, then recalculate every Network from its
starting-grid Facility, Links, and visible adjacency. Do not lift or re-lay
components.

A ring rotation carries each Facility and its Grid-Ready face together.
After recalculating each ${terms.systems.infrastructureNetwork}, flip back any
Facility now outside its owner’s Network.

Joint Ventures remain owned but operate only while their fixed hosts are
adjacent and meet all requirements. Mega-Clusters whose hosts are no longer
adjacent are offline until adjacency returns. Matched tokens travel with their
host Facilities. Immediate ${terms.infrastructure.power} purchases do not persist through Realignment.
Realignment destroys no component, changes no host, and terminates no contract.

Ballot options are public; choices remain secret until simultaneous reveal.
Players may discuss and signal, but those statements are non-binding. The
procedure above alone chooses the motion. Every player then has Era IV’s three
Actions to respond to the changed geography.
