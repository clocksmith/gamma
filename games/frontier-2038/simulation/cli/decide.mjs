import { readFile } from "node:fs/promises";
import { stdin, stdout } from "node:process";
import { ClaudeCliCaller, CodexCliCaller } from "../callers/index.js";
import { validateDecisionPacket } from "../contracts/decision-contract.js";

function parseArguments(values) {
  const options = {};
  for (let index = 0; index < values.length; index += 1) {
    const argument = values[index];
    if (argument === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    if (!argument.startsWith("--")) {
      throw new TypeError(`Unexpected argument: ${argument}`);
    }
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

async function readStdin() {
  const chunks = [];
  for await (const chunk of stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

function usage() {
  return [
    "Usage:",
    "  npm run strategy:claude -- --input decision-packet.json",
    "  npm run strategy:codex -- --input decision-packet.json",
    "  cat decision-packet.json | npm run strategy:claude -- --input -",
    "",
    "Options: --input FILE|- --model MODEL --timeout-ms N --dry-run"
  ].join("\n");
}

const options = parseArguments(process.argv.slice(2));
if (!["claude", "codex"].includes(options.provider)) {
  throw new TypeError(`A valid --provider is required.\n${usage()}`);
}
if (!options.input) {
  throw new TypeError(`--input is required.\n${usage()}`);
}

const source = options.input === "-" ? await readStdin() : await readFile(options.input, "utf8");
const packet = validateDecisionPacket(JSON.parse(source));
const shared = {
  model: options.model,
  timeoutMs: options["timeout-ms"] === undefined
    ? undefined
    : Number(options["timeout-ms"])
};
const caller = options.provider === "claude"
  ? new ClaudeCliCaller(shared)
  : new CodexCliCaller(shared);

if (options.dryRun) {
  const invocation = options.provider === "claude"
    ? await caller.invocation(packet, { redactPrompt: true })
    : await caller.describeInvocation(packet);
  stdout.write(`${JSON.stringify(invocation, null, 2)}\n`);
} else {
  stdout.write(`${JSON.stringify(await caller.decide(packet), null, 2)}\n`);
}
