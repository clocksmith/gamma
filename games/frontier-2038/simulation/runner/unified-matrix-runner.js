import { readFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import {
  empiricalBayesRates,
  intervalCrossesThreshold,
  precisionReached
} from "../statistics/sequential-inference.js";
import {
  loadPlayerProfiles,
  validatePlayerProfile
} from "../personas/player-profile.js";
import { createSimulation } from "../runtime/create-simulation.js";
import { createReportIdentity, fingerprintObject } from "../versioning/game-identity.js";
import { loadBalanceContract } from "../balance/balance-contract.js";
import { simulationCopy } from "../content/simulation-copy.js";
import { mutateStrategy } from "./optimization-runner.js";

const matrixUrl = new URL("../contracts/experiment-matrix.json", import.meta.url);

function integer(value, fallback, minimum, maximum, label) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return parsed;
}

function mean(values) {
  return values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
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

function outcomeSummary(observations) {
  const mandateSources = {};
  const bindingRequirements = {};
  const agiFunnel = {
    playerOpportunities: 0,
    coreRequirementsMet: 0,
    neededExternalPower: 0,
    receivedPowerOffer: 0,
    acceptedPowerPrice: 0,
    becameGridReady: 0,
    legalDeclarationWindow: 0,
    declared: 0
  };
  const factionAbilityValues = {};
  const factionActionSelections = {};
  const factionMandateSources = {};
  const factionStandingTotals = {};
  let declarations = 0;
  let genuineAgi = 0;
  let auditHits = 0;
  let forcedNoOps = 0;
  let actionOpportunities = 0;
  let fallbacks = 0;
  for (const observation of observations) {
    actionOpportunities += observation.standings.length * 12;
    declarations += observation.declarations;
    genuineAgi += Number(observation.worldEndingId === "genuine_agi");
    for (const entry of observation.agiFunnel || []) {
      agiFunnel.playerOpportunities += 1;
      for (const stage of [
        "coreRequirementsMet",
        "neededExternalPower",
        "receivedPowerOffer",
        "acceptedPowerPrice",
        "becameGridReady",
        "legalDeclarationWindow",
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
      fallbacks += standing.policyFallbacks || 0;
      const standingTotals = factionStandingTotals[standing.factionId] || {
        appearances: 0,
        winCredit: 0,
        mandate: 0,
        rank: 0,
        auditHits: 0,
        forcedNoOps: 0
      };
      standingTotals.appearances += 1;
      standingTotals.winCredit += winnerCredit.get(standing.seat) || 0;
      standingTotals.mandate += standing.score || 0;
      standingTotals.rank += index + 1;
      standingTotals.auditHits += standing.auditHits || 0;
      standingTotals.forcedNoOps += standing.forcedNoOps || 0;
      factionStandingTotals[standing.factionId] = standingTotals;
      const actions = factionActionSelections[standing.factionId] || {};
      for (const [actionId, count] of Object.entries(standing.actions || {})) {
        actions[actionId] = (actions[actionId] || 0) + count;
      }
      factionActionSelections[standing.factionId] = actions;
      const faction = factionAbilityValues[standing.factionId] || {};
      for (const [abilityId, values] of Object.entries(
        standing.factionAbilityValues || {}
      )) {
        const ability = faction[abilityId] || {};
        for (const [key, value] of Object.entries(values)) {
          ability[key] = (ability[key] || 0) + value;
        }
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
      }
    }
  }
  return {
    matches: observations.length,
    declarationRate: observations.length ? declarations / observations.length : 0,
    genuineAgiRate: observations.length ? genuineAgi / observations.length : 0,
    meanAuditHitsPerMatch: observations.length ? auditHits / observations.length : 0,
    forcedNoOps,
    forcedNoOpRate: actionOpportunities ? forcedNoOps / actionOpportunities : 0,
    policyFallbacks: fallbacks,
    bindingRequirements,
    mandateSources,
    factionMandateSources,
    factionStandings: Object.fromEntries(
      Object.entries(factionStandingTotals).map(([factionId, totals]) => [
        factionId,
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
    ),
    factionAbilityValues,
    factionActionSelections,
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

function pairedRuleComparisons(observations, rulesConfigurations, alpha = 0.05) {
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
        "Common-seed paired deltas are diagnostic; positive rankDelta means the candidate improved placement. Promotion still requires the registered marginal gate and a tracked receipt.",
      families: {
        faction: summarize(["factionId"]),
        factionBackend: summarize(["factionId", "backendId"]),
        factionBackendPlayerCount: summarize([
          "playerCount",
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
  onProgress,
  progress
}) {
  const rows = [];
  const profileResult = (report, id) =>
    report.profiles.find((entry) => entry.profileId === id);
  const evaluate = async (candidate, opponents, phaseSeed) => {
    const report = await createSimulation({
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
      rulesVariant
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
  for (const configuration of rulesConfigurations) {
    if (!configuration.id || !configuration.overlay ||
        typeof configuration.overlay !== "object" ||
        Array.isArray(configuration.overlay)) {
      throw new TypeError("Every rules configuration requires id and overlay.");
    }
    if (
      configuration.id !== "canonical" &&
      Object.keys(configuration.overlay).length !== 1
    ) {
      throw new TypeError(
        `Rules configuration ${configuration.id} must change exactly one lever.`
      );
    }
  }
  const mandateModes = options.mandateModes || matrixContract.axes.mandateMode;
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
      options.profileOverrides === undefined
    ),
    matrixContractFingerprint: fingerprintObject(matrixContract),
    playerCounts,
    rulesConfigurations,
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

  const runCell = async (cell, requestedRuns, reason) => {
    const runs = Math.min(requestedRuns, matrixMatchLimit - executedMatches);
    if (runs <= 0) return;
    const runStart = cell.runs;
    const cellStarted = performance.now();
    const report = await createSimulation({
      runs,
      playerCount: cell.playerCount,
      seed: `${options.seed || "m3t4-unified-matrix"}:${cell.pairingId}:offset:${cell.runs}`,
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
      runOffset: cell.runs
    });
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
      elapsedMs: Math.round(performance.now() - cellStarted)
    });
    onProgress?.({
      phase: "unified_matrix",
      completed: executedMatches,
      total: settings.maximumMatches
    });
  };

  for (const cell of cells) {
    if (executedMatches >= matrixMatchLimit) break;
    await runCell(cell, settings.initialRunsPerCell, "preregistered_initial_coverage");
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
      seed: `${options.seed || "m3t4-unified-matrix"}:adversarial`,
      rulesVariant: options.rulesVariant || {},
      onProgress,
      progress
    })
    : {
      status: "not_run",
      reason: "Disabled for a fast contract test."
    };
  executedMatches = progress.completed;
  const outcomes = outcomeSummary(observations);
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
  const report = {
    reportType: "unified_matrix_audit",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(options.seed || "m3t4-unified-matrix"),
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
    configurationResults: Object.fromEntries(
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
    ),
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
      settings.alpha
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
      checks: [forcedNoOpCheck],
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
    experimentKind: "unified_matrix_audit"
  });
}
