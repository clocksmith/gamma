# ${content.worldCopy.title} — Component Reference

Use this aid during setup and when a named component state appears. Printed Faction,
Action, Escalation, Headline, Era, Mandate, Training, and Power cards own their
exact text; resolve the printed card.

## Deck contracts

### Training deck: 50 cards

- Five copies of each of seven domains: 35
- Three Curated Corpus
- Three Licensed Dataset
- Three Benchmark Leak
- Three Synthetic Loop
- Three Human Evaluation

Discard every revealed card after a run. If the deck empties, resolve the
current card, shuffle the discard, and continue.

### Headline decks

In Default Game, each Era deck contains every card for that Era without an
**Advanced Play** badge. Reveal three each Era. Leave every resolved card face
up in its Era row to form the twelve-card ${terms.systems.futureTimeline}.

### Deferred Tactic deck: 36 cards

Tactics are absent from the baseline game and evidence; see **Optional Tactic
Rules** for their contracts.

## Component limits

Each faction receives:

- One CEO
- Three Teams
- Four double-sided Facilities: normal / Grid-Ready
- One Generator
- One integrated starting-grid identifier on the first Facility
- Ten ${terms.playerTracks.scrutiny} cubes
- One ${terms.playerTracks.customer} track marker
- One Escalation track marker
- Six Core Action cards
- Seven ${terms.systems.escalation} cards
- One Declare ${terms.systems.agi} card with an unclaimed / claimed reverse

Generators do not count against the Facility limit.

Gain, spend, and lose Escalation availability on the faction-board track.

The shared supply contains:

- ${facts.shared.components.jointVenturePairs} numbered matched Joint Venture token pairs
- ${facts.shared.components.megaClusterPairs} numbered matched ${terms.technology.megaCluster} token pairs with a lead-side indicator
- One dedicated ${terms.technology.advancedGeneration} marker
- Eighteen Systemic Risk cubes
- One opaque Audit bag
- One Initiative marker

Unused contract tokens cannot be reserved; create agreements only while a
matched pair is available.

## Defined markers and effects

- **Remove ${terms.playerTracks.scrutiny}:** return the stated number of your cubes from the Audit
  bag to your supply. If fewer are present, remove as many as possible.
- **Grid-Ready face:** flip a Facility after Production if it received its
  complete Facility demand. Flip it back immediately when that Facility is
  relocated by an Action or effect, becomes ineligible for its owner’s Power
  after any change, or during a Production where it receives insufficient
  ${terms.infrastructure.power}.
- **${terms.infrastructure.power} offline recovery:** reassess every Production.
- **${terms.systems.headline} offline recovery:** ends when the ${terms.systems.headline} states, normally next
  Production.
