# Mandate 2038 Org Instructions

These instructions apply to the entire Mandate 2038 project.

## Git workflow: direct to main

- Commit on the owning repo's `main` and push to `origin/main`. No feature
  branches, branch-backed worktrees, or PRs unless the user asks for them.
- On another branch, preserve its work and move the task to `main` safely;
  never discard changes to switch. Never force-push `main`.
- Stage only task-related changes; integrate remote updates without
  overwriting unrelated work.
- Report the pushed commit or the concrete blocker. A local commit is not a push.

## Component Intent

Before modifying a file, read the `CATSCAN.md` chain from the repository root
to the target directory. Treat Target, Authority, Invariants, Acceptance, and
Non-goals as implementation constraints; a child may narrow but not contradict
its parent. Boundary changes require the affected charter to change with the
implementation; algorithms remain free inside those constraints.

## Product Intent

Mandate 2038 is a 2–5 player medium-weight strategy board game about
institutions racing to build, deploy, regulate, and plausibly declare AGI.
It combines engine building, push-your-luck research, asymmetric
institutions, negotiation, and public Reputation.

Ground the setting in concrete situations, with wonder, opportunity,
absurdity, and danger. Humor comes from recognizable behavior and incentives,
not allegations about real people. Do not force every scene into the same
dystopian conclusion.

## Canonical Boundaries

- `components/` owns mechanical records (mechanics, IDs, rule wording,
  author-only `$scenario` references); creative prose resolves through explicit
  `loreRef` records in `world.md`. Era panels own names, rules, unlocks,
  epigraph references, and structured `$era` notes; Era overviews own extended
  setting prose.
- `rules.md` owns Game procedures, map instructions, component states, and
  supported inventory prose, all included in the complete player rulebook. Named
  excerpts also generate internal review references (not required player
  documents).
- `world.md` is the internal author bible and sole authority for lore,
  editorial method, concept placement, research provenance, tone, and
  writing-layer contracts; `dist/contracts/era-situation-ledger.json` is its
  machine-enforced traceability and deployment projection. Create no parallel
  lore scratchpad or thematic authority. The
  bible is never a player document: a layout selects approved setting and Era
  passages and compiled ending fields for the optional companion at
  `/docs/world-and-institutions.html`, which the physical kit does not require.
  Internal means audience, not access control.
- One ruleset, from the 2026-10-10 shared-hex selection: eighteen playable
  Action hexes around one Era hex, producing Orgs (Build equips one by flipping
  its token), numeric Customers, Mandate derived from visible state, forty
  Training cards (ten designs, four copies each, shared draw/discard
  lifecycle), and the twenty-four current Headlines. Orgs act in Initiative
  order; Actions may repeat. Retired, never selectable: the six-area board;
  separate Facilities, upgrades, Customer cards, Action cards, and Ventures;
  simultaneous selection; Power, Trust milestones, and per-Era scoring (the
  2026-10-09 prototype); any rules profile, connected Network, Link, Power
  market, Realignment, or Volatility module. Simulation parameter research
  must not reintroduce retired modes through unchecked options.
- `ui.json` owns browser labels and tutorial wording; `content/runtime/`
  simulation and strategy copy; `content/data/` shared variables;
  `components/game.json` board and supply records. `content/templates/` holds
  only reference layouts (headings, field labels, owner references), never
  independent procedural prose or numeric overrides.
- `physical/` owns component form, dimensions, and state encoding. The box
  inventory is in `dist/docs/core-rules.md` (review extract:
  `dist/review/docs/component-inventory.md`); generated kit output stays in
  `dist/physical-kit/`, with protocols, receipt schemas, release evidence, and
  source data under each kit's `observer/`.
- `experimental/` owns deferred optional modules, outside baseline play until
  the user explicitly activates them.
- `content/graph.json` declares deployment profiles, authored sources, and
  every generated projection; never hand-edit a declared target. Its audience
  and packaging declarations generate `dist/review/docs/content-provenance.md`
  (content provenance, not a complete code dependency graph).
  `content/README.md` is the editing and build-path map, not a rules source.
- `dist/runtime/` owns compiler-generated runtime JSON, `dist/docs/` the
  complete player rulebook, `dist/review/docs/` supplementary Markdown, and
  `dist/physical-kit/` frozen kit output; `dist/site/docs/` and
  `dist/site/review/` render those audiences separately.
- `versions/current-release.json` is the mutable release declaration;
  `versions/<version>/` is immutable historical release evidence, never
  rewritten to make current sources pass.
- In `docs/`: `design-decisions.md` records rationale, exclusions, open
  evidence questions, and implementation gaps without duplicating rules text;
  `playtesting-and-evidence.md` owns physical and simulated evidence identity,
  test protocol, comparison classes, and change control;
  `manufacturing-and-publishing-study.md` is dated planning research, not
  quotes, legal advice, or authorization to manufacture;
  `simulation-and-player-strategies.md` documents the executable simulation
  surface and must name any gap from the canonical rulebook;
  `balance-and-exploitability.md` owns the human-readable balance,
  counter-strategy, and promotion contract, with machine authority
  `lab/contracts/balance-contract.json`.
