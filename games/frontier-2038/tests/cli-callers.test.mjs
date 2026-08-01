import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { ClaudeCliCaller, CodexCliCaller } from "../lab/callers/index.js";
import {
  buildDecisionPrompt,
  validateDecisionPacket,
  validateDecisionResponse
} from "../lab/contracts/decision-contract.js";
import { DecisionCache } from "../lab/policies/decision-cache.js";
import { CliBackedPlayerPolicy } from "../lab/policies/cli-backed-policy.js";
import {
  loadPlayerProfiles,
  profileForPrompt
} from "../lab/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";

const packet = JSON.parse(await readFile(
  new URL("../lab/fixtures/decision-packet.example.json", import.meta.url),
  "utf8"
));
const fakeCli = fileURLToPath(
  new URL("./fixtures/fake-decision-cli.mjs", import.meta.url)
);
const responseSchema = JSON.parse(await readFile(
  new URL("../lab/contracts/decision-response.schema.json", import.meta.url),
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
    model: "claude-fable-5",
    reasoningEffort: "medium",
    timeoutMs: 5000
  });
  const invocation = await caller.invocation(packet);
  assert.ok(invocation.args.includes("--effort"));
  assert.ok(invocation.args.includes("medium"));
  const result = await caller.decide(packet);
  assert.equal(result.decision.decisionId, "research_stop_3_frontier");
  assert.equal(result.receipt.provider, "claude-cli");
  assert.equal(result.receipt.model, "claude-fable-5");
  assert.equal(result.receipt.reasoningEffort, "medium");
  assert.equal(result.receipt.requestId, packet.requestId);
});

