# M3T4 2038 Agent Instructions

These instructions apply to the entire `frontier-2038` project.

## Product Intent

M3T4 2038 is a 3–5 player medium-weight strategy board game about
institutions racing to build, deploy, regulate, and plausibly declare AGI.
It combines spatial engine building, push-your-luck research, asymmetric
institutions, negotiation, and shared public scrutiny.

The tone is neutral institutional retro-futurism with slight dystopian
pressure. The world treats escalating events solemnly. Humor comes from
systems and incentives, not jokes or allegations about real people.

## Canonical Boundaries

- `docs/core-rules.md` preserves the user-selected rules baseline.
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
- `content/` owns the semantic game graph and every authored player-facing
  string. `generated/`, `docs/core-rules.md`, and prototype HTML targets declared in
  `content/graph.json` are generated projections and must not be hand-edited.
- `generated/` owns generated machine-readable prototype content.
- `web/` owns the browser implementation.
- `tests/` owns contract, determinism, and probability checks.
- `evidence/playtests/` owns observed sessions and receipts. Never present a simulated
  result as a human playtest.

When implementation needs an interpretation that the canonical rules do not
resolve, record it as provisional in `docs/design-decisions.md`. Do not silently
rewrite the baseline.

## Public-Figure Boundary

Sam Altman, Mark Zuckerberg, Demis Hassabis, Elon Musk, Dario Amodei, and
Jensen Huang are the canonical real-name satirical player identities.
Do not replace them with institutional aliases.

Treat every portrayal as fictional, transformative satire based on public
institutional roles. Historically inspired events must target board state, not
present accusations about a named person or company as fact. Do not imply
endorsement or introduce company logos, copied trade dress, or generated
photorealistic likenesses. Public retail release still requires an explicit
publishing decision and appropriate legal review.

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
five-player games are fully supported configurations, not incidental variants:
every promoted rules candidate must preserve their integrity, strategic
diversity, faction viability, negotiation, and completion quality. Two- and
six-player reports remain historical evidence only.

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
