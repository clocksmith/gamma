import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  createSimulation,
  factionRosterForRun
} from "../simulation/runtime/create-simulation.js";
import { loadPlayerProfiles, profileForPrompt } from "../simulation/personas/player-profile.js";
import {
  CliBackedPlayerPolicy,
  WeightedPlayerPolicy
} from "../simulation/policies/policy-factory.js";
import {
  mutateRulesVariant,
  mutateStrategy
} from "../simulation/runner/optimization-runner.js";
import { runExperiment } from "../simulation/runtime/run-experiment.js";
import { createInteractiveGame } from "../simulation/runtime/create-interactive-game.js";
import { archiveSimulationReport } from "../simulation/report-archive.js";
import {
  classifyReportComparison,
  normalizeSimulationReport
} from "../simulation/contracts/report-migrations.js";
import {
  fingerprintObject,
  loadGameIdentity,
  mechanicsProjection
} from "../simulation/versioning/game-identity.js";
import { declarationReadiness } from "../simulation/rules/declaration-readiness.js";
import {
  causallyNecessaryImportSuppliers
} from "../simulation/environment/selected-rules-match.js";
import { loadBalanceContract } from "../simulation/balance/balance-contract.js";
import { runBalanceAudit } from "../simulation/runner/balance-audit-runner.js";
import { runFactionSwapDiagnostic } from "../simulation/runner/faction-swap-runner.js";

test("player personas load as reusable provider-neutral strategy profiles", async () => {
  const profiles = await loadPlayerProfiles();
  assert.ok(profiles.length >= 4);
  assert.equal(new Set(profiles.map((profile) => profile.id)).size, profiles.length);
  const promptProfile = profileForPrompt(profiles[0]);
  assert.equal(promptProfile.id, profiles[0].id);
  assert.ok(promptProfile.persona.worldview.length > 0);
  assert.ok(promptProfile.objectives.length > 0);
});

test("Scientific Method charges only when its protection is actually consumed", async () => {
  const researchDecision = {
    decisionId: "fixture-research",
    label: "Fixture Research",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  };
  const createImperialMatch = async (suffix) => {
    const { match } = await createInteractiveGame(
      {
        playerCount: 3,
        factionId: "imperial_research_lab",
        seed: `scientific-method-${suffix}`
      },
      () => {}
    );
    return match;
  };

  const used = await createImperialMatch("used");
  used.resolveTrainingRun = () => ({
    capability: 0,
    trust: 0,
    runwaySpent: 0,
    safetySpent: 1,
    scrutiny: 0
  });
  used.applyResolution(0, researchDecision);
  assert.equal(used.players[0].runway, 2);
  assert.equal(used.players[0].roundMetrics.scientificMethodUsed, true);
  assert.equal(used.players[0].safety, 0);
  assert.deepEqual(
    used.players[0].metrics.factionAbilityValues.scientific_method,
    {
      uses: 1,
      runwaySpent: 1,
      duplicatesProtected: 1,
      capabilityPreserved: 0,
      capabilityPenalty: 0
    }
  );

  const unused = await createImperialMatch("unused");
  unused.resolveTrainingRun = () => ({
    capability: 1,
    trust: 0,
    runwaySpent: 0,
    safetySpent: 0,
    scrutiny: 0
  });
  unused.applyResolution(0, researchDecision);
  assert.equal(unused.players[0].runway, 3);
  assert.ok(!unused.players[0].roundMetrics.scientificMethodUsed);

  const ordinarySafety = await createImperialMatch("ordinary-safety");
  ordinarySafety.players[0].safety = 1;
  ordinarySafety.resolveTrainingRun = () => ({
    capability: 0,
    trust: 0,
    runwaySpent: 0,
    safetySpent: 1,
    scrutiny: 0
  });
  ordinarySafety.applyResolution(0, researchDecision);
  assert.equal(ordinarySafety.players[0].runway, 3);
  assert.ok(!ordinarySafety.players[0].roundMetrics.scientificMethodUsed);
  assert.equal(ordinarySafety.players[0].safety, 0);
});

test("joint Mega-Cluster acceptance is unavailable after a partner spends its contribution", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "mega-cluster-payment-revalidation"
    },
    () => {}
  );
  const lead = match.players[0];
  const partner = match.players[1];
  lead.runway = 2;
  lead.compute = 1;
  lead.escalation = 1;
  partner.runway = 1;
  partner.compute = 0;
  const frontier = match.board.find((tile) => tile.category === "frontier");
  const adjacent = match.board.find((tile) =>
    tile.instanceId !== frontier.instanceId &&
    match.areAdjacent(frontier.instanceId, tile.instanceId)
  );
  lead.facilities = [{
    id: "lead-facility",
    tileId: frontier.instanceId,
    category: "cloud",
    powered: true,
    gridReady: true,
    gridReadySupportSeats: []
  }];
  partner.facilities = [{
    id: "partner-facility",
    tileId: adjacent.instanceId,
    category: "cloud",
    powered: true,
    gridReady: true,
    gridReadySupportSeats: []
  }];
  const policies = match.players.map(() => ({
    async decide(packet) {
      return {
        decision: packet.legalDecisions[0],
        receipt: { provider: "fixture-policy" }
      };
    }
  }));
  await match.applyWild(policies, 0, "mega_cluster", {
    actionId: "mega_cluster",
    parameters: {
      partnerSeat: 1,
      leftId: "lead-facility",
      rightId: "partner-facility",
      pieceId: lead.pieces[0].id,
      destinationId: frontier.instanceId
    }
  });
  assert.equal(partner.compute, 0);
  assert.equal(partner.runway, 1);
  assert.equal(match.megaClusters.length, 0);
});

test("Foundry starting Compute is an explicit one-lever rules variant", async () => {
  const canonical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "foundry",
      seed: "foundry-compute-canonical"
    },
    () => {}
  );
  const probe = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "foundry",
      seed: "foundry-compute-probe",
      rulesVariant: { foundryStartingCompute: 3 }
    },
    () => {}
  );
  assert.equal(canonical.match.players[0].compute, 4);
  assert.equal(probe.match.players[0].compute, 3);
  assert.equal(
    canonical.match.rulesVariant.foundryShovelsPerRound,
    2
  );
  assert.equal(canonical.match.rulesVariant.foundryNewArchitectureCompute, 3);
  assert.equal(canonical.match.rulesVariant.foundryGpuRivalsPerMandate, 4);
});

