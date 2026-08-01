#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { archiveSimulationReport } from "../report-archive.js";
import { runFactionSwapDiagnostic } from "../runner/faction-swap-runner.js";
import { projectRoot } from "../versioning/game-identity.js";

function argumentsMap(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    if (!argv[index].startsWith("--")) continue;
    const key = argv[index].slice(2);
    result[key] = argv[index + 1]?.startsWith("--") ? true : argv[++index] ?? true;
  }
  return result;
}

const args = argumentsMap(process.argv.slice(2));
if (!args.comparisons) {
  throw new TypeError("--comparisons must name a preregistered comparison JSON file.");
}
const registration = JSON.parse(await readFile(args.comparisons, "utf8"));
const report = await runFactionSwapDiagnostic({
  comparisons: registration.comparisons,
  comparisonMatrix: registration.comparisonMatrix,
  runsPerArm: Number(args["runs-per-arm"] || registration.runsPerArm),
  playerCount: Number(args.players || registration.playerCount),
  profileIds: registration.profileIds,
  promptAddenda: registration.promptAddenda,
  promptLibrary: registration.promptLibrary,
  backends: registration.backends,
  mandateMode: registration.mandateMode,
  rulesVariant: registration.rulesVariant,
  workers: args.workers || registration.workers,
  llmConcurrency:
    args["llm-concurrency"] || registration.llmConcurrency,
  llmRetries: args["llm-retries"] || registration.llmRetries,
  providerConcurrency: {
    ...(registration.providerConcurrency || {}),
    ...(args["claude-concurrency"]
      ? { claude: args["claude-concurrency"] }
      : {}),
    ...(args["codex-concurrency"]
      ? { codex: args["codex-concurrency"] }
      : {})
  },
  allowLlm: args["allow-llm"] === true || Boolean(registration.allowLlm),
  models: registration.models,
  model: args.model || registration.model,
  reasoningEfforts: registration.reasoningEfforts,
  reasoningEffort:
    args["reasoning-effort"] || registration.reasoningEffort,
  maxLlmDecisions:
    args["max-llm-decisions"] || registration.maxLlmDecisions,
  maxLlmDecisionsPerSeatCycle:
    args["max-llm-decisions-per-seat-cycle"] ||
    registration.maxLlmDecisionsPerSeatCycle,
  sampleReplays:
    args["sample-replays"] || registration.sampleReplays,
  seed: args.seed || registration.seed,
  preRegistrationId: registration.id
}, ({ completed, total }) => {
  process.stderr.write(`\rfaction swap: ${completed}/${total}`);
});
process.stderr.write("\n");
const output = `${JSON.stringify(report, null, 2)}\n`;
const archive = await archiveSimulationReport(report, {
  projectRoot,
  jobId: "faction-swap-cli"
});
if (args.output) await writeFile(args.output, output);
console.log(JSON.stringify({
  archive: archive.relativePath,
  output: args.output || null,
  runs: report.runs,
  execution: report.execution,
  comparisons: report.comparisons.map((comparison) => ({
    id: comparison.id,
    meanWinRateDelta: comparison.paired.meanWinRateDelta,
    meanMandateDelta: comparison.paired.meanMandateDelta,
    meanRankAdvantage: comparison.paired.meanRankAdvantage
  })),
  sourceDirty: report.provenance.sourceDirty
}, null, 2));
