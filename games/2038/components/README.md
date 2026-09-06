# Creative writer's review

**The game's most important human review is its lore, prose, and rule clarity.**
A writer needs to judge whether the world is convincing, the institutions have
distinct voices, the events accumulate into a meaningful history, and players
can understand what their choices mean. Automated checks cannot establish those
qualities.

This README is a reading path. [world.md](../world.md) remains the editorial
authority; the linked sources below own their actual text and rules.

## Read in this order

| Order | Source | What to pay attention to |
| --- | --- | --- |
| 1 | [world.md](../world.md) | Start with the four connected chapters in the Player World companion section, then review the voice, thematic progression, and editorial conventions. |
| 2 | [reference-cards.json](reference-cards.json) | Era introductions and the public language on the Governance Board. Does each Era develop the world established by the previous one? This file also contains player aids. |
| 3 | [factions.json](factions.json) | Institutional identities, fictional leaders, and distinct voices. Can a reader understand what each institution values and how it presents itself? |
| 4 | [headlines.json](headlines.json) | Event titles, newswire prose, and quotations. Read the fiction beside the printed effect: does the event make its consequence understandable? |
| 5 | [world.json](world.json) | Ending narratives. Does each outcome feel distinct, and can players connect it to the history their game produced? |
| 6 | [rules.md](../rules.md) | Player comprehension: terminology, explanation order, ambiguity, and repetition. Can a reader understand a procedure without someone filling in missing assumptions? |

[programs.json](programs.json) and [mandates.json](mandates.json) extend the
review to Program and Mandate wording. Consult
[design-decisions.md](../docs/design-decisions.md) when you need the rationale
behind an existing choice.

## Reading the component files

The JSON files keep each component's mechanics and wording together. Distinguish
the text players see from `$scenario` and `$era` notes. Those notes explain
editorial intent and placement; they do not appear in play. A `$scenario.ref`
points to a shared scenario definition rather than creating another one.

Read names, flavor, and exact effects together. When wording suggests a different
mechanic, identify that explicitly so the prose and intended rule can be resolved
together. References such as `${terms.resources.runway}` insert shared wording
during the build.

For the governing writing conventions and review checklist, use
[world.md](../world.md#writing-contract). Keep component notes with their records
and unadopted world ideas in the [existing backlog](../world.md#unadopted-scenarios).

## See the assembled text

After a content build, [World and Institutions](../dist/docs/world-and-institutions.md)
and [Card and Board Reference](../dist/docs/card-reference.md) let you read the
assembled prose without the JSON structure. Make revisions in the owning sources
listed above; these assembled documents are generated.

The [editing and build map](../content/README.md) explains how source changes
reach the rulebooks, references, and browser. Historical copies under `versions/`
preserve earlier releases.
