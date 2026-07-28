import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  alphaSpentAtLook,
  empiricalBayesRates,
  intervalCrossesThreshold
} from "../simulation/statistics/sequential-inference.js";
import { runUnifiedMatrix } from "../simulation/runner/unified-matrix-runner.js";
import { runLlmNegotiationHoldout } from "../simulation/runner/llm-holdout-runner.js";
import { loadPlayerProfiles } from "../simulation/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../simulation/policies/weighted-policy.js";

test("sequential inference shrinks sparse extremes and spends less alpha at later looks", () => {
  assert.ok(
    alphaSpentAtLook({ look: 2 }) <
    alphaSpentAtLook({ look: 1 })
  );
  const family = empiricalBayesRates([
    { id: "thin", success: 1, exposure: 1 },
    { id: "deep", success: 45, exposure: 100 }
  ]);
  const thin = family.cells.find((cell) => cell.id === "thin");
  assert.ok(thin.posteriorMean < 1);
  assert.equal(intervalCrossesThreshold(thin, {
    operator: "max",
    threshold: 0.7,
    minimumExposure: 24
  }), false);
});

test("matrix contract declares all seven factors independently", async () => {
  const contract = JSON.parse(await readFile(
    new URL("../simulation/contracts/experiment-matrix.json", import.meta.url),
    "utf8"
  ));
  assert.deepEqual(Object.keys(contract.axes), [
    "rulesConfiguration",
    "playerCount",
    "factionAndSeat",
    "strategyRoster",
    "randomSeed",
    "mandateMode",
    "decisionBackend"
  ]);
  assert.deepEqual(contract.axes.playerCount, [3, 4, 5]);
  assert.equal(contract.playerCountPolicy.balanceAuthority, 4);
  assert.deepEqual(contract.playerCountPolicy.regressionGuards, [3, 5]);
});

test("unified matrix rotates homogeneous and alternating backend regimes and never auto-promotes", async () => {
  const report = await runUnifiedMatrix({
    maximumMatches: 36,
    initialRunsPerCell: 1,
    batchSize: 2,
    playerCounts: [4],
    mandateModes: ["fixed"],
    includeAdversarial: false,
    seed: "unified-matrix-contract"
  });
  assert.equal(report.reportType, "unified_matrix_audit");
  assert.equal(report.runs, 36);
  assert.deepEqual(
    new Set(report.design.cells.flatMap((cell) => cell.backends)),
    new Set(["weighted", "greedy"])
  );
  assert.deepEqual(
    new Set(report.design.cells.map((cell) => cell.backendRegime)),
    new Set([
      "homogeneous_weighted",
      "homogeneous_greedy",
      "alternating_weighted_first",
      "alternating_greedy_first"
    ])
  );
  assert.ok(report.inference.families.strategyBackendRegime.cells.length > 0);
  assert.ok(report.inference.families.seatBackendRegime.cells.length > 0);
  assert.ok(report.inference.pairwise.cells.every((cell) =>
    typeof cell.dimensions.backendRegime === "string"
  ));
  assert.ok(Array.isArray(report.balanceEvaluation.diagnosticDominance));
  assert.ok(Array.isArray(report.balanceEvaluation.diagnosticPairwiseDominance));
  assert.ok(report.inference.families.backend.cells.length > 0);
  assert.ok(report.inference.pairwise.cells.length > 0);
  assert.equal(report.playerCountResults[4].matches, 36);
  assert.equal(
    typeof report.playerCountResults[4].outcomes.factionAbilityValues,
    "object"
  );
  assert.equal(
    report.playerCountResults[4].outcomes.agiFunnel.playerOpportunities,
    36 * 4
  );
  assert.equal(report.balanceEvaluation.promotionGate.eligible, false);
  assert.equal(
    report.balanceEvaluation.status,
    "incomplete_supported_player_count_coverage"
  );
  assert.deepEqual(report.supportedPlayerCountCoverage, {
    3: 0,
    4: 36,
    5: 0
  });
  assert.equal(report.adversarial.status, "not_run");
});

test("unified matrix rejects player counts outside the supported product", async () => {
  await assert.rejects(
    runUnifiedMatrix({
      maximumMatches: 36,
      initialRunsPerCell: 1,
      batchSize: 1,
      playerCounts: [2, 4],
      mandateModes: ["fixed"],
      includeAdversarial: false,
      seed: "unsupported-player-count"
    }),
    /must be supported: 3, 4, 5/
  );
});

