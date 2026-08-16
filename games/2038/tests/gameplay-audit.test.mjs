import assert from "node:assert/strict";
import test from "node:test";

import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";

const trainingCard = (type, kind = "special") => ({
  id: `${type}-fixture`,
  type,
  kind
});

async function makeMatch(options = {}) {
  const runtime = await createInteractiveGame({
    playerCount: 3,
    seed: "gameplay-audit",
    ...options
  }, () => {});
  await runtime.match.setup(runtime.policies);
  return runtime.match;
}

test("interactive Training banks after one reveal and exposes every duplicate reaction", async () => {
  const match = await makeMatch({ factionId: "imperial_research_lab" });
  const player = match.players[0];
  player.researchProtection = 1;
  player.runway = 4;

  match.trainingDrawPile = [trainingCard("code", "domain")];
  match.trainingDiscard = [];
  match.choose = async (_policies, _seat, stage, decisions) => {
    assert.equal(stage, "training_continue");
    return decisions.find((decision) => decision.decisionId === "training_bank");
  };
  const banked = await match.resolveTrainingRunWithPolicies([], 0, {
    destinationCategory: "research"
  });
  assert.equal(banked.outcome, "banked");
  assert.equal(banked.cardsDrawn, 1);
  assert.equal(banked.capability, 1);

  match.trainingDrawPile = [
    trainingCard("science", "domain"),
    trainingCard("science", "domain")
  ];
  let duplicateChoices;
  match.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "training_continue") {
      return decisions.find((decision) => decision.decisionId === "training_continue");
    }
    if (stage === "training_duplicate") {
      duplicateChoices = decisions;
      return decisions.find((decision) => decision.decisionId === "training_accept_crash");
    }
    return decisions[0];
  };
  const crashed = await match.resolveTrainingRunWithPolicies([], 0, {
    destinationCategory: "research"
  });
  assert.deepEqual(
    duplicateChoices.map((decision) => decision.parameters.protection),
    ["research_protection", "research_visit", "scientific_method", null]
  );
  assert.equal(crashed.outcome, "crashed");
  assert.equal(crashed.researchProtectionSpent, 0);
  assert.equal(player.researchProtection, 1);
});

test("only banked ordinary Training domains drive domain-counting effects", async () => {
  const run = async ({ capability, ordinaryDomainCount }) => {
    const match = await makeMatch({
      factionId: "imperial_research_lab",
      seed: `domain-accounting-${capability}-${ordinaryDomainCount}`
    });
    await match.beginRound([]);
    const player = match.players[0];
    player.compute = 5;
    player.capability = 0;
    match.regime.cycle = { id: "recursive_self_improvement" };
    const decision = match.legalResolutions(0, "research")[0];
    decision.parameters.scalingLawBreakthrough = true;
    decision.parameters.trainingResult = {
      outcome: "banked",
      capability,
      ordinaryDomainCount,
      distinctDomains: ordinaryDomainCount,
      ordinaryDomains: [],
      trust: 0,
      scrutiny: 0,
      runwaySpent: 0,
      researchProtectionSpent: 0,
      cardsDrawn: 1,
      revealed: ["benchmark_leak"]
    };
    match.applyResolution(0, decision);
    return player;
  };

  const benchmarkOnly = await run({ capability: 2, ordinaryDomainCount: 0 });
  assert.equal(benchmarkOnly.capability, 2);
  assert.equal(benchmarkOnly.roundMetrics.bestTrainingDomains, 0);

  const twoDomains = await run({ capability: 2, ordinaryDomainCount: 2 });
  assert.equal(twoDomains.capability, 6);
  assert.equal(twoDomains.roundMetrics.bestTrainingDomains, 2);
});

