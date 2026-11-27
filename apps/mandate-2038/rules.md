# ${game.title} — How to play

**Rules version:** ${game.rulesVersion}
**Executable version:** ${game.executableVersion}

For two through five players. This prototype still needs fresh balance and human-play evidence.

Grow your AI organization over twelve turns. The player with the most points at the end wins.

**On your turn, choose one of your pieces and use its space. At the end of each Era, every piece you have placed earns resources.**

## What the names mean

The names below match the board and cards.

| Name       | Meaning                                                            | Maximum |
| ---------- | ------------------------------------------------------------------ | ------- |
| Runway     | Money for equipment and extra pieces                               | 12      |
| Compute    | Processing power spent on Research, Deploy, and the AGI bonus      | 10      |
| Capability | How capable your AI is; helps you gain Customers and scores points | 12      |
| Reputation | Your public standing; also scores points                           | 6       |
| Customers  | Each gives 1 Runway per Era and 2 points at the end                | 5       |

Your playing pieces are called **Orgs**. You start with two and can have up to four. Extra Orgs do not give extra turns. **Mandate** means your final score; you do not spend it.

You must be able to pay an action's full cost. Gains stop at the printed maximum, and losses stop at zero. Losing Reputation is different from paying it: Fund and Deploy remain available at zero Reputation if you meet their other requirements. A rule that requires you to pay Reputation needs the full amount.

## Set up

Choose an identity card and a colour-and-symbol set of pieces. Your colour does not determine your identity. Place a cube on each of your five player-mat tracks at the starting amounts on your identity card. Its one special ability applies from the start.

Take two Orgs, normal side up, and leave them off the board. Keep your other two in reserve. Put the Era tile in the centre and arrange the eighteen action tiles using their printed positions. Each action type has three tiles; the inner ring runs Fund, Research, Build, Organize, Deploy, Influence clockwise from the top. The centre is not a playable space.

Shuffle the forty Training cards. Separate the Headlines into their four Era piles and shuffle each pile. Separate the objectives into their four Era piles, shuffle each, and reveal one from each pile. Keep these four objectives visible for the whole game; they score only at the end. All holdings and these objectives are public; unrevealed cards stay hidden.

Choose the first player randomly and give them the Initiative marker, which simply marks who starts the next round of turns. Set the Era/cycle marker to the first Era and first cycle.

## How the game moves forward

There are four Eras. In each Era, everyone takes three turns.

Before each round of turns, reveal one Headline from the current Era's pile and finish its instructions. Players then take one turn each, starting with the Initiative marker and going clockwise. Pass that marker one player clockwise after everyone has acted.

After the third round of turns, collect Production and check Reputation as explained below. Then start the next Era. After the fourth Era, finish Production and the Reputation check before scoring.

<!-- headline-selection:start -->
When a Headline targets one player and several players tie, choose the first tied player in the current turn order. An instruction that applies to everyone still applies to everyone. This is separate from objective scoring ties.
<!-- headline-selection:end -->

<!-- map:start -->
## Your turn

Eighteen playable Action hexes surround the central Era hex. Hexes sharing an edge are neighbours. There is no wraparound or occupancy limit.

**1. You may offer one trade.** Offer one named player 1 Runway for 1 Compute, or the reverse. They accept or refuse. Both players must have what they give and room for what they receive. There are no counteroffers or promises. An accepted trade happens all at once and triggers Deal Flow where applicable. A refused offer does not stop the rest of your turn.

**2. Choose one Org.** Keep it where it is, or move it to a space sharing an edge. An Org that has not entered the board may enter any playable space. Do not cross the centre or move across corners. Players may share spaces.

**3. Use that space's action, or skip it.** You may skip even when you could pay. You may also move to a space whose action you cannot afford. Your piece stays there and still earns its end-of-Era resources. Skipping gives no action reward and triggers no action-specific identity ability.

<!-- map:end -->

## Actions now; resources later

Read the middle column when you take an action. Read the last column only at the end of an Era.

| Space     | Action on your turn                                                                                      | End-of-Era reward for each Org there |
| --------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| Fund      | Gain 2 Runway; or gain 4 Runway and lose 1 Reputation.                                                   | 2 Runway                             |
| Research  | Pay 2 Compute and draw Training cards, as explained below.                                               | 1 Compute                            |
| Build     | Pay 2 Runway to equip any one of your unequipped Orgs. Flip that piece.                                  | 2 Compute                            |
| Organize  | Pay 2 Runway to put one reserve Org on this space; or move one other Org to any playable space for free. | 1 Runway                             |
| Deploy    | Meet the next Customer requirement, pay 1 Compute, gain 1 Customer, and lose 1 Reputation.               | 1 Runway                             |
| Influence | Gain 2 Reputation.                                                                                       | 1 Reputation                         |

<!-- construction:start -->
**An equipped Org earns double the last column's reward.** It does not double an action reward. Equipment stays with the piece when it moves. Each Org can be equipped only once.

Build may equip the acting Org or another Org you own. Organize's extra move does not trigger another action. You cannot add a fifth Org.

Deploy needs Capability 2 for your first Customer, then 4, 6, 8, and 10 for the next four. Meet the requirement; do not spend Capability.

