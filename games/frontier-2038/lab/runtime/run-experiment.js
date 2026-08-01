import {
  evolveStrategy,
  searchRuleVariants
} from "../runner/optimization-runner.js";
import { createSimulation } from "./create-simulation.js";
import { runUnifiedMatrix } from "../runner/unified-matrix-runner.js";
import { runLlmNegotiationHoldout } from "../runner/llm-holdout-runner.js";

function integer(value, fallback, minimum, maximum, label) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}.`);
  }
  return parsed;
}

export async function runExperiment(options = {}, onProgress) {
  const mode = options.mode || "tournament";
  if (mode === "tournament") return createSimulation(options, onProgress);
  if (mode === "strategy-evolution") {
    return evolveStrategy({
      targetProfileId: options.targetProfileId,
      generations: integer(options.generations, 4, 1, 50, "generations"),
      population: integer(options.population, 6, 2, 50, "population"),
      runsPerSeat: integer(options.runsPerSeat ?? options.runs, 12, 1, 1000, "runsPerSeat"),
      playerCount: integer(options.playerCount, 4, 3, 5, "playerCount"),
      seed: options.seed,
      magnitude: options.magnitude === undefined ? undefined : Number(options.magnitude),
      rulesVariant: options.rulesVariant,
      signal: options.signal,
      onProgress
    });
  }
  if (mode === "rule-search") {
    return searchRuleVariants({
      iterations: integer(options.iterations, 12, 2, 100, "iterations"),
      runs: integer(options.runs, 80, 1, 10000, "runs"),
      playerCount: integer(options.playerCount, 4, 3, 5, "playerCount"),
      seed: options.seed,
      profileIds: options.profileIds,
      baseline: options.rulesVariant,
      targetAgiRate: options.targetAgiRate === undefined
        ? undefined
        : Number(options.targetAgiRate),
      signal: options.signal,
      onProgress
    });
  }
  if (mode === "balance-audit") {
    return runUnifiedMatrix({
      maximumMatches: integer(
        options.maximumMatches ?? options.runs,
        480,
        30,
        100000,
        "maximumMatches"
      ),
      initialRunsPerCell: integer(options.initialRunsPerCell, 2, 1, 100, "initialRunsPerCell"),
      batchSize: integer(options.batchSize, 2, 1, 100, "batchSize"),
      playerCounts: options.playerCounts,
      mandateModes: options.mandateModes,
      seed: options.seed,
      preRegistrationId: options.preRegistrationId,
      rulesVariant: options.rulesVariant,
      signal: options.signal,
      onProgress
    });
  }
  if (mode === "llm-holdout") {
    return runLlmNegotiationHoldout({
      preRegistrationPath: options.preRegistrationPath,
      allowLlm: Boolean(options.allowLlm),
      signal: options.signal,
      onProgress
    });
  }
  throw new TypeError(`Unknown simulation mode: ${mode}.`);
}