test("Fund records post-cap gain and Frontier Research has no hidden Capability", async () => {
  const match = await makeMatch({ seed: "fund-and-frontier" });
  await match.beginRound([]);
  const player = match.players[0];
  player.runway = 11;
  const fund = match.legalResolutions(0, "fund").find(
    (decision) => decision.parameters.mode === "venture"
  );
  match.applyResolution(0, fund);
  assert.equal(player.runway, 12);
  assert.equal(player.roundMetrics.fundRunway, 1);

  player.actionsUsed = player.actionsUsed.filter((action) => action !== "research");
  player.compute = 2;
  const frontier = match.board.find((tile) => tile.category === "frontier");
  const research = match.legalResolutions(0, "research").find(
    (decision) => decision.parameters.destinationId === frontier.instanceId
  );
  const before = player.capability;
  research.parameters.trainingResult = {
    outcome: "banked",
    capability: 1,
    ordinaryDomainCount: 1,
    distinctDomains: 1,
    ordinaryDomains: ["code"],
    trust: 0,
    scrutiny: 0,
    runwaySpent: 0,
    safetySpent: 0,
    cardsDrawn: 1,
    revealed: ["code"]
  };
  match.applyResolution(0, research);
  assert.equal(player.capability - before, 1);
});

test("Recruit and Redistribute retain exact sequential movement choices", async () => {
  const match = await makeMatch({ seed: "organize-movement-paths" });
  const player = match.players[0];
  const [ceo, team] = player.pieces;
  const starts = new Map(player.pieces.map((piece) => [piece.id, piece.tileId]));
  let recruitStep = 0;
  const recruitPath = [];
  match.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "organize_recruit_follow_up") {
      return decisions.find((decision) => decision.parameters.pieceId === ceo.id);
    }
    if (stage.startsWith("organize_recruit_follow_up_step_")) {
      recruitStep += 1;
      const selected = decisions.find((decision) => decision.parameters.destinationId);
      recruitPath.push(selected.parameters.destinationId);
      return selected;
    }
    return decisions[0];
  };
  await match.resolveRecruitFollowUp([], 0);
  assert.equal(recruitStep, 2);
  assert.equal(recruitPath.length, 2);
  assert.notEqual(recruitPath[0], starts.get(ceo.id));

  const positionsBeforeRedistribute = new Map(
    player.pieces.map((piece) => [piece.id, piece.tileId])
  );
  let movement = 0;
  match.choose = async (_policies, _seat, _stage, decisions) => {
    if (movement >= 2) {
      return decisions.find((decision) => decision.parameters.finish);
    }
    const pieceId = movement++ === 0 ? ceo.id : team.id;
    return decisions.find((decision) =>
      decision.parameters.pieceId === pieceId && decision.parameters.destinationId
    );
  };
  await match.resolveAdditionalMovement([], 0, {
    stage: "organize_redistribute",
    steps: 5
  });
  assert.notEqual(ceo.tileId, positionsBeforeRedistribute.get(ceo.id));
  assert.notEqual(team.tileId, positionsBeforeRedistribute.get(team.id));
  assert.equal(movement, 2);
});

test("effective costs are applied before legality for Cloud, Foundry, and deepfake Deploy", async () => {
  const match = await makeMatch({ seed: "effective-cost-legality" });
  const player = match.players[0];
  player.compute = 0;
  const cloudResearch = match.legalResolutions(0, "research").filter(
    (decision) => decision.parameters.destinationCategory === "cloud"
  );
  assert.ok(cloudResearch.length > 0);
  assert.ok(cloudResearch.every((decision) => decision.parameters.actualComputeCost === 0));

  player.runway = 1;
  const foundryBuild = match.legalResolutions(0, "build").filter(
    (decision) =>
      decision.parameters.buildMode === "facility" &&
      decision.parameters.destinationCategory === "chip"
  );
  assert.ok(foundryBuild.length > 0);
  assert.ok(foundryBuild.every((decision) => decision.parameters.actualRunwayCost === 1));

  player.capability = 12;
  player.compute = 1;
  match.regime.round = { deepfake: "regulate" };
  assert.equal(match.legalResolutions(0, "deploy").some(
    (decision) =>
      decision.parameters.destinationCategory === "media" &&
      decision.parameters.computeCost === 2
  ), false);
  player.compute = 2;
  assert.equal(match.legalResolutions(0, "deploy").some(
    (decision) =>
      decision.parameters.destinationCategory === "media" &&
      decision.parameters.computeCost === 2
  ), true);
});

