import { writeFile } from "node:fs/promises";
import { stderr, stdout } from "node:process";
import { fileURLToPath } from "node:url";
import { archiveSimulationReport } from "../report-archive.js";
import { createSimulation } from "../runtime/create-simulation.js";

function parseArguments(values) {
  const options = {};
  for (let index = 0; index < values.length; index += 1) {
    const argument = values[index];
    if (argument === "--allow-llm") {
      options.allowLlm = true;
      continue;
    }
    if (argument === "--require-llm") {
      options.requireLlm = true;
      continue;
    }
    if (!argument.startsWith("--")) throw new TypeError(`Unexpected argument: ${argument}`);
    const key = argument.slice(2);
    const value = values[index + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new TypeError(`Missing value for ${argument}.`);
    }
    options[key] = value;
    index += 1;
  }
  return options;
}

const input = parseArguments(process.argv.slice(2));
const report = await createSimulation({
  runs: input.runs,
  playerCount: input.players,
  seed: input.seed,
  sampleReplays: input["sample-replays"],
  profileIds: input.profiles?.split(",").filter(Boolean),
  backends: input.backends?.split(",").filter(Boolean),
  allowLlm: input.allowLlm,
  requireLlm: input.requireLlm,
  maxLlmDecisions: input["max-llm-decisions"],
  maxLlmDecisionsPerSeatCycle: input["max-llm-decisions-per-seat-cycle"],
  model: input.model,
  models: input.models?.split(",").filter(Boolean),
  reasoningEffort: input["reasoning-effort"],
  reasoningEfforts: input["reasoning-efforts"]?.split(",").filter(Boolean),
  timeoutMs: input["timeout-ms"],
  shortlistSize: input["shortlist-size"]
}, (progress) => {
  if (progress.phase === "match_progress") {
    stderr.write(`${JSON.stringify(progress)}\n`);
    return;
  }
  stderr.write(`simulation ${progress.completed}/${progress.runs}\n`);
});

const serialized = `${JSON.stringify(report, null, 2)}\n`;
const projectRoot = fileURLToPath(new URL("../../", import.meta.url));
const archive = await archiveSimulationReport(report, {
  projectRoot,
  jobId: "cli"
});
if (input.output) {
  await writeFile(input.output, serialized);
}
stdout.write(`${JSON.stringify({
  archive: archive.relativePath,
  output: input.output || null,
  runs: report.runs,
  playerCount: report.playerCount,
  gameVersion: report.game.version,
  rulesetFingerprint: report.game.rulesetFingerprint,
  diagnostics: report.diagnostics
}, null, 2)}\n`);
