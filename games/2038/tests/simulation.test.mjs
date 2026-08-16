import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  captureSimulationLaunchIdentity,
  createSimulation,
  factionRosterForRun
} from "../lab/runtime/create-simulation.js";
import { loadPlayerProfiles, profileForPrompt } from "../lab/personas/player-profile.js";
import {
  CliBackedPlayerPolicy,
  WeightedPlayerPolicy
} from "../lab/policies/policy-factory.js";
import {
  mutateRulesVariant,
  mutateStrategy
} from "../lab/runner/optimization-runner.js";
import { runExperiment } from "../lab/runtime/run-experiment.js";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import {
  createBrowserInteractiveGame
} from "../lab/runtime/create-browser-interactive-game.js";
import { archiveSimulationReport } from "../lab/report-archive.js";
import {
  classifyReportComparison,
  normalizeSimulationReport
} from "../lab/contracts/report-migrations.js";
import {
  fingerprintObject,
  loadGameIdentity,
  mechanicsProjection
} from "../lab/versioning/game-identity.js";
import { buildDecisionPrompt } from "../lab/contracts/decision-contract.js";
import {
  causallyNecessaryImportSuppliers,
  immediateTradePacketCeiling
} from "../lab/environment/selected-rules-match.js";
import {
  legacyPrePromotionRulesOverlay
} from "../lab/environment/rules-variant.js";
import { loadBalanceContract } from "../lab/balance/balance-contract.js";
import { runBalanceAudit } from "../lab/runner/balance-audit-runner.js";
import {
  expandAgiDeclarationScenarioMatrix,
  expandCoalitionConversionMatrix,
  expandFactionIsolationMatrix,
  LlmConcurrencyBroker,
  runFactionSwapDiagnostic
} from "../lab/runner/faction-swap-runner.js";

function fixturePolicy(select = () => null) {
  return {
    async decide(packet) {
      const selected = select(packet) || packet.legalDecisions[0];
      return {
        decision: {
          decisionId: selected.decisionId,
          rationale: "Deterministic fixture policy."
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

test("player personas load as reusable provider-neutral strategy profiles", async () => {
  const profiles = await loadPlayerProfiles();
  assert.ok(profiles.length >= 4);
  assert.equal(new Set(profiles.map((profile) => profile.id)).size, profiles.length);
  const promptProfile = profileForPrompt(profiles[0]);
  assert.equal(promptProfile.id, profiles[0].id);
  assert.ok(promptProfile.persona.worldview.length > 0);
  assert.ok(promptProfile.objectives.length > 0);
  assert.ok(promptProfile.resourceValues.compute > 0);
});

test("World Ending crosses AGI emergence with both Open-continuity gates", async () => {
  const endingFor = async ({
    emerges,
    trustDeltaPerPlayer = 1,
    systemicRisk = 0
  }) => {
    const { match } = await createInteractiveGame(
      {
        playerCount: 3,
        factionId: "coalition_lab",
        seed: `world-ending-${emerges}-${trustDeltaPerPlayer}-${systemicRisk}`
      },
      () => {}
    );
    for (const player of match.players) {
      const faction = match.factions.find((entry) => entry.id === player.factionId);
      player.trust = faction.starts.trust + trustDeltaPerPlayer;
    }
    match.systemicRisk = systemicRisk;
    if (emerges) {
      match.players[0].agiDeclared = true;
    }
    return match.result().worldEnding;
  };

  assert.deepEqual(await endingFor({ emerges: true }), {
    id: "singularity",
    name: "The Singularity",
    agiEmerges: true,
    openContinuity: true,
    qualifyingDeclarers: 1,
    collectiveTrust: 11,
    requiredCollectiveTrust: 11,
    unresolvedSystemicRisk: 0,
    systemicRiskExclusiveCeiling: 3
  });
  assert.equal((await endingFor({
    emerges: true,
    trustDeltaPerPlayer: 0
  })).id, "closed_loop");
  assert.equal((await endingFor({
    emerges: false,
    systemicRisk: 2
  })).id, "plural_future");
  assert.equal((await endingFor({
    emerges: false,
    systemicRisk: 3
  })).id, "assured_continuity");
});

test("interactive snapshots expose canonical Headline copy and the selected play profile", async () => {
  const options = {
    playerCount: 3,
    factionId: "coalition_lab",
    seed: "browser-headline-copy-contract"
  };
  const { match: defaultMatch } = await createInteractiveGame(options, () => {});
  const headline = defaultMatch.headlineDocument.headlines[0];
  defaultMatch.activeHeadline = headline;
  const defaultSnapshot = defaultMatch.snapshot();

  assert.equal(defaultSnapshot.playProfileId, "default-game");
  assert.deepEqual(defaultSnapshot.activeHeadline, {
    id: headline.id,
    name: headline.name,
    strapline: headline.strapline,
    newswire: headline.newswire,
    text: headline.text,
    quote: headline.quote
  });

  const { match: advancedMatch } = await createInteractiveGame({
    ...options,
    rulesVariant: { playProfileId: "advanced-play" }
  }, () => {});
  assert.equal(advancedMatch.snapshot().playProfileId, "advanced-play");
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
  used.players[0].researchProtection = 0;
  used.resolveTrainingRun = () => ({
    capability: 0,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 1,
    scrutiny: 0
  });
  used.applyResolution(0, researchDecision);
  assert.equal(used.players[0].runway, 2);
  assert.equal(used.players[0].roundMetrics.scientificMethodUsed, true);
  assert.equal(used.players[0].researchProtection, 0);
  assert.deepEqual(
    used.players[0].metrics.factionAbilityValues.scientific_method,
    {
      uses: 1,
      runwaySpent: 1,
      duplicatesProtected: 1,
      capabilityPreserved: 0,
      capabilityPenalty: 0,
      thresholdMandateWithheld: 0,
      scrutinyAdded: 0
    }
  );

  const unused = await createImperialMatch("unused");
  unused.resolveTrainingRun = () => ({
    capability: 1,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 0,
    scrutiny: 0
  });
  unused.applyResolution(0, researchDecision);
  assert.equal(unused.players[0].runway, 3);
  assert.ok(!unused.players[0].roundMetrics.scientificMethodUsed);

  const ordinaryProtection = await createImperialMatch("ordinary-protection");
  ordinaryProtection.players[0].researchProtection = 1;
  ordinaryProtection.resolveTrainingRun = () => ({
    capability: 0,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 1,
    scrutiny: 0
  });
  ordinaryProtection.applyResolution(0, researchDecision);
  assert.equal(ordinaryProtection.players[0].runway, 3);
  assert.ok(!ordinaryProtection.players[0].roundMetrics.scientificMethodUsed);
  assert.equal(ordinaryProtection.players[0].researchProtection, 0);
});

test("legal-decision adjustments do not mutate their generated decision", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "decision-adjustment-immutability"
    },
    () => {}
  );
  const decision = {
    decisionId: "fixture-fund",
    label: "Fixture Fund",
    actionId: "fund",
    parameters: {
      destinationCategory: "capital",
      mode: "conservative"
    },
    consequences: { runway: 2 }
  };
  const original = structuredClone(decision);
  const adjusted = match.adjustDecision(match.players[0], decision);

  assert.deepEqual(decision, original);
  assert.notStrictEqual(adjusted, decision);
  assert.notStrictEqual(adjusted.parameters, decision.parameters);
  assert.equal(adjusted.parameters.actualRunway, 3);
});

test("Scientific Method scrutiny taxes validation without reducing Capability", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-scrutiny-probe",
      rulesVariant: { imperialScientificMethodScrutiny: 2 }
    },
    () => {}
  );
  const researcher = match.players[0];
  researcher.researchProtection = 0;
  match.resolveTrainingRun = () => ({
    capability: 3,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 1,
    scrutiny: 0
  });
  match.applyResolution(0, {
    decisionId: "fixture-scientific-method-scrutiny",
    label: "Fixture Research saved by Scientific Method",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  });
  assert.equal(researcher.capability, 3);
  assert.equal(researcher.scrutiny, 2);
  assert.equal(
    researcher.metrics.factionAbilityValues.scientific_method.scrutinyAdded,
    2
  );
});

test("Mirevanta late validation changes Mandate without changing Capability", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "demis-late-public-validation"
    },
    () => {}
  );
  const researcher = match.players[0];
  const mandateBefore = researcher.mandate;
  match.addResource(researcher, "capability", 9);
  assert.equal(researcher.capability, 9);
  assert.equal(researcher.mandate - mandateBefore, 5);
  assert.deepEqual(
    researcher.metrics.factionAbilityValues.late_public_validation,
    {
      uses: 1,
      mandateWithheld: 1,
      thresholdsValidated: 1
    }
  );
});

test("four rival institutions restore Mirevanta's final validation point", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 5,
      factionId: "imperial_research_lab",
      seed: "demis-peer-validated-capability"
    },
    () => {}
  );
  const researcher = match.players[0];
  const mandateBefore = researcher.mandate;
  match.addResource(researcher, "capability", 12);
  assert.equal(researcher.capability, 12);
  assert.equal(researcher.mandate - mandateBefore, 7);
  assert.deepEqual(
    researcher.metrics.factionAbilityValues.late_public_validation,
    {
      uses: 1,
      mandateWithheld: 1,
      thresholdsValidated: 1
    }
  );
});

test("Mirevanta Peer Validation remains reduced at four players", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 4,
      factionId: "imperial_research_lab",
      seed: "demis-four-player-peer-validation"
    },
    () => {}
  );
  const researcher = match.players[0];
  const mandateBefore = researcher.mandate;
  match.addResource(researcher, "capability", 12);
  assert.equal(researcher.capability, 12);
  assert.equal(researcher.mandate - mandateBefore, 6);
  assert.deepEqual(
    researcher.mandateAwards
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

test("Safety Laboratory programs publish realized ability value", async () => {
  const emergency = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "safety_laboratory",
      seed: "safety-emergency-pause-telemetry"
    },
    () => {}
  );
  emergency.match.round = 4;
  emergency.match.regime.cycle = {};
  const safety = emergency.match.players[0];
  const trustBeforePause = safety.trust;
  const pausePolicies = emergency.match.players.map(() => fixturePolicy(
    (packet) => packet.legalDecisions.find(
      (decision) => decision.parameters?.escalationId === "fusion_demonstrator"
    )
  ));
  await emergency.match.resolveFactionAction(
    pausePolicies,
    0,
    "emergency_pause"
  );
  assert.deepEqual(
    safety.metrics.factionAbilityValues.emergency_pause,
    {
      uses: 1,
      runwaySpent: 1,
      trustGained: safety.trust - trustBeforePause,
      escalationsBlocked: 1
    }
  );

  const audited = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "safety_laboratory",
      seed: "safety-audited-deployment-telemetry"
    },
    () => {}
  );
  audited.match.round = 3;
  const deployer = audited.match.players[0];
  deployer.compute = 5;
  deployer.capability = 2;
  deployer.scrutiny = 2;
  const deploy = audited.match.legalResolutions(0, "deploy")[0];
  assert.ok(deploy, "the fixture should expose a legal Deploy");
  audited.match.applyResolution(0, deploy);
  assert.deepEqual(
    deployer.metrics.factionAbilityValues.audited_deployment,
    {
      uses: 1,
      scrutinyRemoved: 1,
      deploymentsCovered: 1
    }
  );

});

test("Mega-Cluster construction rejects another player's Facility", async () => {
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
  lead.programUses = 1;
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
    powered: true
  }];
  partner.facilities = [{
    id: "partner-facility",
    tileId: adjacent.instanceId,
    category: "cloud",
    powered: true
  }];
  const policies = match.players.map(() => ({
    async decide(packet) {
      return {
        decision: packet.legalDecisions[0],
        receipt: { provider: "fixture-policy" }
      };
    }
  }));
  await match.applyEscalation(policies, 0, "mega_cluster", {
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

test("a stale Mega-Cluster selection cannot reuse a claimed solo host", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "mega-cluster-host-contention" },
    () => {}
  );
  match.round = 2;
  const lead = match.players[0];
  lead.runway = 3;
  lead.compute = 2;
  lead.programUses = 1;
  const frontier = match.board.find((tile) => tile.category === "frontier");
  const adjacent = match.board.find((tile) =>
    tile.instanceId !== frontier.instanceId &&
    match.areAdjacent(frontier.instanceId, tile.instanceId)
  );
  lead.facilities = [
    {
      id: "contention-lead-host",
      tileId: frontier.instanceId,
      category: frontier.category,
      powered: false
    },
    {
      id: "contention-second-host",
      tileId: adjacent.instanceId,
      category: adjacent.category,
      powered: false
    }
  ];
  lead.generators = [{
    id: "contention-generator",
    tileId: frontier.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 3
  }];
  const decision = {
    actionId: "mega_cluster",
    parameters: {
      leftId: "contention-lead-host",
      rightId: "contention-second-host",
      pieceId: lead.pieces[0].id,
      destinationId: frontier.instanceId
    }
  };
  assert.equal(
    match.megaClusterDecisionLocallyEligible(lead.seat, decision.parameters),
    true
  );
  match.megaClusters.push({
    id: "mega-earlier",
    leadSeat: 2,
    leftId: "earlier-other-host",
    rightId: "contention-second-host",
    powered: false
  });

  await match.applyEscalation([], lead.seat, "mega_cluster", decision);

  assert.equal(match.megaClusters.length, 1);
  assert.equal(match.megaClusterHostsAvailable(["contention-second-host"]), false);
  assert.equal(lead.runway, 3);
  assert.equal(lead.compute, 2);
  assert.equal(lead.programUses, 1);
  assert.ok(!lead.escalationsUsed.includes("mega_cluster"));
});