test("Production Compute includes Joint Ventures but excludes immediate Facility effects", async () => {
  const match = await makeMatch({ seed: "production-compute-scope" });
  match.round = 3;
  await match.beginRound([]);
  const [leftPlayer, rightPlayer] = match.players;
  const leftTile = match.board.find((tile) => tile.category === "research");
  const rightTile = match.board.find((tile) =>
    tile.category === "cloud" && match.areAdjacent(leftTile.instanceId, tile.instanceId)
  ) || match.board.find((tile) => tile.category === "cloud");
  if (!match.areAdjacent(leftTile.instanceId, rightTile.instanceId)) {
    rightTile.q = leftTile.q + 1;
    rightTile.r = leftTile.r;
  }
  leftPlayer.facilities = [{
    id: "left-1",
    tileId: leftTile.instanceId,
    category: "research",
    powered: false
  }];
  rightPlayer.facilities = [{
    id: "right-1",
    tileId: rightTile.instanceId,
    category: "cloud",
    powered: false
  }];
  leftPlayer.compute = 0;
  rightPlayer.compute = 0;
  match.contracts = [{
    id: 1,
    kind: "joint_venture",
    createdRound: 2,
    left: { seat: leftPlayer.seat, facilityId: "left-1" },
    right: { seat: rightPlayer.seat, facilityId: "right-1" }
  }];
  match.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "power_allocation") {
      return [...decisions].sort((left, right) =>
        (right.consequences.poweredFacilities || 0) -
        (left.consequences.poweredFacilities || 0)
      )[0];
    }
    return decisions[0];
  };

  await match.produceAll([]);
  assert.equal(leftPlayer.roundMetrics.computeProduced, 2);
  assert.equal(rightPlayer.roundMetrics.computeProduced, 3);

  const immediateBefore = leftPlayer.roundMetrics.computeProduced;
  await match.produceFacility([], leftPlayer, {
    id: "immediate-cloud",
    category: "cloud",
    tileId: rightTile.instanceId
  }, "headline_immediate");
  assert.equal(leftPlayer.roundMetrics.computeProduced, immediateBefore);
});

test("Advanced supplemental Power is chosen before Headline Power and allocation", async () => {
  const match = await makeMatch({
    seed: "supplemental-power-timing",
    rulesVariant: { playProfileId: "advanced-play" }
  });
  match.round = 3;
  await match.beginRound([]);
  match.regime.round.emergencyPowerAuthority = true;
  const [buyer, supplier] = match.players;
  const supplierTile = match.board.find((tile) => tile.id === "renewable_basin");
  const buyerTile = match.board.find((tile) =>
    tile.instanceId !== supplierTile.instanceId &&
    match.areAdjacent(tile.instanceId, supplierTile.instanceId)
  );
  buyer.facilities = [{
    id: "buyer-1",
    tileId: buyerTile.instanceId,
    category: buyerTile.category,
    powered: false
  }];
  supplier.facilities = [{
    id: "supplier-1",
    tileId: supplierTile.instanceId,
    category: supplierTile.category,
    powered: false
  }];
  supplier.generators = [{
    id: "supplier-generator",
    tileId: supplierTile.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 3
  }];
  buyer.runway = 3;
  const stages = [];
  match.choose = async (_policies, seat, stage, decisions) => {
    stages.push(stage);
    if (stage === "power_purchase_0" && seat === buyer.seat) {
      return decisions.find((decision) => decision.parameters?.supplierSeat === supplier.seat);
    }
    if (stage.startsWith("power_sale_") && seat === supplier.seat) {
      return decisions.find((decision) => decision.decisionId.startsWith("power_sale_accept_"));
    }
    if (stage === "production_emergency_power") {
      return decisions.find((decision) => decision.parameters.power === 0);
    }
    if (stage === "power_allocation") {
      return [...decisions].sort((left, right) =>
        (right.consequences.poweredFacilities || 0) -
        (left.consequences.poweredFacilities || 0)
      )[0];
    }
    return decisions[0];
  };
  await match.produceAll([]);
  assert.ok(stages.indexOf("power_purchase_0") >= 0);
  assert.ok(stages.indexOf("production_emergency_power") > stages.indexOf("power_purchase_0"));
  assert.ok(stages.indexOf("production_emergency_power") < stages.indexOf("power_allocation"));
});

