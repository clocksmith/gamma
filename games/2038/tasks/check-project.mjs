import { access, readFile, readdir } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "..");
const required = [
  "AGENTS.md",
  "README.md",
  "dist/docs/core-rules.md",
  "dist/docs/world-and-institutions.md",
  "dist/docs/optional-tactics.md",
  "docs/design-decisions.md",
  "docs/manufacturing-and-publishing-study.md",
  "docs/playtesting-and-evidence.md",
  "docs/simulation-and-player-strategies.md",
  "docs/balance-and-exploitability.md",
  "content/README.md",
  "content/graph.json",
  "content/data/variables.json",
  "content/provenance/numbers.json",
  "content/data/game-config.json",
  "content/data/factions.json",
  "content/data/headlines.json",
  "content/copy/core-rules.md",
  "content/copy/world-and-institutions.md",
  "experimental/tactics-rules.md",
  "content/runtime/ui-copy.json",
  "content/runtime/simulation-copy.json",
  "web/templates/prototype.html",
  "web/templates/simulation.html",
  "versions/current-release.json",
  "dist/runtime/game-config.json",
  "dist/runtime/factions.json",
  "dist/runtime/headlines.json",
  "dist/runtime/tactics.json",
  "dist/runtime/escalations.json",
  "dist/runtime/player-strategies.json",
  "dist/runtime/content-manifest.json",
  "dist/runtime/mandates.json",
  "dist/runtime/reference-cards.json",
  "dist/runtime/reserve-specialists.json",
  "dist/runtime/secret-objectives.json",
  "dist/runtime/simulation-copy.json",
  "dist/runtime/ui-copy.json",
  "dist/runtime/world-copy.json",
  "docs/thematic-content-bible.md",
  "dist/site/index.html",
  "dist/site/simulation.html",
  "web/simulation-app.js",
  "web/simulation.css",
  "web/app.js",
  "web/api-client.js",
  "web/styles.css",
  "web/src/engine.js",
  "lab/index.js",
  "lab/content/simulation-copy.js",
  "lab/contracts/report-migrations.js",
  "lab/contracts/balance-contract.json",
  "lab/contracts/experiment-matrix.json",
  "lab/contracts/llm-holdout-preregistration.schema.json",
  "lab/contracts/player-profile.schema.json",
  "lab/balance/balance-contract.js",
  "lab/balance/winning-path.js",
  "lab/contracts/simulation-report.schema.json",
  "lab/contracts/playtest-receipt.schema.json",
  "lab/report-archive.js",
  "lab/versioning/game-identity.js",
  "lab/environment/selected-rules-match.js",
  "lab/scenarios/agi-declaration-window.js",
  "lab/environment/rules-variant.js",
  "lab/runner/monte-carlo-runner.js",
  "lab/runner/optimization-runner.js",
  "lab/runner/balance-audit-runner.js",
  "lab/runner/unified-matrix-runner.js",
  "lab/runner/faction-swap-runner.js",
  "lab/runner/llm-holdout-runner.js",
  "lab/statistics/sequential-inference.js",
  "lab/policies/decision-cache.js",
  "lab/runtime/run-experiment.js",
  "lab/runtime/create-interactive-game.js",
  "lab/runtime/create-browser-interactive-game.js",
  "lab/runtime/interactive-game-core.js",
  "lab/cli/optimize.mjs",
  "lab/cli/balance-audit.mjs",
  "lab/cli/unified-matrix.mjs",
  "lab/cli/faction-swap.mjs",
  "lab/cli/llm-holdout.mjs",
  "tasks/create-game-release.mjs",
  "tasks/create-physical-kit.mjs",
  "tasks/create-playtest-session.mjs",
  "tasks/render-docs.mjs",
  "tasks/render-gallery.mjs",
  "tasks/serve.mjs",
  "tasks/content/compile.mjs",
  "tasks/content/lint-provenance.mjs",
  "tasks/release-artifacts.mjs",
  "physical/score-sheet.md",
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
  "versions/0.8.9/manifest.json",
  "versions/0.8.9/game-bundle.json",
  "versions/0.5.0-rc.10-test/manifest.json",
  "versions/0.5.0-rc.10-test/rules-candidate-bundle.json",
  "versions/0.8.10/manifest.json",
  "versions/0.8.10/game-bundle.json",
  "versions/0.5.0-rc.11-test/manifest.json",
  "versions/0.5.0-rc.11-test/rules-candidate-bundle.json",
  "versions/0.8.18/manifest.json",
  "versions/0.8.18/game-bundle.json",
  "versions/0.5.0-rc.19-test/manifest.json",
  "versions/0.5.0-rc.19-test/rules-candidate-bundle.json",
  "versions/0.8.19/manifest.json",
  "versions/0.8.19/game-bundle.json",
  "versions/0.5.0-rc.20-test/manifest.json",
  "versions/0.5.0-rc.20-test/rules-candidate-bundle.json",
  "versions/0.8.22/manifest.json",
  "versions/0.8.22/game-bundle.json",
  "versions/0.5.0-rc.23-test/manifest.json",
  "versions/0.5.0-rc.23-test/rules-candidate-bundle.json",
  "versions/0.8.23/manifest.json",
  "versions/0.8.23/game-bundle.json",
  "versions/0.5.0-rc.24-test/manifest.json",
  "versions/0.5.0-rc.24-test/rules-candidate-bundle.json",
  "versions/0.8.27/manifest.json",
  "versions/0.8.27/game-bundle.json",
  "versions/0.8.28/manifest.json",
  "versions/0.8.28/game-bundle.json",
  "versions/0.5.0-rc.28-test/manifest.json",
  "versions/0.5.0-rc.28-test/rules-candidate-bundle.json",
  "versions/0.8.29/manifest.json",
  "versions/0.8.29/game-bundle.json",
  "versions/0.5.0-rc.29-test/manifest.json",
  "versions/0.5.0-rc.29-test/rules-candidate-bundle.json",
  "versions/0.8.30/manifest.json",
  "versions/0.8.30/game-bundle.json",
  "versions/0.5.0-rc.30-test/manifest.json",
  "versions/0.5.0-rc.30-test/rules-candidate-bundle.json",
  "versions/0.8.31/manifest.json",
  "versions/0.8.31/game-bundle.json",
  "versions/0.5.0-rc.31-test/manifest.json",
  "versions/0.5.0-rc.31-test/rules-candidate-bundle.json",
  "versions/0.8.32/manifest.json",
  "versions/0.8.32/game-bundle.json",
  "versions/0.5.0-rc.32-test/manifest.json",
  "versions/0.5.0-rc.32-test/rules-candidate-bundle.json",
  "versions/0.8.34/manifest.json",
  "versions/0.8.34/game-bundle.json",
  "versions/0.5.0-rc.34-test/manifest.json",
  "versions/0.5.0-rc.34-test/rules-candidate-bundle.json",
  "versions/0.8.35/manifest.json",
  "versions/0.8.35/game-bundle.json",
  "versions/0.5.0-rc.35-test/manifest.json",
  "versions/0.5.0-rc.35-test/rules-candidate-bundle.json",
  "evidence/studies/simulation/README.md",
  "evidence/studies/simulation/preregistrations/llm-negotiation-holdout.json",
  "evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v2.json",
  "evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v3-capture.json",
  "evidence/studies/simulation/preregistrations/llm-negotiation-holdout-v3-replay.json",
  "evidence/studies/simulation/preregistrations/foundry-starting-compute-three.json",
  "evidence/studies/simulation/preregistrations/foundry-multiplayer-scaling-probes.json",
  "evidence/studies/simulation/preregistrations/foundry-shovels-once-per-round.json",
  "evidence/studies/simulation/preregistrations/faction-swap-diagnostic-v1.json",
  "evidence/studies/simulation/preregistrations/supported-player-count-baseline-v1.json",
  "evidence/studies/simulation/preregistrations/faction-strength-probes-v1.json",
  "evidence/studies/simulation/preregistrations/faction-strength-probes-v1-rules.json",
  "evidence/studies/simulation/preregistrations/faction-progress-conversion-v1.json",
  "evidence/studies/simulation/preregistrations/faction-progress-conversion-v1-rules.json",
  "evidence/studies/simulation/preregistrations/faction-public-validation-confirmation-v1.json",
  "evidence/studies/simulation/preregistrations/faction-public-validation-confirmation-v1-rules.json",
  "evidence/studies/simulation/preregistrations/foundry-supported-count-conversion-v1.json",
  "evidence/studies/simulation/preregistrations/foundry-supported-count-conversion-v1-rules.json",
  "evidence/studies/simulation/preregistrations/faction-demand-validation-v1.json",
  "evidence/studies/simulation/preregistrations/faction-demand-validation-v1-rules.json",
  "evidence/studies/simulation/preregistrations/faction-demand-validation-v1-restart.json",
  "evidence/studies/simulation/preregistrations/faction-demand-validation-v1-restart-rules.json",
  "evidence/studies/simulation/preregistrations/faction-prestige-demand-v1.json",
  "evidence/studies/simulation/preregistrations/faction-prestige-demand-v1-rules.json",
  "evidence/studies/simulation/preregistrations/demis-late-validation-v1.json",
  "evidence/studies/simulation/preregistrations/demis-late-validation-v1-rules.json",
  "evidence/studies/simulation/preregistrations/demis-peer-validation-v1.json",
  "evidence/studies/simulation/preregistrations/demis-peer-validation-v1-rules.json",
  "evidence/studies/simulation/2026-07-27-current-matrix-and-mega-cluster-integrity.md",
  "evidence/studies/simulation/2026-07-28-supported-player-count-baseline.md",
  "evidence/studies/simulation/2026-07-28-faction-swap-diagnostic.md",
  "evidence/studies/simulation/2026-07-28-faction-strength-probes.md",
  "evidence/studies/simulation/2026-07-28-faction-progress-conversion-calibration.md",
  "evidence/studies/simulation/2026-07-28-faction-public-validation-confirmation.md",
  "evidence/studies/simulation/2026-07-28-foundry-supported-count-conversion.md",
  "evidence/studies/simulation/2026-07-28-faction-demand-validation.md",
  "evidence/studies/simulation/2026-07-28-faction-prestige-demand.md",
  "evidence/studies/simulation/2026-07-28-demis-late-validation.md",
  "evidence/studies/simulation/2026-07-28-four-lever-package-promotion.md",
  "evidence/studies/simulation/2026-07-28-residual-faction-parity-instrumentation.md",
  "evidence/studies/simulation/2026-07-28-residual-faction-parity-restart.md",
  "evidence/studies/simulation/2026-07-28-residual-parity-telemetry-release.md",
  "evidence/studies/simulation/preregistrations/residual-faction-parity-v1.json",
  "evidence/studies/simulation/preregistrations/residual-faction-parity-v1-restart.json",
  "evidence/studies/simulation/2026-07-27-foundry-scaling-rule-selection.md",
  "evidence/studies/simulation/2026-07-27-foundry-shovels-executable-correction.md",
  "evidence/studies/simulation/2026-07-26-first-automated-baseline.md"
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
const localSimulationArchive = `${resolve(root, "evidence/studies/simulation")}${sep}`;
for (const file of files) {
  if (extname(file) !== ".json") continue;
  if (file.startsWith(localSimulationArchive)) continue;
  JSON.parse(await readFile(file, "utf8"));
  jsonCount += 1;
}

const config = JSON.parse(await readFile(resolve(root, "dist/runtime/game-config.json"), "utf8"));
const trainingCount = config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0);
if (trainingCount !== 50) throw new Error(`Training deck must contain 50 cards, found ${trainingCount}.`);