test("CodexCliCaller returns a validated decision from an isolated output file", async () => {
  const caller = new CodexCliCaller({
    command: process.execPath,
    prefixArgs: [fakeCli],
    model: "gpt-5.6-sol",
    reasoningEffort: "medium",
    timeoutMs: 5000
  });
  const invocation = caller.invocation(packet, "fixture-directory", "fixture-output.json");
  assert.ok(invocation.args.includes("--model"));
  assert.ok(invocation.args.includes("gpt-5.6-sol"));
  assert.ok(invocation.args.includes('model_reasoning_effort="medium"'));
  const result = await caller.decide(packet);
  assert.equal(result.decision.decisionId, "research_stop_3_frontier");
  assert.equal(result.receipt.provider, "codex-cli");
  assert.equal(result.receipt.model, "gpt-5.6-sol");
  assert.equal(result.receipt.reasoningEffort, "medium");
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

test("missing formal responses use the rulebook reject or pass default", async () => {
  const profile = (await loadPlayerProfiles())[0];
  const unavailableCaller = {
    async decide() {
      throw new Error("Provider did not respond.");
    }
  };
  const policy = new CliBackedPlayerPolicy(profile, unavailableCaller, {
    backendId: "fixture-cli",
    requireLlm: true
  });
  const powerResponse = await policy.decide({
    ...structuredClone(packet),
    requestId: "fixture:r3:c1:s1:power_sale_0_1:1",
    legalDecisions: [
      { decisionId: "power_sale_accept_0_1", label: "Accept" },
      { decisionId: "power_sale_reject_0_1", label: "Reject" }
    ]
  });
  assert.equal(powerResponse.decision.decisionId, "power_sale_reject_0_1");
  assert.equal(powerResponse.receipt.provider, "rulebook-default");
  assert.equal(powerResponse.receipt.formalResponseDefault, true);

  const claimResponse = await policy.decide({
    ...structuredClone(packet),
    requestId: "fixture:r3:c1:s1:immediate_trade_claim:2",
    legalDecisions: [
      { decisionId: "trade_claim_pass", label: "Pass" },
      { decisionId: "trade_claim_accept", label: "Claim" }
    ]
  });
  assert.equal(claimResponse.decision.decisionId, "trade_claim_pass");

  for (const [requestId, legalDecisions, expectedDecisionId] of [
    [
      "fixture:r3:c1:s1:mega_cluster_partner:3",
      [
        { decisionId: "mega_cluster_accept", label: "Accept" },
        { decisionId: "mega_cluster_reject", label: "Reject" }
      ],
      "mega_cluster_reject"
    ],
    [
      "fixture:r3:c1:s1:boardroom_coup_response:4",
      [
        { decisionId: "boardroom_back", label: "Back" },
        { decisionId: "boardroom_refuse", label: "Refuse" }
      ],
      "boardroom_refuse"
    ],
    [
      "fixture:r3:c1:s1:realignment_ballot:5",
      [
        { decisionId: "realignment_core", label: "Core" },
        { decisionId: "realignment_no_ballot", label: "No ballot" }
      ],
      "realignment_no_ballot"
    ]
  ]) {
    const response = await policy.decide({
      ...structuredClone(packet),
      requestId,
      legalDecisions
    });
    assert.equal(response.decision.decisionId, expectedDecisionId);
    assert.equal(response.receipt.formalResponseDefault, true);
  }
});

test("strict LLM evidence rejects formal and weighted fallback paths", async () => {
  const profile = (await loadPlayerProfiles())[0];
  const unavailableCaller = {
    async decide() {
      const error = new Error("Provider did not respond.");
      error.providerReceipt = {
        attemptedProvider: "codex-cli",
        attemptedModel: "fixture-model",
        attemptedReasoningEffort: "low"
      };
      throw error;
    }
  };
  const policy = new CliBackedPlayerPolicy(profile, unavailableCaller, {
    backendId: "codex",
    requireLlm: true,
    strictLlmEvidence: true,
    fallback: new WeightedPlayerPolicy(profile)
  });
  await assert.rejects(
    () => policy.decide({
      ...structuredClone(packet),
      requestId: "fixture:r3:c1:s1:power_sale_0_1:strict",
      legalDecisions: [
        { decisionId: "power_sale_accept_0_1", label: "Accept" },
        { decisionId: "power_sale_reject_0_1", label: "Reject" }
      ]
    }),
    (error) =>
      error.evidenceOutcome === "quarantined" &&
      error.providerReceipt.attemptedProvider === "codex-cli"
  );
});

test("per-seat cycle prompt budgets fail closed instead of falling back", async () => {
  const profile = (await loadPlayerProfiles())[0];
  const caller = {
    async decide(input) {
      return {
        decision: { decisionId: input.legalDecisions[0].decisionId },
        receipt: { provider: "fixture-cli", requestId: input.requestId }
      };
    }
  };
  const decisionBudget = {
    remaining: 4,
    maxPerSeatCycle: 1,
    perSeatCycleUsage: new Map()
  };
  const policy = new CliBackedPlayerPolicy(profile, caller, {
    fallback: new WeightedPlayerPolicy(profile),
    backendId: "fixture-cli",
    decisionBudget
  });
  await policy.decide(packet);
  await assert.rejects(
    () => policy.decide(packet),
    /LLM prompt budget exhausted/
  );
  assert.equal(decisionBudget.remaining, 3);
});

test("CLI policy preserves its private deterministic seed without sending it to the provider", async () => {
  const profile = (await loadPlayerProfiles())[0];
  let providerPacket;
  const policy = new CliBackedPlayerPolicy(profile, {
    async decide(input) {
      providerPacket = input;
      return {
        decision: { decisionId: input.legalDecisions[0].decisionId },
        receipt: { provider: "fixture-cli", requestId: input.requestId }
      };
    }
  }, {
    fallback: new WeightedPlayerPolicy(profile),
    backendId: "fixture-cli"
  });
  const privatePacket = structuredClone(packet);
  delete privatePacket.seed;
  Object.defineProperty(privatePacket, "policySeed", {
    value: "private-policy-seed",
    enumerable: false
  });

  await policy.decide(privatePacket);

  assert.equal(providerPacket.policySeed, "private-policy-seed");
  assert.doesNotMatch(buildDecisionPrompt(providerPacket), /private-policy-seed/);
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

test("strict LLM evidence rejects historical fallback cache entries", async () => {
  const directory = await mkdtemp(join(tmpdir(), "m3t4-strict-cache-"));
  try {
    const profile = (await loadPlayerProfiles())[0];
    const cache = new DecisionCache(directory);
    const promptProfile = profileForPrompt(profile);
    const cacheInput = {
      backend: "codex",
      model: "fixture-model",
      reasoningEffort: "low",
      packet: {
        ...structuredClone(packet),
        strategy: promptProfile
      },
      profile: promptProfile
    };
    await cache.write(cache.key(cacheInput), {
      decision: { decisionId: packet.legalDecisions[0].decisionId },
      receipt: {
        provider: "weighted",
        requestId: packet.requestId,
        fallback: true,
        fallbackReason: "Historical provider failure."
      }
    });
    const policy = new CliBackedPlayerPolicy(profile, {
      async decide() {
        throw new Error("Strict cache reads must not call the provider.");
      }
    }, {
      backendId: "codex",
      model: "fixture-model",
      reasoningEffort: "low",
      decisionCache: cache,
      cacheMode: "read-only",
      requireLlm: true,
      strictLlmEvidence: true
    });
    await assert.rejects(
      () => policy.decide(packet),
      (error) =>
        error.evidenceOutcome === "quarantined" &&
        error.providerReceipt.fallback === true
    );
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("decision cache misses when reasoning effort changes", async () => {
  const directory = await mkdtemp(join(tmpdir(), "m3t4-decision-cache-effort-"));
  try {
    const profile = (await loadPlayerProfiles())[0];
    let calls = 0;
    const caller = {
      async decide(input) {
        calls += 1;
        return {
          decision: { decisionId: input.legalDecisions[0].decisionId },
          receipt: { provider: "fixture-cli", requestId: input.requestId }
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
    const lowEffort = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      reasoningEffort: "low",
      cacheMode: "read-write"
    });
    await lowEffort.decide(packet);

    const mediumEffort = new CliBackedPlayerPolicy(profile, caller, {
      ...shared,
      reasoningEffort: "medium",
      cacheMode: "read-write"
    });
    const result = await mediumEffort.decide(packet);
    assert.equal(calls, 2);
    assert.equal(result.receipt.cached, false);
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

test("required LLM policies block provider failures instead of falling back", async () => {
  const profile = (await loadPlayerProfiles())[0];
  const caller = {
    async decide() {
      const error = new Error("fixture provider failed");
      error.providerReceipt = {
        attemptedProvider: "fixture-cli",
        attemptedModel: "fixture-model",
        attemptedReasoningEffort: "medium",
        attemptedRequestId: packet.requestId
      };
      throw error;
    }
  };
  const policy = new CliBackedPlayerPolicy(profile, caller, {
    fallback: new WeightedPlayerPolicy(profile),
    backendId: "fixture-cli",
    model: "fixture-model",
    requireLlm: true
  });
  await assert.rejects(
    () => policy.decide(packet),
    /Required LLM decision failed: fixture provider failed/
  );
});
