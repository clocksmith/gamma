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
const field = args.field
  ? registration.fields?.find((candidate) => candidate.id === args.field)
  : null;
if (args.field && !field) {
  throw new TypeError(`Unknown preregistered field: ${args.field}.`);
}
const study = field ? { ...registration, ...field } : registration;
const report = await runFactionSwapDiagnostic({
  comparisons: study.comparisons,
  comparisonMatrix: study.comparisonMatrix,
  conversionMatrix: study.conversionMatrix,
  scenarioMatrix: study.scenarioMatrix,
  diagnosticKind: study.diagnosticKind,
  experimentKind: study.experimentKind,
  runsPerArm: Number(args["runs-per-arm"] || study.runsPerArm),
  playerCount: Number(args.players || study.playerCount),
  profileIds: study.profileIds,
  promptAddenda: study.promptAddenda,
  promptLibrary: study.promptLibrary,
  backends: study.backends,
  mandateMode: study.mandateMode,
  projection: args.projection || study.projection,
  rulesVariant: study.rulesVariant,
  workers: args.workers || study.workers,
  llmConcurrency:
    args["llm-concurrency"] || study.llmConcurrency,
  llmRetries: args["llm-retries"] || study.llmRetries,
  providerConcurrency: {
    ...(study.providerConcurrency || {}),
    ...(args["claude-concurrency"]
      ? { claude: args["claude-concurrency"] }
      : {}),
    ...(args["codex-concurrency"]
      ? { codex: args["codex-concurrency"] }
      : {})
  },
  allowLlm: args["allow-llm"] === true || Boolean(study.allowLlm),
  models: study.models,
  model: args.model || study.model,
  reasoningEfforts: study.reasoningEfforts,
  reasoningEffort:
    args["reasoning-effort"] || study.reasoningEffort,
  maxLlmDecisions:
    args["max-llm-decisions"] || study.maxLlmDecisions,
  maxLlmDecisionsPerSeatCycle:
    args["max-llm-decisions-per-seat-cycle"] ||
    study.maxLlmDecisionsPerSeatCycle,
  sampleReplays:
    args["sample-replays"] || study.sampleReplays,
  seed: args.seed || study.seed,
  preRegistrationId: field
    ? `${registration.id}:${field.id}`
    : registration.id
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
