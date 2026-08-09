#!/usr/bin/env node
import { appendFile, mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { runCodexControlledSession } from "../runner/codex-controlled-session-runner.js";
import { sha256 } from "../versioning/game-identity.js";

function parseArguments(values) {
  const result = {};
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (value === "--allow-llm") {
      result.allowLlm = true;
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

function markdownReceipt(session, gameReport, hashes) {
  const standings = session.stages.gameplay.standings || [];
  const participants = new Map(session.participants.map((entry) => [entry.seat, entry]));
  const rows = standings.map((entry, index) => {
    const participant = participants.get(entry.seat);
    return `| ${index + 1} | ${participant?.factionName || entry.factionId} | ${entry.score} | ${entry.agiDeclared ? "yes" : "no"} |`;
  }).join("\n");
  return `# Codex controlled-session receipt

Session: \`${session.id}\`

Evidence: **LLM simulation**, not a human physical or blind playtest

Rules: \`${session.release.rulesVersion}\`  
Executable: \`${session.release.gameVersion}\`  
Ruleset: \`${session.release.rulesetFingerprint}\`  
Release boundary: \`${session.release.releaseBoundaryCommit}\`  
Physical kit: \`${session.physicalKit.kitId}\`  
Physical-kit fingerprint: \`${session.physicalKit.kitFingerprint}\`  
Harness source: \`${session.gameplayIdentity.provenance.sourceCommit}\`

## Recorded path

- Emulated unboxing and component sorting: ${session.stages.unboxing.length} participant records.
- Independent reading of the four frozen Default Game documents: ${session.stages.rulesReading.length} records.
- Initial participant questions: ${session.stages.initialQuestions.length}.
- Source-grounded facilitator answers: ${session.stages.initialFacilitation.output.answers.length}.
- Remaining follow-up questions: ${session.stages.remainingQuestions.length}.
- Complete Codex gameplay decisions: ${session.gameplayIdentity.usedLlmDecisions}.
- Postgame winner, World Ending, and rules reconstruction: ${session.stages.postgame.length} records.

## Outcome

| Rank | Faction | Mandate | Declared AGI |
| ---: | --- | ---: | --- |
${rows}

World Ending: **${session.stages.gameplay.worldEnding?.name || session.stages.gameplay.worldEnding?.id || "unknown"}**

## Artifact integrity

- \`session.json\`: \`sha256:${hashes.session}\`
- \`gameplay-report.json\`: \`sha256:${hashes.gameplay}\`
- Provider fallback count: ${gameReport.diagnostics?.integrity?.policyFallbacks ?? gameReport.diagnostics?.policyFallbacks ?? "see gameplay report"}
- Rules and engine identity remained frozen through report completion.

## Interpretation boundary

${session.limitations.map((entry) => `- ${entry}`).join("\n")}
`;
}

const args = parseArguments(process.argv.slice(2));
if (!args.preregistration || !args["kit-manifest"] || !args["output-dir"]) {
  throw new TypeError(
    "--preregistration, --kit-manifest, --output-dir, and --allow-llm are required."
  );
}
if (!args.allowLlm) throw new Error("Codex session provider use requires --allow-llm.");

const outputDirectory = resolve(args["output-dir"]);
await mkdir(resolve(outputDirectory, ".."), { recursive: true });
await mkdir(outputDirectory, { recursive: false });
const journalPath = resolve(outputDirectory, "stage-journal.jsonl");

const { session, gameReport } = await runCodexControlledSession({
  preRegistrationPath: args.preregistration,
  kitManifestPath: args["kit-manifest"],
  allowLlm: true,
  onProgress(progress) {
    if (progress.phase === "match_progress") {
      process.stderr.write(`${JSON.stringify(progress)}\n`);
      return;
    }
    process.stderr.write(`codex-session ${progress.id} ${progress.status}\n`);
  },
  async onStageComplete(entry) {
    await appendFile(journalPath, `${JSON.stringify(entry)}\n`);
  }
});

const sessionText = `${JSON.stringify(session, null, 2)}\n`;
const gameplayText = `${JSON.stringify(gameReport, null, 2)}\n`;
const sessionTemporary = resolve(outputDirectory, ".session.json.tmp");
const gameplayTemporary = resolve(outputDirectory, ".gameplay-report.json.tmp");
await writeFile(sessionTemporary, sessionText, { flag: "wx" });
await writeFile(gameplayTemporary, gameplayText, { flag: "wx" });
await rename(sessionTemporary, resolve(outputDirectory, "session.json"));
await rename(gameplayTemporary, resolve(outputDirectory, "gameplay-report.json"));
const hashes = {
  session: sha256(sessionText),
  gameplay: sha256(gameplayText)
};
await writeFile(
  resolve(outputDirectory, "receipt.md"),
  markdownReceipt(session, gameReport, hashes),
  { flag: "wx" }
);
const registration = JSON.parse(await readFile(resolve(args.preregistration), "utf8"));
process.stdout.write(`${JSON.stringify({
  sessionId: registration.id,
  outputDirectory,
  sessionSha256: `sha256:${hashes.session}`,
  gameplaySha256: `sha256:${hashes.gameplay}`,
  usedLlmDecisions: session.gameplayIdentity.usedLlmDecisions,
  worldEnding: session.stages.gameplay.worldEnding?.id || null
}, null, 2)}\n`);