test("late Capability Mandate is an explicit one-lever rules variant", async () => {
  const canonical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "late-capability-canonical"
    },
    () => {}
  );
  const probe = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "late-capability-probe",
      rulesVariant: { lateCapabilityThresholdMandate: 1 }
    },
    () => {}
  );
  for (const game of [canonical.match, probe.match]) {
    game.players[0].capability = 12;
    game.synchronizePublicMandate(game.players[0], "fixture");
  }
  assert.equal(canonical.match.players[0].mandate, 10);
  assert.equal(probe.match.players[0].mandate, 8);
  assert.deepEqual(
    probe.match.players[0].mandateAwards
      .filter((award) => award.id.startsWith("capability-"))
      .map((award) => [award.id, award.points]),
    [
      ["capability-3", 2],
      ["capability-6", 2],
      ["capability-9", 1],
      ["capability-12", 1]
    ]
  );
});

test("uniform Capability Mandate is an explicit one-lever rules variant", async () => {
  const probe = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "uniform-capability-probe",
      rulesVariant: { capabilityThresholdMandate: 1 }
    },
    () => {}
  );
  probe.match.players[0].capability = 12;
  probe.match.synchronizePublicMandate(probe.match.players[0], "fixture");
  assert.equal(probe.match.players[0].mandate, 6);
  assert.deepEqual(
    probe.match.players[0].mandateAwards
      .filter((award) => award.id.startsWith("capability-"))
      .map((award) => [award.id, award.points]),
    [
      ["capability-3", 1],
      ["capability-6", 1],
      ["capability-9", 1],
      ["capability-12", 1]
    ]
  );
});

test("Customer Mandate is an explicit one-lever rules variant", async () => {
  const probe = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "platform_empire",
      seed: "customer-mandate-probe",
      rulesVariant: { customerMandate: 1 }
    },
    () => {}
  );
  assert.equal(probe.match.players[0].customers, 1);
  assert.equal(
    probe.match.players[0].mandateAwards.find((award) => award.id === "customer-1").points,
    1
  );
  assert.equal(probe.match.players[0].mandate, 3);
});

test("faction starting Compute probes are isolated rules variants", async () => {
  const imperial = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "imperial-starting-compute-probe",
      rulesVariant: { imperialStartingCompute: 2 }
    },
    () => {}
  );
  const vertical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "vertical-starting-compute-probe",
      rulesVariant: { verticalStartingCompute: 4 }
    },
    () => {}
  );
  assert.equal(imperial.match.players[0].compute, 2);
  assert.equal(imperial.match.rulesVariant.verticalStartingCompute, null);
  assert.equal(vertical.match.players[0].compute, 4);
  assert.equal(vertical.match.rulesVariant.imperialStartingCompute, null);
});

test("faction mechanism probes remain isolated from canonical play", async () => {
  const coalition = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "coalition-starting-runway-probe",
      rulesVariant: { coalitionStartingRunway: 7 }
    },
    () => {}
  );
  const vertical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "vertical-industrial-velocity-probe",
      rulesVariant: {
        verticalIndustrialVelocityBuildModes: ["facility", "generator", "link"]
      }
    },
    () => {}
  );
  assert.equal(coalition.match.players[0].runway, 7);
  assert.deepEqual(
    coalition.match.rulesVariant.verticalIndustrialVelocityBuildModes,
    ["facility"]
  );
  assert.deepEqual(
    vertical.match.rulesVariant.verticalIndustrialVelocityBuildModes,
    ["facility", "generator", "link"]
  );
  assert.equal(vertical.match.rulesVariant.coalitionStartingRunway, null);
});

test("Scientific Method can be capped across the full game by a rules probe", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-lifetime-probe",
      rulesVariant: { imperialScientificMethodLifetimeLimit: 1 }
    },
    () => {}
  );
  const player = match.players[0];
  player.factionAbilityUsed.scientificMethodUses = 1;
  player.roundMetrics.scientificMethodUsed = false;
  match.resolveTrainingRun = () => ({
    capability: 0,
    trust: 0,
    runwaySpent: 0,
    safetySpent: 0,
    scrutiny: 1
  });
  const runwayBefore = player.runway;
  match.applyResolution(0, {
    decisionId: "fixture-research-lifetime",
    label: "Fixture Research",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  });
  assert.equal(player.runway, runwayBefore);
  assert.equal(player.factionAbilityUsed.scientificMethodUses, 1);
});

test("faction strength probes change only the targeted authored value", async () => {
  const imperial = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-price-probe",
      rulesVariant: {
        imperialScientificMethodRunwayCost: 2,
        imperialScientificMethodCapabilityPenalty: 1
      }
    },
    () => {}
  );
  const vertical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "industrial-velocity-strength-probe",
      rulesVariant: {
        verticalIndustrialVelocityDiscount: 2,
        verticalIndustrialVelocityMandate: 1
      }
    },
    () => {}
  );
  assert.equal(imperial.match.rulesVariant.imperialScientificMethodRunwayCost, 2);
  assert.equal(imperial.match.rulesVariant.imperialScientificMethodCapabilityPenalty, 1);
  assert.equal(imperial.match.rulesVariant.verticalIndustrialVelocityDiscount, 1);
  assert.equal(imperial.match.rulesVariant.verticalIndustrialVelocityMandate, 0);
  assert.equal(vertical.match.rulesVariant.verticalIndustrialVelocityDiscount, 2);
  assert.equal(vertical.match.rulesVariant.verticalIndustrialVelocityMandate, 1);
  assert.equal(vertical.match.rulesVariant.imperialScientificMethodRunwayCost, 1);
  assert.equal(vertical.match.rulesVariant.imperialScientificMethodCapabilityPenalty, 0);
});