test("Export Controls blocks Allocation Window and AI law thresholds scale by rivals", async () => {
  const blocked = await makeMatch({
    factionId: "foundry",
    seed: "allocation-export-controls"
  });
  blocked.round = 2;
  blocked.regime.cycle = { computeTradeBlocked: true };
  let timingChoices;
  blocked.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "allocation_window_timing") timingChoices = decisions;
    return decisions[0];
  };
  await blocked.preSelectionFactionPowers([]);
  assert.deepEqual(timingChoices.map((decision) => decision.decisionId), ["allocation_wait"]);
  assert.equal(Boolean(blocked.players[0].factionAbilityUsed.allocationWindow), false);

  for (const [playerCount, required] of [[3, 1], [6, 3]]) {
    const match = await makeMatch({
      playerCount,
      seed: `law-threshold-${playerCount}`
    });
    await match.beginRound([]);
    match.regime.cycle = { lawController: 0, incentivizedAction: "research" };
    const controller = match.players[0];
    const before = controller.trust;
    const selections = Array.from({ length: playerCount }, () => "fund");
    for (let index = 1; index <= required; index += 1) selections[index] = "research";
    await match.postCycle([], selections);
    assert.equal(controller.trust, Math.min(6, before + 1));
  }
});

test("Allocation Window creates real unsold Compute and expires it at cycle end", async () => {
  const match = await makeMatch({
    factionId: "foundry",
    seed: "allocation-unsold-temporary-compute"
  });
  match.round = 2;
  const foundry = match.players[0];
  foundry.compute = 0;
  for (const rival of match.players.slice(1)) rival.runway = 2;
  const computeBefore = foundry.compute;
  const offerPackets = [];
  match.choose = async (_policies, seat, stage, decisions) => {
    if (stage === "allocation_window_timing") {
      return decisions.find((decision) => decision.decisionId === "allocation_open");
    }
    if (stage.startsWith("allocation_window_")) {
      offerPackets.push(decisions);
      return decisions[0];
    }
    if (stage.startsWith("allocation_response_")) {
      return decisions.find((decision) => decision.decisionId.startsWith("allocation_reject_"));
    }
    return decisions[0];
  };
  await match.preSelectionFactionPowers([]);
  assert.equal(offerPackets.length, 2);
  assert.ok(offerPackets.every((decisions) =>
    decisions.length > 0 && decisions.every((decision) =>
      decision.decisionId.startsWith("allocation_offer_")
    )
  ));
  assert.equal(foundry.compute, computeBefore + 2);
  assert.equal(foundry.temporaryCompute, 2);
  await match.postCycle([], match.players.map(() => "fund"));
  assert.equal(foundry.compute, computeBefore);
  assert.equal(foundry.temporaryCompute, 0);
});

test("deepfake policy and its Customer baseline persist for the Era", async () => {
  const match = await makeMatch({ seed: "deepfake-era-baseline" });
  await match.beginRound([]);
  const player = match.players[0];
  player.customers = 1;
  player.runway = 0;
  match.regime.round.deepfake = "do_nothing";
  match.regime.round.deepfakeIncome = true;
  match.regime.round.deepfakeCustomersAtVote = match.players.map(
    (candidate) => candidate.customers
  );
  match.regime.cycle = { id: "later_cycle" };
  player.customers = 2;
  match.choose = async (_policies, _seat, stage, decisions) =>
    stage === "power_allocation"
      ? decisions.find((decision) => decision.parameters.demand === 0) || decisions[0]
      : decisions[0];
  await match.produceAll([]);
  assert.equal(match.regime.round.deepfake, "do_nothing");
  assert.equal(player.runway, 3);
});

