# Manufacturing And Publishing Study

**Research snapshot:** July 25, 2026
**Status:** advisory recommendation; not game doctrine, a selected product
decision, factory quote, legal opinion, customs determination, campaign
authorization, or manufacturing commitment

## How to read this document

This document records a recommendation for how Mandate 2038 might be
prototyped, quoted, published, and commercially positioned. It does **not**
define the game and does not supersede the selected rules in
[`core-rules.md`](core-rules.md) or the decision statuses in
[`design-decisions.md`](design-decisions.md).

Statements labeled confirmed or resolved below describe inputs that were
already selected in the game design; their presence here does not make this
study their authority. All proposed formats, prices, budgets, suppliers,
publishing paths, legal precautions, and next actions remain recommendations
until the user explicitly selects them. Time-sensitive figures must be
rechecked before use.

Mandate 2038 materially changes the manufacturing estimate from a lightweight
card game. It is currently a medium-box hobby strategy design: 3–5 players,
four Eras, simultaneous action selection, a complete radius-two nineteen-hex
economy, six asymmetric institutions, negotiation, push-your-luck Research, and an
escalating AGI endgame.

Rules `0.8.0-rc.13-test` are ready for a controlled physical prototype and
are implemented by executable game `0.14.12`. That synchronization is
implementation evidence, not a human playtest or balance result. The product
is not ready for a binding factory quote because component layouts, artwork,
materials, packaging, and production files remain unresolved.

## Recommended retail hypothesis

Recommended positioning for testing:

> **Mandate 2038**
> A 3–5 player strategy game about building, deploying, regulating, and
> eventually declaring AGI.
> **75–100 minutes at four players, ages 14+, upper-medium strategy.**

Do not print a duration on the box until blind three-, four-, and five-player
tests support it.

Likely commercial format:

- Approximately 10–11.5-inch square rigid box
- One rigid folding Governance Board with a modular-map frame and writable
  public ledger
- Nineteen thick modular hex tiles
- Six dual-layer faction boards with six captive sliders each
- 134 Default standard cards plus 6 foldout aids; 148 standard cards plus 6
  foldouts with Advanced Play
- Stock wooden pieces and cubes
- Several punchboard sheets
- One opaque Audit bag
- One ordinary six-sided Volatility die
- 24–32-page rulebook
- Planning MSRP: $69–$79

The retail target depends on obtaining real quotes and a landed cost compatible
with the chosen sales channel. The working landed-cost objective is $18–$22
per copy, not a measured result.

## Recommended provisional manufacturer BOM

Use this as a draft for preliminary quote conversations only. It is not a
locked component specification.

| Component | Quote assumption | Status |
| --- | ---: | --- |
| Governance Board | 1 folding board with 19 tile wells, 4 printed Era panels, public tracks, contract bays, and writable ledger | selected physical authority; dimensions unresolved |
| Modular hex tiles | 19, double-sided, 80–90 mm, 2 mm greyboard | selected complete radius-two footprint |
| Faction/player boards | 6 dual-layer boards with 6 captive sliders each | selected physical authority; slider construction unresolved |
| Core Action cards | 36, six per player | confirmed |
| Shared Program cards | 6, one shared copy of each named Program | confirmed |
| Realignment ballot cards | 6 square four-way cards, one per player | Advanced Play only |
| Headline cards | 24: 16 Default plus 8 Advanced | confirmed profile split |
| Tactic cards | 0 baseline; 36-card deferred module | excluded from first quote |
| Training cards | 40 | confirmed test contract |
| Mandate cards | 12 | selected wording; balance provisional |
| Secret objectives | 0 baseline; 18-card deferred module | excluded from first quote |
| Printed Era panels | 4 on the Governance Board plus 1 Current Era marker | replaces four separate Era cards |
| Player aids | 6 four-panel foldouts | replaces twenty-four separate reference cards |
| Printed Power contracts | Emergency and Clean on their Energy tiles; Fusion on its shared Program card | replaces three separate reference cards |
| Total printed card-and-aid pieces | 140 Default or 154 with Advanced | 134 / 148 standard cards plus 6 foldouts; manufacturing overage excluded |
| CEO pieces | 6 | confirmed concept |
| Team pieces | 18 | three per faction |
| Facility pieces | 24 | four per faction |
| Generator pieces | 6 | one per faction; Energy location determines source |
| Link tokens | 12 | Advanced Play only; two per faction |
| Starting-grid identifiers | 6 | integrated into each faction's first Facility |
| Separate Grid-Ready pieces | 0 | no persistent Grid-Ready state exists |
| Faction-board sliders | 36 captive sliders: Runway, Compute, Capability, Customers, Trust, and Research Protection on each board | integrated into boards; no loose track markers |
| Program markers | 12, two per faction | record each player's Era Program allowance on the shared display |
| Mandate markers | 6 | one loose faction-coloured marker per faction for the shared track |
| Scrutiny cubes | 60 player-colored plus 18 Systemic Risk pieces | all Audit pieces must feel identical while concealed |
| AGI Dossier cards | 24 | four Era-labelled Commit / Hedge cards per faction |
| Shared punchboard tokens | 36 retained Power cubes, 2 Temporary Compute tokens, 1 Current Era marker, plus the exact contract pairs and markers in `physical/component-inventory.md` | selected counts; layout unresolved |
| Shared dry-erase marker | 1 fine-tip marker | serves the Governance Board ledger |
| Punchboard sheets | 4–6 | quote placeholder |
| Audit bag | 1 opaque cloth bag | confirmed concept |
| Volatility die | 1 stock d6 | Advanced Play only |
| Rulebook | 24–32 pages | expected |
| Box | rigid two-piece box with cardboard insert | recommendation |

