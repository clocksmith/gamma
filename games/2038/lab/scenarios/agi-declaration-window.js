export const AGI_DECLARATION_WINDOW_SCENARIO_ID =
  "agi_recognition_window_v2";

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
  if (match.round !== 4) return;

  const player = match.players[scenario.focalSeat];
  const requirements = match.currentAgiRequirements();
  const before = {
    score: match.currentScore(player),
    capability: player.capability,
    customers: player.customers,
    trust: player.trust,
    compute: player.compute,
    facilities: player.facilities.length
  };

  player.capability = Math.max(player.capability, requirements.capability);
  player.trust = Math.max(player.trust, requirements.trust);
  // A controlled scenario injects physical evidence explicitly, never a hidden powered flag.
  // Its separately identified report cannot be pooled with ordinary-play evidence.
  const source = match.board.find((tile) => tile.category === "energy");
  const targets = match.board.filter((tile) => tile.category !== "frontier" &&
    (tile.instanceId === source.instanceId || match.areAdjacent(source.instanceId, tile.instanceId)));
  player.generators = [{ id: `s${player.seat}-scenario-generator`, sourceId: "clean_infrastructure", tileId: source.instanceId }];
  player.facilities = targets.slice(0, requirements.poweredFacilities).map((tile, index) => ({
    id: `s${player.seat}-facility-${index + 1}`, tileId: tile.instanceId, category: tile.category
  }));
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
  if (readiness.ready) {
    match.markAgiFunnel(player, "legalDeclarationWindow", "scenario_injected");
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
    readiness: match.declarationReadiness(player),
    declared: player.agiDeclared
  };
}
