import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { promisify } from "node:util";
import { relative, resolve } from "node:path";
import { createSimulation } from "../runtime/create-simulation.js";
import { fingerprintObject, projectRoot } from "../versioning/game-identity.js";

const execFileAsync = promisify(execFile);

async function registrationIdentity(path) {
  const relativePath = relative(projectRoot, path);
  if (
    relativePath.startsWith("..") ||
    !relativePath.startsWith("evidence/studies/simulation/preregistrations/")
  ) {
    throw new Error(
      "LLM holdout preregistration must live under evidence/studies/simulation/preregistrations/."
    );
  }
  await execFileAsync("git", ["ls-files", "--error-unmatch", relativePath], {
    cwd: projectRoot
  }).catch(() => {
    throw new Error("LLM holdout preregistration must be committed before execution.");
  });
  const { stdout } = await execFileAsync(
    "git",
    ["log", "-1", "--format=%H", "--", relativePath],
    { cwd: projectRoot }
  );
  return { path: relativePath, registrationCommit: stdout.trim() };
}

export function validateLlmHoldoutRegistration(document) {
  if (
    document.schemaVersion !== 1 ||
    document.locked !== true ||
    !["fresh_robustness", "cache_reproducibility"].includes(document.purpose) ||
    !Array.isArray(document.profileIds) ||
    document.profileIds.length !== document.playerCount ||
    !Array.isArray(document.backends) ||
    document.backends.length !== document.playerCount ||
    (document.llmStages !== null &&
      (!Array.isArray(document.llmStages) || !document.llmStages.length)) ||
    (document.maximumLlmDecisions !== null &&
      (!Number.isInteger(document.maximumLlmDecisions) ||
        document.maximumLlmDecisions < 1))
  ) {
    throw new TypeError("Invalid locked LLM holdout preregistration.");
  }
  if (!document.backends.some((backend) =>
    !["weighted", "greedy"].includes(backend)
  )) {
    throw new TypeError("LLM holdout requires at least one LLM-backed seat.");
  }
  if (document.purpose === "cache_reproducibility" && !document.cacheDirectory) {
    throw new TypeError("Cache reproducibility requires cacheDirectory.");
  }
  return document;
}

export async function runLlmNegotiationHoldout({
  preRegistrationPath,
  allowLlm = false,
  signal,
  onProgress
} = {}) {
  if (!allowLlm) {
    throw new Error("Fresh or cached LLM holdouts require explicit allowLlm authorization.");
  }
  if (!preRegistrationPath) {
    throw new TypeError("preRegistrationPath is required.");
  }
  const absolute = resolve(preRegistrationPath);
  const document = validateLlmHoldoutRegistration(
    JSON.parse(await readFile(absolute, "utf8"))
  );
  const identity = await registrationIdentity(absolute);
  const fingerprint = fingerprintObject(document);
  const cacheMode = document.purpose === "fresh_robustness"
    ? document.cacheDirectory
      ? "write-only"
      : "off"
    : "read-only";
  const preRegistration = {
    ...identity,
    id: document.id,
    purpose: document.purpose,
    fingerprint,
    analysis: document.analysis,
    locked: true
  };
  const report = await createSimulation({
    runs: document.runs,
    playerCount: document.playerCount,
    seed: document.seed,
    sampleReplays: 0,
    profileIds: document.profileIds,
    backends: document.backends,
    allowLlm: true,
    requireLlm: true,
    maxLlmDecisions: document.maximumLlmDecisions ?? undefined,
    model: document.model || undefined,
    reasoningEffort: document.reasoningEffort || undefined,
    llmStages: document.llmStages,
    strictLlmEvidence: true,
    llmCacheMode: cacheMode,
    llmCacheDirectory: document.cacheDirectory || undefined,
    preRegistrationId: document.id,
    preRegistration,
    reportType: "llm_negotiation_holdout",
    experimentKind: "llm_negotiation_holdout",
    simulateNegotiation: true,
    includeObservations: true,
    rotateProfiles: true,
    rotateFactions: true,
    signal
  }, onProgress);
  return {
    ...report,
    balanceEvaluation: {
      contractId: report.balanceContract.id,
      status: "llm_holdout_descriptive",
      checks: [],
      promotionGate: {
        eligible: false,
        automatedPass: false,
        sourceClean: report.provenance.sourceDirty === false,
        trackedReceipt: false,
        humanApproval: false,
        verdict: "must_compare_with_preregistered_deterministic_cells",
        reasons: [
          "An LLM holdout tests negotiation robustness only.",
          "A tracked receipt and explicit human approval remain mandatory."
        ]
      }
    }
  };
}
