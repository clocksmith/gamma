import { access, readFile, readdir } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "..");
const required = [
  "AGENTS.md",
  "README.md",
  "docs/core-rules.md",
  "docs/design-decisions.md",
  "docs/manufacturing-and-publishing-study.md",
  "docs/playtesting-and-evidence.md",
  "docs/simulation-and-player-strategies.md",
  "docs/balance-and-exploitability.md",
  "content/README.md",
  "content/graph.json",
  "content/variables.json",
  "content/editions/named.json",
  "content/editions/institutional.json",
  "content/provenance/numbers.json",
  "content/game/game-config.json",
  "content/game/factions.json",
  "content/game/headlines.json",
  "content/game/ui-copy.json",
  "content/game/simulation-copy.json",
  "content/templates/core-rules.md",
  "content/templates/prototype.html",
  "content/templates/simulation.html",
  "data/game-version.json",
  "data/game-config.json",
  "data/factions.json",
  "data/headlines.json",
  "data/tactics.json",
  "data/wild-actions.json",
  "data/player-strategies.json",
  "data/content-manifest.json",
  "data/mandates.json",
  "data/reference-cards.json",
  "data/reserve-specialists.json",
  "data/secret-objectives.json",
  "data/simulation-copy.json",
  "data/ui-copy.json",
  "data/world-copy.json",
  "docs/thematic-content-bible.md",
  "prototype/index.html",
  "prototype/simulation.html",
  "prototype/simulation-app.js",
  "prototype/simulation.css",
  "prototype/app.js",
  "prototype/styles.css",
  "prototype/src/engine.js",
  "simulation/index.js",
  "simulation/content/simulation-copy.js",
  "simulation/contracts/report-migrations.js",
  "simulation/contracts/balance-contract.json",
  "simulation/contracts/experiment-matrix.json",
  "simulation/contracts/llm-holdout-preregistration.schema.json",
  "simulation/contracts/player-profile.schema.json",
  "simulation/balance/balance-contract.js",
  "simulation/contracts/simulation-report.schema.json",
  "simulation/contracts/playtest-receipt.schema.json",
  "simulation/report-archive.js",
  "simulation/versioning/game-identity.js",
  "simulation/environment/selected-rules-match.js",
  "simulation/rules/declaration-readiness.js",
  "simulation/environment/rules-variant.js",
  "simulation/runner/monte-carlo-runner.js",
  "simulation/runner/optimization-runner.js",
  "simulation/runner/balance-audit-runner.js",
  "simulation/runner/unified-matrix-runner.js",
  "simulation/runner/faction-swap-runner.js",
  "simulation/runner/llm-holdout-runner.js",
  "simulation/statistics/sequential-inference.js",
  "simulation/policies/decision-cache.js",
  "simulation/runtime/run-experiment.js",
  "simulation/runtime/create-interactive-game.js",
  "simulation/cli/optimize.mjs",
  "simulation/cli/balance-audit.mjs",
  "simulation/cli/unified-matrix.mjs",
  "simulation/cli/faction-swap.mjs",
  "simulation/cli/llm-holdout.mjs",
  "tools/create-game-release.mjs",
  "tools/create-playtest-session.mjs",
  "tools/render-docs.mjs",
  "tools/render-gallery.mjs",
  "tools/serve.mjs",
  "scripts/content/compile.mjs",
  "scripts/content/lint-provenance.mjs",
  "versions/current.json",
  "versions/0.1.0/manifest.json",
  "versions/0.1.0/game-bundle.json",
  "versions/0.3.2/manifest.json",
  "versions/0.3.2/game-bundle.json",
  "versions/0.4.0/manifest.json",
  "versions/0.4.0/game-bundle.json",
  "versions/0.4.1/manifest.json",
  "versions/0.4.1/game-bundle.json",
  "versions/0.4.2/manifest.json",
  "versions/0.4.2/game-bundle.json",
  "versions/0.4.3/manifest.json",
  "versions/0.4.3/game-bundle.json",
  "versions/0.5.0/manifest.json",
  "versions/0.5.0/game-bundle.json",
  "versions/0.7.2/manifest.json",
  "versions/0.7.2/game-bundle.json",
  "versions/0.4.0-rc.17-test/manifest.json",
  "versions/0.4.0-rc.17-test/rules-candidate-bundle.json",
  "versions/0.7.4/manifest.json",
  "versions/0.7.4/game-bundle.json",
  "versions/0.4.0-rc.18-test/manifest.json",
  "versions/0.4.0-rc.18-test/rules-candidate-bundle.json",
  "versions/0.8.0/manifest.json",
  "versions/0.8.0/game-bundle.json",
  "versions/0.5.0-rc.1-test/manifest.json",
  "versions/0.5.0-rc.1-test/rules-candidate-bundle.json",
  "versions/0.8.1/manifest.json",
  "versions/0.8.1/game-bundle.json",
  "versions/0.5.0-rc.2-test/manifest.json",
  "versions/0.5.0-rc.2-test/rules-candidate-bundle.json",
  "versions/0.8.2/manifest.json",
  "versions/0.8.2/game-bundle.json",
  "versions/0.5.0-rc.3-test/manifest.json",
  "versions/0.5.0-rc.3-test/rules-candidate-bundle.json",
  "versions/0.8.3/manifest.json",
  "versions/0.8.3/game-bundle.json",
  "versions/0.5.0-rc.4-test/manifest.json",
  "versions/0.5.0-rc.4-test/rules-candidate-bundle.json",
  "versions/0.8.4/manifest.json",
  "versions/0.8.4/game-bundle.json",
  "versions/0.5.0-rc.5-test/manifest.json",
  "versions/0.5.0-rc.5-test/rules-candidate-bundle.json",
  "versions/0.8.5/manifest.json",
  "versions/0.8.5/game-bundle.json",
  "versions/0.5.0-rc.6-test/manifest.json",
  "versions/0.5.0-rc.6-test/rules-candidate-bundle.json",
  "versions/0.8.6/manifest.json",
  "versions/0.8.6/game-bundle.json",
  "versions/0.5.0-rc.7-test/manifest.json",
  "versions/0.5.0-rc.7-test/rules-candidate-bundle.json",
  "versions/0.8.7/manifest.json",
  "versions/0.8.7/game-bundle.json",
  "versions/0.5.0-rc.8-test/manifest.json",
  "versions/0.5.0-rc.8-test/rules-candidate-bundle.json",
  "versions/0.8.8/manifest.json",
  "versions/0.8.8/game-bundle.json",
  "versions/0.5.0-rc.9-test/manifest.json",
  "versions/0.5.0-rc.9-test/rules-candidate-bundle.json",
  "studies/simulation/README.md",
  "studies/simulation/preregistrations/llm-negotiation-holdout.json",
  "studies/simulation/preregistrations/llm-negotiation-holdout-v2.json",
  "studies/simulation/preregistrations/llm-negotiation-holdout-v3-capture.json",
  "studies/simulation/preregistrations/llm-negotiation-holdout-v3-replay.json",
  "studies/simulation/preregistrations/foundry-starting-compute-three.json",
  "studies/simulation/preregistrations/foundry-multiplayer-scaling-probes.json",
  "studies/simulation/preregistrations/foundry-shovels-once-per-round.json",
  "studies/simulation/preregistrations/faction-swap-diagnostic-v1.json",
  "studies/simulation/preregistrations/supported-player-count-baseline-v1.json",
  "studies/simulation/preregistrations/faction-strength-probes-v1.json",
  "studies/simulation/preregistrations/faction-strength-probes-v1-rules.json",
  "studies/simulation/preregistrations/faction-progress-conversion-v1.json",
  "studies/simulation/preregistrations/faction-progress-conversion-v1-rules.json",
  "studies/simulation/preregistrations/faction-public-validation-confirmation-v1.json",
  "studies/simulation/preregistrations/faction-public-validation-confirmation-v1-rules.json",
  "studies/simulation/preregistrations/foundry-supported-count-conversion-v1.json",
  "studies/simulation/preregistrations/foundry-supported-count-conversion-v1-rules.json",
  "studies/simulation/preregistrations/faction-demand-validation-v1.json",
  "studies/simulation/preregistrations/faction-demand-validation-v1-rules.json",
  "studies/simulation/preregistrations/faction-demand-validation-v1-restart.json",
  "studies/simulation/preregistrations/faction-demand-validation-v1-restart-rules.json",
  "studies/simulation/2026-07-27-current-matrix-and-mega-cluster-integrity.md",
  "studies/simulation/2026-07-28-supported-player-count-baseline.md",
  "studies/simulation/2026-07-28-faction-swap-diagnostic.md",
  "studies/simulation/2026-07-28-faction-strength-probes.md",
  "studies/simulation/2026-07-28-faction-progress-conversion-calibration.md",
  "studies/simulation/2026-07-28-faction-public-validation-confirmation.md",
  "studies/simulation/2026-07-28-foundry-supported-count-conversion.md",
  "studies/simulation/2026-07-28-faction-demand-validation.md",
  "studies/simulation/2026-07-27-foundry-scaling-rule-selection.md",
  "studies/simulation/2026-07-27-foundry-shovels-executable-correction.md",
  "studies/simulation/2026-07-26-first-automated-baseline.md"
];