test("faction progress probes alter only realized protected Research and discounted Build", async () => {
  const imperial = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-progress-probe",
      rulesVariant: { imperialScientificMethodCapabilityPenalty: 1 }
    },
    () => {}
  );
  const researcher = imperial.match.players[0];
  imperial.match.resolveTrainingRun = () => ({
    capability: 3,
    trust: 0,
    runwaySpent: 0,
    safetySpent: 1,
    scrutiny: 0
  });
  imperial.match.applyResolution(0, {
    decisionId: "fixture-scientific-progress",
    label: "Fixture protected Research",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  });
  assert.equal(researcher.capability, 2);
  assert.equal(researcher.lastTrainingResult.capability, 2);

  const vertical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "industrial-velocity-progress-probe",
      rulesVariant: { verticalIndustrialVelocityMandate: 1 }
    },
    () => {}
  );
  const builder = vertical.match.players[0];
  const build = vertical.match.legalResolutions(0, "build").find(
    (decision) => decision.parameters?.buildMode === "facility"
  );
  const mandateBefore = builder.mandate;
  vertical.match.applyResolution(0, build);
  assert.equal(builder.mandate, mandateBefore + 1);
  assert.equal(
    builder.metrics.factionAbilityValues.industrial_velocity.mandateGained,
    1
  );

  const zeroSavings = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "industrial-velocity-zero-savings-probe",
      rulesVariant: { verticalIndustrialVelocityMandate: 1 }
    },
    () => {}
  );
  const zeroSavingsBuilder = zeroSavings.match.players[0];
  const freeBuild = zeroSavings.match.legalResolutions(0, "build").find(
    (decision) => decision.parameters?.buildMode === "facility"
  );
  freeBuild.parameters.actualRunwayCost = 0;
  freeBuild.parameters.industrialVelocitySavings = 0;
  const zeroSavingsMandateBefore = zeroSavingsBuilder.mandate;
  zeroSavings.match.applyResolution(0, freeBuild);
  assert.equal(zeroSavingsBuilder.mandate, zeroSavingsMandateBefore);
  assert.equal(
    zeroSavingsBuilder.metrics.factionAbilityValues.industrial_velocity.mandateGained,
    0
  );
});

test("Foundry scaling probes expose one authored lever at a time", async () => {
  const architecture = await createInteractiveGame(
    {
      playerCount: 4,
      factionId: "foundry",
      seed: "foundry-architecture-probe",
      rulesVariant: { foundryNewArchitectureCompute: 2 }
    },
    () => {}
  );
  const gpu = await createInteractiveGame(
    {
      playerCount: 5,
      factionId: "foundry",
      seed: "foundry-gpu-probe",
      rulesVariant: { foundryGpuRivalsPerMandate: 2 }
    },
    () => {}
  );
  assert.equal(architecture.match.rulesVariant.foundryNewArchitectureCompute, 2);
  assert.equal(architecture.match.rulesVariant.foundryGpuRivalsPerMandate, 4);
  assert.equal(gpu.match.rulesVariant.foundryNewArchitectureCompute, 3);
  assert.equal(gpu.match.rulesVariant.foundryGpuRivalsPerMandate, 2);
});

test("Foundry Shovels observes two-Compute Wild Actions and respects its round cap", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "foundry-shovels-wild-action",
      rulesVariant: { foundryShovelsPerRound: 1 }
    },
    () => {}
  );
  const spender = match.players[0];
  const foundry = match.players[1];
  foundry.factionId = "foundry";
  foundry.metrics.shovelsIncome = 0;
  match.round = 2;
  match.cycle = 1;
  spender.runway = 3;
  spender.compute = 2;
  spender.escalation = 1;
  spender.selectedAction = "wild_mega_cluster";
  const frontier = match.board.find((tile) => tile.category === "frontier");
  const left = match.board.find((tile) =>
    tile.category !== "frontier" &&
    match.areAdjacent(frontier.instanceId, tile.instanceId)
  );
  const right = match.board.find((tile) =>
    tile.category !== "frontier" &&
    tile.instanceId !== left.instanceId &&
    match.areAdjacent(left.instanceId, tile.instanceId)
  );
  spender.facilities = [
    {
      id: "spender-left",
      tileId: left.instanceId,
      category: left.category,
      powered: true,
      gridReady: true,
      gridReadySupportSeats: []
    },
    {
      id: "spender-right",
      tileId: right.instanceId,
      category: right.category,
      powered: true,
      gridReady: true,
      gridReadySupportSeats: []
    }
  ];
  match.planImmediateTrade = async () => null;
  const policies = match.players.map(() => ({
    async decide(packet) {
      return {
        decision: packet.legalDecisions[0],
        receipt: { provider: "fixture-policy" }
      };
    }
  }));
  const runwayBefore = foundry.runway;

  await match.resolveSelectedSeat(policies, spender.seat);

  assert.equal(spender.compute, 0);
  assert.equal(foundry.runway, runwayBefore + 1);
  assert.equal(foundry.metrics.shovelsIncome, 1);
  assert.equal(
    foundry.metrics.factionAbilityValues.the_shovels.runwayGained,
    1
  );
  match.rewardFoundryComputeSpend(spender.seat, 2);
  assert.equal(foundry.runway, runwayBefore + 1);
  assert.equal(foundry.metrics.shovelsIncome, 1);
});

test("offline Facility penalties cannot reduce final Mandate below zero", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "offline-score-floor"
    },
    () => {}
  );
  const player = match.players[0];
  const tile = match.board.find((candidate) => candidate.category !== "frontier");
  player.mandate = 0;
  player.facilities = [{
    id: "offline-facility",
    tileId: tile.instanceId,
    category: tile.category,
    powered: false,
    gridReady: false,
    gridReadySupportSeats: []
  }];
  const standing = match.result().standings.find((entry) => entry.seat === 0);
  assert.equal(standing.offlinePenalty, 1);
  assert.equal(standing.score, 0);
});

test("Agent Swarm suppresses the second destination bonus before affordability", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "agent-swarm-second-action-payment"
    },
    () => {}
  );
  const player = match.players[0];
  const cloud = match.board.find((tile) => tile.category === "cloud");
  const research = match.legalResolutions(0, "research").find((decision) =>
    decision.parameters.destinationId === cloud.instanceId
  );
  player.compute = 0;
  const adjusted = match.suppressAgentSwarmDestinationBonus(player, research);
  assert.equal(research.parameters.actualComputeCost, 0);
  assert.equal(adjusted, null);
  assert.equal(player.compute, 0);
});

