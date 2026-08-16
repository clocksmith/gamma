import { resolvePlayProfile } from "../../web/src/engine.js";

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
  if (rule.powerSalesPerSupplier !== 1) {
    throw new RangeError("single-generator-default permits one Power sale per supplier.");
  }
  if (rule.megaClusterDemand !== 2) {
    throw new RangeError("single-generator-default keeps Mega-Cluster demand at two Power.");
  }
  return structuredClone(rule);
}

export function canonicalRulesVariant(config) {
  const lateCapabilityThreshold =
    config.scoring.capabilityThresholds.find((entry) => entry.value >= 9);
  const profile = resolvePlayProfile(config);
  return {
    playProfileId: profile.id,
    immediateTradeCounteroffers: profile.immediateTradeCounteroffers,
    immediateTradeThirdPartyClaims: profile.immediateTradeThirdPartyClaims,
    powerPurchaseRequests: profile.powerPurchaseRequests,
    realignmentEnabled: profile.realignmentEnabled,
    singleGeneratorRule: structuredClone(config.singleGeneratorRule),
    auditMultiplier: 1,
    fundConservative: 2,
    fundVenture: 4,
    ventureScrutiny: 2,
    facilityCost: 2,
    deployComputeCost: 1,
    startingGridPower: config.board.startingGridConnection.capacity,
    customerMandate: config.scoring.customerMandate,
    customerMandateSchedule: structuredClone(
      config.scoring.customerMandateSchedule
    ),
    capabilityThresholdMandate: null,
    lateCapabilityThresholdMandate: lateCapabilityThreshold?.mandate ?? 2,
    agiComputePerCommit: config.agiDossier.computePerCommit,
    agiScrutinyPerCommit: config.agiDossier.scrutinyPerCommit,
    agiMinimumSupportedEvidenceClaims:
      config.agiDossier.claimResolution?.minimumSupportedEvidenceClaims ?? 2,
    customerCapabilityOffset: 0,
    startingTeamsDeployed: 1,
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
  const requestedProfileId = overlay.playProfileId ??
    config.playProfiles?.defaultGame?.id ?? "default-game";
  const profile = resolvePlayProfile(config, requestedProfileId);
  if (!profile) throw new RangeError(`Unknown play profile: ${requestedProfileId}.`);
  const effective = {
    ...canonicalRulesVariant(config),
    ...profile,
    ...overlay
  };
  effective.playProfileId = requestedProfileId;
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