Apply the special ability printed on your identity card. For example, Industrial Velocity reduces the equipment price by 1 Runway, and Installed Base gives 1 Runway after the Deploy action, not after a Headline grants a Customer.
<!-- construction:end -->

## Research: stop safely or risk another card

Pay 2 Compute once, then draw a Training card. The seven ordinary categories are Code, Science, Web, Books, Images, Video, and Synthetic.

A category you have not seen during this Research action adds 1 Capability to this attempt's temporary total. After resolving a card, choose **Stop and keep the total** or **Draw again**. The board may call stopping **Bank**. Cards may call the temporary total **provisional Capability** and categories **domains**.

A repeated ordinary category ends the attempt and loses its temporary total, except where your identity ability saves some or all of it. You never lose Capability earned before this attempt. Reputation changes from cards remain, even if the attempt fails.

Three special cards work differently:

| Card             | What to do                                                                                                                                                                                                                 |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Curated Corpus | ${content.gameConfig.trainingDeck.cards.7.rulesText} |
| Benchmark Leak   | Add 2 to the temporary total and lose 1 Reputation immediately. This card is not an ordinary category.                                                                                                                     |
| Human Evaluation | Gain 1 Reputation, keep the temporary total, and stop immediately.                                                                                                                                                         |

Scientific Method lets you pay 1 Runway when a repeat would end the attempt; discard that repeat, keep your temporary total, and stop. Reviewed Research lets you keep 1 from a failed attempt, but never more than its temporary total.

Keep a visible record of categories counted in this attempt. Revealed cards go to the shared discard. If the draw pile empties, shuffle the discard and continue without clearing the category record. Stop after at most forty draws. Kept Capability still obeys its maximum of 12.

## End of each Era

Starting with the Initiative marker, each player collects any Production ability, then the rewards from every placed Org, then 1 Runway per Customer. Apply the maximum whenever you receive a reward. Orgs still off the board earn nothing.

The Shovels gives 1 Runway for each rival who has at least one equipped Org, up to 2 Runway.

After all Production, anyone with Reputation 0 or 1 loses 2 Runway, stopping at zero.

**Example:** An equipped Org on Build earns 4 Compute at Production. It does not equip another Org for free. An Org on Research earns Compute at Production; it does not draw Training cards then.

<!-- mandate-scoring:start -->
## End of the game

After the fourth Era's Production and Reputation check, resolve the optional **AGI bonus** in turn order. You need at least 9 Capability, 4 Reputation, and 3 Compute. Pay 3 Compute and turn your identity card upside down to mark the bonus. Capability and Reputation are requirements, not payments. This earns 4 points; it does not automatically win the game.

Now count your final score once:

**Capability + twice Customers + Reputation + 4 for the AGI bonus + objective points.**

${content.gameConfig.scoreDisplay.instructions} Do not keep a separate running score.

For each visible objective, check its requirement against the final board and tracks. The best qualifying player gets 2 points. Tied qualifying leaders get 1 point each. If nobody qualifies, nobody gets points. Earlier achievements do not lock in an objective.

When an objective asks for control, count Orgs on that space. You control it only if you have more than each opponent. Equipment does not increase this count; a tie means nobody controls it. Control adds no Production bonus.

When an objective counts neighbouring rivals, count each rival once, even if several of their pieces border yours. Sharing a space alone does not count as neighbouring. When an objective asks for nominal Compute production, total what your placed Orgs would earn, including equipment, before applying the Compute maximum. Do not actually collect it or trigger abilities.

Most points wins. Break a tie by Reputation, then Customers, then Compute. If still tied, share the win.

The World Ending describes the shared outcome; it does not change the winner. If anyone recognized AGI, average final Reputation of at least 3 gives The Singularity; below 3 gives The Closed Loop. Without recognized AGI, those outcomes are The Plural Future and Assured Continuity respectively.
<!-- mandate-scoring:end -->

<!-- card-authority:start -->
## Printed component authority

Component records own exact effects; this rulebook owns procedures and inventory. Actions and their lore are printed on hexes. Unique institutional, Headline, objective, Training, and historical lore is preserved. Historical technology lore remains reference content, not extra equipment or an additional subsystem.
<!-- card-authority:end -->
<!-- era-panels:start -->
The central hex displays all four Eras and the current cycle. Each Era brings its own Headlines. All four selected objectives are already visible from setup. Equipment is available from the start; AGI recognition occurs only after Era IV. There are no Venture or upgrade unlocks to remember.
<!-- era-panels:end -->
<!-- player-aids:start -->
Each player mat includes five holding tracks, a final Mandate scale along its lower edge, the six Action summaries, and the turn and scoring reference. No separate player aid is required.
<!-- player-aids:end -->
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
- Twelve objective cards: three per Era, one from each Era revealed at setup.
- One Era/cycle marker and one Initiative marker.

The playing kit has eighty-two cards and 153 items in total. No writing or pencil is required. Unique historical technology lore remains in the existing reference collection; it has no mandatory pieces. Action lore is printed on the eighteen Action hexes and Era lore on the center. No separate Action, Customer, or Facility cards; no Venture, equipment, recognition, or scoring tokens; no separate Governance Board or foldout aids. Deferred Tactics and secret objectives remain excluded.
<!-- inventory:end -->
<!-- components:end -->
