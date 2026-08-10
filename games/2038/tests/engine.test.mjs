import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  addScrutiny,
  availableHeadlines,
  applyBoardMotion,
  axialDistance,
  calculateAuditDraws,
  castRealignmentVote,
  commitAction,
  createGame,
  generateBoard,
  legalDestinations,
  networkedFacilityIds,
  publicMandateAwards,
  resolveBlindRealignmentVote,
  resolvePlayProfile,
  resolveTieByInitiative,
  resolveSelectedAction,
  simulateTrainingRun
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
  assert.equal(first.length, 13);
});

test("play profiles compose declared rule modules without exposing ad hoc player profiles", async () => {
  const [config] = await load();
  assert.deepEqual(resolvePlayProfile(config, "default-game"), {
    ...config.playProfiles.defaultGame,
    ...config.playRuleDefaults,
    immediateTradeCounteroffers: true
  });
  assert.deepEqual(resolvePlayProfile(config, "advanced-play"), {
    ...config.playProfiles.advancedPlay,
    immediateTradeCounteroffers: true,
    immediateTradeThirdPartyClaims: true,
    powerPurchaseRequests: 2,
    realignmentEnabled: true,
    networkInfrastructureEnabled: true,
    headlinePersistentEffectsEnabled: true,
    headlinePublicProceduresEnabled: true,
    headlineVolatilityEnabled: true
  });
  const invalid = structuredClone(config);
  invalid.playProfiles.advancedPlay.moduleIds = ["third-party-trade-claims"];
  assert.throws(() => resolvePlayProfile(invalid, "advanced-play"), /require trade counteroffers/);
});

test("Default Game excludes Advanced-only Headline procedures while Advanced Play restores them", async () => {
  const [config, , headlines] = await load();
  const defaultProfile = resolvePlayProfile(config, "default-game");
  const advancedProfile = resolvePlayProfile(config, "advanced-play");
  for (const round of [1, 2, 3, 4]) {
    const defaultDeck = availableHeadlines(headlines, round, defaultProfile);
    const advancedDeck = availableHeadlines(headlines, round, advancedProfile);
    assert.ok(defaultDeck.length >= 3, `Default Game has three Headline cards in Era ${round}`);
    assert.ok(defaultDeck.every((card) => !card.requiredRuleModules?.length));
    assert.equal(advancedDeck.length, 6);
  }
});

test("board is a sixfold-symmetric thirteen-hex layout with balanced ring pools", async () => {
  const [config] = await load();
  const board = generateBoard(config, "ring-contract");
  const byDistance = [0, 1, 2].map((distance) =>
    board.filter((tile) => Math.max(
      Math.abs(tile.q),
      Math.abs(tile.r),
      Math.abs(-tile.q - tile.r)
    ) === distance)
  );
  assert.deepEqual(byDistance.map((ring) => ring.length), [1, 6, 6]);
  assert.deepEqual(
    byDistance[1].map((tile) => tile.category).sort(),
    ["capital", "chip", "cloud", "energy", "research", "talent"]
  );
  assert.equal(byDistance[2].filter((tile) => tile.category === "consumer").length, 1);
});

