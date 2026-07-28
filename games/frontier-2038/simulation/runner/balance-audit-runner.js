import { evaluateAuditBalance, loadBalanceContract } from "../balance/balance-contract.js";
import { loadPlayerProfiles, validatePlayerProfile } from "../personas/player-profile.js";
import { mutateStrategy } from "./optimization-runner.js";
import { createSimulation } from "../runtime/create-simulation.js";
import { createReportIdentity } from "../versioning/game-identity.js";

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function profileResult(report, id) {
  return report.profiles.find((entry) => entry.profileId === id) || {
    winShare: 0,
    meanScore: 0,
    actionDiversity: 0
  };
}

function renamedMutation(source, id, seed, magnitude) {
  const profile = mutateStrategy(source, seed, { magnitude });
  profile.id = id;
  profile.name = `${source.name} (${id.replaceAll("_", " ")})`;
  return validatePlayerProfile(profile);
}

async function evaluateLineup({
  candidate,
  opponents,
  runs,
  seed,
  rulesVariant
}) {
  const lineup = [candidate, ...opponents].slice(0, 4);
  while (lineup.length < 4) lineup.push(opponents[lineup.length % opponents.length]);
  const report = await createSimulation({
    runs,
    playerCount: 4,
    seed,
    sampleReplays: 0,
    profileIds: lineup.map((entry) => entry.id),
    profileOverrides: [candidate, ...opponents],
    rotateProfiles: true,
    rotateFactions: true,
    backends: ["weighted"],
    rulesVariant
  });
  return {
    report,
    result: profileResult(report, candidate.id)
  };
}

function worstLeagueDiagnostics(reports) {
  const pick = (path, reducer, fallback) => {
    const values = reports.map((report) =>
      path.reduce((value, key) => value?.[key], report.diagnostics)
    ).filter(Number.isFinite);
    return values.length ? reducer(...values) : fallback;
  };
  return {
    seatWinShareRange: pick(["seatWinShareRange"], Math.max, 1),
    factionWinShareRange: pick(["factionWinShareRange"], Math.max, 1),
    profileWinShareRange: pick(["profileWinShareRange"], Math.max, 1),
    actionDiversity: pick(["actionDiversity"], Math.min, 0),
    openingDiversity: {
      entropy: pick(["openingDiversity", "entropy"], Math.min, 0),
      topShare: pick(["openingDiversity", "topShare"], Math.max, 1)
    },
    winningPathDiversity: {
      entropy: pick(["winningPathDiversity", "entropy"], Math.min, 0),
      topShare: pick(["winningPathDiversity", "topShare"], Math.max, 1)
    },
    factionStrategyInteractionRange: pick(["factionStrategyInteractionRange"], Math.max, 1),
    leaderPredictability: {
      round2: pick(["leaderPredictability", "round2"], Math.max, 1)
    },
    pairwiseDominance: pick(["pairwiseDominance"], Math.max, 1),
    integrity: {
      violations: reports.reduce((sum, report) =>
        sum + (report.diagnostics.integrity?.violations || 0), 0),
      policyFallbacks: reports.reduce((sum, report) =>
        sum + (report.diagnostics.integrity?.policyFallbacks || 0), 0)
    }
  };
}

