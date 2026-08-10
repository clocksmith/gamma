import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { effectiveRulesVariant } from "../lab/environment/rules-variant.js";
import { canAllocateLocalPower } from "../lab/rules/local-power-allocation.js";

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

test("single-generator contract is canonical in both play profiles", async () => {
  const config = await readJson("dist/runtime/game-config.json");
  const defaultRules = effectiveRulesVariant(config);
  const advancedRules = effectiveRulesVariant(config, {
    playProfileId: "advanced-play"
  });

  assert.equal(defaultRules.singleGeneratorRule.id, "single-generator-default");
  assert.equal(advancedRules.singleGeneratorRule.id, "single-generator-default");
  assert.deepEqual(defaultRules.singleGeneratorRule, advancedRules.singleGeneratorRule);
  assert.ok(!config.playProfiles.defaultGame.moduleIds.includes(
    "single-generator-default"
  ));
  assert.ok(!config.playProfiles.advancedPlay.moduleIds.includes(
    "single-generator-default"
  ));
});

test("precision patch prints final Generator prices and consolidated state", async () => {
  const [config, factions, mapReference, coreRules, componentReference] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    readJson("dist/runtime/factions.json"),
    readFile(new URL("dist/docs/map-reference.md", root), "utf8"),
    readFile(new URL("dist/docs/core-rules.md", root), "utf8"),
    readFile(new URL("dist/docs/component-reference.md", root), "utf8")
  ]);
  const locations = new Map(config.board.tiles.map((location) => [
    location.id,
    location
  ]));

  assert.equal(
    locations.get("grid_reactor").visit,
    "Build Emergency Power Complex here for 1 Runway."
  );
  assert.equal(
    locations.get("renewable_basin").visit,
    "Build Civic Heat Battery here for 2 Runway."
  );
  assert.match(mapReference, /Power Corridor \| Build Emergency Power Complex here for one Runway/);
  assert.match(mapReference, /Thermal and Water Basin \| Build Civic Heat Battery here for two Runway/);
  assert.doesNotMatch(mapReference, /Infrastructure Build costs one less/);
  assert.doesNotMatch(mapReference, /Civic Heat Battery costs one less/);

  assert.match(coreRules, /four\s+Facilities/);
  assert.match(coreRules, /one persistent institutional identity and one\s+signature program/);
  assert.doesNotMatch(coreRules, /Escalation token/);
  assert.match(componentReference, /\n- Four Facilities\n/);
  assert.doesNotMatch(componentReference, /Grid-Ready/);
  assert.match(componentReference, /Gain, spend, and lose Escalation availability/);

  const coalition = factions.factions.find((faction) => faction.id === "coalition_lab");
  const vertical = factions.factions.find((faction) => faction.id === "vertical_empire");
  assert.match(coalition.abilities[1].text, /both fixed host Facilities are powered and within 2 hexes/);
  assert.match(vertical.abilities[1].text, /legal Power eligibility under the selected profile/);
  assert.doesNotMatch(vertical.abilities[1].text, /Recalculate its Network/);
});

test("single-generator contract fails explicitly when incomplete", async () => {
  const config = await readJson("dist/runtime/game-config.json");
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
    (decision) => decision.parameters?.buildMode === "generator"
  );
  const byDestination = new Map();
  for (const decision of decisions) {
    const destination = match.board.find(
      (tile) => tile.instanceId === decision.parameters.destinationId
    );
    const facts = byDestination.get(destination.id) || new Set();
    facts.add(JSON.stringify({
      sourceId: decision.parameters.sourceId,
      cost: decision.parameters.actualRunwayCost
    }));
    byDestination.set(destination.id, facts);
    assert.equal(decision.parameters.generatorRuleId, "single-generator-default");
    assert.ok(!decision.decisionId.includes("clean_infrastructure"));
    assert.ok(!decision.decisionId.includes("emergency_infrastructure"));
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
    (decision) => decision.parameters?.sourceId === "clean_infrastructure"
  );
  const cleanTrust = cleanPlayer.trust;
  clean.applyResolution(0, cleanDecision);
  assert.equal(cleanPlayer.runway, 8);
  assert.equal(cleanPlayer.trust, cleanTrust + 1);
  assert.equal(cleanPlayer.generators[0].capacity, 3);
  assert.equal(
    clean.legalResolutions(0, "build").some(
      (decision) => decision.parameters?.buildMode === "generator"
    ),
    false
  );

  const emergency = await createMatch("emergency");
  const emergencyPlayer = emergency.players[0];
  const emergencyDecision = emergency.legalResolutions(0, "build").find(
    (decision) => decision.parameters?.sourceId === "emergency_infrastructure"
  );
  emergency.applyResolution(0, emergencyDecision);
  assert.equal(emergencyPlayer.runway, 9);
  assert.equal(emergencyPlayer.generators[0].capacity, 4);

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
  assert.equal(emergencyPlayer.facilities[0].powered, true);
  assert.ok(!("gridReady" in emergencyPlayer.facilities[0]));
});

test("single-generator allocation cannot spend dedicated grid Power elsewhere", () => {
  const board = [
    { instanceId: "first-tile", q: 0, r: 0 },
    { instanceId: "generator-tile", q: 2, r: 0 },
    { instanceId: "local-a-tile", q: 2, r: -1 },
    { instanceId: "local-b-tile", q: 1, r: 0 },
    { instanceId: "local-c-tile", q: 2, r: 1 }
  ];
  const player = {
    facilities: [
      { id: "first", tileId: "first-tile" },
      { id: "local-a", tileId: "local-a-tile" },
      { id: "local-b", tileId: "local-b-tile" },
      { id: "local-c", tileId: "local-c-tile" }
    ]
  };
  const common = {
    board,
    player,
    connectedGenerators: [{
      id: "generator",
      tileId: "generator-tile",
      capacity: 3
    }],
    startingGridPower: 1,
    importedPower: 0,
    supplementalPower: 0,
    exportedPower: 1
  };

  assert.equal(canAllocateLocalPower({
    ...common,
    selectedFacilityIds: ["first", "local-a", "local-b"]
  }), true);
  assert.equal(canAllocateLocalPower({
    ...common,
    selectedFacilityIds: ["local-a", "local-b", "local-c"]
  }), false);
});

test("canonical simplification removes stored-token state and keeps two programs per faction", async () => {
  const [config, factions, componentReference] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    readJson("dist/runtime/factions.json"),
    readFile(new URL("dist/docs/component-reference.md", root), "utf8")
  ]);

  assert.equal(config.playerSupply.generators, 1);
  assert.equal(config.playerSupply.influenceCubes, 0);
  assert.ok(factions.factions.every((faction) => faction.abilities.length === 2));
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
    "Public Research Grant",
    "Influence cube"
  ]) assert.ok(!componentReference.includes(removed), `${removed} is absent`);
});
