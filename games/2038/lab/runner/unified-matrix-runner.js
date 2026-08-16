import { readFile } from "node:fs/promises";
import { availableParallelism } from "node:os";
import { performance } from "node:perf_hooks";
import { Worker } from "node:worker_threads";
import {
  empiricalBayesRates,
  intervalCrossesThreshold,
  precisionReached
} from "../statistics/sequential-inference.js";
import {
  loadPlayerProfiles,
  validatePlayerProfile
} from "../personas/player-profile.js";
import {
  captureSimulationLaunchIdentity,
  createSimulation
} from "../runtime/create-simulation.js";
import { createReportIdentity, fingerprintObject } from "../versioning/game-identity.js";
import { loadBalanceContract } from "../balance/balance-contract.js";
import {
  classifyWinningPath,
  WINNING_PATH_CLASSIFIER,
  winningPathMargin
} from "../balance/winning-path.js";
import { simulationCopy } from "../content/simulation-copy.js";
import { mutateStrategy } from "./optimization-runner.js";

const matrixUrl = new URL("../contracts/experiment-matrix.json", import.meta.url);
const cellWorkerUrl = new URL("./unified-matrix-cell-worker.js", import.meta.url);

function integer(value, fallback, minimum, maximum, label) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return parsed;
}

function matrixWorkerCount(value) {
  const fallback = Math.min(64, Math.max(1, availableParallelism() - 1));
  return integer(value, fallback, 1, 64, "workers");
}

function restoreWorkerError(value) {
  const error = new Error(value?.message || "Unified-matrix cell failed.");
  error.name = value?.name || "Error";
  error.stack = value?.stack || error.stack;
  if (value?.code) error.code = value.code;
  return error;
}

async function runMatrixCellTasks(tasks, { workers, signal }) {
  if (workers === 1 || tasks.length < 2) {
    const results = [];
    for (const task of tasks) {
      const started = performance.now();
      const report = await createSimulation({
        ...task.options,
        workers: 1,
        launchIdentity: task.launchIdentity
      });
      results.push({
        taskIndex: task.taskIndex,
        report,
        elapsedMs: Math.round(performance.now() - started)
      });
    }
    return results;
  }
  const actualWorkers = Math.min(workers, tasks.length);
  const pool = Array.from({ length: actualWorkers }, () => new Worker(cellWorkerUrl, {
    execArgv: process.execArgv.filter((argument) => !argument.startsWith("--input-type"))
  }));
  const results = Array(tasks.length);
  const active = new Map(pool.map((worker) => [worker, null]));
  let next = 0;
  let completed = 0;
  let settled = false;
  return new Promise((resolve, reject) => {
    const terminate = () => Promise.allSettled(pool.map((worker) => worker.terminate()));
    const finish = async (error, value) => {
      if (settled) return;
      settled = true;
      signal?.removeEventListener("abort", abort);
      await terminate();
      if (error) reject(error);
      else resolve(value);
    };
    const abort = () => finish(
      signal?.reason || new DOMException("Unified matrix was cancelled.", "AbortError")
    );
    const assign = (worker) => {
      if (settled || next >= tasks.length) return;
      const task = tasks[next++];
      active.set(worker, task);
      worker.postMessage({ kind: "unified_matrix_cell", ...task });
    };
    const receive = async (worker, message) => {
      const task = active.get(worker);
      if (
        settled ||
        message.kind !== "cell_result" ||
        !task ||
        message.taskIndex !== task.taskIndex
      ) {
        if (!settled) await finish(new Error("Unified matrix received a stale cell result."));
        return;
      }
      if (message.error) {
        await finish(restoreWorkerError(message.error));
        return;
      }
      results[task.taskIndex] = message;
      completed += 1;
      active.set(worker, null);
      if (completed === tasks.length) {
        await finish(null, results);
        return;
      }
      assign(worker);
    };
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) {
      abort();
      return;
    }
    for (const worker of pool) {
      worker.on("message", (message) => receive(worker, message));
      worker.on("error", (error) => finish(error));
      worker.on("exit", (code) => {
        if (!settled && active.get(worker)) {
          finish(new Error(`Unified-matrix worker exited early (code ${code}).`));
        }
      });
      assign(worker);
    }
  });
}

function mean(values) {
  return values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
}

function increment(target, key, amount = 1) {
  target[key] = (target[key] || 0) + amount;
}

function mergeAbilityTelemetry(target, source = {}) {
  for (const [key, value] of Object.entries(source)) {
    if (typeof value === "number") {
      target[key] = (Number(target[key]) || 0) + value;
    } else if (!(key in target)) {
      target[key] = structuredClone(value);
    } else if (target[key] !== value) {
      target[key] = [...new Set([].concat(target[key], value))];
    }
  }
}

function normalizedEntropy(counts) {
  const values = Object.values(counts).filter((value) => value > 0);
  const total = values.reduce((sum, value) => sum + value, 0);
  if (values.length < 2 || total === 0) return 0;
  const entropy = -values.reduce((sum, value) => {
    const probability = value / total;
    return sum + probability * Math.log(probability);
  }, 0);
  return entropy / Math.log(values.length);
}

function concentration(counts) {
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0);
  const top = Math.max(0, ...Object.values(counts));
  return {
    counts,
    observed: Object.keys(counts).length,
    entropy: normalizedEntropy(counts),
    topShare: total ? top / total : 0
  };
}

function range(values) {
  return values.length
    ? Math.max(...values) - Math.min(...values)
    : Number.NaN;
}

function observedCheck({
  id,
  value,
  operator,
  threshold,
  configurationId,
  playerCount
}) {
  const comparable = Number.isFinite(value);
  return {
    id,
    configurationId,
    playerCount,
    value: comparable ? value : null,
    operator,
    threshold,
    evidence: "observed_configuration_player_count",
    passed:
      comparable &&
      (operator === "max" ? value <= threshold : value >= threshold)
  };
}

export function configurationOutcomeBalanceChecks({
  configurationResults,
  configurationIds,
  playerCounts,
  thresholds
}) {
  const definitions = [
    {
      id: "seat_win_share_range",
      read: (outcomes) => outcomes.seatWinShareRange,
      operator: "max",
      threshold: thresholds.seatWinShareRangeMax
    },
    {
      id: "faction_win_share_range",
      read: (outcomes) => range(
        Object.values(outcomes.factionStandings || {})
          .filter((standing) => standing.appearances > 0)
          .map((standing) => standing.winShare)
      ),
      operator: "max",
      threshold: thresholds.factionWinShareRangeMax
    },
    {
      id: "profile_win_share_range",
      read: (outcomes) => outcomes.profileWinShareRange,
      operator: "max",
      threshold: thresholds.profileWinShareRangeMax
    },
    {
      id: "action_entropy",
      read: (outcomes) => outcomes.actionDiversity,
      operator: "min",
      threshold: thresholds.actionEntropyMin
    },
    {
      id: "opening_entropy",
      read: (outcomes) => outcomes.openingDiversity?.entropy,
      operator: "min",
      threshold: thresholds.openingEntropyMin
    },
    {
      id: "opening_top_share",
      read: (outcomes) => outcomes.openingDiversity?.topShare,
      operator: "max",
      threshold: thresholds.openingTopShareMax
    },
    {
      id: "winning_path_entropy",
      read: (outcomes) => outcomes.winningPathDiversity?.entropy,
      operator: "min",
      threshold: thresholds.winningPathEntropyMin
    },
    {
      id: "winning_path_top_share",
      read: (outcomes) => outcomes.winningPathDiversity?.topShare,
      operator: "max",
      threshold: thresholds.winningPathTopShareMax
    },
    {
      id: "policy_fallbacks",
      read: (outcomes) => outcomes.policyFallbacks,
      operator: "max",
      threshold: thresholds.policyFallbacksMax
    },
    {
      id: "forced_no_op_rate",
      read: (outcomes) => outcomes.forcedNoOpRate,
      operator: "max",
      threshold: thresholds.forcedNoOpRateMax
    }
  ];
  return configurationIds.flatMap((configurationId) =>
    playerCounts.flatMap((playerCount) => {
      const outcomes =
        configurationResults[configurationId]?.playerCountResults?.[playerCount]
          ?.outcomes || {};
      return definitions.map((definition) => observedCheck({
        id: `${configurationId}:p${playerCount}:${definition.id}`,
        value: definition.read(outcomes),
        operator: definition.operator,
        threshold: definition.threshold,
        configurationId,
        playerCount
      }));
    })
  );
}

function rotate(values, amount) {
  return values.map((_, index) => values[(index + amount) % values.length]);
}