test("supplier attribution requires counterfactual Power necessity", () => {
  assert.deepEqual(causallyNecessaryImportSuppliers({
    localAvailable: 1,
    importedSupplierSeats: [1, 2],
    allocatedDemand: 3
  }), [1, 2]);
  assert.deepEqual(causallyNecessaryImportSuppliers({
    localAvailable: 2,
    importedSupplierSeats: [1, 2],
    allocatedDemand: 3
  }), []);
  assert.deepEqual(causallyNecessaryImportSuppliers({
    localAvailable: 3,
    importedSupplierSeats: [],
    allocatedDemand: 3
  }), []);
});

test("Talent production exposes Team movement through a decision packet", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "talent-production-choice" },
    () => {}
  );
  const player = match.players[0];
  const team = player.pieces.find((piece) => piece.kind === "team");
  const start = team.tileId;
  let captured;
  match.choose = async (_policies, seat, stage, decisions) => {
    captured = { seat, stage, decisions };
    return decisions.find((decision) => decision.parameters?.destinationId);
  };

  await match.produceFacility([], player, {
    id: "fixture-talent",
    category: "talent",
    tileId: start
  });

  assert.equal(captured.seat, 0);
  assert.equal(captured.stage, "facility_production_talent_movement");
  assert.ok(captured.decisions.some(
    (decision) => decision.decisionId === "facility_production_talent_stay"
  ));
  assert.ok(captured.decisions.every(
    (decision) =>
      !decision.parameters?.destinationId ||
      decision.parameters.destinationId !== start
  ));
  assert.notEqual(team.tileId, start);
});

test("Ownership Headline lets the affected player choose the producing Facility", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "ownership-facility-choice" },
    () => {}
  );
  match.round = 3;
  match.cycle = 1;
  const player = match.players[0];
  const cloud = match.board.find((tile) => tile.category === "cloud");
  const capital = match.board.find((tile) => tile.category === "capital");
  player.facilities = [
    {
      id: "cloud-fixture",
      tileId: cloud.instanceId,
      category: "cloud",
      powered: true,
      gridReady: true,
      gridReadySupportSeats: []
    },
    {
      id: "capital-fixture",
      tileId: capital.instanceId,
      category: "capital",
      powered: true,
      gridReady: true,
      gridReadySupportSeats: []
    }
  ];
  player.capability = 0;
  match.players[1].capability = 4;
  const headline = match.headlineDocument.headlines.find(
    (candidate) => candidate.id === "weights_on_internet"
  );
  match.headlineDecks[3][0] = headline;
  let captured;
  match.choose = async (_policies, seat, stage, decisions) => {
    if (stage === "weights_on_internet_facility") {
      captured = { seat, stage, decisions };
      return decisions.find(
        (decision) => decision.parameters.facilityId === "capital-fixture"
      );
    }
    return decisions[0];
  };
  const runwayBefore = player.runway;

  await match.prepareHeadline([]);

  assert.equal(captured.seat, 0);
  assert.equal(captured.decisions.length, 2);
  assert.equal(player.runway, runwayBefore + 2);
});

test("Build discounts remain optional and can make an otherwise unaffordable Build legal", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "optional-build-discount" },
    () => {}
  );
  const player = match.players[0];
  match.round = 2;
  player.runway = 1;
  player.buildDiscounts = 1;

  const decisions = match.legalResolutions(0, "build");
  const discounted = decisions.find((decision) =>
    decision.parameters.buildMode === "facility" &&
    decision.parameters.useBuildDiscount &&
    decision.parameters.actualRunwayCost === 1
  );
  const undiscounted = decisions.find((decision) =>
    decision.parameters.buildMode === "facility" &&
    !decision.parameters.useBuildDiscount
  );

  assert.ok(discounted, "the discount should expose a one-Runway Facility Build");
  assert.ok(undiscounted, "a naturally affordable destination should permit keeping it");

  const beforeFacilities = player.facilities.length;
  match.applyResolution(0, discounted);
  assert.equal(player.runway, 0);
  assert.equal(player.buildDiscounts, 0);
  assert.equal(player.facilities.length, beforeFacilities + 1);
});

test("Market Access is spent only when the player selects its Deploy variant", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "optional-market-access" },
    () => {}
  );
  const player = match.players[0];
  player.compute = 10;
  player.customers = 0;
  player.capability = 1;
  player.marketAccess = 1;

  const requiredDecisions = match.legalResolutions(0, "deploy");
  assert.ok(requiredDecisions.length > 0);
  assert.ok(requiredDecisions.every(
    (decision) => decision.parameters.useMarketAccess
  ));

  player.capability = 2;
  const optionalDecisions = match.legalResolutions(0, "deploy");
  const keep = optionalDecisions.find(
    (decision) => !decision.parameters.useMarketAccess
  );
  assert.ok(keep, "meeting the printed requirement should allow keeping the token");

  match.applyResolution(0, keep);
  assert.equal(player.marketAccess, 1);
  assert.equal(player.customers, 1);
});

test("trade generation uses the receiver's Safety cap", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "safety_laboratory",
      seed: "receiver-safety-cap"
    },
    () => {}
  );
  const safetyLab = match.players[0];
  const ordinaryInstitution = match.players[1];
  safetyLab.safety = 1;
  ordinaryInstitution.safety = match.config.resources.safety.cap;

  assert.ok(!match.tradableResources(
    safetyLab,
    ordinaryInstitution
  ).includes("safety"));
  assert.ok(match.tradableResources(
    ordinaryInstitution,
    safetyLab
  ).includes("safety"));
});

