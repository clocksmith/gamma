# ${game.title} — Core Rules

**Rules version:** ${game.rulesVersion}
**Executable version:** ${game.executableVersion}

A smaller institutional strategy prototype for two through five players, across four Eras. Six institutions compete through research, engine building, customers, and negotiation. Costs and scoring values are a test candidate; balance and blind usability are unqualified.

An Org is a major operating branch of your institution, encompassing people, AI systems, and automated operations. Its internal scale grows across the Eras. You start with two Orgs and may establish up to four; additional Orgs increase presence, not the number of turns.

## Setup

Choose an institution and a colour-and-symbol player kit independently. The faction identity card gives your starting Runway, Compute, Capability, Reputation, and Customer cards, plus one permanent ability. Place four cubes on the generic player mat. Take two Orgs into play, initially unassigned, and leave two in supply. Leave your four numbered Facilities unbuilt, five Customer cards in order, and six Core Action cards available. An institution never determines piece colour. Seat identifies ownership in the engine.

Lay out the six shared areas, the four-Era Governance Board, and the shuffled shared forty-card Training deck. Split Headlines by Era and shuffle each six-card packet. Split objectives by Era. Choose Initiative randomly before the game; the executable uses seat zero. Initiative advances clockwise after every cycle. All resource holdings and components are public; selected Actions remain secret until everyone has selected. Unrevealed cards and Training draw order remain hidden.

<!-- map:start -->
## Six shared areas

There is one area per Core Action: Fund, Research, Build, Organize, Deploy, and Influence. Each has two shared Facility spaces. Orgs do not consume these spaces. Area order has no mechanical effect. There is no adjacency, distance, movement cost, Facility relocation, Generator, or Power eligibility.

An acting Org goes to the area matching its Core Action and stays there until reassigned. Build may place a Facility in any area with an open space. Orgs and Facilities each count as one presence. You control an area only if you have strictly more presence than every rival; tied areas are uncontrolled. Control matters only when a printed objective asks for it.

Each Facility always produces its area's printed yield. Upgraded Facilities double that yield. The six yields are printed on the areas:

| Action area | Yield per Facility |
|---|---|
| Fund | ${content.gameConfig.board.tiles.0.production} |
| Research | ${content.gameConfig.board.tiles.1.production} |
| Build | ${content.gameConfig.board.tiles.2.production} |
| Organize | ${content.gameConfig.board.tiles.3.production} |
| Deploy | ${content.gameConfig.board.tiles.4.production} |
| Influence | ${content.gameConfig.board.tiles.5.production} |
<!-- map:end -->

## Four tracks and Customer cards

Runway is money; Compute pays for Research, Deployment, upgrades, and AGI recognition. Capability represents demonstrated intelligence. Reputation represents public standing. Apply costs before gains; a cost must be affordable in full. Gains stop at the printed cap, and losses stop at zero: Runway 12, Compute 10, Capability 12, Reputation 6. Reputation losses are consequences and may occur at zero; a printed Reputation payment must be affordable.

Customers are cards, not a fifth numerical track. The five cards require Capability 2, 4, 6, 8, and 10 respectively. Take the next card in order; never more than five. Each held Customer provides one Runway at Production and two points at game end. Read Customer count from the cards. There is no historical deployment counter or remembered customer threshold.

## Era and cycle

At the start of each Era, ready all six Actions. Reveal one of that Era's three objective cards and retain it face up. It will score from the final table, not now. Play three cycles:

1. Reveal one Headline from this Era's packet and resolve its immediate effects and choices in Initiative order. Keep it in the timeline; it leaves no continuing modifier.
2. Each institution secretly selects one unused Core Action, even if it currently cannot afford a resolution. Reveal together.
3. Resolve in Initiative order. You may offer one immediate trade, then choose an Org, assign it to the matching area, pay the cost, and resolve one legal mode of your selected Action. If no legal resolution exists after trading, the Action does nothing and is still used.
4. Exhaust the selected card. Advance Initiative clockwise.

No Action may be selected twice in one Era. After the third cycle, resolve Production and Reputation Review. Advance the Era; in Era IV proceed to AGI recognition and final scoring instead.

## Six Core Actions

**Fund:** Gain two Runway, or gain four Runway and lose one Reputation. Credit the actual income after caps.

**Research:** Pay one Compute and begin a Training Run. Draw one card, resolve it, then bank or draw again when permitted. Ordinary domains add one provisional Capability the first time they appear. Repeating a domain crashes the run and loses all provisional Capability. Banking adds the provisional amount to your track, subject to its cap. Revealed cards enter the shared discard pile; when the deck empties, shuffle the discard as a new draw pile. There is no private Research deck.

Curated Corpus counts as the first absent ordinary domain in printed deck order (Code, Science, Web, Books, Images, Video, Synthetic), adding one provisional Capability; with all seven present it crashes. Benchmark Leak adds two provisional Capability and loses one Reputation; its loss stays even if the run later crashes. Human Evaluation gains one Reputation and automatically banks the run. Neither special card is an ordinary domain. Resolve Scientific Method or crash retention exactly as the chosen faction card states.

<!-- construction:start -->
**Build:** Build one numbered Facility in any area with an open Facility space for two Runway, or from Era II upgrade one of your existing unupgraded Facilities for three Runway and one Compute. These are exclusive choices. Use Facilities in numerical order. Flip an upgraded Facility; it doubles its printed area yield permanently. Each Facility can be upgraded once. No separate upgrade chips or types exist. Industrial Velocity discounts only the Facility construction price by one Runway.
<!-- construction:end -->

**Organize:** Pay two Runway to establish one Org from supply into the Organize area, or reassign one other Org to any area. First assign the acting Org to Organize. You may have at most four Orgs. Reassignment has no cost or distance restriction and does not resolve another Action.