test("Mega-Clusters require two adjacent Facilities owned by the acting player", async () => {
  const match = await makeMatch({ seed: "solo-mega-host-and-scrutiny" });
  match.round = 2;
  await match.beginRound([]);
  const [lead, partner] = match.players;
  const leftTile = match.board.find((tile) => tile.category === "research");
  const rightTile = match.board.find((tile) =>
    tile.instanceId !== leftTile.instanceId &&
    match.areAdjacent(leftTile.instanceId, tile.instanceId)
  );
  lead.facilities = [
    { id: "lead-host", tileId: leftTile.instanceId, category: leftTile.category },
    { id: "lead-second-host", tileId: rightTile.instanceId, category: rightTile.category }
  ];
  partner.facilities = [{ id: "partner-host", tileId: rightTile.instanceId, category: rightTile.category }];
  lead.generators = [{
    id: "lead-generator",
    tileId: leftTile.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 3
  }];
  partner.generators = [{
    id: "partner-generator",
    tileId: rightTile.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 3
  }];
  lead.pieces[0].tileId = leftTile.instanceId;
  lead.runway = 4;
  lead.compute = 3;
  partner.runway = 3;
  partner.compute = 2;
  lead.programUses = 1;
  const legal = match.legalEscalationResolutions(lead.seat, "mega_cluster");
  assert.ok(legal.length > 0);
  assert.ok(legal.every((decision) => decision.parameters.partnerSeat === undefined));
  assert.ok(legal.some((decision) =>
    new Set([decision.parameters.leftId, decision.parameters.rightId]).size === 2 &&
    [decision.parameters.leftId, decision.parameters.rightId].includes("lead-host") &&
    [decision.parameters.leftId, decision.parameters.rightId].includes("lead-second-host")
  ));
  const before = [lead.scrutiny, partner.scrutiny];
  await match.applyEscalation([], lead.seat, "mega_cluster", legal[0]);
  assert.equal(lead.scrutiny, before[0] + 2);
  assert.equal(partner.scrutiny, before[1]);
});

test("Mega-Cluster Power is chosen in the same allocation as its host Facilities", async () => {
  const match = await makeMatch({ seed: "mega-power-allocation-choice" });
  match.round = 2;
  await match.beginRound([]);
  const player = match.players[0];
  const leftTile = match.board.find((tile) => tile.category === "research");
  const rightTile = match.board.find((tile) =>
    tile.instanceId !== leftTile.instanceId &&
    match.areAdjacent(leftTile.instanceId, tile.instanceId)
  );
  player.facilities = [
    { id: "mega-left", tileId: leftTile.instanceId, category: leftTile.category },
    { id: "mega-right", tileId: rightTile.instanceId, category: rightTile.category }
  ];
  player.generators = [{
    id: "mega-generator",
    tileId: leftTile.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 4
  }];
  const cluster = {
    id: "mega-choice",
    leadSeat: player.seat,
    partnerSeat: null,
    leftId: "mega-left",
    rightId: "mega-right",
    powered: false
  };
  match.megaClusters = [cluster];
  player.megaClusters = [cluster];
  let allocations;
  match.choose = async (_policies, seat, stage, decisions) => {
    if (stage === "power_allocation" && seat === player.seat) {
      allocations = decisions;
      return decisions.find((decision) =>
        decision.parameters.projectIds.includes(cluster.id)
      );
    }
    if (stage === "power_allocation") return decisions[0];
    return decisions[0];
  };
  await match.produceAll([]);
  assert.ok(allocations.some((decision) => decision.parameters.projectIds.length === 0));
  assert.ok(allocations.some((decision) =>
    decision.parameters.projectIds.includes(cluster.id) &&
    decision.parameters.facilityIds.includes("mega-left") &&
    decision.parameters.facilityIds.includes("mega-right")
  ));
  assert.equal(cluster.powered, true);
});

test("Agent Swarm filters known-unresolvable Core Actions without forced no-ops", async () => {
  const match = await makeMatch({ seed: "agent-swarm-no-dead-actions" });
  match.round = 4;
  await match.beginRound([]);
  const player = match.players[0];
  player.actionsUsed = ["fund", "organize", "deploy", "influence"];
  player.compute = 0;
  player.runway = 0;
  player.escalation = 1;
  const before = player.metrics.forcedNoOps;
  let selectionPackets = 0;
  match.choose = async (_policies, _seat, stage, decisions) => {
    if (stage.startsWith("agent_swarm_")) selectionPackets += 1;
    return decisions[0];
  };
  await match.applyEscalation([], player.seat, "agent_swarm", {
    decisionId: "agent-swarm-fixture",
    label: "Agent Swarm",
    actionId: "agent_swarm",
    parameters: {
      pieceId: player.pieces[0].id,
      destinationId: player.pieces[0].tileId
    }
  });
  assert.equal(selectionPackets, 0);
  assert.equal(player.metrics.forcedNoOps, before);
});