test("shared contract supplies cap construction and Joint Venture termination requires Facility presence", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "shared-contract-supply" },
    () => {}
  );
  match.round = 3;
  const player = match.players[0];
  const partner = match.players[1];
  match.contracts = Array.from(
    { length: match.config.sharedSupply.jointVenturePairs },
    (_, index) => ({
      id: index + 1,
      kind: "joint_venture",
      left: { seat: 0, facilityId: `left-${index}` },
      right: { seat: 1, facilityId: `right-${index}` }
    })
  );
  player.jointVentures = match.contracts.map((contract) => ({ contractId: contract.id }));
  partner.jointVentures = match.contracts.map((contract) => ({ contractId: contract.id }));
  player.facilities = [{
    id: "political-host",
    tileId: player.pieces[0].tileId,
    category: "frontier",
    powered: true
  }];

  const legal = match.legalResolutions(0, "influence");
  assert.equal(match.jointVentureSupplyAvailable(), false);
  assert.equal(legal.some((decision) => decision.parameters?.mode === "joint_venture"), false);
  const termination = legal.find((decision) =>
    decision.parameters?.mode === "terminate_joint_venture" &&
    decision.parameters.contractId === 1
  );
  assert.ok(termination);
  match.applyResolution(0, termination);
  assert.equal(match.contracts.length, match.config.sharedSupply.jointVenturePairs - 1);
  assert.equal(player.jointVentures.some((venture) => venture.contractId === 1), false);
  assert.equal(partner.jointVentures.some((venture) => venture.contractId === 1), false);

  player.programUses = 1;
  match.megaClusters = Array.from(
    { length: match.config.sharedSupply.megaClusterPairs },
    (_, index) => ({ id: `mega-${index + 1}` })
  );
  assert.deepEqual(match.legalEscalationResolutions(0, "mega_cluster"), []);
  await match.applyEscalation([], 0, "mega_cluster", { parameters: {} });
  assert.equal(player.programUses, 1);
  assert.deepEqual(player.escalationsUsed, []);
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
  assert.ok(canonical.match.players[0].metrics.mandateEvents.some((event) =>
    event.source === "trust-2" && event.points === 2
  ));
  assert.equal(
    canonical.match.rulesVariant.foundryShovelsPerRound,
    2
  );
});

test("Safety study variants derive setup Mandate from Trust and can pause Emergency Pause", async () => {
  const game = await createInteractiveGame({
    playerCount: 3,
    factionId: "safety_laboratory",
    seed: "safety-study-variants",
    rulesVariant: {
      safetyStartingTrust: 3,
      safetyEmergencyPauseEnabled: false
    }
  }, () => {});
  const safety = game.match.players[0];
  assert.equal(safety.trust, 3);
  assert.equal(safety.mandate, 2, "setup Mandate follows the Trust threshold");
  game.match.round = 4;
  safety.runway = 3;
  assert.equal(game.match.rulesVariant.safetyEmergencyPauseEnabled, false);
  assert.equal(game.match.isEmergencyPauseEnabled(safety), false);
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

test("canonical Customer recognition diminishes only for the fourth and fifth Customer", async () => {
  const canonical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "platform_empire",
      seed: "customer-mandate-schedule-canonical"
    },
    () => {}
  );
  canonical.match.players[0].customers = 5;
  canonical.match.synchronizePublicMandate(
    canonical.match.players[0],
    "fixture"
  );
  assert.deepEqual(
    canonical.match.players[0].mandateAwards
      .filter((award) => award.id.startsWith("customer-"))
      .map((award) => [award.id, award.points]),
    [
      ["customer-1", 2],
      ["customer-2", 2],
      ["customer-3", 2],
      ["customer-4", 1],
      ["customer-5", 1]
    ]
  );

  const legacy = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "platform_empire",
      seed: "customer-mandate-schedule-legacy",
      rulesVariant: legacyPrePromotionRulesOverlay
    },
    () => {}
  );
  legacy.match.players[0].customers = 5;
  legacy.match.synchronizePublicMandate(legacy.match.players[0], "fixture");
  assert.deepEqual(
    legacy.match.players[0].mandateAwards
      .filter((award) => award.id.startsWith("customer-"))
      .map((award) => [award.id, award.points]),
    [
      ["customer-1", 2],
      ["customer-2", 2],
      ["customer-3", 2],
      ["customer-4", 2],
      ["customer-5", 2]
    ]
  );
  assert.equal(canonical.match.players[0].customers, 5);
  assert.equal(canonical.match.players[0].runway, 4);
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
    researchProtectionSpent: 0,
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
  assert.equal(imperial.match.rulesVariant.verticalIndustrialVelocityMandate, 1);
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
  researcher.researchProtection = 0;
  imperial.match.resolveTrainingRun = () => ({
    capability: 3,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 1,
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

  const publicValidation = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-public-validation-probe",
      rulesVariant: {
        imperialScientificMethodThresholdMandatePenalty: 1
      }
    },
    () => {}
  );
  const validatedResearcher = publicValidation.match.players[0];
  validatedResearcher.capability = 2;
  validatedResearcher.researchProtection = 0;
  const mandateBeforeValidation = validatedResearcher.mandate;
  publicValidation.match.resolveTrainingRun = () => ({
    capability: 1,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 1,
    scrutiny: 0
  });
  publicValidation.match.applyResolution(0, {
    decisionId: "fixture-scientific-public-validation",
    label: "Fixture protected Research crossing a threshold",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  });
  assert.equal(validatedResearcher.capability, 3);
  assert.equal(validatedResearcher.lastTrainingResult.capability, 1);
  assert.equal(validatedResearcher.mandate, mandateBeforeValidation + 1);
  assert.equal(
    validatedResearcher.metrics.factionAbilityValues.scientific_method
      .thresholdMandateWithheld,
    1
  );

  const unprotectedValidation = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "imperial_research_lab",
      seed: "scientific-method-public-validation-unused",
      rulesVariant: {
        imperialScientificMethodThresholdMandatePenalty: 1
      }
    },
    () => {}
  );
  const ordinaryResearcher = unprotectedValidation.match.players[0];
  ordinaryResearcher.capability = 2;
  const ordinaryMandateBefore = ordinaryResearcher.mandate;
  unprotectedValidation.match.resolveTrainingRun = () => ({
    capability: 1,
    trust: 0,
    runwaySpent: 0,
    researchProtectionSpent: 0,
    scrutiny: 0
  });
  unprotectedValidation.match.applyResolution(0, {
    decisionId: "fixture-scientific-public-validation-unused",
    label: "Fixture Research crossing a threshold without protection",
    actionId: "research",
    parameters: {
      destinationCategory: "cloud",
      destinationId: "frontier",
      pieceId: "s0-ceo",
      stopAt: 3
    }
  });
  assert.equal(ordinaryResearcher.capability, 3);
  assert.equal(ordinaryResearcher.mandate, ordinaryMandateBefore + 2);
  assert.ok(
    !ordinaryResearcher.metrics.factionAbilityValues.scientific_method
  );

  const vertical = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "vertical_empire",
      seed: "industrial-velocity-progress-probe",
      rulesVariant: {}
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
      rulesVariant: {}
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

test("the legacy pre-promotion overlay reproduces retained historical defaults", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 4,
      factionId: "foundry",
      seed: "legacy-pre-promotion-defaults",
      rulesVariant: legacyPrePromotionRulesOverlay
    },
    () => {}
  );
  assert.equal(match.rulesVariant.customerMandateSchedule, null);
  assert.equal(match.rulesVariant.imperialLateCapabilityThresholdMandate, null);
  assert.equal(match.rulesVariant.verticalIndustrialVelocityMandate, 0);
});

test("Foundry Shovels observes two-Compute Programs and respects its round cap", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "foundry",
      seed: "foundry-shovels-escalation",
      rulesVariant: { foundryShovelsPerRound: 1 }
    },
    () => {}
  );
  const foundry = match.players[0];
  const spender = match.players[1];
  foundry.metrics.shovelsIncome = 0;
  match.round = 2;
  match.cycle = 1;
  spender.runway = 3;
  spender.compute = 2;
  spender.programUses = 1;
  spender.selectedAction = "escalation_mega_cluster";
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
      powered: true
    },
    {
      id: "spender-right",
      tileId: right.instanceId,
      category: right.category,
      powered: true
    }
  ];
  spender.generators = [{
    id: "spender-generator",
    tileId: left.instanceId,
    sourceId: "clean_infrastructure",
    capacity: 2
  }];
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

test("Allocation Window uses its authored positive-price contract and one lower counteroffer", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "foundry",
      seed: "allocation-window-contract"
    },
    () => {}
  );
  const foundry = match.players[0];
  const buyer = match.players[1];
  const observed = [];
  match.round = 2;
  buyer.runway = 3;
  const runwayBefore = foundry.runway;
  const computeBefore = buyer.compute;
  const stageOf = (packet) => packet.requestId.split(":").at(-2);
  const policies = match.players.map(() => ({
    async decide(packet) {
      observed.push(packet);
      const stage = stageOf(packet);
      const selected = stage === "allocation_window_timing"
        ? packet.legalDecisions.find((decision) => decision.decisionId === "allocation_open")
        : stage === "allocation_window_0"
          ? packet.legalDecisions.find((decision) =>
            decision.decisionId === `allocation_offer_0_${buyer.seat}_3`
          )
          : stage === "allocation_response_0"
            ? packet.legalDecisions.find((decision) =>
              decision.decisionId === "allocation_counter_0_2"
            )
            : stage === "allocation_counterparty_0"
              ? packet.legalDecisions.find((decision) =>
                decision.decisionId === "allocation_counter_accept_0"
              )
              : packet.legalDecisions.find((decision) =>
                decision.decisionId === "allocation_hold_1"
              ) || packet.legalDecisions[0];
      return {
        decision: selected,
        receipt: { provider: "fixture-policy", requestId: packet.requestId }
      };
    }
  }));

  await match.preSelectionFactionPowers(policies);

  const offer = observed.find((packet) => stageOf(packet) === "allocation_window_0");
  const response = observed.find((packet) => stageOf(packet) === "allocation_response_0");
  assert.deepEqual(match.config.factionRules.foundry.allocationWindow, {
    temporaryCompute: 2,
    paymentResource: "runway",
    minimumPrice: 1
  });
  assert.ok(offer.legalDecisions.every((decision) =>
    !decision.decisionId.startsWith(`allocation_offer_0_${buyer.seat}_0`)
  ));
  assert.ok(response.legalDecisions.every((decision) =>
    decision.decisionId !== "allocation_counter_0_0"
  ));
  assert.equal(buyer.runway, 1);
  assert.equal(buyer.compute, computeBefore + 1);
  assert.equal(foundry.runway, runwayBefore + 2);
  assert.equal(
    foundry.metrics.factionAbilityValues.allocation_window.paymentReceived,
    2
  );
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
    powered: false
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

test("LLM decision packets expose the public table without simulation-only state", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "private-visibility-contract" },
    () => {}
  );
  for (let index = 0; index < 9; index += 1) {
    match.recordEvent("headline_revealed", null, `Public event ${index}.`);
  }
  match.recordEvent("strategy_decision", 1, "A concealed simultaneous choice.");
  const packet = match.packet(0, "visibility_inspection", [{
    decisionId: "inspection_pass",
    label: "Pass inspection",
    actionId: "inspection"
  }]);
  const prompt = buildDecisionPrompt(packet);
  const opponent = packet.observation.opponents[0];
  const opponentCeo = match.players[opponent.seat].pieces.find((piece) => piece.kind === "ceo");

  assert.equal(packet.policySeed, "private-visibility-contract");
  assert.equal(packet.seed, undefined);
  assert.doesNotMatch(prompt, /private-visibility-contract/);
  assert.doesNotMatch(prompt, /profileId/);
  assert.equal(opponent.profileId, undefined);
  assert.equal(packet.observation.publicTable.players[opponent.seat].objectiveId, undefined);
  assert.equal(packet.observation.publicTable.players[opponent.seat].tactics, undefined);
  assert.equal(
    opponent.researchProtection,
    match.players[opponent.seat].researchProtection
  );
  assert.deepEqual(opponent.pieces, match.players[opponent.seat].pieces);
  assert.ok(packet.observation.board.some((tile) =>
    tile.components.some((component) => component.id === opponentCeo.id)
  ));
  assert.deepEqual(
    packet.observation.publicTable.contracts,
    match.contracts
  );
  assert.ok(packet.publicHistory.length >= 10);
  assert.ok(packet.publicHistory.some((event) => event.summary === "Public event 0."));
  assert.ok(!packet.publicHistory.some((event) => event.type === "strategy_decision"));
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
      powered: true
    },
    {
      id: "capital-fixture",
      tileId: capital.instanceId,
      category: "capital",
      powered: true
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
  assert.ok(captured.decisions.length >= 2);
  assert.ok(captured.decisions.some(
    (decision) => decision.parameters.facilityId === "cloud-fixture"
  ));
  assert.ok(captured.decisions.some(
    (decision) => decision.parameters.facilityId === "capital-fixture"
  ));
  assert.equal(player.runway, runwayBefore + 2);
});

