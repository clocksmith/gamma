# Supported box component inventory

This is the human-readable physical requirement for the supported game. It
separates components required by Default Game from the additive Advanced Play
profile. Numeric limits are governed by `content/data/game-config.json`.

This inventory records the selected state encoding rather than adding separate
markers for state already carried by a component or faction-board track.

## Default Game — one faction set per player

- 1 faction board
- 1 CEO
- 3 Teams
- 4 double-sided Facilities, each showing normal or Grid-Ready
- 1 Generator; its Energy district determines clean or emergency Power
- 1 integrated starting-grid identifier on the first Facility
- 10 Scrutiny cubes, tactually identical to Systemic Risk while concealed
- 1 Customer-track marker per faction board, showing zero through five
- 1 Escalation-track marker per faction board, showing zero to two currently
  available
- 6 Core Action cards
- 7 Escalation cards
- 1 Declare AGI card with an undeclared / declared reverse
- Track or token state for Runway, Compute, Capability, Trust, and Safety
- 1 Mandate marker for the shared Mandate track

The integrated prototype therefore needs no separate Grid-Ready markers,
Power Source selectors, Influence cubes, Customer counters, Escalation-
availability counters, or AGI Declaration markers. Generic track cubes remain
a separate supply because they serve other player-board tracks.

## Default Game — shared components

- 13 district tiles: Frontier, six operational, and six public
- 4 Era cards
- 4 player-reference designs; final production copy count remains open
- 16 Default-eligible Headline cards; reveal 12 per game
- 12 Mandate cards; use 4 per game
- 50 Training cards
- 3 Power Source reference cards: 2 ordinary sources and Fusion
- 6 matched Joint Venture pairs
- 6 matched Mega-Cluster pairs
- 1 Fusion Demonstrator marker
- 18 Systemic Risk pieces, tactually identical to Scrutiny while concealed
- 1 opaque Audit bag
- 1 Initiative marker
- Shared or player-board state for Runway, Compute, Safety, temporary Power
  allocation, and the Mandate track

## Advanced Play addendum

Advanced Play uses every Default component plus:

- 8 additional Headline cards, producing six Headlines in each Era deck
- 2 Link tokens per faction; 12 in a complete six-faction box
- 1 Network-capacity marker per faction; 6 in a complete box, with the capacity
  track printed on its faction board
- 3 Realignment ballot cards per player; 18 in a complete box
- 1 ordinary six-sided Volatility die

These components remain in the box during Default Game setup. No Default
component is removed when playing Advanced Play.

## Excluded deferred content

The supported box does not currently require:

- Tactics
- Secret Objectives
- Specialists and Patrons

## Unresolved packing quantities and forms

The rules specify caps but have not selected exact stock quantities for generic
Runway, Compute, Safety, temporary Power-allocation, or generic track-marker
supplies. Player-reference production copies are also unresolved. The selected
Facility, Generator, Customer, Escalation, starting-grid, and AGI embodiments
are recorded in `component-spec.md`. Generic track-marker stock remains
unresolved.

These are production blockers, not permission to improvise a retail bill of
materials. Select exact quantities and embodiments here before placing an RFQ;
change `content/data/game-config.json` first whenever the decision changes a
mechanical limit or legal state.
