import { availableParallelism } from "node:os";
import {
  isMainThread,
  parentPort,
  Worker
} from "node:worker_threads";
import { createSimulation } from "../runtime/create-simulation.js";
import { fingerprintObject } from "../versioning/game-identity.js";

const PARALLEL_BACKENDS = new Set(["weighted", "greedy"]);
const workerUrl = new URL(import.meta.url);

if (!isMainThread) {
  parentPort.on("message", async ({ taskIndex, options }) => {
    try {
      const report = await createSimulation(options);
      parentPort.postMessage({ taskIndex, report });
    } catch (error) {
      parentPort.postMessage({
        taskIndex,
        error: {
          message: error.message,
          name: error.name,
          stack: error.stack
        }
      });
    }
  });
}

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

function workerCount(value) {
  const fallback = Math.max(1, availableParallelism() - 1);
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 64) {
    throw new RangeError("workers must be an integer from 1 to 64.");
  }
  return parsed;
}

function workersForTasks(value, tasks) {
  const workers = workerCount(value);
  const unsupported = new Set(tasks.flatMap((task) =>
    (task.options.backends || []).filter((backend) => !PARALLEL_BACKENDS.has(backend))
  ));
  if (!unsupported.size || workers === 1) return workers;
  if (value === undefined) return 1;
  if (unsupported.size) {
    throw new Error(
      `Parallel faction swaps support deterministic backends only; use workers=1 for: ${[
        ...unsupported
      ].join(", ")}.`
    );
  }
  return workers;
}

async function runInline(tasks, { signal, onProgress, totalGames }) {
  const reports = [];
  let completed = 0;
  for (const task of tasks) {
    if (signal?.aborted) throw signal.reason;
    onProgress?.({
      completed,
      total: totalGames,
      completedTasks: reports.filter(Boolean).length,
      totalTasks: tasks.length,
      activeTaskIndices: [task.taskIndex]
    });
    reports[task.taskIndex] = await createSimulation({
      ...task.options,
      signal
    });
    completed += task.options.runs;
    onProgress?.({
      completed,
      total: totalGames,
      completedTasks: reports.filter(Boolean).length,
      totalTasks: tasks.length,
      activeTaskIndices: []
    });
  }
  return reports;
}

async function runInWorkers(tasks, {
  workers,
  signal,
  onProgress,
  totalGames
}) {
  if (signal?.aborted) throw signal.reason;
  const count = Math.min(workers, tasks.length);
  const reports = Array(tasks.length);
  const pool = Array.from({ length: count }, () => new Worker(workerUrl));
  let nextTask = 0;
  let completedTasks = 0;
  let completedGames = 0;
  let settled = false;
  const activeTasks = new Map();

  return new Promise((resolve, reject) => {
    const terminate = () => Promise.allSettled(pool.map((worker) => worker.terminate()));
    const finishWithError = async (error) => {
      if (settled) return;
      settled = true;
      signal?.removeEventListener("abort", abort);
      await terminate();
      reject(error);
    };
    const abort = () => finishWithError(
      signal.reason || new Error("Parallel faction swap was cancelled.")
    );
    const assign = (worker) => {
      if (settled || nextTask >= tasks.length) return;
      const task = tasks[nextTask];
      nextTask += 1;
      activeTasks.set(worker, task.taskIndex);
      onProgress?.({
        completed: completedGames,
        total: totalGames,
        completedTasks,
        totalTasks: tasks.length,
        activeTaskIndices: [...activeTasks.values()]
      });
      worker.postMessage(task);
    };
    const accept = async (worker, message) => {
      if (settled) return;
      if (message.error) {
        const error = new Error(message.error.message);
        error.name = message.error.name;
        error.stack = message.error.stack;
        await finishWithError(error);
        return;
      }
      const task = tasks[message.taskIndex];
      if (!task || reports[message.taskIndex]) {
        await finishWithError(new Error(
          `Parallel faction swap returned an invalid task index: ${message.taskIndex}.`
        ));
        return;
      }
      reports[message.taskIndex] = message.report;
      activeTasks.delete(worker);
      completedTasks += 1;
      completedGames += task.options.runs;
      onProgress?.({
        completed: completedGames,
        total: totalGames,
        completedTasks,
        totalTasks: tasks.length,
        activeTaskIndices: [...activeTasks.values()]
      });
      if (completedTasks === tasks.length) {
        settled = true;
        signal?.removeEventListener("abort", abort);
        await terminate();
        resolve(reports);
        return;
      }
      assign(worker);
    };

    signal?.addEventListener("abort", abort, { once: true });
    for (const worker of pool) {
      worker.on("message", (message) => accept(worker, message));
      worker.on("error", finishWithError);
      worker.on("exit", (code) => {
        if (!settled) {
          finishWithError(new Error(
            `Faction-swap worker exited before completing its task (code ${code}).`
          ));
        }
      });
      assign(worker);
    }
  });
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
  const prepared = comparisons.map((comparison) => {
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
    return { comparison, focalSeat, common };
  });
  const tasks = prepared.flatMap(({ comparison, common }) => [
    {
      options: {
        ...common,
        factionIds: comparison.leftFactionIds
      }
    },
    {
      options: {
        ...common,
        factionIds: comparison.rightFactionIds
      }
    }
  ]).map((task, taskIndex) => ({ ...task, taskIndex }));
  const requestedWorkers = workersForTasks(options.workers, tasks);
  const totalGames = tasks.length * runsPerArm;
  const actualWorkers = Math.min(requestedWorkers, tasks.length);
  const armReports = requestedWorkers === 1
    ? await runInline(tasks, {
      signal: options.signal,
      onProgress,
      totalGames
    })
    : await runInWorkers(tasks, {
      workers: requestedWorkers,
      signal: options.signal,
      onProgress,
      totalGames
    });
  if (armReports.length !== tasks.length || armReports.some((report) => !report)) {
    throw new Error("Parallel faction swap did not return every scheduled arm.");
  }
  const identityReport = armReports[0];
  const results = prepared.map(({ comparison, focalSeat }, comparisonIndex) => {
    const left = armReports[comparisonIndex * 2];
    const right = armReports[comparisonIndex * 2 + 1];
    return {
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
    };
  });
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
    execution: {
      scheduler: actualWorkers > 1 ? "worker_threads" : "inline",
      taskUnit: "simulation_arm",
      requestedWorkers,
      workers: actualWorkers,
      deterministicResultOrder: "comparison_then_arm"
    },
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
