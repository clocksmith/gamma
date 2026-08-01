import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  alphaSpentAtLook,
  empiricalBayesRates,
  intervalCrossesThreshold
} from "../lab/statistics/sequential-inference.js";
import {
  configurationOutcomeBalanceChecks,
  runUnifiedMatrix
} from "../lab/runner/unified-matrix-runner.js";
import {
  runLlmNegotiationHoldout,
  validateLlmHoldoutRegistration
} from "../lab/runner/llm-holdout-runner.js";
import { loadPlayerProfiles } from "../lab/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";

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
    new URL("../lab/contracts/experiment-matrix.json", import.meta.url),
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

test("unified balance checks enforce faction and diversity bounds per candidate count", () => {
  const outcomes = {
    factionStandings: {
      a: { appearances: 10, winShare: 0.4 },
      b: { appearances: 10, winShare: 0.2 }
    },
    actionDiversity: 0.9,
    openingDiversity: { entropy: 0.7, topShare: 0.2 },
    winningPathDiversity: { entropy: 0.5, topShare: 0.51 },
    policyFallbacks: 0,
    forcedNoOpRate: 0.01
  };
  const checks = configurationOutcomeBalanceChecks({
    configurationResults: {
      candidate: {
        playerCountResults: {
          4: { outcomes }
        }
      }
    },
    configurationIds: ["candidate"],
    playerCounts: [4],
    thresholds: {
      factionWinShareRangeMax: 0.15,
      actionEntropyMin: 0.72,
      openingEntropyMin: 0.65,
      openingTopShareMax: 0.3,
      winningPathEntropyMin: 0.6,
      winningPathTopShareMax: 0.55,
      policyFallbacksMax: 0,
      forcedNoOpRateMax: 0.03
    }
  });
  assert.equal(checks.length, 8);
  assert.deepEqual(
    checks.filter((entry) => !entry.passed).map((entry) => entry.id),
    [
      "candidate:p4:faction_win_share_range",
      "candidate:p4:winning_path_entropy"
    ]
  );
  assert.ok(checks.every((entry) =>
    entry.configurationId === "candidate" && entry.playerCount === 4
  ));
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
  assert.deepEqual(report.execution, {
    projection: "batch",
    requestedWorkers: null,
    configuredWorkers: report.execution.configuredWorkers,
    initialCellWorkers: report.execution.initialCellWorkers,
    scheduler: report.execution.initialCellWorkers > 1 ? "worker_threads" : "inline",
    chunkSize: null,
    resultOrder: "matrix_cell_then_match_index"
  });
  assert.match(report.launchIdentity.study.fingerprint, /^sha256:/);
  assert.equal(report.launchIdentity.cells.length, report.design.cells.length);
  assert.ok(report.launchIdentity.cells.every(({ identity }) =>
    identity.provenance.sourceCommit === report.launchIdentity.study.provenance.sourceCommit &&
    identity.provenance.sourceDirty === report.launchIdentity.study.provenance.sourceDirty
  ));
  assert.ok(report.launchIdentity.cells.every(({ identity }) =>
    /^sha256:/.test(identity.fingerprint)
  ));
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
  assert.ok(report.playerCountResults[4].outcomes.actionDiversity > 0);
  assert.ok(report.playerCountResults[4].outcomes.openingDiversity.observed > 1);
  assert.ok(report.playerCountResults[4].outcomes.winningPathDiversity.observed > 1);
  assert.deepEqual(
    report.playerCountResults[4].outcomes.winningPathClassifier,
    { id: "lane-margin-v1", hybridMargin: 1 }
  );
  const pathMargins = report.playerCountResults[4].outcomes.winningPathMargins;
  assert.equal(pathMargins.wins, report.playerCountResults[4].matches);
  assert.ok(pathMargins.meanGap >= 0);
  assert.ok(pathMargins.exactTieShare <= pathMargins.withinHalfPointShare);
  assert.ok(pathMargins.withinHalfPointShare <= pathMargins.withinOnePointShare);
  assert.ok(pathMargins.withinOnePointShare <= pathMargins.withinTwoPointsShare);
  assert.ok(Object.keys(pathMargins.primarySecondary).length > 1);
  assert.ok(Object.hasOwn(pathMargins.byProfile, "trust_governor"));
  const pathAttribution =
    report.playerCountResults[4].outcomes.winningPathAttribution;
  assert.deepEqual(
    new Set(Object.keys(pathAttribution)),
    new Set(Object.keys(
      report.playerCountResults[4].outcomes.winningPathDiversity.counts
    ))
  );
  assert.ok(Object.values(pathAttribution).every((path) =>
    path.wins > 0 &&
    Number.isFinite(path.meanMandate) &&
    typeof path.mandateSources === "object" &&
    typeof path.actionSelections === "object" &&
    typeof path.factions === "object" &&
    typeof path.profiles === "object"
  ));
  assert.ok(
    Math.abs(
      Object.values(pathAttribution).reduce(
        (sum, path) => sum + path.share,
        0
      ) - 1
    ) < 1e-9
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

test("unified matrix cell workers preserve deterministic evidence order", async () => {
  const options = {
    maximumMatches: 36,
    initialRunsPerCell: 1,
    batchSize: 2,
    playerCounts: [4],
    mandateModes: ["fixed"],
    includeAdversarial: false,
    projection: "batch",
    seed: "unified-matrix-worker-parity"
  };
  const inline = await runUnifiedMatrix({ ...options, workers: 1 });
  const parallel = await runUnifiedMatrix({ ...options, workers: 2 });
  for (const field of [
    "outcomes",
    "cooperation",
    "configurationResults",
    "playerCountResults",
    "supportedPlayerCountCoverage",
    "rulesComparisons",
    "integrity",
    "balanceEvaluation"
  ]) {
    assert.deepEqual(parallel[field], inline[field], field);
  }
  assert.equal(inline.execution.scheduler, "inline");
  assert.equal(parallel.execution.scheduler, "worker_threads");
  assert.equal(parallel.execution.initialCellWorkers, 2);
  assert.equal(parallel.design.allocations.length, inline.design.allocations.length);
  assert.deepEqual(
    parallel.design.allocations.map(({ elapsedMs, ...allocation }) => allocation),
    inline.design.allocations.map(({ elapsedMs, ...allocation }) => allocation)
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
      {
        id: "probe",
        overlay: {
          foundryNewArchitectureDemandCoupling: {
            baseCompute: 1,
            computePerLicense: 1,
            maximumCompute: 3
          }
        }
      }
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
  assert.ok(
    report.rulesComparisons[0].families
      .factionBackendPlayerCountMandateMode.every((cell) =>
        cell.dimensions.playerCount === 4 &&
        cell.dimensions.mandateMode === "fixed" &&
        typeof cell.dimensions.factionId === "string" &&
        typeof cell.dimensions.backendId === "string"
      )
  );
  assert.match(
    report.rulesComparisons[0].interpretation,
    /positive rankDelta means the candidate improved placement/
  );
  assert.equal(report.integrity.violations, 0);
});

test("package interaction matrices require and record multiple selected levers", async () => {
  const packageOverlay = {
    verticalIndustrialVelocityMandate: 1,
    foundryNewArchitectureDemandCoupling: {
      baseCompute: 0,
      computePerLicense: 1,
      maximumCompute: 3
    }
  };
  await assert.rejects(
    runUnifiedMatrix({
      maximumMatches: 56,
      initialRunsPerCell: 1,
      batchSize: 1,
      playerCounts: [4],
      mandateModes: ["fixed"],
      rulesConfigurations: [
        { id: "canonical", overlay: {} },
        { id: "unregistered_package", overlay: packageOverlay }
      ],
      includeAdversarial: false,
      seed: "package-needs-explicit-kind"
    }),
    /must change exactly one lever/
  );
  const report = await runUnifiedMatrix({
    maximumMatches: 56,
    initialRunsPerCell: 1,
    batchSize: 1,
    playerCounts: [4],
    mandateModes: ["fixed"],
    comparisonKind: "package_interaction",
    rulesConfigurations: [
      { id: "canonical", overlay: {} },
      { id: "selected_package", overlay: packageOverlay }
    ],
    includeAdversarial: false,
    seed: "package-interaction-contract"
  });
  assert.equal(report.preRegistration.comparisonKind, "package_interaction");
  assert.equal(report.rulesComparisons[0].matchedPairs, 28);
  assert.equal(report.rulesComparisons[0].standingMismatches, 0);
  assert.match(
    report.rulesComparisons[0].interpretation,
    /interaction of independently selected levers/
  );
  assert.ok(report.balanceEvaluation.checks.some((entry) =>
    entry.id === "selected_package:p4:faction_win_share_range"
  ));
  assert.ok(report.balanceEvaluation.checks.some((entry) =>
    entry.id === "selected_package:p4:winning_path_entropy"
  ));
  assert.ok(report.balanceEvaluation.checks.every((entry) =>
    !entry.configurationId || entry.configurationId !== "canonical"
  ));
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
        "evidence/studies/simulation/preregistrations/llm-negotiation-holdout.json"
    }),
    /explicit allowLlm/
  );
});

test("strict LLM holdouts permit full-seat authority without an arbitrary decision cap", () => {
  const registration = validateLlmHoldoutRegistration({
    schemaVersion: 1,
    id: "full-seat-fixture",
    locked: true,
    purpose: "fresh_robustness",
    seed: "full-seat-fixture",
    runs: 1,
    playerCount: 3,
    profileIds: ["agi_candidate", "power_broker", "trust_governor"],
    backends: ["codex", "weighted", "weighted"],
    model: "fixture-model",
    reasoningEffort: "medium",
    llmStages: null,
    maximumLlmDecisions: null,
    analysis: {
      primaryOutcome: "fixture",
      secondaryOutcomes: [],
      interpretationBoundary: "fixture"
    }
  });
  assert.equal(registration.llmStages, null);
  assert.equal(registration.maximumLlmDecisions, null);
  assert.equal(registration.reasoningEffort, "medium");
});