**Deploy:** If your Capability meets the next Customer card's requirement, pay one Compute, take that card, and lose one Reputation. Installed Base gives one Runway on this Deploy; gaining a Customer from a Headline does not trigger it.

**Influence:** Gain two Reputation. From Era III you may instead propose one Joint Venture or terminate one you participate in.

## Immediate trading and Joint Ventures

On your resolution turn, you may offer one Runway for one Compute, or one Compute for one Runway, to one named rival. Both must possess the payment and have space under the receiving cap. They may accept or refuse. An accepted trade exchanges both resources atomically, then triggers your Deal Flow if applicable. No counteroffers, third-party transfers, credit, or promises are rules effects. Refusal does not prevent resolving your Action. You cannot trade Capability, Reputation, Customers, recognition, or ownership.

Joint Ventures pair one Facility you own with one rival-owned Facility, regardless of area. Each Facility may host at most one Venture; there are six shared numbered pairs. Public terms identify both hosts and both reciprocal incomes. The rival must consent. Either participant may terminate the Venture using Influence. A Venture is active while both named hosts exist under their recorded owners. At each Production, each participant receives one of the other host's printed contract resource: Compute from Research or Build; Runway from the other four areas. An upgrade does not increase Venture income. No retroactive Production occurs when a Venture is signed. Keep matching Venture numbers on the hosts; no Era markings are needed.

## Production and Reputation Review

In Initiative order, each institution resolves its supplier ability, then all its Facility yields, then one Runway per Customer card. Next resolve active Ventures in agreement order. Apply caps to every credit; nominal capacity for an objective ignores caps but never credits income or triggers abilities. The Shovels pays one Runway per rival owning any Facility, to a maximum of two.

After Production, each institution with Reputation one or less loses two Runway, floored at zero. This fixed Reputation Review replaces the risk bag and Audit draws. There are no Scrutiny or Systemic Risk cubes. No fallback penalty consumes Compute or Capability.

## Final AGI recognition

After Era IV Production and Reputation Review, every institution with at least nine Capability, four Reputation, and three Compute may pay three Compute to take its AGI recognition marker. Resolve optional declarations in Initiative order. Recognition requires no specific Facility. It is a final holding worth four points and does not override the winner.

<!-- mandate-scoring:start -->
## Score the final table once

Final points equal Capability + twice the number of Customer cards + Reputation + four for recognized AGI + awards from all four revealed objectives. Score objectives only now. No immediate points, score track, Trust milestones, or remembered gains remain.

Each revealed objective specifies its current metric and qualification. The best qualified value earns two points; tied qualified leaders each earn one. If nobody qualifies, nobody scores. Qualification is separate from comparison, including a valid zero when a card permits it. Changing past history without changing final holdings must change no score. Nominal Compute capacity uses the same current Facility and Venture eligibility as Production, without spending, producing, applying caps, or firing abilities.

Break final score ties by Reputation, then Customer cards, then Compute. If all are tied, share victory. The separate World Ending uses whether any AGI is recognized and whether average final Reputation is at least three: recognized/open gives The Singularity; recognized/closed gives The Closed Loop; unrecognized/open gives The Plural Future; unrecognized/closed gives Assured Continuity.
<!-- mandate-scoring:end -->

<!-- card-authority:start -->
## Printed component authority

Component records own exact Action, Headline, faction, Training, upgrade, and objective effects. This rulebook owns procedures and the box inventory. Reference aids project those owners. Fiction does not introduce extra requirements.
<!-- card-authority:end -->
<!-- era-panels:start -->
Four Governance Board panels show the Era sequence and unlocks. Upgrades unlock in Era II, Ventures in Era III, and recognition in Era IV. Earlier effects remain available.
<!-- era-panels:end -->
<!-- player-aids:start -->
Each kit has a three-panel foldout summarizing turns, Actions, Production, Review, negotiation, and final scoring. The player mat has four resource tracks and one recognition space. Customer and Facility states are visible on cards.
<!-- player-aids:end -->
<!-- headline-selection:start -->
Twenty-four Headlines are organized as six per Era. Shuffle each packet and reveal three, one before each cycle. Resolve only the printed immediate instruction. Lowest/highest ties target the first tied institution in Initiative order unless an effect applies to everyone.
<!-- headline-selection:end -->
<!-- components:start -->
## Components

Five interchangeable kits serve up to five players; six institutions are independent choices. Mark every owned item with kit colour and symbol. Facilities are numbered and have normal/upgraded faces. Customer cards stay in ordinal order. Org location and matching Venture host numbers are the only shared-area encodings.

<!-- inventory:start -->
### Box inventory

- Six shared action-area cards, each with two Facility spaces.
- One Governance Board with four Era panels, one Era marker, one Initiative marker, and four objective holding spaces.
- Six faction identity cards; five generic player mats and five three-panel player aids.
- Thirty Core Action cards: six in each kit.
- Twenty Orgs: four per kit, two initially in play.
- Twenty two-sided numbered Facility cards: four per kit; the reverse shows the single upgrade.
- Twenty-five Customer cards: five ordered cards per kit.
- Twenty resource-track cubes: four per kit; five AGI recognition markers.
- Twelve paired Venture host markers: six matching numbered pairs.
- Forty shared Training cards: four copies of seven ordinary domains and three special types.
- Twenty-four Headlines: six per Era; twelve objectives: three per Era, four revealed per game.

No hex tiles, Generators, Power contracts, upgrade chips, Audit bag, risk cubes, score cubes, or milestone markers belong to this prototype. Deferred Tactics and secret objectives are excluded.
<!-- inventory:end -->
<!-- components:end -->
