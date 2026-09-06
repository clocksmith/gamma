import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  addScrutiny,
  availableHeadlines,
  axialDistance,
  calculateAuditDraws,
  commitAction,
  createGame,
  generateBoard,
  legalDestinations,
  locallyEligibleFacilityIds,
  publicMandateAwards,
  resolveTieByInitiative,
  resolveSelectedAction,
  simulateTrainingRun,
  TRAINING_DOMAINS
} from "../web/src/engine.js";

const root = new URL("../", import.meta.url);
const readJson = async (path) => JSON.parse(await readFile(new URL(path, root), "utf8"));
const load = async () => Promise.all([
  readJson("dist/runtime/game-config.json"),
  readJson("dist/runtime/factions.json"),
  readJson("dist/runtime/headlines.json")
]);

test("board generation is deterministic by seed", async () => {
  const [config] = await load();
  const first = generateBoard(config, "same-seed").map((tile) => tile.instanceId);
  const second = generateBoard(config, "same-seed").map((tile) => tile.instanceId);
  const different = generateBoard(config, "different-seed").map((tile) => tile.instanceId);
  assert.deepEqual(first, second);
  assert.notDeepEqual(first, different);
  assert.equal(first[0], "frontier-1");
  assert.equal(first.length, 19);
});

test("game setup rejects obsolete rules selectors", async () => {
 const [config,factions,headlines]=await load();
 for(const playProfileId of ["default-game","advanced-play"])
  assert.throws(()=>createGame(config,factions,headlines,"retired-options","coalition_lab",4,{playProfileId}), /alternate rules options/);
});

test("one Headline deck supplies three draws in every Era", async () => {
 const [, , headlines]=await load();
 assert.deepEqual([1,2,3,4].map(round=>availableHeadlines(headlines,round).length),[5,4,3,4]);
 assert.equal(new Set(headlines.headlines.map(card=>card.id)).size,16);
 assert.ok(headlines.headlines.every(card=>!('requiredRuleModules' in card)&&!('profileText' in card)));
});

test("board is a complete sixfold-symmetric nineteen-hex layout with balanced ring pools", async () => {
  const [config] = await load();
  const board = generateBoard(config, "ring-contract");
  const byDistance = [0, 1, 2].map((distance) =>
    board.filter((tile) => Math.max(
      Math.abs(tile.q),
      Math.abs(tile.r),
      Math.abs(-tile.q - tile.r)
    ) === distance)
  );
  assert.deepEqual(byDistance.map((ring) => ring.length), [1, 6, 12]);
  assert.deepEqual(
    byDistance[1].map((tile) => tile.category).sort(),
    ["capital", "chip", "cloud", "energy", "research", "talent"]
  );
  assert.deepEqual(
    Object.fromEntries(
      ["research", "cloud", "consumer", "media", "government", "energy"]
        .map((category) => [
          category,
          byDistance[2].filter((tile) => tile.category === category).length
        ])
    ),
    { research: 2, cloud: 2, consumer: 2, media: 2, government: 2, energy: 2 }
  );
});

test("complete radius-two topology and duplicated ring resources remain exact", async () => {
  const [config] = await load();
  const board = generateBoard(config, "sparse-topology-contract");
  const edges = board.flatMap((left, leftIndex) =>
    board.slice(leftIndex + 1)
      .filter((right) => axialDistance(left, right) === 1)
      .map((right) => [left, right])
  );
  const degree = (tile) => edges.filter((edge) => edge.includes(tile)).length;

  assert.equal(edges.length, 42);
  assert.deepEqual(
    board.map((tile) => degree(tile)).sort((left, right) => left - right),
    [3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 6, 6, 6, 6, 6, 6, 6]
  );
  assert.equal(edges.filter(([left, right]) =>
    left.placementRing === "outer" && right.placementRing === "outer"
  ).length, 12);

  for (const id of ["research", "cloud"]) {
    const copies = board.filter((tile) => tile.id === id);
    assert.deepEqual(
      copies.map((tile) => tile.placementRing).sort(),
      ["inner", "outer", "outer"]
    );
    for (const field of ["category", "visit", "production", "facilitySpaces"]) {
      assert.equal(copies[0][field], copies[1][field], `${id} copies share ${field}`);
    }
  }

  for (const start of board) {
    const distances = new Map([[start.instanceId, 0]]);
    const queue = [start];
    while (queue.length) {
      const current = queue.shift();
      for (const next of board.filter((tile) => axialDistance(current, tile) === 1)) {
        if (!distances.has(next.instanceId)) {
          distances.set(next.instanceId, distances.get(current.instanceId) + 1);
          queue.push(next);
        }
      }
    }
    for (const destination of board) {
      assert.equal(
        distances.get(destination.instanceId),
        axialDistance(start, destination),
        `${start.instanceId} to ${destination.instanceId} preserves graph distance`
      );
    }
  }
});

