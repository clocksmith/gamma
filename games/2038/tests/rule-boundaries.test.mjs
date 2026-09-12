import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { deriveEraUnlocks } from "../tasks/content/era-unlocks.mjs";

const seed = "rule-audit-20260912";
const card = (type, kind = "special") => ({ id: type, type, kind });

async function fixture(options = {}) {
  const runtime = await createInteractiveGame({ playerCount: 4, seed,
    factionId: "platform_empire", ...options }, () => {});
  const { match } = runtime;
  await match.setup(runtime.policies);
  await match.beginRound([]);
  match.round = 4;
  match.choose = async (_policies, _seat, _stage, choices) =>
    choices.find(choice => choice.decisionId === "training_continue") ||
    choices.find(choice => choice.decisionId === "training_protect_scientific_method") ||
    choices[0];
  return match;
}

function host(player, tile) {
  player.facilities = [{ id: `s${player.seat}-facility-1`,
    tileId: tile.instanceId, category: tile.category }];
}

test("district discounts make each project affordable and determine the actual payment", async () => {
  for (const factionId of ["platform_empire", "vertical_empire"]) {
    for (const [category, runway, compute] of [["cloud", 3, 0], ["chip", 2, 1]]) {
      for (const projectId of ["mega_cluster", "fusion_demonstrator", "quantum"]) {
        const match = await fixture({ factionId }), player = match.players[0];
        host(player, match.board.find(tile => tile.category === category));
        Object.assign(player, { runway, compute, scrutiny: 0 });
        const plan = match.legalBuildResolutions(0).find(choice =>
          !choice.parameters.facility && choice.parameters.project?.id === projectId);
        assert.ok(plan, `${factionId}: ${projectId} at ${category}`);
        assert.equal(plan.parameters.actualRunwayCost, runway);
        assert.equal(plan.parameters.project.compute, compute);
        match.applyBuild(0, plan);
        assert.deepEqual([player.runway, player.compute, player.scrutiny], [0, 0, 1]);
      }
    }
  }
});

test("a combined Build applies the district discount once and the faction discount only to its Facility", async () => {
  for (const [factionId, industrial] of [["platform_empire", false], ["vertical_empire", true]]) {
    for (const [category, baseRunway, compute] of [["chip", 4, 1], ["cloud", 5, 0]]) {
      const match = await fixture({ factionId }), player = match.players[0];
      assert.equal(match.hasFactionAbility(player, "industrial_velocity"), industrial);
      const runway = baseRunway - Number(industrial);
      Object.assign(player, { runway, compute, facilities: [], scrutiny: 0 });
      const plan = match.legalBuildResolutions(0).find(choice => choice.parameters.facility &&
        choice.parameters.destinationCategory === category && choice.parameters.project?.id === "mega_cluster");
      assert.ok(plan);
      assert.equal(plan.parameters.actualRunwayCost, runway);
      assert.equal(plan.parameters.facilityCost + plan.parameters.project.runway, runway);
      match.applyBuild(0, plan);
      assert.deepEqual([player.runway, player.compute], [0, 0]);
      assert.equal(player.projects[0].hostId, player.facilities[0].id);
    }
  }
});

test("an exchange is legal before a blocked action and does not falsely promise to enable it", async () => {
  const match = await fixture(), player = match.players[0], partner = match.players[1];
  Object.assign(player, { selectedAction: "deploy", capability: 0, runway: 1, compute: 0 });
  Object.assign(partner, { runway: 0, compute: 1 });
  const choice = match.immediateTradeDecisions(0).find(choice => choice.parameters?.partnerSeat === 1);
  assert.ok(choice);
  assert.equal(choice.consequences.selectedActionCurrentlyResolvable, false);
  assert.equal(choice.consequences.selectedActionResolvableAfterTrade, false);
  assert.equal(choice.consequences.enablesSelectedAction, false);
  assert.match(choice.label, /remains blocked/);
  assert.equal(match.completeImmediateTrade(0, 1, choice.parameters), true);
  assert.deepEqual([player.runway, player.compute, partner.runway, partner.compute], [0, 1, 1, 0]);
  assert.equal(match.legalResolutions(0, "deploy").length, 0);
  const customers = player.customers;
  match.applyResolution(0, match.assignmentOnlyDecisions(player, "deploy")[0]);
  assert.equal(player.customers, customers);
  assert.ok(player.actionsUsed.includes("deploy"));
});

