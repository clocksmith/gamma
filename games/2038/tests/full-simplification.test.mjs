import assert from "node:assert/strict";
import test from "node:test";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { simulateTrainingRun } from "../web/src/engine.js";

const card = (type, kind = "domain") => ({ id: `${type}-fixture`, type, kind });
async function game(factionId = "coalition_lab") {
  const { match } = await createInteractiveGame({ playerCount: 3, factionId, seed: "full-simplification" }, () => {});
  match.choose = async (_policies, _seat, _stage, decisions) => decisions[0];
  await match.beginRound([]);
  return match;
}

function qualify(match, player) {
  const energy = match.board.find(tile => tile.category === "energy");
  const neighbor = match.board.find(tile => tile.category !== "frontier" && match.areAdjacent(energy.instanceId, tile.instanceId));
  player.facilities = [energy, neighbor].map((tile, index) => ({ id: `s${player.seat}-facility-${index + 1}`, tileId: tile.instanceId, category: tile.category }));
  player.generators = [{ id: `s${player.seat}-generator`, sourceId: "clean_infrastructure", tileId: energy.instanceId }];
  player.capability = 9; player.trust = 4; player.compute = 3;
}

test("Agents preserve two starting operations, free district assignment, and contested presence", async () => {
  const match = await game();
  const [player, rival] = match.players;
  assert.equal(player.pieces.length, 2);
  assert.equal(player.agentsInSupply, 2);
  assert.ok(player.pieces.every(piece => piece.kind === "agent"));
  const government = match.board.find(tile => tile.category === "government");
  const far = match.board.find(tile => tile.category === "consumer");
  player.pieces[0].tileId = government.instanceId;
  assert.equal(match.districtController(government.instanceId), 0);
  rival.pieces[0].tileId = government.instanceId;
  assert.equal(match.districtController(government.instanceId), null);
  assert.equal(match.legalDestinations(player, player.pieces[0]).length, 19);
  match.assignAgent(player, { pieceId: player.pieces[0].id, destinationId: far.instanceId });
  assert.equal(match.districtController(government.instanceId), 1);
  assert.equal(match.districtController(far.instanceId), 0);
});

test("speculative selection assigns and exhausts when the committed effect cannot resolve", async () => {
  const match = await game();
  const player = match.players[0]; player.compute = 0; player.runway = 0;
  assert.ok(match.legalActionSelections(0).some(choice => choice.actionId === "build"));
  assert.equal(match.legalResolutions(0, "build").length, 0);
  const destination = match.board.find(tile => tile.category === "government");
  match.choose = async (_policies, _seat, stage, choices) => {
    if (stage === "resolve") return choices.find(choice => choice.parameters.destinationId === destination.instanceId);
    return choices.find(choice => choice.decisionId === "trade_none") || choices[0];
  };
  player.selectedAction = "build";
  await match.resolveSelectedSeat([], 0);
  assert.ok(player.pieces.some(piece => piece.tileId === destination.instanceId));
  assert.deepEqual(player.actionsUsed, ["build"]);
  assert.equal(player.compute, 0); assert.equal(player.capability, 0);
  assert.equal(player.metrics.blockedAfterCommitment, 1);
});

test("Organize only recruits or relocates, respects supply, and grants no extra turn", async () => {
  const match = await game(); const player = match.players[0]; player.runway = 12;
  for (let count = 2; count < 4; count++) {
    const choices = match.legalResolutions(0, "organize");
    assert.ok(choices.every(choice => ["recruit", "relocate"].includes(choice.parameters.mode)));
    match.applyResolution(0, choices.find(choice => choice.parameters.mode === "recruit"));
    assert.equal(player.pieces.length, count + 1);
  }
  assert.equal(player.agentsInSupply, 0);
  assert.ok(!match.legalResolutions(0, "organize").some(choice => choice.parameters.mode === "recruit"));
  assert.equal(new Set(player.pieces.map(piece => piece.id)).size, 4);
  assert.equal(match.cycle, 1);
});

