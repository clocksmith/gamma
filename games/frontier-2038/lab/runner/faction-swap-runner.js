import { createSimulation } from "../runtime/create-simulation.js";
import { fingerprintObject } from "../versioning/game-identity.js";

function mean(values) {
  return values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
}

function winCredit(observation, seat) {
  return observation.winnerSeats.includes(seat)
    ? 1 / observation.winnerSeats.length
    : 0;
}

function standingAt(observation, seat) {
  const ordered = [...observation.standings].sort(
    (left, right) =>
      right.score - left.score ||
      right.trust - left.trust ||
      right.customers - left.customers ||
      right.compute - left.compute ||
      left.seat - right.seat
  );
  const standing = ordered.find((entry) => entry.seat === seat);
  return {
    ...standing,
    rank: ordered.findIndex((entry) => entry.seat === seat) + 1
  };
}

function validateComparison(comparison, playerCount) {
  for (const key of ["id", "leftFactionIds", "rightFactionIds"]) {
    if (!comparison[key]) throw new TypeError(`Faction comparison requires ${key}.`);
  }
  for (const key of ["leftFactionIds", "rightFactionIds"]) {
    if (comparison[key].length !== playerCount) {
      throw new RangeError(`${comparison.id} ${key} must contain ${playerCount} factions.`);
    }
  }
  const focalSeat = Number(comparison.focalSeat ?? 0);
  if (!Number.isInteger(focalSeat) || focalSeat < 0 || focalSeat >= playerCount) {
    throw new RangeError(`${comparison.id} has an invalid focalSeat.`);
  }
  return focalSeat;
}

function summarizePair(left, right, focalSeat) {
  if (left.observations.length !== right.observations.length) {
    throw new Error("Paired faction arms produced different observation counts.");
  }
  const rows = left.observations.map((leftObservation, index) => {
    const rightObservation = right.observations[index];
    const leftStanding = standingAt(leftObservation, focalSeat);
    const rightStanding = standingAt(rightObservation, focalSeat);
    return {
      matchIndex: index,
      scoreDelta: leftStanding.score - rightStanding.score,
      rankAdvantage: rightStanding.rank - leftStanding.rank,
      winCreditDelta:
        winCredit(leftObservation, focalSeat) -
        winCredit(rightObservation, focalSeat)
    };
  });
  return {
    pairs: rows.length,
    leftWinRate: mean(left.observations.map((observation) =>
      winCredit(observation, focalSeat)
    )),
    rightWinRate: mean(right.observations.map((observation) =>
      winCredit(observation, focalSeat)
    )),
    meanWinRateDelta: mean(rows.map((row) => row.winCreditDelta)),
    meanMandateDelta: mean(rows.map((row) => row.scoreDelta)),
    meanRankAdvantage: mean(rows.map((row) => row.rankAdvantage)),
    rows
  };
}