test("an exchange may leave a previously affordable Build blocked, while fixed-rate and cap limits remain enforced", async () => {
  const match = await fixture(), player = match.players[0], partner = match.players[1];
  Object.assign(player, { selectedAction: "build", runway: 1, compute: 0, facilities: [] });
  Object.assign(partner, { runway: 0, compute: 1 });
  const choice = match.immediateTradeDecisions(0).find(choice => choice.parameters?.partnerSeat === 1);
  assert.ok(choice);
  assert.equal(choice.consequences.selectedActionCurrentlyResolvable, true);
  assert.equal(choice.consequences.selectedActionResolvableAfterTrade, false);
  assert.equal(choice.consequences.enablesSelectedAction, false);
  assert.match(choice.label, /remains blocked/);
  const offer = choice.parameters;
  for (const change of [{ giveAmount: 2 }, { receiveAmount: 2 }, { giveAmount: 0 },
    { receiveResource: "runway" }, { giveResource: "trust" }, { timing: "after" }]) {
    assert.equal(match.canCompleteImmediateTrade(0, 1, { ...offer, ...change }), false);
  }
  assert.equal(match.canCompleteImmediateTrade(0, 0, { ...offer, partnerSeat: 0 }), false);
  partner.runway = match.factionResourceCap(partner, "runway");
  assert.equal(match.canCompleteImmediateTrade(0, 1, offer), false);
});

test("The Dead Remain on Shift pays excess Scrutiny before its Facility produces", async () => {
  const match = await fixture(), player = match.players[0];
  host(player, match.board.find(tile => tile.category === "capital"));
  Object.assign(player, { scrutiny: 10, runway: 0, trust: 3 });
  match.headlineDecks[4][match.cycle - 1] = match.headlineDocument.headlines.find(
    headline => headline.id === "agent_swarm_escapes_scope");
  match.choose = async (_policies, _seat, _stage, choices) =>
    choices.find(choice => choice.parameters?.facilityId) || choices[0];
  await match.prepareHeadline([]);
  assert.deepEqual([player.runway, player.trust, player.scrutiny], [2, 2, 10]);
});

test("overflow exhausts Runway, then Trust, without a pending settlement", async () => {
  const match = await fixture(), player = match.players[0];
  Object.assign(player, { scrutiny: 10, runway: 1, trust: 1 });
  match.addScrutiny(player, 4);
  assert.deepEqual([player.runway, player.trust, player.scrutiny], [0, 0, 10]);
  match.addResource(player, "runway", 2);
  assert.equal(player.runway, 2);
});

test("both Research paths settle Benchmark Leak before deciding whether Scientific Method is affordable", async () => {
  for (const mode of ["synchronous", "policy"]) {
    for (const [scrutiny, runway, protectedDuplicate, trust] of [
      [10, 1, false, 2], [9, 1, true, 3], [10, 2, true, 3]
    ]) {
      const match = await fixture({ factionId: "imperial_research_lab" });
      const player = match.players[0];
      Object.assign(player, { scrutiny, runway, trust: 3, capability: 0, compute: 1 });
      match.trainingDrawPile = [card("code", "domain"), card("benchmark_leak"), card("code", "domain")];
      match.trainingDiscard = [];
      const decision = match.legalResolutions(0, "research").find(choice => choice.parameters.destinationCategory === "cloud");
      decision.parameters.stopAt = 7;
      if (mode === "policy") await match.applyResolutionWithPolicies([], 0, decision);
      else match.applyResolution(0, decision);
      assert.equal(player.lastTrainingResult.protectedDuplicate, protectedDuplicate, `${mode}: ${scrutiny}/${runway}`);
      assert.equal(player.lastTrainingResult.protection, protectedDuplicate ? "scientific_method" : null);
      assert.equal(player.lastTrainingResult.runwaySpent, Number(protectedDuplicate));
      assert.deepEqual([player.runway, player.trust, player.scrutiny, player.capability],
        [0, trust, 10, protectedDuplicate ? 3 : 0]);
      assert.equal(match.runwayConversionContexts.length, 0);
    }
  }
});