test("recruiting reuses the actual missing Team identity without duplicates", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "team-identity-reuse" },
    () => {}
  );
  const player = match.players[0];
  const frontier = match.board.find((tile) => tile.category === "frontier");
  player.pieces = [
    { id: "s0-ceo", kind: "ceo", tileId: frontier.instanceId },
    { id: "s0-team-1", kind: "team", tileId: frontier.instanceId },
    { id: "s0-team-3", kind: "team", tileId: frontier.instanceId }
  ];
  player.teamsInSupply = 1;

  match.applyResolution(0, {
    decisionId: "recruit-missing-team",
    label: "Recruit the missing Team",
    actionId: "organize",
    parameters: {
      mode: "recruit",
      count: 1,
      cost: 0,
      pieceId: "s0-ceo",
      destinationId: frontier.instanceId
    },
    consequences: { teams: 1 }
  });

  const teamIds = player.pieces
    .filter((piece) => piece.kind === "team")
    .map((piece) => piece.id);
  assert.deepEqual(teamIds.sort(), [
    "s0-team-1",
    "s0-team-2",
    "s0-team-3"
  ]);
  assert.equal(new Set(teamIds).size, teamIds.length);
  assert.equal(player.teamsInSupply, 0);
});

test("declaration readiness is pure, diagnostic, and UI-ready", async () => {
  const player = {
    seat: 0,
    agiDeclared: false,
    capability: 9,
    customers: 3,
    trust: 3,
    compute: 4,
    runway: 3,
    links: [],
    facilities: Array.from({ length: 3 }, (_, index) => ({
      id: `facility-${index + 1}`,
      tileId: `site-${index + 1}`,
      gridReady: true
    })),
    generators: [{
      id: "generator-1",
      tileId: "site-1",
      capacity: 99
    }]
  };
  const state = {
    players: [player],
    contracts: [],
    megaClusters: [],
    startingGridPower: 1,
    requirements: {
      capability: 9,
      customers: 3,
      facilities: 3,
      trust: 2,
      computeCost: 3
    }
  };
  const before = structuredClone(state);
  const readiness = declarationReadiness(state, player);
  assert.equal(readiness.ready, true);
  assert.equal(readiness.failingRequirement, null);
  assert.equal(readiness.gridReadyFacilities, 3);
  assert.equal(readiness.ppaIterations, 0);
  assert.equal(readiness.capacityOps, 3);
  assert.deepEqual(state, before);

  const unproven = structuredClone(player);
  unproven.facilities[2].gridReady = false;
  const capacityCannotSubstitute = declarationReadiness(state, unproven);
  assert.equal(capacityCannotSubstitute.ready, false);
  assert.equal(capacityCannotSubstitute.failingRequirement, "grid_ready_facilities");
  assert.equal(capacityCannotSubstitute.gridReadyFacilities, 2);

  const blocked = declarationReadiness(state, { ...player, capability: 8 });
  assert.equal(blocked.ready, false);
  assert.equal(blocked.failingRequirement, "capability");
});

test("Production earns Grid-Ready markers and infrastructure changes revoke them", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "grid-ready-lifecycle" },
    () => {}
  );
  match.round = 2;
  const player = match.players[0];
  player.capability = 9;
  player.customers = 3;
  player.trust = 3;
  player.compute = 4;
  const sites = match.board.filter((tile) => tile.category !== "frontier").slice(0, 3);
  player.facilities = sites.map((tile, index) => ({
    id: `s0-facility-${index + 1}`,
    tileId: tile.instanceId,
    category: tile.category,
    powered: false,
    gridReady: false
  }));
  player.links = player.facilities.slice(1).map((facility) => facility.id);
  player.generators = [{
    id: "s0-generator-1",
    tileId: sites[0].instanceId,
    sourceId: "clean_infrastructure",
    capacity: 2
  }];
  player.runway = 10;
  for (const rival of match.players.slice(1)) {
    rival.facilities = [];
    rival.generators = [];
  }

  const policies = match.players.map((candidate) => ({
    async decide(packet) {
      const decisions = packet.legalDecisions;
      const selected = [...decisions].sort((left, right) =>
        (right.consequences?.poweredFacilities || 0) -
          (left.consequences?.poweredFacilities || 0) ||
        (right.consequences?.power || 0) - (left.consequences?.power || 0)
      )[0];
      return {
        decision: {
          decisionId: selected.decisionId,
          rationale: "Maximize demonstrated operating capacity."
        },
        receipt: {
          provider: "test",
          profileId: candidate.profileId,
          requestId: packet.requestId
        }
      };
    }
  }));

  await match.produceAll(policies);
  assert.equal(player.facilities.filter((facility) => facility.gridReady).length, 3);
  assert.equal(match.declarationReadiness(player).gridReadyFacilities, 3);
  assert.ok(match.matchMetrics.agiFunnel[0].coreRequirementsMet);
  assert.ok(match.matchMetrics.agiFunnel[0].becameGridReady);
  assert.equal(match.matchMetrics.agiFunnel[0].neededExternalPower, null);

  match.round = 4;
  player.escalation = 2;
  player.actionsUsed = [];
  assert.ok(match.legalActionSelections(0).some(
    (decision) => decision.actionId === "declare_agi"
  ));
  assert.ok(match.matchMetrics.agiFunnel[0].legalDeclarationWindow);
  match.declareAgi(player);
  assert.ok(match.matchMetrics.agiFunnel[0].declared);

  const currentTile = match.board.find(
    (tile) => tile.instanceId === player.facilities[0].tileId
  );
  const destination = match.board.find(
    (tile) =>
      tile.instanceId !== currentTile.instanceId &&
      Math.max(
        Math.abs(tile.q - currentTile.q),
        Math.abs(tile.r - currentTile.r),
        Math.abs((-tile.q - tile.r) - (-currentTile.q - currentTile.r))
      ) === 1
  );
  match.applyResolution(0, {
    decisionId: "move-revokes-grid-ready",
    label: "Move the first Facility",
    actionId: "organize",
    parameters: {
      mode: "relocate",
      facilityId: player.facilities[0].id,
      pieceId: player.pieces[0].id,
      destinationId: player.facilities[0].tileId,
      destinationCategory: player.facilities[0].category,
      facilityDestinationId: destination.instanceId
    },
    consequences: { relocateFacility: true }
  });
  assert.equal(player.facilities[0].gridReady, false);
  assert.equal(match.declarationReadiness(player).gridReadyFacilities, 2);
});

