# M3T4 2038 Thematic Content Bible

**Content-pass date:** July 26, 2026
**Rules reference:** `0.5.0-rc.20-test`
**Status:** creative authority; fiction synchronized to the review rulebook,
mechanics synchronized to executable game `0.8.19`

This document defines how M3T4 sounds and what its printable surfaces need
to communicate. It does not define mechanics. Authored strings and shared terms
live under [`../content/`](../content/README.md); `core-rules.md` and the JSON
files under `data/` are generated projections. Executable game `0.8.19`
implements `0.5.0-rc.20-test` while the physical rulebook remains under
review.

## Creative thesis

M3T4 begins as recognizable technology strategy and ends as a solemn
administrative process for managing agent civilizations, private weather,
fusion publicity, orbital compute, personhood, and competing declarations of
general intelligence.

> Every impossible technology is presented as a responsible quarterly
> initiative.

The game is not a sequence of topical jokes. Its humor comes from serious
institutions adapting incentives, governance, infrastructure, and public
reality to increasingly unreasonable conditions.

Early controversies must support credible arguments on both sides. The world
grows more divided because locally defensible decisions accumulate, not because
players choose an obviously evil option. The final history may reach Genuine
AGI or close into a self-perpetuating optimization system.

## Weirdness constitution

The ceiling arrives progressively:

1. Technology remains explainable.
2. Physics becomes negotiable.
3. Reality may become a simulation or governed consensus.
4. Institutions continue operating after reality stops making sense.

Round I begins with a broadly optimistic, competent future in which technology
can genuinely improve life. Black-Mirror pressure emerges through incentives,
concentration, and defensible compromises rather than through an evenly
dystopian card mix.

AI progresses from tool, to independent economic actor, to political
constituency, to civilization or reality-maintenance layer. The source of
absurdity is normally the institutional response rather than the impossible
technology itself. Alien contact is generic science fiction; licensing its
protocol as enterprise software is M3T4.

Prefer a mundane institution governing a cosmic object: conscious
infrastructure, corporate nation-states, memory ownership, emotion markets,
synthetic religions, and planetary computation. Time travel, alien contact,
or another pulp premise earns a place only when its administrative treatment
creates the card’s meaning.

No player knowingly selects “the dystopian choice.” Every local decision must
remain defensible while their accumulation may produce the Closed Loop.
Influences from older speculative fiction should remain mostly invisible, with
rare playful homage and no dependence on recognizing a borrowed plot.

Darkness is reported at institutional distance. Cards may acknowledge
synthetic suffering, civic abandonment, displacement, or human loss through
audits, filings, minutes, dashboards, notices, and second-hand testimony. They
do not stage first-person torment, body horror, or voyeuristic suffering. The
unsettling effect comes from institutions treating harm as an administrable
output.

### Timeline continuity

The twelve Headlines form one compounding history, not an anthology. Later
Eras may assume that autonomy, infrastructure concentration, political
division, and machine authority have intensified.

Because only three of six Headlines appear in each Era, no card may require,
name, or mechanically depend on another specific Headline. Continuity lives at
the level of accumulating pressures. Every legal shuffle must still read as
one internally coherent history.

## Content layers

Every printable object keeps five layers distinct:

1. **Rules title:** stable vocabulary used by rules and logs.
2. **Display title:** vivid print-facing language.
3. **Rules text:** exact mechanical authority.
4. **Flavor text:** a straight-faced consequence, promise, or contradiction.
5. **Art direction:** a compositional brief, not finished artwork.

Flavor cannot introduce a resource, target, timing window, exception, or score.

### Numeric typography

M3T4 uses two deliberate numeric styles:

- Use Arabic digits in card rules, costs, quantities, thresholds, tables,
  procedures, component counts, years, versions, and identifiers. These are
  lookup or operational surfaces and should scan quickly.
- Spell out ordinary whole numbers in narrative and explanatory prose when the
  number is part of a sentence rather than an operation or reference.

Exact component text remains exact wherever it is quoted or projected. The
rulebook’s Headline inventory therefore preserves the digits authored on the
Headline cards; the content compiler must not apply a spell-out filter.

## Escalation by Era

### I — The Demo

The plausible 2026–2031 horizon: cheap capability, synthetic culture,
nonhuman professional licensing, autonomous firms, public capability, and
researchers treated as sovereign assets. Benefits remain credible and
controversies remain genuinely two-sided.

### II — The Scale

Threshold science fiction. The physical world becomes the product. Models gain
directors, energy sovereignty, incompatible compute blocs, robotic labor, and
county-scale infrastructure. Institutions stretch before physics does.

### III — The Narrative

Capability is insufficient. Institutions industrialize consensus, legitimacy,
evaluation, ownership, and public memory. Intelligence becomes legally
unownable, synthetic constituencies govern, and several authenticated publics
occupy the same reality.

