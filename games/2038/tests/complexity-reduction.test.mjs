import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { effectiveRulesVariant } from "../lab/environment/rules-variant.js";
import { connectedFacilityIds } from "../lab/rules/local-power-connections.js";

const root = new URL("../", import.meta.url);
const readJson = async (path) =>
  JSON.parse(await readFile(new URL(path, root), "utf8"));

function maximizingPowerPolicy() {
  return {
    async decide(packet) {
      const selected = [...packet.legalDecisions].sort((left, right) =>
        (right.consequences?.poweredFacilities || 0) -
          (left.consequences?.poweredFacilities || 0) ||
        left.decisionId.localeCompare(right.decisionId)
      )[0];
      return {
        decision: {
          decisionId: selected.decisionId,
          rationale: "Exercise the maximum legal Power allocation."
        },
        receipt: {
          provider: "fixture",
          profileId: "fixture",
          requestId: packet.requestId
        }
      };
    }
  };
}

test("single-generator contract is canonical and obsolete options fail closed", async () => {
 const config=await readJson("dist/runtime/game-config.json");
 assert.equal(effectiveRulesVariant(config).singleGeneratorRule.id,"single-generator-default");
 for(const key of ["playProfileId","moduleIds","realignmentEnabled","networkInfrastructureEnabled","powerPurchaseRequests","headlinePersistentEffectsEnabled","headlinePublicProceduresEnabled","headlineVolatilityEnabled"])
  assert.throws(()=>effectiveRulesVariant(config,{[key]:true}), /Unsupported rules option/);
});

test("local connections retain exact construction prices and remove allocation components", async () => {
 const config = await readJson("dist/runtime/game-config.json");
 const rules = await readFile(new URL("dist/docs/core-rules.md", root), "utf8");
 assert.deepEqual(config.powerSources.map(s => s.runwayCost), [2, 1, 5]);
 assert.ok(config.powerSources.every(s => !Object.hasOwn(s, "capacity")));
 assert.equal(config.playerSupply.agents, 4);
 assert.equal(config.playerSupply.startingAgents, 2);
 assert.equal(config.playerSupply.factionBoardCaptiveSliders, 5);
 for (const key of ["ceos", "teams", "agiDossierCards"]) assert.ok(!Object.hasOwn(config.playerSupply, key));
 assert.ok(!Object.hasOwn(config.sharedSupply, "powerAllocationMarkers"));
 assert.match(rules, /Reason → Act → Observe/);
 assert.doesNotMatch(rules, /Program markers|permanent six-box/);
});

test("single-generator contract fails explicitly when incomplete", async () => {
  const config = await readJson("dist/runtime/game-config.json");
  assert.throws(() => effectiveRulesVariant(config, { singleGeneratorRule: null }), /rule is required/);
  const invalid = structuredClone(config.singleGeneratorRule);
  delete invalid.locations.renewable_basin;

  assert.throws(
    () => effectiveRulesVariant(config, { singleGeneratorRule: invalid }),
    /requires exact grid_reactor and renewable_basin location rules/
  );
});

test("canonical Generator derives source and cost from Energy location", async () => {
  const { match } = await createInteractiveGame({
    playerCount: 3,
    seed: "single-generator-location-contract",
  }, () => {});
  match.round = 2;
  match.players[0].runway = 10;

  const decisions = match.legalResolutions(0, "build").filter(
    (decision) => !decision.parameters?.facility && decision.parameters?.project?.id === "generator"
  );
  const byDestination = new Map();
  for (const decision of decisions) {
    const destination = match.board.find(
      (tile) => tile.instanceId === decision.parameters.destinationId
    );
    const facts = byDestination.get(destination.id) || new Set();
    facts.add(JSON.stringify({
      sourceId: decision.parameters.project.sourceId,
      cost: decision.parameters.actualRunwayCost
    }));
    byDestination.set(destination.id, facts);
  }

  assert.deepEqual([...byDestination.get("grid_reactor")], [
    JSON.stringify({ sourceId: "emergency_infrastructure", cost: 1 })
  ]);
  assert.deepEqual([...byDestination.get("renewable_basin")], [
    JSON.stringify({ sourceId: "clean_infrastructure", cost: 2 })
  ]);
});

