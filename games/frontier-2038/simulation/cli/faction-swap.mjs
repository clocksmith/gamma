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
  runsPerArm: Number(args["runs-per-arm"] || registration.runsPerArm),
  playerCount: Number(args.players || registration.playerCount),
  profileIds: registration.profileIds,
  backends: registration.backends,
  mandateMode: registration.mandateMode,
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
  comparisons: report.comparisons.map((comparison) => ({
    id: comparison.id,
    meanWinRateDelta: comparison.paired.meanWinRateDelta,
    meanMandateDelta: comparison.paired.meanMandateDelta,
    meanRankAdvantage: comparison.paired.meanRankAdvantage
  })),
  sourceDirty: report.provenance.sourceDirty
}, null, 2));