function backendRegimes(playerCount) {
  return [
    {
      id: "homogeneous_weighted",
      backends: Array.from({ length: playerCount }, () => "weighted")
    },
    {
      id: "homogeneous_greedy",
      backends: Array.from({ length: playerCount }, () => "greedy")
    },
    {
      id: "alternating_weighted_first",
      backends: Array.from({ length: playerCount }, (_, seat) =>
        seat % 2 === 0 ? "weighted" : "greedy"
      )
    },
    {
      id: "alternating_greedy_first",
      backends: Array.from({ length: playerCount }, (_, seat) =>
        seat % 2 === 0 ? "greedy" : "weighted"
      )
    }
  ];
}

function buildCells({ profiles, playerCounts, rulesConfigurations, mandateModes }) {
  const cells = [];
  const rosterStarts = profiles.map((_, index) => index);
  for (const rules of rulesConfigurations) {
    for (const playerCount of playerCounts) {
      for (const mandateMode of mandateModes) {
        for (const backendRegime of backendRegimes(playerCount)) {
          for (const rosterStart of rosterStarts) {
            const roster = Array.from({ length: playerCount }, (_, seat) =>
              profiles[(rosterStart + seat) % profiles.length].id
            );
            const pairingId = [
              `p${playerCount}`,
              mandateMode,
              backendRegime.id,
              `r${rosterStart}`
            ].join(":");
            const id = [rules.id, pairingId].join(":");
            cells.push({
              id,
              pairingId,
              rulesConfigurationId: rules.id,
              rulesVariant: rules.overlay || {},
              playerCount,
              mandateMode,
              profileIds: roster,
              backendRegime: backendRegime.id,
              backends: backendRegime.backends,
              runs: 0
            });
          }
        }
      }
    }
  }
  return cells;
}

function studyIdentityBasis(identity) {
  return {
    game: identity.game,
    engine: identity.engine,
    contracts: identity.contracts,
    rng: identity.rng,
    provenance: identity.provenance
  };
}

async function captureCellLaunchIdentities({ cells, profiles, projection }) {
  let expected = null;
  for (const cell of cells) {
    const identity = await captureSimulationLaunchIdentity({
      playerCount: cell.playerCount,
      profileIds: cell.profileIds,
      profileOverrides: profiles,
      backends: cell.backends,
      rulesVariant: cell.rulesVariant,
      projection,
      experimentKind: "unified_matrix_audit"
    });
    const basis = studyIdentityBasis(identity);
    const fingerprint = fingerprintObject(basis);
    if (expected && expected.fingerprint !== fingerprint) {
      const error = new Error(
        "Unified-matrix source identity changed while cell launch identities were captured."
      );
      error.code = "study_launch_identity_mismatch";
      throw error;
    }
    expected ||= { ...basis, fingerprint };
    cell.launchIdentity = identity;
  }
  return expected;
}

function assertStudyIdentity(studyIdentity, identity, context) {
  const actual = fingerprintObject(studyIdentityBasis(identity));
  if (actual === studyIdentity.fingerprint) return;
  const error = new Error(`${context} source identity differs from the study launch snapshot.`);
  error.code = "study_launch_identity_mismatch";
  error.expectedStudyIdentity = studyIdentity.fingerprint;
  error.actualStudyIdentity = actual;
  throw error;
}

function groupKey(record, dimensions) {
  return dimensions.map((dimension) => `${dimension}=${record[dimension]}`).join("|");
}

function groupedWinCells(records, dimensions) {
  const groups = new Map();
  for (const record of records) {
    const id = groupKey(record, dimensions);
    const group = groups.get(id) || {
      id,
      dimensions: Object.fromEntries(dimensions.map((key) => [key, record[key]])),
      success: 0,
      exposure: 0,
      expected: 0
    };
    group.success += record.winCredit;
    group.exposure += 1;
    group.expected += 1 / record.playerCount;
    groups.set(id, group);
  }
  return [...groups.values()].map((group) => ({
    ...group,
    expected: group.expected / group.exposure
  }));
}

function inferenceFamilies(records, settings, look) {
  const definitions = {
    seat: ["rulesConfigurationId", "playerCount", "seat"],
    faction: ["rulesConfigurationId", "playerCount", "factionId"],
    strategy: ["rulesConfigurationId", "playerCount", "profileId"],
    backend: ["rulesConfigurationId", "playerCount", "backendId"],
    factionStrategy: [
      "rulesConfigurationId",
      "playerCount",
      "factionId",
      "profileId"
    ],
    factionBackend: [
      "rulesConfigurationId",
      "playerCount",
      "factionId",
      "backendId"
    ],
    strategyBackend: [
      "rulesConfigurationId",
      "playerCount",
      "profileId",
      "backendId"
    ],
    seatBackendRegime: [
      "rulesConfigurationId",
      "playerCount",
      "seat",
      "backendRegime"
    ],
    factionBackendRegime: [
      "rulesConfigurationId",
      "playerCount",
      "factionId",
      "backendRegime"
    ],
    strategyBackendRegime: [
      "rulesConfigurationId",
      "playerCount",
      "profileId",
      "backendRegime"
    ],
    factionStrategyBackendRegime: [
      "rulesConfigurationId",
      "playerCount",
      "factionId",
      "profileId",
      "backendRegime"
    ]
  };
  const raw = Object.fromEntries(Object.entries(definitions).map(([id, dimensions]) => [
    id,
    groupedWinCells(records, dimensions)
  ]));
  const familySize = Object.values(raw).reduce((sum, cells) => sum + cells.length, 0);
  return Object.fromEntries(Object.entries(raw).map(([id, cells]) => [
    id,
    empiricalBayesRates(cells, {
      alpha: settings.alpha,
      familySize: Math.max(1, familySize),
      look,
      minimumExposure: 1
    })
  ]));
}

function pairwiseInference(records, settings, look) {
  const cells = groupedWinCells(records, [
    "rulesConfigurationId",
    "playerCount",
    "backendRegime",
    "profileId",
    "opponentProfileId"
  ]);
  return empiricalBayesRates(cells, {
    alpha: settings.alpha,
    familySize: Math.max(1, cells.length),
    look,
    minimumExposure: 1
  });
}

function credibleMetaCycles(pairwise, {
  threshold = 0.55,
  minimumExposure
}) {
  const strata = [...new Map(pairwise.cells.map((cell) => {
    const configuration = cell.dimensions.rulesConfigurationId;
    const backendRegime = cell.dimensions.backendRegime;
    return [
      `${configuration}:${backendRegime}`,
      { rulesConfigurationId: configuration, backendRegime }
    ];
  })).values()].sort((left, right) =>
    left.rulesConfigurationId.localeCompare(right.rulesConfigurationId) ||
    left.backendRegime.localeCompare(right.backendRegime)
  );
  const ids = [...new Set(pairwise.cells.flatMap((cell) => [
    cell.dimensions.profileId,
    cell.dimensions.opponentProfileId
  ]))].sort();
  const edge = (stratum, left, right) => pairwise.cells.some((cell) =>
    cell.dimensions.rulesConfigurationId === stratum.rulesConfigurationId &&
    cell.dimensions.backendRegime === stratum.backendRegime &&
    cell.dimensions.profileId === left &&
    cell.dimensions.opponentProfileId === right &&
    cell.exposure >= minimumExposure &&
    cell.posteriorInterval.lower > threshold &&
    cell.confidenceSequence.lower > threshold
  );
  const cycles = [];
  for (const stratum of strata) {
    for (let a = 0; a < ids.length; a += 1) {
      for (let b = a + 1; b < ids.length; b += 1) {
        for (let c = b + 1; c < ids.length; c += 1) {
          const [x, y, z] = [ids[a], ids[b], ids[c]];
          if (edge(stratum, x, y) &&
              edge(stratum, y, z) &&
              edge(stratum, z, x)) {
            cycles.push({
              ...stratum,
              profiles: [x, y, z]
            });
          }
          if (edge(stratum, x, z) &&
              edge(stratum, z, y) &&
              edge(stratum, y, x)) {
            cycles.push({
              ...stratum,
              profiles: [x, z, y]
            });
          }
        }
      }
    }
  }
  return {
    threshold,
    minimumExposure,
    count: cycles.length,
    cycles
  };
}

function flattenGroups(families) {
  return Object.entries(families).flatMap(([familyId, family]) =>
    family.cells.map((cell) => ({ familyId, ...cell }))
  );
}

