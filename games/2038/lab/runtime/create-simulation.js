import { readFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SelectedRulesMatch } from "../environment/selected-rules-match.js";
import {
  loadPlayerProfiles,
  validatePlayerProfile
} from "../personas/player-profile.js";
import {
  createPlayerPolicy,
  validatePolicyBackend
} from "../policies/policy-factory.js";
import { validatePolicyTreatment } from "../policies/weighted-policy.js";
import { runMonteCarlo } from "../runner/monte-carlo-runner.js";
import { effectiveRulesVariant } from "../environment/rules-variant.js";
import { DecisionCache } from "../policies/decision-cache.js";
import {
  assertLaunchIdentity,
  createLaunchIdentity,
  createReportIdentity,
  loadGameIdentity,
  projectRoot
} from "../versioning/game-identity.js";
import {
  evaluateTournamentBalance,
  loadBalanceContract
} from "../balance/balance-contract.js";
import { runDeterministicChunks } from "./deterministic-chunk-scheduler.js";
import { throwIfAborted } from "../cancellation.js";
import { archiveSimulationReport } from "../report-archive.js";

const configUrl = new URL("../../dist/runtime/game-config.json", import.meta.url);
const factionsUrl = new URL("../../dist/runtime/factions.json", import.meta.url);
const headlinesUrl = new URL("../../dist/runtime/headlines.json", import.meta.url);
const escalationsUrl = new URL("../../dist/runtime/escalations.json", import.meta.url);
const tacticsUrl = new URL("../../dist/runtime/tactics.json", import.meta.url);
const mandatesUrl = new URL("../../dist/runtime/mandates.json", import.meta.url);
const objectivesUrl = new URL("../../dist/runtime/secret-objectives.json", import.meta.url);
const execFileAsync = promisify(execFile);

