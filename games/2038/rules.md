# ${game.title} — Core Rules

**Rules version:** ${game.rulesVersion}
**Executable version:** ${game.executableVersion}

Two through five institutions compete across four Eras. One shared hex map, Orgs, a player mat, and lore cards carry the game. These newly selected mechanics require fresh balance and human-play evidence.

An Org is a major operating branch encompassing people, AI systems, and automated operations. Its internal scale grows across the Eras. Start with two Orgs; four is the maximum. More Orgs increase presence and production, never the number of turns.

## Setup

Choose an institution and one of five colour-and-symbol player kits independently. Your identity card supplies starting Runway, Compute, Capability, Reputation, Customers, and one permanent ability. Place a cube on each of these five holdings on your mat. Keep your identity card upright. Mandate is the sixth value: a calculated score, not another currency.

Place the Era hex in the middle, then fill two rings with the eighteen Action hexes according to their printed coordinates. Each of the six Action types has three hexes; the inner ring runs Fund, Research, Build, Organize, Deploy, Influence clockwise from the top. Give each player two normal-side Orgs, initially off the map; leave two in reserve. No other player pieces go on the map.

Separate the twenty-four Headlines into four six-card Era packets and objectives into four three-card packets. Shuffle each packet. The Training deck contains forty cards: four copies of each of ten designs. Choose Initiative randomly; it moves clockwise after every cycle. All holdings are public; unrevealed cards remain hidden.

<!-- map:start -->
## Shared hex map

Eighteen playable Action hexes surround the central Era hex. Hexes sharing an edge are neighbors. The center records the Era and is not traversable. There is no wraparound or movement across corners.

On your turn choose one Org. It may stay on its hex or move to one neighboring hex, then perform that hex's Action. An off-map Org may enter any playable hex. Multiple players may share a hex; there is no occupancy limit. If you cannot afford an Action, choose another reachable Action or spend the turn doing nothing. An unresolvable Action does not move the Org.

Each Org counts as one presence, equipped or not. You control a hex only if you have more Orgs there than every rival. Ties leave it uncontrolled. Control matters when an objective asks for it.

At Production, every placed Org earns its hex's printed yield. An equipped Org earns twice that yield. Unplaced Orgs produce nothing. Equipment travels with its Org.

| Hex | Production per Org |
|---|---|
| Fund | ${content.gameConfig.board.tiles.0.production} |
| Research | ${content.gameConfig.board.tiles.1.production} |
| Build | ${content.gameConfig.board.tiles.2.production} |
| Organize | ${content.gameConfig.board.tiles.3.production} |
| Deploy | ${content.gameConfig.board.tiles.4.production} |
| Influence | ${content.gameConfig.board.tiles.5.production} |
<!-- map:end -->

## Six values on one mat

Runway buys equipment and Orgs. Compute pays for Research, Deployment, and AGI recognition. Capability is demonstrated intelligence. Reputation is public standing. Customers are adoption and income. Mandate is your calculated score.

Holding caps are Runway 12, Compute 10, Capability 12, Reputation 6, Customers 5. Costs must be affordable in full; gains stop at the cap and losses at zero. Consequential Reputation losses may occur at zero. A printed Reputation payment must be affordable.

Each Customer provides one Runway at Production and two Mandate at game end. To gain your next Customer through Deploy requires Capability 2, 4, 6, 8, or 10 respectively. There are no Customer cards or remembered deployment thresholds.

## Era and cycle

Reveal one objective at the beginning of each Era and keep it face up for final scoring. Each Era has three cycles:

1. Reveal one Headline from the current Era packet and resolve its immediate instructions in Initiative order.
2. In Initiative order, each institution may offer one immediate trade, then chooses one reachable Action, assigns one Org, and resolves it. Actions may repeat; there are no hands, simultaneous commitments, or exhausted cards.
3. Pass Initiative clockwise. After the third cycle, resolve Production and Reputation Review, then advance the Era.

After Era IV Production and Review, resolve optional AGI recognition, score the final table, and read the World Ending. Every institution receives twelve turns, regardless of Org count.

## Six Core Actions

**Fund:** Gain two Runway, or gain four Runway and lose one Reputation.

**Research:** Pay one Compute. Use the shared forty-card draw pile. Shuffle it at setup and reshuffle the discard pile whenever it runs out. Draw a card, resolve it, then bank or draw again. Keep drawn cards face up for this run. The first appearance of each ordinary domain adds one provisional Capability; a repeated domain crashes the run and loses its provisional Capability. Banking adds the provisional total to your Capability, up to its cap. Revealed cards enter the shared discard; finish after at most forty draws. Retain the current run’s visible domain record if a reshuffle is needed.

Curated Corpus counts as the first absent domain in this order: Code, Science, Web, Books, Images, Video, Synthetic. It adds one provisional Capability; with all seven present it crashes. Benchmark Leak adds two provisional Capability and loses one Reputation, even if the run later crashes. Human Evaluation gains one Reputation and immediately banks the run. Resolve Scientific Method or crash retention as printed on the institution card.

