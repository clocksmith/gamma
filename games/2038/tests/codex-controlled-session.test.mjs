import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { CodexCliRunner } from "../lab/callers/codex-cli-runner.js";
import {
  chunkRulesDocument,
  followupResponseSchema,
  postgameResponseSchema,
  rulesDocumentResponseSchema,
  rulesResponseSchema,
  unboxingResponseSchema,
  validateCodexSessionRegistration
} from "../lab/runner/codex-controlled-session-runner.js";

const root = new URL("../", import.meta.url);

test("CodexCliRunner isolates structured session stages from workspace state", () => {
  const runner = new CodexCliRunner({
    model: "gpt-5.6-sol",
    reasoningEffort: "medium"
  });
  const invocation = runner.invocation(
    "read the frozen rules",
    "/tmp/session",
    "/tmp/session/schema.json",
    "/tmp/session/output.json"
  );
  assert.equal(invocation.command, "codex");
  for (const argument of [
    "--sandbox",
    "read-only",
    "--ephemeral",
    "--ignore-user-config",
    "--ignore-rules",
    "--output-schema",
    "--output-last-message"
  ]) assert.ok(invocation.args.includes(argument));
  assert.ok(invocation.args.includes("gpt-5.6-sol"));
  assert.ok(invocation.args.includes("model_reasoning_effort=\"medium\""));
  assert.equal(invocation.input, "read the frozen rules");
});

test("controlled-session registration freezes four unique Codex seats and the release boundary", async () => {
  const registration = JSON.parse(await readFile(
    new URL(
      "evidence/studies/simulation/preregistrations/codex-controlled-session-2026-08-09-v5.json",
      root
    ),
    "utf8"
  ));
  assert.equal(validateCodexSessionRegistration(registration), registration);
  assert.equal(registration.release.gameVersion, "0.10.2");
  assert.equal(registration.release.rulesVersion, "0.7.0-rc.3-test");
  assert.equal(
    registration.release.releaseBoundaryCommit,
    "149a99be3c21cff71abf3ac734a927ae4f35d2d3"
  );
  assert.deepEqual(
    registration.participants.map((participant) => participant.factionName),
    ["Mirevanta Works", "Kestralyn", "Corthaven", "Loopfold AI"]
  );
  assert.ok(registration.participants.every((participant) => participant.backend === "codex"));
  assert.equal(registration.provider.maximumLlmDecisions, null);
  assert.equal(registration.provider.timeoutMs, 300000);
  assert.equal(registration.provider.reasoningEffort, "low");
  assert.equal(registration.provider.maximumAttemptsPerRequest, 2);
  assert.equal(registration.predecessor.disposition, "failed_diagnostic");
});

test("controlled-session schemas cover the complete recorded path", () => {
  assert.ok(unboxingResponseSchema.properties.immediateConfusions);
  assert.ok(rulesResponseSchema.properties.questions);
  assert.ok(rulesDocumentResponseSchema.properties.keyRules);
  assert.ok(rulesDocumentResponseSchema.properties.crossReferencesNeeded);
  assert.ok(followupResponseSchema.properties.readyToPlay);
  assert.ok(postgameResponseSchema.properties.winnerExplanation);
  assert.ok(postgameResponseSchema.properties.worldEndingExplanation);
});

test("rules documents split into bounded lossless source chunks", () => {
  const contents = [
    "# Rules\n\n",
    "A".repeat(6000),
    "\n\n## Next\n\n",
    "B".repeat(6000)
  ].join("");
  const chunks = chunkRulesDocument({
    id: "rules",
    fileName: "rules.md",
    contents,
    headings: ["Rules", "Next"]
  });
  assert.ok(chunks.length > 1);
  assert.equal(chunks.map((chunk) => chunk.contents).join(""), contents);
  assert.ok(chunks.every((chunk) => chunk.contents.length <= 8000));
  assert.deepEqual(chunks.map((chunk) => chunk.part), [1, 2]);
  assert.ok(chunks.every((chunk) => chunk.parts === chunks.length));
});