test("all six unused Core Actions remain selectable before payment is known", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 4, seed: "six-core-actions" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const selections = runtime.match.legalActionSelections(0)
    .filter((decision) => !decision.decisionId.startsWith("select_wild_"));
  assert.deepEqual(
    selections.map((decision) => decision.actionId),
    ["fund", "research", "build", "organize", "deploy", "influence"]
  );
  assert.equal(
    selections.find((decision) => decision.actionId === "fund")
      .consequences.resolvableWithoutTrade,
    true
  );
  assert.equal(
    selections.find((decision) => decision.actionId === "deploy")
      .consequences.resolvableWithoutTrade,
    false
  );
});

test("deterministic policies preserve legal commitment while avoiding known dead actions", async () => {
  const profiles = await loadPlayerProfiles();
  const profile = profiles.find((candidate) => candidate.id === "capability_rusher");
  const policy = new WeightedPlayerPolicy(profile, { selection: "greedy" });
  const packet = {
    schemaVersion: 1,
    requestId: "known-dead-action",
    matchId: "match",
    seed: "known-dead-action",
    seat: 0,
    factionId: "imperial_research_lab",
    round: 1,
    cycle: 1,
    observation: { self: { compute: 0, canDeploy: false } },
    legalDecisions: [
      {
        decisionId: "select_research",
        label: "Select Research",
        actionId: "research",
        consequences: {
          stage: "action_selection",
          currentResolutionCount: 0,
          resolvableWithoutTrade: false
        }
      },
      {
        decisionId: "select_fund",
        label: "Select Fund",
        actionId: "fund",
        consequences: {
          stage: "action_selection",
          currentResolutionCount: 12,
          resolvableWithoutTrade: true
        }
      }
    ]
  };
  assert.equal((await policy.decide(packet)).decision.decisionId, "select_fund");
  assert.ok(
    policy.score(packet, packet.legalDecisions[0]) <
      policy.score(packet, packet.legalDecisions[1])
  );
});

test("ordinary successful Round I actions populate opening evidence exactly once", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 3, seed: "opening-evidence" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const player = runtime.match.players[0];
  const decision = runtime.match.legalResolutions(0, "fund")[0];
  runtime.match.applyResolution(0, decision);
  assert.deepEqual(player.metrics.openingActions, ["fund"]);
  assert.equal(player.metrics.actions.fund, 1);
});

test("mechanics fingerprints ignore edition vocabulary", () => {
  const named = {
    edition: "named",
    factions: [{
      id: "coalition_lab",
      roleId: "faction-1",
      name: "Sam Altman",
      motto: "Named wording",
      starts: { runway: 5 }
    }]
  };
  const institutional = {
    edition: "institutional",
    factions: [{
      id: "coalition_lab",
      roleId: "faction-1",
      name: "The Coalition Lab",
      motto: "Alias wording",
      starts: { runway: 5 }
    }]
  };
  assert.deepEqual(
    mechanicsProjection(named).factions,
    mechanicsProjection(institutional).factions
  );
});

test("four-player tournaments rotate through all six factions without duplicate seats", () => {
  const factions = ["a", "b", "c", "d", "e", "f"].map((id) => ({ id }));
  const appearances = new Set();
  const bySeat = Array.from({ length: 4 }, () => new Set());
  for (let run = 0; run < 24; run += 1) {
    const roster = factionRosterForRun(factions, 4, run);
    assert.equal(new Set(roster.map((faction) => faction.id)).size, 4);
    for (const [seat, faction] of roster.entries()) {
      appearances.add(faction.id);
      bySeat[seat].add(faction.id);
    }
  }
  assert.deepEqual([...appearances].sort(), ["a", "b", "c", "d", "e", "f"]);
  assert.ok(bySeat.every((ids) => ids.size === factions.length));
});

test("explicit faction rosters preserve paired diagnostic seats and identity", async () => {
  const factionIds = [
    "imperial_research_lab",
    "platform_empire",
    "safety_laboratory",
    "foundry"
  ];
  const report = await createSimulation({
    runs: 2,
    playerCount: 4,
    seed: "explicit-faction-roster",
    sampleReplays: 0,
    factionIds,
    rotateFactions: false,
    profileIds: [
      "capability_rusher",
      "balanced_operator",
      "trust_governor",
      "power_broker"
    ],
    backends: ["weighted"],
    includeObservations: true
  });
  assert.deepEqual(report.configuration.factionIds, factionIds);
  assert.deepEqual(
    report.observations[0].standings
      .sort((left, right) => left.seat - right.seat)
      .map((standing) => standing.factionId),
    factionIds
  );
  assert.match(report.experiment.configurationFingerprint, /^sha256:[a-f0-9]{64}$/);
});

test("paired faction diagnostics keep every non-focal input on common seeds", async () => {
  const report = await runFactionSwapDiagnostic({
    runsPerArm: 1,
    playerCount: 4,
    seed: "paired-faction-diagnostic",
    preRegistrationId: "paired-faction-diagnostic-test",
    mandateMode: "fixed",
    profileIds: [
      "capability_rusher",
      "balanced_operator",
      "trust_governor",
      "power_broker"
    ],
    backends: ["weighted", "weighted", "weighted", "weighted"],
    comparisons: [{
      id: "demis_vs_mark",
      focalSeat: 0,
      leftFactionIds: [
        "imperial_research_lab",
        "coalition_lab",
        "safety_laboratory",
        "foundry"
      ],
      rightFactionIds: [
        "platform_empire",
        "coalition_lab",
        "safety_laboratory",
        "foundry"
      ]
    }]
  });
  assert.equal(report.diagnosticKind, "paired_faction_swap");
  assert.equal(report.runs, 2);
  assert.equal(report.comparisons[0].paired.pairs, 1);
  assert.equal(report.balanceEvaluation.promotionGate.eligible, false);
  assert.match(report.preRegistration.fingerprint, /^sha256:[a-f0-9]{64}$/);
});

test("weighted policies replay deterministically from packet seed and persona", async () => {
  const [profile] = await loadPlayerProfiles();
  const policy = new WeightedPlayerPolicy(profile);
  const packet = {
    schemaVersion: 1,
    requestId: "policy-replay",
    matchId: "match",
    seed: "same-seed",
    seat: 0,
    factionId: "coalition_lab",
    round: 1,
    cycle: 1,
    observation: {
      self: {
        runway: 2,
        unpoweredFacilities: 1,
        canDeploy: false
      }
    },
    legalDecisions: [
      {
        decisionId: "fund_conservative_s0",
        label: "Fund",
        actionId: "fund"
      },
      {
        decisionId: "build_generator_clean_infrastructure_s0",
        label: "Build grid",
        actionId: "build"
      }
    ]
  };
  assert.deepEqual(await policy.decide(packet), await policy.decide(packet));
  assert.ok(
    policy.score(packet, packet.legalDecisions[1]) >
    policy.score(packet, packet.legalDecisions[0])
  );
});

