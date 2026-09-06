import {
  classifyWinningPath,
  WINNING_PATH_CLASSIFIER
} from "../balance/winning-path.js";
import {
  outcomePlacementPoint,
  outcomeRanks
} from "../balance/outcome-placement.js";

function increment(target, key, amount = 1) {
  target[key] = (target[key] || 0) + amount;
}

function mergeCounts(target, source = {}) {
  for (const [key, value] of Object.entries(source)) increment(target, key, value);
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

function histogram(values) {
  const result = {};
  for (const value of values) increment(result, String(value));
  return result;
}

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function deviation(values) {
  const average = mean(values);
  return Math.sqrt(mean(values.map((value) => (value - average) ** 2)));
}

function range(values) {
  return values.length ? Math.max(...values) - Math.min(...values) : 0;
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

function summarizeEntries(entries, wins) {
  const actionCounts = {};
  const projectCounts = {};
  const providerCounts = {};
  const mandateCounts = {};
  let auditHits = 0;
  let eligibilityCount = 0;
  let eligibilityRoundTotal = 0;
  let fallbacks = 0;
  let declarations = 0;
  let shovelsIncome = 0;
  let powerBought = 0;
  let powerSold = 0;
  let powerTradeRunway = 0;
  for (const entry of entries) {
    auditHits += entry.metrics.auditHits;
    fallbacks += entry.metrics.policyFallbacks;
    declarations += Number(entry.agiDeclared);
    shovelsIncome += entry.metrics.shovelsIncome || 0;
    powerBought += entry.metrics.powerBought || 0;
    powerSold += entry.metrics.powerSold || 0;
    powerTradeRunway += entry.metrics.powerTradeRunway || 0;
    mergeCounts(actionCounts, entry.metrics.actions);
    mergeCounts(projectCounts, entry.metrics.projects);
    mergeCounts(providerCounts, entry.metrics.policyProviders);
    mergeCounts(mandateCounts, entry.metrics.mandatesWon);
    if (entry.metrics.earliestAgiEligibility) {
      eligibilityCount += 1;
      eligibilityRoundTotal += entry.metrics.earliestAgiEligibility.round;
    }
  }
  return {
    appearances: entries.length,
    winShare: entries.length ? wins / entries.length : 0,
    meanScore: mean(entries.map((entry) => entry.score)),
    scoreStdDev: deviation(entries.map((entry) => entry.score)),
    scoreDistribution: histogram(entries.map((entry) => entry.score)),
    meanCapability: mean(entries.map((entry) => entry.capability)),
    meanCustomers: mean(entries.map((entry) => entry.customers)),
    meanFacilities: mean(entries.map((entry) => entry.facilities)),
    meanAuditHits: auditHits / entries.length,
    agiEligibilityRate: eligibilityCount / entries.length,
    agiDeclarationRate: declarations / entries.length,
    meanShovelsIncome: shovelsIncome / entries.length,
    meanPowerBought: powerBought / entries.length,
    meanPowerSold: powerSold / entries.length,
    meanPowerTradeRunway: powerTradeRunway / entries.length,
    meanEarliestAgiRound: eligibilityCount
      ? eligibilityRoundTotal / eligibilityCount
      : null,
    actionCounts,
    actionDiversity: normalizedEntropy(actionCounts),
    projectCounts,
    mandateCounts,
    providerCounts,
    policyFallbacks: fallbacks
  };
}

function groupedSummary(outcomes, key) {
  const groups = new Map();
  for (const outcome of outcomes) {
    for (const entry of outcome.standings) {
      const id = entry[key];
      if (!groups.has(id)) groups.set(id, { entries: [], wins: 0 });
      const group = groups.get(id);
      group.entries.push(entry);
      if (outcome.winnerSeats.includes(entry.seat)) {
        group.wins += 1 / outcome.winnerSeats.length;
      }
    }
  }
  return [...groups.entries()].map(([id, group]) => ({
    [key]: id,
    ...summarizeEntries(group.entries, group.wins)
  }));
}

function compositeGroupedSummary(outcomes, keys) {
  const groups = new Map();
  for (const outcome of outcomes) {
    for (const entry of outcome.standings) {
      const id = keys.map((key) => entry[key]).join("::");
      if (!groups.has(id)) groups.set(id, { entries: [], wins: 0 });
      const group = groups.get(id);
      group.entries.push(entry);
      if (outcome.winnerSeats.includes(entry.seat)) group.wins += 1 / outcome.winnerSeats.length;
    }
  }
  return [...groups.entries()].map(([id, group]) => ({
    id,
    ...Object.fromEntries(keys.map((key, index) => [key, id.split("::")[index]])),
    ...summarizeEntries(group.entries, group.wins)
  }));
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

function profileMatchups(outcomes) {
  const pairs = new Map();
  for (const outcome of outcomes) {
    for (const left of outcome.standings) {
      for (const right of outcome.standings) {
        if (left.seat === right.seat || left.profileId === right.profileId) continue;
        const key = `${left.profileId}::${right.profileId}`;
        const row = pairs.get(key) || {
          profileId: left.profileId,
          opponentProfileId: right.profileId,
          comparisons: 0,
          placementPoints: 0,
          wins: 0
        };
        row.comparisons += 1;
        row.placementPoints += outcomePlacementPoint(outcome, left, right);
        if (outcome.winnerSeats.includes(left.seat)) row.wins += 1 / outcome.winnerSeats.length;
        pairs.set(key, row);
      }
    }
  }
  return [...pairs.values()].map((row) => ({
    ...row,
    relativePlacementRate: row.placementPoints / row.comparisons,
    matchWinRate: row.wins / row.comparisons
  }));
}

function metaCycles(matchups, edgeThreshold = 0.55) {
  const ids = [...new Set(matchups.flatMap((entry) => [
    entry.profileId,
    entry.opponentProfileId
  ]))].sort();
  const edge = (left, right) => matchups.some((entry) =>
    entry.profileId === left &&
    entry.opponentProfileId === right &&
    entry.comparisons >= 4 &&
    entry.relativePlacementRate >= edgeThreshold
  );
  const cycles = [];
  for (let a = 0; a < ids.length; a += 1) {
    for (let b = a + 1; b < ids.length; b += 1) {
      for (let c = b + 1; c < ids.length; c += 1) {
        const [x, y, z] = [ids[a], ids[b], ids[c]];
        if (edge(x, y) && edge(y, z) && edge(z, x)) cycles.push([x, y, z]);
        if (edge(x, z) && edge(z, y) && edge(y, x)) cycles.push([x, z, y]);
      }
    }
  }
  return { edgeThreshold, count: cycles.length, cycles };
}

function leaderPredictability(outcomes) {
  const result = {};
  const rounds = [...new Set(outcomes.flatMap((outcome) =>
    (outcome.matchMetrics?.productionSnapshots || []).map((entry) => entry.round)
  ))].sort((left, right) => left - right);
  for (const round of rounds) {
    let numerator = 0;
    let denominator = 0;
    for (const outcome of outcomes) {
      const snapshot = outcome.matchMetrics?.productionSnapshots?.find(
        (entry) => entry.round === round
      );
      if (!snapshot?.scores?.length) continue;
      const high = Math.max(...snapshot.scores.map((entry) => entry.mandate));
      const leaders = snapshot.scores.filter((entry) => entry.mandate === high);
      numerator += leaders.filter((entry) => outcome.winnerSeats.includes(entry.seat)).length /
        leaders.length;
      denominator += 1;
    }
    result[`round${round}`] = denominator ? numerator / denominator : null;
  }
  return result;
}

function integritySummary(outcomes) {
  const details = [];
  let policyFallbacks = 0;
  let forcedNoOps = 0;
  let tradeRequiredSelections = 0;
  let requiredTradeOffers = 0;
  let requiredTradeAcceptances = 0;
  let requiredTradeFailures = 0;
  let blockedAfterCommitment = 0;
  let actionOpportunities = 0;
  for (const [matchIndex, outcome] of outcomes.entries()) {
    actionOpportunities += outcome.standings.length * 12;
    if (outcome.matchMetrics?.productionSnapshots?.length !== 4) {
      details.push({ matchIndex, id: "production_count" });
    }
    const seats = new Set();
    for (const entry of outcome.standings) {
      seats.add(entry.seat);
      policyFallbacks += entry.metrics.policyFallbacks || 0;
      forcedNoOps += entry.metrics.forcedNoOps || 0;
      tradeRequiredSelections += entry.metrics.selectionAvailability?.tradeRequired || 0;
      requiredTradeOffers += entry.metrics.requiredTradeOffers || 0;
      requiredTradeAcceptances += entry.metrics.requiredTradeAcceptances || 0;
      requiredTradeFailures += entry.metrics.requiredTradeFailures || 0;
      blockedAfterCommitment += entry.metrics.blockedAfterCommitment || 0;
      for (const key of ["score", "trust", "customers", "compute", "capability", "facilities"]) {
        if (!Number.isFinite(entry[key]) || entry[key] < 0) {
          details.push({ matchIndex, seat: entry.seat, id: `invalid_${key}`, value: entry[key] });
        }
      }
      const actionCount = Object.values(entry.metrics.actions || {})
        .reduce((sum, value) => sum + value, 0);
      if (actionCount > 24) details.push({ matchIndex, seat: entry.seat, id: "action_amplification", value: actionCount });
    }
    if (seats.size !== outcome.standings.length) details.push({ matchIndex, id: "duplicate_seat" });
  }
  return {
    violations: details.length,
    details: details.slice(0, 100),
    policyFallbacks,
    forcedNoOps,
    forcedNoOpRate: actionOpportunities ? forcedNoOps / actionOpportunities : 0,
    tradeRequiredSelections,
    requiredTradeOffers,
    requiredTradeAcceptances,
    requiredTradeFailures,
    blockedAfterCommitment
  };
}

function aggregateMatchMetrics(outcomes) {
  const totals = {
    headlines: {},
    headlineOutcomes: {},
    mandates: {},
    projects: {},
    tactics: {},

    systemicRiskCreated: 0,
    declarations: 0,
    declarationPpaIterations: 0,
    declarationCapacityOps: 0,
    agiResolution: {
      opportunities: 0,
      emerged: 0,
      claimantRegistrations: 0,
      selectedClaimant: 0,
      winnerOverrides: 0,
      selectedMandateRanks: {}
    },
    agiFunnel: {
      playerOpportunities: 0,
      coreRequirementsMet: 0,
      legalDeclarationWindow: 0,
      claimRegistered: 0,
      emergenceTriggered: 0,
      declared: 0
    },
    factionAbilityValues: {},
    factionActionSelections: {},
    profileActionSelections: {},
    profileMandateSources: {},
    powerTrades: 0,
    causallyNecessaryPowerTrades: 0,
    cooperativeDeclarationMatches: 0,
    supplierSupportMatches: 0,
    supplierWins: 0,
    supplierTopHalfFinishes: 0,
    supplierFinalScoreGap: 0,
    supplierRound4ScoreGap: 0,
    worldEndings: {},
    nonDeclaringWins: 0,
    negotiationOutcomes: {}
  };
  for (const outcome of outcomes) {
    const metrics = outcome.matchMetrics || {};
    for (const key of [
      "headlines",
      "headlineOutcomes",
      "mandates",
      "projects",
      "tactics"
    ]) {
      mergeCounts(totals[key], metrics[key]);
    }
    totals.systemicRiskCreated += metrics.systemicRiskCreated || 0;
    totals.declarations += metrics.declarations || 0;
    if (metrics.agiResolution) {
      const resolution = metrics.agiResolution;
      totals.agiResolution.opportunities += 1;
      totals.agiResolution.claimantRegistrations +=
        resolution.claimantSeats?.length || 0;
      if (resolution.emerged) {
        totals.agiResolution.emerged += 1;
        totals.agiResolution.selectedClaimant += Number(
          resolution.selectedWasClaimant
        );
        totals.agiResolution.winnerOverrides += Number(
          resolution.winnerOverridden
        );
        increment(
          totals.agiResolution.selectedMandateRanks,
          String(resolution.selectedMandateRank)
        );
      }
    }
    for (const entry of metrics.agiFunnel || []) {
      totals.agiFunnel.playerOpportunities += 1;
      for (const stage of [
        "coreRequirementsMet",
        "legalDeclarationWindow",
        "claimRegistered",
        "emergenceTriggered",
        "declared"
      ]) {
        totals.agiFunnel[stage] += Number(Boolean(entry[stage]));
      }
    }
    for (const standing of outcome.standings) {
      const actions = totals.factionActionSelections[standing.factionId] || {};
      mergeCounts(actions, standing.metrics.actions || {});
      totals.factionActionSelections[standing.factionId] = actions;
      const profileActions =
        totals.profileActionSelections[standing.profileId] || {};
      mergeCounts(profileActions, standing.metrics.actions || {});
      totals.profileActionSelections[standing.profileId] = profileActions;
      const profileSources =
        totals.profileMandateSources[standing.profileId] || {};
      for (const event of standing.metrics.mandateEvents || []) {
        increment(profileSources, event.source || "unknown", event.points || 0);
      }
      totals.profileMandateSources[standing.profileId] = profileSources;
      const faction = totals.factionAbilityValues[standing.factionId] || {};
      for (const [abilityId, values] of Object.entries(
        standing.metrics.factionAbilityValues || {}
      )) {
        const ability = faction[abilityId] || {};
        mergeAbilityTelemetry(ability, values);
        faction[abilityId] = ability;
      }
      totals.factionAbilityValues[standing.factionId] = faction;
    }
    totals.powerTrades += metrics.powerTrades?.length || 0;
    for (const negotiation of metrics.negotiations || []) {
      if (["fulfilled", "broken", "superseded", "unexercised"].includes(
        negotiation.status
      )) {
        increment(totals.negotiationOutcomes, negotiation.status);
      }
    }
    totals.causallyNecessaryPowerTrades +=
      metrics.powerTrades?.filter((trade) => trade.causallyNecessary).length || 0;
    for (const readiness of metrics.declarationReadiness || []) {
      totals.declarationPpaIterations += readiness.ppaIterations || 0;
      totals.declarationCapacityOps += readiness.capacityOps || 0;
    }
    increment(totals.worldEndings, outcome.worldEnding?.id || "unknown");
    const supportingSeats = new Set(
      (metrics.declarationReadiness || [])
        .filter((entry) => entry.ready)
        .flatMap((entry) => entry.supportingSeats || [])
    );
    if (supportingSeats.size) totals.cooperativeDeclarationMatches += 1;
    const ranks = outcomeRanks(outcome);
    const standingsBySeat = new Map(outcome.standings.map((entry, index) => [
      entry.seat,
      { ...entry, rank: ranks.get(entry.seat) || index + 1 }
    ]));
    const winnerScore = outcome.standings[0]?.score || 0;
    const round4BySeat = new Map(
      (metrics.round4Start || []).map((entry) => [entry.seat, entry.score])
    );
    const round4Lead = Math.max(0, ...round4BySeat.values());
    for (const seat of supportingSeats) {
      const standing = standingsBySeat.get(seat);
      if (!standing) continue;
      totals.supplierSupportMatches += 1;
      if (outcome.winnerSeats.includes(seat)) {
        totals.supplierWins += 1 / outcome.winnerSeats.length;
      }
      if (standing.rank <= Math.ceil(outcome.standings.length / 2)) {
        totals.supplierTopHalfFinishes += 1;
      }
      totals.supplierFinalScoreGap += winnerScore - standing.score;
      totals.supplierRound4ScoreGap +=
        round4Lead - (round4BySeat.get(seat) || 0);
    }
    for (const seat of outcome.winnerSeats) {
      const winner = outcome.standings.find((entry) => entry.seat === seat);
      if (winner && !winner.agiDeclared) totals.nonDeclaringWins += 1 / outcome.winnerSeats.length;
    }
  }
  return {
    ...totals,
    agiFunnelRates: Object.fromEntries(
      Object.entries(totals.agiFunnel)
        .filter(([stage]) => stage !== "playerOpportunities")
        .map(([stage, count]) => [
          stage,
          totals.agiFunnel.playerOpportunities
            ? count / totals.agiFunnel.playerOpportunities
            : 0
        ])
    ),
    meanSystemicRiskCreated: totals.systemicRiskCreated / outcomes.length,
    declarationRate: totals.declarations / outcomes.length,
    powerTradesPerMatch: totals.powerTrades / outcomes.length,
    causallyNecessaryPowerTradesPerMatch:
      totals.causallyNecessaryPowerTrades / outcomes.length,
    cooperativeDeclarationRate:
      totals.cooperativeDeclarationMatches / outcomes.length,
    supplierCompetitiveRate: totals.supplierSupportMatches
      ? totals.supplierTopHalfFinishes / totals.supplierSupportMatches
      : 0,
    supplierWinRate: totals.supplierSupportMatches
      ? totals.supplierWins / totals.supplierSupportMatches
      : 0,
    supplierMeanFinalScoreGap: totals.supplierSupportMatches
      ? totals.supplierFinalScoreGap / totals.supplierSupportMatches
      : null,
    supplierMeanRound4ScoreGap: totals.supplierSupportMatches
      ? totals.supplierRound4ScoreGap / totals.supplierSupportMatches
      : null,
    meanPpaIterationsPerDeclaration: totals.declarations
      ? totals.declarationPpaIterations / totals.declarations
      : 0,
    meanCapacityOpsPerDeclaration: totals.declarations
      ? totals.declarationCapacityOps / totals.declarations
      : 0,
    nonDeclaringWinRate: totals.nonDeclaringWins / outcomes.length
  };
}

function createSummaryAccumulator() {
  return {
    appearances: 0,
    wins: 0,
    scores: [],
    capability: 0,
    customers: 0,
    facilities: 0,
    auditHits: 0,
    eligibilityCount: 0,
    eligibilityRoundTotal: 0,
    declarations: 0,
    shovelsIncome: 0,
    powerBought: 0,
    powerSold: 0,
    powerTradeRunway: 0,
    policyFallbacks: 0,
    actionCounts: {},
    projectCounts: {},
    providerCounts: {},
    mandateCounts: {}
  };
}

function addSummaryEntry(accumulator, entry, winCredit) {
  accumulator.appearances += 1;
  accumulator.wins += winCredit;
  accumulator.scores.push(entry.score);
  accumulator.capability += entry.capability;
  accumulator.customers += entry.customers;
  accumulator.facilities += entry.facilities;
  accumulator.auditHits += entry.metrics.auditHits;
  accumulator.policyFallbacks += entry.metrics.policyFallbacks;
  accumulator.declarations += Number(entry.agiDeclared);
  accumulator.shovelsIncome += entry.metrics.shovelsIncome || 0;
  accumulator.powerBought += entry.metrics.powerBought || 0;
  accumulator.powerSold += entry.metrics.powerSold || 0;
  accumulator.powerTradeRunway += entry.metrics.powerTradeRunway || 0;
  mergeCounts(accumulator.actionCounts, entry.metrics.actions);
  mergeCounts(accumulator.projectCounts, entry.metrics.projects);
  mergeCounts(accumulator.providerCounts, entry.metrics.policyProviders);
  mergeCounts(accumulator.mandateCounts, entry.metrics.mandatesWon);
  if (entry.metrics.earliestAgiEligibility) {
    accumulator.eligibilityCount += 1;
    accumulator.eligibilityRoundTotal += entry.metrics.earliestAgiEligibility.round;
  }
}

function summarizeAccumulator(accumulator) {
  const appearances = accumulator.appearances;
  return {
    appearances,
    winShare: appearances ? accumulator.wins / appearances : 0,
    meanScore: mean(accumulator.scores),
    scoreStdDev: deviation(accumulator.scores),
    scoreDistribution: histogram(accumulator.scores),
    meanCapability: appearances ? accumulator.capability / appearances : 0,
    meanCustomers: appearances ? accumulator.customers / appearances : 0,
    meanFacilities: appearances ? accumulator.facilities / appearances : 0,
    meanAuditHits: appearances ? accumulator.auditHits / appearances : 0,
    agiEligibilityRate: appearances ? accumulator.eligibilityCount / appearances : 0,
    agiDeclarationRate: appearances ? accumulator.declarations / appearances : 0,
    meanShovelsIncome: appearances ? accumulator.shovelsIncome / appearances : 0,
    meanPowerBought: appearances ? accumulator.powerBought / appearances : 0,
    meanPowerSold: appearances ? accumulator.powerSold / appearances : 0,
    meanPowerTradeRunway: appearances ? accumulator.powerTradeRunway / appearances : 0,
    meanEarliestAgiRound: accumulator.eligibilityCount
      ? accumulator.eligibilityRoundTotal / accumulator.eligibilityCount
      : null,
    actionCounts: accumulator.actionCounts,
    actionDiversity: normalizedEntropy(accumulator.actionCounts),
    projectCounts: accumulator.projectCounts,
    mandateCounts: accumulator.mandateCounts,
    providerCounts: accumulator.providerCounts,
    policyFallbacks: accumulator.policyFallbacks
  };
}

function compactObservation(outcome, matchIndex) {
  return {
    matchIndex,
    winnerSeats: outcome.winnerSeats,
    standings: outcome.standings.map((entry) => ({
      seat: entry.seat,
      factionId: entry.factionId,
      profileId: entry.profileId,
      backendId: entry.backendId,
      score: entry.score,
      capability: entry.capability,
      facilities: entry.facilities,
      customers: entry.customers,
      trust: entry.trust,
      agiDeclared: entry.agiDeclared,
      openingActions: entry.metrics.openingActions,
      actions: entry.metrics.actions,
      forcedNoOps: entry.metrics.forcedNoOps,
      selectionAvailability: entry.metrics.selectionAvailability,
      requiredTradeOffers: entry.metrics.requiredTradeOffers,
      requiredTradeAcceptances: entry.metrics.requiredTradeAcceptances,
      requiredTradeFailures: entry.metrics.requiredTradeFailures,
      blockedAfterCommitment: entry.metrics.blockedAfterCommitment,
      policyFallbacks: entry.metrics.policyFallbacks,
      auditHits: entry.metrics.auditHits,
      mandateEvents: entry.metrics.mandateEvents,
      promisesMade: entry.metrics.promisesMade,
      promisesFulfilled: entry.metrics.promisesFulfilled,
      promisesBroken: entry.metrics.promisesBroken,
      dealFlowConversion: entry.metrics.dealFlowConversion,
      factionAbilityValues: entry.metrics.factionAbilityValues,
      policyReceipts: entry.metrics.policyReceipts
    })),
    worldEndingId: outcome.worldEnding?.id || "unknown",
    worldEnding: outcome.worldEnding,
    powerTrades: outcome.matchMetrics?.powerTrades || [],
    negotiations: outcome.matchMetrics?.negotiations || [],
    declarationReadiness: outcome.matchMetrics?.declarationReadiness || [],
    agiFunnel: outcome.matchMetrics?.agiFunnel || [],
    scenario: outcome.matchMetrics?.scenario || null,
    declarations: outcome.matchMetrics?.declarations || 0,

    systemicRiskCreated: outcome.matchMetrics?.systemicRiskCreated || 0,
    futureTimeline: outcome.matchMetrics?.futureTimeline || []
  };
}

class BatchAccumulator {
  constructor() {
    this.scope = null;
    this.rulesVariant = null;
    this.playerCount = null;
    this.seats = new Map();
    this.factions = new Map();
    this.profiles = new Map();
    this.backends = new Map();
    this.factionStrategies = new Map();
    this.factionBackends = new Map();
    this.strategyBackends = new Map();
    this.matchups = new Map();
    this.openingCounts = {};
    this.winningPathCounts = {};
    this.scores = [];
    this.roundLeaders = new Map();
    this.integrity = {
      details: [],
      policyFallbacks: 0,
      forcedNoOps: 0,
      actionOpportunities: 0,
      tradeRequiredSelections: 0,
      requiredTradeOffers: 0,
      requiredTradeAcceptances: 0,
      requiredTradeFailures: 0,
      blockedAfterCommitment: 0
    };
    this.metrics = {
      headlines: {}, headlineOutcomes: {}, mandates: {}, projects: {}, tactics: {},
      systemicRiskCreated: 0, declarations: 0, declarationPpaIterations: 0, declarationCapacityOps: 0,
      agiFunnel: {
        playerOpportunities: 0, coreRequirementsMet: 0,
        legalDeclarationWindow: 0, claimRegistered: 0,
        emergenceTriggered: 0, declared: 0
      },
      agiResolution: {
        opportunities: 0,
        emerged: 0,
        claimantRegistrations: 0,
        selectedClaimant: 0,
        winnerOverrides: 0,
        selectedMandateRanks: {}
      },
      factionAbilityValues: {}, factionActionSelections: {},
      profileActionSelections: {}, profileMandateSources: {}, powerTrades: 0,
      causallyNecessaryPowerTrades: 0, cooperativeDeclarationMatches: 0,
      supplierSupportMatches: 0, supplierWins: 0, supplierTopHalfFinishes: 0,
      supplierFinalScoreGap: 0, supplierRound4ScoreGap: 0, worldEndings: {},
      nonDeclaringWins: 0, negotiationOutcomes: {}
    };
    this.outcomeCount = 0;
  }

  group(map, key, entry, winCredit, fields = {}) {
    if (!map.has(key)) map.set(key, { accumulator: createSummaryAccumulator(), ...fields });
    addSummaryEntry(map.get(key).accumulator, entry, winCredit);
  }

  add(outcome, matchIndex) {
    this.scope ||= outcome.scope;
    this.rulesVariant ||= outcome.rulesVariant;
    this.playerCount ||= outcome.standings.length;
    this.outcomeCount += 1;
    const winnerCredit = 1 / outcome.winnerSeats.length;
    const winningSeats = new Set(outcome.winnerSeats);
    this.integrity.actionOpportunities += outcome.standings.length * 12;
    if (outcome.matchMetrics?.productionSnapshots?.length !== 4) {
      this.integrity.details.push({ matchIndex, id: "production_count" });
    }
    const seenSeats = new Set();
    for (const entry of outcome.standings) {
      const credit = winningSeats.has(entry.seat) ? winnerCredit : 0;
      seenSeats.add(entry.seat);
      this.scores.push(entry.score);
      const seat = this.seats.get(entry.seat) || {
        accumulator: createSummaryAccumulator(), factionIds: new Set(), profileIds: new Set()
      };
      seat.factionIds.add(entry.factionId);
      seat.profileIds.add(entry.profileId);
      addSummaryEntry(seat.accumulator, entry, credit);
      this.seats.set(entry.seat, seat);
      this.group(this.factions, entry.factionId, entry, credit, { factionId: entry.factionId });
      this.group(this.profiles, entry.profileId, entry, credit, { profileId: entry.profileId });
      this.group(this.backends, entry.backendId, entry, credit, { backendId: entry.backendId });
      this.group(this.factionStrategies, `${entry.factionId}::${entry.profileId}`, entry, credit, {
        id: `${entry.factionId}::${entry.profileId}`,
        factionId: entry.factionId,
        profileId: entry.profileId
      });
      this.group(this.factionBackends, `${entry.factionId}::${entry.backendId}`, entry, credit, {
        id: `${entry.factionId}::${entry.backendId}`,
        factionId: entry.factionId,
        backendId: entry.backendId
      });
      this.group(this.strategyBackends, `${entry.profileId}::${entry.backendId}`, entry, credit, {
        id: `${entry.profileId}::${entry.backendId}`,
        profileId: entry.profileId,
        backendId: entry.backendId
      });
      increment(this.openingCounts, (entry.metrics.openingActions || []).join("→") || "none");
      if (credit) increment(this.winningPathCounts, classifyWinningPath(entry), credit);
      this.integrity.policyFallbacks += entry.metrics.policyFallbacks || 0;
      this.integrity.forcedNoOps += entry.metrics.forcedNoOps || 0;
      this.integrity.tradeRequiredSelections +=
        entry.metrics.selectionAvailability?.tradeRequired || 0;
      this.integrity.requiredTradeOffers += entry.metrics.requiredTradeOffers || 0;
      this.integrity.requiredTradeAcceptances +=
        entry.metrics.requiredTradeAcceptances || 0;
      this.integrity.requiredTradeFailures += entry.metrics.requiredTradeFailures || 0;
      this.integrity.blockedAfterCommitment +=
        entry.metrics.blockedAfterCommitment || 0;
      for (const key of ["score", "trust", "customers", "compute", "capability", "facilities"]) {
        if (!Number.isFinite(entry[key]) || entry[key] < 0) {
          this.integrity.details.push({ matchIndex, seat: entry.seat, id: `invalid_${key}`, value: entry[key] });
        }
      }
      const actionCount = Object.values(entry.metrics.actions || {}).reduce((sum, value) => sum + value, 0);
      if (actionCount > 24) this.integrity.details.push({ matchIndex, seat: entry.seat, id: "action_amplification", value: actionCount });
    }
    if (seenSeats.size !== outcome.standings.length) this.integrity.details.push({ matchIndex, id: "duplicate_seat" });
    for (const left of outcome.standings) {
      for (const right of outcome.standings) {
        if (left.seat === right.seat || left.profileId === right.profileId) continue;
        const key = `${left.profileId}::${right.profileId}`;
        const row = this.matchups.get(key) || {
          profileId: left.profileId, opponentProfileId: right.profileId,
          comparisons: 0, placementPoints: 0, wins: 0
        };
        row.comparisons += 1;
        row.placementPoints += outcomePlacementPoint(outcome, left, right);
        if (winningSeats.has(left.seat)) row.wins += winnerCredit;
        this.matchups.set(key, row);
      }
    }
    for (const snapshot of outcome.matchMetrics?.productionSnapshots || []) {
      if (!snapshot?.scores?.length) continue;
      const high = Math.max(...snapshot.scores.map((entry) => entry.mandate));
      const leaders = snapshot.scores.filter((entry) => entry.mandate === high);
      const row = this.roundLeaders.get(snapshot.round) || { numerator: 0, denominator: 0 };
      row.numerator += leaders.filter((entry) => winningSeats.has(entry.seat)).length / leaders.length;
      row.denominator += 1;
      this.roundLeaders.set(snapshot.round, row);
    }
    this.addMetrics(outcome);
  }

  addMetrics(outcome) {
    const totals = this.metrics;
    const metrics = outcome.matchMetrics || {};
    for (const key of ["headlines", "headlineOutcomes", "mandates", "projects", "tactics"]) {
      mergeCounts(totals[key], metrics[key]);
    }
    totals.systemicRiskCreated += metrics.systemicRiskCreated || 0;
    totals.declarations += metrics.declarations || 0;
    if (metrics.agiResolution) {
      const resolution = metrics.agiResolution;
      totals.agiResolution.opportunities += 1;
      totals.agiResolution.claimantRegistrations +=
        resolution.claimantSeats?.length || 0;
      if (resolution.emerged) {
        totals.agiResolution.emerged += 1;
        totals.agiResolution.selectedClaimant += Number(
          resolution.selectedWasClaimant
        );
        totals.agiResolution.winnerOverrides += Number(
          resolution.winnerOverridden
        );
        increment(
          totals.agiResolution.selectedMandateRanks,
          String(resolution.selectedMandateRank)
        );
      }
    }
    for (const entry of metrics.agiFunnel || []) {
      totals.agiFunnel.playerOpportunities += 1;
      for (const stage of ["coreRequirementsMet", "legalDeclarationWindow", "claimRegistered", "emergenceTriggered", "declared"]) {
        totals.agiFunnel[stage] += Number(Boolean(entry[stage]));
      }
    }
    for (const standing of outcome.standings) {
      const actions = totals.factionActionSelections[standing.factionId] || {};
      mergeCounts(actions, standing.metrics.actions || {});
      totals.factionActionSelections[standing.factionId] = actions;
      const profileActions =
        totals.profileActionSelections[standing.profileId] || {};
      mergeCounts(profileActions, standing.metrics.actions || {});
      totals.profileActionSelections[standing.profileId] = profileActions;
      const profileSources =
        totals.profileMandateSources[standing.profileId] || {};
      for (const event of standing.metrics.mandateEvents || []) {
        increment(profileSources, event.source || "unknown", event.points || 0);
      }
      totals.profileMandateSources[standing.profileId] = profileSources;
      const faction = totals.factionAbilityValues[standing.factionId] || {};
      for (const [abilityId, values] of Object.entries(standing.metrics.factionAbilityValues || {})) {
        const ability = faction[abilityId] || {};
        mergeAbilityTelemetry(ability, values);
        faction[abilityId] = ability;
      }
      totals.factionAbilityValues[standing.factionId] = faction;
    }
    totals.powerTrades += metrics.powerTrades?.length || 0;
    for (const negotiation of metrics.negotiations || []) {
      if (["fulfilled", "broken", "superseded", "unexercised"].includes(negotiation.status)) {
        increment(totals.negotiationOutcomes, negotiation.status);
      }
    }
    totals.causallyNecessaryPowerTrades += metrics.powerTrades?.filter((trade) => trade.causallyNecessary).length || 0;
    for (const readiness of metrics.declarationReadiness || []) {
      totals.declarationPpaIterations += readiness.ppaIterations || 0;
      totals.declarationCapacityOps += readiness.capacityOps || 0;
    }
    increment(totals.worldEndings, outcome.worldEnding?.id || "unknown");
    const supportingSeats = new Set((metrics.declarationReadiness || [])
      .filter((entry) => entry.ready).flatMap((entry) => entry.supportingSeats || []));
    if (supportingSeats.size) totals.cooperativeDeclarationMatches += 1;
    const ranks = outcomeRanks(outcome);
    const standingsBySeat = new Map(outcome.standings.map((entry, index) => [
      entry.seat,
      { ...entry, rank: ranks.get(entry.seat) || index + 1 }
    ]));
    const winnerScore = outcome.standings[0]?.score || 0;
    const round4BySeat = new Map((metrics.round4Start || []).map((entry) => [entry.seat, entry.score]));
    const round4Lead = Math.max(0, ...round4BySeat.values());
    for (const seat of supportingSeats) {
      const standing = standingsBySeat.get(seat);
      if (!standing) continue;
      totals.supplierSupportMatches += 1;
      if (outcome.winnerSeats.includes(seat)) totals.supplierWins += 1 / outcome.winnerSeats.length;
      if (standing.rank <= Math.ceil(outcome.standings.length / 2)) totals.supplierTopHalfFinishes += 1;
      totals.supplierFinalScoreGap += winnerScore - standing.score;
      totals.supplierRound4ScoreGap += round4Lead - (round4BySeat.get(seat) || 0);
    }
    for (const seat of outcome.winnerSeats) {
      const winner = outcome.standings.find((entry) => entry.seat === seat);
      if (winner && !winner.agiDeclared) totals.nonDeclaringWins += 1 / outcome.winnerSeats.length;
    }
  }

  grouped(map) {
    return [...map.values()].map(({ accumulator, ...fields }) => ({
      ...fields,
      ...summarizeAccumulator(accumulator)
    }));
  }

  result({ runs, seed, samples, observations }) {
    const seats = [...this.seats.entries()].sort(([left], [right]) => left - right).map(([seat, entry]) => ({
      seat,
      factionIds: [...entry.factionIds],
      profileIds: [...entry.profileIds],
      ...summarizeAccumulator(entry.accumulator)
    }));
    const factions = this.grouped(this.factions);
    const profiles = this.grouped(this.profiles);
    const backends = this.grouped(this.backends);
    const factionStrategies = this.grouped(this.factionStrategies);
    const factionBackends = this.grouped(this.factionBackends);
    const strategyBackends = this.grouped(this.strategyBackends);
    // Match rich aggregation order exactly.  Accumulating by final standings
    // changes floating-point entropy at the last decimal even with identical
    // counts, because rich mode merges the seat summaries in seat order.
    const allActionCounts = {};
    for (const seat of seats) mergeCounts(allActionCounts, seat.actionCounts);
    const matchups = [...this.matchups.values()].map((row) => ({
      ...row,
      relativePlacementRate: row.placementPoints / row.comparisons,
      matchWinRate: row.wins / row.comparisons
    }));
    const matchupMax = Math.max(0, ...matchups.filter((entry) => entry.comparisons >= 4)
      .map((entry) => entry.relativePlacementRate));
    const leaderPredictability = Object.fromEntries([...this.roundLeaders.entries()]
      .sort(([left], [right]) => left - right)
      .map(([round, entry]) => [`round${round}`, entry.denominator ? entry.numerator / entry.denominator : null]));
    const integrity = {
      violations: this.integrity.details.length,
      details: this.integrity.details.slice(0, 100),
      policyFallbacks: this.integrity.policyFallbacks,
      forcedNoOps: this.integrity.forcedNoOps,
      forcedNoOpRate: this.integrity.actionOpportunities
        ? this.integrity.forcedNoOps / this.integrity.actionOpportunities
        : 0,
      tradeRequiredSelections: this.integrity.tradeRequiredSelections,
      requiredTradeOffers: this.integrity.requiredTradeOffers,
      requiredTradeAcceptances: this.integrity.requiredTradeAcceptances,
      requiredTradeFailures: this.integrity.requiredTradeFailures,
      blockedAfterCommitment: this.integrity.blockedAfterCommitment
    };
    const metrics = this.metrics;
    const matchMetrics = {
      ...metrics,
      agiFunnelRates: Object.fromEntries(Object.entries(metrics.agiFunnel)
        .filter(([stage]) => stage !== "playerOpportunities")
        .map(([stage, count]) => [stage, metrics.agiFunnel.playerOpportunities
          ? count / metrics.agiFunnel.playerOpportunities : 0])),
      meanSystemicRiskCreated: metrics.systemicRiskCreated / runs,
      declarationRate: metrics.declarations / runs,
      powerTradesPerMatch: metrics.powerTrades / runs,
      causallyNecessaryPowerTradesPerMatch: metrics.causallyNecessaryPowerTrades / runs,
      cooperativeDeclarationRate: metrics.cooperativeDeclarationMatches / runs,
      supplierCompetitiveRate: metrics.supplierSupportMatches
        ? metrics.supplierTopHalfFinishes / metrics.supplierSupportMatches : 0,
      supplierWinRate: metrics.supplierSupportMatches ? metrics.supplierWins / metrics.supplierSupportMatches : 0,
      supplierMeanFinalScoreGap: metrics.supplierSupportMatches
        ? metrics.supplierFinalScoreGap / metrics.supplierSupportMatches : null,
      supplierMeanRound4ScoreGap: metrics.supplierSupportMatches
        ? metrics.supplierRound4ScoreGap / metrics.supplierSupportMatches : null,
      meanPpaIterationsPerDeclaration: metrics.declarations
        ? metrics.declarationPpaIterations / metrics.declarations : 0,
      meanCapacityOpsPerDeclaration: metrics.declarations
        ? metrics.declarationCapacityOps / metrics.declarations : 0,
      nonDeclaringWinRate: metrics.nonDeclaringWins / runs
    };
    const diagnostics = {
      seatWinShareRange: range(seats.map((seat) => seat.winShare)),
      factionWinShareRange: range(factions.map((faction) => faction.winShare)),
      profileWinShareRange: range(profiles.map((profile) => profile.winShare)),
      scoreStdDev: deviation(this.scores),
      actionDiversity: normalizedEntropy(allActionCounts),
      openingDiversity: concentration(this.openingCounts),
      winningPathDiversity: concentration(this.winningPathCounts),
      winningPathClassifier: WINNING_PATH_CLASSIFIER,
      factionStrategyInteractionRange: range(factionStrategies.filter((entry) => entry.appearances >= 4).map((entry) => entry.winShare)),
      leaderPredictability,
      pairwiseDominance: matchupMax,
      cyclicMeta: metaCycles(matchups),
      integrity,
      agiEligibilityRate: mean(seats.map((seat) => seat.agiEligibilityRate)),
      agiDeclarationRate: mean(seats.map((seat) => seat.agiDeclarationRate)),
      agiEmergenceRate: (
        (metrics.worldEndings.singularity || 0) + (metrics.worldEndings.closed_loop || 0)
      ) / runs,
      openContinuityRate: (
        (metrics.worldEndings.singularity || 0) + (metrics.worldEndings.plural_future || 0)
      ) / runs,
      nonDeclaringWinRate: metrics.nonDeclaringWins / runs
    };
    diagnostics.alerts = [
      ...(diagnostics.seatWinShareRange > 0.15 ? [{ id: "seat_bias", severity: "high", value: diagnostics.seatWinShareRange }] : []),
      ...(diagnostics.factionWinShareRange > 0.15 ? [{ id: "faction_spread", severity: "high", value: diagnostics.factionWinShareRange }] : []),
      ...(diagnostics.actionDiversity < 0.72 ? [{ id: "action_collapse", severity: "high", value: diagnostics.actionDiversity }] : []),
      ...(diagnostics.agiEmergenceRate < 0.03 ? [{ id: "agi_drought", severity: "medium", value: diagnostics.agiEmergenceRate }] : []),
      ...(diagnostics.agiEmergenceRate > 0.08 ? [{ id: "agi_flood", severity: "medium", value: diagnostics.agiEmergenceRate }] : []),
      ...(diagnostics.openContinuityRate === 0 ? [{ id: "closed_continuity_only", severity: "medium", value: diagnostics.openContinuityRate }] : [])
    ];
    return {
      schemaVersion: 2,
      reportType: "tournament",
      evidenceLabel: "simulation",
      generatedAt: new Date().toISOString(),
      seed: String(seed),
      runs,
      playerCount: this.playerCount,
      scope: this.scope,
      rulesVariant: this.rulesVariant,
      seats, factions, profiles, backends, factionStrategies, factionBackends, strategyBackends,
      profileMatchups: matchups, diagnostics, matchMetrics, samples,
      ...(observations ? { observations } : {})
    };
  }
}

export async function runMonteCarlo({
  runs,
  seed,
  createMatch,
  policies,
  policiesForRun,
  sampleReplays = 3,
  includeObservations = false,
  projection = "rich",
  runOffset = 0,
  sampleReplaysGlobal = false,
  precomputedOutcomes = null,
  returnOutcomes = false,
  signal,
  onProgress,
  onCompletedOutcome
}) {
  if (!Number.isInteger(runs) || runs < 1) {
    throw new RangeError("Monte Carlo runs must be a positive integer.");
  }
  if (!["rich", "batch"].includes(projection)) {
    throw new TypeError(`Unknown Monte Carlo projection: ${projection}.`);
  }
  const outcomes = [];
  const samples = [];
  const observations = includeObservations ? [] : null;
  const batch = projection === "batch" ? new BatchAccumulator() : null;
  const rawOutcomes = returnOutcomes ? [] : null;
  let scope;

  const consume = (reportOutcome, run, fullOutcome = null) => {
    scope ||= reportOutcome.scope;
    if (batch) batch.add(reportOutcome, run);
    else outcomes.push(reportOutcome);
    if (fullOutcome) samples.push(fullOutcome);
    if (observations) observations.push(compactObservation(reportOutcome, run));
  };

  if (precomputedOutcomes) {
    if (precomputedOutcomes.length !== runs) {
      throw new RangeError("Precomputed Monte Carlo outcomes must match runs.");
    }
    for (const entry of [...precomputedOutcomes].sort(
      (left, right) => left.runIndex - right.runIndex
    )) {
      consume(entry.outcome, entry.runIndex, entry.fullOutcome || null);
    }
  } else for (let run = 0; run < runs; run += 1) {
    if (signal?.aborted) throw signal.reason;
    const replayIndex = sampleReplaysGlobal ? run + runOffset : run;
    const match = createMatch({
      seed: `${seed}:run:${run + runOffset}`,
      recordReplay: replayIndex < sampleReplays,
      runIndex: run
    });
    const outcome = await match.play(
      policiesForRun ? policiesForRun(run) : policies
    );
    const reportOutcome = {
      scope: outcome.scope,
      winnerSeats: outcome.winnerSeats,
      standings: outcome.standings,
      matchMetrics: outcome.matchMetrics,
      rulesVariant: outcome.rulesVariant,
      worldEnding: outcome.worldEnding
    };
    const fullOutcome = replayIndex < sampleReplays ? outcome : null;
    consume(reportOutcome, run, fullOutcome);
    if (onCompletedOutcome) {
      await onCompletedOutcome({
        runIndex: run + runOffset,
        outcome,
        reportOutcome
      });
    }
    if (rawOutcomes) rawOutcomes.push({
      runIndex: run + runOffset,
      outcome: reportOutcome,
      ...(fullOutcome ? { fullOutcome } : {})
    });
    if (onProgress && (run + 1 === runs || (run + 1) % 25 === 0)) {
      onProgress({ completed: run + 1, runs });
    }
    // Yield only cancellable jobs so the server can receive the cancel request.
    if (signal) await new Promise((resolve) => setImmediate(resolve));
  }

  const result = batch
    ? batch.result({
      runs,
      seed,
      samples,
      observations
    })
    : null;

  if (result) return returnOutcomes ? { report: result, rawOutcomes } : result;

  const seatCount = outcomes[0].standings.length;
  const seats = Array.from({ length: seatCount }, (_, seat) => {
    const entries = outcomes.map((outcome) =>
      outcome.standings.find((standing) => standing.seat === seat)
    );
    let wins = 0;
    for (const [index, entry] of entries.entries()) {
      if (outcomes[index].winnerSeats.includes(entry.seat)) {
        wins += 1 / outcomes[index].winnerSeats.length;
      }
    }
    return {
      seat,
      factionIds: [...new Set(entries.map((entry) => entry.factionId))],
      profileIds: [...new Set(entries.map((entry) => entry.profileId))],
      ...summarizeEntries(entries, wins)
    };
  });
  const factions = groupedSummary(outcomes, "factionId");
  const profiles = groupedSummary(outcomes, "profileId");
  const backends = groupedSummary(outcomes, "backendId");
  const factionStrategies = compositeGroupedSummary(outcomes, ["factionId", "profileId"]);
  const factionBackends = compositeGroupedSummary(outcomes, ["factionId", "backendId"]);
  const strategyBackends = compositeGroupedSummary(outcomes, ["profileId", "backendId"]);
  const matchups = profileMatchups(outcomes);
  const allActionCounts = {};
  for (const seat of seats) mergeCounts(allActionCounts, seat.actionCounts);
  const openingCounts = {};
  const winningPathCounts = {};
  for (const outcome of outcomes) {
    for (const entry of outcome.standings) {
      increment(openingCounts, (entry.metrics.openingActions || []).join("→") || "none");
      if (outcome.winnerSeats.includes(entry.seat)) {
        increment(
          winningPathCounts,
          classifyWinningPath(entry),
          1 / outcome.winnerSeats.length
        );
      }
    }
  }
  const matchupMax = Math.max(
    0,
    ...matchups.filter((entry) => entry.comparisons >= 4)
      .map((entry) => entry.relativePlacementRate)
  );
  const diagnostics = {
    seatWinShareRange: range(seats.map((seat) => seat.winShare)),
    factionWinShareRange: range(factions.map((faction) => faction.winShare)),
    profileWinShareRange: range(profiles.map((profile) => profile.winShare)),
    scoreStdDev: deviation(outcomes.flatMap((outcome) =>
      outcome.standings.map((entry) => entry.score)
    )),
    actionDiversity: normalizedEntropy(allActionCounts),
    openingDiversity: concentration(openingCounts),
    winningPathDiversity: concentration(winningPathCounts),
    winningPathClassifier: WINNING_PATH_CLASSIFIER,
    factionStrategyInteractionRange: range(
      factionStrategies.filter((entry) => entry.appearances >= 4).map((entry) => entry.winShare)
    ),
    leaderPredictability: leaderPredictability(outcomes),
    pairwiseDominance: matchupMax,
    cyclicMeta: metaCycles(matchups),
    integrity: integritySummary(outcomes),
    agiEligibilityRate: mean(seats.map((seat) => seat.agiEligibilityRate)),
    agiDeclarationRate: mean(seats.map((seat) => seat.agiDeclarationRate)),
    agiEmergenceRate: outcomes.filter((outcome) => outcome.worldEnding?.agiEmerges).length /
      outcomes.length,
    openContinuityRate: outcomes.filter((outcome) => outcome.worldEnding?.openContinuity).length /
      outcomes.length,
    nonDeclaringWinRate: outcomes.filter((outcome) =>
      outcome.winnerSeats.some((seat) =>
        !outcome.standings.find((entry) => entry.seat === seat)?.agiDeclared
      )
    ).length / outcomes.length
  };
  diagnostics.alerts = [
    ...(diagnostics.seatWinShareRange > 0.15
      ? [{ id: "seat_bias", severity: "high", value: diagnostics.seatWinShareRange }]
      : []),
    ...(diagnostics.factionWinShareRange > 0.15
      ? [{ id: "faction_spread", severity: "high", value: diagnostics.factionWinShareRange }]
      : []),
    ...(diagnostics.actionDiversity < 0.72
      ? [{ id: "action_collapse", severity: "high", value: diagnostics.actionDiversity }]
      : []),
    ...(diagnostics.agiEmergenceRate < 0.03
      ? [{ id: "agi_drought", severity: "medium", value: diagnostics.agiEmergenceRate }]
      : []),
    ...(diagnostics.agiEmergenceRate > 0.08
      ? [{ id: "agi_flood", severity: "medium", value: diagnostics.agiEmergenceRate }]
      : []),
    ...(diagnostics.openContinuityRate === 0
      ? [{ id: "closed_continuity_only", severity: "medium", value: diagnostics.openContinuityRate }]
      : [])
  ];

  const report = {
    schemaVersion: 2,
    reportType: "tournament",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(seed),
    runs,
    playerCount: seatCount,
    scope,
    rulesVariant: outcomes[0].rulesVariant,
    seats,
    factions,
    profiles,
    backends,
    factionStrategies,
    factionBackends,
    strategyBackends,
    profileMatchups: matchups,
    diagnostics,
    matchMetrics: aggregateMatchMetrics(outcomes),
    samples,
    ...(observations ? { observations } : {})
  };
  return returnOutcomes ? { report, rawOutcomes } : report;
}
