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
