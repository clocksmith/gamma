import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { ClaudeCliCaller, CodexCliCaller } from "../simulation/callers/index.js";
import {
  buildDecisionPrompt,
  validateDecisionPacket,
  validateDecisionResponse
} from "../simulation/contracts/decision-contract.js";
import { DecisionCache } from "../simulation/policies/decision-cache.js";
import { CliBackedPlayerPolicy } from "../simulation/policies/cli-backed-policy.js";
import { loadPlayerProfiles } from "../simulation/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../simulation/policies/weighted-policy.js";

const packet = JSON.parse(await readFile(
  new URL("../simulation/fixtures/decision-packet.example.json", import.meta.url),
  "utf8"
));
const fakeCli = fileURLToPath(
  new URL("./fixtures/fake-decision-cli.mjs", import.meta.url)
);
const responseSchema = JSON.parse(await readFile(
  new URL("../simulation/contracts/decision-response.schema.json", import.meta.url),
  "utf8"
));

test("decision packets enumerate unique legal choices", () => {
  assert.equal(validateDecisionPacket(packet), packet);
  assert.match(buildDecisionPrompt(packet), /Choose exactly one decisionId/);
  assert.throws(
    () => validateDecisionResponse(packet, { decisionId: "invented_action" }),
    /illegal decisionId/
  );
});

test("provider response schema is strict-compatible without making commentary semantic", () => {
  assert.deepEqual(
    responseSchema.required,
    Object.keys(responseSchema.properties)
  );
  assert.deepEqual(responseSchema.properties.rationale.type, ["string", "null"]);
  assert.deepEqual(responseSchema.properties.confidence.type, ["number", "null"]);
  assert.deepEqual(
    validateDecisionResponse(packet, {
      decisionId: "research_stop_3_frontier",
      rationale: null,
      confidence: null
    }),
    { decisionId: "research_stop_3_frontier" }
  );
});

test("ClaudeCliCaller returns a validated decision and receipt", async () => {
  const caller = new ClaudeCliCaller({
    command: process.execPath,
    prefixArgs: [fakeCli],
    timeoutMs: 5000
  });
  const result = await caller.decide(packet);
  assert.equal(result.decision.decisionId, "research_stop_3_frontier");
  assert.equal(result.receipt.provider, "claude-cli");
  assert.equal(result.receipt.requestId, packet.requestId);
});

test("CodexCliCaller returns a validated decision from an isolated output file", async () => {
  const caller = new CodexCliCaller({
    command: process.execPath,
    prefixArgs: [fakeCli],
    timeoutMs: 5000
  });
  const result = await caller.decide(packet);
  assert.equal(result.decision.decisionId, "research_stop_3_frontier");
  assert.equal(result.receipt.provider, "codex-cli");
  assert.equal(result.receipt.requestId, packet.requestId);
});

test("provider decisions outside the legal set fail closed", async () => {
  const caller = new ClaudeCliCaller({
    command: process.execPath,
    prefixArgs: [fakeCli],
    env: { FAKE_DECISION_ID: "not_legal" },
    timeoutMs: 5000
  });
  await assert.rejects(() => caller.decide(packet), /illegal decisionId/);
});

test("decision cache replays a provider result without a fresh call", async () => {
  const directory = await mkdtemp(join(tmpdir(), "m3t4-decision-cache-"));
  try {
    const profile = (await loadPlayerProfiles())[0];
    let calls = 0;
    const caller = {
      async decide(input) {
        calls += 1;
        return {
          decision: {
            decisionId: input.legalDecisions[0].decisionId,
            rationale: "fixture"
          },
          receipt: {
            provider: "fixture-cli",
            requestId: input.requestId
          }
        };
      }
    };
    const shared = {
      fallback: new WeightedPlayerPolicy(profile),
      decisionBudget: { remaining: 2 },
      decisionCache: new DecisionCache(directory),
      backendId: "fixture-cli",
      model: "fixture-model"
    };
    const writer = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      cacheMode: "read-write"
    });
    const first = await writer.decide(packet);
    const reader = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      cacheMode: "read-only"
    });
    const second = await reader.decide(packet);
    assert.equal(calls, 1);
    assert.equal(first.decision.decisionId, second.decision.decisionId);
    assert.equal(second.receipt.cached, true);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("write-only capture never reads and supplies a later read-only replay", async () => {
  const directory = await mkdtemp(join(tmpdir(), "m3t4-decision-cache-capture-"));
  try {
    const profile = (await loadPlayerProfiles())[0];
    let calls = 0;
    const caller = {
      async decide(input) {
        calls += 1;
        return {
          decision: {
            decisionId: input.legalDecisions[0].decisionId,
            rationale: "fresh fixture"
          },
          receipt: {
            provider: "fixture-cli",
            requestId: input.requestId
          }
        };
      }
    };
    const shared = {
      fallback: new WeightedPlayerPolicy(profile),
      decisionBudget: { remaining: 3 },
      decisionCache: new DecisionCache(directory),
      backendId: "fixture-cli",
      model: "fixture-model"
    };
    const capture = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      cacheMode: "write-only"
    });
    const fresh = await capture.decide(packet);
    assert.equal(calls, 1);
    assert.equal(fresh.receipt.cached, false);

    const replay = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      cacheMode: "read-only"
    });
    const cached = await replay.decide(packet);
    assert.equal(calls, 1);
    assert.equal(cached.receipt.cached, true);
    assert.equal(cached.decision.decisionId, fresh.decision.decisionId);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("provider failure provenance survives deterministic fallback", async () => {
  const profile = (await loadPlayerProfiles())[0];
  const caller = {
    async decide() {
      const error = new Error("fixture provider failed");
      error.providerReceipt = {
        attemptedProvider: "fixture-cli",
        attemptedModel: "fixture-model",
        attemptedRequestId: packet.requestId,
        attemptedPromptSha256: "prompt-sha",
        providerErrorClass: "FixtureError",
        providerErrorMessage: "fixture provider failed",
        providerErrorExitCode: 17,
        providerErrorStderrSha256: "stderr-sha",
        providerDurationMs: 42
      };
      throw error;
    }
  };
  const policy = new CliBackedPlayerPolicy(profile, caller, {
    fallback: new WeightedPlayerPolicy(profile),
    backendId: "fixture-cli",
    model: "fixture-model"
  });
  const result = await policy.decide(packet);
  assert.equal(result.receipt.fallback, true);
  assert.equal(result.receipt.provider, "weighted-policy");
  assert.equal(result.receipt.attemptedProvider, "fixture-cli");
  assert.equal(result.receipt.attemptedPromptSha256, "prompt-sha");
  assert.equal(result.receipt.providerErrorStderrSha256, "stderr-sha");
});