test("canonical Generator enforces one ordinary piece and source effects", async () => {
  const createMatch = async (suffix) => {
    const { match } = await createInteractiveGame({
      playerCount: 3,
      seed: `single-generator-effects-${suffix}`
    }, () => {});
    match.round = 2;
    match.players[0].runway = 10;
    return match;
  };

  const clean = await createMatch("clean");
  const cleanPlayer = clean.players[0];
  const cleanDecision = clean.legalResolutions(0, "build").find(
    (decision) => !decision.parameters?.facility && decision.parameters?.project?.sourceId === "clean_infrastructure"
  );
  const cleanTrust = cleanPlayer.trust;
  clean.applyResolution(0, cleanDecision);
  assert.equal(cleanPlayer.runway, 8);
  assert.equal(cleanPlayer.trust, cleanTrust + 1);
  assert.ok(!Object.hasOwn(cleanPlayer.generators[0], "capacity"));
  assert.equal(
    clean.legalResolutions(0, "build").some(
      (decision) => !decision.parameters?.facility && decision.parameters?.project?.id === "generator"
    ),
    false
  );

  const emergency = await createMatch("emergency");
  const emergencyPlayer = emergency.players[0];
  const emergencyDecision = emergency.legalResolutions(0, "build").find(
    (decision) => !decision.parameters?.facility && decision.parameters?.project?.sourceId === "emergency_infrastructure"
  );
  emergency.applyResolution(0, emergencyDecision);
  assert.equal(emergencyPlayer.runway, 9);
  assert.ok(!Object.hasOwn(emergencyPlayer.generators[0], "capacity"));

  emergencyPlayer.facilities = [{
    id: "s0-facility-1",
    tileId: emergencyDecision.parameters.destinationId,
    category: "energy",
    powered: false
  }];
  for (const rival of emergency.players.slice(1)) {
    rival.facilities = [];
    rival.generators = [];
  }
  const scrutinyBefore = emergencyPlayer.scrutiny;
  await emergency.produceAll(
    emergency.players.map(() => maximizingPowerPolicy())
  );
  assert.equal(emergencyPlayer.scrutiny, scrutinyBefore + 1);
  assert.deepEqual(
    emergencyPlayer.latestProductionSnapshot.poweredFacilityIds,
    [emergencyPlayer.facilities[0].id]
  );
  assert.equal(emergencyPlayer.facilities[0].powered, true);
  assert.ok(!("gridReady" in emergencyPlayer.facilities[0]));
});

test("local connections cover every nearby Facility without capacity or propagation", () => {
 const board = [
  { instanceId: "starter", q: -2, r: 0 }, { instanceId: "source", q: 0, r: 0 },
  { instanceId: "a", q: 1, r: 0 }, { instanceId: "b", q: 0, r: 1 },
  { instanceId: "c", q: 1, r: -1 }, { instanceId: "far", q: 2, r: 0 }
 ];
 const player = { facilities: ["starter", "a", "b", "c", "far"].map(id => ({ id, tileId: id })),
  generators: [{ tileId: "source" }] };
 assert.deepEqual([...connectedFacilityIds(board, player)], ["starter", "a", "b", "c"]);
 player.facilities[0].tileId = "far";
 assert.ok(connectedFacilityIds(board, player).has("starter"), "starting grid travels with Facility 1");
 player.generators = [];
 assert.deepEqual([...connectedFacilityIds(board, player)], ["starter"]);
});

test("canonical simplification removes stored-token state and keeps one permanent ability per faction", async () => {
  const [config, factions, componentReference] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    readJson("dist/runtime/factions.json"),
    readFile(new URL("dist/docs/component-reference.md", root), "utf8")
  ]);

  assert.equal(config.playerSupply.generators, 1);
  assert.equal(config.playerSupply.influenceCubes, 0);
  assert.ok(factions.factions.every((faction) => faction.abilities.length === 1));
  assert.ok(factions.factions.every((faction) =>
    faction.abilities.every((ability) => typeof ability.id === "string")
  ));
  for (const removed of [
    "Market Access",
    "Build discount",
    "Policy Shield",
    "Economic Benchmark",
    "Expert",
    "Spotlight",
    "Public Research Grant"
  ]) assert.ok(!componentReference.includes(removed), `${removed} is absent`);
  // The consolidated inventory mentions retired pieces only to exclude them.
  assert.match(componentReference, /There is no[\s\S]*Influence cube/);
  assert.doesNotMatch(componentReference, /^- .*Influence cube/m);
});