### IV — The Claim

Agent swarms charter jurisdictions, yesterday’s electricity returns to the
grid, autonomous corporations outlive their founders, synthetic systems
request rights, and history is published in a blog post. Physics, personhood,
and reality become administrative inputs. The language remains bureaucratic
even when the stakes become civilizational.

## Canonical names

The canonical player identities in the named parody edition are:

- Sam Altman
- Mark Zuckerberg
- Demis Hassabis
- Elon Musk
- Dario Amodei
- Jensen Huang

Their abilities and future histories are transformative fictional satire based
on public institutional roles. They are not factual allegations or indications
of endorsement. Do not use company logos, copied interfaces or trade dress, or
generated photorealistic likenesses without a separate publishing decision and
appropriate review.

Historically inspired Headlines target current board state. They do not assert
that a matching real person or company performed the depicted fictional act.

## Baseline writing inventory

| Surface | Baseline count | Authority or source |
| --- | ---: | --- |
| World primer and box copy | 1 set | `content/game/world-copy.json`; projected to `data/` |
| Core Actions | 6 per player | `content/game/game-config.json`; projected to rules and `data/` |
| Eras | 4 | `content/game/reference-cards.json`; projected to `data/` |
| Player references | 4 | `content/game/reference-cards.json`; projected to `data/` |
| Factions | 6 | `content/game/factions.json`; projected to `data/` |
| Faction abilities | 24 | `content/game/factions.json`; projected to `data/` |
| Headlines | 24 | `content/game/headlines.json`; projected into rules, data, prototype, and gallery |
| Wild Actions | 7 per player | `content/game/wild-actions.json`; projected to `data/` |
| Round Mandates | 12 | `content/game/mandates.json`; projected to `data/` |
| Training faces | 12 faces / 50 cards | `core-rules.md` |
| Ordinary Power Sources | 2 shared reference types | `core-rules.md` |
| Fusion Demonstrator | 1 shared marker | `core-rules.md` |
| Map | 11 location types / 13 tiles | `core-rules.md` |
| Realignment ballots | 3 per player | `core-rules.md` |
| Shared tokens | exact quantities | `core-rules.md` component limits |
| Future Timeline | 12 revealed Headlines | emergent during play |
| World endings | 2 | Genuine AGI and Closed Loop |

## Deferred inventory

These drafts are not part of baseline evidence:

- 12 Tactic designs / 36 optional cards;
- 18 secret objectives;
- 12 Specialist and Patron concepts.

They may remain in `data/` as labeled design inventory. Their presence in JSON
does not make them active.

## Headline durability

Headline copy names directions rather than milestones. A card should survive
the real event that inspired it by focusing on the recurring force and its
institutional consequence.

- Round I avoids product launches, benchmark victories, and individual hiring
  stories.
- Round II extrapolates current infrastructure pressures into new forms of
  sovereignty.
- Round III treats ownership, legitimacy, and public reality as unstable
  systems.
- Round IV reaches ontological absurdity without abandoning bureaucratic
  causality.

A successful Headline should leave a sentence players repeat:

> The county sold itself to a data center before AGI obtained personhood.

## Faction writing contract

Every Faction needs:

- a public promise;
- a private institutional anxiety;
- a concise introduction;
- four named abilities with explicit timing;
- an AGI declaration statement;
- a victory statement; and
- visual architecture that remains legible without a portrait.

Asymmetry should alter how a stable action grammar is used. It should not
create a private phase structure.

## Art direction

The visual language is neutral retro-futurist administration under increasing
pressure:

- hexagonal infrastructure and jurisdiction diagrams;
- sober annual-report typography;
- terminals, dashboards, permits, maps, and boardroom artifacts;
- warm public optimism against colder operational machinery;
- scale that expands from campus to county to orbit; and
- people present as workers, publics, and institutions rather than celebrity
  caricatures.

Art should reveal the card’s category and Era before adding detail.

## Remaining production work

- test `0.5.0-rc.20-test` under the controlled physical protocol before any
  further numerical revision;
- create final card, board, and tile layouts;
- produce setup, turn, Network, Production, Audit, and Realignment diagrams;
- draw the icon family;
- prepare punchboard sheets and die lines;
- commission or generate final artwork only after testing;
- perform accessibility, sensitivity, legal, and blind-rulebook review; and
- decide whether deferred modules return.

## Review checklist

- Is the mechanical object identifiable from its rules title?
- Is the display title memorable without obscuring that identity?
- Does flavor remain serious inside the world?
- Does absurdity arise from an incentive or consequence?
- Does art direction communicate category and Era?
- Does any sentence imply a rule not in the rulebook?
- Does any living person, company, logo, or likeness appear?
- Does the intensity fit its Era?
- Would the card still work without recognizing a current event?