for (const relative of required) await access(resolve(root, relative));

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.map(async (entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  }))).flat();
}

const files = await walk(root);
let jsonCount = 0;
const localSimulationArchive = `${resolve(root, "studies/simulation")}${sep}`;
for (const file of files) {
  if (extname(file) !== ".json") continue;
  if (file.startsWith(localSimulationArchive)) continue;
  JSON.parse(await readFile(file, "utf8"));
  jsonCount += 1;
}

const config = JSON.parse(await readFile(resolve(root, "data/game-config.json"), "utf8"));
const trainingCount = config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0);
if (trainingCount !== 50) throw new Error(`Training deck must contain 50 cards, found ${trainingCount}.`);

const contentManifest = JSON.parse(await readFile(resolve(root, "data/content-manifest.json"), "utf8"));
const missingWriting = contentManifest.surfaces.filter((surface) => (
  surface.status !== "production_layout_missing"
  && surface.status !== "final_art_missing"
  && !surface.file
));
if (missingWriting.length > 0) {
  throw new Error(`Content manifest has unowned writing surfaces: ${missingWriting.map((item) => item.id).join(", ")}.`);
}

const html = await readFile(resolve(root, "prototype/index.html"), "utf8");
for (const id of [
  "board",
  "players",
  "decisions",
  "decision-context",
  "headline-name",
  "log",
  "start-game",
  "export"
]) {
  if (!html.includes(`id="${id}"`)) throw new Error(`Prototype is missing #${id}.`);
}
if (!html.includes('href="/lab"')) {
  throw new Error("Playable prototype must link to the external Simulation Lab route.");
}