test("Employee-Free returns named Teams after ordinary Organize and Shovels does not aggregate 1+1", async () => {
  const match = await makeMatch({
    factionId: "foundry",
    seed: "employee-free-and-shovels"
  });
  await match.beginRound([]);
  const foundry = match.players[0];
  const organizer = match.players[1];
  organizer.pieces.push({
    id: `s${organizer.seat}-team-2`,
    kind: "team",
    tileId: organizer.pieces[0].tileId
  });
  organizer.teamsInSupply = 1;
  match.regime.cycle = { id: "employee_free_unicorn" };
  const targetTeam = organizer.pieces.find((piece) => piece.id.endsWith("team-2"));
  match.choose = async (_policies, _seat, stage, decisions) => {
    assert.equal(stage, "employee_free_return");
    return decisions.find((decision) =>
      decision.parameters.teamIds.length === 1 &&
      decision.parameters.teamIds[0] === targetTeam.id
    );
  };
  const runwayBefore = organizer.runway;
  await match.resolveEmployeeFreeFollowUp([], organizer.seat);
  assert.equal(organizer.pieces.some((piece) => piece.id === targetTeam.id), false);
  assert.equal(organizer.runway, Math.min(12, runwayBefore + 2));

  const shovelsBefore = foundry.metrics.shovelsIncome;
  match.rewardFoundryComputeSpend(organizer.seat, 1);
  match.rewardFoundryComputeSpend(organizer.seat, 1);
  assert.equal(foundry.metrics.shovelsIncome, shovelsBefore);
  match.rewardFoundryComputeSpend(organizer.seat, 2);
  assert.equal(foundry.metrics.shovelsIncome, shovelsBefore + 1);
});

test("Reorganization exposes every Team destination and the exact optional return", async () => {
  const match = await makeMatch({ seed: "reorganization-explicit-choices" });
  match.round = 2;
  await match.beginRound([]);
  const player = match.players[0];
  player.escalation = 1;
  const secondTeam = {
    id: `s${player.seat}-team-2`,
    kind: "team",
    tileId: player.pieces[0].tileId
  };
  player.pieces.push(secondTeam);
  player.teamsInSupply = 1;
  const captured = [];
  match.choose = async (_policies, _seat, stage, decisions) => {
    captured.push({ stage, decisions });
    if (stage === "reorganization_return") {
      return decisions.find((decision) => decision.parameters.teamId === secondTeam.id);
    }
    return decisions.at(-1);
  };
  const runwayBefore = player.runway;
  const scrutinyBefore = player.scrutiny;
  await match.applyEscalation([], player.seat, "reorganization", {
    decisionId: "reorganization-fixture",
    label: "Reorganization",
    actionId: "reorganization",
    parameters: {
      pieceId: player.pieces[0].id,
      destinationId: player.pieces[0].tileId
    }
  });
  const movePackets = captured.filter((entry) => entry.stage.startsWith("reorganization_move_"));
  assert.equal(movePackets.length, 2);
  assert.ok(movePackets.every((entry) => entry.decisions.length > 1));
  assert.equal(player.pieces.some((piece) => piece.id === secondTeam.id), false);
  assert.equal(player.runway, Math.min(12, runwayBefore + 3));
  assert.equal(player.scrutiny, scrutinyBefore + 1);
});

test("Scrutiny overflow and Audit apply the same automatic Runway/Trust penalty", async () => {
  const match = await makeMatch({ seed: "scrutiny-and-audit-choices" });
  const player = match.players[0];
  player.scrutiny = 10;
  player.runway = 2;
  player.trust = 2;
  match.addScrutiny(player, 1);
  await match.settlePendingScrutinyOverflow([], "scrutiny_overflow_test");
  assert.equal(player.runway, 1);
  assert.equal(player.trust, 2);

  match.round = 4;
  player.runway = 0;
  player.trust = 2;
  match.applyAutomaticPenalty(player, "audit_choice_test");
  assert.equal(player.runway, 0);
  assert.equal(player.trust, 1);
});