<!-- construction:start -->
**Build:** Pay two Runway to equip any one of your normal-side Orgs. Flip its token. It now earns twice its hex's yield at Production. An Org can be equipped once. The acting Org moves to Build; the equipped Org may be that Org or another one you own. Industrial Velocity reduces the price by one Runway. No Facility cards, building pieces, or separate upgrade markers exist.
<!-- construction:end -->

**Organize:** Pay two Runway to establish one reserve Org, normal side up, on the Organize hex; or reassign one other Org to any playable hex for free. First move or keep the acting Org on Organize. Reassignment is Organize's explicit exception to one-edge movement and does not trigger another Action.

**Deploy:** If you meet the next Customer's Capability requirement, pay one Compute, increase Customers by one, and lose one Reputation. Installed Base grants one Runway on this Action, but not when a Headline grants a Customer.

**Influence:** Gain two Reputation.

## Immediate trading

Before your Action, offer one Runway for one Compute, or one Compute for one Runway, to one named rival. They may accept or refuse. Both must afford the payment and have room under the receiving cap. An accepted exchange happens atomically and triggers Deal Flow where applicable. There are no counteroffers, credit, promises, or persistent Venture contracts. Refusal does not cost your Action.

## Production and Reputation Review

In Initiative order resolve each institution's supplier ability, its placed Org yields, then one Runway per Customer. The Shovels grants one Runway per rival with at least one equipped Org, to a maximum of two. Apply caps to each credit.

After Production, each institution at Reputation one or less loses two Runway, floored at zero. No risk bag or Audit pieces are needed.

## Final AGI recognition

After Era IV Production and Reputation Review, an institution with at least nine Capability, four Reputation, and three Compute may pay three Compute to recognize AGI; rotate its identity card half a turn. Resolve in Initiative order. Recognition grants four final Mandate; it does not override the winner.

<!-- mandate-scoring:start -->
## Score the final table once

Mandate equals Capability + twice Customers + Reputation + four for recognized AGI + awards from the four revealed objectives. Count it from the final table. ${content.gameConfig.scoreDisplay.instructions} Do not accumulate a second historical score.

For each objective, the best qualified value receives two Mandate; tied qualified leaders receive one each. If nobody qualifies, nobody scores. Count Orgs, equipped Orgs, control, neighboring rival institutions, and nominal Compute production directly from the map. A neighboring rival counts once even if several of its Orgs border yours; sharing your hex alone is not adjacency. Nominal Compute production ignores caps without actually producing or triggering abilities.

Break ties by Reputation, then Customers, then Compute; otherwise share victory. The separate World Ending uses recognized AGI and average final Reputation: recognized/at least three gives The Singularity; recognized/below three gives The Closed Loop; unrecognized/at least three gives The Plural Future; unrecognized/below three gives Assured Continuity.
<!-- mandate-scoring:end -->

<!-- card-authority:start -->
## Printed component authority

Component records own exact effects; this rulebook owns procedures and inventory. Actions and their lore are printed on hexes. Unique institutional, Headline, objective, Training, and historical lore is preserved. Historical technology lore remains reference content, not extra equipment or an additional subsystem.
<!-- card-authority:end -->
<!-- era-panels:start -->
The central hex displays all four Eras and the current cycle. Each Era brings its own Headlines and objective. Equipment is available from the start; AGI recognition occurs only after Era IV. There are no Venture or upgrade unlocks to remember.
<!-- era-panels:end -->
<!-- player-aids:start -->
Each player mat includes five holding tracks, a final Mandate scale along its lower edge, the six Action summaries, and the turn and scoring reference. No separate player aid is required.
<!-- player-aids:end -->
<!-- headline-selection:start -->
Keep all twenty-four Headlines: six per Era, three revealed per Era. Their effects finish before turns begin. Unless an effect applies to everyone, tied lowest/highest targets resolve to the first tied institution in Initiative order.
<!-- headline-selection:end -->
<!-- components:start -->
## Components

Five kits use colour and a non-colour symbol. Each kit's four Orgs have numbered normal/equipped faces, with the same owner and number on both sides. Hex positions show presence; token faces show equipment. Five cubes show holdings, while identity-card orientation shows recognition and its upper-edge pointer marks final Mandate on the mat’s lower scale.

<!-- inventory:start -->
### Box inventory

- Nineteen shared hex tiles: three copies of each of six Action types and one central Era/cycle hex.
- Five player mats with integrated references; twenty-five holding-track cubes.
- Twenty double-sided Org tokens: four per kit, two initially available.
- Six institution identity cards.
- Forty Training cards: four copies of all ten existing designs.
- Twenty-four Headline cards: six per Era.
- Twelve objective cards: three per Era, four revealed per game.
- One Era/cycle marker and one Initiative marker.

The playing kit has eighty-two cards and 153 items in total. No writing or pencil is required. Unique historical technology lore remains in the existing reference collection; it has no mandatory pieces. Action lore is printed on the eighteen Action hexes and Era lore on the center. No separate Action, Customer, or Facility cards; no Venture, equipment, recognition, or scoring tokens; no separate Governance Board or foldout aids. Deferred Tactics and secret objectives remain excluded.
<!-- inventory:end -->
<!-- components:end -->
