# Deferred Modules

These modules are not part of the Default Game or its physical component
counts. Each module keeps mechanics and stable IDs in `data/` and its
player-facing prose in `copy/`.

- `data/tactics.json` with `copy/tactics.json`: an optional 36-card modifier deck, deferred to keep the
  baseline focused on its central action engine.
- `data/secret-objectives.json` with `copy/secret-objectives.json`: an optional private-objective deck, deferred to
  keep baseline scoring public and its balance and duration evidence focused.
- `data/reserve-specialists.json` with `copy/reserve-specialists.json`: twelve writing and illustration concepts only;
  no Specialist or Patron rules system has been designed or tested.

`tactics-rules.md` is the generated-source rule document for the Tactics
module; it remains excluded from Default Game.

Do not include these modules in Default Game component counts, rules, balance
studies, or physical playtests. A future variant must explicitly enable and
test each module before it becomes physical-game content.