test("one-lever matrices preserve rules arms in inference and common-seed pairs", async () => {
  const report = await runUnifiedMatrix({
    maximumMatches: 56,
    initialRunsPerCell: 1,
    batchSize: 1,
    playerCounts: [4],
    mandateModes: ["fixed"],
    rulesConfigurations: [
      { id: "canonical", overlay: {} },
      { id: "probe", overlay: { foundryStartingCompute: 3 } }
    ],
    includeAdversarial: false,
    seed: "unified-matrix-paired-contract"
  });
  const pairs = new Map();
  for (const cell of report.design.cells) {
    const ids = pairs.get(cell.pairingId) || [];
    ids.push(cell.rulesConfigurationId);
    pairs.set(cell.pairingId, ids);
  }
  assert.ok([...pairs.values()].every((ids) =>
    new Set(ids).size === 2
  ));
  assert.deepEqual(
    new Set(report.inference.families.faction.cells.map((cell) =>
      cell.dimensions.rulesConfigurationId
    )),
    new Set(["canonical", "probe"])
  );
  assert.equal(report.configurationResults.canonical.matches, 28);
  assert.equal(report.configurationResults.probe.matches, 28);
  assert.equal(
    report.configurationResults.canonical.playerCountResults[4].matches,
    28
  );
  assert.equal(
    typeof report.configurationResults.canonical.outcomes.factionMandateSources,
    "object"
  );
  assert.ok(
    Object.values(
      report.configurationResults.canonical.outcomes.factionStandings
    ).some((standing) => standing.appearances > 0)
  );
  assert.ok(
    Object.values(
      report.configurationResults.canonical.playerCountResults[4].outcomes
        .factionStandings
    ).some((standing) => standing.appearances > 0)
  );
  assert.equal(report.rulesComparisons[0].matchedPairs, 28);
  assert.equal(report.rulesComparisons[0].unmatchedPairs, 0);
  assert.equal(report.rulesComparisons[0].standingMismatches, 0);
  assert.ok(report.rulesComparisons[0].families.faction.every((cell) =>
    Number.isFinite(cell.rankDelta)
  ));
  assert.match(
    report.rulesComparisons[0].interpretation,
    /positive rankDelta means the candidate improved placement/
  );
  assert.equal(report.integrity.violations, 0);
});

test("unified matrix fingerprints and executes evolved profile overrides", async () => {
  const profiles = await loadPlayerProfiles();
  const override = structuredClone(
    profiles.find((profile) => profile.id === "trust_governor")
  );
  override.strategy.actionWeights.influence = 7.25;
  override.provenance = {
    kind: "test_strategy_override",
    parentId: override.id,
    seed: "override-fixture"
  };
  const report = await runUnifiedMatrix({
    maximumMatches: 142,
    initialRunsPerCell: 1,
    batchSize: 1,
    playerCounts: [4],
    mandateModes: ["fixed"],
    includeAdversarial: false,
    profileOverrides: [override],
    seed: "profile-override-matrix-fixture"
  });
  const registered = report.preRegistration.profiles.find(
    (profile) => profile.id === "trust_governor"
  );
  assert.equal(registered.provenance.kind, "test_strategy_override");
  assert.match(registered.fingerprint, /^sha256:/);
  assert.equal(report.integrity.violations, 0);
});

test("deterministic negotiators can rationally fulfill or break a promise", async () => {
  const base = structuredClone((await loadPlayerProfiles())[0]);
  const packet = {
    schemaVersion: 1,
    requestId: "negotiation-fixture:r3:c1:s0:power_sale_1_0",
    matchId: "negotiation-fixture",
    seed: "negotiation-fixture",
    seat: 0,
    factionId: "coalition_lab",
    round: 3,
    cycle: 1,
    observation: {},
    publicHistory: [],
    legalDecisions: [
      {
        decisionId: "power_sale_accept_1_0",
        label: "Accept",
        actionId: "production",
        consequences: { promiseFulfillment: 1 }
      },
      {
        decisionId: "power_sale_reject_1_0",
        label: "Reject",
        actionId: "production",
        consequences: { promiseBetrayal: 1 }
      }
    ]
  };
  base.strategy.negotiation.fulfillWeight = 4;
  base.strategy.negotiation.betrayWeight = 0.1;
  assert.equal(
    (await new WeightedPlayerPolicy(base, { selection: "greedy" }).decide(packet))
      .decision.decisionId,
    "power_sale_accept_1_0"
  );
  base.strategy.negotiation.fulfillWeight = 0.1;
  base.strategy.negotiation.betrayWeight = 4;
  assert.equal(
    (await new WeightedPlayerPolicy(base, { selection: "greedy" }).decide(packet))
      .decision.decisionId,
    "power_sale_reject_1_0"
  );
});

test("LLM holdout cannot run without explicit authorization", async () => {
  await assert.rejects(
    () => runLlmNegotiationHoldout({
      preRegistrationPath:
        "studies/simulation/preregistrations/llm-negotiation-holdout.json"
    }),
    /explicit allowLlm/
  );
});
