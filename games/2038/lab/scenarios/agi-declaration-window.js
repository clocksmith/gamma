export const AGI_DECLARATION_WINDOW_SCENARIO_ID =
  "agi_claim_window_v1";

const ARMS = new Set(["eligible", "blocked_compute"]);

export function validateAgiDeclarationScenario(value, playerCount) {
  if (value === null || value === undefined) return null;
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError("scenario must be an object or null.");
  }
  if (value.id !== AGI_DECLARATION_WINDOW_SCENARIO_ID) {
    throw new TypeError(`Unknown deterministic scenario: ${value.id}.`);
  }
  if (!ARMS.has(value.arm)) {
    throw new TypeError(
      `${value.id} arm must be eligible or blocked_compute.`
    );
  }
  const focalSeat = Number(value.focalSeat);
  if (
    !Number.isInteger(focalSeat) ||
    focalSeat < 0 ||
    focalSeat >= playerCount
  ) {
    throw new RangeError(`${value.id} has an invalid focalSeat.`);
  }
  return {
    id: value.id,
    arm: value.arm,
    focalSeat,
    applied: false
  };
}

export function applyAgiDeclarationScenario(match) {
  const scenario = match.scenario;
  if (
    !scenario ||
    scenario.id !== AGI_DECLARATION_WINDOW_SCENARIO_ID ||
    scenario.applied
  ) return;
  if (match.round !== 4 || match.cycle !== 1) return;

  const player = match.players[scenario.focalSeat];
  const requirements = match.currentAgiRequirements();
  const before = {
    score: match.currentScore(player),
    capability: player.capability,
    customers: player.customers,
    trust: player.trust,
    compute: player.compute,
    facilities: player.facilities.length,
    gridReadyFacilities: match.gridReadyFacilityCount(player)
  };

  player.capability = Math.max(player.capability, requirements.capability);
  player.compute = scenario.arm === "eligible"
    ? Math.max(player.compute, requirements.computeCost)
    : Math.max(0, requirements.computeCost - 1);

  match.synchronizePublicMandate(player, "agi_declaration_scenario");
  match.recordAgiCoreRequirements(player, "scenario_injected");
  match.recordEligibility(player, "scenario_injected");
  const readiness = match.declarationReadiness(player);
  const expectedReady = scenario.arm === "eligible";
  if (readiness.ready !== expectedReady) {
    throw new Error(
      `${scenario.id} ${scenario.arm} produced unexpected readiness ` +
      `${readiness.ready} (${readiness.failingRequirement || "none"}).`
    );
  }

  scenario.applied = true;
  match.matchMetrics.scenario = {
    id: scenario.id,
    arm: scenario.arm,
    focalSeat: scenario.focalSeat,
    focalFactionId: player.factionId,
    appliedRound: match.round,
    appliedCycle: match.cycle,
    before,
    afterInjection: {
      score: match.currentScore(player),
      capability: player.capability,
      customers: player.customers,
      trust: player.trust,
      compute: player.compute,
      facilities: player.facilities.length,
      gridReadyFacilities: 0,
      legalDeclaration: readiness.ready,
      failingRequirement: readiness.failingRequirement
    },
    claimed: false,
    declared: false,
    final: null
  };
}

export function markScenarioDeclaration(match, player) {
  const scenario = match.matchMetrics.scenario;
  if (!scenario || scenario.focalSeat !== player.seat) return;
  scenario.declared = true;
  scenario.declarationRound = match.round;
  scenario.declarationCycle = match.cycle;
}

export function markScenarioClaim(match, player) {
  const scenario = match.matchMetrics.scenario;
  if (!scenario || scenario.focalSeat !== player.seat) return;
  scenario.claimed = true;
  scenario.claimRound = match.round;
  scenario.claimCycle = match.cycle;
}

export function finalizeAgiDeclarationScenario(match) {
  const scenario = match.matchMetrics.scenario;
  if (!scenario) return;
  const player = match.players[scenario.focalSeat];
  scenario.final = {
    score: match.currentScore(player),
    mandate: player.mandate,
    capability: player.capability,
    customers: player.customers,
    trust: player.trust,
    compute: player.compute,
    facilities: player.facilities.length,
    gridReadyFacilities: match.gridReadyFacilityCount(player),
    declared: player.agiDeclared
  };
}