test("latest Production snapshot governs later powered and offline rules", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "production-snapshot-contract" },
    () => {}
  );
  const player = match.players[0];
  const first = match.board.find((tile) => tile.category === "cloud");
  const second = match.board.find((tile) => tile.category === "capital");
  player.facilities = [
    { id: "snapshot-powered", tileId: first.instanceId, category: "cloud", powered: false },
    { id: "snapshot-offline", tileId: second.instanceId, category: "capital", powered: true }
  ];
  player.latestProductionSnapshot = {
    round: 4,
    poweredFacilityIds: ["snapshot-powered"],
    offlineFacilityIds: ["snapshot-offline"],
    powerSupply: 1,
    powerDemandSatisfied: 1
  };

  assert.deepEqual(
    match.latestPoweredFacilities(player).map((facility) => facility.id),
    ["snapshot-powered"]
  );
  assert.deepEqual(
    match.latestOfflineFacilities(player).map((facility) => facility.id),
    ["snapshot-offline"]
  );
  assert.equal(match.finalMandate(player).offlinePenalty, 1);
});

test("powered Facility Mandate probe scores only the latest Production snapshot", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      seed: "powered-facility-mandate-probe",
      rulesVariant: { finalPoweredFacilityMandate: 1 }
    },
    () => {}
  );
  const player = match.players[0];
  const first = match.board.find((tile) => tile.category === "cloud");
  const second = match.board.find((tile) => tile.category === "capital");
  player.mandate = 5;
  player.facilities = [
    { id: "probe-powered", tileId: first.instanceId, category: "cloud", powered: false },
    { id: "probe-offline", tileId: second.instanceId, category: "capital", powered: true }
  ];
  player.latestProductionSnapshot = {
    round: 4,
    poweredFacilityIds: ["probe-powered"],
    offlineFacilityIds: ["probe-offline"],
    powerSupply: 1,
    powerDemandSatisfied: 1
  };

  assert.deepEqual(match.finalMandate(player), {
    score: 5,
    poweredFacilityMandate: 1,
    offlinePenalty: 1
  });
});

test("Fusion consumes the single shared project marker", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "single-fusion-marker" },
    () => {}
  );
  match.round = 4;
  const first = match.players[0];
  const second = match.players[1];
  for (const player of [first, second]) {
    player.programUses = 1;
    player.runway = 10;
    player.compute = 10;
  }
  const firstChoice = match.legalEscalationResolutions(0, "fusion_demonstrator")[0];
  assert.ok(firstChoice);
  await match.applyEscalation([], 0, "fusion_demonstrator", firstChoice);
  assert.equal(match.fusionBuiltBy, 0);
  assert.deepEqual(match.legalEscalationResolutions(1, "fusion_demonstrator"), []);
});

test("Frontier never contributes control to category Mandates", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "frontier-control-exception" },
    () => {}
  );
  assert.equal(match.controlledCategories(match.players[0]).has("frontier"), false);
});

test("immediate exchanges are exactly one-for-one across Runway and Compute", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 3, factionId: "coalition_lab", seed: "same-type-exchange" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const match = runtime.match;
  const player = match.players[0];
  const partner = match.players[1];
  player.runway = 2;
  partner.runway = 1;
  partner.compute = 1;
  assert.ok(match.immediateTradeOffers(0, "before").every((offer) =>
    offer.giveResource !== offer.receiveResource &&
    offer.giveAmount === 1 &&
    offer.receiveAmount === 1
  ));
  assert.equal(match.completeImmediateTrade(player.seat, partner.seat, {
    timing: "before",
    partnerSeat: partner.seat,
    giveResource: "runway",
    giveAmount: 1,
    receiveResource: "runway",
    receiveAmount: 1
  }), false);
  assert.equal(player.runway, 2);
  assert.equal(partner.runway, 1);
  assert.equal(player.roundMetrics.dealFlowUsed, undefined);
  assert.equal(player.metrics.factionAbilityValues.deal_flow, undefined);
});

test("Boardroom Coup removes the leader's CEO from legal action movement", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "boardroom-ceo-lock" },
    () => {}
  );
  match.round = 3;
  match.cycle = 1;
  const headline = match.headlineDocument.headlines.find(
    (candidate) => candidate.id === "boardroom_coup"
  );
  match.headlineDecks[3][0] = headline;
  match.choose = async (_policies, _seat, _stage, decisions) =>
    decisions.find((decision) => decision.decisionId === "boardroom_accept_lock");

  await match.prepareHeadline([]);

  const leader = match.players[match.regime.cycle.ceoLockedSeat];
  assert.ok(leader);
  assert.ok(match.legalResolutions(leader.seat, "fund").length > 0);
  assert.ok(match.legalResolutions(leader.seat, "fund")
    .every((decision) => decision.parameters.pieceId !== leader.pieces.find(
      (piece) => piece.kind === "ceo"
    ).id));
});

test("Entanglement Custody Replicates does not discount Links or Fusion", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      seed: "entanglement-printed-fields-only",
      rulesVariant: { networkInfrastructureEnabled: true }
    },
    () => {}
  );
  match.round = 4;
  match.regime.cycle = { superconductor: "replicates" };
  const player = match.players[0];
  player.facilities = [{
    id: "entanglement-facility",
    tileId: player.pieces[0].tileId,
    category: "frontier",
    powered: false
  }];

  player.runway = 0;
  assert.equal(
    match.legalResolutions(player.seat, "build")
      .some((decision) => decision.parameters?.buildMode === "link"),
    false
  );
  player.runway = 1;
  const links = match.legalResolutions(player.seat, "build")
    .filter((decision) => decision.parameters?.buildMode === "link");
  assert.ok(links.length > 0);
  assert.ok(links.every((decision) => decision.parameters.actualRunwayCost === 1));

  player.runway = 4;
  assert.deepEqual(
    match.legalEscalationResolutions(player.seat, "fusion_demonstrator"),
    []
  );
  player.runway = 5;
  const fusion = match.legalEscalationResolutions(player.seat, "fusion_demonstrator");
  assert.ok(fusion.length > 0);
  assert.ok(fusion.every((decision) => decision.parameters.cost === 5));
});

test("Loopfold stacks Social Graph with its destination-dependent Installed Base", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, factionId: "platform_empire", seed: "faction-modifier-stack" },
    () => {}
  );
  match.round = 4;
  const player = match.players[0];
  player.compute = 1;
  const decision = match.adjustDecision(player, {
    decisionId: "deploy_social_graph_stack",
    actionId: "deploy",
    parameters: {
      destinationCategory: "media",
      socialGraph: true
    },
    consequences: {}
  });

  assert.equal(decision.parameters.computeCost, 0);
  match.applyResolution(player.seat, decision);
  assert.equal(player.roundMetrics.socialGraphUsed, true);
  assert.equal(player.roundMetrics.installedBaseUsed, true);
});

test("Influence Joint Venture proposals use the acting destination Facility", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "influence-destination-host" },
    () => {}
  );
  match.round = 3;
  const player = match.players[0];
  const rival = match.players[1];
  const destination = match.board.find((tile) => tile.category === "frontier");
  const adjacent = match.board.find((tile) =>
    tile.instanceId !== destination.instanceId && match.areAdjacent(destination.instanceId, tile.instanceId)
  );
  const elsewhere = match.board.find((tile) =>
    tile.category !== "frontier" && tile.instanceId !== adjacent.instanceId
  );
  player.facilities = [
    { id: "destination-host", tileId: destination.instanceId, category: "frontier", powered: false },
    { id: "elsewhere-host", tileId: elsewhere.instanceId, category: elsewhere.category, powered: false }
  ];
  rival.facilities = [
    { id: "rival-host", tileId: adjacent.instanceId, category: adjacent.category, powered: false }
  ];
  const proposals = match.legalResolutions(0, "influence")
    .filter((decision) => decision.parameters?.mode === "joint_venture");
  assert.ok(proposals.length > 0);
  assert.ok(proposals.every((decision) =>
    player.facilities.find((facility) => facility.id === decision.parameters.leftFacilityId)
      .tileId === decision.parameters.destinationId
  ));
});

test("removed Build discounts cannot create otherwise unaffordable Builds", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "optional-build-discount" },
    () => {}
  );
  const player = match.players[0];
  match.round = 2;
  player.runway = 0;

  const decisions = match.legalResolutions(0, "build");
  assert.ok(decisions.every((decision) => !Object.hasOwn(
    decision.parameters,
    "useBuildDiscount"
  )));
  assert.ok(decisions.every((decision) =>
    decision.parameters.buildMode !== "facility"
  ));
});

test("removed Market Access cannot lower a Deploy requirement", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "optional-market-access" },
    () => {}
  );
  const player = match.players[0];
  player.compute = 10;
  player.customers = 0;
  player.capability = 1;

  const requiredDecisions = match.legalResolutions(0, "deploy");
  assert.equal(requiredDecisions.length, 0);

  player.capability = 2;
  const legal = match.legalResolutions(0, "deploy");
  assert.ok(legal.length > 0);
  assert.ok(legal.every((decision) => !Object.hasOwn(
    decision.parameters,
    "useMarketAccess"
  )));

  match.applyResolution(0, legal[0]);
  assert.equal(player.customers, 1);
});

test("Research Protection is never a tradable resource", async () => {
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
  safetyLab.runway = 1;
  safetyLab.compute = 1;
  ordinaryInstitution.runway = 1;
  ordinaryInstitution.compute = 1;
  assert.ok(match.config.resources.researchProtection);
  for (const [giver, receiver] of [
    [safetyLab, ordinaryInstitution],
    [ordinaryInstitution, safetyLab]
  ]) {
    assert.deepEqual(match.tradableResources(giver, receiver).sort(), ["compute", "runway"]);
  }
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

test("AGI Dossier readiness is pure, diagnostic, and UI-ready", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      seed: "agi-dossier-readiness"
    },
    () => {}
  );
  const player = match.players[0];
  player.compute = 4;
  player.agiDossier.choices = Object.fromEntries(
    match.config.agiDossier.modules.map((module) => [module.id, "commit"])
  );
  const before = structuredClone(player);
  assert.deepEqual(match.declarationReadiness(player), {
    ready: true,
    failingRequirement: null,
    committedCount: 4,
    publicationCommitted: true,
    fullyPaid: false,
    eligible: false
  });
  assert.deepEqual(player, before);
  player.compute = 3;
  assert.equal(match.declarationReadiness(player).failingRequirement, "compute");
  player.compute = 4;
  player.agiDossier.choices.publication_claim = "hedge";
  assert.equal(match.declarationReadiness(player).failingRequirement, "publication");
});

test("revealed Dossier payment eligibility reaches aggregate bookkeeping", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "dossier-eligibility-bookkeeping" },
    () => {}
  );
  const player = match.players[0];
  match.round = 4;
  player.compute = 4;
  player.agiDossier.choices = Object.fromEntries(
    match.config.agiDossier.modules.map((module) => [module.id, "commit"])
  );
  for (const rival of match.players.slice(1)) {
    rival.agiDossier.choices = Object.fromEntries(
      match.config.agiDossier.modules.map((module) => [module.id, "hedge"])
    );
  }

  match.revealAgiDossiers();

  assert.deepEqual(player.metrics.earliestAgiEligibility, {
    round: 4,
    cycle: 1,
    timing: "dossier_reveal"
  });
  assert.equal(player.agiDossier.eligible, true);
  assert.equal(player.compute, 0);
});

test("the strongest supported Dossier claim deterministically overrides Mandate", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "agi-prediction-bag-resolution" },
    () => {}
  );
  const mandates = [18, 15, 12];
  for (const [seat, mandate] of mandates.entries()) match.players[seat].mandate = mandate;
  for (const player of match.players) {
    player.agiDossier = {
      choices: Object.fromEntries(
        match.config.agiDossier.modules.map((module) => [module.id, "commit"])
      ),
      revealed: true,
      fullyPaid: true,
      eligible: true,
      committedCount: 4,
      computePaid: 4,
      finalPoweredFacilities: player.seat < 2 ? 2 : 0
    };
  }
  match.players[0].capability = 3;
  match.players[0].trust = 4;
  match.players[1].capability = 12;
  match.players[1].trust = 4;
  match.players[2].capability = 2;
  match.players[2].trust = 1;

  match.resolveAgiOutcome();

  const resolution = match.matchMetrics.agiResolution;
  assert.equal(resolution.method, "highest-supported-claim");
  assert.equal(resolution.emerged, true);
  assert.deepEqual(resolution.provisionalWinnerSeats, [0]);
  assert.equal(resolution.selectedSeat, 1);
  assert.equal(resolution.strengths[0].strength, 8);
  assert.ok(!Object.hasOwn(resolution, "draws"));
  assert.equal(match.players.filter((player) => player.agiDeclared).length, 1);
  assert.deepEqual(match.result().winnerSeats, [resolution.selectedSeat]);
});