export async function runFactionSwapDiagnostic(options = {}, onProgress) {
  const comparisons = options.comparisons || [];
  if (!comparisons.length) throw new RangeError("At least one faction comparison is required.");
  const playerCount = Number(options.playerCount || 4);
  const runsPerArm = Number(options.runsPerArm || 100);
  if (!Number.isInteger(runsPerArm) || runsPerArm < 1 || runsPerArm > 10000) {
    throw new RangeError("runsPerArm must be an integer from 1 to 10000.");
  }
  const rootSeed = String(options.seed || "m3t4-faction-swap");
  const results = [];
  let identityReport = null;
  let completed = 0;
  for (const comparison of comparisons) {
    const focalSeat = validateComparison(comparison, playerCount);
    const common = {
      runs: runsPerArm,
      playerCount,
      seed: `${rootSeed}:${comparison.id}`,
      sampleReplays: 0,
      profileIds: comparison.profileIds || options.profileIds,
      backends: comparison.backends || options.backends,
      rotateProfiles: false,
      rotateFactions: false,
      mandateMode: options.mandateMode || "variable",
      rulesVariant: options.rulesVariant || {},
      simulateNegotiation: true,
      includeObservations: true,
      experimentKind: "balance_audit"
    };
    const left = await createSimulation({
      ...common,
      factionIds: comparison.leftFactionIds
    });
    identityReport ||= left;
    completed += runsPerArm;
    onProgress?.({ completed, total: comparisons.length * runsPerArm * 2 });
    const right = await createSimulation({
      ...common,
      factionIds: comparison.rightFactionIds
    });
    completed += runsPerArm;
    onProgress?.({ completed, total: comparisons.length * runsPerArm * 2 });
    results.push({
      id: comparison.id,
      question: comparison.question || null,
      focalSeat,
      left: {
        factionId: comparison.leftFactionIds[focalSeat],
        factionIds: comparison.leftFactionIds,
        strategiesFingerprint: left.strategies.fingerprint,
        abilityValues: left.matchMetrics.factionAbilityValues[
          comparison.leftFactionIds[focalSeat]
        ] || {}
      },
      right: {
        factionId: comparison.rightFactionIds[focalSeat],
        factionIds: comparison.rightFactionIds,
        strategiesFingerprint: right.strategies.fingerprint,
        abilityValues: right.matchMetrics.factionAbilityValues[
          comparison.rightFactionIds[focalSeat]
        ] || {}
      },
      paired: summarizePair(left, right, focalSeat)
    });
  }
  const preRegistration = {
    id: options.preRegistrationId || "unregistered-faction-swap",
    lockedBeforeResults: Boolean(options.preRegistrationId),
    rootSeed,
    runsPerArm,
    playerCount,
    mandateMode: options.mandateMode || "variable",
    rulesVariant: options.rulesVariant || {},
    profileIds: options.profileIds,
    backends: options.backends,
    comparisons
  };
  preRegistration.fingerprint = fingerprintObject(preRegistration);
  return {
    schemaVersion: 6,
    reportSchemaVersion: 6,
    replaySchemaVersion: 2,
    decisionSchemaVersion: 2,
    reportType: "balance_audit",
    diagnosticKind: "paired_faction_swap",
    evidenceLabel: "simulation",
    evidenceType: "simulation",
    generatedAt: new Date().toISOString(),
    seed: rootSeed,
    runs: comparisons.length * runsPerArm * 2,
    runsPerArm,
    playerCount,
    game: identityReport.game,
    engine: identityReport.engine,
    variant: identityReport.variant,
    strategies: {
      ...identityReport.strategies,
      configurations: comparisons.map((comparison) => ({
        id: comparison.id,
        profileIds: comparison.profileIds || options.profileIds,
        backends: comparison.backends || options.backends
      })),
      fingerprint: fingerprintObject(comparisons.map((comparison) => ({
        id: comparison.id,
        profileIds: comparison.profileIds || options.profileIds,
        backends: comparison.backends || options.backends
      })))
    },
    experiment: {
      reportType: "balance_audit",
      seed: rootSeed,
      playerCount,
      runs: comparisons.length * runsPerArm * 2,
      preRegistrationFingerprint: preRegistration.fingerprint,
      fingerprint: fingerprintObject(preRegistration)
    },
    rng: identityReport.rng,
    provenance: identityReport.provenance,
    balanceContract: identityReport.balanceContract,
    balanceEvaluation: {
      contractId: identityReport.balanceContract.id,
      status: "diagnostic_only",
      checks: [],
      promotionGate: {
        eligible: false,
        automatedPass: false,
        sourceClean: identityReport.provenance.sourceDirty === false,
        trackedReceipt: false,
        humanApproval: false,
        verdict: "diagnostic_not_balance_authority",
        reasons: [
          "Paired faction swaps locate main effects but do not promote a physical rule."
        ]
      }
    },
    preRegistration,
    comparisons: results
  };
}
