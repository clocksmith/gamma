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
  agiCapability: [6, 12, 1],
  agiComputeCost: [1, 5, 1],
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
  agiCapability: 6,
  agiComputeCost: 3,
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

function mutateWeightMap(weights, rng, magnitude) {
  return Object.fromEntries(Object.entries(weights).map(([key, value]) => {
    const factor = Math.exp((rng() * 2 - 1) * magnitude);
    return [key, round(clamp(value * factor, 0.05, 20))];
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
  playerCount,
  runsPerSeat,
  seed,
  rulesVariant,
  signal
}) {
  const opponents = profiles.filter((candidate) => candidate.id !== profile.id);
  const seatReports = [];
  for (let seat = 0; seat < playerCount; seat += 1) {
    const profileIds = Array.from({ length: playerCount }, (_, index) => {
      if (index === seat) return profile.id;
      return opponents[(index < seat ? index : index - 1) % opponents.length].id;
    });
    seatReports.push(await createSimulation({
      runs: runsPerSeat,
      playerCount,
      seed: `${seed}:seat:${seat}`,
      sampleReplays: 0,
      profileIds,
      profileOverrides: [profile],
      backends: ["weighted"],
      rotateProfiles: false,
      rulesVariant,
      signal
    }));
  }
  const target = seatReports.map((report) => candidateProfile(report, profile.id));
  const meanWinShare = average(target.map((entry) => entry.winShare));
  const meanScore = average(target.map((entry) => entry.meanScore));
  const actionDiversity = average(target.map((entry) => entry.actionDiversity));
  return {
    fitness: round(meanWinShare * 100 + meanScore * 0.1 + actionDiversity),
    meanWinShare,
    meanScore,
    actionDiversity,
    seatWinShares: target.map((entry) => entry.winShare)
  };
}

export async function evolveStrategy({
  targetProfileId = "balanced_operator",
  generations = 4,
  population = 6,
  runsPerSeat = 12,
  playerCount = 4,
  seed = "frontier-strategy-evolution",
  magnitude = 0.45,
  rulesVariant,
  signal,
  onProgress
} = {}) {
  const profiles = await loadPlayerProfiles();
  const source = profiles.find((profile) => profile.id === targetProfileId);
  if (!source) throw new TypeError(`Unknown player profile: ${targetProfileId}.`);
  let incumbent = structuredClone(source);
  const history = [];
  const total = generations * population;
  let completed = 0;

  for (let generation = 0; generation < generations; generation += 1) {
    const candidates = [incumbent, ...Array.from({ length: population - 1 }, (_, index) =>
      mutateStrategy(incumbent, `${seed}:g:${generation}:candidate:${index}`, { magnitude })
    )];
    const evaluated = [];
    for (const [index, profile] of candidates.entries()) {
      const evaluation = await evaluateStrategyCandidate({
        profile,
        profiles,
        playerCount,
        runsPerSeat,
        seed: `${seed}:g:${generation}:candidate:${index}`,
        rulesVariant,
        signal
      });
      evaluated.push({ profile, evaluation });
      completed += 1;
      onProgress?.({ phase: "strategy_evolution", completed, total });
    }
    evaluated.sort((left, right) =>
      right.evaluation.fitness - left.evaluation.fitness ||
      JSON.stringify(left.profile.strategy).localeCompare(JSON.stringify(right.profile.strategy))
    );
    incumbent = structuredClone(evaluated[0].profile);
    history.push({
      generation: generation + 1,
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
        meanWinShare: evaluated[0].evaluation.meanWinShare
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
    targetProfileId,
    generations,
    population,
    runsPerSeat,
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
    backends: ["weighted"],
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
