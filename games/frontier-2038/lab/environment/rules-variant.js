export function canonicalRulesVariant(config) {
  const lateCapabilityThreshold =
    config.scoring.capabilityThresholds.find((entry) => entry.value >= 9);
  return {
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
    agiFirstMandate: config.agiDeclaration.firstMandate,
    agiLaterMandate: config.agiDeclaration.laterMandate,
    agiCapability: config.agiDeclaration.capability,
    agiCustomers: config.agiDeclaration.customers,
    agiFacilities: config.agiDeclaration.facilities,
    agiTrust: config.agiDeclaration.trust,
    agiComputeCost: config.agiDeclaration.computeCost,
    customerCapabilityOffset: 0,
    startingTeamsDeployed: 1,
    coalitionStartingRunway: null,
    coalitionWildcardGovernanceScrutiny: 2,
    imperialStartingCompute: null,
    imperialScientificMethodCapabilityPenalty: 0,
    imperialScientificMethodThresholdMandatePenalty: 0,
    imperialScientificMethodScrutiny: 0,
    imperialScientificMethodRunwayCost: 1,
    imperialScientificMethodLifetimeLimit: null,
    imperialNobelTrust: 2,
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
    foundryNewArchitectureCompute: config.factionRules.foundry.newArchitectureCompute,
    foundryNewArchitectureDemandCoupling: structuredClone(
      config.factionRules.foundry.newArchitectureDemandCoupling
    ),
    foundryGpuMandateEnabled: true,
    foundryGpuRivalsPerMandate: config.factionRules.foundry.everybodyGpuRivalsPerMandate,
    safetyEmergencyPauseEnabled: true,
    safetyStartingTrust: null,
    // Simulation-only intervention surface. Each entry names the canonical
    // faction and ability suppressed for the entire match.
    pausedFactionAbilities: []
  };
}

export const legacyPrePromotionRulesOverlay = Object.freeze({
  customerMandateSchedule: null,
  imperialLateCapabilityThresholdMandate: null,
  verticalIndustrialVelocityMandate: 0,
  foundryNewArchitectureDemandCoupling: null
});

export function effectiveRulesVariant(config, overlay = {}) {
  const effective = {
    ...canonicalRulesVariant(config),
    ...overlay
  };
  if (
    Object.hasOwn(overlay, "customerMandate") &&
    !Object.hasOwn(overlay, "customerMandateSchedule")
  ) {
    effective.customerMandateSchedule = null;
  }
  return effective;
}
