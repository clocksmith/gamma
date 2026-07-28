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
    imperialStartingCompute: null,
    imperialScientificMethodCapabilityPenalty: 0,
    imperialScientificMethodThresholdMandatePenalty: 0,
    imperialScientificMethodScrutiny: 0,
    imperialScientificMethodRunwayCost: 1,
    imperialScientificMethodLifetimeLimit: null,
    verticalStartingCompute: null,
    verticalIndustrialVelocityDiscount: 1,
    verticalIndustrialVelocityMandate: 0,
    verticalIndustrialVelocityBuildModes: ["facility"],
    foundryStartingCompute: config.factionRules.foundry.startingCompute,
    foundryShovelsPerRound: config.factionRules.foundry.shovelsPerRound,
    foundryNewArchitectureCompute: config.factionRules.foundry.newArchitectureCompute,
    foundryNewArchitectureDemandBaseCompute: null,
    foundryNewArchitectureComputePerLicense: 0,
    foundryNewArchitectureMaximumCompute:
      config.factionRules.foundry.newArchitectureCompute,
    foundryGpuMandateEnabled: true,
    foundryGpuRivalsPerMandate: config.factionRules.foundry.everybodyGpuRivalsPerMandate
  };
}

export function effectiveRulesVariant(config, overlay = {}) {
  return {
    ...canonicalRulesVariant(config),
    ...overlay
  };
}
