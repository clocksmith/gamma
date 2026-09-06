import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";

const headlines = JSON.parse(await readFile(new URL("../dist/runtime/headlines.json", import.meta.url), "utf8")).headlines;
async function game(factionId = "coalition_lab", playerCount = 3) {
  const { match } = await createInteractiveGame({ playerCount, factionId, seed: "three-cuts" }, () => {});
  match.choose = async (_policies, _seat, _stage, choices) => choices.at(-1);
  await match.beginRound([]);
  return match;
}
async function headline(match, id) {
  const card = headlines.find(card => card.id === id);
  match.round = card.round; match.cycle = 1;
  await match.beginRound([]);
  match.headlineDecks[match.round][0] = card;
  await match.prepareHeadline([]);
}

test("all sixteen Headlines finish choices before selection without action use or continuing modifiers", async () => {
  assert.equal(headlines.length, 16);
  for (const card of headlines) {
    assert.equal(card.duration, "immediate", card.id);
    const match = await game();
    const energy = match.board.find(tile => tile.category === "energy");
    for (const player of match.players) {
      player.runway = 6; player.compute = 5; player.capability = 5;
      player.facilities = [{ id: `s${player.seat}-facility-1`, tileId: energy.instanceId, category: energy.category }];
      player.generators = [{ id: `s${player.seat}-generator`, tileId: energy.instanceId, sourceId: player.seat ? "clean_infrastructure" : "emergency_infrastructure" }];
    }
    await headline(match, card.id);
    assert.deepEqual(match.regime.cycle, {}, card.id);
    assert.deepEqual(match.regime.round, {}, card.id);
    for (const player of match.players) assert.deepEqual(player.actionsUsed, [], card.id);
    assert.equal(match.matchMetrics.futureTimeline.at(-1).id, card.id);
    const research = match.legalResolutions(0, "research").find(choice => choice.parameters.destinationCategory === "government");
    assert.equal(research.parameters.actualComputeCost, 1, `${card.id} leaves ordinary Research costs intact`);
  }
});

test("Token Price offer is voluntary and resolved before actions with no later discount or surcharge", async () => {
  const match = await game();
  const before = match.players.map(player => ({ compute: player.compute, scrutiny: player.scrutiny }));
  match.choose = async (_p, seat, _stage, choices) => seat === 0 ? choices.at(-1) : choices[0];
  await headline(match, "ten_dollar_intelligence");
  for (const player of match.players) {
    assert.equal(player.compute, before[player.seat].compute + Number(player.seat === 0));
    assert.equal(player.scrutiny, before[player.seat].scrutiny + Number(player.seat === 0));
  }
  const player = match.players[0];
  const scrutiny = player.scrutiny;
  match.trainingDrawPile = [{ id: "code", type: "code", kind: "domain" }];
  match.trainingDiscard = [];
  const choice = match.legalResolutions(0, "research").find(choice => choice.parameters.destinationCategory === "government");
  choice.parameters.stopAt = 1;
  const compute = player.compute;
  match.applyResolution(0, choice);
  assert.equal(player.compute, compute - 1);
  assert.equal(player.scrutiny, scrutiny);
});

test("immediate risk choices preserve public risk without changing later Research", async () => {
  const match = await game();
  for (const player of match.players) player.compute = 2;
  const before = match.players.map(player => player.capability);
  await headline(match, "recursive_self_improvement");
  assert.equal(match.systemicRisk, match.playerCount);
  for (const player of match.players) {
    assert.equal(player.capability, before[player.seat] + 3);
    assert.equal(player.compute, 0);
    assert.equal(player.scrutiny, 2);
  }
  assert.deepEqual(match.regime.cycle, {});
});

test("retirement is immediate, returns exactly one selected Agent, and preserves one operation", async () => {
  const match = await game();
  const before = match.players.map(player => player.runway);
  await headline(match, "employee_free_unicorn");
  for (const player of match.players) {
    assert.equal(player.pieces.length, 1);
    assert.equal(player.agentsInSupply, 3);
    assert.equal(player.runway, before[player.seat] + 2);
    assert.equal(player.scrutiny, 2);
  }
  await headline(match, "employee_free_unicorn");
  assert.ok(match.players.every(player => player.pieces.length === 1));
});

