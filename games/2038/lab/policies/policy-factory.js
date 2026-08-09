import { ClaudeCliCaller, CodexCliCaller } from "../callers/index.js";
import { CliBackedPlayerPolicy, HybridPlayerPolicy } from "./cli-backed-policy.js";
import {
  validatePolicyTreatment,
  WeightedPlayerPolicy
} from "./weighted-policy.js";

export const supportedPolicyBackends = new Set([
  "weighted",
  "greedy",
  "claude",
  "codex",
  "hybrid-claude",
  "hybrid-codex"
]);

export function validatePolicyBackend(backend) {
  if (!supportedPolicyBackends.has(backend)) {
    throw new TypeError(`Unknown player-policy backend: ${backend}.`);
  }
  return backend;
}

export function createPlayerPolicy(profile, backend = profile.defaultBackend || "weighted", options = {}) {
  validatePolicyBackend(backend);
  if (backend === "weighted" || backend === "greedy") {
    return new WeightedPlayerPolicy(profile, {
      selection: backend,
      treatment: validatePolicyTreatment(options.policyTreatment),
      rosterProfileIds: options.rosterProfileIds
    });
  }
  if (options.policyTreatment) {
    throw new TypeError("Deterministic policy treatments cannot be applied to LLM backends.");
  }
  if (!options.allowLlm) {
    throw new Error(`Backend ${backend} requires --allow-llm.`);
  }

  const fallback = new WeightedPlayerPolicy(profile, {
    rosterProfileIds: options.rosterProfileIds
  });
  const callerOptions = {
    ...(options.callerOptions || {}),
    model: options.model,
    reasoningEffort: options.reasoningEffort,
    timeoutMs: options.timeoutMs
  };
  const isClaude = backend.includes("claude");
  const caller = options.callerFactory
    ? options.callerFactory({
        backend,
        provider: isClaude ? "claude" : "codex",
        model: options.model,
        reasoningEffort: options.reasoningEffort,
        timeoutMs: options.timeoutMs,
        callerOptions: options.callerOptions || {}
      })
    : isClaude
      ? new ClaudeCliCaller(callerOptions)
      : new CodexCliCaller(callerOptions);
  const shared = {
    fallback,
    decisionBudget: options.decisionBudget,
    decisionCache: options.decisionCache,
    cacheMode: options.cacheMode,
    backendId: backend,
    model: options.model,
    reasoningEffort: options.reasoningEffort,
    signal: options.signal,
    requireLlm: Boolean(options.requireLlm),
    strictLlmEvidence: Boolean(options.strictLlmEvidence),
    llmStages: options.llmStages
  };
  return backend.startsWith("hybrid-")
    ? new HybridPlayerPolicy(profile, caller, {
        ...shared,
        shortlistSize: options.shortlistSize
      })
    : new CliBackedPlayerPolicy(profile, caller, shared);
}

export { CliBackedPlayerPolicy, HybridPlayerPolicy, WeightedPlayerPolicy };