test("CLI-backed personas pass natural-language identity through the shared packet", async () => {
  const [profile] = await loadPlayerProfiles();
  let received;
  const caller = {
    async decide(packet) {
      received = packet;
      return {
        decision: { decisionId: packet.legalDecisions[0].decisionId },
        receipt: { provider: "fixture-cli", requestId: packet.requestId }
      };
    }
  };
  const fallback = new WeightedPlayerPolicy(profile);
  const policy = new CliBackedPlayerPolicy(profile, caller, { fallback });
  const packet = {
    schemaVersion: 1,
    requestId: "persona-call",
    matchId: "match",
    seed: "seed",
    seat: 0,
    factionId: "coalition_lab",
    round: 1,
    cycle: 1,
    observation: { self: {} },
    legalDecisions: [{
      decisionId: "select_fund",
      label: "Select Fund",
      actionId: "fund"
    }]
  };
  await policy.decide(packet);
  assert.equal(received.strategy.id, profile.id);
  assert.equal(received.strategy.persona.identity, profile.persona.identity);
});

test("Monte Carlo pipeline is deterministic and carries sampled replays", async () => {
  const options = {
    runs: 2,
    playerCount: 4,
    seed: "simulation-contract",
    sampleReplays: 1,
    profileIds: [
      "balanced_operator",
      "capability_rusher",
      "infrastructure_compounder",
      "market_maximalist"
    ],
    backends: ["weighted"]
  };
  const first = await createSimulation(options);
  const second = await createSimulation(options);
  assert.deepEqual(first.seats, second.seats);
  assert.deepEqual(first.samples, second.samples);
  assert.equal(first.scope.id, "three-to-five-grid-ready-v1");
  assert.ok(first.scope.excluded.includes("the deferred Tactic module"));
  assert.equal(first.schemaVersion, 6);
  assert.equal(first.reportSchemaVersion, 6);
  assert.equal(first.replaySchemaVersion, 2);
  assert.equal(first.decisionSchemaVersion, 2);
  assert.equal(first.game.version, "0.8.4");
  assert.match(first.game.rulesetFingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.engine.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.strategies.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.experiment.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.equal(first.variant.kind, "canonical");
  assert.equal(first.rng.algorithm, "mulberry32");
  assert.ok(first.factions.length >= 4 && first.factions.length <= 6);
  assert.equal(first.profiles.length, 4);
  assert.match(first.balanceContract.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.ok(first.balanceEvaluation.checks.length >= 10);
  assert.ok(first.diagnostics.openingDiversity.observed > 0);
  assert.ok(first.diagnostics.winningPathDiversity.observed > 0);
  assert.ok(Array.isArray(first.profileMatchups));
  assert.equal(first.balanceEvaluation.promotionGate.eligible, false);
  assert.equal(first.seats[0].profileIds.length, 2);
  assert.equal(typeof first.diagnostics.factionWinShareRange, "number");
  assert.equal(typeof first.diagnostics.actionDiversity, "number");
  assert.equal(first.samples[0].replay.filter((event) =>
    event.type === "headline_revealed"
  ).length, 12);
  assert.equal(first.samples[0].replay[0].state.board.length, 13);
  assert.equal(first.samples[0].replay.filter((event) =>
    event.type === "realignment_resolved"
  ).length, 1);
  assert.equal(
    Object.values(first.matchMetrics.realignments).reduce((sum, count) => sum + count, 0),
    options.runs
  );
  assert.equal(
    first.matchMetrics.agiFunnel.playerOpportunities,
    options.runs * options.playerCount
  );
  assert.equal(typeof first.matchMetrics.agiFunnelRates.declared, "number");
  assert.equal(typeof first.matchMetrics.factionAbilityValues, "object");
  assert.equal(typeof first.matchMetrics.factionActionSelections, "object");
  assert.equal(first.samples[0].replay.at(-1).type, "round_settled");
  assert.equal(first.samples[0].replay.at(-1).round, 4);
});

test("Monte Carlo refuses metered providers without explicit authorization", async () => {
  await assert.rejects(
    () => createSimulation({
      runs: 1,
      playerCount: 3,
      profileIds: ["balanced_operator", "capability_rusher"],
      backends: ["claude", "weighted"]
    }),
    /explicit allowLlm/
  );
});

test("simulation rejects unsupported two- and six-player games", async () => {
  for (const playerCount of [2, 6]) {
    await assert.rejects(
      createSimulation({
        runs: 1,
        playerCount,
        sampleReplays: 0,
        seed: `unsupported-${playerCount}`
      }),
      /playerCount must be an integer from 3 to 5/
    );
  }
});

test("aggregate-only Monte Carlo runs do not require replay samples", async () => {
  const report = await createSimulation({
    runs: 2,
    playerCount: 3,
    seed: "aggregate-only",
    sampleReplays: 0,
    profileIds: ["balanced_operator", "capability_rusher"],
    backends: ["greedy"]
  });
  assert.equal(report.samples.length, 0);
  assert.equal(report.scope.id, "three-to-five-grid-ready-v1");
  assert.equal(report.seats.length, 3);
});

test("blocked Core Actions exhaust without corrupting state or winner resolution", async () => {
  const report = await createSimulation({
    runs: 8,
    playerCount: 4,
    seed: "blocked-actions-remain-finite",
    sampleReplays: 1
  });
  assert.ok(report.samples[0].winnerSeats.length > 0);
  for (const standing of report.samples[0].standings) {
    for (const key of ["score", "trust", "customers", "compute", "capability"]) {
      assert.ok(Number.isFinite(standing[key]), `${key} remains finite`);
    }
  }
});

test("strategy and rule mutations are deterministic, bounded, and do not edit source profiles", async () => {
  const [profile] = await loadPlayerProfiles();
  const before = structuredClone(profile);
  const first = mutateStrategy(profile, "mutation-contract");
  const second = mutateStrategy(profile, "mutation-contract");
  assert.deepEqual(first, second);
  assert.deepEqual(profile, before);
  assert.notDeepEqual(first.strategy.actionWeights, profile.strategy.actionWeights);

  const rules = mutateRulesVariant({}, "rule-contract", { mutations: 3 });
  assert.deepEqual(rules, mutateRulesVariant({}, "rule-contract", { mutations: 3 }));
  assert.ok(rules.changed.length >= 1);
});

test("strategy evolution and rule search return inspectable recommendations", async () => {
  const evolution = await runExperiment({
    mode: "strategy-evolution",
    targetProfileId: "balanced_operator",
    generations: 1,
    population: 2,
    runsPerSeat: 1,
    playerCount: 3,
    seed: "evolution-contract"
  });
  assert.equal(evolution.reportType, "strategy_evolution");
  assert.equal(evolution.history.length, 1);
  assert.equal(evolution.championProfile.id, "balanced_operator");

  const search = await runExperiment({
    mode: "rule-search",
    iterations: 2,
    runs: 1,
    playerCount: 3,
    seed: "rule-search-contract"
  });
  assert.equal(search.reportType, "rule_search");
  assert.equal(search.evaluations.length, 2);
  assert.ok(search.recommendation.variant);
  assert.match(search.scope.verdictBoundary, /never changed automatically/i);
});

test("completed simulation reports archive under the central studies directory", async () => {
  const projectRoot = await mkdtemp(join(tmpdir(), "frontier-archive-"));
  try {
    const report = {
      schemaVersion: 3,
      reportSchemaVersion: 3,
      reportType: "tournament",
      evidenceLabel: "simulation",
      evidenceType: "simulation",
      generatedAt: "2026-07-26T13:03:25.621Z",
      seed: "archive contract",
      runs: 100,
      playerCount: 4,
      game: {
        version: "0.1.0",
        rulesetFingerprint: `sha256:${"a".repeat(64)}`
      }
    };
    const archive = await archiveSimulationReport(report, {
      projectRoot,
      jobId: "job-123"
    });
    assert.match(
      archive.relativePath,
      /^studies\/simulation\/20260726T130325621Z-tournament-0-1-0-aaaaaaaaaaaa-archive-contract-100x4-job-123\.json$/
    );
    assert.deepEqual(
      JSON.parse(await readFile(join(projectRoot, archive.relativePath), "utf8")),
      report
    );
  } finally {
    await rm(projectRoot, { recursive: true, force: true });
  }
});

test("game identity fingerprints exact rules, engine, variants, and strategies", async () => {
  const profiles = await loadPlayerProfiles();
  const first = await loadGameIdentity({
    profiles: profiles.slice(0, 2),
    backends: ["weighted", "greedy"]
  });
  const second = await loadGameIdentity({
    profiles: profiles.slice(0, 2),
    backends: ["weighted", "greedy"]
  });
  assert.equal(first.game.version, "0.8.4");
  assert.ok(!Object.hasOwn(first.game.files, "docs/core-rules.md"));
  assert.equal(first.game.rulesetFingerprint, second.game.rulesetFingerprint);
  assert.equal(first.engine.fingerprint, second.engine.fingerprint);
  assert.equal(first.strategies.fingerprint, second.strategies.fingerprint);
  assert.notEqual(
    first.variant.fingerprint,
    fingerprintObject({ auditMultiplier: 0.8 })
  );
});

test("legacy reports migrate for viewing without gaining false attribution", () => {
  const legacy = {
    schemaVersion: 2,
    reportType: "tournament",
    evidenceLabel: "simulation",
    generatedAt: "2026-07-26T13:03:25.621Z",
    seed: "legacy",
    playerCount: 4,
    scope: { id: "selected-rules-v1" }
  };
  const before = structuredClone(legacy);
  const migrated = normalizeSimulationReport(legacy);
  assert.deepEqual(legacy, before);
  assert.equal(migrated.reportSchemaVersion, 6);
  assert.equal(migrated.game.version, "unknown");
  assert.equal(migrated.migration.attribution, "legacy_unattributed");
  assert.equal(
    classifyReportComparison(migrated, migrated).classification,
    "incompatible"
  );
});

test("balance audit covers every persona pair and never auto-promotes", async () => {
  const profiles = await loadPlayerProfiles();
  const contract = await loadBalanceContract();
  const report = await runBalanceAudit({
    runsPerMatchup: 1,
    generations: 1,
    population: 2,
    seed: "balance-audit-contract-test"
  });
  assert.equal(report.reportType, "balance_audit");
  assert.equal(report.league.coverage, 1);
  assert.equal(
    report.design.observedPairs,
    profiles.length * (profiles.length - 1) / 2
  );
  assert.equal(report.adversarial.profiles.length, profiles.length);
  assert.equal(report.balanceContract.id, contract.id);
  assert.equal(report.balanceEvaluation.promotionGate.eligible, false);
  assert.equal(report.balanceEvaluation.promotionGate.humanApproval, false);
});

test("report comparison separates exact, controlled-rules, and descriptive evidence", async () => {
  const baseline = await createSimulation({
    runs: 1,
    playerCount: 3,
    seed: "comparison-contract",
    sampleReplays: 0,
    profileIds: ["balanced_operator", "capability_rusher"],
    backends: ["weighted"]
  });
  assert.equal(
    classifyReportComparison(baseline, structuredClone(baseline)).classification,
    "exact"
  );

  const rulesCandidate = structuredClone(baseline);
  rulesCandidate.variant.fingerprint = `sha256:${"b".repeat(64)}`;
  assert.equal(
    classifyReportComparison(baseline, rulesCandidate).classification,
    "controlled_rules"
  );

  const mixed = structuredClone(rulesCandidate);
  mixed.seed = "another-seed";
  mixed.experiment.fingerprint = `sha256:${"d".repeat(64)}`;
  mixed.strategies.fingerprint = `sha256:${"c".repeat(64)}`;
  assert.equal(
    classifyReportComparison(baseline, mixed).classification,
    "descriptive_historical"
  );
});
