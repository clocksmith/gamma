import { readFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SelectedRulesMatch } from "../environment/selected-rules-match.js";
import {
  loadPlayerProfiles,
  validatePlayerProfile
} from "../personas/player-profile.js";
import { createPlayerPolicy } from "../policies/policy-factory.js";
import { runMonteCarlo } from "../runner/monte-carlo-runner.js";
import { effectiveRulesVariant } from "../environment/rules-variant.js";
import { DecisionCache } from "../policies/decision-cache.js";
import {
  createReportIdentity,
  loadGameIdentity
} from "../versioning/game-identity.js";
import {
  evaluateTournamentBalance,
  loadBalanceContract
} from "../balance/balance-contract.js";

const configUrl = new URL("../../data/game-config.json", import.meta.url);
const factionsUrl = new URL("../../data/factions.json", import.meta.url);
const headlinesUrl = new URL("../../data/headlines.json", import.meta.url);
const wildActionsUrl = new URL("../../data/wild-actions.json", import.meta.url);
const tacticsUrl = new URL("../../data/tactics.json", import.meta.url);
const mandatesUrl = new URL("../../data/mandates.json", import.meta.url);
const objectivesUrl = new URL("../../data/secret-objectives.json", import.meta.url);
const execFileAsync = promisify(execFile);

async function providerProvenance(backends, model) {
  const providers = [...new Set(backends.filter((backend) =>
    !["weighted", "greedy"].includes(backend)
  ).map((backend) => backend.includes("claude") ? "claude" : "codex"))];
  return Promise.all(providers.map(async (provider) => {
    try {
      const { stdout, stderr } = await execFileAsync(provider, ["--version"], {
        timeout: 10000
      });
      return {
        provider,
        command: provider,
        version: `${stdout}${stderr}`.trim(),
        model: model || null
      };
    } catch (error) {
      return {
        provider,
        command: provider,
        version: null,
        model: model || null,
        versionError: error.message
      };
    }
  }));
}

function boundedInteger(value, fallback, minimum, maximum, label) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return parsed;
}

export function factionRosterForRun(factions, playerCount, runIndex, rotate = true) {
  if (!rotate) return factions.slice(0, playerCount);
  const poolStart = runIndex % factions.length;
  const seatShift = Math.floor(runIndex / factions.length) % playerCount;
  return Array.from({ length: playerCount }, (_, seat) =>
    factions[(poolStart + ((seat + seatShift) % playerCount)) % factions.length]
  );
}