Physical component form, state encoding, and the supported-box inventory are
owned by [`physical/`](../physical/README.md). This study may evaluate the
cost and availability of those choices, but does not select them.

No manufactured spare allowance is selected. Replacement cards, punchboard
overage, spare cubes, and spare wooden pieces remain quote variables until
prototype loss, wear, and blind-play evidence establishes what must be packed.

## Recommended resolution before a real RFQ

### Resolved: Training distribution

The selected 40-card test distribution is:

- Seven domains × four cards = 28
- Four Curated Corpus
- Four Benchmark Leak
- Four Human Evaluation

It remains a balance subject, but its current physical count is exact.

### Resolved: baseline module boundary

Tactics and secret objectives are excluded from the controlled baseline.
Their 36-card and 18-card drafts remain optional future modules and should not
be included in the first prototype quote.

### Resolved: shared Program use

Six named Program cards remain face up on the Governance Board. Each player
has two Program markers. The Era panels allow `0 / 1 / 1 / 2` Program uses;
unused allowance expires at Era end. A player may use each named Program at
most once per game. This removes thirty-six private cards and the captive
Escalation track while preserving public timing and once-per-game identity.

### Resolved: player component maxima

The player-colored maxima and shared component counts are explicit in the
canonical rules. Physical dimensions and material choices remain unresolved.

### Resolved: exact board inventory

The selected nineteen-tile map is a complete radius-two hexagon: one fixed
Frontier, six shuffled inner-ring locations, and twelve shuffled outer-ring
locations. The inner ring contains one each of Research, Cloud, Foundry,
Capital, Talent, and Grid. The outer ring contains two each of Research,
Cloud, Consumer, Media, Government, and Renewable. Every outer tile has the
same geometric role, and all twelve outer positions are occupied.
Advanced Play adds six four-way Realignment ballots for six factions; Default
Game uses none. Its vote occurs only after Era III.

### Resolved: Mandates and references

The baseline contains twelve Era-specific Mandates and four Era panels printed
on the Governance Board. Mandate balance remains provisional. The box contains
six identical four-panel foldout player aids; only final fold and layout remain
unresolved.

### Resolved rules, unresolved production format

Three Power contracts remain in the rules without separate cards: Emergency
Infrastructure is printed on Grid, Clean Infrastructure on Renewable, and
Fusion on its shared Program. Generator pieces and Energy slots create scarcity.
Fusion uses one dedicated shared marker. Shared token quantities are exact in
the rulebook.

One Governance Board ledger replaces six personal score sheets. The thirty-six
Power cubes remain on the map as the latest Production snapshot until the next
Allocate step. One shared marker records only the current Mandate criterion,
Setup Collective Trust, and final public resolution.

Six labelled faction trays, four Default Era packets, and one separately packed
Advanced module are selected setup organization. Their exact insert material
and construction remain quote variables.

The remaining manufacturing decisions are material, dimensions, player-board
tracking, card sizing, Link and Generator format, punchboard organization, and
insert design.

## Planning cost bands

These are directional budgets, not quotes.

| Stage | Manufacturing or inventory | Whole-project planning budget |
| --- | ---: | ---: |
| DIY prototype and testing | $200–$800 | $500–$2,000 |
| 6–10 polished prototypes | $1,000–$2,500 | $2,000–$6,000 |
| 500-copy direct-only edition | $13,000–$17,000 factory | $35,000–$65,000 |
| 1,500-copy commercial edition | $20,000–$29,000 factory | $55,000–$95,000 |
| 3,000-copy commercial edition | $30,000–$45,000 factory | $70,000–$125,000 |

