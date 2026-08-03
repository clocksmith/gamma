export const AGI_DECLARATION_WINDOW_SCENARIO_ID =
  "agi_declaration_window_v1";

const ARMS = new Set(["eligible", "blocked_grid_ready"]);

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
      `${value.id} arm must be eligible or blocked_grid_ready.`
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

function availableFacilityTile(match, player, index) {
  const occupiedByPlayer = new Set(
    player.facilities.map((facility) => facility.tileId)
  );
  const candidates = match.board.filter((tile) =>
    tile.category !== "frontier" &&
    !occupiedByPlayer.has(tile.instanceId) &&
    match.tileOccupancy(tile.instanceId) <
      (tile.facilitySpaces ?? match.config.board.facilitySpacesPerHex)
  );
  if (!candidates.length) {
    throw new Error("AGI declaration scenario could not place a legal Facility.");
  }
  return candidates[index % candidates.length];
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
  player.customers = Math.max(player.customers, requirements.customers);
  player.trust = Math.max(player.trust, requirements.trust);
  player.compute = Math.max(player.compute, requirements.computeCost);

  while (player.facilities.length < requirements.facilities) {
    const tile = availableFacilityTile(
      match,
      player,
      player.facilities.length
    );
    player.facilities.push({
      id: `scenario-s${player.seat}-facility-${player.facilities.length + 1}`,
      tileId: tile.instanceId,
      category: tile.category,
      powered: true,
      gridReady: false,
      gridReadySupportSeats: []
    });
  }

  for (const candidate of match.players) {
    for (const facility of candidate.facilities) {
      facility.gridReady = false;
      facility.gridReadySupportSeats = [];
    }
  }
  const markedFacilities = scenario.arm === "eligible"
    ? requirements.facilities
    : Math.max(0, requirements.facilities - 1);
  for (const facility of player.facilities.slice(0, markedFacilities)) {
    facility.powered = true;
    facility.gridReady = true;
  }

  match.synchronizePublicMandate(player, "agi_declaration_scenario");
  match.recordAgiCoreRequirements(player, "scenario_injected");
  if (markedFacilities >= requirements.facilities) {
    match.markAgiFunnel(player, "becameGridReady", "scenario_injected", {
      gridReadyFacilities: markedFacilities,
      supportingSeats: []
    });
  }
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
      gridReadyFacilities: readiness.gridReadyFacilities,
      legalDeclaration: readiness.ready,
      failingRequirement: readiness.failingRequirement
    },
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