test("Tactics are explicit, deterministic, target-selected, and cycle-bounded", async () => {
  const match = await makeMatch({
    seed: "tactic-lifecycle",
    rulesVariant: { tacticsEnabled: true }
  });
  assert.equal(match.rulesVariant.tacticsEnabled, true);
  assert.ok(match.players.every((player) => player.tactics.length === 1));
  await match.beginRound([]);
  assert.ok(match.players.every((player) => player.tactics.length === 2));

  const player = match.players[0];
  player.tactics = ["api_price_cut", "model_card", "board_reshuffle"];
  match.tacticDrawPile.unshift("custom_silicon");
  match.choose = async (_policies, seat, stage, decisions) => {
    if (seat === player.seat && stage === "tactic_hand_limit") {
      return decisions.find((decision) => decision.parameters.tacticId === "model_card");
    }
    return decisions[0];
  };
  await match.beginRound([]);
  assert.equal(player.tactics.length, 3);
  assert.ok(!player.tactics.includes("model_card"));
  assert.ok(match.tacticDiscard.includes("model_card"));

  const beneficiary = match.players[2];
  player.tactics = ["cloud_partnership"];
  player.runway = 3;
  const beneficiaryRunway = beneficiary.runway;
  match.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "tactic_resolution") {
      return decisions.find((decision) => decision.parameters.tacticId === "cloud_partnership");
    }
    if (stage === "tactic_cloud_partnership_target") {
      return decisions.find((decision) => decision.parameters.targetSeat === beneficiary.seat);
    }
    return decisions[0];
  };
  await match.maybePlayTacticForResolution([], 0, {
    decisionId: "fund_fixture",
    label: "Fund",
    actionId: "fund",
    parameters: {}
  });
  assert.equal(beneficiary.runway, beneficiaryRunway + 1);
  assert.deepEqual(player.tactics, []);
  assert.deepEqual(match.tacticDiscard.at(-1), "cloud_partnership");
});