function cellAllocationScore(cell, groupedCounts, families) {
  const keys = [
    `rulesConfigurationId=${cell.rulesConfigurationId}`,
    `playerCount=${cell.playerCount}`,
    `mandateMode=${cell.mandateMode}`,
    `backendRegime=${cell.backendRegime}`,
    ...cell.profileIds.map((id) => `profileId=${id}`),
    ...cell.backends.map((id) => `backendId=${id}`)
  ];
  const scarcity = keys.reduce(
    (sum, key) => sum + 1 / Math.sqrt(1 + (groupedCounts.get(key) || 0)),
    0
  );
  const uncertainty = [
    ...(families.strategy?.cells || []).filter((entry) =>
      entry.dimensions.rulesConfigurationId === cell.rulesConfigurationId &&
      entry.dimensions.playerCount === cell.playerCount &&
      cell.profileIds.includes(entry.dimensions.profileId)
    ),
    ...(families.backend?.cells || []).filter((entry) =>
      entry.dimensions.rulesConfigurationId === cell.rulesConfigurationId &&
      entry.dimensions.playerCount === cell.playerCount &&
      cell.backends.includes(entry.dimensions.backendId)
    ),
    ...(families.strategyBackendRegime?.cells || []).filter((entry) =>
      entry.dimensions.rulesConfigurationId === cell.rulesConfigurationId &&
      entry.dimensions.playerCount === cell.playerCount &&
      entry.dimensions.backendRegime === cell.backendRegime &&
      cell.profileIds.includes(entry.dimensions.profileId)
    ),
    ...(families.factionBackendRegime?.cells || []).filter((entry) =>
      entry.dimensions.rulesConfigurationId === cell.rulesConfigurationId &&
      entry.dimensions.playerCount === cell.playerCount &&
      entry.dimensions.backendRegime === cell.backendRegime
    )
  ].reduce((sum, entry) => sum + entry.confidenceSequence.halfWidth, 0);
  return uncertainty * 4 + scarcity + 1 / Math.sqrt(1 + cell.runs);
}

function countCoverage(records) {
  const result = new Map();
  for (const record of records) {
    for (const [key, value] of Object.entries({
      playerCount: record.playerCount,
      rulesConfigurationId: record.rulesConfigurationId,
      mandateMode: record.mandateMode,
      backendRegime: record.backendRegime,
      profileId: record.profileId,
      backendId: record.backendId,
      factionId: record.factionId,
      seat: `${record.playerCount}:${record.seat}`
    })) {
      const id = `${key}=${value}`;
      result.set(id, (result.get(id) || 0) + 1);
    }
  }
  return result;
}

function cooperationSummary(observations) {
  const statuses = {};
  let emergentMatches = 0;
  let betrayalMatches = 0;
  let declarationsWithNecessarySupplier = 0;
  let suppliers = 0;
  let suppliersTopHalf = 0;
  for (const observation of observations) {
    const resolved = observation.negotiations.filter((entry) =>
      ["fulfilled", "broken", "superseded", "unexercised"].includes(entry.status)
    );
    for (const entry of resolved) statuses[entry.status] = (statuses[entry.status] || 0) + 1;
    if (resolved.some((entry) => entry.status === "fulfilled") ||
        observation.powerTrades.length) emergentMatches += 1;
    if (resolved.some((entry) => entry.status === "broken")) betrayalMatches += 1;
    const necessarySeats = new Set(observation.powerTrades
      .filter((entry) => entry.causallyNecessary)
      .map((entry) => entry.supplierSeat));
    if (observation.declarations > 0 && necessarySeats.size) {
      declarationsWithNecessarySupplier += 1;
    }
    const rankBySeat = new Map(
      [...observation.standings]
        .sort((left, right) => right.score - left.score)
        .map((entry, index) => [entry.seat, index + 1])
    );
    for (const seat of necessarySeats) {
      suppliers += 1;
      if ((rankBySeat.get(seat) || Infinity) <= Math.ceil(observation.standings.length / 2)) {
        suppliersTopHalf += 1;
      }
    }
  }
  return {
    statuses,
    emergentCooperationRate: observations.length ? emergentMatches / observations.length : 0,
    betrayalRate: observations.length ? betrayalMatches / observations.length : 0,
    declarationsWithNecessarySupplier,
    supplierCompetitiveRate: suppliers ? suppliersTopHalf / suppliers : null,
    supplierObservations: suppliers
  };
}

function recordStandingTotal(target, id, standing, rank, winCredit) {
  const totals = target[id] || {
    appearances: 0,
    winCredit: 0,
    mandate: 0,
    rank: 0,
    auditHits: 0,
    forcedNoOps: 0
  };
  totals.appearances += 1;
  totals.winCredit += winCredit;
  totals.mandate += standing.score || 0;
  totals.rank += rank;
  totals.auditHits += standing.auditHits || 0;
  totals.forcedNoOps += standing.forcedNoOps || 0;
  target[id] = totals;
}

function summarizeStandingTotals(totalsById) {
  return Object.fromEntries(
    Object.entries(totalsById).map(([id, totals]) => [
      id,
      {
        appearances: totals.appearances,
        winShare: totals.appearances
          ? totals.winCredit / totals.appearances
          : 0,
        meanMandate: totals.appearances
          ? totals.mandate / totals.appearances
          : 0,
        meanRank: totals.appearances
          ? totals.rank / totals.appearances
          : 0,
        meanAuditHits: totals.appearances
          ? totals.auditHits / totals.appearances
          : 0,
        meanForcedNoOps: totals.appearances
          ? totals.forcedNoOps / totals.appearances
          : 0
      }
    ])
  );
}

