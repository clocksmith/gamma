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
- Physical and automated evidence share one protocol in
  [`docs/playtesting-and-evidence.md`](docs/playtesting-and-evidence.md).
- Manufacturing, publishing, legal, and cost research is a dated advisory
  recommendation—not game doctrine or a product commitment—in
  [`docs/manufacturing-and-publishing-study.md`](docs/manufacturing-and-publishing-study.md).
- The browser prototype lives in [`prototype/`](prototype/).
- Machine-readable content lives in [`data/`](data/).
- The canonical semantic content graph lives in [`content/`](content/README.md);
  it generates the rulebook, game data, prototype HTML, UI copy, and simulation
  descriptions.
- The complete first-pass thematic inventory and writing contract live in
  [`docs/thematic-content-bible.md`](docs/thematic-content-bible.md) and
  [`data/content-manifest.json`](data/content-manifest.json).
- Player personas, CLI-backed decision policies, Monte Carlo execution, and
  replay are documented in
  [`docs/simulation-and-player-strategies.md`](docs/simulation-and-player-strategies.md).
- Balance, counter-strategy, exploitability, and promotion gates are defined in
  [`docs/balance-and-exploitability.md`](docs/balance-and-exploitability.md).

The lean physical rulebook is under controlled review at `0.5.0-rc.21-test`.
Executable game `0.8.20` implements that candidate under
`three-to-five-grid-ready-v1`, including persistent Grid-Ready markers, immediate
Production power trades, and the reduced two-source energy contract. Synchronization
means the browser and simulator execute the selected contract; it does not
claim physical teachability or numerical balance.

## Launch

```bash
npm run dev
```

That single command rebuilds every generated content artifact and then starts
the canonical server:

- `http://localhost:8038/` — play the synchronized `0.8.20` game and export its
  replay.
- `http://localhost:8038/lab` — run `0.8.20` tournaments, strategy evolution,
  and rule-balance searches.
- `http://localhost:8038/docs` — read the generated, cross-linked project docs.
- `http://localhost:8038/gallery` — review all player-facing component text and
  art-direction placeholders.

`npm start` intentionally remains the raw `node tools/serve.mjs` contract used
by the release gate. On a clean checkout, use `npm run dev`; if generated views
are already current, `npm start` serves them without rebuilding.

Use the Simulation Lab’s **Experiment** control to run:

- Tournament + replays
- Strategy evolution
- Rule-balance search
- Unified seven-axis evidence matrix
- Preregistered LLM negotiation holdout

Every completed job is automatically archived under
`studies/simulation/`. The browser’s **Download another copy** button is
optional and still follows the browser’s configured download location.

The browser owns normal operation. The equivalent npm simulation commands
remain available only for automation, CI, and saved batch studies.

```bash
npm run simulate:audit -- --maximum-matches 480 --initial-runs 2 --batch-size 2
npm run simulate:faction-swap -- --comparisons studies/simulation/preregistrations/faction-swap-diagnostic-v1.json
```

## Optional CLI automation

Claude and Codex decision scripts accept the shared decision packet:

```bash
npm run strategy:claude -- --input simulation/fixtures/decision-packet.example.json
npm run strategy:codex -- --input simulation/fixtures/decision-packet.example.json
```

These commands can consume metered provider usage. Monte Carlo requires
explicit `--allow-llm` before using either CLI backend.

## Validation

```bash
npm test
node scripts/content/compile.mjs --check
node tools/check-project.mjs
```

`npm run check` is the release gate. It verifies the executable `0.8.20`
bundle, its synchronized `0.5.0-rc.21-test` physical-rules candidate, both
identity vocabularies, numeric provenance, and generated content.

Create and verify the attributed artifacts with:

```bash
npm run game:release
npm run game:release:verify
```

## Theme boundary

The canonical player identities in the named parody edition are:

- Sam Altman
- Mark Zuckerberg
- Demis Hassabis
- Elon Musk
- Dario Amodei
- Jensen Huang

Their abilities are fictional, satirical exaggerations of public institutional
roles and do not imply endorsement. The institutional-alias vocabulary is a
separate generated projection over the identical mechanical graph; it is not
the canonical prototype and cannot change balance evidence.
Commercial publication should receive appropriate legal review.

The selected tone is solemn institutional absurdity: each Era becomes more
extreme, while every institution describes the impossible as a responsible
quarterly initiative.
