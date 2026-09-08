# Creative writer's review

[world.md](../world.md) is the internal author bible. Read the setting and four
Eras, institutions and component copy, scenario canon, endings, publishing copy,
and editorial notes. This is an authoring order, not the order of a player book.

Edit prose in the named lore entry. A component uses one `"loreRef"` to select
that entry's labeled player fields, such as `#### Newswire` and `#### Quote`.
An optional `#### Author notes` passage stays out of all player projections.
The lore ID is stable even when a title changes. Keep exact costs, effects, and
ending conditions in component JSON; use [rules.md](../rules.md) for procedures.

Review the generated [World and Institutions](../dist/docs/world-and-institutions.md)
and [Card and Board Reference](../dist/review/docs/card-reference.md) to judge what the
player sees. Neither is an authoring location. Internal describes the source's
audience; it does not mean access restrictions.

`$scenario.ref` links a component to the scenario canon; `$era` records Era
placement. Their usage and surface paths are derived from the component records.
Both are stripped from playable data, as is the resolved `loreRef`.
The [editing map](../content/README.md) gives the exact syntax and commands.