test("Build supplies an Era III production engine and still leaves Era IV for Fusion", async () => {
  const match = await game("coalition_lab");
  const player = match.players[0];
  const energy = match.board.find(tile => tile.id === "renewable_basin");
  const neighbor = match.board.find(tile => tile.category !== "frontier" && match.areAdjacent(tile.instanceId, energy.instanceId));
  const build = (predicate) => {
    player.runway = 12; player.compute = 10;
    const choice = match.legalResolutions(0, "build").find(predicate);
    assert.ok(choice, `legal construction in Era ${match.round}`);
    match.applyResolution(0, choice);
    assert.deepEqual(player.actionsUsed, ["build"]);
    assert.ok(match.legalActionSelections(0).every(choice => !choice.decisionId.includes("escalation")));
    assert.ok(!match.legalActionSelections(0).some(choice => choice.actionId === "build"));
  };
  build(choice => choice.parameters.facility && choice.parameters.destinationId === neighbor.instanceId);
  match.round = 2; await match.beginRound([]);
  build(choice => choice.parameters.facility && choice.parameters.project?.id === "generator" && choice.parameters.destinationId === energy.instanceId);
  assert.equal(match.latestPoweredFacilities(player).length, 2);
  match.round = 3; await match.beginRound([]);
  build(choice => !choice.parameters.facility && choice.parameters.project?.id === "mega_cluster");
  await match.produceAll([]);
  assert.equal(player.megaClusters.length, 1);
  assert.equal(player.megaClusters[0].powered, true);
  match.round = 4; await match.beginRound([]);
  build(choice => !choice.parameters.facility && choice.parameters.project?.id === "fusion_demonstrator");
  assert.equal(match.fusionBuiltBy, 0);
  assert.equal(player.megaClusters[0].builtEra, 3);
});

test("Build checks the combined price and refuses stale plans without partial construction", async () => {
  const match = await game(); match.round = 2; await match.beginRound([]);
  const player = match.players[0]; player.runway = 8;
  const choice = match.legalResolutions(0, "build").find(choice => choice.parameters.facility && choice.parameters.project?.id === "generator");
  assert.ok(choice);
  player.runway = choice.parameters.actualRunwayCost - 1;
  assert.throws(() => match.applyResolution(0, choice), /no longer legal/);
  assert.equal(player.facilities.length, 0); assert.equal(player.generators.length, 0);
  assert.deepEqual(player.actionsUsed, []);
  assert.ok(!match.legalResolutions(0, "build").some(item => item.decisionId === choice.decisionId));
});

test("factions keep exactly one permanent idea and preserve their original starts and fiction", async () => {
  const current = JSON.parse(await readFile(new URL("../dist/runtime/factions.json", import.meta.url), "utf8"));
  for (const faction of current.factions) {
    assert.equal(faction.abilities.length, 1);
    assert.equal(faction.abilities[0].round, 1);
    assert.equal(faction.abilities[0].timing, "passive");
    assert.ok(!Object.hasOwn(faction, "scoringRule"));
    assert.equal(faction.lore.length, 1);
    assert.ok(!Object.hasOwn(faction.lore[0], "text"));
  }
  assert.equal(current.factions.find(f => f.id === "safety_laboratory").starts.trust, 5);
});

test("Loopfold earns Deploy income without waiving price or Scrutiny; Orisonix keeps ordinary Deploy exposure", async () => {
  for (const faction of ["platform_empire", "safety_laboratory"]) {
    const match = await game(faction); const player = match.players[0];
    player.capability = 4; player.compute = 3;
    const before = { runway: player.runway, scrutiny: player.scrutiny };
    const choice = match.legalResolutions(0, "deploy").find(choice => choice.parameters.destinationCategory === "media");
    match.applyResolution(0, choice);
    assert.equal(player.compute, 2);
    assert.equal(player.scrutiny, before.scrutiny + 1);
    assert.equal(player.runway, before.runway + Number(faction === "platform_empire"));
  }
});

test("Kestralyn discounts the Facility within combined Build and receives no separate Mandate award", async () => {
  const match = await game("vertical_empire"); match.round = 2; await match.beginRound([]);
  const player = match.players[0]; player.runway = 10;
  const choice = match.legalResolutions(0, "build").find(choice => choice.parameters.facility && choice.parameters.project?.sourceId === "emergency_infrastructure");
  assert.equal(choice.parameters.actualRunwayCost, 2);
  const mandate = player.mandate;
  match.applyResolution(0, choice);
  assert.equal(player.runway, 8); assert.equal(player.mandate, mandate);
  assert.equal(player.facilities.length, 1); assert.equal(player.generators.length, 1);
});