export async function createSimulation(options = {}, onProgress) {
  const [
    config,
    factionDocument,
    headlineDocument,
    wildActionDocument,
    tacticDocument,
    mandateDocument,
    objectiveDocument,
    availableProfiles,
    balanceContract
  ] = await Promise.all([
    readFile(configUrl, "utf8").then(JSON.parse),
    readFile(factionsUrl, "utf8").then(JSON.parse),
    readFile(headlinesUrl, "utf8").then(JSON.parse),
    readFile(wildActionsUrl, "utf8").then(JSON.parse),
    readFile(tacticsUrl, "utf8").then(JSON.parse),
    readFile(mandatesUrl, "utf8").then(JSON.parse),
    readFile(objectivesUrl, "utf8").then(JSON.parse),
    loadPlayerProfiles(),
    loadBalanceContract()
  ]);
  const profileOverrides = new Map(
    (options.profileOverrides || []).map((profile) => {
      validatePlayerProfile(profile);
      return [profile.id, structuredClone(profile)];
    })
  );
  const profiles = availableProfiles.map((profile) =>
    profileOverrides.get(profile.id) || profile
  );
  for (const [id, profile] of profileOverrides) {
    if (!profiles.some((candidate) => candidate.id === id)) profiles.push(profile);
  }
  const playerCount = boundedInteger(
    options.playerCount,
    4,
    config.players.min,
    config.players.max,
    "playerCount"
  );
  const runs = boundedInteger(options.runs, 100, 1, 10000, "runs");
  const runOffset = boundedInteger(
    options.runOffset,
    0,
    0,
    10000000,
    "runOffset"
  );
  const sampleReplays = boundedInteger(options.sampleReplays, 3, 0, 10, "sampleReplays");
  const profileIds = options.profileIds?.length
    ? options.profileIds
    : profiles.slice(0, playerCount).map((profile) => profile.id);
  const selectedProfiles = Array.from({ length: playerCount }, (_, seat) => {
    const id = profileIds[seat % profileIds.length];
    const profile = profiles.find((candidate) => candidate.id === id);
    if (!profile) throw new TypeError(`Unknown player profile: ${id}.`);
    return profile;
  });
  const backends = options.backends?.length
    ? options.backends
    : selectedProfiles.map((profile) => profile.defaultBackend || "weighted");
  const llmRequested = backends.some(
    (backend) => !["weighted", "greedy"].includes(backend)
  );
  if (llmRequested && !options.allowLlm) {
    throw new Error("LLM-backed simulation requires explicit allowLlm authorization.");
  }

  const maximumLlmDecisions = boundedInteger(
    options.maxLlmDecisions,
    llmRequested ? 24 : 0,
    0,
    10000,
    "maxLlmDecisions"
  );
  const decisionBudget = { remaining: maximumLlmDecisions };
  const cacheMode = options.llmCacheMode || "off";
  if (!["off", "read-only", "read-write", "write-only"].includes(cacheMode)) {
    throw new TypeError(`Unknown LLM cache mode: ${cacheMode}.`);
  }
  const decisionCache = options.llmCacheDirectory
    ? new DecisionCache(options.llmCacheDirectory)
    : null;
  if (cacheMode !== "off" && !decisionCache) {
    throw new TypeError("LLM cache mode requires llmCacheDirectory.");
  }
  const cliProviders = await providerProvenance(backends, options.model || null);
  const resolvedRulesVariant = effectiveRulesVariant(config, options.rulesVariant);
  const decisionIdentity = await loadGameIdentity({
    rulesVariant: resolvedRulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends,
    model: options.model || null,
    experimentKind: options.experimentKind || "tournament"
  });
  const policies = selectedProfiles.map((profile, seat) =>
    createPlayerPolicy(profile, backends[seat % backends.length], {
      allowLlm: Boolean(options.allowLlm),
      decisionBudget,
      model: options.model,
      timeoutMs: options.timeoutMs,
      shortlistSize: options.shortlistSize,
      decisionCache,
      cacheMode,
      llmStages: options.llmStages
    })
  );
  const seed = String(options.seed || "frontier-monte-carlo");
  const factions = factionDocument.factions;
  const explicitFactions = options.factionIds?.length
    ? options.factionIds.map((id) => {
      const faction = factions.find((candidate) => candidate.id === id);
      if (!faction) throw new TypeError(`Unknown faction: ${id}.`);
      return faction;
    })
    : null;
  if (explicitFactions && explicitFactions.length !== playerCount) {
    throw new RangeError("Explicit factionIds must provide exactly one faction per seat.");
  }
  if (explicitFactions && new Set(explicitFactions.map((faction) => faction.id)).size !== playerCount) {
    throw new RangeError("Explicit factionIds cannot repeat a faction.");
  }
  const report = await runMonteCarlo({
    runs,
    seed,
    policies,
    policiesForRun: (runIndex) => {
      if (options.rotateProfiles === false) return policies;
      const offset = (runIndex + runOffset) % playerCount;
      return policies.map((_, seat) => policies[(seat + offset) % playerCount]);
    },
    sampleReplays,
    onProgress,
    createMatch: ({ seed: matchSeed, recordReplay, runIndex }) => {
      const globalRunIndex = runIndex + runOffset;
      const profileOffset = options.rotateProfiles === false
        ? 0
        : globalRunIndex % playerCount;
      const rotatedFactions = explicitFactions || factionRosterForRun(
        factions,
        playerCount,
        globalRunIndex,
        options.rotateFactions !== false
      );
      const rotatedProfiles = selectedProfiles.map((_, seat) =>
        selectedProfiles[(seat + profileOffset) % playerCount]
      );
      const rotatedBackends = selectedProfiles.map((_, seat) =>
        backends[(seat + profileOffset) % playerCount]
      );
      return (
      new SelectedRulesMatch({
        config,
        factions: rotatedFactions,
        profiles: rotatedProfiles,
        backends: rotatedBackends,
        headlines: headlineDocument,
        wildActions: wildActionDocument,
        tactics: tacticDocument,
        mandates: mandateDocument,
        objectives: objectiveDocument,
        seed: matchSeed,
        playerCount,
        recordReplay,
        rulesVariant: resolvedRulesVariant,
        mandateMode: options.mandateMode || "variable",
        simulateNegotiation: Boolean(options.simulateNegotiation),
        decisionContext: {
          schemaVersion: decisionIdentity.contracts.decisionSchemaVersion,
          game: {
            version: decisionIdentity.game.version,
            rulesetFingerprint: decisionIdentity.game.rulesetFingerprint,
            engineFingerprint: decisionIdentity.engine.fingerprint,
            variantFingerprint: decisionIdentity.variant.fingerprint
          }
        }
      })
      );
    },
    includeObservations: Boolean(options.includeObservations)
  });

  const completedReport = {
    ...report,
    reportType: options.reportType || report.reportType,
    ...(options.preRegistration ? {
      preRegistration: structuredClone(options.preRegistration)
    } : {}),
    configuration: {
      profileIds: selectedProfiles.map((profile) => profile.id),
      backends: selectedProfiles.map((_, seat) => backends[seat % backends.length]),
      llmAuthorized: Boolean(options.allowLlm),
      maxLlmDecisions: maximumLlmDecisions,
      usedLlmDecisions: maximumLlmDecisions - decisionBudget.remaining,
      model: options.model || null,
      factionPoolIds: factions.map((faction) => faction.id),
      factionIds: explicitFactions?.map((faction) => faction.id) || null,
      mandateMode: options.mandateMode || "variable",
      simulateNegotiation: Boolean(options.simulateNegotiation),
      cliProviders,
      llmCacheMode: cacheMode,
      llmCacheDirectory: options.llmCacheDirectory || null,
      preRegistrationId: options.preRegistrationId || null,
      llmStages: options.llmStages || null,
      runOffset
    },
    balanceContract: {
      id: balanceContract.id,
      status: balanceContract.status,
      fingerprint: balanceContract.fingerprint,
      provenance: balanceContract.provenance
    },
    rulesVariant: report.samples[0]?.rulesVariant ||
      report.rulesVariant ||
      report.matchMetrics?.rulesVariant ||
      options.rulesVariant ||
      null
  };
  completedReport.balanceEvaluation = evaluateTournamentBalance(
    completedReport,
    balanceContract
  );
  return createReportIdentity({
    report: completedReport,
    rulesVariant: completedReport.rulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends: completedReport.configuration.backends,
    model: completedReport.configuration.model,
    experimentKind: options.experimentKind || "tournament"
  });
}