test("a later Human Evaluation cannot retroactively fund a penalty or earn a transient Trust award", async () => {
  for (const mode of ["synchronous", "policy"]) {
    const match = await fixture(), player = match.players[0];
    const threshold = match.config.scoring.trustThresholds.find(threshold => threshold.value > 0).value;
    Object.assign(player, { scrutiny: 10, runway: 0, trust: threshold - 1, capability: 0,
      customers: 0, compute: 1, mandate: 0, mandateAwards: [] });
    match.synchronizePublicMandate(player, "fixture");
    match.trainingDrawPile = [card("benchmark_leak"), card("human_evaluation")];
    match.trainingDiscard = [];
    const decision = match.legalResolutions(0, "research").find(choice => choice.parameters.destinationCategory === "cloud");
    decision.parameters.stopAt = 7;
    if (mode === "policy") await match.applyResolutionWithPolicies([], 0, decision);
    else match.applyResolution(0, decision);
    assert.equal(player.trust, threshold - 1);
    assert.ok(!player.mandateAwards.some(award => award.id === `trust-${threshold}`), mode);
    assert.deepEqual(player.lastTrainingResult.permanentEffects,
      [{ type: "scrutiny", amount: 1 }, { type: "trust", amount: 1 }]);
  }
});

async function ventureYield(keepContract, relocate) {
  const match = await fixture();
  for (const player of match.players) Object.assign(player, { factionId: "platform_empire",
    runway: 0, compute: 0, customers: 0, facilities: [], generators: [], projects: [] });
  const leftTile = match.board.find(tile => tile.category === "cloud");
  const rightTile = match.board.find(tile => ["cloud", "research", "capital", "consumer", "chip"].includes(tile.category) &&
    match.areAdjacent(leftTile.instanceId, tile.instanceId));
  host(match.players[0], leftTile);
  host(match.players[1], rightTile);
  const proposal = match.legalResolutions(0, "influence").find(choice =>
    choice.parameters?.mode === "joint_venture" && choice.parameters.targetSeat === 1);
  assert.ok(proposal);
  assert.equal(await match.negotiate([], 0, proposal), true);
  if (relocate) {
    const relocation = match.legalResolutions(1, "organize").find(choice =>
      choice.parameters.mode === "relocate" && choice.parameters.facilityDestinationId === leftTile.instanceId);
    assert.ok(relocation);
    match.applyResolution(1, relocation);
    assert.equal(match.canFormPartnership(match.players[0], match.players[1]), false);
    assert.ok(!match.legalResolutions(0, "influence").some(choice =>
      choice.parameters?.mode === "joint_venture" && choice.parameters.targetSeat === 1));
  }
  if (!keepContract) match.contracts = [];
  await match.produceAll([]);
  assert.equal(match.contracts.length, Number(keepContract));
  return match.players[1].compute;
}

test("a Venture survives relocation as a contract but produces only between adjacent districts", async () => {
  assert.equal((await ventureYield(true, false)) - (await ventureYield(false, false)), 1);
  assert.equal((await ventureYield(true, true)) - (await ventureYield(false, true)), 0);
});

test("Era summaries move with project unlock data and do not mutate authored inputs", () => {
  const game = { rounds: [1, 2, 3, 4].map(number => ({ number, newThisEra: [] })) };
  const projects = [{ id: "fusion_demonstrator", unlockedRound: 3 }];
  const ref = "${content.projects.byId.fusion_demonstrator.name}";
  assert.deepEqual(deriveEraUnlocks(game, projects).rounds.map(round => round.newThisEra), [[], [], [ref], []]);
  projects[0].unlockedRound = 2;
  assert.deepEqual(deriveEraUnlocks(game, projects).rounds.map(round => round.newThisEra), [[], [ref], [], []]);
  assert.deepEqual(game.rounds.map(round => round.newThisEra), [[], [], [], []]);
});

test("compiled instructions agree with project unlocks, shared risk, and Fusion connections", async () => {
  const config = JSON.parse(await readFile(new URL("../dist/runtime/game-config.json", import.meta.url)));
  const projects = JSON.parse(await readFile(new URL("../dist/runtime/projects.json", import.meta.url)));
  for (const project of projects.projects) {
    for (const round of config.rounds) {
      assert.equal(round.newThisEra.includes(project.name), round.number === project.unlockedRound);
    }
  }
  assert.ok(config.actions.find(action => action.id === "build").turnContract.risk.includes(`${projects.constructionCost.scrutiny} Scrutiny`));
  assert.match(config.board.startingGridConnection.rule, /Generator or Fusion host/);
  assert.doesNotMatch(config.board.startingGridConnection.restrictions, /demand/);
});