test("Tactic action context and exact target choices are retained", async () => {
  const createTacticMatch = (seed) => makeMatch({
    seed,
    rulesVariant: { tacticsEnabled: true }
  });

  const talent = await createTacticMatch("tactic-talent-target");
  const talentPlayer = talent.players[0];
  talentPlayer.tactics = ["talent_raid"];
  talentPlayer.runway = 3;
  talentPlayer.teamsInSupply = 1;
  const talentDestination = talent.board.find((tile) => tile.category === "media");
  talent.choose = async (_policies, _seat, stage, decisions) =>
    stage === "tactic_resolution"
      ? decisions.find((decision) => decision.parameters.tacticId === "talent_raid")
      : decisions[0];
  await talent.maybePlayTacticForResolution([], 0, {
    decisionId: "talent-action",
    label: "Influence",
    actionId: "influence",
    parameters: { destinationId: talentDestination.instanceId }
  });
  assert.ok(talentPlayer.pieces.some((piece) =>
    piece.kind === "team" && piece.tileId === talentDestination.instanceId
  ));

  const reshuffle = await createTacticMatch("tactic-board-target");
  const reshufflePlayer = reshuffle.players[0];
  reshufflePlayer.tactics = ["board_reshuffle"];
  reshufflePlayer.actionsUsed = ["organize", "influence"];
  let readyChoices;
  reshuffle.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "tactic_resolution") {
      return decisions.find((decision) => decision.parameters.tacticId === "board_reshuffle");
    }
    if (stage === "tactic_board_reshuffle_target") {
      readyChoices = decisions;
      return decisions.find((decision) => decision.parameters.action === "influence");
    }
    return decisions[0];
  };
  await reshuffle.maybePlayTacticForResolution([], 0, {
    decisionId: "board-action",
    label: "Fund",
    actionId: "fund",
    parameters: {}
  });
  assert.deepEqual(readyChoices.map((decision) => decision.parameters.action), [
    "organize",
    "influence"
  ]);
  assert.deepEqual(reshufflePlayer.actionsUsed, ["organize"]);

  const silicon = await createTacticMatch("tactic-silicon-target");
  const siliconPlayer = silicon.players[0];
  const firstTile = silicon.board.find((tile) => tile.category === "research");
  const secondTile = silicon.board.find((tile) => tile.category === "cloud");
  siliconPlayer.facilities = [
    { id: "silicon-1", tileId: firstTile.instanceId, category: firstTile.category },
    { id: "silicon-2", tileId: secondTile.instanceId, category: secondTile.category }
  ];
  siliconPlayer.tactics = ["custom_silicon"];
  let siliconChoices;
  silicon.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "tactic_resolution") {
      return decisions.find((decision) => decision.parameters.tacticId === "custom_silicon");
    }
    if (stage === "tactic_custom_silicon_target") {
      siliconChoices = decisions;
      return decisions.find((decision) => decision.parameters.facilityId === "silicon-2");
    }
    return decisions[0];
  };
  await silicon.maybePlayTacticForResolution([], 0, {
    decisionId: "silicon-action",
    label: "Fund",
    actionId: "fund",
    parameters: {}
  });
  assert.equal(siliconChoices.length, 2);
  assert.equal(siliconPlayer.facilities[0].customSilicon, undefined);
  assert.equal(siliconPlayer.facilities[1].customSilicon, true);

  const leak = await createTacticMatch("tactic-weights-target");
  const leakPlayer = leak.players[0];
  const rival = leak.players[1];
  rival.facilities = [
    { id: "leak-cloud", tileId: secondTile.instanceId, category: "cloud" },
    { id: "leak-capital", tileId: firstTile.instanceId, category: "capital" }
  ];
  rival.latestProductionSnapshot = {
    round: 2,
    poweredFacilityIds: ["leak-cloud", "leak-capital"],
    offlineFacilityIds: [],
    powerSupply: 2,
    powerDemandSatisfied: 2
  };
  leakPlayer.tactics = ["weights_leak"];
  leakPlayer.runway = 0;
  let leakChoices;
  leak.choose = async (_policies, _seat, stage, decisions) => {
    if (stage === "tactic_resolution") {
      return decisions.find((decision) => decision.parameters.tacticId === "weights_leak");
    }
    if (stage === "tactic_weights_leak_target") {
      leakChoices = decisions;
      return decisions.find((decision) => decision.parameters.facilityId === "leak-capital");
    }
    return decisions[0];
  };
  await leak.maybePlayTacticForResolution([], 0, {
    decisionId: "leak-action",
    label: "Fund",
    actionId: "fund",
    parameters: {}
  });
  assert.ok(leakChoices.some((decision) => decision.parameters.facilityId === "leak-cloud"));
  assert.ok(leakChoices.some((decision) => decision.parameters.facilityId === "leak-capital"));
  assert.equal(leakPlayer.runway, 2);
});

test("Open Letter is public evidence before ordinary Government votes", async () => {
  const match = await makeMatch({
    seed: "open-letter-precommit",
    rulesVariant: { tacticsEnabled: true }
  });
  match.players[0].tactics = ["open_letter"];
  match.players[1].tactics = [];
  match.players[2].tactics = [];
  const capturedVotes = [];
  match.choose = async (_policies, seat, stage, decisions) => {
    if (stage.endsWith("open_letter_precommit")) {
      return decisions.find((decision) => decision.parameters.outcomeId === "accept");
    }
    if (stage.endsWith("_vote")) capturedVotes.push(...decisions);
    return decisions[0];
  };
  await match.governmentVote([], "fixture_vote", [
    { id: "accept", label: "Accept" },
    { id: "reject", label: "Reject" }
  ]);
  assert.ok(match.regime.cycle.publicVoteInterventions.some(
    (entry) => entry.seat === 0 && entry.outcomeId === "accept"
  ));
  assert.ok(match.publicHistory.some((entry) => entry.type === "open_letter_committed"));
  assert.ok(capturedVotes.some(
    (decision) =>
      decision.parameters.outcomeId === "accept" &&
      decision.consequences.publicVotes === 1
  ));
});