test("Corthaven's supplier income uses rival infrastructure and caps at two at three, four, and five players", async () => {
  for (const count of [3, 4, 5]) {
    const match = await game("foundry", count); const player = match.players[0];
    player.runway = 0;
    await match.produceAll([]); assert.equal(player.runway, 0);
    for (const rival of match.players.slice(1)) rival.facilities = [{ id: `s${rival.seat}-facility-1`, tileId: match.board.find(t => t.category === "cloud").instanceId, category: "cloud" }];
    await match.produceAll([]); assert.equal(player.runway, 2);
    assert.equal(player.metrics.shovelsIncome, 2);
    assert.ok(!Object.hasOwn(player.roundMetrics, "shovelsIncome"));
  }
});

test("Dovetalis earns on its own optional trades across turns, never on a rival's turn", async () => {
  const match = await game("coalition_lab"); const player = match.players[0]; const rival = match.players[1];
  player.runway = 5; player.compute = 2; rival.compute = 5; rival.runway = 2;
  const trade = { timing: "before", partnerSeat: 1, giveResource: "runway", giveAmount: 1, receiveResource: "compute", receiveAmount: 1 };
  assert.ok(match.completeImmediateTrade(0, 1, trade));
  assert.equal(player.runway, 5);
  match.cycle = 2;
  assert.ok(match.completeImmediateTrade(0, 1, trade));
  assert.equal(player.runway, 5);
  assert.ok(match.completeImmediateTrade(1, 0, { timing: "before", partnerSeat: 0, giveResource: "runway", giveAmount: 1, receiveResource: "compute", receiveAmount: 1 }));
  assert.equal(player.runway, 6, "only the traded Runway arrives on a rival's turn");
});

test("Mega-Cluster host ownership, shared supply, and stale plans remain authoritative under Build", async () => {
  const match = await game(); match.round = 3; await match.beginRound([]);
  const player = match.players[0]; player.runway = 10; player.compute = 10;
  const energy = match.board.find(t => t.id === "renewable_basin");
  const adjacent = match.board.find(t => t.category !== "frontier" && match.areAdjacent(t.instanceId, energy.instanceId));
  player.facilities = [{ id: "s0-facility-1", tileId: energy.instanceId, category: "energy" }];
  const second = { id: "s1-facility-1", tileId: adjacent.instanceId, category: adjacent.category };
  match.players[1].facilities = [second];
  player.generators = [{ id: "g0", tileId: energy.instanceId, sourceId: "clean_infrastructure" }];
  assert.ok(!match.legalResolutions(0, "build").some(c => !c.parameters.facility && c.parameters.project?.id === "mega_cluster"));
  match.players[1].facilities = []; player.facilities.push({ ...second, id: "s0-facility-2" });
  const choice = match.legalResolutions(0, "build").find(c => !c.parameters.facility && c.parameters.project?.id === "mega_cluster");
  assert.ok(choice);
  match.megaClusters.push({ id: "occupied", leftId: choice.parameters.project.leftId, rightId: choice.parameters.project.rightId });
  assert.throws(() => match.applyResolution(0, choice), /no longer legal/);
  assert.equal(player.runway, 10); assert.equal(player.compute, 10);
  match.megaClusters = Array.from({ length: match.config.sharedSupply.megaClusterPairs }, (_, i) => ({ id: `full-${i}`, leftId: `left-${i}`, rightId: `right-${i}` }));
  assert.ok(!match.legalResolutions(0, "build").some(c => c.parameters.project?.id === "mega_cluster"));
});

test("Fusion remains unique across all institutions and consumes a Generator slot", async () => {
  const match = await game(); match.round = 4; await match.beginRound([]);
  for (const player of match.players) player.runway = 10;
  const choice = match.legalResolutions(0, "build").find(c => c.parameters.project?.id === "fusion_demonstrator");
  match.applyResolution(0, choice);
  assert.equal(match.fusionBuiltBy, 0);
  assert.ok(match.players.every(player => !match.legalResolutions(player.seat, "build").some(c => c.parameters.project?.id === "fusion_demonstrator")));
});

test("the infrastructure Mandate counts current connections rather than removed Power allocation", async () => {
  const match = await game(); match.round = 2; await match.beginRound([]);
  const player = match.players[0];
  const energy = match.board.find(t => t.id === "renewable_basin");
  const adjacent = match.board.find(t => t.category !== "frontier" && match.areAdjacent(t.instanceId, energy.instanceId));
  player.facilities = [{ id: "a", tileId: energy.instanceId, category: "energy" }, { id: "b", tileId: adjacent.instanceId, category: adjacent.category }];
  player.generators = [{ id: "g", tileId: energy.instanceId, sourceId: "clean_infrastructure" }];
  match.roundMandate = match.mandateDocument.mandates.find(c => c.id === "stack_reaches_horizon");
  const before = player.mandate;
  match.scoreMandate(); assert.equal(player.mandate, before + 2);
});