- Scenario bindings are generated from component records, never maintained
  separately. Each shared scenario has one Markdown definition and disposition
  in the marked canon section of `world.md`, linked by `$scenario.ref`. The
  compiler strips `$scenario` and `$era` from all playable outputs.
- The user-selected simplification (2026-10-12 movement and setup-objective
  candidate): after optional trading, choose one Org to stay or move one edge,
  then perform or deliberately skip its destination Action even when
  affordable. Movement is independent of Action affordability; a skip applies
  no Action costs, rewards, or Action-specific ability. Off-map entry and
  Organize’s second-Org reassignment keep their exceptions. Two-sided Orgs
  retain equipment, presence, and ordinary Production. Turns are sequential,
  with five holdings and derived final Mandate. All four objectives are
  revealed at setup, one per Era packet before the first Headline, stay
  visible, and score once from final state without Era-by-Era replacement. No
  control-income bonus; Research stays two Compute; prices, yields, faction
  abilities, lore, Initiative, eighty-two cards, and 153 components are
  unchanged. Preserve the six Core Actions, push-your-luck Training, four Eras,
  and the separate World Ending. More Orgs increase presence and production,
  not turns. This candidate needs fresh balance and human-play evidence; no
  publication is authorized. Full dated text: `CATSCAN.md`.
- `web/` owns the browser implementation; `tests/` contract, determinism, and
  probability checks; `evidence/playtests/` observed sessions and receipts.
  Never present a simulated result as a human playtest.

When implementation needs an interpretation the canonical rules do not
resolve, record it as provisional in `docs/design-decisions.md`; do not
silently rewrite the baseline.

## Fictional-Identity Boundary

Dovetalis Labs, Loopfold AI, Mirevanta Works, Kestralyn, Orisonix, and
Corthaven are the canonical fictional player institutions, with fictional
CEOs; never replace them with real people, recognizable caricatures, or real
institutional aliases. Historically inspired events target board state, never
presenting accusations about a real person or company as fact. No implied
endorsement, company logos, copied trade dress, or generated photorealistic
likenesses. Public retail release requires an explicit publishing decision and
legal review.

## Development

- Browser-native modern JavaScript; no framework unless the user chooses one.
- Keep the simulation deterministic under an explicit seed.
- Keep game content in the semantic graph, not UI code; generate JSON
  projections for runtime consumers.
- Log state transitions so a play session can be reconstructed.
- Prefer accessible HTML controls and SVG/CSS geometry over image-only UI.
- Do not add final art before rules and component counts survive blind tests.

## Validation

Reference commands, not per-edit gates: `npm test` (prefer one
`node --test tests/<name>.test.mjs`), `npm run check` (after editing authored
content or projections), `git diff --check`. Browser claims require a browser
check; probability studies require the simulation command and a saved dated
result under `evidence/studies/`.

## Simulation-Driven Change Control

A change motivated by simulated play includes, in the same Git history:

1. The raw report in the local `evidence/studies/simulation/` archive.
2. A tracked dated study receipt: seed, run count, player count, profiles,
   backends, rules variant, report hash, aggregate results, validity limits,
   and the hypothesis tested.
3. Every resulting delta and affected surface, auditing at least the canonical
   rulebook, machine-readable data, simulator, browser prototype,
   reference/player aids, tests, and playtest documentation.
4. An explicit “no change” for an audited surface needing no delta; do not
   edit the rulebook merely to make the checklist look complete.
5. The checks covering the changed surfaces, then an intentional commit naming
   the study or receipt.

Simulation evidence may motivate a candidate rule variant; it becomes
canonical only when the user selects it and every affected authority is
updated together.

Four players is the authoritative balance configuration. Three and five
players are suggested, fully supported configurations; every promoted rules
candidate must preserve their integrity, strategic diversity, faction
viability, negotiation, and completion quality. Two-player games are playable
but exploratory, with non-promotional reports until their own evidence
contract is approved. Six-player games are not playable; keep only their
historical evidence.

No tournament average, strategy-evolution champion, rule-search
recommendation, thin-cell maximum, or LLM anecdote alone may be called
balanced or promoted. Promotion requires the unified `npm run simulate:audit`
frame with registered coverage, partial pooling, multiplicity-safe sequential
intervals, the bounded adversarial diagnostic, a clean committed source, a
tracked receipt, a one-lever common-seed comparison for any proposed rule
delta, and explicit user approval.

## Git And Publication

- This game has no publication target independent of Gamma and is not
  publishable through `rdpush` until it has an explicit remote and is in the
  canonical Deco workspace registry.
- Do not invent a remote, deployment target, crowdfunding status, quote, or
  manufacturing commitment.
