import { writeFile } from "node:fs/promises";

const args = process.argv.slice(2);
const input = [];
for await (const chunk of process.stdin) input.push(chunk);

const prompt = Buffer.concat(input).toString("utf8");
const providerPacket = JSON.parse(prompt.split("DECISION_PACKET\n").at(-1));
const decision = {
  decisionId: process.env.FAKE_DECISION_ID || providerPacket.legalDecisions[1].decisionId,
  rationale: "Fixture provider selected a legal decision.",
  confidence: 0.75
};

if (args[0] === "exec") {
  for (const required of ["--sandbox", "read-only", "--ephemeral", "--output-schema"]) {
    if (!args.includes(required)) throw new Error(`Missing Codex argument: ${required}`);
  }
  const outputIndex = args.indexOf("--output-last-message");
  if (outputIndex < 0) throw new Error("Missing Codex output path.");
  await writeFile(args[outputIndex + 1], `${JSON.stringify(decision)}\n`);
  process.stdout.write("fixture codex events\n");
} else {
  for (const required of ["-p", "--tools", "--safe-mode", "--json-schema"]) {
    if (!args.includes(required)) throw new Error(`Missing Claude argument: ${required}`);
  }
  process.stdout.write(JSON.stringify({
    type: "result",
    structured_output: decision
  }));
}