export async function runBalanceAudit({
  runsPerMatchup = 8,
  generations = 2,
  population = 3,
  seed = "m3t4-balance-audit",
  magnitude = 0.45,
  rulesVariant,
  onProgress
} = {}) {
  const profiles = await loadPlayerProfiles();
  const contract = await loadBalanceContract();
  const pairs = [];
  for (let left = 0; left < profiles.length; left += 1) {
    for (let right = left + 1; right < profiles.length; right += 1) {
      pairs.push([profiles[left], profiles[right]]);
    }
  }
  const total = pairs.length + profiles.length * generations * population * 2 +
    profiles.length * 3;
  let completed = 0;
  const leagueReports = [];
  const matchups = [];
  for (const [left, right] of pairs) {
    const report = await createSimulation({
      runs: runsPerMatchup,
      playerCount: 4,
      seed: `${seed}:league:${left.id}:${right.id}`,
      sampleReplays: 0,
      profileIds: [left.id, right.id, left.id, right.id],
      rotateProfiles: true,
      rotateFactions: true,
      backends: ["weighted"],
      rulesVariant
    });
    leagueReports.push(report);
    matchups.push({
      left: left.id,
      right: right.id,
      runs: runsPerMatchup,
      leftWinShare: profileResult(report, left.id).winShare,
      rightWinShare: profileResult(report, right.id).winShare,
      relativePlacement: report.profileMatchups
        .find((entry) => entry.profileId === left.id && entry.opponentProfileId === right.id)
        ?.relativePlacementRate ?? null
    });
    completed += 1;
    onProgress?.({ phase: "matchup_league", completed, total });
  }

  const aggregate = {
    diagnostics: worstLeagueDiagnostics(leagueReports)
  };
  const { evaluateTournamentBalance } = await import("../balance/balance-contract.js");
  const leagueEvaluation = evaluateTournamentBalance(aggregate, contract);
  const adversarialRows = [];
  for (const [targetIndex, target] of profiles.entries()) {
    const source = profiles.find((entry) => entry.id !== target.id);
    const holdouts = profiles.filter((entry) =>
      entry.id !== target.id && entry.id !== source.id
    ).slice(targetIndex % 3, targetIndex % 3 + 2);
    const trainingOpponents = [target, ...holdouts];
    const baseline = await evaluateLineup({
      candidate: source,
      opponents: trainingOpponents,
      runs: runsPerMatchup,
      seed: `${seed}:response:${target.id}:common`,
      rulesVariant
    });
    completed += 1;
    onProgress?.({ phase: "best_response", completed, total });
    let incumbent = source;
    let incumbentEvaluation = baseline;
    for (let generation = 0; generation < generations; generation += 1) {
      const candidates = [
        incumbent,
        ...Array.from({ length: population - 1 }, (_, index) =>
          renamedMutation(
            incumbent,
            `response_${targetIndex}_${generation}_${index}`,
            `${seed}:response:${target.id}:${generation}:${index}`,
            magnitude
          )
        )
      ];
      for (const [index, candidate] of candidates.entries()) {
        const evaluation = await evaluateLineup({
          candidate,
          opponents: trainingOpponents,
          runs: runsPerMatchup,
          seed: `${seed}:response:${target.id}:common`,
          rulesVariant
        });
        if (
          evaluation.result.winShare > incumbentEvaluation.result.winShare ||
          (
            evaluation.result.winShare === incumbentEvaluation.result.winShare &&
            evaluation.result.meanScore > incumbentEvaluation.result.meanScore
          )
        ) {
          incumbent = candidate;
          incumbentEvaluation = evaluation;
        }
        completed += 1;
        onProgress?.({ phase: "best_response", completed, total });
      }
    }
    const targetBaseline = await evaluateLineup({
      candidate: target,
      opponents: [incumbent, ...holdouts],
      runs: runsPerMatchup,
      seed: `${seed}:counter:${target.id}:common`,
      rulesVariant
    });
    completed += 1;
    let counter = target;
    let counterEvaluation = targetBaseline;
    for (let generation = 0; generation < generations; generation += 1) {
      const candidates = [
        counter,
        ...Array.from({ length: population - 1 }, (_, index) =>
          renamedMutation(
            counter,
            `counter_${targetIndex}_${generation}_${index}`,
            `${seed}:counter:${target.id}:${generation}:${index}`,
            magnitude
          )
        )
      ];
      for (const candidate of candidates) {
        const evaluation = await evaluateLineup({
          candidate,
          opponents: [incumbent, ...holdouts],
          runs: runsPerMatchup,
          seed: `${seed}:counter:${target.id}:common`,
          rulesVariant
        });
        if (evaluation.result.winShare > counterEvaluation.result.winShare) {
          counter = candidate;
          counterEvaluation = evaluation;
        }
        completed += 1;
        onProgress?.({ phase: "counter_response", completed, total });
      }
    }
    const holdout = await evaluateLineup({
      candidate: incumbent,
      opponents: [...holdouts, profiles[(targetIndex + 3) % profiles.length]],
      runs: runsPerMatchup,
      seed: `${seed}:holdout:${target.id}`,
      rulesVariant
    });
    completed += 1;
    onProgress?.({ phase: "holdout", completed, total });
    adversarialRows.push({
      targetProfileId: target.id,
      sourceProfileId: source.id,
      bestResponseProfile: incumbent,
      baselineWinShare: baseline.result.winShare,
      bestResponseWinShare: incumbentEvaluation.result.winShare,
      bestResponseGain: incumbentEvaluation.result.winShare - baseline.result.winShare,
      targetBaselineWinShare: targetBaseline.result.winShare,
      counterProfile: counter,
      counterWinShare: counterEvaluation.result.winShare,
      counterRecovery: counterEvaluation.result.winShare - targetBaseline.result.winShare,
      holdoutProfileIds: holdouts.map((entry) => entry.id),
      holdoutWinShare: holdout.result.winShare,
      holdoutCollapse: Math.max(
        0,
        incumbentEvaluation.result.winShare - holdout.result.winShare
      )
    });
  }

  const report = {
    reportType: "balance_audit",
    evidenceLabel: "simulation",
    generatedAt: new Date().toISOString(),
    seed: String(seed),
    playerCount: 4,
    runsPerMatchup,
    generations,
    population,
    scope: {
      id: "strategic-unsolvability-audit-v1",
      verdictBoundary: "Automated falsification evidence only; it cannot prove mathematical hardness, human fun, or optimal play."
    },
    design: {
      profileCount: profiles.length,
      expectedPairs: pairs.length,
      observedPairs: matchups.length,
      seatRotation: true,
      factionRotation: true,
      commonSeeds: true
    },
    league: {
      coverage: matchups.length / pairs.length,
      diagnostics: aggregate.diagnostics,
      matchups,
      evaluation: leagueEvaluation
    },
    adversarial: {
      profiles: adversarialRows,
      maxBestResponseGain: Math.max(...adversarialRows.map((entry) => entry.bestResponseGain)),
      minCounterRecovery: Math.min(...adversarialRows.map((entry) => entry.counterRecovery)),
      maxHoldoutCollapse: Math.max(...adversarialRows.map((entry) => entry.holdoutCollapse))
    },
    balanceContract: {
      id: contract.id,
      status: contract.status,
      fingerprint: contract.fingerprint,
      provenance: contract.provenance
    }
  };
  report.balanceEvaluation = evaluateAuditBalance(report, contract);
  return createReportIdentity({
    report,
    rulesVariant: rulesVariant || {},
    variantOverlay: rulesVariant,
    profiles,
    backends: ["weighted"],
    model: null,
    experimentKind: "balance_audit"
  });
}