test("sparse board topology and duplicated ring resources remain exact", async () => {
  const [config] = await load();
  const board = generateBoard(config, "sparse-topology-contract");
  const edges = board.flatMap((left, leftIndex) =>
    board.slice(leftIndex + 1)
      .filter((right) => axialDistance(left, right) === 1)
      .map((right) => [left, right])
  );
  const degree = (tile) => edges.filter((edge) => edge.includes(tile)).length;

  assert.equal(edges.length, 24);
  assert.deepEqual(
    board.map((tile) => degree(tile)).sort((left, right) => left - right),
    [2, 2, 2, 2, 2, 2, 5, 5, 5, 5, 5, 5, 6]
  );
  assert.ok(!edges.some(([left, right]) =>
    left.placementRing === "outer" && right.placementRing === "outer"
  ));

  for (const id of ["research", "cloud"]) {
    const copies = board.filter((tile) => tile.id === id);
    assert.deepEqual(copies.map((tile) => tile.placementRing).sort(), ["inner", "outer"]);
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

test("Realignment rotates full rings, carries tile identity, and changes cross-ring adjacency", async () => {
  const [config] = await load();
  const board = generateBoard(config, "realignment-geometry");
  const frontier = board.find((tile) => tile.id === "frontier");
  const inner = board.find((tile) => tile.q === 1 && tile.r === 0);
  const outer = board.find((tile) => tile.q === 2 && tile.r === -1);
  const frontierBefore = { q: frontier.q, r: frontier.r };
  assert.equal(Math.max(
    Math.abs(inner.q - outer.q),
    Math.abs(inner.r - outer.r),
    Math.abs((-inner.q - inner.r) - (-outer.q - outer.r))
  ), 1);

  const motion = config.board.realignment.motions.find(
    (candidate) => candidate.id === "consolidate_core"
  );
  const receipt = applyBoardMotion(board, motion);
  assert.equal(receipt.movements.length, 6);
  assert.deepEqual({ q: frontier.q, r: frontier.r }, frontierBefore);
  assert.deepEqual({ q: inner.q, r: inner.r }, { q: 0, r: 1 });
  assert.equal(Math.max(
    Math.abs(inner.q - outer.q),
    Math.abs(inner.r - outer.r),
    Math.abs((-inner.q - inner.r) - (-outer.q - outer.r))
  ), 2);
});

test("blind Realignment ties resolve by the first Initiative-clockwise leading ballot", () => {
  const result = resolveBlindRealignmentVote(
    [
      { seat: 0, motionId: "core" },
      { seat: 1, motionId: "outer" },
      { seat: 2, motionId: "core" },
      { seat: 3, motionId: "outer" }
    ],
    1,
    ["core", "outer", "counter"]
  );
  assert.equal(result.winningMotionId, "outer");
  assert.equal(result.tied, true);
});

test("absent Realignment ballots leave the tied choice to Initiative", () => {
  const result = resolveBlindRealignmentVote(
    [
      { seat: 0, motionId: null },
      { seat: 1, motionId: null },
      { seat: 2, motionId: null }
    ],
    1,
    ["core", "outer", "counter"]
  );
  assert.equal(result.winningMotionId, undefined);
  assert.deepEqual(result.leadingMotionIds, ["core", "outer", "counter"]);
  assert.equal(result.tied, true);
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

test("browser game permits two through six players while recommending three through five", async () => {
  const [config, factions, headlines] = await load();
  assert.deepEqual(config.players.playableCounts, [2, 3, 4, 5, 6]);
  assert.deepEqual(config.players.supportedCounts, [3, 4, 5]);
  assert.deepEqual(config.players.historicalOnlyCounts, [2, 6]);
  for (const players of config.players.playableCounts) {
    assert.equal(
      createGame(config, factions, headlines, `playable-${players}`, "coalition_lab", players)
        .playerCount,
      players
    );
  }
  for (const players of [1, 7]) {
    assert.throws(
      () => createGame(
        config,
        factions,
        headlines,
        `out-of-range-${players}`,
        "coalition_lab",
        players
      ),
      /playerCount must be one of 2, 3, 4, 5, 6/
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
  assert.equal(state.phase, "move");
  assert.equal(state.selectedAction.id, "fund");
  assert.equal(state.selectedPieceId, null);
  assert.equal(state.selectedTileId, null);
  assert.ok(legalDestinations(state, "ceo").length > 1);
});

test("three different Core Actions advance exactly one era without early Realignment", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "round-contract", "coalition_lab");
  const frontier = state.board.find((tile) => tile.id === "frontier");
  for (const action of ["fund", "influence", "organize"]) {
    commitAction(state, action);
    resolveSelectedAction(config, headlines, state, "ceo", frontier.instanceId);
  }
  assert.equal(state.phase, "select");
  assert.equal(state.round, 2);
  assert.equal(state.cycle, 1);
  assert.deepEqual(state.player.actionsUsed, []);
  assert.equal(state.player.escalation, 1);
  assert.deepEqual(
    state.metrics.actionSelections.map((selection) => selection.actionId),
    ["fund", "influence", "organize"]
  );
  assert.equal(state.metrics.realignmentVotes.length, 0);
});

test("the first Facility is powered by the basic starting grid connection", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "starter-grid", "coalition_lab", 4);
  const buildTile = state.board.find((tile) => tile.category === "research");

  for (const action of ["build", "fund", "influence"]) {
    commitAction(state, action);
    resolveSelectedAction(config, headlines, state, "ceo", buildTile.instanceId, {
      buildMode: "facility"
    });
  }

  assert.equal(state.metrics.poweredFacilityRounds[0].powered, 1);
  assert.equal(state.metrics.poweredFacilityRounds[0].supply, 1);
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
  resolveSelectedAction(config, headlines, state, "ceo", consumer.instanceId);

  assert.equal(state.player.customers, 1);
  assert.ok(state.log.some((entry) => /Customer 2 needs Capability 4/.test(entry)));
});

test("Advanced Networks use the first Facility, visible adjacency, and bounded Links", async () => {
  const [config, factions, headlines] = await load();
  const state = createGame(config, factions, headlines, "network-contract", "coalition_lab");
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
  const connected = networkedFacilityIds(state.board, state.player);
  assert.ok(connected.has("first"));
  assert.ok(connected.has("remote"));
  if (Math.max(
    Math.abs(first.q - adjacent.q),
    Math.abs(first.r - adjacent.r),
    Math.abs((-first.q - first.r) - (-adjacent.q - adjacent.r))
  ) <= 1) assert.ok(connected.has("adjacent"));
  assert.equal(config.playerSupply.linkTokens, 2);
});

test("Default Game local Power ignores Links and does not propagate through Facilities", async () => {
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
  const local = networkedFacilityIds(state.board, state.player, {
    networkInfrastructureEnabled: false
  });
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
  resolveSelectedAction(config, headlines, state, "ceo", frontier.instanceId);
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
    [3, [2, 2, 1, 1]],
    [4, [2, 2, 1, 1]],
    [5, [2, 2, 1, 2]]
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
      `${playerCount}-player Peer Validation schedule`
    );
  }
});

test("Training studies replay exactly under the same seed", async () => {
  const [config] = await load();
  const first = simulateTrainingRun(config, "training-42", { stopAt: 4, runway: 5, safety: 1 });
  const second = simulateTrainingRun(config, "training-42", { stopAt: 4, runway: 5, safety: 1 });
  assert.deepEqual(first, second);
  assert.ok(["banked", "crashed", "protected", "human-evaluation", "licensed-stop", "stopped"].includes(first.outcome));
});