function outcomeSummary(observations) {
  const mandateSources = {};
  const actionCounts = {};
  const openingCounts = {};
  const winningPathCounts = {};
  const winningPathAttributionTotals = {};
  const winningPathMarginTotals = {
    winCredit: 0,
    gap: 0,
    exactTie: 0,
    withinHalfPoint: 0,
    withinOnePoint: 0,
    withinTwoPoints: 0,
    primarySecondary: {},
    byPrimaryPath: {},
    byProfile: {}
  };
  const bindingRequirements = {};
  const agiFunnel = {
    playerOpportunities: 0,
    coreRequirementsMet: 0,
    legalDeclarationWindow: 0,
    claimRegistered: 0,
    emergenceTriggered: 0,
    declared: 0
  };
  const factionAbilityValues = {};
  const factionActionSelections = {};
  const profileActionSelections = {};
  const factionMandateSources = {};
  const profileMandateSources = {};
  const factionStandingTotals = {};
  const profileStandingTotals = {};
  const seatStandingTotals = {};
  let declarations = 0;
  let agiEmergence = 0;
  let openContinuity = 0;
  let auditHits = 0;
  let forcedNoOps = 0;
  let tradeRequiredSelections = 0;
  let requiredTradeOffers = 0;
  let requiredTradeAcceptances = 0;
  let requiredTradeFailures = 0;
  let blockedAfterCommitment = 0;
  let actionOpportunities = 0;
  let fallbacks = 0;
  for (const observation of observations) {
    actionOpportunities += observation.standings.length * 12;
    declarations += observation.declarations;
    agiEmergence += Number(
      observation.worldEndingId === "singularity" || observation.worldEndingId === "closed_loop"
    );
    openContinuity += Number(
      observation.worldEndingId === "singularity" || observation.worldEndingId === "plural_future"
    );
    for (const entry of observation.agiFunnel || []) {
      agiFunnel.playerOpportunities += 1;
      for (const stage of [
        "coreRequirementsMet",
        "legalDeclarationWindow",
        "claimRegistered",
        "emergenceTriggered",
        "declared"
      ]) {
        agiFunnel[stage] += Number(Boolean(entry[stage]));
      }
    }
    for (const readiness of observation.declarationReadiness) {
      const id = readiness.failingRequirement || "ready";
      bindingRequirements[id] = (bindingRequirements[id] || 0) + 1;
    }
    const winnerCredit = new Map(
      observation.winnerSeats.map((seat) => [
        seat,
        1 / observation.winnerSeats.length
      ])
    );
    for (const [index, standing] of observation.standings.entries()) {
      auditHits += standing.auditHits || 0;
      forcedNoOps += standing.forcedNoOps || 0;
      tradeRequiredSelections += standing.selectionAvailability?.tradeRequired || 0;
      requiredTradeOffers += standing.requiredTradeOffers || 0;
      requiredTradeAcceptances += standing.requiredTradeAcceptances || 0;
      requiredTradeFailures += standing.requiredTradeFailures || 0;
      blockedAfterCommitment += standing.blockedAfterCommitment || 0;
      fallbacks += standing.policyFallbacks || 0;
      const standingWinCredit = winnerCredit.get(standing.seat) || 0;
      recordStandingTotal(
        factionStandingTotals,
        standing.factionId,
        standing,
        index + 1,
        standingWinCredit
      );
      recordStandingTotal(
        profileStandingTotals,
        standing.profileId,
        standing,
        index + 1,
        standingWinCredit
      );
      recordStandingTotal(
        seatStandingTotals,
        String(standing.seat),
        standing,
        index + 1,
        standingWinCredit
      );
      const actions = factionActionSelections[standing.factionId] || {};
      const profileActions = profileActionSelections[standing.profileId] || {};
      for (const [actionId, count] of Object.entries(standing.actions || {})) {
        actions[actionId] = (actions[actionId] || 0) + count;
        profileActions[actionId] = (profileActions[actionId] || 0) + count;
        increment(actionCounts, actionId, count);
      }
      factionActionSelections[standing.factionId] = actions;
      profileActionSelections[standing.profileId] = profileActions;
      increment(
        openingCounts,
        (standing.openingActions || []).join("→") || "none"
      );
      if (winnerCredit.has(standing.seat)) {
        const credit = winnerCredit.get(standing.seat);
        const pathId = classifyWinningPath(standing);
        const margin = winningPathMargin(standing);
        const recordMargin = (totals) => {
          totals.winCredit = (totals.winCredit || 0) + credit;
          totals.gap = (totals.gap || 0) + margin.gap * credit;
          totals.exactTie =
            (totals.exactTie || 0) + Number(margin.gap === 0) * credit;
          totals.withinHalfPoint =
            (totals.withinHalfPoint || 0) +
            Number(margin.gap <= 0.5) * credit;
          totals.withinOnePoint =
            (totals.withinOnePoint || 0) +
            Number(margin.gap <= 1) * credit;
          totals.withinTwoPoints =
            (totals.withinTwoPoints || 0) +
            Number(margin.gap <= 2) * credit;
        };
        recordMargin(winningPathMarginTotals);
        increment(
          winningPathMarginTotals.primarySecondary,
          `${margin.primary}→${margin.secondary}`,
          credit
        );
        const primaryMargins =
          winningPathMarginTotals.byPrimaryPath[margin.primary] || {};
        recordMargin(primaryMargins);
        winningPathMarginTotals.byPrimaryPath[margin.primary] = primaryMargins;
        const profileMargins =
          winningPathMarginTotals.byProfile[standing.profileId] || {
            primaryPaths: {},
            secondaryPaths: {}
          };
        recordMargin(profileMargins);
        increment(profileMargins.primaryPaths, margin.primary, credit);
        increment(profileMargins.secondaryPaths, margin.secondary, credit);
        winningPathMarginTotals.byProfile[standing.profileId] = profileMargins;
        increment(
          winningPathCounts,
          pathId,
          credit
        );
        const path = winningPathAttributionTotals[pathId] || {
          winCredit: 0,
          mandate: 0,
          capability: 0,
          facilities: 0,
          customers: 0,
          trust: 0,
          agiDeclarations: 0,
          actionSelections: {},
          mandateSources: {},
          factions: {},
          profiles: {},
          backends: {},
          worldEndings: {}
        };
        path.winCredit += credit;
        path.mandate += (standing.score || 0) * credit;
        path.capability += (standing.capability || 0) * credit;
        path.facilities += (standing.facilities || 0) * credit;
        path.customers += (standing.customers || 0) * credit;
        path.trust += (standing.trust || 0) * credit;
        path.agiDeclarations += Number(standing.agiDeclared) * credit;
        for (const [actionId, count] of Object.entries(standing.actions || {})) {
          increment(path.actionSelections, actionId, count * credit);
        }
        for (const event of standing.mandateEvents || []) {
          increment(
            path.mandateSources,
            event.source || "unknown",
            (event.points || 0) * credit
          );
        }
        increment(path.factions, standing.factionId, credit);
        increment(path.profiles, standing.profileId, credit);
        increment(path.backends, standing.backendId, credit);
        increment(path.worldEndings, observation.worldEndingId || "unknown", credit);
        winningPathAttributionTotals[pathId] = path;
      }
      const faction = factionAbilityValues[standing.factionId] || {};
      for (const [abilityId, values] of Object.entries(
        standing.factionAbilityValues || {}
      )) {
        const ability = faction[abilityId] || {};
        mergeAbilityTelemetry(ability, values);
        faction[abilityId] = ability;
      }
      factionAbilityValues[standing.factionId] = faction;
      for (const event of standing.mandateEvents || []) {
        const source = event.source || "unknown";
        mandateSources[source] =
          (mandateSources[source] || 0) + (event.points || 0);
        const factionSources =
          factionMandateSources[standing.factionId] || {};
        factionSources[source] =
          (factionSources[source] || 0) + (event.points || 0);
        factionMandateSources[standing.factionId] = factionSources;
        const profileSources =
          profileMandateSources[standing.profileId] || {};
        profileSources[source] =
          (profileSources[source] || 0) + (event.points || 0);
        profileMandateSources[standing.profileId] = profileSources;
      }
    }
  }
  const factionStandings = summarizeStandingTotals(factionStandingTotals);
  const profileStandings = summarizeStandingTotals(profileStandingTotals);
  const seatStandings = summarizeStandingTotals(seatStandingTotals);
  const totalWinCredit = Object.values(winningPathAttributionTotals)
    .reduce((sum, path) => sum + path.winCredit, 0);
  const winningPathAttribution = Object.fromEntries(
    Object.entries(winningPathAttributionTotals).map(([pathId, totals]) => [
      pathId,
      {
        wins: totals.winCredit,
        share: totalWinCredit ? totals.winCredit / totalWinCredit : 0,
        meanMandate: totals.winCredit ? totals.mandate / totals.winCredit : 0,
        meanCapability: totals.winCredit
          ? totals.capability / totals.winCredit
          : 0,
        meanFacilities: totals.winCredit
          ? totals.facilities / totals.winCredit
          : 0,
        meanCustomers: totals.winCredit
          ? totals.customers / totals.winCredit
          : 0,
        meanTrust: totals.winCredit ? totals.trust / totals.winCredit : 0,
        agiDeclarationRate: totals.winCredit
          ? totals.agiDeclarations / totals.winCredit
          : 0,
        actionSelections: totals.actionSelections,
        mandateSources: totals.mandateSources,
        factions: totals.factions,
        profiles: totals.profiles,
        backends: totals.backends,
        worldEndings: totals.worldEndings
      }
    ])
  );
  const summarizeMargins = (totals) => ({
    wins: totals.winCredit || 0,
    meanGap: totals.winCredit ? totals.gap / totals.winCredit : 0,
    exactTieShare: totals.winCredit
      ? totals.exactTie / totals.winCredit
      : 0,
    withinHalfPointShare: totals.winCredit
      ? totals.withinHalfPoint / totals.winCredit
      : 0,
    withinOnePointShare: totals.winCredit
      ? totals.withinOnePoint / totals.winCredit
      : 0,
    withinTwoPointsShare: totals.winCredit
      ? totals.withinTwoPoints / totals.winCredit
      : 0
  });
  const winningPathMargins = {
    ...summarizeMargins(winningPathMarginTotals),
    primarySecondary: winningPathMarginTotals.primarySecondary,
    byPrimaryPath: Object.fromEntries(
      Object.entries(winningPathMarginTotals.byPrimaryPath)
        .map(([pathId, totals]) => [pathId, summarizeMargins(totals)])
    ),
    byProfile: Object.fromEntries(
      Object.entries(winningPathMarginTotals.byProfile)
        .map(([profileId, totals]) => [
          profileId,
          {
            ...summarizeMargins(totals),
            primaryPaths: totals.primaryPaths,
            secondaryPaths: totals.secondaryPaths
          }
        ])
    )
  };
  return {
    matches: observations.length,
    declarationRate: observations.length ? declarations / observations.length : 0,
    agiEmergenceRate: observations.length ? agiEmergence / observations.length : 0,
    openContinuityRate: observations.length ? openContinuity / observations.length : 0,
    meanAuditHitsPerMatch: observations.length ? auditHits / observations.length : 0,
    forcedNoOps,
    forcedNoOpRate: actionOpportunities ? forcedNoOps / actionOpportunities : 0,
    tradeRequiredSelections,
    requiredTradeOffers,
    requiredTradeAcceptances,
    requiredTradeFailures,
    blockedAfterCommitment,
    policyFallbacks: fallbacks,
    actionDiversity: normalizedEntropy(actionCounts),
    openingDiversity: concentration(openingCounts),
    winningPathDiversity: concentration(winningPathCounts),
    winningPathClassifier: WINNING_PATH_CLASSIFIER,
    winningPathAttribution,
    winningPathMargins,
    factionWinShareRange: range(
      Object.values(factionStandings).map((standing) => standing.winShare)
    ),
    profileWinShareRange: range(
      Object.values(profileStandings).map((standing) => standing.winShare)
    ),
    seatWinShareRange: range(
      Object.values(seatStandings).map((standing) => standing.winShare)
    ),
    bindingRequirements,
    mandateSources,
    factionMandateSources,
    profileMandateSources,
    factionStandings,
    profileStandings,
    seatStandings,
    factionAbilityValues,
    factionActionSelections,
    profileActionSelections,
    agiFunnel,
    agiFunnelRates: Object.fromEntries(
      Object.entries(agiFunnel)
        .filter(([stage]) => stage !== "playerOpportunities")
        .map(([stage, count]) => [
          stage,
          agiFunnel.playerOpportunities
            ? count / agiFunnel.playerOpportunities
            : 0
        ])
    )
  };
}

