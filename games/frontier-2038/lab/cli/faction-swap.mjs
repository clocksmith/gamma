#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { archiveSimulationReport } from "../report-archive.js";
import { createSimulationRunMonitor } from "../run-monitor.js";
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
const runsPerArm = Number(args["runs-per-arm"] || registration.runsPerArm);
const playerCount = Number(args.players || registration.playerCount);
const totalGames = registration.comparisons.length * runsPerArm * 2;
const jobId = args["job-id"] || `${registration.id}-${process.pid}`;
const monitor = createSimulationRunMonitor({
  projectRoot,
  jobId,
  totalGames
});
await monitor.start({
  configuration: {
    preRegistrationId: registration.id,
    comparisonsPath: args.comparisons,
    runsPerArm,
    playerCount,
    rulesVariant: registration.rulesVariant || {},
    backends: registration.backends || []
  }
});
process.stderr.write(`faction swap status: ${monitor.relativePath}\n`);
let report;
let archive;
try {
  report = await runFactionSwapDiagnostic({
    comparisons: registration.comparisons,
    runsPerArm,
    playerCount,
  profileIds: registration.profileIds,
  backends: registration.backends,
  mandateMode: registration.mandateMode,
  rulesVariant: registration.rulesVariant,
  workers: args.workers || registration.workers,
  seed: args.seed || registration.seed,
    preRegistrationId: registration.id
  }, (progress) => {
    void monitor.update(progress);
    process.stderr.write(`\rfaction swap: ${progress.completed}/${progress.total}`);
  });
  await monitor.flush();
  process.stderr.write("\n");
  const output = `${JSON.stringify(report, null, 2)}\n`;
  archive = await archiveSimulationReport(report, {
    projectRoot,
    jobId: "faction-swap-cli"
  });
  if (args.output) await writeFile(args.output, output);
  await monitor.complete({ archive: archive.relativePath });
} catch (error) {
  await monitor.fail(error);
  throw error;
}
const output = `${JSON.stringify(report, null, 2)}\n`;
console.log(JSON.stringify({
  archive: archive.relativePath,
  status: monitor.relativePath,
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
