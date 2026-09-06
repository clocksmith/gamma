import test from "node:test";
import assert from "node:assert/strict";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { loadPlayerProfiles } from "../lab/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";

test("the deliberate infrastructure plan funds, connects hosts, and selects a legal project", async () => {
  const { match } = await createInteractiveGame({ playerCount: 4, seed: "construction-policy-contract" }, () => {});
  match.choose = async (_policies, _seat, _stage, choices) => choices.at(-1);
  await match.beginRound([]);
  const profiles = await loadPlayerProfiles();
  const policy = new WeightedPlayerPolicy(profiles.find(profile => profile.id === "infrastructure_compounder"),
    { selection: "greedy", treatment: "infrastructure_plan_v1" });
  const choose = choices => policy.rank(match.packet(0, "study", choices))[0].decision;
  const player = match.players[0];
  player.runway = 6;
  const first = choose(match.legalResolutions(0, "build"));
  assert.ok(["cloud", "chip", "research"].includes(first.parameters.destinationCategory));
  match.applyResolution(0, first);
  match.round = 2; await match.beginRound([]);
  player.runway = 1;
  assert.equal(choose(match.legalActionSelections(0)).actionId, "fund");
  player.runway = 4;
  const hosts = choose(match.legalResolutions(0, "build"));
  assert.equal(hosts.parameters.facility, true);
  assert.equal(hosts.parameters.project.id, "generator");
  match.applyResolution(0, hosts);
  assert.equal(match.latestPoweredFacilities(player).length, 2);
  match.round = 3; await match.beginRound([]);
  player.runway = 3; player.compute = 2;
  const cluster = choose(match.legalResolutions(0, "build"));
  assert.equal(cluster.parameters.project.id, "mega_cluster");
  assert.equal(cluster.parameters.facility, false);
  match.applyResolution(0, cluster);
  await match.produceAll([]);
  assert.deepEqual(match.matchMetrics.projectProduction.map(event => [event.round, event.seat, event.nominalCompute]), [[3, 0, 3]]);
  assert.ok(match.matchMetrics.projectProduction[0].gainedCompute <= 3);
  // An existing project that loses its hosts must not count as productive.
  player.facilities = [];
  match.round = 4;
  await match.produceAll([]);
  assert.equal(match.matchMetrics.projectProduction.length, 1);
});