function pairedRuleComparisons(
  observations,
  rulesConfigurations,
  alpha = 0.05,
  comparisonKind = "causal_one_lever"
) {
  if (rulesConfigurations.length < 2) return [];
  const byPair = new Map();
  for (const observation of observations) {
    const pair = byPair.get(observation.comparisonPairId) || new Map();
    pair.set(observation.rulesConfigurationId, observation);
    byPair.set(observation.comparisonPairId, pair);
  }
  const baselineId = rulesConfigurations[0].id;
  return rulesConfigurations.slice(1).map((configuration) => {
    const records = [];
    let unmatchedPairs = 0;
    let standingMismatches = 0;
    for (const pair of byPair.values()) {
      const baseline = pair.get(baselineId);
      const candidate = pair.get(configuration.id);
      if (!baseline || !candidate) {
        unmatchedPairs += 1;
        continue;
      }
      const baselineWins = new Map(baseline.winnerSeats.map((seat) => [
        seat,
        1 / baseline.winnerSeats.length
      ]));
      const candidateWins = new Map(candidate.winnerSeats.map((seat) => [
        seat,
        1 / candidate.winnerSeats.length
      ]));
      const baselineRanks = new Map(
        baseline.standings.map((entry, index) => [entry.seat, index + 1])
      );
      const candidateRanks = new Map(
        candidate.standings.map((entry, index) => [entry.seat, index + 1])
      );
      for (const left of baseline.standings) {
        const right = candidate.standings.find((entry) => entry.seat === left.seat);
        if (
          !right ||
          right.factionId !== left.factionId ||
          right.profileId !== left.profileId ||
          right.backendId !== left.backendId
        ) {
          standingMismatches += 1;
          continue;
        }
        records.push({
          playerCount: baseline.playerCount,
          mandateMode: baseline.mandateMode,
          factionId: left.factionId,
          backendId: left.backendId,
          winDelta:
            (candidateWins.get(right.seat) || 0) -
            (baselineWins.get(left.seat) || 0),
          scoreDelta: right.score - left.score,
          rankDelta:
            baselineRanks.get(left.seat) - candidateRanks.get(right.seat)
        });
      }
    }
    const summarize = (dimensions) => {
      const groups = new Map();
      for (const record of records) {
        const id = groupKey(record, dimensions);
        const group = groups.get(id) || {
          id,
          dimensions: Object.fromEntries(
            dimensions.map((key) => [key, record[key]])
          ),
          winDeltas: [],
          scoreDeltas: [],
          rankDeltas: []
        };
        group.winDeltas.push(record.winDelta);
        group.scoreDeltas.push(record.scoreDelta);
        group.rankDeltas.push(record.rankDelta);
        groups.set(id, group);
      }
      const familyAlpha = alpha / Math.max(1, groups.size);
      return [...groups.values()].map((group) => {
        const exposure = group.winDeltas.length;
        const winShareDelta = mean(group.winDeltas);
        const halfWidth = Math.min(
          1,
          Math.sqrt((2 * Math.log(2 / familyAlpha)) / exposure)
        );
        return {
          id: group.id,
          dimensions: group.dimensions,
          exposure,
          winShareDelta,
          scoreDelta: mean(group.scoreDeltas),
          rankDelta: mean(group.rankDeltas),
          boundedConfidenceInterval: {
            lower: Math.max(-1, winShareDelta - halfWidth),
            upper: Math.min(1, winShareDelta + halfWidth),
            halfWidth,
            alpha: familyAlpha
          }
        };
      });
    };
    return {
      baselineId,
      candidateId: configuration.id,
      matchedPairs: [...byPair.values()].filter((pair) =>
        pair.has(baselineId) && pair.has(configuration.id)
      ).length,
      unmatchedPairs,
      standingMismatches,
      interpretation:
        comparisonKind === "package_interaction"
          ? "Common-seed paired deltas validate the interaction of independently selected levers; they do not establish a new causal one-lever effect. Positive rankDelta means the package improved placement. Promotion still requires the registered package gate, a tracked receipt, and explicit approval."
          : "Common-seed paired deltas are diagnostic; positive rankDelta means the candidate improved placement. Promotion still requires the registered marginal gate and a tracked receipt.",
      families: {
        faction: summarize(["factionId"]),
        factionBackend: summarize(["factionId", "backendId"]),
        factionBackendPlayerCount: summarize([
          "playerCount",
          "factionId",
          "backendId"
        ]),
        factionBackendPlayerCountMandateMode: summarize([
          "playerCount",
          "mandateMode",
          "factionId",
          "backendId"
        ])
      }
    };
  });
}

async function runAdversarialSlice({
  profiles,
  runs,
  population,
  seed,
  rulesVariant,
  studyLaunchIdentity,
  projection,
  signal,
  onProgress,
  progress
}) {
  const rows = [];
  const profileResult = (report, id) =>
    report.profiles.find((entry) => entry.profileId === id);
  const evaluate = async (candidate, opponents, phaseSeed) => {
    const options = {
      runs,
      playerCount: 4,
      seed: phaseSeed,
      sampleReplays: 0,
      profileIds: [candidate.id, ...opponents.map((entry) => entry.id)].slice(0, 4),
      profileOverrides: [candidate, ...opponents],
      backends: ["weighted", "greedy", "weighted", "greedy"],
      rotateProfiles: true,
      rotateFactions: true,
      simulateNegotiation: true,
      rulesVariant,
      signal,
      projection,
      experimentKind: "unified_matrix_audit"
    };
    const launchIdentity = await captureSimulationLaunchIdentity(options);
    assertStudyIdentity(studyLaunchIdentity, launchIdentity, "Unified-matrix adversarial slice");
    const report = await createSimulation({
      ...options,
      launchIdentity
    });
    progress.completed += runs;
    onProgress?.({
      phase: "adversarial_slice",
      completed: progress.completed,
      total: progress.total
    });
    const result = profileResult(report, candidate.id);
    return {
      profile: candidate,
      success: result.winShare * result.appearances,
      exposure: result.appearances,
      winShare: result.winShare,
      meanScore: result.meanScore
    };
  };

  for (const [targetIndex, target] of profiles.entries()) {
    const source = profiles[(targetIndex + 1) % profiles.length];
    const trainingOpponents = [
      target,
      profiles[(targetIndex + 2) % profiles.length],
      profiles[(targetIndex + 3) % profiles.length]
    ];
    const responses = [];
    for (let index = 0; index < population; index += 1) {
      const candidate = index === 0
        ? structuredClone(source)
        : mutateStrategy(
          source,
          `${seed}:response:${target.id}:${index}`,
          { magnitude: 0.45 }
        );
      candidate.id = `response_${targetIndex}_${index}`;
      responses.push(await evaluate(
        candidate,
        trainingOpponents,
        `${seed}:response:${target.id}:common`
      ));
    }
    responses.sort((left, right) =>
      right.winShare - left.winShare || right.meanScore - left.meanScore
    );
    const best = responses[0];
    const counterOpponents = [
      best.profile,
      profiles[(targetIndex + 4) % profiles.length],
      profiles[(targetIndex + 5) % profiles.length]
    ];
    const counters = [];
    for (let index = 0; index < population; index += 1) {
      const candidate = index === 0
        ? structuredClone(target)
        : mutateStrategy(
          target,
          `${seed}:counter:${target.id}:${index}`,
          { magnitude: 0.45 }
        );
      candidate.id = `counter_${targetIndex}_${index}`;
      counters.push(await evaluate(
        candidate,
        counterOpponents,
        `${seed}:counter:${target.id}:common`
      ));
    }
    counters.sort((left, right) =>
      right.winShare - left.winShare || right.meanScore - left.meanScore
    );
    const holdoutOpponents = [
      profiles[(targetIndex + 4) % profiles.length],
      profiles[(targetIndex + 5) % profiles.length],
      profiles[(targetIndex + 6) % profiles.length]
    ];
    const holdout = await evaluate(
      best.profile,
      holdoutOpponents,
      `${seed}:holdout:${target.id}`
    );
    rows.push({
      targetProfileId: target.id,
      sourceProfileId: source.id,
      baseline: responses.find((entry) => entry.profile.id === `response_${targetIndex}_0`),
      bestResponse: best,
      counterResponse: counters[0],
      holdout,
      holdoutProfileIds: holdoutOpponents.map((entry) => entry.id)
    });
  }
  const rateCells = rows.flatMap((row) => [
    {
      id: `${row.targetProfileId}:baseline`,
      phase: "baseline",
      targetProfileId: row.targetProfileId,
      success: row.baseline.success,
      exposure: row.baseline.exposure
    },
    {
      id: `${row.targetProfileId}:best_response`,
      phase: "best_response",
      targetProfileId: row.targetProfileId,
      success: row.bestResponse.success,
      exposure: row.bestResponse.exposure
    },
    {
      id: `${row.targetProfileId}:counter_response`,
      phase: "counter_response",
      targetProfileId: row.targetProfileId,
      success: row.counterResponse.success,
      exposure: row.counterResponse.exposure
    },
    {
      id: `${row.targetProfileId}:holdout`,
      phase: "holdout",
      targetProfileId: row.targetProfileId,
      success: row.holdout.success,
      exposure: row.holdout.exposure
    }
  ]);
  return {
    status: "diagnostic_not_balance_authority",
    runsPerCandidate: runs,
    population,
    rows: rows.map((row) => ({
      targetProfileId: row.targetProfileId,
      sourceProfileId: row.sourceProfileId,
      baselineWinShare: row.baseline.winShare,
      bestResponseWinShare: row.bestResponse.winShare,
      counterResponseWinShare: row.counterResponse.winShare,
      holdoutWinShare: row.holdout.winShare,
      holdoutProfileIds: row.holdoutProfileIds,
      bestResponseWeights: row.bestResponse.profile.strategy,
      counterResponseWeights: row.counterResponse.profile.strategy
    })),
    inference: empiricalBayesRates(rateCells, {
      alpha: 0.05,
      familySize: rateCells.length,
      look: 1
    })
  };
}

