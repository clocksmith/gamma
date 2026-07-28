import { ClaudeCliCaller, CodexCliCaller } from "../callers/index.js";
import { CliBackedPlayerPolicy, HybridPlayerPolicy } from "./cli-backed-policy.js";
import { WeightedPlayerPolicy } from "./weighted-policy.js";

export function createPlayerPolicy(profile, backend = profile.defaultBackend || "weighted", options = {}) {
  if (backend === "weighted" || backend === "greedy") {
    return new WeightedPlayerPolicy(profile, { selection: backend });
  }
  if (!options.allowLlm) {
    throw new Error(`Backend ${backend} requires --allow-llm.`);
  }

  const fallback = new WeightedPlayerPolicy(profile);
  const callerOptions = {
    model: options.model,
    timeoutMs: options.timeoutMs
  };
  const isClaude = backend.includes("claude");
  const caller = isClaude
    ? new ClaudeCliCaller(callerOptions)
    : new CodexCliCaller(callerOptions);
  const shared = {
    fallback,
    decisionBudget: options.decisionBudget,
    decisionCache: options.decisionCache,
    cacheMode: options.cacheMode,
    backendId: backend,
    model: options.model,
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
