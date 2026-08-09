import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { effectiveRulesVariant } from "../lab/environment/rules-variant.js";
import { canAllocateLocalPower } from "../lab/rules/local-power-allocation.js";

const root = new URL("../", import.meta.url);
const readJson = async (path) =>
  JSON.parse(await readFile(new URL(path, root), "utf8"));

async function candidateOverlay() {
  const configurations = await readJson(
    "experimental/data/single-generator-default.rules-configurations.json"
  );
  assert.deepEqual(configurations.map((entry) => entry.id), [
    "canonical",
    "single-generator-default"
  ]);
  assert.deepEqual(configurations[0].overlay, {});
  assert.deepEqual(Object.keys(configurations[1].overlay), ["singleGeneratorRule"]);
  return configurations[1].overlay;
}

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

test("single-generator candidate remains one explicit inactive rules lever", async () => {
  const [config, overlay] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    candidateOverlay()
  ]);
  const defaultRules = effectiveRulesVariant(config);
  const advancedRules = effectiveRulesVariant(config, {
    playProfileId: "advanced-play"
  });

  assert.equal(Object.hasOwn(defaultRules, "singleGeneratorRule"), false);
  assert.equal(Object.hasOwn(advancedRules, "singleGeneratorRule"), false);
  assert.ok(!config.playProfiles.defaultGame.moduleIds.includes(
    "single-generator-default"
  ));
  assert.ok(!config.playProfiles.advancedPlay.moduleIds.includes(
    "single-generator-default"
  ));
  assert.equal(
    effectiveRulesVariant(config, overlay).singleGeneratorRule.id,
    "single-generator-default"
  );
});

test("single-generator candidate fails explicitly on an incomplete contract", async () => {
  const [config, overlay] = await Promise.all([
    readJson("dist/runtime/game-config.json"),
    candidateOverlay()
  ]);
  const invalid = structuredClone(overlay);
  delete invalid.singleGeneratorRule.locations.renewable_basin;

  assert.throws(
    () => effectiveRulesVariant(config, invalid),
    /requires exact grid_reactor and renewable_basin location rules/
  );
});

test("single-generator candidate derives source and cost from Energy location", async () => {
  const overlay = await candidateOverlay();
  const { match } = await createInteractiveGame({
    playerCount: 3,
    seed: "single-generator-location-contract",
    rulesVariant: overlay
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

test("single-generator candidate enforces one ordinary piece and source effects", async () => {
  const overlay = await candidateOverlay();
  const createMatch = async (suffix) => {
    const { match } = await createInteractiveGame({
      playerCount: 3,
      seed: `single-generator-effects-${suffix}`,
      rulesVariant: overlay
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
    powered: false,
    gridReady: false,
    gridReadySupportSeats: []
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
  assert.equal(emergencyPlayer.facilities[0].gridReady, true);
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
