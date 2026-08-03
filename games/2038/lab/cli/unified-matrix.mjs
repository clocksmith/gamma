#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { runUnifiedMatrix } from "../runner/unified-matrix-runner.js";
import { archiveSimulationReport } from "../report-archive.js";
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
const rulesConfigurations = args["rules-configurations"]
  ? JSON.parse(await readFile(args["rules-configurations"], "utf8"))
  : undefined;
const profileOverrideReports = args["profile-override-reports"]
  ? await Promise.all(
    String(args["profile-override-reports"]).split(",").filter(Boolean).map(async (path) => {
      const report = JSON.parse(await readFile(path, "utf8"));
      if (!report.championProfile) {
        throw new TypeError(`Evolution report ${path} has no championProfile.`);
      }
      return report.championProfile;
    })
  )
  : undefined;
const numberArgument = (...names) => {
  const value = names.map((name) => args[name]).find((candidate) =>
    candidate !== undefined
  );
  return value === undefined ? undefined : Number(value);
};
const report = await runUnifiedMatrix({
  maximumMatches: numberArgument("runs", "maximum-matches"),
  initialRunsPerCell: numberArgument("initial-runs"),
  batchSize: numberArgument("batch-size"),
  playerCounts: args["player-counts"]
    ? String(args["player-counts"]).split(",").map(Number)
    : undefined,
  mandateModes: args["mandate-modes"]
    ? String(args["mandate-modes"]).split(",")
    : undefined,
  rulesConfigurations,
  comparisonKind: args["comparison-kind"],
  profileOverrides: profileOverrideReports,
  seed: args.seed || "mandate-2038-unified-matrix",
  preRegistrationId: args["pre-registration-id"],
  projection: args.projection,
  workers: args.workers === undefined ? undefined : Number(args.workers),
  chunkSize: args["chunk-size"] === undefined
    ? undefined
    : Number(args["chunk-size"])
}, ({ phase, completed, total }) => {
  process.stderr.write(`\r${phase}: ${completed}/${total}`);
});
process.stderr.write("\n");
const output = `${JSON.stringify(report, null, 2)}\n`;
const archive = await archiveSimulationReport(report, {
  projectRoot,
  jobId: "unified-matrix-cli"
});
if (args.output) {
  await writeFile(args.output, output);
}
console.log(JSON.stringify({
  archive: archive.relativePath,
  output: args.output || null,
  runs: report.runs,
  playerCounts: report.playerCounts,
  projection: report.execution.projection,
  workers: report.execution.requestedWorkers,
  matrixStatus: report.balanceEvaluation.status,
  sourceDirty: report.provenance.sourceDirty
}, null, 2));