test("ordinary Research can crash; Orisonix retains one and the district only rewards banking", async () => {
  const match = await game();
  const duplicate = [card("code"), card("code")];
  const options = { deck: duplicate, stopAt: 7, bankBonus: 1 };
  const ordinary = simulateTrainingRun(match.config, "crash", options);
  assert.equal(ordinary.outcome, "crashed"); assert.equal(ordinary.capability, 0); assert.equal(ordinary.scrutiny, 1);
  const safety = simulateTrainingRun(match.config, "crash", { ...options, crashRetain: 1 });
  assert.equal(safety.capability, 1); assert.equal(safety.scrutiny, 1);
  const bank = simulateTrainingRun(match.config, "bank", { deck: [card("code")], stopAt: 1, bankBonus: 1 });
  assert.equal(bank.capability, 2);
  assert.ok(!Object.hasOwn(match.players[0], "researchProtection"));
});

test("interactive and automatic Research agree on crash retention and destination banking bonuses", async () => {
  for (const factionId of ["coalition_lab", "safety_laboratory"]) {
    for (const destinationCategory of ["research", "government"]) {
      for (const stopAt of [1, 8]) {
        const match = await game(factionId);
        const deck = [card("code"), card("science"), card("code")];
        match.trainingDrawPile = structuredClone(deck); match.trainingDiscard = [];
        match.choose = async (_policies, _seat, stage, choices) => {
          assert.equal(stage, "training_continue", "ordinary duplicate crashes without an insurance decision");
          return choices.find(choice => choice.parameters.continue === (stopAt > 1));
        };
        const interactive = await match.resolveTrainingRunWithPolicies([], 0, { destinationCategory });
        const automatic = simulateTrainingRun(match.config, "parity", {
          deck, stopAt, bankBonus: Number(destinationCategory === "research"),
          crashRetain: Number(factionId === "safety_laboratory")
        });
        for (const field of ["outcome", "capability", "trust", "scrutiny", "cardsDrawn", "ordinaryDomains"]) {
          assert.deepEqual(interactive[field], automatic[field], `${factionId}/${destinationCategory}/${stopAt}/${field}`);
        }
      }
    }
  }
});

test("Scientific Method is an explicit paid banking choice bounded by the Research card", async () => {
  const match = await game("imperial_research_lab"); const player = match.players[0];
  player.runway = 4; player.compute = 4;
  const decision = match.legalResolutions(0, "research").find(choice => choice.parameters.destinationCategory === "research");
  match.trainingDrawPile = [card("code"), card("code")]; match.trainingDiscard = [];
  match.choose = async (_policies, _seat, stage, choices) => {
    if (stage === "training_continue") return choices.find(choice => choice.decisionId === "training_continue");
    if (stage === "training_duplicate") {
      assert.deepEqual(choices.map(choice => choice.parameters.protection), ["scientific_method", null]);
      return choices[0];
    }
    return choices[0];
  };
  await match.applyResolutionWithPolicies([], 0, decision);
  assert.equal(player.runway, 3);
  assert.equal(player.capability, 2);
  assert.equal(player.roundMetrics.scientificMethodUsed, undefined);
  assert.equal(player.pieces.find(piece => piece.id === decision.parameters.pieceId).tileId, decision.parameters.destinationId);
  assert.equal(match.scientificMethodAvailable(player), true);
  assert.ok(!match.legalActionSelections(0).some(choice => choice.actionId === "research"));
});

test("current connection changes affect claims and penalties without another Production", async () => {
  const match = await game(); const player = match.players[0]; qualify(match, player);
  player.latestProductionSnapshot = { poweredFacilityIds: [], offlineFacilityIds: player.facilities.map(f => f.id) };
  assert.equal(match.latestPoweredFacilities(player).length, 2);
  assert.equal(match.declarationReadiness(player).ready, true);
  assert.equal(match.finalMandate(player).offlinePenalty, 0);
  player.generators = [];
  assert.equal(match.latestPoweredFacilities(player).length, 1);
  assert.equal(match.declarationReadiness(player).failingRequirement, "poweredFacilities");
  assert.equal(match.finalMandate(player).offlinePenalty, 1);
});

