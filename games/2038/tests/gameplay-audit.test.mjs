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
  assert.equal(banked.capability, 2);

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
    ["scientific_method", null]
  );
  assert.equal(crashed.outcome, "crashed");
  assert.equal(crashed.capability, 0);
  assert.ok(!Object.hasOwn(player, "researchProtection"));
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

  const twoDomains = await run({ capability: 4, ordinaryDomainCount: 2 });
  assert.equal(twoDomains.capability, 4);
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

test("Recruit makes one new persistent assignment with no follow-up travel", async () => {
 const match = await makeMatch(); const player = match.players[0];
 const other = player.pieces[1]; const before = other.tileId;
 const destination = match.board.find(tile => tile.category === "talent");
 const decision = match.legalResolutions(0, "organize").find(choice => choice.parameters.mode === "recruit" && choice.parameters.pieceId === player.pieces[0].id && choice.parameters.destinationId === destination.instanceId);
 match.choose = async () => { throw new Error("Recruit must not request movement"); };
 await match.applyResolutionWithPolicies([], 0, decision);
 assert.equal(other.tileId, before);
 assert.equal(player.pieces.length, 3);
 assert.equal(player.pieces[2].tileId, destination.instanceId);
 assert.ok(!match.legalResolutions(0, "organize").some(choice => choice.parameters.mode === "redistribute"));
});

test("effective costs are applied before legality for Cloud and Foundry", async () => {
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
      decision.parameters.facility && !decision.parameters.project &&
      decision.parameters.destinationCategory === "chip"
  );
  assert.ok(foundryBuild.length > 0);
  assert.ok(foundryBuild.every((decision) => decision.parameters.actualRunwayCost === 1));

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





test("Mega-Cluster operates automatically with connected adjacent hosts", async () => {
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
  match.choose = async (_policies, _seat, stage, decisions) => {
    assert.notEqual(stage, "power_allocation");
    return decisions[0];
  };
  await match.produceAll([]);
  assert.equal(cluster.powered, true);
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
  talentPlayer.agentsInSupply = 1;
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
    piece.kind === "agent" && piece.tileId === talentDestination.instanceId
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
  rival.generators = [{ id: "fixture-generator", tileId: firstTile.instanceId, sourceId: "clean_infrastructure" }];
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