function evaluateMatrix({ families, pairwise, settings, thresholds }) {
  const all = flattenGroups(families);
  const dominanceCandidates = all.filter((cell) => intervalCrossesThreshold(cell, {
    operator: "max",
    threshold: cell.expected + thresholds.dominanceUpliftMax,
    minimumExposure: settings.minimumMarginalExposure
  }));
  const isHomogeneous = (cell) =>
    cell.dimensions.backendRegime?.startsWith("homogeneous_");
  const ruleFamilies = new Set([
    "seatBackendRegime",
    "factionBackendRegime",
    "strategyBackendRegime",
    "factionStrategyBackendRegime"
  ]);
  const summarizeDominance = (cells) => cells.map((cell) => ({
    familyId: cell.familyId,
    id: cell.id,
    exposure: cell.exposure,
    expected: cell.expected,
    posteriorInterval: cell.posteriorInterval,
    confidenceSequence: cell.confidenceSequence
  }));
  const dominance = summarizeDominance(dominanceCandidates.filter((cell) =>
    ruleFamilies.has(cell.familyId) && isHomogeneous(cell)
  ));
  const diagnosticDominance = summarizeDominance(dominanceCandidates.filter((cell) =>
    !ruleFamilies.has(cell.familyId) || !isHomogeneous(cell)
  ));
  const pairwiseCandidates = pairwise.cells.filter((cell) =>
    intervalCrossesThreshold(cell, {
      operator: "max",
      threshold: thresholds.pairwiseDominanceMax,
      minimumExposure: settings.minimumMarginalExposure
    })
  );
  const summarizePairwise = (cells) => cells.map((cell) => ({
    id: cell.id,
    dimensions: cell.dimensions,
    exposure: cell.exposure,
    posteriorInterval: cell.posteriorInterval,
    confidenceSequence: cell.confidenceSequence
  }));
  const pairwiseDominance = summarizePairwise(pairwiseCandidates.filter(isHomogeneous));
  const diagnosticPairwiseDominance = summarizePairwise(
    pairwiseCandidates.filter((cell) => !isHomogeneous(cell))
  );
  const core = all.filter((cell) =>
    ["seatBackendRegime", "factionBackendRegime", "strategyBackendRegime"]
      .includes(cell.familyId) &&
    isHomogeneous(cell)
  );
  const precision = precisionReached(core, {
    targetHalfWidth: settings.targetHalfWidth,
    minimumExposure: settings.minimumMarginalExposure
  });
  return {
    status: dominance.length || pairwiseDominance.length
      ? "credible_dominance_detected"
      : precision
        ? "no_credible_dominance_at_registered_precision"
        : "inconclusive_precision_not_reached",
    dominance,
    diagnosticDominance,
    pairwiseDominance,
    diagnosticPairwiseDominance,
    precisionReached: precision,
    maximumCoreHalfWidth: Math.max(0, ...core.map((cell) =>
      cell.confidenceSequence.halfWidth
    )),
    promotionGate: {
      eligible: false,
      automatedPass: dominance.length === 0 && pairwiseDominance.length === 0 && precision,
      sourceClean: null,
      trackedReceipt: false,
      humanApproval: false,
      verdict: dominance.length
        || pairwiseDominance.length
        ? "credible_dominance_requires_one_lever_review"
        : precision
          ? "awaiting_clean_receipt_and_human_approval"
          : "insufficient_precision",
      reasons: [
        ...(dominance.length || pairwiseDominance.length
          ? ["At least one partially pooled marginal or head-to-head cell and its multiplicity-safe confidence sequence clear the registered bound."]
          : []),
        ...(diagnosticDominance.length || diagnosticPairwiseDominance.length
          ? ["Mixed-regime or pooled dominance is reported diagnostically and does not alone fail the rules gate."]
          : []),
        ...(!precision ? ["The registered precision target was not reached."] : []),
        "A tracked receipt and explicit human approval remain mandatory."
      ]
    }
  };
}