test("Production never requests allocation and Mega-Clusters need only connected adjacent hosts", async () => {
  const match = await game(); const player = match.players[0]; qualify(match, player);
  player.compute = 0;
  match.round = 2;
  match.megaClusters.push({ id: "fixture-cluster", leadSeat: 0, leftId: player.facilities[0].id, rightId: player.facilities[1].id });
  match.choose = async (_policies, _seat, stage, choices) => {
    assert.doesNotMatch(stage, /allocation|additional_movement|talent_movement/);
    return choices[0];
  };
  await match.produceAll([]);
  assert.equal(match.megaClusters[0].powered, true);
  assert.ok(player.compute >= 3);
  player.generators = [];
  await match.produceAll([]);
  assert.equal(match.megaClusters[0].powered, false);
});

test("every qualifying institution may score AGI without replacing the Mandate winner", async () => {
  const match = await game(); match.round = 4;
  for (const player of match.players.slice(0, 2)) qualify(match, player);
  match.players[2].mandate = 80;
  const scores = match.players.map(player => player.mandate);
  match.choose = async (_policies, _seat, stage, choices) => {
    assert.equal(stage, "agi_achievement");
    return choices.find(choice => choice.decisionId === "agi_declare");
  };
  await match.declareAgiAchievements([]);
  for (const player of match.players.slice(0, 2)) {
    assert.equal(player.compute, 0); assert.equal(player.mandate, scores[player.seat] + 4);
    assert.equal(player.scrutiny, 2); assert.equal(player.agiDeclared, true);
    player.trust = 0;
  }
  await match.declareAgiAchievements([]);
  match.resolveAgiOutcome();
  assert.equal(match.matchMetrics.declarations, 2);
  assert.equal(match.matchMetrics.agiResolution.winnerOverridden, false);
  assert.deepEqual(match.result().winnerSeats, [2]);
  assert.equal(match.result().worldEnding.agiEmerges, true);
});

test("AGI qualification independently enforces every threshold and its final-era window", async () => {
  const match = await game(); const player = match.players[0]; qualify(match, player);
  match.choose = async () => { throw new Error("No AGI decision before Era IV"); };
  await match.declareAgiAchievements([]);
  for (const [field, value] of [["capability", 8], ["trust", 3], ["compute", 2]]) {
    const before = player[field]; player[field] = value;
    assert.equal(match.declarationReadiness(player).failingRequirement, field);
    player[field] = before;
  }
  assert.equal(player.agiDeclared, false);
});

test("combined candidate completes deterministically at three, four, and five players", async () => {
  for (const playerCount of [3, 4, 5]) {
    const options = { playerCount, seed: `combined-${playerCount}`, recordReplay: true };
    const first = await createInteractiveGame(options, () => {});
    const second = await createInteractiveGame(options, () => {});
    first.policies[0] = first.policies[1];
    second.policies[0] = second.policies[1];
    const result = await first.match.play(first.policies);
    const replay = await second.match.play(second.policies);
    assert.deepEqual(result, replay);
    assert.equal(result.futureTimeline.length, 12);
    assert.ok(result.winnerSeats.length > 0);
    for (const player of first.match.players) {
      assert.ok(player.pieces.length >= 1 && player.pieces.length <= 4);
      assert.ok(player.pieces.every(piece => piece.kind === "agent"));
      for (const key of ["runway", "compute", "capability", "customers", "trust", "mandate"]) assert.ok(Number.isFinite(player[key]) && player[key] >= 0, key);
      assert.ok(!Object.hasOwn(player, "agiDossier"));
    }
  }
});