const simulationHtml = await readFile(resolve(root, "prototype/simulation.html"), "utf8");
for (const id of [
  "simulation-form",
  "experiment-mode",
  "mode-description",
  "seat-config",
  "results-view",
  "experiment-results",
  "archive-path",
  "evidence-identity",
  "faction-results",
  "profile-results",
  "replay-board"
]) {
  if (!simulationHtml.includes(`id="${id}"`)) {
    throw new Error(`Simulation lab is missing #${id}.`);
  }
}

const baselineReceipt = await readFile(
  resolve(root, "studies/simulation/2026-07-26-first-automated-baseline.md"),
  "utf8"
);
for (const requiredText of [
  "SHA-256",
  "Canonical rulebook",
  "Machine-readable game data",
  "Simulation runtime",
  "Browser Simulation Lab",
  "Tests"
]) {
  if (!baselineReceipt.includes(requiredText)) {
    throw new Error(`Baseline simulation receipt is missing ${requiredText}.`);
  }
}

const packageDocument = JSON.parse(await readFile(resolve(root, "package.json"), "utf8"));
if (packageDocument.scripts?.start !== "node tools/serve.mjs") {
  throw new Error("npm start must remain the canonical raw server launch.");
}
if (
  packageDocument.scripts?.["build:all"] !==
    "npm run content:build && npm run docs:html && npm run gallery:html"
) {
  throw new Error("npm run build:all must regenerate content, docs, and gallery views.");
}
if (packageDocument.scripts?.dev !== "npm run build:all && npm start") {
  throw new Error("npm run dev must remain the one-command build-and-serve launch.");
}

const gameVersion = JSON.parse(
  await readFile(resolve(root, "data/game-version.json"), "utf8")
);
if (packageDocument.version !== gameVersion.gameVersion) {
  throw new Error(
    `Package version ${packageDocument.version} must match game version ${gameVersion.gameVersion}.`
  );
}
if (
  gameVersion.contracts?.reportSchemaVersion !== 6 ||
  gameVersion.contracts?.replaySchemaVersion !== 2 ||
  gameVersion.contracts?.decisionSchemaVersion !== 2
) {
  throw new Error("Current report, replay, and decision contract versions are inconsistent.");
}
const candidate = gameVersion.rulesCandidate;
const candidateStatusValid = candidate?.implementationStatus === "not-synchronized"
  ? candidate.implementedByGameVersion === null
  : candidate?.implementationStatus === "synchronized"
    && candidate.implementedByGameVersion === gameVersion.gameVersion;
if (
  typeof candidate?.version !== "string" ||
  candidate.version === gameVersion.gameVersion ||
  !candidateStatusValid ||
  !candidate?.files?.includes("docs/core-rules.md")
) {
  throw new Error("Physical rules candidate identity is incomplete or conflated with the executable game.");
}
const coreRules = await readFile(resolve(root, "docs/core-rules.md"), "utf8");
if (!coreRules.includes(`**Rules version:** ${gameVersion.rulesCandidate.version}`)) {
  throw new Error("Physical rules candidate version does not match the canonical rulebook.");
}

process.stdout.write(
  `check-project: ${required.length} required files, ${jsonCount} JSON files, executable game ${gameVersion.gameVersion}, physical candidate ${gameVersion.rulesCandidate.version}, report schema 6, unified strategic-unsolvability contract, 50-card Training contract, structurally complete thematic manifest\n`
);
