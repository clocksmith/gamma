const SINGLE_GENERATOR_POLICIES = Object.freeze({
  delivery: "own-or-adjacent-facilities",
  slotContention: "initiative-order-no-reservations"
});

function validateSingleGeneratorRule(config, rule) {
  if (rule === undefined || rule === null) return null;
  if (!rule || typeof rule !== "object" || Array.isArray(rule)) {
    throw new TypeError("singleGeneratorRule must be an object.");
  }
  if (rule.id !== "single-generator-default") {
    throw new RangeError("singleGeneratorRule.id must be single-generator-default.");
  }
  if (rule.ordinaryGeneratorLimit !== 1) {
    throw new RangeError("single-generator-default requires exactly one ordinary Generator.");
  }
  const expectedLocations = ["grid_reactor", "renewable_basin"];
  if (
    !rule.locations ||
    typeof rule.locations !== "object" ||
    Array.isArray(rule.locations) ||
    Object.keys(rule.locations).sort().join(",") !== expectedLocations.join(",")
  ) {
    throw new RangeError(
      "single-generator-default requires exact grid_reactor and renewable_basin location rules."
    );
  }
  const sourceIds = new Set(config.powerSources.map((source) => source.id));
  for (const [locationId, location] of Object.entries(rule.locations)) {
    if (!sourceIds.has(location.sourceId)) {
      throw new RangeError(
        `single-generator-default location ${locationId} has unknown source ${location.sourceId}.`
      );
    }
    if (!Number.isInteger(location.constructionCost) || location.constructionCost < 0) {
      throw new RangeError(
        `single-generator-default location ${locationId} requires a non-negative constructionCost.`
      );
    }
  }
  for (const [field, expected] of [
    ["localDelivery", SINGLE_GENERATOR_POLICIES.delivery],
    ["slotContention", SINGLE_GENERATOR_POLICIES.slotContention]
  ]) {
    if (rule[field] !== expected) {
      throw new RangeError(`single-generator-default ${field} must be ${expected}.`);
    }
  }
  return structuredClone(rule);
}

export function canonicalRulesVariant(config) {
  const lateCapabilityThreshold =
    config.scoring.capabilityThresholds.find((entry) => entry.value >= 9);
  return {
    ...config.playRules,
    singleGeneratorRule: structuredClone(config.singleGeneratorRule),
    auditMultiplier: 1,
    fundConservative: 2,
    fundVenture: 4,
    ventureScrutiny: 2,
    facilityCost: 2,
    deployComputeCost: 1,
    customerMandate: config.scoring.customerMandate,
    customerMandateSchedule: structuredClone(
      config.scoring.customerMandateSchedule
    ),
    capabilityThresholdMandate: null,
    lateCapabilityThresholdMandate: lateCapabilityThreshold?.mandate ?? 2,
    agiAchievement: structuredClone(config.agiAchievement),
    finalPoweredFacilityMandate: 0,
    customerCapabilityOffset: 0,
    startingAgentsDeployed: config.playerSupply.startingAgents,
    coalitionStartingRunway: null,
    imperialStartingCompute: null,
    imperialScientificMethodCapabilityPenalty: 0,
    imperialScientificMethodThresholdMandatePenalty: 0,
    imperialScientificMethodScrutiny: 0,
    imperialScientificMethodRunwayCost: 1,
    imperialScientificMethodLifetimeLimit: null,
    imperialLateCapabilityThresholdMandate: structuredClone(
      config.factionRules.imperial.peerValidation
    ),
    verticalStartingCompute: null,
    verticalIndustrialVelocityDiscount: 1,
    verticalIndustrialVelocityMandate:
      config.factionRules.vertical.industrialVelocityMandate,
    verticalIndustrialVelocityBuildModes: ["facility"],
    foundryStartingCompute: config.factionRules.foundry.startingCompute,
    foundryShovelsPerRound: config.factionRules.foundry.shovelsPerRound,
    safetyEmergencyPauseEnabled: true,
    safetyStartingTrust: null,
    tacticsEnabled: false,
    // Simulation-only intervention surface. Each entry names the canonical
    // faction and ability suppressed for the entire match.
    pausedFactionAbilities: []
  };
}

export const legacyPrePromotionRulesOverlay = Object.freeze({
  customerMandateSchedule: null,
  imperialLateCapabilityThresholdMandate: null,
  verticalIndustrialVelocityMandate: 0
});

export function effectiveRulesVariant(config, overlay = {}) {
  const canonical = canonicalRulesVariant(config);
  for (const key of Object.keys(overlay)) {
    if (!Object.hasOwn(canonical, key)) {
      throw new RangeError(`Unsupported rules option: ${key}.`);
    }
  }
  const effective = {
    ...canonical,
    ...overlay
  };
  if (
    Object.hasOwn(overlay, "customerMandate") &&
    !Object.hasOwn(overlay, "customerMandateSchedule")
  ) {
    effective.customerMandateSchedule = null;
  }
  if (Object.hasOwn(effective, "singleGeneratorRule")) {
    effective.singleGeneratorRule = validateSingleGeneratorRule(
      config,
      effective.singleGeneratorRule
    );
  }
  return effective;
}