export async function runUnifiedMatrix(options = {}, onProgress) {
  const [baseProfiles, matrixContract, balanceContract] = await Promise.all([
    loadPlayerProfiles(),
    readFile(matrixUrl, "utf8").then(JSON.parse),
    loadBalanceContract()
  ]);
  const profileOverrides = new Map(
    (options.profileOverrides || []).map((profile) => {
      validatePlayerProfile(profile);
      return [profile.id, structuredClone(profile)];
    })
  );
  const profiles = baseProfiles.map((profile) =>
    profileOverrides.get(profile.id) || profile
  );
  for (const [id, profile] of profileOverrides) {
    if (!profiles.some((candidate) => candidate.id === id)) profiles.push(profile);
  }
  const playerCounts = (options.playerCounts || matrixContract.axes.playerCount)
    .map(Number);
  const supportedPlayerCounts = matrixContract.playerCountPolicy.supported;
  const unsupportedPlayerCounts = playerCounts.filter(
    (count) => !supportedPlayerCounts.includes(count)
  );
  if (unsupportedPlayerCounts.length) {
    throw new RangeError(
      `Unified matrix player counts must be supported: ${supportedPlayerCounts.join(", ")}.`
    );
  }
  const rulesConfigurations = options.rulesConfigurations || [
    { id: "canonical", overlay: options.rulesVariant || {} }
  ];
  const comparisonKind = options.comparisonKind || "causal_one_lever";
  if (!["causal_one_lever", "package_interaction"].includes(comparisonKind)) {
    throw new TypeError(
      "comparisonKind must be causal_one_lever or package_interaction."
    );
  }
  if (
    comparisonKind === "package_interaction" &&
    (
      rulesConfigurations.length !== 2 ||
      rulesConfigurations[0]?.id !== "canonical" ||
      Object.keys(rulesConfigurations[0]?.overlay || {}).length !== 0
    )
  ) {
    throw new TypeError(
      "Package interaction validation requires one empty canonical baseline and one package candidate."
    );
  }
  for (const configuration of rulesConfigurations) {
    if (!configuration.id || !configuration.overlay ||
        typeof configuration.overlay !== "object" ||
        Array.isArray(configuration.overlay)) {
      throw new TypeError("Every rules configuration requires id and overlay.");
    }
    const leverCount = Object.keys(configuration.overlay).length;
    if (
      configuration.id !== "canonical" &&
      comparisonKind === "causal_one_lever" &&
      leverCount !== 1
    ) {
      throw new TypeError(
        `Rules configuration ${configuration.id} must change exactly one lever.`
      );
    }
    if (
      configuration.id !== "canonical" &&
      comparisonKind === "package_interaction" &&
      leverCount < 2
    ) {
      throw new TypeError(
        `Package configuration ${configuration.id} must combine at least two independently selected levers.`
      );
    }
  }
  const mandateModes = options.mandateModes || matrixContract.axes.mandateMode;
  const projection = options.projection || "batch";
  if (!['rich', 'batch'].includes(projection)) {
    throw new TypeError("projection must be rich or batch.");
  }
  const settings = {
    ...matrixContract.sampling,
    initialRunsPerCell: integer(
      options.initialRunsPerCell,
      matrixContract.sampling.initialRunsPerCell,
      1,
      100,
      "initialRunsPerCell"
    ),
    batchSize: integer(
      options.batchSize,
      matrixContract.sampling.batchSize,
      1,
      100,
      "batchSize"
    ),
    maximumMatches: integer(
      options.maximumMatches ?? options.runs,
      matrixContract.sampling.maximumMatches,
      30,
      100000,
      "maximumMatches"
    )
  };
  const adversarialRuns = integer(options.adversarialRuns, 2, 1, 100, "adversarialRuns");
  const adversarialPopulation = integer(
    options.adversarialPopulation,
    2,
    2,
    20,
    "adversarialPopulation"
  );
  const includeAdversarial = options.includeAdversarial !== false;
  const cells = buildCells({
    profiles,
    playerCounts,
    rulesConfigurations,
    mandateModes
  });
  const studyLaunchIdentity = await captureCellLaunchIdentities({
    cells,
    profiles,
    projection
  });
  const configuredWorkers = matrixWorkerCount(options.workers);
  const initialCellWorkers = Math.min(configuredWorkers, cells.length);
  const adversarialMatches = includeAdversarial
    ? profiles.length * (adversarialPopulation * 2 + 1) * adversarialRuns
    : 0;
  const minimumCoverageMatches = cells.length * settings.initialRunsPerCell;
  if (settings.maximumMatches < minimumCoverageMatches + adversarialMatches) {
    throw new RangeError(
      `maximumMatches must be at least ${minimumCoverageMatches + adversarialMatches} ` +
      `for initial coverage${includeAdversarial ? " plus the adversarial slice" : ""}.`
    );
  }
  const matrixMatchLimit = settings.maximumMatches - adversarialMatches;
  const preRegistration = {
    id: options.preRegistrationId || `deterministic-${matrixContract.id}`,
    lockedBeforeResults: true,
    registrationAuthority: matrixContract.id,
    usesCommittedDefault: (
      options.initialRunsPerCell === undefined &&
      options.batchSize === undefined &&
      options.maximumMatches === undefined &&
      options.runs === undefined &&
      options.playerCounts === undefined &&
      options.mandateModes === undefined &&
      options.rulesConfigurations === undefined &&
      options.profileOverrides === undefined &&
      options.projection === undefined &&
      options.workers === undefined &&
      options.chunkSize === undefined
    ),
    matrixContractFingerprint: fingerprintObject(matrixContract),
    playerCounts,
    rulesConfigurations,
    comparisonKind,
    mandateModes,
    backendSet: ["weighted", "greedy"],
    backendRegimes: [
      "homogeneous_weighted",
      "homogeneous_greedy",
      "alternating_weighted_first",
      "alternating_greedy_first"
    ],
    profiles: profiles.map((profile) => ({
      id: profile.id,
      provenance: profile.provenance || null,
      fingerprint: fingerprintObject(profile)
    })),
    settings,
    execution: {
      projection,
      requestedWorkers: options.workers === undefined ? null : Number(options.workers),
      configuredWorkers,
      initialCellWorkers,
      scheduler: initialCellWorkers > 1 ? "worker_threads" : "inline",
      chunkSize: options.chunkSize === undefined ? null : Number(options.chunkSize),
      resultOrder: "matrix_cell_then_match_index"
    },
    adversarial: {
      enabled: includeAdversarial,
      runsPerCandidate: adversarialRuns,
      population: adversarialPopulation,
      reservedMatches: adversarialMatches
    },
    llm: {
      enabled: false,
      reason: "Deterministic matrix precedes the separately preregistered metered holdout."
    }
  };
  preRegistration.fingerprint = fingerprintObject(preRegistration);
  const observations = [];
  const records = [];
  const pairwiseRecords = [];
  const allocations = [];
  const integrityDetails = [];
  let look = 0;
  let executedMatches = 0;
  const started = performance.now();

  const cellOptions = (cell, runs) => ({
    runs,
    playerCount: cell.playerCount,
    seed: `${options.seed || "mandate-2038-unified-matrix"}:${cell.pairingId}:offset:${cell.runs}`,
    sampleReplays: 0,
    profileIds: cell.profileIds,
    profileOverrides: profiles,
    backends: cell.backends,
    rotateProfiles: true,
    rotateFactions: true,
    rulesVariant: cell.rulesVariant,
    mandateMode: cell.mandateMode,
    simulateNegotiation: true,
    includeObservations: true,
    runOffset: cell.runs,
    launchIdentity: cell.launchIdentity,
    projection,
    workers: 1,
    chunkSize: options.chunkSize,
    experimentKind: "unified_matrix_audit",
    signal: options.signal
  });

  const recordCell = ({ cell, runs, reason, report, elapsedMs }) => {
    const runStart = cell.runs;
    for (const detail of report.diagnostics.integrity.details) {
      integrityDetails.push({
        cellId: cell.id,
        rulesConfigurationId: cell.rulesConfigurationId,
        ...detail
      });
    }
    for (const observation of report.observations) {
      const tagged = {
        ...observation,
        matrixCellId: cell.id,
        comparisonPairId:
          `${cell.pairingId}:run:${runStart + observation.matchIndex}`,
        rulesConfigurationId: cell.rulesConfigurationId,
        mandateMode: cell.mandateMode,
        backendRegime: cell.backendRegime,
        playerCount: cell.playerCount
      };
      observations.push(tagged);
      const winnerCredit = new Map(observation.winnerSeats.map((seat) => [
        seat,
        1 / observation.winnerSeats.length
      ]));
      for (const standing of observation.standings) {
        records.push({
          matrixCellId: cell.id,
          rulesConfigurationId: cell.rulesConfigurationId,
          mandateMode: cell.mandateMode,
          backendRegime: cell.backendRegime,
          playerCount: cell.playerCount,
          seat: standing.seat,
          factionId: standing.factionId,
          profileId: standing.profileId,
          backendId: standing.backendId,
          winCredit: winnerCredit.get(standing.seat) || 0
        });
        for (const opponent of observation.standings) {
          if (opponent.seat === standing.seat) continue;
          pairwiseRecords.push({
            rulesConfigurationId: cell.rulesConfigurationId,
            playerCount: cell.playerCount,
            backendRegime: cell.backendRegime,
            profileId: standing.profileId,
            opponentProfileId: opponent.profileId,
            winCredit: standing.score === opponent.score
              ? 0.5
              : Number(standing.score > opponent.score)
          });
        }
      }
    }
    cell.runs += runs;
    executedMatches += runs;
    look += 1;
    allocations.push({
      look,
      cellId: cell.id,
      runs,
      cumulativeMatches: executedMatches,
      reason,
      elapsedMs
    });
    onProgress?.({
      phase: "unified_matrix",
      completed: executedMatches,
      total: settings.maximumMatches
    });
  };

  const runCell = async (cell, requestedRuns, reason) => {
    const runs = Math.min(requestedRuns, matrixMatchLimit - executedMatches);
    if (runs <= 0) return;
    const started = performance.now();
    const report = await createSimulation({
      ...cellOptions(cell, runs),
      workers: options.workers
    });
    recordCell({
      cell,
      runs,
      reason,
      report,
      elapsedMs: Math.round(performance.now() - started)
    });
  };

  const initialTasks = cells.map((cell, taskIndex) => ({
    kind: "unified_matrix_cell",
    taskIndex,
    cell,
    runs: settings.initialRunsPerCell,
    reason: "preregistered_initial_coverage",
    launchIdentity: cell.launchIdentity,
    options: cellOptions(cell, settings.initialRunsPerCell)
  }));
  const initialResults = await runMatrixCellTasks(initialTasks, {
    workers: configuredWorkers,
    signal: options.signal
  });
  for (const result of initialResults) {
    const task = initialTasks[result.taskIndex];
    recordCell({ ...task, ...result });
  }

  let families = inferenceFamilies(records, settings, Math.max(1, look));
  let pairwise = pairwiseInference(pairwiseRecords, settings, Math.max(1, look));
  while (executedMatches < matrixMatchLimit) {
    const evaluation = evaluateMatrix({
      families,
      pairwise,
      settings,
      thresholds: {
        dominanceUpliftMax: balanceContract.thresholds.dominanceUpliftMax || 0.15,
        pairwiseDominanceMax: balanceContract.thresholds.pairwiseDominanceMax
      }
    });
    if (evaluation.precisionReached) break;
    const coverage = countCoverage(records);
    const selected = [...cells].sort((left, right) =>
      cellAllocationScore(right, coverage, families) -
        cellAllocationScore(left, coverage, families) ||
      left.id.localeCompare(right.id)
    )[0];
    const selectedCells = rulesConfigurations.length > 1
      ? cells.filter((cell) => cell.pairingId === selected.pairingId)
      : [selected];
    if (
      matrixMatchLimit - executedMatches <
        selectedCells.length * settings.batchSize
    ) break;
    for (const selectedCell of selectedCells) {
      await runCell(
        selectedCell,
        settings.batchSize,
        "largest_interval_proxy_then_factor_coverage"
      );
    }
    families = inferenceFamilies(records, settings, look);
    pairwise = pairwiseInference(pairwiseRecords, settings, look);
  }

  const evaluation = evaluateMatrix({
    families,
    pairwise,
    settings,
    thresholds: {
      dominanceUpliftMax: balanceContract.thresholds.dominanceUpliftMax || 0.15,
      pairwiseDominanceMax: balanceContract.thresholds.pairwiseDominanceMax
    }
  });
  const integrity = {
    violations: integrityDetails.length,
    details: integrityDetails.slice(0, 100)
  };
  if (integrity.violations) {
    evaluation.status = "invalid_integrity";
    evaluation.promotionGate.automatedPass = false;
    evaluation.promotionGate.verdict = "integrity_failure";
    evaluation.promotionGate.reasons.unshift(
      "At least one nested tournament reported a procedural-integrity violation."
    );
  }
  const progress = { completed: executedMatches, total: settings.maximumMatches };
  const adversarial = includeAdversarial
    ? await runAdversarialSlice({
      profiles,
      runs: adversarialRuns,
      population: adversarialPopulation,
      seed: `${options.seed || "mandate-2038-unified-matrix"}:adversarial`,
      rulesVariant: options.rulesVariant || {},
      studyLaunchIdentity,
      projection,
      signal: options.signal,
      onProgress,
      progress
    })
    : {
      status: "not_run",
      reason: "Disabled for a fast contract test."
    };
  executedMatches = progress.completed;
  const outcomes = outcomeSummary(observations);
  const configurationResults = Object.fromEntries(
    rulesConfigurations.map((configuration) => {
      const selected = observations.filter((observation) =>
        observation.rulesConfigurationId === configuration.id
      );
      return [
        configuration.id,
        {
          matches: selected.length,
          outcomes: outcomeSummary(selected),
          cooperation: cooperationSummary(selected),
          playerCountResults: Object.fromEntries(
            playerCounts.map((count) => {
              const countSelected = selected.filter(
                (observation) => observation.playerCount === count
              );
              return [
                count,
                {
                  matches: countSelected.length,
                  outcomes: outcomeSummary(countSelected),
                  cooperation: cooperationSummary(countSelected)
                }
              ];
            })
          )
        }
      ];
    })
  );
  const supportedPlayerCountCoverage = Object.fromEntries(
    supportedPlayerCounts.map((count) => [
      count,
      observations.filter((observation) => observation.playerCount === count).length
    ])
  );
  const completeSupportedPlayerCountCoverage = Object.values(
    supportedPlayerCountCoverage
  ).every((matches) => matches > 0);
  const forcedNoOpCheck = {
    id: "forced_no_op_rate",
    value: outcomes.forcedNoOpRate,
    operator: "max",
    threshold: balanceContract.thresholds.forcedNoOpRateMax,
    evidence: "observed",
    passed:
      outcomes.forcedNoOpRate <= balanceContract.thresholds.forcedNoOpRateMax
  };
  const balanceConfigurationIds = rulesConfigurations.length > 1
    ? rulesConfigurations.slice(1).map((configuration) => configuration.id)
    : rulesConfigurations.map((configuration) => configuration.id);
  const configurationChecks = configurationOutcomeBalanceChecks({
    configurationResults,
    configurationIds: balanceConfigurationIds,
    playerCounts,
    thresholds: balanceContract.thresholds
  });
  const failedConfigurationChecks = configurationChecks.filter(
    (entry) => !entry.passed
  );
  if (!forcedNoOpCheck.passed) {
    evaluation.status = "invalid_policy_quality";
    evaluation.promotionGate.automatedPass = false;
    evaluation.promotionGate.verdict = "policy_quality_failure";
    evaluation.promotionGate.reasons.unshift(
      "Deterministic policies exhausted too many Core Actions without a legal resolution."
    );
  }
  if (!completeSupportedPlayerCountCoverage) {
    evaluation.status = "incomplete_supported_player_count_coverage";
    evaluation.promotionGate.automatedPass = false;
    evaluation.promotionGate.verdict = "supported_player_count_coverage_missing";
    evaluation.promotionGate.reasons.unshift(
      "Promotion evidence must include three-, four-, and five-player games."
    );
  }
  if (
    failedConfigurationChecks.length &&
    integrity.violations === 0 &&
    forcedNoOpCheck.passed &&
    completeSupportedPlayerCountCoverage
  ) {
    if (evaluation.status !== "credible_dominance_detected") {
      evaluation.status = "outside_provisional_bounds";
      evaluation.promotionGate.verdict = "provisional_bounds_failed";
    }
    evaluation.promotionGate.automatedPass = false;
    evaluation.promotionGate.reasons.unshift(
      `${failedConfigurationChecks.length} configuration-by-player-count ` +
      "diversity, faction-range, fallback, or forced-no-op checks failed."
    );
  }
  const report = {
    reportType: "unified_matrix_audit",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(options.seed || "mandate-2038-unified-matrix"),
    playerCount: 4,
    playerCounts,
    runs: executedMatches,
    scope: {
      id: matrixContract.id,
      verdictBoundary: "One adaptive deterministic sampling frame. Partial pooling and sequential intervals can falsify robustness but cannot prove optimality, hardness, fun, or human negotiation quality.",
      automated: simulationCopy.coverage.balanceAudit.automated,
      excluded: simulationCopy.coverage.balanceAudit.excluded
    },
    preRegistration,
    matrixContract: {
      id: matrixContract.id,
      fingerprint: preRegistration.matrixContractFingerprint,
      inference: matrixContract.inference,
      playerCountPolicy: matrixContract.playerCountPolicy
    },
    design: {
      cellCount: cells.length,
      cells,
      allocations,
      looks: look,
      stoppedBecause: evaluation.precisionReached
        ? "registered_precision_reached"
        : "maximum_matches_reached",
      elapsedMs: Math.round(performance.now() - started)
    },
    launchIdentity: {
      schemaVersion: 1,
      study: studyLaunchIdentity,
      cellOrder: "rules_configuration_then_player_count_then_mandate_then_backend_then_roster",
      cells: cells.map((cell) => ({
        id: cell.id,
        identity: structuredClone(cell.launchIdentity)
      }))
    },
    execution: {
      projection,
      requestedWorkers: options.workers === undefined ? null : Number(options.workers),
      configuredWorkers,
      initialCellWorkers,
      scheduler: initialCellWorkers > 1 ? "worker_threads" : "inline",
      chunkSize: options.chunkSize === undefined ? null : Number(options.chunkSize),
      resultOrder: "matrix_cell_then_match_index"
    },
    inference: {
      families,
      pairwise,
      credibleMetaCycles: credibleMetaCycles(pairwise, {
        minimumExposure: settings.minimumMarginalExposure
      }),
      alpha: settings.alpha,
      multiplicity: matrixContract.inference.multiplicity,
      adaptiveSampling: true
    },
    outcomes,
    cooperation: cooperationSummary(observations),
    configurationResults,
    playerCountResults: Object.fromEntries(
      playerCounts.map((count) => {
        const selected = observations.filter(
          (observation) => observation.playerCount === count
        );
        return [
          count,
          {
            matches: selected.length,
            outcomes: outcomeSummary(selected),
            cooperation: cooperationSummary(selected)
          }
        ];
      })
    ),
    supportedPlayerCountCoverage,
    rulesComparisons: pairedRuleComparisons(
      observations,
      rulesConfigurations,
      settings.alpha,
      comparisonKind
    ),
    integrity,
    adversarial,
    balanceContract: {
      id: balanceContract.id,
      status: balanceContract.status,
      fingerprint: balanceContract.fingerprint,
      provenance: balanceContract.provenance
    },
    balanceEvaluation: {
      contractId: balanceContract.id,
      contractFingerprint: balanceContract.fingerprint,
      checks: [forcedNoOpCheck, ...configurationChecks],
      ...evaluation
    }
  };
  return createReportIdentity({
    report,
    rulesVariant: { configurations: rulesConfigurations },
    variantOverlay: options.rulesVariant,
    profiles,
    backends: ["weighted", "greedy"],
    model: null,
    policyProjection: projection,
    experimentKind: "unified_matrix_audit"
  });
}
