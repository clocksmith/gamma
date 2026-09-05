# Deferred Modules

These modules are not part of the game or its physical component
counts. Each component keeps its mechanics, stable ID, and prose together in
`components/`.

- `components/tactics.json`: an optional 36-card modifier deck, deferred to keep the
  baseline focused on its central action engine.
- `components/secret-objectives.json`: an optional private-objective deck, deferred to
  keep baseline scoring public and its balance and duration evidence focused.
- `components/reserve-specialists.json`: twelve writing and illustration concepts only;
  no Specialist or Patron rules system has been designed or tested.

`tactics-rules.md` is the generated-source rule document for the Tactics
module; it remains excluded from game.

[`single-generator-default.md`](single-generator-default.md) preserves the
historical pre-promotion candidate and its paired comparison configuration.
Current play takes the promoted rule directly from canonical game data.

Do not include these modules in game component counts, rules, balance
studies, or physical playtests. A future variant must explicitly enable and
test each module before it becomes physical-game content.