test("Production recalculates powered Facilities without persistent Grid-Ready state", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      seed: "grid-ready-lifecycle",
      rulesVariant: { playProfileId: "advanced-play" }
    },
    () => {}
  );
  match.round = 2;
  const player = match.players[0];
  player.capability = 9;
  player.customers = 3;
  player.trust = 3;
  player.compute = 4;
  const anchor = match.board.find((tile) => tile.category !== "frontier");
  const sites = [
    anchor,
    ...match.board.filter((tile) =>
      tile.category !== "frontier" &&
      tile.instanceId !== anchor.instanceId &&
      match.areAdjacent(anchor.instanceId, tile.instanceId)
    ).slice(0, 2)
  ];
  player.facilities = sites.map((tile, index) => ({
    id: `s0-facility-${index + 1}`,
    tileId: tile.instanceId,
    category: tile.category,
      powered: false
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
  assert.equal(player.latestProductionSnapshot.poweredFacilityIds.length, 3);
  assert.equal(player.facilities.filter((facility) => facility.powered).length, 0);
  assert.ok(player.facilities.every((facility) => !("gridReady" in facility)));
  assert.ok(match.matchMetrics.agiFunnel[0].coreRequirementsMet);

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
    decisionId: "move-preserves-no-power-state",
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
  assert.equal(player.facilities[0].powered, false);
  assert.ok(!("gridReady" in player.facilities[0]));
});

test("action selection excludes impossible commitments without trade-assisted legality", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 4, seed: "six-core-actions" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  let selections = runtime.match.legalActionSelections(0)
    .filter((decision) => !decision.decisionId.startsWith("select_escalation_"));
  assert.deepEqual(
    selections.map((decision) => decision.actionId),
    ["fund", "research", "build", "organize", "influence"]
  );
  assert.ok(selections.every(
    (decision) => decision.consequences.currentResolutionCount > 0
  ));

  runtime.match.players[0].compute = 0;
  runtime.match.players[1].compute = 1;
  for (const tile of runtime.match.board) {
    if (tile.category === "cloud") tile.category = "media";
  }
  selections = runtime.match.legalActionSelections(0)
    .filter((decision) => !decision.decisionId.startsWith("select_escalation_"));
  const research = selections.find((decision) => decision.actionId === "research");
  assert.equal(research, undefined);

  for (const opponent of runtime.match.players.slice(1)) opponent.compute = 0;
  selections = runtime.match.legalActionSelections(0)
    .filter((decision) => !decision.decisionId.startsWith("select_escalation_"));
  assert.equal(selections.some((decision) => decision.actionId === "research"), false);

  runtime.match.round = 2;
  runtime.match.players[0].programUses = 1;
  const megaCluster = runtime.match.legalActionSelections(0).find(
    (decision) => decision.actionId === "mega_cluster"
  );
  assert.equal(megaCluster, undefined);

  const player = runtime.match.players[0];
  const forcedNoOpsBefore = player.metrics.forcedNoOps;
  runtime.match.commitEscalationSelection(player, "mega_cluster");
  player.selectedAction = "escalation_mega_cluster";
  await runtime.match.resolveSelectedSeat(runtime.policies, 0);
  assert.equal(player.programUses, 0);
  assert.ok(player.escalationsUsed.includes("mega_cluster"));
  assert.equal(player.metrics.forcedNoOps, forcedNoOpsBefore + 1);
});

test("pre-Act offers cannot make the selected action illegal", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 4, seed: "preserve-selected-action" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const match = runtime.match;
  const player = match.players[0];
  const partner = match.players[1];

  player.selectedAction = "research";
  player.compute = 2;
  partner.compute = 0;
  assert.deepEqual(
    match.immediateTradeGiveAmounts(0, partner, "compute"),
    [1]
  );
  assert.ok(match.immediateTradeDecisions(0, "before")
    .filter((decision) => decision.parameters?.giveResource === "compute")
    .every((decision) => match.provisionalTradeResolvesSelection(
      0,
      decision.parameters,
      "research"
    )));
  player.compute = 1;
  assert.deepEqual(
    match.immediateTradeGiveAmounts(0, partner, "compute"),
    [1]
  );
  assert.ok(match.immediateTradeDecisions(0, "before")
    .filter((decision) => decision.parameters)
    .every((decision) => match.provisionalTradeResolvesSelection(
      0,
      decision.parameters,
      "research"
    )));
  partner.selectedAction = "research";
  partner.compute = 1;
  assert.deepEqual(
    match.immediateTradeReceiveAmounts(0, partner, "compute"),
    [1]
  );

  player.selectedAction = "deploy";
  player.factionId = "vertical_empire";
  player.capability = 4;
  player.customers = 0;
  player.compute = 0;
  player.facilities = [{ id: "orbital-facility", tileId: player.pieces[0].tileId }];
  match.round = 4;
  assert.ok(match.selectedActionResolutions(0).length > 0);
  let askedToUseOrbitalCompute = false;
  const usedOrbitalCompute = await match.maybeUseOrbitalCompute([
    {
      async decide(packet) {
        askedToUseOrbitalCompute = true;
        return {
          decision: { decisionId: packet.legalDecisions[0].decisionId },
          receipt: { provider: "test", requestId: packet.requestId }
        };
      }
    }
  ], 0);
  assert.equal(askedToUseOrbitalCompute, false);
  assert.equal(usedOrbitalCompute, false);
  assert.notEqual(player.factionAbilityUsed.orbitalCompute, true);
});

test("immediate trades skip impossible turns and package each offer", async () => {
  const runtime = await createInteractiveGame(
    { playerCount: 4, seed: "packed-immediate-trade" },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const match = runtime.match;
  for (const player of match.players) {
    player.runway = 0;
    player.compute = 0;
  }
  const unavailablePolicies = match.players.map(() => ({
    async decide() {
      throw new Error("An impossible trade must not create a decision packet.");
    }
  }));
  assert.equal(await match.chooseImmediateTrade(unavailablePolicies, 0, "before"), null);

  const player = match.players[0];
  const partner = match.players[1];
  player.runway = 2;
  partner.compute = 1;
  const stages = [];
  const policies = match.players.map(() => ({
    async decide(packet) {
      const stage = packet.requestId.split(":").at(-2);
      stages.push(stage);
      const selected = stage === "immediate_trade_response"
        ? packet.legalDecisions.find((decision) => decision.decisionId === "trade_accept")
        : packet.legalDecisions.find((decision) =>
          decision.decisionId.startsWith("trade_offer_")
        );
      return {
        decision: { decisionId: selected.decisionId },
        receipt: { provider: "fixture" }
      };
    }
  }));
  const offer = await match.chooseImmediateTrade(policies, player.seat, "before");
  assert.deepEqual(stages, ["immediate_trade_before"]);
  assert.ok(offer);
  assert.equal(offer.partnerSeat, partner.seat);
  const resourcesBeforeTrade = match.players.map((candidate) => ({
    runway: candidate.runway,
    compute: candidate.compute
  }));
  assert.equal(await match.settleImmediateTrade(policies, player.seat, offer), true);
  assert.deepEqual(stages, ["immediate_trade_before", "immediate_trade_response"]);
  for (const resource of ["runway", "compute"]) {
    const dealFlowBonus = resource === "runway" && player.factionId === "coalition_lab" ? 1 : 0;
    assert.equal(
      player[resource],
      resourcesBeforeTrade[player.seat][resource]
        - (offer.giveResource === resource ? offer.giveAmount : 0)
        + (offer.receiveResource === resource ? offer.receiveAmount : 0)
        + dealFlowBonus
    );
    const partnerDealFlowBonus =
      resource === "runway" && partner.factionId === "coalition_lab" ? 1 : 0;
    assert.equal(
      partner[resource],
      resourcesBeforeTrade[partner.seat][resource]
        + (offer.giveResource === resource ? offer.giveAmount : 0)
        - (offer.receiveResource === resource ? offer.receiveAmount : 0)
        + partnerDealFlowBonus
    );
  }
});

test("Deal Flow can be paused without suppressing the underlying trade", async () => {
  const runtime = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "paused-deal-flow",
      rulesVariant: {
        pausedFactionAbilities: [{
          factionId: "coalition_lab",
          abilityId: "deal_flow"
        }]
      }
    },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const match = runtime.match;
  const coalition = match.players[0];
  const partner = match.players[1];
  coalition.runway = 2;
  coalition.compute = 0;
  partner.runway = 0;
  partner.compute = 1;

  assert.equal(match.completeImmediateTrade(coalition.seat, partner.seat, {
    timing: "before",
    partnerSeat: partner.seat,
    giveResource: "runway",
    giveAmount: 1,
    receiveResource: "compute",
    receiveAmount: 1
  }), true);
  assert.equal(coalition.runway, 1);
  assert.equal(coalition.compute, 1);
  assert.equal(partner.runway, 1);
  assert.equal(partner.compute, 0);
  assert.equal(coalition.roundMetrics.dealFlowUsed, undefined);
  assert.equal(coalition.metrics.factionAbilityValues.deal_flow, undefined);
});

test("immediate-trade packet ceiling is rule-derived and formal windows cannot repeat", async () => {
  assert.deepEqual(
    [2, 3, 4, 5, 6].map((playerCount) => immediateTradePacketCeiling(playerCount)),
    [48, 72, 96, 120, 144]
  );
  assert.throws(
    () => immediateTradePacketCeiling(4, { counteroffers: true }),
    /forbids counteroffers and claims/
  );
  assert.throws(
    () => immediateTradePacketCeiling(4, {
      counteroffers: true,
      thirdPartyClaims: true
    }),
    /forbids counteroffers and claims/
  );
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "immediate-trade-window-ledger" },
    () => {}
  );
  match.activeImmediateTradeSeat = 0;
  match.registerImmediateTradeDecisionWindow(1, "immediate_trade_response");
  assert.throws(
    () => match.registerImmediateTradeDecisionWindow(1, "immediate_trade_response"),
    /formal window repeated/
  );
  assert.equal(match.immediateTradePackets, 1);
  assert.equal(match.immediateTradePacketCeiling, 72);
});

test("rejected immediate trades end without counteroffers or claims", async () => {
  const runtime = await createInteractiveGame(
    {
      playerCount: 4,
      seed: "open-counteroffer",
      rulesVariant: { playProfileId: "advanced-play" }
    },
    () => {}
  );
  await runtime.match.setup(runtime.policies);
  const match = runtime.match;
  for (const player of match.players) {
    player.runway = 0;
    player.compute = 0;
  }
  const active = match.players[0];
  const counterMaker = match.players[1];
  active.runway = 2;
  counterMaker.compute = 1;
  const stages = [];
  const policies = match.players.map(() => ({
    async decide(packet) {
      const stage = packet.requestId.split(":").at(-2);
      stages.push(stage);
      const selected = stage === "immediate_trade_response"
        ? packet.legalDecisions.find((decision) => decision.decisionId === "trade_reject")
        : packet.legalDecisions.find((decision) =>
          decision.decisionId.startsWith("trade_offer_")
        );
      return {
        decision: { decisionId: selected.decisionId },
        receipt: { provider: "fixture" }
      };
    }
  }));
  const offer = await match.chooseImmediateTrade(policies, active.seat, "before");
  assert.ok(offer);
  assert.equal(await match.settleImmediateTrade(policies, active.seat, offer), false);
  assert.deepEqual(stages, [
    "immediate_trade_before",
    "immediate_trade_response"
  ]);
  assert.equal(active.runway, 2);
  assert.equal(active.compute, 0);
  assert.equal(counterMaker.runway, 0);
  assert.equal(counterMaker.compute, 1);
});

test("counteroffer and third-party-claim overlays fail closed", async () => {
  await assert.rejects(
    createInteractiveGame({
      playerCount: 2,
      seed: "forbidden-counteroffer",
      rulesVariant: { immediateTradeCounteroffers: true }
    }, () => {}),
    /forbids counteroffers and claims/
  );
  await assert.rejects(
    createInteractiveGame({
      playerCount: 2,
      seed: "forbidden-claims",
      rulesVariant: { immediateTradeThirdPartyClaims: true }
    }, () => {}),
    /forbids counteroffers and claims/
  );
});

test("interactive games accept mixed per-opponent personas and decision backends", async () => {
  const runtime = await createInteractiveGame(
    {
      playerCount: 4,
      seed: "mixed-interactive-backends",
      opponentProfileIds: [
        "power_broker",
        "trust_governor",
        "capability_rusher"
      ],
      opponentBackends: ["greedy", "claude", "hybrid-codex"],
      allowLlm: true,
      maxLlmDecisions: 7,
      model: "test-model"
    },
    () => {}
  );
  assert.deepEqual(
    runtime.opponents.map((opponent) => opponent.profile.id),
    ["power_broker", "trust_governor", "capability_rusher"]
  );
  assert.deepEqual(
    runtime.opponents.map((opponent) => opponent.backend),
    ["greedy", "claude", "hybrid-codex"]
  );
  assert.deepEqual(
    runtime.policies.map((policy) => policy.kind),
    ["human", "deterministic", "llm", "hybrid"]
  );
  assert.equal(runtime.opponents[0].decisionBudget, null);
  assert.equal(runtime.opponents[1].decisionBudget.remaining, 7);
  assert.equal(runtime.opponents[2].decisionBudget.remaining, 7);
  assert.notEqual(
    runtime.opponents[1].decisionBudget,
    runtime.opponents[2].decisionBudget
  );
  assert.equal(runtime.policies[2].caller.model, "test-model");
  assert.equal(runtime.policies[3].caller.model, "test-model");

  await assert.rejects(
    createInteractiveGame(
      {
        playerCount: 3,
        opponentBackends: ["weighted", "codex"],
        allowLlm: false
      },
      () => {}
    ),
    /explicit allowLlm authorization/
  );
  await assert.rejects(
    createInteractiveGame(
      {
        playerCount: 3,
        opponentBackends: ["weighted", "claude"],
        allowLlm: true,
        maxLlmDecisions: 25
      },
      () => {}
    ),
    /maxLlmDecisions must be an integer from 0 to 24/
  );
});