Whole-project planning includes allowances for freight, importation, factory
samples, inspection, graphic design, illustration, rulebook editing, legal
review, review copies, campaign production, advertising, replacements, and
contingency. It excludes postage from a fulfillment warehouse to individual
customers.

For comparison only, the cited PrintNinja snapshot publishes a Catan-style
500-copy example with nineteen hexes, 126 cards, wooden pieces, dice, and
instructions
at $14,385.21, or $28.77 per unit. It also states that a more straightforward
game may cost $8–$15 per unit at quantities of at least 1,500. Those examples
are not quotes for Mandate 2038. Mandate 2038 still has substantially more
cards than that reference, so it must not inherit the reference price. See
[PrintNinja’s Catan-style example](https://printninja.com/custom-board-games/custom-settlers-of-catan/)
and
[board-game manufacturing overview](https://printninja.com/printing-products/board-game-printing/).

## Art and graphic-design exposure

Potential needs include:

- One box cover
- Six faction identities
- Thirteen hex environments
- Twenty-four Headline treatments
- Deferred Tactic treatments only if that module returns
- Training-domain art and icons
- Facility, resource, and audit iconography
- Player boards and information design
- Rulebook diagrams
- Campaign graphics

A modular graphic system may hold the planning range for final art and graphic
design around $10,000–$20,000. Unique illustrations for most cards could move
the range above $30,000–$50,000. These are internal planning estimates, not
vendor bids.

Do not commission final illustration before the card set and component counts
survive blind testing.

## Retail and crowdfunding hypothesis

| Item | Planning target |
| --- | ---: |
| Base-game crowdfunding pledge | $69–$79 |
| Eventual MSRP | $79 |
| Customer shipping | charged separately |
| Campaign goal | $60,000–$75,000 |
| Backers at $75 average | approximately 800–1,000 |

At the research-snapshot date, Kickstarter stated that successfully funded
projects paid a five percent platform fee and roughly three to five percent
payment processing.
Accordingly, a $70,000 campaign would retain roughly $63,000–$64,400 before
taxes, refunds, manufacturing, and fulfillment. Verify the fee schedule at
launch. See
[Kickstarter Support](https://help.kickstarter.com/hc/en-us/articles/115005028634-What-are-the-fees).

A 500-copy run may be suitable for an expensive direct-only edition but is
unlikely to support conventional retail economics. The product hypothesis is
one non-miniature edition rather than a deluxe component ladder.

## Recommended publishing paths

### Prototype phase

Planning allocation: $2,000–$4,000 for:

- One complete physical master
- Six to ten polished prototypes
- A blind-test rulebook
- Setup diagram
- Locked component inventory
- One-page sell sheet
- Short overview video

The Game Crafter is a candidate for small prototype quantities. At the
research-snapshot date, its bulk-pricing documentation said discounts begin at
ten copies and can reach
approximately 35 percent at one hundred copies, depending on the game’s
components. Randomized decks are excluded from bulk pricing. See
[The Game Crafter bulk pricing](https://help.thegamecrafter.com/article/84-bulk-pricing).

### Licensing

Planning cash exposure: approximately $3,000–$8,000 for design, prototypes,
rules, video, and pitch materials. A publisher may rename or retheme the game,
change factions or components, reduce player count, or alter the visual
direction. Those are negotiation possibilities, not predictions.

### Self-publishing

Request matched quotes for 500, 1,500, and 3,000 copies with identical
components and clearly stated EXW, FOB, CIF, DDU, or DDP terms.

- PrintNinja states a typical 500-unit board-game minimum.
- Gameland states a 500-unit minimum for paper-print board games and offers
  several freight terms.
- Panda states a 1,500-unit minimum, or 2,000 with custom plastic.

Sources:

- [PrintNinja](https://printninja.com/printing-products/board-game-printing/)
- [Gameland](https://gamelandcn.com/service/)
- [Panda MOQ](https://pandagm.com/docs/what-is-your-minimum-order-quantity-moq/)

Panda describes quote, design verification, pre-production copy, mass
production, mass-production copy, assembly inspection, and shipping as
separate gates. Its snapshot-date FAQ gave representative—not
guaranteed—ranges of
two to four weeks for design verification, two to three for pre-production,
eight to ten for production, two to three for assembly, and four to eight for
shipping for a comparable game. See
[Panda’s process](https://pandagm.com/our-process/) and
[Panda’s timing FAQ](https://pandagm.com/docs/how-much-time-does-it-take-to-produce-my-game/).

### Panda p20 opportunity

As of this research snapshot, Panda’s p20 program states:

- Submissions close May 2027.
- It is open to eligible designers with no more than two published games.
- Twenty credits range from $2,000 to $20,000.
- Submission requires a sell sheet, a video of at most ten minutes, and a
  blind-tested English rulebook.
- Entries must use original IP and be physically playable.

Eligibility must be confirmed before applying. See
[Panda p20](https://pandagm.com/p20/).

## Fictional-institution publishing recommendation

The current design uses fictional institutions and fictional CEOs. Before a
retail print run or crowdfunding campaign, obtain an explicit legal review of
the complete cards, box, art, and marketing, including the final chosen names.

Do not add recognizable portraits, real company logos, proprietary interfaces,
or trade dress to retail artifacts without a separate explicit decision.

New York Civil Rights Law §51 provides a cause of action where a living
person’s name, portrait, picture, likeness, or voice is used for advertising
or trade without written consent. Other jurisdictions and federal law can add
different publicity, trademark, endorsement, and unfair-competition rules.
Satire and commentary can receive protection, but this project does not treat
“satire” as automatic commercial clearance. See
[New York Civil Rights Law §51](https://www.nysenate.gov/legislation/laws/CVR/51).

Historically inspired Headlines should continue to target current board state,
not accuse their real-world inspiration.

This section is issue spotting, not legal advice. Obtain qualified review
before public sale or marketing.

## Copyright, trademark, and product classification

The U.S. Copyright Office states that game ideas, titles, and methods of play
are not protected by copyright, while sufficiently expressive rule text and
graphic art may be. Contributor agreements must cover the commercial rights
needed for rulebook text, illustration, graphic design, and marketing. See
[U.S. Copyright Office: Games](https://www.copyright.gov/register/tx-games.html).

Before announcing a settled title:

1. Conduct a professional trademark clearance search.
2. Secure relevant domains and social handles.
3. Consider an intent-to-use filing after the name is selected.

At the research-snapshot date, the USPTO listed a base electronic filing fee
of $350 per class when the application met the base requirements, plus
possible additional and intent-to-use fees. Verify current fees before filing.
See
[USPTO trademark fee information](https://www.uspto.gov/trademarks/trademark-fee-information).

The design should be assessed for a 14+ general-use product, but an age label
alone does not determine U.S. product classification. The manufacturer or
importer should document the intended audience and applicable testing. See
[CPSC children’s-product guidance](https://www.cpsc.gov/FAQ/Childrens-Products).

## Tariff and import boundary

Do not use a permanent flat tariff assumption.

The cited CBP ruling classifies a boxed board game under HTSUS 9504.90.6000
with a free base general duty, but additional Chapter 99 duties, fees, and
origin-specific measures can apply. See
[CBP CROSS ruling N353003](https://rulings.cbp.gov/ruling/N353003).

The February 2026 presidential proclamation imposed a temporary ten-percent
Section 122 surcharge effective February 24, 2026 through 12:01 a.m. EDT on
July 24, 2026 unless earlier modified or extended by Congress. Because this
study is dated July 25, its expiration language should not be converted into a
current zero-tariff claim. Later measures or entry-specific treatment may
apply. See the
[White House proclamation](https://www.whitehouse.gov/presidential-actions/2026/02/imposing-a-temporary-import-surcharge-to-address-fundamental-international-payments-problems/).

For every serious quote:

- Request an FOB quote.
- Request a fully itemized DDP quote.
- Identify country of origin.
- Have a customs broker verify classification, Chapter 99 duties, processing
  fees, harbor fees, and entry-date treatment before production authorization.

## Consolidated recommendation

Do not manufacture inventory yet.

First:

1. Run the controlled four-player `0.8.0-rc.13-test` physical test.
2. Rebuild player aids and prototype components from the frozen rulebook.
3. Decide the physical format of Generators, Links, tracks, and shared tokens.
4. Test the twelve Mandates while keeping deferred modules out.
5. Produce six to ten blind-testable prototypes after the first corrections
   are selected.
6. Validate three- and five-player quality as explicit supported formats rather
   than extrapolating from the four-player balance target.
7. Lock dimensions, materials, card count, and packaging.
8. Build one manufacturer RFQ with identical columns for 500, 1,500, and
   3,000 copies.

Then compare licensing with self-publishing using actual quotes, legal review,
and measured demand.