const contentManifest = JSON.parse(await readFile(resolve(root, "dist/runtime/content-manifest.json"), "utf8"));
const missingWriting = contentManifest.surfaces.filter((surface) => (
  surface.status !== "production_layout_missing"
  && surface.status !== "final_art_missing"
  && !surface.file
));
if (missingWriting.length > 0) {
  throw new Error(`Content manifest has unowned writing surfaces: ${missingWriting.map((item) => item.id).join(", ")}.`);
}

const html = await readFile(resolve(root, "dist/site/index.html"), "utf8");
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

const simulationHtml = await readFile(resolve(root, "dist/site/simulation.html"), "utf8");
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
  resolve(root, "evidence/studies/simulation/2026-07-26-first-automated-baseline.md"),
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
if (packageDocument.scripts?.start !== "node tasks/serve.mjs") {
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
  await readFile(resolve(root, "versions/current-release.json"), "utf8")
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
const requiredCandidateDocuments = [
  "dist/docs/core-rules.md",
  "dist/docs/world-and-institutions.md",
  "dist/docs/optional-tactics.md"
];
const candidateStatusValid = candidate?.implementationStatus === "not-synchronized"
  ? candidate.implementedByGameVersion === null
  : candidate?.implementationStatus === "synchronized"
    && candidate.implementedByGameVersion === gameVersion.gameVersion;
if (
  typeof candidate?.version !== "string" ||
  candidate.version === gameVersion.gameVersion ||
  !candidateStatusValid ||
  !requiredCandidateDocuments.every((path) => candidate?.files?.includes(path))
) {
  throw new Error("Physical rules candidate identity is incomplete or conflated with the executable game.");
}
for (const path of requiredCandidateDocuments) {
  const document = await readFile(resolve(root, path), "utf8");
  if (!document.includes(`**Rules version:** ${gameVersion.rulesCandidate.version}`)) {
    throw new Error(`Physical rules candidate version does not match ${path}.`);
  }
}

process.stdout.write(
  `check-project: ${required.length} required files, ${jsonCount} JSON files, executable game ${gameVersion.gameVersion}, physical candidate ${gameVersion.rulesCandidate.version}, report schema 6, unified strategic-unsolvability contract, 50-card Training contract, structurally complete thematic manifest\n`
);
