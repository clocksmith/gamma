#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { runLlmNegotiationHoldout } from "../runner/llm-holdout-runner.js";
import { archiveSimulationReport } from "../report-archive.js";
import { projectRoot } from "../versioning/game-identity.js";

function parseArguments(values) {
  const result = {};
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (value === "--allow-llm") {
      result["allow-llm"] = true;
      continue;
    }
    if (!value.startsWith("--")) throw new TypeError(`Unexpected argument: ${value}.`);
    const next = values[index + 1];
    if (next === undefined || next.startsWith("--")) {
      throw new TypeError(`Missing value for ${value}.`);
    }
    result[value.slice(2)] = next;
    index += 1;
  }
  return result;
}

const args = parseArguments(process.argv.slice(2));
if (!args.preregistration) throw new TypeError("--preregistration is required.");
const report = await runLlmNegotiationHoldout({
  preRegistrationPath: args.preregistration,
  allowLlm: Boolean(args["allow-llm"])
});
const output = `${JSON.stringify(report, null, 2)}\n`;
const archive = await archiveSimulationReport(report, {
  projectRoot,
  jobId: "llm-holdout-cli"
});
if (args.output) {
  await writeFile(args.output, output);
}
console.log(JSON.stringify({
  archive: archive.relativePath,
  output: args.output || null,
  preRegistrationId: report.preRegistration.id,
  providerProvenance: report.configuration.cliProviders,
  usedLlmDecisions: report.configuration.usedLlmDecisions,
  sourceDirty: report.provenance.sourceDirty
}, null, 2));
