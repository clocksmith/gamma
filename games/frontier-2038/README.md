# M3T4 2038

A 3–5 player strategy game about building, deploying, regulating, and
plausibly declaring AGI.

The game is designed and balanced first at four players. Three- and
five-player games are fully supported configurations with their own evidence
gates; they are not shortened or extended afterthoughts.

The standard game lasts four rounds with three simultaneous action selections
per player per round. Players build networks across a thirteen-tile hex
economy, push risky Training Runs, negotiate shared infrastructure, manage
public scrutiny, and secretly vote on one late-game spatial Realignment
without direct combat or elimination.

## Status

This repository is a **prototype**, not a manufactured or published product.

- The supplied rules baseline is preserved in
  [`docs/core-rules.md`](docs/core-rules.md).
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
- Machine-readable content lives in [`generated/`](generated/).
- The canonical semantic content graph lives in [`content/`](content/README.md);
  it generates the rulebook, game data, prototype HTML, UI copy, and simulation
  descriptions.
- The complete first-pass thematic inventory and writing contract live in
  [`docs/thematic-content-bible.md`](docs/thematic-content-bible.md) and
  [`generated/content-manifest.json`](generated/content-manifest.json).
- Player personas, CLI-backed decision policies, Monte Carlo execution, and
  replay are documented in
  [`docs/simulation-and-player-strategies.md`](docs/simulation-and-player-strategies.md).
- Balance, counter-strategy, exploitability, and promotion gates are defined in
  [`docs/balance-and-exploitability.md`](docs/balance-and-exploitability.md).

The lean physical rulebook is under controlled review at `0.5.0-rc.28-test`.
Executable game `0.8.27` implements that candidate under
`three-to-five-grid-ready-v1`, including persistent Grid-Ready markers, immediate
Production power trades, and the reduced two-source energy contract. Synchronization
means the browser and simulator execute the selected contract; it does not
claim physical teachability or numerical balance.

## Folder Map

- [`physical/`](physical/README.md) is the authored physical game, with excluded optional modules under `physical/optional/`.
- [`content/`](content/README.md) is shared authored runtime copy, the semantic graph, and numeric provenance.
- [`generated/`](generated/README.md) is compiler-owned runtime projection data.
- [`web/`](web/README.md) is the browser game and Lab interface.
- [`lab/`](lab/README.md) is the deterministic simulator and experiment system.
- [`tasks/`](tasks/README.md) is the command implementation surface.
- [`build/`](build/README.md) is regenerated rendered output.
- [`evidence/`](evidence/README.md) separates studies from human playtests.
- [`release/`](release/README.md) declares the current mutable release; [`versions/`](versions/README.md) preserves immutable snapshots.

## Launch

```bash
npm run dev
```

That single command rebuilds every generated content artifact and then starts
the canonical server:

- `http://localhost:8038/` — play the synchronized `0.8.27` game and export its
  replay.
- `http://localhost:8038/lab` — run `0.8.27` tournaments, strategy evolution,
  and rule-balance searches.
- `http://localhost:8038/docs` — read the generated, cross-linked project docs.
- `http://localhost:8038/gallery` — review all player-facing component text and
  art-direction placeholders.

`npm start` intentionally remains the raw `node tasks/serve.mjs` contract used
by the release gate. On a clean checkout, use `npm run dev`; if generated views
are already current, `npm start` serves them without rebuilding.

The deployed review interface at
`https://gamma-web-game.web.app/m3t4-2038/` plays weighted and greedy opponents
entirely in the browser with no Node server. The local server is an optional
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

## Optional CLI automation

Claude and Codex decision scripts accept the shared decision packet:

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

`npm run check` is the release gate. It verifies the executable `0.8.27`
bundle, its synchronized `0.5.0-rc.28-test` physical-rules candidate, both
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

The game uses these real-name satirical player identities:

- Sam Altman
- Mark Zuckerberg
- Demis Hassabis
- Elon Musk
- Dario Amodei
- Jensen Huang

Their abilities are fictional, satirical exaggerations of public institutional
roles and do not imply endorsement.
Commercial publication should receive appropriate legal review.

The selected tone is solemn institutional absurdity: each Era becomes more
extreme, while every institution describes the impossible as a responsible
quarterly initiative.
