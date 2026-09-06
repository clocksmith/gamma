# Mandate 2038

**The game's most important human review is its lore, prose, and rule clarity.**
Start with the [creative writer's review guide](components/README.md), which
leads through the world, Eras, factions, Headlines, endings, and play instructions.

A 3–5 player strategy game about building, deploying, regulating, and
plausibly declaring AGI.

The game is designed and balanced first at four players. Three- and
five-player games are fully supported configurations with their own evidence
gates; they are not shortened or extended afterthoughts.

The standard game lasts four rounds with three simultaneous action selections
per player per round. Players build institutions across a complete nineteen-tile
radius-two hex
economy, push risky Training Runs, negotiate shared infrastructure, and manage
public scrutiny without direct combat or elimination. Each Faction has one permanent ability. Headlines finish before selection,
and Build constructs up to one Facility and one project. Each player
has one location-defined Generator, and political control
uses visible Agent and Facility presence rather than Influence cubes.
The jurisdiction stays fixed throughout the game, and Power eligibility is local.

## Status

This repository is a **prototype**, not a manufactured or published product.

- The required **Play Kit** is the generated
  [Core Rules](dist/docs/core-rules.md),
  [Map Reference](dist/docs/map-reference.md),
  [Component Reference](dist/docs/component-reference.md), and
  [Card and Board Reference](dist/docs/card-reference.md). Together, these four
  documents contain the complete game procedure, board, component,
  and card information needed to play.
- The browser’s First Game Guide teaches those rules interactively; it is an
  onboarding aid, not a second rules authority.
- [World and Institutions](dist/docs/world-and-institutions.md) is the
  optional setting companion for tone, Era fiction, and ending narratives.
- The excluded Tactic module retains its complete contract in
  [Optional Tactic Rules](dist/docs/optional-tactics.md).
- Current rationale and implementation boundaries are recorded in
  [`docs/design-decisions.md`](docs/design-decisions.md).
- Defect investigation, containment, regression, and closure rules are in
  [`docs/defect-investigation-and-closure.md`](docs/defect-investigation-and-closure.md).
- Physical and automated evidence share one protocol in
  [`docs/playtesting-and-evidence.md`](docs/playtesting-and-evidence.md).
- Manufacturing, publishing, legal, and cost research is a dated advisory
  recommendation—not game doctrine or a product commitment—in
  [`docs/manufacturing-and-publishing-study.md`](docs/manufacturing-and-publishing-study.md).
- The browser prototype lives in [`web/`](web/).
- Machine-readable content lives in [`dist/runtime/`](dist/runtime/).
- The canonical semantic content graph lives in [`content/`](content/README.md);
  it generates the player documents, game data, prototype HTML, UI copy, and
  simulation descriptions.
- Every declared Markdown projection under `dist/docs/` is rendered into the
  Documentation reader during `npm run docs:html`. Use the
  [editing and build map](content/README.md) to find its owner: `rules.md` for
  procedures, `components/` for exact effects, `world.md` for lore.
  `content/templates/` arranges references to those owners; it does not own
  separate rules. Never author directly in `dist/docs/`.
- The sole lore authority, editorial backlog, research boundary, Era placement,
  and writing contract live in
  [`world.md`](world.md). Its
  machine-enforced scenario, surface, copy, mechanic, and deployment projection
  is [`dist/contracts/era-situation-ledger.json`](dist/contracts/era-situation-ledger.json).
  The generated surface inventory lives in
  [`dist/runtime/content-manifest.json`](dist/runtime/content-manifest.json).
- Player personas, CLI-backed decision policies, Monte Carlo execution, and
  replay are documented in
  [`docs/simulation-and-player-strategies.md`](docs/simulation-and-player-strategies.md).
- Balance, counter-strategy, exploitability, and promotion gates are defined in
  [`docs/balance-and-exploitability.md`](docs/balance-and-exploitability.md).

The separated physical rules candidate is under controlled review at
`0.11.0-rc.1-test`.
Executable game `0.18.0` implements that candidate under
`react-agent-assignments-v1`, including direct Agent assignments,
current local Power connections, Research without universal Protection, one
optional pre-resolution 1-for-1 trade, and scored public AGI recognition.
CEOs remain faction characters; each faction has two
starting Agents and four available in total. Synchronization means
the browser and simulator execute the selected contract; it does not claim
physical teachability, numerical balance, or that the AGI coda is enjoyable.

## Folder Map

- [`world.md`](world.md), [`rules.md`](rules.md), and [`ui.json`](ui.json) own lore, play instructions, and browser wording.
- [`components/`](components/) contains complete component records with wording, mechanics, and scenario notes; deferred modules live under `experimental/components/`.
- [`content/`](content/README.md) contains build declarations, reference templates, shared variables, simulation copy, and numeric provenance.
- [`physical/`](physical/README.md) owns component form and state encoding. The supported box inventory is generated from `rules.md`.
- [`dist/docs/`](dist/docs/) is compiler-owned Markdown projected from declared
  sources; `npm run docs:html` turns every file there into the deployed
  Documentation reader.
- [`dist/runtime/`](dist/runtime/) is compiler-owned runtime projection data.
- [`web/`](web/README.md) is the browser game and Lab interface.
- [`lab/`](lab/README.md) is the deterministic simulator and experiment system.
- [`tasks/`](tasks/README.md) is the command implementation surface.
- [`dist/site/`](dist/site/) is regenerated rendered output.
- [`evidence/`](evidence/README.md) separates studies from human playtests.
- [`versions/current-release.json`](versions/current-release.json) declares the current mutable release; [`versions/`](versions/README.md) preserves immutable snapshots.

## Launch

```bash
npm run dev
```

That single command rebuilds every generated content artifact and then starts
the canonical server:

- `http://localhost:8038/` — play the synchronized `0.18.0` game and export its
  replay.
- `http://localhost:8038/lab` — run `0.18.0` tournaments, strategy evolution,
  and rule-balance searches.
- `http://localhost:8038/docs` — read the generated, cross-linked project docs.
- `http://localhost:8038/gallery` — review all player-facing component text and
  art-direction placeholders.

`npm start` intentionally remains the raw `node tasks/serve.mjs` contract used
by the release gate. On a clean checkout, use `npm run dev`; if generated views
are already current, `npm start` serves them without rebuilding.

The public playtest interface at `https://canvascontext.com/` contains only the
playable game, First Game Guide, required play references, World and
Institutions, baseline gallery, release identity, and feedback route. It plays
weighted and greedy opponents entirely in the browser with no Node server. The
Simulation Lab, internal design and evidence records, manufacturing research,
complete gallery, and deferred modules are excluded. Crawler directives do not
provide access control.

Build the exact Firebase allowlist with `npm run publish:firebase:build`. Build
the complete, explicitly non-deployable local review artifact with
`npm run review:site:build`.

The local server is an optional
bridge for Claude, Codex, hybrid opponents, and server-backed Simulation Lab
jobs. When needed, paste the private token printed by `npm run dev` and approve
Chrome’s local-network prompt. The bridge remains bound to loopback, accepts
only the exact deployed origin, and requires the token on every remote API
request.

Interactive games can combine one human with independently selected weighted,
greedy, Claude CLI, Codex CLI, hybrid-Claude, and hybrid-Codex opponents.
Claude/Codex use requires explicit per-game authorization. Each LLM opponent
has its own maximum of 24 authorized decisions and falls back to its
deterministic persona after exhausting that budget or encountering a CLI
failure.

Use the Simulation Lab’s **Experiment** control to run:

- Tournament + replays
- Strategy evolution
- Rule-balance search
- Unified seven-axis evidence matrix
- Preregistered LLM negotiation holdout

Every completed job is automatically archived under
`evidence/studies/simulation/`. The browser’s **Download another copy** button is
optional and still follows the browser’s configured download location.

The browser owns normal operation. The equivalent npm simulation commands
remain available only for automation, CI, and saved batch studies.

```bash
npm run simulate:audit -- --maximum-matches 480 --initial-runs 2 --batch-size 2
npm run simulate:faction-swap -- --comparisons evidence/studies/simulation/preregistrations/faction-swap-diagnostic-v1.json
```

The separately preregistered `npm run simulate:codex-session` path records a
complete LLM-simulated session from frozen-kit inspection and rules questions
through gameplay and postgame reconstruction. It never counts as a physical or
blind human playtest.

## Optional CLI automation

Claude and Codex decision scripts receive the shared decision packet. Their
provider-facing legal IDs are short deterministic aliases; the caller maps the
selected alias back to the packet's canonical legal decision before state can
change.

```bash
npm run strategy:claude -- --input lab/fixtures/decision-packet.example.json
npm run strategy:codex -- --input lab/fixtures/decision-packet.example.json
```

These commands can consume metered provider usage. Monte Carlo requires
explicit `--allow-llm` before using either CLI backend.

## Validation

```bash
npm test
node tasks/content/compile.mjs --check
node tasks/check-project.mjs
```

`npm run check` is the release gate. It verifies the executable `0.18.0`
bundle, its synchronized `0.11.0-rc.1-test` physical-rules candidate, both
identity vocabularies, numeric provenance, and generated content.

Create and verify the attributed artifacts with:

```bash
npm run game:release
npm run game:release:verify
```

After the release commit is pushed, freeze the exact controlled physical kit:

```bash
npm run physical-kit:freeze
```

The command refuses a dirty or unpushed source and stamps the rulebook,
baseline component masters, session templates, and kit manifest with the exact
rules version, executable reference, and remote source commit.

## Theme boundary

The game uses six fictional AI institutions: Dovetalis Labs, Loopfold AI,
Mirevanta Works, Kestralyn, Orisonix, and Corthaven. Their fictional CEOs and
abilities depict institutional incentives, not real people or companies.
Commercial publication should still receive appropriate legal review.

The selected tone is solemn institutional absurdity: each Era becomes more
extreme, while every institution describes the impossible as a responsible
quarterly initiative.
