import { createRng } from "../../web/src/engine.js";
import { simulationCopy } from "../content/simulation-copy.js";
import { loadPlayerProfiles, validatePlayerProfile } from "../personas/player-profile.js";
import { createSimulation } from "../runtime/create-simulation.js";
import { createReportIdentity } from "../versioning/game-identity.js";

const RULE_BOUNDS = {
  auditMultiplier: [0.6, 1.5, 0.1],
  fundConservative: [1, 4, 1],
  fundVenture: [3, 7, 1],
  ventureScrutiny: [1, 4, 1],
  facilityCost: [1, 4, 1],
  deployComputeCost: [0, 3, 1],
  startingGridPower: [1, 3, 1],
  customerMandate: [1, 4, 1],
  customerCapabilityOffset: [-2, 2, 1],
  startingTeamsDeployed: [0, 3, 1]
};

const DEFAULT_RULE_VARIANT = {
  auditMultiplier: 1,
  fundConservative: 2,
  fundVenture: 4,
  ventureScrutiny: 2,
  facilityCost: 2,
  deployComputeCost: 1,
  startingGridPower: 1,
  customerMandate: 2,
  customerCapabilityOffset: 0,
  startingTeamsDeployed: 1
};

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function round(value, places = 3) {
  const scale = 10 ** places;
  return Math.round(value * scale) / scale;
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function weightedAverage(entries, value) {
  const totalWeight = entries.reduce((sum, entry) => sum + entry.weight, 0);
  return entries.reduce((sum, entry) => sum + value(entry) * entry.weight, 0) /
    Math.max(1, totalWeight);
}

function normalizePlayerCounts(playerCount, playerCounts) {
  const values = playerCounts === undefined ? [playerCount] : playerCounts;
  if (!Array.isArray(values) || values.length === 0) {
    throw new TypeError("Strategy evolution playerCounts must be a non-empty array.");
  }
  if (values.some((value) => !Number.isInteger(value) || value < 3 || value > 5)) {
    throw new RangeError("Strategy evolution playerCounts must contain only 3, 4, or 5.");
  }
  if (new Set(values).size !== values.length) {
    throw new TypeError("Strategy evolution playerCounts must not contain duplicates.");
  }
  return [...values];
}

function resolvedTargetWinShare(targetWinShare, playerCount) {
  if (targetWinShare === "neutral") return 1 / playerCount;
  return Number.isFinite(targetWinShare) ? targetWinShare : null;
}

export function opponentProfileWindows({
  profiles,
  targetProfileId,
  playerCount,
  opponentCoverage = "all_windows"
}) {
  if (!Array.isArray(profiles)) {
    throw new TypeError("Strategy evolution profiles must be an array.");
  }
  if (!Number.isInteger(playerCount) || playerCount < 3 || playerCount > 5) {
    throw new RangeError("Strategy evolution playerCount must be 3, 4, or 5.");
  }
  if (!["all_windows", "fixed_window"].includes(opponentCoverage)) {
    throw new TypeError(
      "Strategy evolution opponentCoverage must be all_windows or fixed_window."
    );
  }
  const opponents = profiles.filter((candidate) => candidate.id !== targetProfileId);
  const width = playerCount - 1;
  if (opponents.length < width) {
    throw new RangeError(
      `Strategy evolution requires at least ${width} opponents for ${playerCount} players.`
    );
  }
  const starts = opponentCoverage === "all_windows" ? opponents.length : 1;
  return Array.from({ length: starts }, (_, start) =>
    Array.from({ length: width }, (_, offset) =>
      opponents[(start + offset) % opponents.length].id
    )
  );
}

export function mergeStrategyProfiles(baseProfiles, profileOverrides = []) {
  if (!Array.isArray(baseProfiles) || !Array.isArray(profileOverrides)) {
    throw new TypeError("Strategy evolution profiles and overrides must be arrays.");
  }
  const baseIds = new Set(baseProfiles.map((profile) => profile.id));
  const overrides = new Map();
  for (const profile of profileOverrides) {
    validatePlayerProfile(profile);
    if (!baseIds.has(profile.id)) {
      throw new TypeError(
        `Strategy evolution override has unknown profile id: ${profile.id}.`
      );
    }
    if (overrides.has(profile.id)) {
      throw new TypeError(
        `Strategy evolution override repeats profile id: ${profile.id}.`
      );
    }
    overrides.set(profile.id, structuredClone(profile));
  }
  return baseProfiles.map((profile) =>
    overrides.get(profile.id) || structuredClone(profile)
  );
}

function runsByWindow(runsPerSeat, windowCount) {
  if (runsPerSeat < windowCount) {
    throw new RangeError(
      `Strategy evolution runsPerSeat must be at least ${windowCount} ` +
      "to cover every opponent window."
    );
  }
  const base = Math.floor(runsPerSeat / windowCount);
  const remainder = runsPerSeat % windowCount;
  return Array.from(
    { length: windowCount },
    (_, index) => base + (index < remainder ? 1 : 0)
  );
}

export function compareStrategyEvaluations(left, right, targetWinShare) {
  if (targetWinShare === "neutral" || Number.isFinite(targetWinShare)) {
    const targetOrder = left.evaluation.targetDistance - right.evaluation.targetDistance;
    if (targetOrder !== 0) return targetOrder;
    const meanTargetOrder =
      left.evaluation.meanTargetDistance - right.evaluation.meanTargetDistance;
    if (meanTargetOrder !== 0) return meanTargetOrder;
  }
  return right.evaluation.fitness - left.evaluation.fitness ||
    JSON.stringify(left.profile.strategy).localeCompare(
      JSON.stringify(right.profile.strategy)
    );
}

function mutateWeightMap(weights, rng, magnitude) {
  return Object.fromEntries(Object.entries(weights).map(([key, value]) => {
    const factor = Math.exp((rng() * 2 - 1) * magnitude);
    // Existing authored profiles may intentionally use a weight above the
    // ordinary search ceiling. A mutation may reduce that weight, but the
    // optimizer must not silently replace it with 20 before comparison.
    const upperBound = Math.max(20, value);
    return [key, round(clamp(value * factor, 0.05, upperBound))];
  }));
}

export function mutateStrategy(profile, seed, { magnitude = 0.45 } = {}) {
  validatePlayerProfile(profile);
  const result = structuredClone(profile);
  const rng = createRng(`${seed}:${profile.id}`);
  result.strategy.actionWeights = mutateWeightMap(
    result.strategy.actionWeights,
    rng,
    magnitude
  );
  result.strategy.decisionWeights = mutateWeightMap(
    result.strategy.decisionWeights || {},
    rng,
    magnitude
  );
  result.strategy.negotiation = mutateWeightMap(
    result.strategy.negotiation,
    rng,
    magnitude
  );
  result.provenance = {
    kind: "simulated_strategy_mutation",
    parentId: profile.id,
    seed: String(seed),
    magnitude
  };
  return validatePlayerProfile(result);
}

export function mutateRulesVariant(variant, seed, { mutations = 2 } = {}) {
  const result = { ...DEFAULT_RULE_VARIANT, ...variant };
  const rng = createRng(seed);
  const keys = Object.keys(RULE_BOUNDS);
  const changed = [];
  for (let index = 0; index < mutations; index += 1) {
    const key = keys[Math.floor(rng() * keys.length)];
    const [minimum, maximum, step] = RULE_BOUNDS[key];
    const direction = rng() < 0.5 ? -1 : 1;
    result[key] = round(clamp(result[key] + direction * step, minimum, maximum));
    if (!changed.includes(key)) changed.push(key);
  }
  result.fundVenture = Math.max(result.fundConservative + 1, result.fundVenture);
  return { variant: result, changed };
}

function candidateProfile(report, profileId) {
  return report.profiles.find((profile) => profile.profileId === profileId);
}

async function evaluateStrategyCandidate({
  profile,
  profiles,
  playerCounts,
  runsPerSeat,
  seed,
  rulesVariant,
  backendId,
  targetWinShare,
  opponentCoverage,
  signal
}) {
  const playerCountEvaluations = {};
  for (const playerCount of playerCounts) {
    const opponentWindows = opponentProfileWindows({
      profiles,
      targetProfileId: profile.id,
      playerCount,
      opponentCoverage
    });
    const allocatedRuns = runsByWindow(runsPerSeat, opponentWindows.length);
    const seatEvaluations = [];
    for (let seat = 0; seat < playerCount; seat += 1) {
      const windowEvaluations = [];
      for (const [windowIndex, opponents] of opponentWindows.entries()) {
        const profileIds = Array.from({ length: playerCount }, (_, index) => {
          if (index === seat) return profile.id;
          return opponents[index < seat ? index : index - 1];
        });
        const report = await createSimulation({
          runs: allocatedRuns[windowIndex],
          playerCount,
          seed: `${seed}:players:${playerCount}:seat:${seat}:window:${windowIndex}`,
          sampleReplays: 0,
          profileIds,
          profileOverrides: profiles.map((candidate) =>
            candidate.id === profile.id ? profile : candidate
          ),
          backends: [backendId],
          rotateProfiles: false,
          projection: "batch",
          rulesVariant,
          signal
        });
        windowEvaluations.push({
          weight: allocatedRuns[windowIndex],
          opponents,
          target: candidateProfile(report, profile.id)
        });
      }
      seatEvaluations.push({
        winShare: weightedAverage(windowEvaluations, (entry) => entry.target.winShare),
        meanScore: weightedAverage(windowEvaluations, (entry) => entry.target.meanScore),
        actionDiversity: weightedAverage(
          windowEvaluations,
          (entry) => entry.target.actionDiversity
        )
      });
    }
    const meanWinShare = average(seatEvaluations.map((entry) => entry.winShare));
    const target = resolvedTargetWinShare(targetWinShare, playerCount);
    playerCountEvaluations[playerCount] = {
      playerCount,
      targetWinShare: target,
      targetDistance: Number.isFinite(target)
        ? Math.abs(meanWinShare - target)
        : null,
      meanWinShare,
      meanScore: average(seatEvaluations.map((entry) => entry.meanScore)),
      actionDiversity: average(
        seatEvaluations.map((entry) => entry.actionDiversity)
      ),
      seatWinShares: seatEvaluations.map((entry) => entry.winShare),
      opponentWindows,
      runsByWindow: allocatedRuns,
      totalMatches: runsPerSeat * playerCount
    };
  }
  const evaluations = Object.values(playerCountEvaluations);
  const meanWinShare = average(evaluations.map((entry) => entry.meanWinShare));
  const meanScore = average(evaluations.map((entry) => entry.meanScore));
  const actionDiversity = average(evaluations.map((entry) => entry.actionDiversity));
  const targetDistances = evaluations
    .map((entry) => entry.targetDistance)
    .filter(Number.isFinite);
  const targetDistance = targetDistances.length
    ? Math.max(...targetDistances)
    : null;
  const meanTargetDistance = targetDistances.length
    ? average(targetDistances)
    : null;
  return {
    fitness: round(meanWinShare * 100 + meanScore * 0.1 + actionDiversity),
    meanWinShare,
    meanScore,
    actionDiversity,
    targetDistance,
    meanTargetDistance,
    playerCountEvaluations
  };
}

export async function evolveStrategy({
  targetProfileId = "balanced_operator",
  generations = 4,
  population = 6,
  runsPerSeat = 12,
  playerCount = 4,
  playerCounts,
  seed = "frontier-strategy-evolution",
  magnitude = 0.45,
  backendId = "weighted",
  targetWinShare,
  opponentCoverage = "all_windows",
  profileOverrides = [],
  profileOverrideSources = [],
  rulesVariant,
  signal,
  onProgress
} = {}) {
  if (!["weighted", "greedy"].includes(backendId)) {
    throw new TypeError("Strategy evolution backendId must be weighted or greedy.");
  }
  if (
    targetWinShare !== undefined && targetWinShare !== "neutral" &&
    (!Number.isFinite(targetWinShare) || targetWinShare < 0 || targetWinShare > 1)
  ) {
    throw new RangeError(
      "Strategy evolution targetWinShare must be neutral or a number from zero to one."
    );
  }
  const selectedPlayerCounts = normalizePlayerCounts(playerCount, playerCounts);
  const profiles = mergeStrategyProfiles(await loadPlayerProfiles(), profileOverrides);
  const source = profiles.find((profile) => profile.id === targetProfileId);
  if (!source) throw new TypeError(`Unknown player profile: ${targetProfileId}.`);
  for (const selectedPlayerCount of selectedPlayerCounts) {
    const windowCount = opponentProfileWindows({
      profiles,
      targetProfileId,
      playerCount: selectedPlayerCount,
      opponentCoverage
    }).length;
    runsByWindow(runsPerSeat, windowCount);
  }
  let incumbent = structuredClone(source);
  const history = [];
  const total = generations * population;
  let completed = 0;

  for (let generation = 0; generation < generations; generation += 1) {
    const evaluationSeed = `${seed}:g:${generation}:common`;
    const candidates = [incumbent, ...Array.from({ length: population - 1 }, (_, index) =>
      mutateStrategy(incumbent, `${seed}:g:${generation}:candidate:${index}`, { magnitude })
    )];
    const evaluated = [];
    for (const [index, profile] of candidates.entries()) {
      const evaluation = await evaluateStrategyCandidate({
        profile,
        profiles,
        playerCounts: selectedPlayerCounts,
        runsPerSeat,
        seed: evaluationSeed,
        rulesVariant,
        backendId,
        targetWinShare,
        opponentCoverage,
        signal
      });
      evaluated.push({ profile, evaluation });
      completed += 1;
      onProgress?.({ phase: "strategy_evolution", completed, total });
    }
    evaluated.sort((left, right) =>
      compareStrategyEvaluations(left, right, targetWinShare)
    );
    incumbent = structuredClone(evaluated[0].profile);
    history.push({
      generation: generation + 1,
      evaluationSeed,
      candidates: evaluated.map(({ profile, evaluation }, rank) => ({
        rank: rank + 1,
        profile: {
          id: profile.id,
          actionWeights: profile.strategy.actionWeights,
          decisionWeights: profile.strategy.decisionWeights || {}
        },
        evaluation
      })),
      champion: {
        fitness: evaluated[0].evaluation.fitness,
        meanWinShare: evaluated[0].evaluation.meanWinShare,
        targetDistance: evaluated[0].evaluation.targetDistance,
        meanTargetDistance: evaluated[0].evaluation.meanTargetDistance
      }
    });
  }

  const report = {
    schemaVersion: 2,
    reportType: "strategy_evolution",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(seed),
    playerCount,
    playerCounts: selectedPlayerCounts,
    targetProfileId,
    generations,
    population,
    runsPerSeat,
    backendId,
    targetWinShare: targetWinShare ?? null,
    targetWinShares: Object.fromEntries(selectedPlayerCounts.map((count) => [
      count,
      resolvedTargetWinShare(targetWinShare, count)
    ])),
    opponentCoverage,
    profileOverrideSources: structuredClone(profileOverrideSources),
    ecologyProfiles: structuredClone(profiles),
    evaluatedMatchesPerCandidate: selectedPlayerCounts.reduce(
      (sum, count) => sum + count * runsPerSeat,
      0
    ),
    scope: structuredClone(simulationCopy.coverage.strategyEvolution),
    baselineProfile: source,
    championProfile: incumbent,
    history
  };
  return createReportIdentity({
    report,
    rulesVariant: rulesVariant || {},
    variantOverlay: rulesVariant,
    profiles,
    backends: [backendId],
    model: null,
    experimentKind: "strategy_evolution"
  });
}

function ruleFitness(report, targetAgiRate) {
  const diagnostics = report.diagnostics;
  const agiPenalty = Math.abs(diagnostics.agiEmergenceRate - targetAgiRate);
  const contractPenalty = (report.balanceEvaluation?.checks || []).reduce((sum, entry) => {
    if (entry.passed || !Number.isFinite(entry.value) || !Number.isFinite(entry.threshold)) {
      return sum;
    }
    const scale = Math.max(0.01, Math.abs(entry.threshold));
    const miss = entry.operator === "max"
      ? entry.value - entry.threshold
      : entry.threshold - entry.value;
    return sum + Math.max(0, miss) / scale;
  }, 0);
  return round(
    contractPenalty +
    agiPenalty +
    diagnostics.scoreStdDev * 0.01
  );
}

export async function searchRuleVariants({
  iterations = 12,
  runs = 80,
  playerCount = 4,
  seed = "frontier-rule-search",
  profileIds,
  baseline = DEFAULT_RULE_VARIANT,
  targetAgiRate = 0.05,
  signal,
  onProgress
} = {}) {
  const availableProfiles = await loadPlayerProfiles();
  const selectedProfiles = profileIds?.length
    ? profileIds.map((id) => {
      const profile = availableProfiles.find((candidate) => candidate.id === id);
      if (!profile) throw new TypeError(`Unknown player profile: ${id}.`);
      return profile;
    })
    : availableProfiles.slice(0, playerCount);
  let incumbent = { ...DEFAULT_RULE_VARIANT, ...baseline };
  const evaluations = [];
  for (let iteration = 0; iteration < iterations; iteration += 1) {
    const proposal = iteration === 0
      ? { variant: incumbent, changed: [] }
      : mutateRulesVariant(
        incumbent,
        `${seed}:variant:${iteration}`,
        { mutations: iteration % 3 === 0 ? 2 : 1 }
      );
    const report = await createSimulation({
      runs,
      playerCount,
      seed: `${seed}:common`,
      sampleReplays: 0,
      profileIds,
      backends: ["weighted"],
      rulesVariant: proposal.variant,
      signal
    });
    const fitness = ruleFitness(report, targetAgiRate);
    const entry = {
      iteration,
      variant: proposal.variant,
      changed: proposal.changed,
      fitness,
      diagnostics: report.diagnostics
    };
    evaluations.push(entry);
    const best = [...evaluations].sort((left, right) =>
      left.fitness - right.fitness ||
      JSON.stringify(left.variant).localeCompare(JSON.stringify(right.variant))
    )[0];
    incumbent = { ...best.variant };
    onProgress?.({ phase: "rule_search", completed: iteration + 1, total: iterations });
  }
  evaluations.sort((left, right) => left.fitness - right.fitness);
  const report = {
    schemaVersion: 2,
    reportType: "rule_search",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(seed),
    playerCount,
    iterations,
    runsPerVariant: runs,
    targetAgiRate,
    scope: structuredClone(simulationCopy.coverage.ruleSearch),
    baseline: evaluations.find((entry) => entry.iteration === 0),
    recommendation: evaluations[0],
    evaluations
  };
  const testedVariants = evaluations.map((entry) => entry.variant);
  return createReportIdentity({
    report,
    rulesVariant: {
      baseline: report.baseline.variant,
      testedVariants
    },
    variantOverlay: {
      search: true,
      baseline
    },
    profiles: selectedProfiles,
    backends: ["weighted"],
    model: null,
    experimentKind: "rule_search"
  });
}

export { DEFAULT_RULE_VARIANT, RULE_BOUNDS };