test("browser-native games use deterministic opponents without a server or LLM authorization", async () => {
  const runtime = await createBrowserInteractiveGame(
    {
      playerCount: 4,
      seed: "browser-native-deterministic",
      opponentProfileIds: [
        "power_broker",
        "trust_governor",
        "capability_rusher"
      ],
      opponentBackends: ["weighted", "greedy", "weighted"],
      allowLlm: false
    },
    () => {}
  );
  assert.deepEqual(
    runtime.opponents.map((opponent) => opponent.backend),
    ["weighted", "greedy", "weighted"]
  );
  assert.deepEqual(
    runtime.policies.map((policy) => policy.kind),
    ["human", "deterministic", "deterministic", "deterministic"]
  );
  let completingRuntime;
  completingRuntime = await createBrowserInteractiveGame(
    {
      playerCount: 3,
      seed: "browser-native-complete-match",
      opponentBackends: ["weighted", "greedy"]
    },
    (packet) => queueMicrotask(() => {
      completingRuntime.human.submit(packet.legalDecisions[0].decisionId);
    })
  );
  const result = await completingRuntime.match.play(completingRuntime.policies);
  assert.ok(result.worldEnding.name);
  assert.ok(completingRuntime.match.replay.length > 0);
  await assert.rejects(
    createBrowserInteractiveGame(
      {
        playerCount: 3,
        opponentBackends: ["weighted", "claude"],
        allowLlm: true
      },
      () => {}
    ),
    /requires the optional local bridge/
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

test("greedy policy resolves equal utility without leaking lexicographic decision order", async () => {
  const profiles = await loadPlayerProfiles();
  const profile = profiles.find((candidate) => candidate.id === "infrastructure_compounder");
  const policy = new WeightedPlayerPolicy(profile, { selection: "greedy" });
  const decisions = [
    {
      decisionId: "agi_dossier_commit_benchmark_claim",
      label: "Commit",
      actionId: "agi_dossier",
      consequences: { agiClaim: 1, compute: -1, scrutiny: 1 }
    },
    {
      decisionId: "agi_dossier_hedge_benchmark_claim",
      label: "Hedge",
      actionId: "agi_dossier",
      consequences: { agiClaim: 0 }
    }
  ];
  const selected = new Set();
  for (let index = 0; index < 64; index += 1) {
    const packet = {
      schemaVersion: 1,
      requestId: `dossier-tie-${index}`,
      matchId: "dossier-tie",
      seed: "dossier-tie",
      seat: 0,
      factionId: "coalition_lab",
      round: 1,
      cycle: 1,
      observation: { self: {} },
      legalDecisions: decisions
    };
    const first = await policy.decide(packet);
    const repeated = await policy.decide(packet);
    assert.equal(repeated.decision.decisionId, first.decision.decisionId);
    assert.equal(first.receipt.tiedTopCount, 2);
    selected.add(first.decision.decisionId);
  }
  assert.deepEqual(selected, new Set(decisions.map((decision) => decision.decisionId)));
});

test("Dossier decisions expose support and payment facts to every policy", async () => {
  const { match } = await createInteractiveGame(
    { playerCount: 3, seed: "dossier-decision-assessment" },
    () => {}
  );
  const player = match.players[0];
  player.capability = 3;
  player.compute = 2;
  const benchmark = match.config.agiDossier.modules.find(
    (module) => module.id === "benchmark_claim"
  );
  const assessment = match.agiDossierDecisionAssessment(
    player,
    benchmark,
    "commit"
  );
  assert.deepEqual(assessment, {
    moduleId: "benchmark_claim",
    metric: "capability",
    orientation: "commit",
    currentEvidenceValue: 3,
    currentEvidenceThreshold: 3,
    supportedNow: true,
    supportedCommittedEvidenceClaims: 0,
    minimumSupportedEvidenceClaims: 2,
    committedBefore: 0,
    projectedCommittedCount: 1,
    projectedComputeCost: 1,
    currentCompute: 2,
    canPayProjectedCost: true
  });
});

test("greedy Dossier policy commits supported affordable claims and hedges dead claims", async () => {
  const profiles = await loadPlayerProfiles();
  const profile = profiles.find((candidate) => candidate.id === "infrastructure_compounder");
  const policy = new WeightedPlayerPolicy(profile, { selection: "greedy" });
  const packetFor = (assessment) => ({
    schemaVersion: 1,
    requestId: `dossier-semantic-${assessment.moduleId}-${assessment.supportedNow}`,
    matchId: "dossier-semantic",
    seed: "dossier-semantic",
    seat: 0,
    factionId: "coalition_lab",
    round: assessment.metric === "publication" ? 4 : 1,
    cycle: 3,
    observation: { self: {} },
    legalDecisions: [
      {
        decisionId: `agi_dossier_commit_${assessment.moduleId}`,
        label: "Commit",
        actionId: "agi_dossier",
        parameters: { orientation: "commit", dossierAssessment: assessment },
        consequences: { agiClaim: 1, compute: -1, scrutiny: 1 }
      },
      {
        decisionId: `agi_dossier_hedge_${assessment.moduleId}`,
        label: "Hedge",
        actionId: "agi_dossier",
        parameters: {
          orientation: "hedge",
          dossierAssessment: {
            ...assessment,
            orientation: "hedge",
            projectedCommittedCount: assessment.projectedCommittedCount - 1,
            projectedComputeCost: assessment.projectedComputeCost - 1,
            canPayProjectedCost: true
          }
        },
        consequences: { agiClaim: 0 }
      }
    ]
  });
  const supported = {
    moduleId: "benchmark_claim",
    metric: "capability",
    orientation: "commit",
    supportedNow: true,
    projectedCommittedCount: 1,
    projectedComputeCost: 1,
    canPayProjectedCost: true
  };
  assert.equal(
    (await policy.decide(packetFor(supported))).decision.decisionId,
    "agi_dossier_commit_benchmark_claim"
  );
  assert.equal(
    (await policy.decide(packetFor({
      ...supported,
      moduleId: "publication_claim",
      metric: "publication",
      supportedNow: false
    }))).decision.decisionId,
    "agi_dossier_hedge_publication_claim"
  );
  assert.equal(
    (await policy.decide(packetFor({
      ...supported,
      canPayProjectedCost: false
    }))).decision.decisionId,
    "agi_dossier_hedge_benchmark_claim"
  );
});

test("deterministic personas execute partner, placement, and resource preferences", async () => {
  const profiles = await loadPlayerProfiles();
  const profile = profiles.find((candidate) => candidate.id === "power_broker");
  const policy = new WeightedPlayerPolicy(profile, {
    selection: "greedy",
    rosterProfileIds: ["power_broker", "agi_candidate", "balanced_operator"]
  });
  const packet = {
    observation: {
      self: { facilities: 0 },
      board: [
        {
          tileId: "target",
          q: 0,
          r: 0,
          components: [{ type: "piece", ownerSeat: 1 }]
        },
        { tileId: "near", q: 1, r: 0, components: [] },
        { tileId: "far", q: 3, r: 0, components: [] }
      ]
    }
  };
  const promiseCandidate = {
    decisionId: "negotiation_power_1",
    actionId: "negotiation",
    parameters: { targetSeat: 1 }
  };
  const ordinaryPromise = {
    decisionId: "negotiation_power_2",
    actionId: "negotiation",
    parameters: { targetSeat: 2 }
  };
  assert.equal(
    policy.score(packet, promiseCandidate),
    policy.score(packet, ordinaryPromise) * 15
  );

  const nearBuild = {
    decisionId: "build_facility_near",
    actionId: "build",
    parameters: { destinationId: "near" }
  };
  const farBuild = {
    decisionId: "build_facility_far",
    actionId: "build",
    parameters: { destinationId: "far" }
  };
  assert.equal(
    policy.score(packet, nearBuild),
    policy.score(packet, farBuild) * 20
  );

  const favorableComputeTrade = {
    decisionId: "trade_accept",
    actionId: "trade",
    parameters: {
      giveResource: "runway",
      giveAmount: 1,
      receiveResource: "compute",
      receiveAmount: 2
    }
  };
  const unfavorableComputeTrade = {
    ...favorableComputeTrade,
    parameters: {
      ...favorableComputeTrade.parameters,
      giveAmount: 2,
      receiveAmount: 1
    }
  };
  assert.ok(
    policy.score(packet, favorableComputeTrade) >
      policy.score(packet, unfavorableComputeTrade)
  );
});

test("Coalition conversion treatment prioritizes causally necessary Deal Flow spending", async () => {
  const profiles = await loadPlayerProfiles();
  const profile = profiles.find((candidate) => candidate.id === "balanced_operator");
  const baseline = new WeightedPlayerPolicy(profile, { selection: "greedy" });
  const treated = new WeightedPlayerPolicy(profile, {
    selection: "greedy",
    treatment: "coalition_conversion_v1"
  });
  const packet = {
    schemaVersion: 1,
    requestId: "coalition-conversion-treatment",
    matchId: "match",
    seed: "coalition-conversion-treatment",
    seat: 0,
    factionId: "coalition_lab",
    round: 2,
    cycle: 1,
    observation: {
      self: {
        runway: 1,
        dealFlowConversion: { unspentCredits: 1 }
      }
    },
    legalDecisions: [
      {
        decisionId: "build_facility_research_fixture",
        label: "Build Research Facility",
        actionId: "build",
        parameters: { buildMode: "facility", actualRunwayCost: 1 },
        consequences: { runway: -1, facility: "research" }
      },
      {
        decisionId: "influence_gain_trust_fixture",
        label: "Gain Trust",
        actionId: "influence",
        parameters: { mode: "trust" },
        consequences: { trust: 1 }
      }
    ]
  };
  const baselineBuild = baseline.score(packet, packet.legalDecisions[0]);
  const treatedBuild = treated.score(packet, packet.legalDecisions[0]);
  assert.equal(treatedBuild, baselineBuild * 4);
  assert.equal(
    treated.score(packet, packet.legalDecisions[1]),
    baseline.score(packet, packet.legalDecisions[1])
  );
  assert.throws(
    () => new WeightedPlayerPolicy(profile, { treatment: "unknown" }),
    /Unknown deterministic policy treatment/
  );
});

test("Deal Flow telemetry conservatively traces necessary spend into Mandate", async () => {
  const { match } = await createInteractiveGame(
    {
      playerCount: 3,
      factionId: "coalition_lab",
      seed: "deal-flow-conversion-telemetry"
    },
    () => {}
  );
  const player = match.players[0];
  player.runway = 2;
  assert.equal(match.grantDealFlowRunway(player, { fixture: true }), 1);
  match.beginRunwayConversionContext(player, {
    actionId: "build",
    decisionId: "fixture-build"
  });
  match.spendRunway(player, 2, {
    cause: "fixture_nonnecessary_build_spend",
    conversionEligible: true
  });
  assert.equal(player.metrics.dealFlowConversion.creditsSpent, 0);
  match.spendRunway(player, 1, {
    cause: "fixture_necessary_build_spend",
    conversionEligible: true
  });
  match.awardMandate(player, 2, "fixture_build_threshold");
  match.endRunwayConversionContext(player);
  assert.equal(player.metrics.dealFlowConversion.creditsGranted, 1);
  assert.equal(player.metrics.dealFlowConversion.creditsSpent, 1);
  assert.equal(
    player.metrics.dealFlowConversion.causallyNecessaryCreditsSpent,
    1
  );
  assert.equal(player.metrics.dealFlowConversion.mandateAttributed, 2);
  assert.deepEqual(
    player.metrics.dealFlowConversion.events.map((event) => ({
      decisionId: event.decisionId,
      necessary: event.causallyNecessaryCreditsSpent,
      mandate: event.mandateAttributed
    })),
    [{ decisionId: "fixture-build", necessary: 1, mandate: 2 }]
  );
});

test("ordinary successful Era I actions populate opening evidence exactly once", async () => {
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

test("mechanics fingerprints ignore faction presentation copy", () => {
  const firstPresentation = {
    factions: [{
      id: "coalition_lab",
      roleId: "faction-1",
      name: "Dovetalis Labs",
      motto: "Named wording",
      starts: { runway: 5 }
    }]
  };
  const secondPresentation = {
    factions: [{
      id: "coalition_lab",
      roleId: "faction-1",
      name: "The Coalition Lab",
      motto: "Alias wording",
      starts: { runway: 5 }
    }]
  };
  assert.deepEqual(
    mechanicsProjection(firstPresentation).factions,
    mechanicsProjection(secondPresentation).factions
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
    workers: 1,
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

test("AGI claim scenarios create paired legal and one-Compute-short states", async () => {
  const common = {
    runs: 1,
    playerCount: 3,
    seed: "agi-declaration-scenario-contract",
    sampleReplays: 0,
    includeObservations: true,
    rotateProfiles: false,
    rotateFactions: false,
    profileIds: ["agi_candidate", "agi_candidate", "agi_candidate"],
    backends: ["greedy", "greedy", "greedy"],
    factionIds: [
      "coalition_lab",
      "vertical_empire",
      "foundry"
    ],
    experimentKind: "agi_declaration_scenario"
  };
  const eligible = await createSimulation({
    ...common,
    scenario: {
      id: "agi_claim_window_v1",
      arm: "eligible",
      focalSeat: 0
    }
  });
  const blocked = await createSimulation({
    ...common,
    scenario: {
      id: "agi_claim_window_v1",
      arm: "blocked_compute",
      focalSeat: 0
    }
  });

  assert.equal(
    eligible.observations[0].scenario.afterInjection.legalDeclaration,
    true
  );
  assert.equal(eligible.observations[0].scenario.claimed, true);
  assert.equal(
    blocked.observations[0].scenario.afterInjection.legalDeclaration,
    false
  );
  assert.equal(
    blocked.observations[0].scenario.afterInjection.failingRequirement,
    "compute"
  );
  assert.equal(blocked.observations[0].scenario.claimed, false);
  assert.notEqual(
    eligible.launchIdentity.fingerprint,
    blocked.launchIdentity.fingerprint
  );
  assert.deepEqual(eligible.configuration.scenario, {
    id: "agi_claim_window_v1",
    arm: "eligible",
    focalSeat: 0
  });
});

test("AGI scenario matrices rotate faction, seat, backend, and opponent roster", () => {
  const comparisons = expandAgiDeclarationScenarioMatrix({
    playerCount: 3,
    factionIds: [
      "platform_empire",
      "imperial_research_lab",
      "vertical_empire",
      "coalition_lab",
      "safety_laboratory",
      "foundry"
    ],
    focalSeats: [0, 1, 2],
    backends: ["greedy", "weighted"],
    opponentRotations: 3,
    profileId: "agi_candidate"
  });
  assert.equal(comparisons.length, 108);
  assert.ok(comparisons.every((comparison) =>
    comparison.leftFactionIds[comparison.focalSeat] ===
      comparison.focalFactionId &&
    comparison.rightFactionIds[comparison.focalSeat] ===
      comparison.focalFactionId &&
    comparison.leftScenario.arm === "eligible" &&
    comparison.rightScenario.arm === "blocked_compute"
  ));
  assert.deepEqual(
    new Set(comparisons.map((comparison) => comparison.backend)),
    new Set(["greedy", "weighted"])
  );
});

test("paired diagnostics report AGI scenario coverage and declaration effects", async () => {
  const roster = ["coalition_lab", "vertical_empire", "foundry"];
  const report = await runFactionSwapDiagnostic({
    workers: 1,
    runsPerArm: 1,
    playerCount: 3,
    seed: "paired-agi-scenario-contract",
    preRegistrationId: "paired-agi-scenario-contract",
    diagnosticKind: "paired_agi_declaration_scenario",
    experimentKind: "agi_declaration_scenario",
    comparisons: [{
      id: "coalition_seat_0_greedy",
      focalSeat: 0,
      profileIds: ["agi_candidate", "agi_candidate", "agi_candidate"],
      backends: ["greedy", "greedy", "greedy"],
      leftFactionIds: roster,
      rightFactionIds: roster,
      leftScenario: {
        id: "agi_claim_window_v1",
        arm: "eligible",
        focalSeat: 0
      },
      rightScenario: {
        id: "agi_claim_window_v1",
        arm: "blocked_compute",
        focalSeat: 0
      }
    }]
  });
  const comparison = report.comparisons[0];
  assert.equal(report.diagnosticKind, "paired_agi_declaration_scenario");
  assert.equal(comparison.paired.leftLegalDeclarationRate, 1);
  assert.equal(comparison.paired.rightLegalDeclarationRate, 0);
  assert.equal(comparison.paired.leftClaimRate, 1);
  assert.equal(comparison.paired.rightClaimRate, 0);
  assert.equal(comparison.left.scenario.arm, "eligible");
  assert.equal(comparison.right.scenario.arm, "blocked_compute");
  assert.match(
    report.balanceEvaluation.promotionGate.reasons[0],
    /qualify a route endpoint/
  );
});

test("parallel faction diagnostics preserve sequential outcomes and fingerprints", async () => {
  const options = {
    runsPerArm: 2,
    playerCount: 4,
    seed: "parallel-faction-diagnostic",
    preRegistrationId: "parallel-faction-diagnostic-test",
    mandateMode: "fixed",
    profileIds: [
      "capability_rusher",
      "balanced_operator",
      "trust_governor",
      "power_broker"
    ],
    backends: ["weighted", "weighted", "weighted", "weighted"],
    comparisons: [{
      id: "orisonix_vs_corthaven",
      focalSeat: 2,
      leftFactionIds: [
        "imperial_research_lab",
        "coalition_lab",
        "safety_laboratory",
        "foundry"
      ],
      rightFactionIds: [
        "imperial_research_lab",
        "coalition_lab",
        "platform_empire",
        "foundry"
      ]
    }]
  };
  const sequential = await runFactionSwapDiagnostic({ ...options, workers: 1 });
  const parallel = await runFactionSwapDiagnostic({ ...options, workers: 2 });

  assert.equal(sequential.execution.scheduler, "inline");
  assert.equal(parallel.execution.scheduler, "worker_threads");
  assert.equal(parallel.execution.workers, 2);
  assert.deepEqual(parallel.comparisons, sequential.comparisons);
  assert.deepEqual(parallel.game, sequential.game);
  assert.deepEqual(parallel.engine, sequential.engine);
  assert.deepEqual(parallel.variant, sequential.variant);
  assert.deepEqual(parallel.strategies, sequential.strategies);
  assert.equal(
    parallel.preRegistration.fingerprint,
    sequential.preRegistration.fingerprint
  );
  assert.equal(parallel.experiment.fingerprint, sequential.experiment.fingerprint);
  assert.equal(parallel.launchIdentity.taskOrder, "comparison_then_arm_then_match");
  assert.equal(parallel.launchIdentity.tasks.length, 2);
  assert.ok(parallel.launchIdentity.study.fingerprint);
  assert.ok(parallel.launchIdentity.tasks.every((task) =>
    task.identity.fingerprint &&
    task.identity.provenance.sourceCommit === parallel.launchIdentity.study.provenance.sourceCommit
  ));
});

test("LLM concurrency broker enforces global and provider-specific caps", async () => {
  assert.throws(
    () => new LlmConcurrencyBroker({ concurrency: 17 }),
    /llmConcurrency must be an integer from 1 to 16/
  );
  assert.throws(
    () => new LlmConcurrencyBroker({
      providerConcurrency: { claude: 5 }
    }),
    /claude concurrency must be an integer from 1 to 4/
  );
  const active = { all: 0, claude: 0, codex: 0 };
  const peak = { all: 0, claude: 0, codex: 0 };
  const broker = new LlmConcurrencyBroker({
    concurrency: 3,
    providerConcurrency: { claude: 1, codex: 2 },
    generation: "broker-cap-test",
    callerFactory: ({ provider }) => ({
      async decide(packet) {
        active.all += 1;
        active[provider] += 1;
        peak.all = Math.max(peak.all, active.all);
        peak[provider] = Math.max(peak[provider], active[provider]);
        await new Promise((resolve) => setTimeout(resolve, 5));
        active.all -= 1;
        active[provider] -= 1;
        return {
          decision: { decisionId: packet.legalDecisions[0].decisionId },
          receipt: { provider: `${provider}-cli` }
        };
      }
    })
  });
  const providers = ["claude", "codex", "claude", "codex", "codex", "claude"];
  await Promise.all(providers.map((provider, taskIndex) => broker.request({
    studyGeneration: "broker-cap-test",
    taskGeneration: `broker-cap-test:${taskIndex}`,
    taskIndex,
    requestToken: `request-${taskIndex}`,
    provider,
    backend: provider,
    packet: {
      requestId: `packet-${taskIndex}`,
      legalDecisions: [{ decisionId: "fixture-choice" }]
    }
  })));
  assert.deepEqual(peak, { all: 3, claude: 1, codex: 2 });
  assert.equal(broker.summary().peakActiveLlmCalls, 3);
  assert.ok(broker.summary().throttledRequests > 0);
});

test("LLM concurrency broker rejects cancelled and stale-generation responses", async () => {
  let release;
  const broker = new LlmConcurrencyBroker({
    concurrency: 1,
    generation: "active-generation",
    callerFactory: () => ({
      async decide(packet) {
        await new Promise((resolve) => {
          release = resolve;
        });
        return {
          decision: { decisionId: packet.legalDecisions[0].decisionId },
          receipt: { provider: "codex-cli" }
        };
      }
    })
  });
  const pending = broker.request({
    studyGeneration: "active-generation",
    taskGeneration: "active-generation:0",
    taskIndex: 0,
    requestToken: "late-request",
    provider: "codex",
    backend: "codex",
    packet: {
      requestId: "late-packet",
      legalDecisions: [{ decisionId: "fixture-choice" }]
    }
  });
  await new Promise((resolve) => setImmediate(resolve));
  broker.cancel(new DOMException("Study replaced.", "AbortError"));
  await assert.rejects(pending, /Study replaced/);
  release();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(broker.summary().completedRequests, 0);
  assert.equal(broker.summary().cancelledRequests, 1);
  await assert.rejects(
    () => broker.request({
      studyGeneration: "replacement-generation",
      taskGeneration: "replacement-generation:0",
      taskIndex: 0,
      requestToken: "stale-request",
      provider: "codex",
      backend: "codex",
      packet: {
        requestId: "stale-packet",
        legalDecisions: [{ decisionId: "fixture-choice" }]
      }
    }),
    /cancelled/
  );
});

test("LLM-backed faction diagnostics require explicit authorization", async () => {
  await assert.rejects(
    () => runFactionSwapDiagnostic({
      runsPerArm: 1,
      playerCount: 4,
      backends: ["codex", "weighted", "weighted", "weighted"],
      comparisons: [{
        id: "llm-inline-default",
        focalSeat: 0,
        leftFactionIds: [
          "safety_laboratory",
          "coalition_lab",
          "imperial_research_lab",
          "foundry"
        ],
        rightFactionIds: [
          "platform_empire",
          "coalition_lab",
          "imperial_research_lab",
          "foundry"
        ]
      }]
    }),
    /explicit allowLlm authorization/
  );
});

test("parallel LLM faction diagnostics cap calls and quarantine failed pairs", async () => {
  let active = 0;
  let peak = 0;
  const report = await runFactionSwapDiagnostic({
    archiveLlmMatches: false,
    workers: 4,
    llmConcurrency: 2,
    llmRetries: 1,
    providerConcurrency: { codex: 2 },
    allowLlm: true,
    runsPerArm: 3,
    sampleReplays: 1,
    playerCount: 4,
    seed: "parallel-llm-faction-diagnostic",
    profileIds: [
      "capability_rusher",
      "balanced_operator",
      "trust_governor",
      "power_broker"
    ],
    backends: ["codex", "weighted", "weighted", "weighted"],
    model: "fixture-model",
    reasoningEffort: "low",
    llmCallerFactory: () => ({
      async decide(packet, { brokerContext }) {
        active += 1;
        peak = Math.max(peak, active);
        await new Promise((resolve) =>
          setTimeout(resolve, brokerContext.taskIndex % 2 ? 2 : 1)
        );
        active -= 1;
        if (brokerContext.taskIndex === 1) {
          const error = new Error("Fixture provider failure.");
          error.providerReceipt = {
            attemptedProvider: "codex-cli",
            attemptedModel: "fixture-model",
            attemptedReasoningEffort: "low",
            attemptedRequestId: packet.requestId
          };
          throw error;
        }
        const decision = packet.legalDecisions[0];
        return {
          decision: { decisionId: decision.decisionId },
          receipt: {
            provider: "codex-cli",
            model: "fixture-model",
            reasoningEffort: "low",
            requestId: packet.requestId,
            decisionId: decision.decisionId
          }
        };
      }
    }),
    comparisons: [{
      id: "strict-llm-pair",
      focalSeat: 0,
      leftFactionIds: [
        "safety_laboratory",
        "coalition_lab",
        "imperial_research_lab",
        "foundry"
      ],
      rightFactionIds: [
        "platform_empire",
        "coalition_lab",
        "imperial_research_lab",
        "foundry"
      ]
    }]
  });

  assert.equal(peak, 2);
  assert.equal(report.execution.scheduler, "worker_threads");
  assert.equal(report.execution.llmConcurrency, 2);
  assert.equal(report.execution.llm.peakActiveLlmCalls, 2);
  assert.equal(report.execution.llm.retries, 1);
  assert.equal(report.execution.quarantinedMatches, 1);
  assert.equal(report.comparisons[0].paired.pairs, 2);
  assert.equal(report.comparisons[0].paired.quarantinedPairs, 1);
  assert.deepEqual(
    report.comparisons[0].paired.rows.map((row) => row.matchIndex),
    [0, 2]
  );
  assert.deepEqual(
    report.llmEvidence.matches.map((match) => match.matchIndex),
    [0, 2]
  );
  assert.ok(report.llmEvidence.matches[0].left.replay);
  assert.ok(report.llmEvidence.matches[0].right.replay);
  assert.ok(report.llmEvidence.matches.every((match) =>
    [...match.left.receipts, ...match.right.receipts].every((receipt) =>
      receipt.provider === "codex-cli" &&
      receipt.model === "fixture-model" &&
      receipt.reasoningEffort === "low" &&
      receipt.fallback === false
    )
  ));
  assert.equal(
    report.quarantine.matches[0].left.providerReceipt.brokerAttempts,
    2
  );
});

test("each completed strict LLM faction match archives before aggregate reporting", async () => {
  const archiveProjectRoot = await mkdtemp(join(tmpdir(), "frontier-llm-archive-"));
  try {
    const report = await runFactionSwapDiagnostic({
      workers: 2,
      llmConcurrency: 1,
      allowLlm: true,
      runsPerArm: 1,
      playerCount: 3,
      seed: "strict-llm-immediate-archive",
      archiveProjectRoot,
      profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
      backends: ["codex", "weighted", "weighted"],
      model: "fixture-model",
      reasoningEffort: "low",
      llmCallerFactory: () => ({
        async decide(packet) {
          return {
            decision: { decisionId: packet.legalDecisions[0].decisionId },
            receipt: {
              provider: "codex-cli",
              model: "fixture-model",
              reasoningEffort: "low",
              requestId: packet.requestId,
              decisionId: packet.legalDecisions[0].decisionId
            }
          };
        }
      }),
      comparisons: [{
        id: "archive-each-llm-match",
        focalSeat: 0,
        leftFactionIds: ["coalition_lab", "platform_empire", "foundry"],
        rightFactionIds: ["safety_laboratory", "platform_empire", "foundry"]
      }]
    });
    const archives = report.execution.completedLlmArchives;
    assert.equal(archives.length, 2);
    assert.deepEqual(archives.map((archive) => archive.arm), ["left", "right"]);
    for (const archive of archives) {
      const stored = JSON.parse(await readFile(join(archiveProjectRoot, archive.relativePath), "utf8"));
      assert.equal(stored.configuration.llmEvidenceMode, "strict_quarantine");
      assert.equal(stored.configuration.usedLlmDecisions > 0, true);
    }
  } finally {
    await rm(archiveProjectRoot, { recursive: true, force: true });
  }
});

test("parallel faction diagnostics fail closed when a worker game fails", async () => {
  await assert.rejects(
    () => runFactionSwapDiagnostic({
      workers: 2,
      runsPerArm: 1,
      playerCount: 4,
      backends: ["weighted", "weighted", "weighted", "weighted"],
      comparisons: [{
        id: "worker-failure",
        focalSeat: 0,
        leftFactionIds: [
          "missing_faction",
          "coalition_lab",
          "imperial_research_lab",
          "foundry"
        ],
        rightFactionIds: [
          "platform_empire",
          "coalition_lab",
          "imperial_research_lab",
          "foundry"
        ]
      }]
    }),
    /Unknown faction: missing_faction/
  );
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
  assert.equal(first.scope.id, "nineteen-hex-simplified-v1");
  assert.ok(first.scope.excluded.includes("the deferred Tactic module"));
  assert.equal(first.schemaVersion, 6);
  assert.equal(first.reportSchemaVersion, 6);
  assert.equal(first.replaySchemaVersion, 2);
  assert.equal(first.decisionSchemaVersion, 2);
  assert.equal(first.game.version, "0.14.3");
  assert.match(first.game.rulesetFingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.engine.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.strategies.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.match(first.experiment.fingerprint, /^sha256:[a-f0-9]{64}$/);
  assert.equal(first.variant.kind, "canonical");
  assert.equal(first.variant.effective.playProfileId, "default-game");
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
  assert.equal(first.samples[0].replay[0].state.board.length, 19);
  assert.equal(first.samples[0].replay.filter((event) =>
    event.type === "realignment_resolved"
  ).length, 0);
  assert.equal(
    Object.values(first.matchMetrics.realignments).reduce((sum, count) => sum + count, 0),
    0
  );
  assert.equal(
    first.matchMetrics.agiFunnel.playerOpportunities,
    options.runs * options.playerCount
  );
  assert.equal(typeof first.matchMetrics.agiFunnelRates.declared, "number");
  assert.equal(typeof first.matchMetrics.factionAbilityValues, "object");
  assert.equal(typeof first.matchMetrics.factionActionSelections, "object");
  assert.equal(typeof first.matchMetrics.profileActionSelections, "object");
  assert.equal(typeof first.matchMetrics.profileMandateSources, "object");
  assert.equal(first.samples[0].replay.at(-1).type, "round_settled");
  assert.equal(first.samples[0].replay.at(-1).round, 4);

  const advanced = await createSimulation({
    ...options,
    runs: 1,
    seed: "simulation-contract-advanced",
    rulesVariant: { playProfileId: "advanced-play" }
  });
  assert.equal(advanced.variant.effective.playProfileId, "advanced-play");
  assert.equal(advanced.samples[0].replay.filter((event) =>
    event.type === "realignment_resolved"
  ).length, 1);
  assert.equal(
    Object.values(advanced.matchMetrics.realignments).reduce((sum, count) => sum + count, 0),
    1
  );
});

test("simulation reports deterministic turn and round projections", async () => {
  const progress = [];
  await createSimulation({
    runs: 1,
    playerCount: 3,
    seed: "live-progress-contract",
    sampleReplays: 0,
    profileIds: ["capability_rusher", "power_broker", "trust_governor"],
    backends: ["weighted"],
    models: ["gpt-5.6-sol"],
    reasoningEfforts: ["medium"]
  }, (entry) => progress.push(entry));
  const turns = progress.filter((entry) => entry.kind === "turn");
  const cycles = progress.filter((entry) => entry.kind === "cycle");
  const rounds = progress.filter((entry) => entry.kind === "round");
  assert.equal(turns.length, 36);
  assert.equal(cycles.length, 12);
  assert.equal(rounds.length, 4);
  assert.deepEqual(turns.map((entry) => entry.turnNumber), Array.from({ length: 36 }, (_, index) => index + 1));
  assert.ok(turns.every((entry) => Number.isInteger(entry.completedSeat)));
  assert.ok(turns.every((entry) => entry.standings.every((standing) =>
    standing.model === null && standing.reasoningEffort === null
  )));
  for (const entry of [...turns, ...cycles, ...rounds]) {
    assert.equal(entry.phase, "match_progress");
    assert.equal(entry.run, 1);
    assert.equal(entry.runs, 1);
    assert.equal(entry.standings.length, 3);
    assert.equal(entry.projectedWinnerSeat, entry.standings[0].seat);
    assert.deepEqual(
      entry.standings.map((standing) => standing.score),
      [...entry.standings.map((standing) => standing.score)].sort((left, right) => right - left)
    );
  }
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

test("LLM evidence modes make fallback policy explicit and leave call budgets uncapped by default", async () => {
  const report = await createSimulation({
    runs: 1,
    playerCount: 3,
    seed: "llm-evidence-mode-contract",
    sampleReplays: 0,
    profileIds: ["capability_rusher", "power_broker", "trust_governor"],
    backends: ["codex"],
    allowLlm: true,
    archiveLlmMatches: false,
    llmStages: ["not-a-decision-stage"]
  });
  assert.equal(report.configuration.llmEvidenceMode, "fallback_allowed");
  assert.equal(report.configuration.maxLlmDecisions, null);
  assert.equal(report.configuration.maxLlmDecisionsPerSeatCycle, null);
  await assert.rejects(
    () => createSimulation({
      runs: 1,
      playerCount: 3,
      backends: ["weighted"],
      requireLlm: true
    }),
    /requireLlm requires at least one LLM-backed policy/
  );
});

test("generic completed strict LLM matches archive before the tournament returns", async () => {
  const archiveProjectRoot = await mkdtemp(join(tmpdir(), "frontier-generic-llm-archive-"));
  try {
    const report = await createSimulation({
      runs: 1,
      playerCount: 3,
      seed: "generic-llm-archive-contract",
      sampleReplays: 0,
      allowLlm: true,
      requireLlm: true,
      strictLlmEvidence: true,
      archiveProjectRoot,
      profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
      backends: ["codex", "weighted", "weighted"],
      callerFactory: () => ({
        async decide(packet) {
          return {
            decision: { decisionId: packet.legalDecisions[0].decisionId },
            receipt: { provider: "fixture", requestId: packet.requestId }
          };
        }
      })
    });
    assert.equal(report.configuration.completedLlmArchives.length, 1);
    const archive = report.configuration.completedLlmArchives[0];
    const stored = JSON.parse(await readFile(join(archiveProjectRoot, archive.relativePath), "utf8"));
    assert.equal(stored.runs, 1);
    assert.equal(stored.configuration.llmEvidenceMode, "strict_quarantine");
    assert.equal(stored.standings.length, 3);
    assert.ok(stored.experiment);
    assert.ok(stored.rng);
    assert.ok(stored.provenance);
    assert.doesNotThrow(() => normalizeSimulationReport(stored));
  } finally {
    await rm(archiveProjectRoot, { recursive: true, force: true });
  }
});

test("LLM prompt treatments are explicit, fingerprinted, and delivered by seat", async () => {
  const guidance =
    "Before choosing, identify how this decision converts current resources into Mandate and fulfill any promise whose legal window is open.";
  const baseOptions = {
    runs: 1,
    playerCount: 3,
    seed: "prompt-treatment-contract",
    sampleReplays: 0,
    profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
    backends: ["codex", "weighted", "weighted"],
    model: "fixture-model",
    reasoningEffort: "medium"
  };
  const baselineIdentity = await captureSimulationLaunchIdentity(baseOptions);
  const treatedOptions = {
    ...baseOptions,
    promptAddenda: [guidance, null, null]
  };
  const treatedIdentity = await captureSimulationLaunchIdentity(treatedOptions);
  assert.notEqual(
    treatedIdentity.strategies.fingerprint,
    baselineIdentity.strategies.fingerprint
  );

  let treatedPackets = 0;
  await createSimulation({
    ...treatedOptions,
    allowLlm: true,
    requireLlm: true,
    strictLlmEvidence: true,
    archiveLlmMatches: false,
    callerFactory: () => ({
      async decide(packet) {
        assert.ok(packet.strategy.objectives.includes(
          `Experimental decision guidance: ${guidance}`
        ));
        treatedPackets += 1;
        return {
          decision: { decisionId: packet.legalDecisions[0].decisionId },
          receipt: { provider: "fixture", requestId: packet.requestId }
        };
      }
    })
  });
  assert.ok(treatedPackets > 0);
});

test("faction comparisons can share a registered seed across treatment cells", async () => {
  const comparison = {
    focalSeat: 0,
    seedGroup: "shared-treatment-cell",
    leftFactionIds: [
      "coalition_lab",
      "vertical_empire",
      "foundry"
    ],
    rightFactionIds: [
      "safety_laboratory",
      "vertical_empire",
      "foundry"
    ]
  };
  const report = await runFactionSwapDiagnostic({
    runsPerArm: 1,
    playerCount: 3,
    seed: "shared-treatment-root",
    profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
    backends: ["weighted", "weighted", "weighted"],
    comparisons: [
      { ...comparison, id: "control", promptTreatmentId: "control" },
      { ...comparison, id: "replicate", promptTreatmentId: "replicate" }
    ]
  });
  assert.equal(report.comparisons[0].seedGroup, "shared-treatment-cell");
  assert.equal(report.comparisons[1].seedGroup, "shared-treatment-cell");
  assert.deepEqual(
    report.comparisons[0].paired.rows,
    report.comparisons[1].paired.rows
  );
});

test("paired deterministic policy treatments are fingerprinted and reported by arm", async () => {
  const base = {
    runs: 1,
    playerCount: 3,
    seed: "deterministic-treatment-identity",
    sampleReplays: 0,
    profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
    backends: ["greedy", "greedy", "greedy"],
    factionIds: ["coalition_lab", "vertical_empire", "foundry"],
    rotateProfiles: false,
    rotateFactions: false
  };
  const baselineIdentity = await captureSimulationLaunchIdentity(base);
  const treatedIdentity = await captureSimulationLaunchIdentity({
    ...base,
    policyTreatments: ["coalition_conversion_v1", null, null]
  });
  assert.notEqual(treatedIdentity.fingerprint, baselineIdentity.fingerprint);

  const report = await runFactionSwapDiagnostic({
    workers: 1,
    runsPerArm: 1,
    playerCount: 3,
    seed: "paired-deterministic-treatment",
    preRegistrationId: "paired-deterministic-treatment-test",
    projection: "batch",
    comparisons: [{
      id: "coalition_conversion_seat_0_greedy",
      focalSeat: 0,
      profileIds: base.profileIds,
      backends: base.backends,
      leftFactionIds: base.factionIds,
      rightFactionIds: base.factionIds,
      leftPolicyTreatments: ["coalition_conversion_v1", null, null],
      rightPolicyTreatments: [null, null, null]
    }]
  });
  const comparison = report.comparisons[0];
  assert.deepEqual(comparison.left.policyTreatments, [
    "coalition_conversion_v1",
    null,
    null
  ]);
  assert.deepEqual(comparison.right.policyTreatments, [null, null, null]);
  assert.equal(typeof comparison.paired.meanCausallyNecessaryCreditDelta, "number");
  assert.equal(typeof comparison.paired.meanAttributedMandateDelta, "number");
  assert.equal(report.execution.simulationWorkersPerTask, 1);
  assert.notEqual(
    report.launchIdentity.tasks[0].identity.fingerprint,
    report.launchIdentity.tasks[1].identity.fingerprint
  );
});

test("Coalition conversion matrices cover every comparator, seat, and backend", () => {
  const comparisons = expandCoalitionConversionMatrix({
    playerCount: 3,
    focalFactionId: "coalition_lab",
    comparatorFactionIds: [
      "platform_empire",
      "imperial_research_lab",
      "vertical_empire",
      "safety_laboratory",
      "foundry"
    ],
    focalSeats: [0, 1, 2],
    backends: ["greedy", "weighted"],
    opponentFactionCycle: [
      "platform_empire",
      "imperial_research_lab",
      "vertical_empire",
      "safety_laboratory",
      "foundry"
    ],
    focalProfileId: "balanced_operator",
    opponentProfileIds: ["capability_rusher", "trust_governor"]
  });
  assert.equal(comparisons.length, 30);
  assert.deepEqual(
    new Set(comparisons.map((comparison) => comparison.focalSeat)),
    new Set([0, 1, 2])
  );
  assert.deepEqual(
    new Set(comparisons.flatMap((comparison) => comparison.backends)),
    new Set(["greedy", "weighted"])
  );
  assert.ok(comparisons.every((comparison) =>
    comparison.leftFactionIds[comparison.focalSeat] === "coalition_lab" &&
    comparison.rightFactionIds[comparison.focalSeat] === "coalition_lab" &&
    comparison.leftPolicyTreatments[comparison.focalSeat] ===
      "coalition_conversion_v1" &&
    comparison.rightPolicyTreatments.every((treatment) => treatment === null) &&
    comparison.leftFactionIds.includes(comparison.comparatorId)
  ));
});

test("faction isolation matrices rotate every comparator through every focal seat", () => {
  const comparisons = expandFactionIsolationMatrix({
    focalFactionId: "coalition_lab",
    comparatorFactionIds: [
      "platform_empire",
      "imperial_research_lab",
      "vertical_empire",
      "safety_laboratory",
      "foundry"
    ],
    focalSeats: [0, 1, 2],
    policyArms: [
      { id: "baseline", leftPromptId: "coalition_baseline" },
      { id: "follow_through", leftPromptId: "coalition_follow_through" }
    ],
    opponentFactionCycle: [
      "platform_empire",
      "imperial_research_lab",
      "vertical_empire",
      "safety_laboratory",
      "foundry"
    ],
    focalProfileId: "balanced_operator",
    opponentProfileIds: ["capability_rusher", "trust_governor"],
    rightPromptIdsByFaction: {
      platform_empire: "platform_objective",
      imperial_research_lab: "imperial_objective",
      vertical_empire: "vertical_objective",
      safety_laboratory: "safety_objective",
      foundry: "foundry_objective"
    }
  });
  assert.equal(comparisons.length, 30);
  for (const factionId of [
    "platform_empire",
    "imperial_research_lab",
    "vertical_empire",
    "safety_laboratory",
    "foundry"
  ]) {
    const cells = comparisons.filter((entry) => entry.comparatorId === factionId);
    assert.deepEqual(new Set(cells.map((entry) => entry.focalSeat)), new Set([0, 1, 2]));
    assert.deepEqual(
      new Set(cells.map((entry) => entry.promptTreatmentId)),
      new Set(["baseline", "follow_through"])
    );
  }
  assert.ok(comparisons.every((entry) =>
    entry.leftFactionIds[entry.focalSeat] === "coalition_lab" &&
    entry.rightFactionIds[entry.focalSeat] === entry.comparatorId &&
    entry.backends[entry.focalSeat] === "codex"
  ));
});

test("paired faction arms receive their registered canonical prompt treatment", async () => {
  const seen = new Map();
  const promptLibrary = {
    coalition: "Use Coalition's canonical trading abilities.",
    safety: "Use Safety's canonical governance abilities."
  };
  const report = await runFactionSwapDiagnostic({
    archiveLlmMatches: false,
    workers: 2,
    llmConcurrency: 2,
    providerConcurrency: { codex: 2 },
    allowLlm: true,
    runsPerArm: 1,
    playerCount: 3,
    seed: "arm-prompt-treatment",
    promptLibrary,
    llmCallerFactory: () => ({
      async decide(packet) {
        const objectives = packet.strategy.objectives.join("\n");
        const expected = packet.factionId === "coalition_lab"
          ? promptLibrary.coalition
          : promptLibrary.safety;
        assert.match(objectives, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
        seen.set(packet.factionId, (seen.get(packet.factionId) || 0) + 1);
        return {
          decision: { decisionId: packet.legalDecisions[0].decisionId },
          receipt: { provider: "fixture", requestId: packet.requestId }
        };
      }
    }),
    comparisons: [{
      id: "arm-specific-prompts",
      focalSeat: 0,
      profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
      backends: ["codex", "weighted", "weighted"],
      leftPromptIds: ["coalition", null, null],
      rightPromptIds: ["safety", null, null],
      leftFactionIds: ["coalition_lab", "vertical_empire", "foundry"],
      rightFactionIds: ["safety_laboratory", "vertical_empire", "foundry"]
    }]
  });
  assert.ok(seen.get("coalition_lab") > 0);
  assert.ok(seen.get("safety_laboratory") > 0);
  assert.equal(report.comparisons[0].paired.pairs, 1);
  assert.notEqual(
    report.comparisons[0].left.strategiesFingerprint,
    report.comparisons[0].right.strategiesFingerprint
  );
});

test("simulation records two- and six-player games as exploratory non-promotional diagnostics", async () => {
  for (const playerCount of [2, 6]) {
    const report = await createSimulation({
      runs: 1,
      playerCount,
      sampleReplays: 0,
      seed: `exploratory-${playerCount}`
    });
    assert.equal(report.playerCount, playerCount);
    assert.equal(report.configuration.playerCountStatus, "exploratory_nonpromotional");
    assert.match(report.scope.id, new RegExp(`exploratory-${playerCount}p$`));
    assert.match(report.scope.verdictBoundary, /non-promotional diagnostic/);
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
  assert.equal(report.scope.id, "nineteen-hex-simplified-v1");
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
    backendId: "greedy",
    seed: "evolution-contract"
  });
  assert.equal(evolution.reportType, "strategy_evolution");
  assert.equal(evolution.history.length, 1);
  assert.equal(evolution.championProfile.id, "balanced_operator");
  assert.equal(evolution.backendId, "greedy");
  assert.equal(
    evolution.history[0].evaluationSeed,
    "evolution-contract:g:0:common"
  );

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
      /^evidence\/studies\/simulation\/20260726T130325621Z-tournament-0-1-0-aaaaaaaaaaaa-archive-contract-100x4-job-123\.json$/
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
  assert.equal(first.game.version, "0.14.3");
  assert.ok(!Object.hasOwn(first.game.files, "dist/docs/core-rules.md"));
  assert.equal(first.game.rulesetFingerprint, second.game.rulesetFingerprint);
  assert.equal(first.engine.fingerprint, second.engine.fingerprint);
  assert.equal(first.strategies.fingerprint, second.strategies.fingerprint);
  assert.notEqual(
    first.variant.fingerprint,
    fingerprintObject({ auditMultiplier: 0.8 })
  );
  const lowReasoning = await loadGameIdentity({
    profiles: profiles.slice(0, 2),
    backends: ["codex", "codex"],
    model: ["fixture-model", "fixture-model"],
    reasoningEffort: ["low", "low"]
  });
  const mediumReasoning = await loadGameIdentity({
    profiles: profiles.slice(0, 2),
    backends: ["codex", "codex"],
    model: ["fixture-model", "fixture-model"],
    reasoningEffort: ["medium", "medium"]
  });
  assert.notEqual(
    lowReasoning.strategies.fingerprint,
    mediumReasoning.strategies.fingerprint
  );
});

test("simulations validate a frozen launch identity before they run", async () => {
  const options = {
    runs: 1,
    playerCount: 3,
    seed: "launch-identity-contract",
    sampleReplays: 0,
    profileIds: ["balanced_operator", "balanced_operator", "balanced_operator"],
    backends: ["weighted", "weighted", "weighted"]
  };
  const launchIdentity = await captureSimulationLaunchIdentity(options);
  const report = await createSimulation({ ...options, launchIdentity });
  assert.deepEqual(report.launchIdentity, launchIdentity);

  const incompatible = structuredClone(launchIdentity);
  incompatible.strategies.backends = ["greedy", "greedy", "greedy"];
  const payload = structuredClone(incompatible);
  delete payload.fingerprint;
  incompatible.fingerprint = fingerprintObject(payload);
  await assert.rejects(
    () => createSimulation({ ...options, launchIdentity: incompatible }),
    (error) => error.code === "launch_identity_mismatch"
  );
});

test("batch projection exactly matches rich deterministic outcomes at three through five players", async () => {
  for (const playerCount of [3, 4, 5]) {
    const options = {
      runs: 2,
      playerCount,
      seed: `batch-parity-${playerCount}p`,
      sampleReplays: 2,
      includeObservations: true,
      profileIds: [
        "balanced_operator",
        "capability_rusher",
        "trust_governor",
        "power_broker",
        "agi_candidate"
      ],
      backends: ["weighted", "weighted", "weighted", "weighted", "weighted"],
      simulateNegotiation: true
    };
    const rich = await createSimulation({ ...options, projection: "rich" });
    const batch = await createSimulation({ ...options, projection: "batch" });
    for (const field of [
      "seats",
      "factions",
      "profiles",
      "backends",
      "factionStrategies",
      "factionBackends",
      "strategyBackends",
      "profileMatchups",
      "diagnostics",
      "matchMetrics",
      "samples",
      "observations"
    ]) {
      assert.deepEqual(batch[field], rich[field], `${playerCount}p ${field}`);
    }
    assert.equal(batch.configuration.projection, "batch");
    assert.notEqual(batch.launchIdentity.fingerprint, rich.launchIdentity.fingerprint);
  }
  await assert.rejects(
    () => createSimulation({
      runs: 1,
      playerCount: 3,
      projection: "batch",
      backends: ["codex", "weighted", "weighted"],
      allowLlm: true
    }),
    /Batch projection supports deterministic policies only/,
    "batch must not silently alter an LLM packet"
  );
});

test("parallel deterministic chunks restore batch outcomes in global run order", async () => {
  const options = {
    runs: 10,
    playerCount: 3,
    seed: "parallel-batch-parity",
    sampleReplays: 2,
    includeObservations: true,
    projection: "batch",
    chunkSize: 5,
    profileIds: ["balanced_operator", "capability_rusher", "trust_governor"],
    backends: ["weighted", "weighted", "weighted"],
    simulateNegotiation: true
  };
  const parallel = await createSimulation({ ...options, workers: 2 });
  const inline = await createSimulation({ ...options, workers: 1 });
  for (const field of [
    "seats",
    "factions",
    "profiles",
    "backends",
    "factionStrategies",
    "factionBackends",
    "strategyBackends",
    "profileMatchups",
    "diagnostics",
    "matchMetrics",
    "samples",
    "observations"
  ]) {
    assert.deepEqual(parallel[field], inline[field], field);
  }
  assert.deepEqual(parallel.configuration.execution, {
    scheduler: "worker_threads",
    requestedWorkers: 2,
    workers: 2,
    chunkSize: 5,
    chunks: 2
  });
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

test("incomplete schema-six match archives migrate from their recorded launch identity", () => {
  const archive = {
    schemaVersion: 6,
    reportSchemaVersion: 6,
    reportType: "tournament",
    evidenceLabel: "simulation",
    evidenceType: "simulation",
    generatedAt: "2026-08-01T00:00:00.000Z",
    seed: "historical-immediate-match",
    runs: 1,
    playerCount: 4,
    scope: { id: "selected-rules" },
    game: {},
    engine: {},
    variant: {},
    strategies: {},
    launchIdentity: {
      rng: { algorithm: "mulberry32", version: 1 },
      provenance: { sourceCommit: "recorded", sourceDirty: false }
    }
  };
  const migrated = normalizeSimulationReport(archive);
  assert.equal(migrated.experiment.fingerprint, null);
  assert.equal(migrated.rng.algorithm, "mulberry32");
  assert.equal(migrated.provenance.sourceCommit, "recorded");
  assert.equal(
    migrated.migration.attribution,
    "launch_identity_preserved_experiment_backfilled"
  );
  assert.equal(classifyReportComparison(migrated, migrated).classification, "incompatible");
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