test("Audit profiles scale from the four-player base", () => {
  assert.deepEqual(
    [3, 4, 5].map((players) =>
      [2, 3, 4, 5].map((base) => calculateAuditDraws(base, players))
    ),
    [
      [2, 2, 3, 4],
      [2, 3, 4, 5],
      [3, 4, 5, 6]
    ]
  );
});

test("browser game permits two through five players while recommending three through five", async () => {
  const [config, factions, headlines] = await load();
  assert.deepEqual(config.players.playableCounts, [2, 3, 4, 5]);
  assert.deepEqual(config.players.supportedCounts, [3, 4, 5]);
  assert.deepEqual(config.players.historicalOnlyCounts, [2]);
  for (const players of config.players.playableCounts) {
    assert.equal(
      createGame(config, factions, headlines, `playable-${players}`, "coalition_lab", players)
        .playerCount,
      players
    );
  }
  for (const players of [1, 6, 7]) {
    assert.throws(
      () => createGame(
        config,
        factions,
        headlines,
        `out-of-range-${players}`,
        "coalition_lab",
        players
      ),
      /playerCount must be one of 2, 3, 4, 5/
    );
  }
});

test("universal ties resolve from Initiative clockwise", () => {
  const order = ["blue", "green", "red", "yellow"];
  assert.equal(resolveTieByInitiative(["red", "blue"], order, 1), "red");
  assert.equal(resolveTieByInitiative(["blue", "yellow"], order, 2), "yellow");
});

test("action identity locks before piece and destination", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "cycle-contract", "coalition_lab");
  commitAction(state, "fund");
  assert.equal(state.phase, "act");
  assert.equal(state.selectedAction.id, "fund");
  assert.equal(state.selectedPieceId, null);
  assert.equal(state.selectedTileId, null);
  assert.ok(legalDestinations(state, "agent-1").length > 1);
});

test("three different Core Actions advance exactly one era on the fixed map", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "round-contract", "coalition_lab");
  const frontier = state.board.find((tile) => tile.id === "frontier");
  for (const action of ["fund", "influence", "organize"]) {
    commitAction(state, action);
    resolveSelectedAction(config, headlines, state, "agent-1", frontier.instanceId);
  }
  assert.equal(state.phase, "select");
  assert.equal(state.round, 2);
  assert.equal(state.cycle, 1);
  assert.deepEqual(state.player.actionsUsed, []);
  assert.equal(state.player.programUses, undefined);
  assert.deepEqual(
    state.metrics.actionSelections.map((selection) => selection.actionId),
    ["fund", "influence", "organize"]
  );
  assert.ok(!("realignmentVotes" in state.metrics));
});

test("the first Facility is powered by the basic starting grid connection", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "starter-grid", "coalition_lab", 4);
  const buildTile = state.board.find((tile) => tile.category === "research");

  for (const action of ["build", "fund", "influence"]) {
    commitAction(state, action);
    resolveSelectedAction(config, headlines, state, "agent-1", buildTile.instanceId, {
      buildMode: "facility"
    });
  }

  assert.equal(state.metrics.poweredFacilityRounds[0].powered, 1);
  assert.ok(!Object.hasOwn(state.metrics.poweredFacilityRounds[0], "supply"));
  assert.equal(state.player.facilities[0].powered, true);
  assert.ok(!("gridReady" in state.player.facilities[0]));
});

test("Scrutiny beyond the ten-cube supply immediately creates penalties", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "scrutiny-overflow", "coalition_lab");
  state.player.auditBag = Array.from({ length: 10 }, () => state.player.factionId);
  state.player.runway = 2;
  state.player.trust = 3;

  const result = addScrutiny(config, state.player, 3);
  assert.deepEqual(result, { added: 0, overflow: 3, paidRunway: 2, lostTrust: 1 });
  assert.equal(state.player.auditBag.length, 10);
  assert.equal(state.player.runway, 0);
  assert.equal(state.player.trust, 2);
});

test("Loopfold AI's starting Customer is Customer one", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "platform-customer", "platform_empire");
  const consumer = state.board.find((tile) => tile.id === "consumer");
  state.player.capability = 3;

  commitAction(state, "deploy");
  resolveSelectedAction(config, headlines, state, "agent-1", consumer.instanceId);

  assert.equal(state.player.customers, 1);
  assert.ok(state.log.some((entry) => /Customer 2 needs Capability 4/.test(entry)));
});

test("an isolated Generator powers only its nearby Facilities", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "isolated-generator", "coalition_lab");
  state.board = [
    { instanceId: "first-tile", q: 0, r: 0 },
    { instanceId: "remote-tile", q: 3, r: 0 }
  ];
  state.player.facilities = [
    { id: "first", tileId: "first-tile" },
    { id: "remote", tileId: "remote-tile" }
  ];
  state.player.startingGridConnection.assignedFacilityId = "first";
  state.player.generators = [{ id: "isolated", tileId: "remote-tile", capacity: 3 }];
  state.player.links = [];

  const connected = locallyEligibleFacilityIds(state.board, state.player);
  assert.deepEqual([...connected], ["first", "remote"]);
});

