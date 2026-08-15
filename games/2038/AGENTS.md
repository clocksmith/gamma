# Mandate 2038 Agent Instructions

These instructions apply to the entire Mandate 2038 project.

## Component Intent

Before modifying a file, read the `CATSCAN.md` chain from the repository root
to the target directory. Treat Target, Authority, Invariants, Acceptance, and
Non-goals as implementation constraints. A child may narrow its parent but may
not contradict it. Boundary changes require the affected charter to change
with the implementation; algorithms remain free inside those constraints.

## Product Intent

Mandate 2038 is a 2–6 player medium-weight strategy board game about
institutions racing to build, deploy, regulate, and plausibly declare AGI.
It combines spatial engine building, push-your-luck research, asymmetric
institutions, negotiation, and shared public scrutiny.

The tone is neutral institutional retro-futurism with slight dystopian
pressure. The world treats escalating events solemnly. Humor comes from
systems and incentives, not jokes or allegations about real people.

## Canonical Boundaries

- `content/data/` owns authored mechanics, stable IDs, values, and shared
  terminology.
- `content/copy/` owns authored component copy and the player-readable
  rulebook and World companion sources.
- `content/runtime/` owns authored browser UI, simulation, and strategy copy.
- `physical/` owns the physical component specification, state encoding, and
  human-readable box inventory. Mechanical counts remain in `content/data/`;
  generated physical-kit output remains in `dist/physical-kit/`.
- `experimental/` owns deferred optional modules; its content is never part of
  baseline play unless the user explicitly activates it.
- `content/graph.json` composes the authored sources and declares every
  generated projection. Do not hand-edit any target it declares.
- `dist/runtime/` owns compiler-generated runtime JSON; `dist/docs/` owns the
  generated rulebooks; `dist/site/` owns rendered site output; and
  `dist/physical-kit/` owns frozen kit output.
- `versions/current-release.json` is the mutable release declaration.
  `versions/<version>/` contains immutable historical release evidence and
  must never be rewritten to make current sources pass.
- `docs/design-decisions.md` records current rationale, exclusions, open
  evidence questions, and implementation gaps without duplicating rules text.
- `docs/playtesting-and-evidence.md` owns physical and simulated evidence
  identity, test protocol, comparison classes, and change control.
- `docs/manufacturing-and-publishing-study.md` contains dated planning research,
  not quotes, legal advice, or authorization to manufacture.
- `docs/thematic-content-bible.md` owns tone and writing-layer contracts.
- `docs/simulation-and-player-strategies.md` documents the executable
  simulation surface and must name any gap from the canonical rulebook.
- `docs/balance-and-exploitability.md` owns the human-readable balance,
  counter-strategy, and promotion contract. Its machine authority is
  `lab/contracts/balance-contract.json`.
- `web/` owns the browser implementation.
- `tests/` owns contract, determinism, and probability checks.
- `evidence/playtests/` owns observed sessions and receipts. Never present a simulated
  result as a human playtest.

When implementation needs an interpretation that the canonical rules do not
resolve, record it as provisional in `docs/design-decisions.md`. Do not silently
rewrite the baseline.

## Fictional-Identity Boundary

Dovetalis Labs, Loopfold AI, Mirevanta Works, Kestralyn, Orisonix, and
Corthaven are the canonical fictional player institutions. Their CEOs are
fictional characters. Do not replace them with real people, recognizable
caricatures, or real institutional aliases.

Historically inspired events must target board state, not present accusations
about a real person or company as fact. Do not imply endorsement or introduce
company logos, copied trade dress, or generated photorealistic likenesses.
Public retail release still requires an explicit publishing decision and
appropriate legal review.

## Development

- Use modern browser-native JavaScript with no framework unless the user
  chooses one.
- Keep the simulation deterministic under an explicit seed.
- Keep game content in the semantic graph rather than duplicating it in UI
  code. Generate JSON projections for runtime consumers.
- Log state transitions so a play session can be reconstructed.
- Prefer accessible HTML controls and SVG/CSS geometry over image-only UI.
- Do not add final art before rules and component counts survive blind tests.

## Validation

Run:

```bash
npm test
npm run check
git diff --check
```

Browser claims require a browser check. Probability studies require the
simulation command and a saved dated result under `evidence/studies/`.

## Simulation-Driven Change Control

Any change motivated by simulated play must include all of the following in
the same Git history:

1. Preserve the raw report in the local `evidence/studies/simulation/` archive.
2. Add a tracked dated study receipt recording seed, run count, player count,
   profiles, backends, rules variant, report hash, aggregate results, validity
   limits, and the hypothesis being tested.
3. List every resulting delta and every affected surface. At minimum audit the
   canonical rulebook, machine-readable data, simulator, browser prototype,
   reference/player aids, tests, and playtest documentation.
4. Explicitly record “no change” for an audited surface that does not require a
   delta; do not edit the rulebook merely to make the checklist look complete.
5. Validate implementation and content contracts, then create an intentional
   Git commit that names the study or receipt.

Simulation evidence may motivate a candidate rule variant. It does not become
canonical doctrine until the user selects it and every affected authority is
updated together.

Four players is the authoritative balance configuration. Three- and
five-player games are the suggested fully supported configurations, not incidental variants:
every promoted rules candidate must preserve their integrity, strategic
diversity, faction viability, negotiation, and completion quality. Two- and
six-player games are playable exploratory configurations; their reports are
non-promotional diagnostics until their own evidence contract is approved.

No tournament average, strategy-evolution champion, rule-search recommendation,
thin-cell maximum, or LLM anecdote may be described as balanced or promoted
alone. Run the unified `npm run simulate:audit` frame; require registered
coverage, partial pooling, multiplicity-safe sequential intervals, the bounded
adversarial diagnostic, a clean committed source, tracked receipt, one-lever
common-seed comparison for any proposed rule delta, and explicit user approval.

## Git And Publication

- Work on `main`.
- Preserve unrelated work.
- This project is not publishable through `rdpush` until it has an explicit
  remote and is added to the canonical Deco workspace registry.
- Do not invent a remote, deployment target, crowdfunding status, quote, or
  manufacturing commitment.