async function providerProvenance(backends, models, reasoningEfforts) {
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
        models: [...new Set(models.filter(Boolean))],
        reasoningEfforts: [...new Set(reasoningEfforts.filter(Boolean))]
      };
    } catch (error) {
      return {
        provider,
        command: provider,
        version: null,
        models: [...new Set(models.filter(Boolean))],
        reasoningEfforts: [...new Set(reasoningEfforts.filter(Boolean))],
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

function decisionBudget(value, fallback, label) {
  if (value === undefined || value === null || value === "unlimited") return fallback;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new RangeError(`${label} must be a non-negative integer or "unlimited".`);
  }
  return parsed;
}

function simulationProjection(value) {
  const projection = value || "rich";
  if (!["rich", "batch"].includes(projection)) {
    throw new TypeError(`Unknown simulation projection: ${projection}.`);
  }
  return projection;
}

function resolveSimulationConfiguration(options, { config, availableProfiles }) {
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
  const profileIds = options.profileIds?.length
    ? options.profileIds
    : profiles.slice(0, playerCount).map((profile) => profile.id);
  const selectedProfiles = Array.from({ length: playerCount }, (_, seat) => {
    const id = profileIds[seat % profileIds.length];
    const profile = profiles.find((candidate) => candidate.id === id);
    if (!profile) throw new TypeError(`Unknown player profile: ${id}.`);
    return profile;
  });
  if (
    options.promptAddenda !== undefined &&
    (!Array.isArray(options.promptAddenda) ||
      options.promptAddenda.length !== playerCount)
  ) {
    throw new RangeError(
      `promptAddenda must provide exactly ${playerCount} seat entries.`
    );
  }
  const promptedProfiles = selectedProfiles.map((profile, seat) => {
    const addendum = options.promptAddenda?.[seat];
    if (addendum === null || addendum === undefined) return profile;
    if (typeof addendum !== "string" || addendum.trim().length === 0) {
      throw new TypeError(
        `promptAddenda seat ${seat} must be a non-empty string or null.`
      );
    }
    const prompted = structuredClone(profile);
    prompted.strategy.objectives = [
      ...(prompted.strategy.objectives || []),
      `Experimental decision guidance: ${addendum.trim()}`
    ];
    return prompted;
  });
  const backends = options.backends?.length
    ? options.backends
    : promptedProfiles.map((profile) => profile.defaultBackend || "weighted");
  const configuredBackends = Array.from({ length: playerCount }, (_, seat) =>
    backends[seat % backends.length]
  );
  for (const backend of configuredBackends) validatePolicyBackend(backend);
  if (
    options.policyTreatments !== undefined &&
    (!Array.isArray(options.policyTreatments) ||
      options.policyTreatments.length !== playerCount)
  ) {
    throw new RangeError(
      `policyTreatments must provide exactly ${playerCount} seat entries.`
    );
  }
  const policyTreatments = Array.from({ length: playerCount }, (_, seat) =>
    validatePolicyTreatment(options.policyTreatments?.[seat] ?? null)
  );
  const isLlmBackend = (backend) => !["weighted", "greedy"].includes(backend);
  const models = Array.from({ length: playerCount }, (_, seat) =>
    isLlmBackend(configuredBackends[seat])
      ? options.models?.[seat % options.models.length] || options.model || null
      : null
  );
  const reasoningEfforts = Array.from({ length: playerCount }, (_, seat) =>
    isLlmBackend(configuredBackends[seat])
      ? options.reasoningEfforts?.[seat % options.reasoningEfforts.length] ||
        options.reasoningEffort || null
      : null
  );
  return {
    playerCount,
    profiles,
    selectedProfiles: promptedProfiles,
    configuredBackends,
    policyTreatments,
    models,
    reasoningEfforts
  };
}

export async function captureSimulationLaunchIdentity(options = {}) {
  const [config, availableProfiles] = await Promise.all([
    readFile(configUrl, "utf8").then(JSON.parse),
    loadPlayerProfiles()
  ]);
  const {
    selectedProfiles,
    configuredBackends,
    policyTreatments,
    models,
    reasoningEfforts
  } = resolveSimulationConfiguration(options, { config, availableProfiles });
  const projection = simulationProjection(options.projection);
  const resolvedRulesVariant = effectiveRulesVariant(config, options.rulesVariant);
  return createLaunchIdentity(await loadGameIdentity({
    rulesVariant: resolvedRulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends: configuredBackends,
    model: models,
    reasoningEffort: reasoningEfforts,
    policyProjection: projection,
    experimentKind: options.experimentKind || "tournament",
    experimentConfiguration: {
      scenario: options.scenario || null,
      policyTreatments
    }
  }));
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
  throwIfAborted(options.signal);
  const [
    config,
    factionDocument,
    headlineDocument,
    escalationDocument,
    tacticDocument,
    mandateDocument,
    objectiveDocument,
    availableProfiles,
    balanceContract
  ] = await Promise.all([
    readFile(configUrl, "utf8").then(JSON.parse),
    readFile(factionsUrl, "utf8").then(JSON.parse),
    readFile(headlinesUrl, "utf8").then(JSON.parse),
    readFile(escalationsUrl, "utf8").then(JSON.parse),
    readFile(tacticsUrl, "utf8").then(JSON.parse),
    readFile(mandatesUrl, "utf8").then(JSON.parse),
    readFile(objectivesUrl, "utf8").then(JSON.parse),
    loadPlayerProfiles(),
    loadBalanceContract()
  ]);
  const {
    playerCount,
    selectedProfiles,
    configuredBackends,
    policyTreatments,
    models,
    reasoningEfforts
  } = resolveSimulationConfiguration(options, { config, availableProfiles });
  const projection = simulationProjection(options.projection);
  const runs = boundedInteger(options.runs, 100, 1, 10000, "runs");
  const runOffset = boundedInteger(
    options.runOffset,
    0,
    0,
    10000000,
    "runOffset"
  );
  const sampleReplays = boundedInteger(options.sampleReplays, 3, 0, 10, "sampleReplays");
  const isLlmBackend = (backend) => !["weighted", "greedy"].includes(backend);
  const llmRequested = configuredBackends.some(isLlmBackend);
  if (projection === "batch" && llmRequested) {
    throw new Error("Batch projection supports deterministic policies only.");
  }
  const requireLlm = Boolean(options.requireLlm);
  if (llmRequested && !options.allowLlm) {
    throw new Error("LLM-backed simulation requires explicit allowLlm authorization.");
  }
  if (requireLlm && !llmRequested) {
    throw new Error("requireLlm requires at least one LLM-backed policy.");
  }

  const maximumLlmDecisions = decisionBudget(
    options.maxLlmDecisions,
    llmRequested ? null : 0,
    "maxLlmDecisions"
  );
  const maximumLlmDecisionsPerSeatCycle =
    llmRequested && maximumLlmDecisions !== 0
      ? decisionBudget(
        options.maxLlmDecisionsPerSeatCycle,
        null,
        "maxLlmDecisionsPerSeatCycle"
      )
      : null;
  const decisionBudgets = configuredBackends.map(() => ({
    maximum: maximumLlmDecisions,
    remaining: maximumLlmDecisions ?? Infinity,
    used: 0,
    maxPerSeatCycle: maximumLlmDecisionsPerSeatCycle,
    perSeatCycleUsage: new Map()
  }));
  const usedLlmDecisions = () => decisionBudgets.reduce(
    (total, budget) => total + budget.used,
    0
  );
  const seatCycleUsage = () => Object.assign(
    {},
    ...decisionBudgets.map((budget) => Object.fromEntries(budget.perSeatCycleUsage))
  );
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
  const cliProviders = await providerProvenance(configuredBackends, models, reasoningEfforts);
  const resolvedRulesVariant = effectiveRulesVariant(config, options.rulesVariant);
  const decisionIdentity = await loadGameIdentity({
    rulesVariant: resolvedRulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends: configuredBackends,
    model: models,
    reasoningEffort: reasoningEfforts,
    policyProjection: projection,
    experimentKind: options.experimentKind || "tournament",
    experimentConfiguration: {
      scenario: options.scenario || null,
      policyTreatments
    }
  });
  const launchIdentity = assertLaunchIdentity(
    options.launchIdentity,
    decisionIdentity,
    "Simulation"
  );
  const policies = selectedProfiles.map((profile, seat) =>
    createPlayerPolicy(profile, configuredBackends[seat], {
      allowLlm: Boolean(options.allowLlm),
      decisionBudget: decisionBudgets[seat],
      model: models[seat],
      reasoningEffort: reasoningEfforts[seat],
      signal: options.signal,
      requireLlm,
      strictLlmEvidence: Boolean(options.strictLlmEvidence),
      timeoutMs: options.timeoutMs,
      callerFactory: options.callerFactory,
      callerOptions: options.llmCallerOptions,
      shortlistSize: options.shortlistSize,
      policyTreatment: policyTreatments[seat],
      decisionCache,
      cacheMode,
      llmStages: options.llmStages
    })
  );
  const seed = String(options.seed || "frontier-monte-carlo");
  const completedLlmArchives = [];
  const archiveCompletedLlmMatch = llmRequested && options.archiveLlmMatches !== false
    ? async ({ runIndex, outcome }) => {
      const immediateReport = await createReportIdentity({
        report: {
          schemaVersion: 6,
          reportSchemaVersion: 6,
          reportType: "tournament",
          evidenceLabel: "simulation",
          evidenceType: "simulation",
          generatedAt: new Date().toISOString(),
          seed: `${seed}:run:${runIndex}`,
          runs: 1,
          playerCount,
          scope: outcome.scope,
          game: decisionIdentity.game,
          engine: decisionIdentity.engine,
          variant: decisionIdentity.variant,
          strategies: decisionIdentity.strategies,
          launchIdentity,
          configuration: {
            backends: configuredBackends,
            model: options.model || null,
            reasoningEffort: options.reasoningEffort || null,
            llmEvidenceMode: options.strictLlmEvidence ? "strict_quarantine" : "required",
            projection
          },
          rulesVariant: outcome.rulesVariant,
          standings: outcome.standings,
          winnerSeats: outcome.winnerSeats,
          matchMetrics: outcome.matchMetrics,
          worldEnding: outcome.worldEnding,
          samples: [outcome]
        },
        identity: decisionIdentity,
        rulesVariant: outcome.rulesVariant,
        variantOverlay: options.rulesVariant,
        profiles: selectedProfiles,
        backends: configuredBackends,
        model: models,
        reasoningEffort: reasoningEfforts,
        policyProjection: projection,
        experimentKind: options.experimentKind || "tournament"
      });
      const archive = await archiveSimulationReport(immediateReport, {
        projectRoot: options.archiveProjectRoot || projectRoot,
        directory: options.archiveDirectory || "evidence/studies/simulation",
        jobId: `llm-match-${runIndex}`,
        canPublish: () => !options.signal?.aborted
      });
      completedLlmArchives.push({ runIndex, ...archive });
    }
    : null;
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
  const chunked = !llmRequested && !options.returnOutcomes &&
    (projection === "batch" || options.workers !== undefined)
    ? await runDeterministicChunks({
      options: {
        ...options,
        runs,
        playerCount,
        projection,
        sampleReplays,
        includeObservations: Boolean(options.includeObservations),
        seed
      },
      launchIdentity,
      onProgress
    })
    : null;
  const runResult = chunked?.report || await runMonteCarlo({
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
        configuredBackends[(seat + profileOffset) % playerCount]
      );
      const rotatedModels = selectedProfiles.map((_, seat) =>
        models[(seat + profileOffset) % playerCount]
      );
      const rotatedReasoningEfforts = selectedProfiles.map((_, seat) =>
        reasoningEfforts[(seat + profileOffset) % playerCount]
      );
      return (
      new SelectedRulesMatch({
        config,
        factions: rotatedFactions,
        profiles: rotatedProfiles,
        backends: rotatedBackends,
        models: rotatedModels,
        reasoningEfforts: rotatedReasoningEfforts,
        headlines: headlineDocument,
        escalations: escalationDocument,
        tactics: tacticDocument,
        mandates: mandateDocument,
        objectives: objectiveDocument,
        seed: matchSeed,
        playerCount,
        recordReplay,
        projection,
        rulesVariant: resolvedRulesVariant,
        mandateMode: options.mandateMode || "variable",
        simulateNegotiation: Boolean(options.simulateNegotiation),
        scenario: options.scenario || null,
        decisionContext: {
          schemaVersion: decisionIdentity.contracts.decisionSchemaVersion,
          game: {
            version: decisionIdentity.game.version,
            rulesetFingerprint: decisionIdentity.game.rulesetFingerprint,
            engineFingerprint: decisionIdentity.engine.fingerprint,
            variantFingerprint: decisionIdentity.variant.fingerprint
          }
        },
        signal: options.signal,
        onProgress: (progress) => onProgress?.({
          phase: "match_progress",
          run: runIndex + 1,
          runs,
          llmDecisionsUsed: usedLlmDecisions(),
          ...progress
        })
      })
      );
    },
    includeObservations: Boolean(options.includeObservations),
    projection,
    runOffset,
    sampleReplaysGlobal: Boolean(options.sampleReplaysGlobal),
    returnOutcomes: Boolean(options.returnOutcomes),
    signal: options.signal,
    onCompletedOutcome: archiveCompletedLlmMatch
  });
  const report = options.returnOutcomes ? runResult.report : runResult;
  const historicalPlayerCount = config.players.historicalOnlyCounts.includes(playerCount);
  const playerCountStatus = historicalPlayerCount
    ? "exploratory_nonpromotional"
    : "suggested_balance_scope";

  const completedReport = {
    ...report,
    scope: historicalPlayerCount ? {
      ...report.scope,
      id: `${report.scope.id}-exploratory-${playerCount}p`,
      verdictBoundary: `${report.scope.verdictBoundary} This ${playerCount}-player report is an exploratory, non-promotional diagnostic; only three-, four-, and five-player evidence is eligible for the current balance contract.`
    } : report.scope,
    reportType: options.reportType || report.reportType,
    ...(options.preRegistration ? {
      preRegistration: structuredClone(options.preRegistration)
    } : {}),
    launchIdentity,
    configuration: {
      profileIds: selectedProfiles.map((profile) => profile.id),
      backends: configuredBackends,
      policyTreatments,
      llmAuthorized: Boolean(options.allowLlm),
      llmEvidenceMode: llmRequested
        ? options.strictLlmEvidence
          ? "strict_quarantine"
          : requireLlm ? "required" : "fallback_allowed"
        : "not_requested",
      maxLlmDecisions: maximumLlmDecisions,
      llmDecisionBudgetScope: "per_configured_policy",
      totalLlmDecisionBudget: configuredBackends.filter(isLlmBackend).length *
        maximumLlmDecisions,
      usedLlmDecisions: usedLlmDecisions(),
      maxLlmDecisionsPerSeatCycle: maximumLlmDecisionsPerSeatCycle,
      llmDecisionsBySeatCycle: seatCycleUsage(),
      model: options.model || null,
      reasoningEffort: options.reasoningEffort || null,
      players: selectedProfiles.map((profile, seat) => ({
        seat,
        profileId: profile.id,
        backendId: configuredBackends[seat],
        policyTreatment: policyTreatments[seat],
        model: models[seat],
        reasoningEffort: reasoningEfforts[seat]
      })),
      playerCountStatus,
      factionPoolIds: factions.map((faction) => faction.id),
      factionIds: explicitFactions?.map((faction) => faction.id) || null,
      mandateMode: options.mandateMode || "variable",
      simulateNegotiation: Boolean(options.simulateNegotiation),
      scenario: options.scenario || null,
      cliProviders,
      llmCacheMode: cacheMode,
      llmCacheDirectory: options.llmCacheDirectory || null,
      preRegistrationId: options.preRegistrationId || null,
      llmStages: options.llmStages || null,
      runOffset,
      projection,
      completedLlmArchives,
      execution: chunked?.execution || {
        scheduler: "inline",
        requestedWorkers: Number(options.workers || 1),
        workers: 1,
        chunkSize: null,
        chunks: 1
      }
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
  const finalIdentity = await loadGameIdentity({
    rulesVariant: completedReport.rulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends: completedReport.configuration.backends,
    model: models,
    reasoningEffort: reasoningEfforts,
    policyProjection: projection,
    experimentKind: options.experimentKind || "tournament",
    experimentConfiguration: {
      scenario: options.scenario || null,
      policyTreatments
    }
  });
  assertLaunchIdentity(launchIdentity, finalIdentity, "Completed simulation");
  const identifiedReport = await createReportIdentity({
    report: completedReport,
    identity: finalIdentity,
    rulesVariant: completedReport.rulesVariant,
    variantOverlay: options.rulesVariant,
    profiles: selectedProfiles,
    backends: completedReport.configuration.backends,
    model: models,
    reasoningEffort: reasoningEfforts,
    policyProjection: projection,
    experimentKind: options.experimentKind || "tournament"
  });
  return options.returnOutcomes
    ? { report: identifiedReport, outcomes: runResult.rawOutcomes }
    : identifiedReport;
}