test("local Power does not propagate through Facilities", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "local-power-contract", "coalition_lab");
  const [first, adjacent, remote] = state.board.filter((tile) =>
    ["frontier", "research", "consumer"].includes(tile.id)
  );
  state.player.facilities = [
    { id: "first", tileId: first.instanceId, powered: false },
    { id: "adjacent", tileId: adjacent.instanceId, powered: false },
    { id: "remote", tileId: remote.instanceId, powered: false }
  ];
  state.player.startingGridConnection.assignedFacilityId = "first";
  state.player.links = ["remote"];
  const local = locallyEligibleFacilityIds(state.board, state.player);
  assert.deepEqual([...local], ["first"]);
});

test("Customer, Capability, and Trust Mandate are visible and awarded once", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "public-mandate", "platform_empire");
  assert.equal(state.player.mandate, 4);
  assert.deepEqual(
    state.player.mandateAwards.map((award) => award.id).sort(),
    ["customer-1", "trust-2"]
  );
  const frontier = state.board.find((tile) => tile.id === "frontier");
  state.player.capability = 3;
  commitAction(state, "fund");
  resolveSelectedAction(config, headlines, state, "agent-1", frontier.instanceId);
  assert.equal(state.player.mandate, 6);
  assert.equal(
    state.player.mandateAwards.filter((award) => award.id === "capability-3").length,
    1
  );
});

test("public Mandate schedules are canonical at three, four, and five players", async () => {
  const [config] = await load();
  const customerAwards = publicMandateAwards(config, {
    factionId: "platform_empire",
    playerCount: 4,
    customers: 5,
    capability: 0,
    trust: 0
  });
  assert.deepEqual(
    customerAwards.map((award) => [award.id, award.points]),
    [
      ["customer-1", 2],
      ["customer-2", 2],
      ["customer-3", 2],
      ["customer-4", 1],
      ["customer-5", 1]
    ]
  );

  for (const [playerCount, expected] of [
    [3, [2, 2, 2, 2]],
    [4, [2, 2, 2, 2]],
    [5, [2, 2, 2, 2]]
  ]) {
    const awards = publicMandateAwards(config, {
      factionId: "imperial_research_lab",
      playerCount,
      customers: 0,
      capability: 12,
      trust: 0
    });
    assert.deepEqual(
      awards.map((award) => award.points),
      expected,
      `${playerCount}-player common Capability schedule`
    );
  }
});

test("Training studies replay exactly under the same seed", async () => {
  const [config] = await load();
  const first = simulateTrainingRun(config, "training-42", {
    stopAt: 4,
    scientificMethod: true
  });
  const second = simulateTrainingRun(config, "training-42", {
    stopAt: 4,
    scientificMethod: true
  });
  assert.deepEqual(first, second);
  assert.ok(["banked", "crashed", "protected", "human-evaluation", "stopped"].includes(first.outcome));
});

test("the forty-card Training deck preserves its exact special-card contracts", async () => {
  const [config] = await load();
  const domain = (type) => ({ id: type, type, kind: "domain" });
  const special = (type) => ({ id: type, type, kind: "special" });

  const curatedAfterEveryOrdinaryDomain = simulateTrainingRun(
    config,
    "curated-all-domains",
    {
      stopAt: 8,
      researchProtection: 0,
      deck: [
        ...TRAINING_DOMAINS.map(domain),
        special("curated_corpus")
      ]
    }
  );
  assert.equal(curatedAfterEveryOrdinaryDomain.outcome, "crashed");
  assert.equal(curatedAfterEveryOrdinaryDomain.cardsDrawn, 8);
  assert.equal(curatedAfterEveryOrdinaryDomain.ordinaryDomainCount, 7);

  const protectedDuplicate = simulateTrainingRun(config, "protected-duplicate", {
    stopAt: 8,
    scientificMethod: true,
    deck: [domain("code"), domain("code")]
  });
  assert.equal(protectedDuplicate.outcome, "scientific-method-banked");
  assert.equal(protectedDuplicate.crashProtectable, true);
  assert.equal(protectedDuplicate.protection, "scientific_method");
  assert.deepEqual(protectedDuplicate.revealed, ["code", "code"]);

  const benchmarkThenHuman = simulateTrainingRun(config, "benchmark-human", {
    stopAt: 8,
    deck: [special("benchmark_leak"), special("human_evaluation")]
  });
  assert.equal(benchmarkThenHuman.outcome, "human-evaluation");
  assert.equal(benchmarkThenHuman.capability, 2);
  assert.equal(benchmarkThenHuman.scrutiny, 1);
  assert.equal(benchmarkThenHuman.trust, 1);
  assert.deepEqual(benchmarkThenHuman.revealed, ["benchmark_leak", "human_evaluation"]);
});
