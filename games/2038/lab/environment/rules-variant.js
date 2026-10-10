// Experiment knobs change current numbers only. They never restore a removed system.
export const CURRENT_RULE_BOUNDS = Object.freeze({
  fundConservative: [1, 4, 1],
  fundVenture: [3, 7, 1],
  ventureReputationLoss: [0, 2, 1],
  facilityCost: [1, 4, 1],
  deployComputeCost: [1, 3, 1],
  customerPoints: [1, 4, 1],
  reviewRunwayPenalty: [1, 3, 1],
  startingAgentsDeployed: [2, 4, 1],
});
export function canonicalRulesVariant(config) {
  if (config.board.layout !== "shared-hex-radius-two")
    throw new Error("Only the shared-hex rules are current.");
  return {
    kind: "shared-hex-orgs-v1",
    pausedFactionAbilities: [],
    fundConservative: config.actionEffects.fund.conservative,
    fundVenture: config.actionEffects.fund.venture,
    ventureReputationLoss: config.actionEffects.fund.reputationLoss,
    facilityCost: config.construction.orgEquipmentCost,
    deployComputeCost: config.actionEffects.deploy.computeCost,
    customerPoints: config.scoring.customer,
    reviewRunwayPenalty: config.reputationReview.runwayPenalty,
    startingAgentsDeployed: config.playerSupply.startingAgents,
  };
}
export function effectiveRulesVariant(config, overlay = {}) {
  if (!overlay || typeof overlay !== "object" || Array.isArray(overlay))
    throw new TypeError("rulesVariant must be an object");
  const current = canonicalRulesVariant(config);
  for (const key of Object.keys(overlay))
    if (!Object.hasOwn(current, key))
      throw new RangeError(`Unsupported rules option: ${key}`);
  if (overlay.kind !== undefined && overlay.kind !== current.kind)
    throw new RangeError("Alternate rules modes are unavailable.");
  if (
    overlay.pausedFactionAbilities !== undefined &&
    (!Array.isArray(overlay.pausedFactionAbilities) ||
      overlay.pausedFactionAbilities.some(
        (a) =>
          !a ||
          typeof a.factionId !== "string" ||
          typeof a.abilityId !== "string",
      ))
  )
    throw new TypeError(
      "pausedFactionAbilities must identify faction and ability",
    );
  for (const [key, [min, max]] of Object.entries(CURRENT_RULE_BOUNDS))
    if (
      overlay[key] !== undefined &&
      (!Number.isInteger(overlay[key]) ||
        overlay[key] < min ||
        overlay[key] > max)
    )
      throw new RangeError(`Invalid current-rule value: ${key}`);
  const result = { ...current, ...structuredClone(overlay) };
  if (result.fundVenture <= result.fundConservative)
    throw new RangeError("Venture Fund must exceed conservative Fund.");
  return result;
}
