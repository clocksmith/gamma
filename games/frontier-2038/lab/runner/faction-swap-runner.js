import { availableParallelism } from "node:os";
import { randomUUID } from "node:crypto";
import {
  isMainThread,
  parentPort,
  Worker
} from "node:worker_threads";
import { ClaudeCliCaller, CodexCliCaller } from "../callers/index.js";
import {
  captureSimulationLaunchIdentity,
  createSimulation
} from "../runtime/create-simulation.js";
import { archiveSimulationReport } from "../report-archive.js";
import { fingerprintObject, projectRoot } from "../versioning/game-identity.js";

const DETERMINISTIC_BACKENDS = new Set(["weighted", "greedy"]);
const DEFAULT_LLM_CONCURRENCY = 2;
const MAX_LLM_CONCURRENCY = 16;
const DEFAULT_PROVIDER_CONCURRENCY = Object.freeze({
  claude: 1,
  codex: 2
});
const MAX_PROVIDER_CONCURRENCY = Object.freeze({
  claude: 4,
  codex: 8
});
const workerUrl = new URL(import.meta.url);

function serializeError(error) {
  return {
    message: error?.message || "Unknown simulation failure.",
    name: error?.name || "Error",
    stack: error?.stack || null,
    evidenceOutcome: error?.evidenceOutcome || null,
    providerReceipt: error?.providerReceipt
      ? structuredClone(error.providerReceipt)
      : null
  };
}

function restoreError(value) {
  const error = new Error(value?.message || "Unknown simulation failure.");
  error.name = value?.name || "Error";
  error.stack = value?.stack || error.stack;
  error.evidenceOutcome = value?.evidenceOutcome || null;
  error.providerReceipt = value?.providerReceipt || null;
  return error;
}

function boundedConcurrency(value, fallback, maximum, label) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > maximum) {
    throw new RangeError(`${label} must be an integer from 1 to ${maximum}.`);
  }
  return parsed;
}

function retryCount(value) {
  const parsed = value === undefined ? 0 : Number(value);
  if (!Number.isInteger(parsed) || parsed < 0 || parsed > 2) {
    throw new RangeError("llmRetries must be an integer from 0 to 2.");
  }
  return parsed;
}

function providerLimits(value = {}) {
  const configured = value || {};
  return Object.fromEntries(
    Object.keys(DEFAULT_PROVIDER_CONCURRENCY).map((provider) => [
      provider,
      boundedConcurrency(
        configured[provider],
        DEFAULT_PROVIDER_CONCURRENCY[provider],
        MAX_PROVIDER_CONCURRENCY[provider],
        `${provider} concurrency`
      )
    ])
  );
}

function defaultCallerFactory({
  provider,
  model,
  reasoningEffort,
  timeoutMs,
  callerOptions
}) {
  const options = {
    ...(callerOptions || {}),
    ...(model !== undefined ? { model } : {}),
    ...(reasoningEffort !== undefined ? { reasoningEffort } : {}),
    ...(timeoutMs !== undefined ? { timeoutMs } : {})
  };
  return provider === "claude"
    ? new ClaudeCliCaller(options)
    : new CodexCliCaller(options);
}

export class LlmConcurrencyBroker {
  constructor({
    concurrency,
    providerConcurrency,
    retries,
    signal,
    generation = randomUUID(),
    callerFactory = defaultCallerFactory
  } = {}) {
    this.concurrency = boundedConcurrency(
      concurrency,
      DEFAULT_LLM_CONCURRENCY,
      MAX_LLM_CONCURRENCY,
      "llmConcurrency"
    );
    this.providerConcurrency = providerLimits(providerConcurrency);
    this.retries = retryCount(retries);
    this.generation = generation;
    this.callerFactory = callerFactory;
    this.callers = new Map();
    this.queue = [];
    this.active = new Map();
    this.activeByProvider = Object.fromEntries(
      Object.keys(this.providerConcurrency).map((provider) => [provider, 0])
    );
    this.peakActive = 0;
    this.peakActiveByProvider = structuredClone(this.activeByProvider);
    this.requested = 0;
    this.completed = 0;
    this.failed = 0;
    this.cancelledRequests = 0;
    this.retryAttempts = 0;
    this.throttled = 0;
    this.cancelled = false;
    this.signal = signal;
    this.abort = () => this.cancel(
      signal?.reason || new DOMException("LLM study cancelled.", "AbortError")
    );
    signal?.addEventListener("abort", this.abort, { once: true });
    if (signal?.aborted) this.abort();
  }

  request(request) {
    if (this.cancelled || this.signal?.aborted) {
      return Promise.reject(
        this.signal?.reason || new DOMException("LLM study cancelled.", "AbortError")
      );
    }
    if (request.studyGeneration !== this.generation) {
      return Promise.reject(new Error("LLM request belongs to an inactive study generation."));
    }
    if (!(request.provider in this.providerConcurrency)) {
      return Promise.reject(new TypeError(`Unsupported LLM provider: ${request.provider}.`));
    }
    this.requested += 1;
    return new Promise((resolve, reject) => {
      const entry = {
        ...request,
        queuedAt: Date.now(),
        resolve,
        reject,
        controller: new AbortController(),
        settled: false
      };
      if (!this.canStart(entry)) this.throttled += 1;
      this.queue.push(entry);
      this.drain();
    });
  }

  canStart(entry) {
    return this.active.size < this.concurrency &&
      this.activeByProvider[entry.provider] < this.providerConcurrency[entry.provider];
  }

  drain() {
    if (this.cancelled) return;
    while (this.active.size < this.concurrency) {
      const index = this.queue.findIndex((entry) => this.canStart(entry));
      if (index < 0) return;
      const [entry] = this.queue.splice(index, 1);
      this.start(entry);
    }
  }

  callerFor(entry) {
    const config = {
      provider: entry.provider,
      backend: entry.backend,
      model: entry.model,
      reasoningEffort: entry.reasoningEffort,
      timeoutMs: entry.timeoutMs,
      callerOptions: entry.callerOptions
    };
    const key = JSON.stringify(config);
    if (!this.callers.has(key)) this.callers.set(key, this.callerFactory(config));
    return this.callers.get(key);
  }

  async start(entry) {
    this.active.set(entry.requestToken, entry);
    this.activeByProvider[entry.provider] += 1;
    this.peakActive = Math.max(this.peakActive, this.active.size);
    this.peakActiveByProvider[entry.provider] = Math.max(
      this.peakActiveByProvider[entry.provider],
      this.activeByProvider[entry.provider]
    );
    let attempts = 0;
    try {
      while (true) {
        attempts += 1;
        try {
          const caller = await this.callerFor(entry);
          const result = await caller.decide(entry.packet, {
            signal: entry.controller.signal,
            brokerContext: {
              studyGeneration: entry.studyGeneration,
              taskGeneration: entry.taskGeneration,
              taskIndex: entry.taskIndex,
              requestToken: entry.requestToken,
              attempt: attempts
            }
          });
          if (this.cancelled || entry.studyGeneration !== this.generation) {
            throw new DOMException("Late LLM response rejected.", "AbortError");
          }
          this.completed += 1;
          entry.settled = true;
          entry.resolve({
            ...result,
            receipt: {
              ...result.receipt,
              brokerTaskIndex: entry.taskIndex,
              brokerRequestToken: entry.requestToken,
              brokerAttempts: attempts,
              brokerRetries: attempts - 1,
              brokerQueuedMs: Math.max(0, Date.now() - entry.queuedAt)
            }
          });
          return;
        } catch (error) {
          if (
            this.cancelled ||
            entry.controller.signal.aborted ||
            error?.name === "AbortError"
          ) {
            throw error;
          }
          if (attempts > this.retries) throw error;
          this.retryAttempts += 1;
        }
      }
    } catch (error) {
      if (!entry.settled) {
        this.failed += 1;
        entry.settled = true;
        error.providerReceipt = {
          ...(error.providerReceipt || {}),
          brokerTaskIndex: entry.taskIndex,
          brokerRequestToken: entry.requestToken,
          brokerAttempts: attempts,
          brokerRetries: Math.max(0, attempts - 1),
          brokerQueuedMs: Math.max(0, Date.now() - entry.queuedAt)
        };
        entry.reject(error);
      }
    } finally {
      this.active.delete(entry.requestToken);
      this.activeByProvider[entry.provider] -= 1;
      this.drain();
    }
  }

  cancelRequest(requestToken, reason) {
    const queuedIndex = this.queue.findIndex((entry) =>
      entry.requestToken === requestToken
    );
    if (queuedIndex >= 0) {
      const [entry] = this.queue.splice(queuedIndex, 1);
      entry.settled = true;
      this.cancelledRequests += 1;
      entry.reject(reason || new DOMException("LLM request cancelled.", "AbortError"));
      return;
    }
    const entry = this.active.get(requestToken);
    if (entry && !entry.settled) {
      const cancellation =
        reason || new DOMException("LLM request cancelled.", "AbortError");
      entry.settled = true;
      this.cancelledRequests += 1;
      entry.reject(cancellation);
      entry.controller.abort(cancellation);
    }
  }

  cancel(reason = new DOMException("LLM study cancelled.", "AbortError")) {
    if (this.cancelled) return;
    this.cancelled = true;
    for (const entry of this.queue.splice(0)) {
      entry.settled = true;
      this.cancelledRequests += 1;
      entry.reject(reason);
    }
    for (const entry of this.active.values()) {
      if (!entry.settled) {
        entry.settled = true;
        this.cancelledRequests += 1;
        entry.reject(reason);
      }
      entry.controller.abort(reason);
    }
  }

  close() {
    this.signal?.removeEventListener("abort", this.abort);
  }

  summary() {
    return {
      generation: this.generation,
      requestedConcurrency: this.concurrency,
      concurrency: this.concurrency,
      providerConcurrency: structuredClone(this.providerConcurrency),
      peakActiveLlmCalls: this.peakActive,
      peakActiveByProvider: structuredClone(this.peakActiveByProvider),
      requests: this.requested,
      completedRequests: this.completed,
      failedRequests: this.failed,
      cancelledRequests: this.cancelledRequests,
      retries: this.retryAttempts,
      throttledRequests: this.throttled
    };
  }
}

let activeWorkerTask = null;
let workerRequestSequence = 0;
const pendingWorkerRequests = new Map();

class WorkerBrokerCaller {
  constructor(configuration) {
    this.configuration = configuration;
  }

  decide(packet, { signal } = {}) {
    if (!activeWorkerTask) {
      return Promise.reject(new Error("Worker LLM caller has no active simulation task."));
    }
    const requestToken =
      `${activeWorkerTask.generation}:${workerRequestSequence += 1}`;
    return new Promise((resolve, reject) => {
      const abort = () => {
        pendingWorkerRequests.delete(requestToken);
        parentPort.postMessage({
          kind: "llm_abort",
          requestToken,
          reason: serializeError(signal.reason)
        });
        reject(signal.reason || new DOMException("LLM request cancelled.", "AbortError"));
      };
      if (signal?.aborted) {
        abort();
        return;
      }
      pendingWorkerRequests.set(requestToken, {
        resolve,
        reject,
        signal,
        abort
      });
      signal?.addEventListener("abort", abort, { once: true });
      parentPort.postMessage({
        kind: "llm_request",
        requestToken,
        studyGeneration: activeWorkerTask.studyGeneration,
        taskGeneration: activeWorkerTask.generation,
        taskIndex: activeWorkerTask.taskIndex,
        packet,
        ...this.configuration
      });
    });
  }
}

if (!isMainThread) {
  parentPort.on("message", async (message) => {
    if (message.kind === "llm_response") {
      const pending = pendingWorkerRequests.get(message.requestToken);
      if (!pending) return;
      pendingWorkerRequests.delete(message.requestToken);
      pending.signal?.removeEventListener("abort", pending.abort);
      if (message.error) pending.reject(restoreError(message.error));
      else pending.resolve(message.result);
      return;
    }
    if (message.kind !== "simulation_task") return;
    activeWorkerTask = {
      taskIndex: message.taskIndex,
      studyGeneration: message.studyGeneration,
      generation: message.taskGeneration
    };
    try {
      const report = await createSimulation({
        ...message.options,
        launchIdentity: message.launchIdentity,
        ...(message.brokeredLlm ? {
          callerFactory: (configuration) => new WorkerBrokerCaller(configuration)
        } : {})
      });
      parentPort.postMessage({
        kind: "task_result",
        taskIndex: message.taskIndex,
        taskGeneration: message.taskGeneration,
        report
      });
    } catch (error) {
      parentPort.postMessage({
        kind: "task_result",
        taskIndex: message.taskIndex,
        taskGeneration: message.taskGeneration,
        error: serializeError(error)
      });
    } finally {
      activeWorkerTask = null;
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

function scenarioOutcome(observation, seat) {
  const funnel = (observation.agiFunnel || []).find((entry) =>
    entry.seat === seat
  );
  return {
    legalDeclaration: Boolean(funnel?.legalDeclarationWindow),
    declared: Boolean(funnel?.declared),
    scenario: observation.scenario || null
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
  if (
    comparison.seedGroup !== undefined &&
    (typeof comparison.seedGroup !== "string" || !comparison.seedGroup.length)
  ) {
    throw new TypeError(`${comparison.id} has an invalid seedGroup.`);
  }
  return focalSeat;
}

function resolvePromptAddenda(comparison, arm, options, playerCount) {
  const promptIds = comparison[`${arm}PromptIds`];
  if (promptIds !== undefined) {
    if (!Array.isArray(promptIds) || promptIds.length !== playerCount) {
      throw new RangeError(
        `${comparison.id} ${arm}PromptIds must contain ${playerCount} entries.`
      );
    }
    return promptIds.map((id, seat) => {
      if (id === null) return null;
      const prompt = options.promptLibrary?.[id];
      if (typeof prompt !== "string" || !prompt.length) {
        throw new TypeError(
          `${comparison.id} ${arm}PromptIds seat ${seat} names unknown prompt ${id}.`
        );
      }
      return prompt;
    });
  }
  return comparison[`${arm}PromptAddenda`] ||
    comparison.promptAddenda ||
    options.promptAddenda;
}

export function expandFactionIsolationMatrix(matrix = {}) {
  const matrixPlayerCount = Number(matrix.playerCount || 3);
  const comparatorFactionIds = matrix.comparatorFactionIds || [];
  const focalSeats = matrix.focalSeats || [];
  const policyArms = matrix.policyArms || [];
  const opponentFactionCycle = matrix.opponentFactionCycle || [];
  if (
    !matrix.focalFactionId ||
    !matrix.focalProfileId ||
    comparatorFactionIds.length < 1 ||
    focalSeats.length < 1 ||
    policyArms.length < 1 ||
    opponentFactionCycle.length < 3 ||
    !Number.isInteger(matrixPlayerCount) ||
    matrixPlayerCount < 3 ||
    matrixPlayerCount > 5 ||
    matrix.opponentProfileIds?.length !== matrixPlayerCount - 1
  ) {
    throw new TypeError("comparisonMatrix is incomplete.");
  }
  return comparatorFactionIds.flatMap((comparatorFactionId) => {
    const comparatorIndex = opponentFactionCycle.indexOf(comparatorFactionId);
    if (comparatorIndex < 0) {
      throw new TypeError(
        `comparisonMatrix opponentFactionCycle omits ${comparatorFactionId}.`
      );
    }
    const opponentFactionIds = Array.from(
      { length: matrixPlayerCount - 1 },
      (_, index) => index + 1
    ).map((offset) =>
      opponentFactionCycle[
        (comparatorIndex + offset) % opponentFactionCycle.length
      ]
    );
    return focalSeats.flatMap((focalSeat) => policyArms.map((policyArm) => {
      const place = (focal, opponents) => {
        const values = [];
        let opponentIndex = 0;
        for (let seat = 0; seat < matrixPlayerCount; seat += 1) {
          values.push(seat === focalSeat ? focal : opponents[opponentIndex++]);
        }
        return values;
      };
      return {
        id: [comparatorFactionId, `seat_${focalSeat}`, policyArm.id].join("_"),
        seedGroup: `${comparatorFactionId}:seat:${focalSeat}`,
        promptTreatmentId: policyArm.id,
        comparatorId: comparatorFactionId,
        focalSeat,
        profileIds: place(matrix.focalProfileId, matrix.opponentProfileIds),
        backends: place(
          matrix.focalBackend || "codex",
          Array(matrixPlayerCount - 1).fill("weighted")
        ),
        leftPromptIds: place(
          policyArm.leftPromptId,
          Array(matrixPlayerCount - 1).fill(null)
        ),
        rightPromptIds: place(
          matrix.rightPromptIdsByFaction?.[comparatorFactionId],
          Array(matrixPlayerCount - 1).fill(null)
        ),
        leftFactionIds: place(matrix.focalFactionId, opponentFactionIds),
        rightFactionIds: place(comparatorFactionId, opponentFactionIds)
      };
    }));
  });
}

export function expandAgiDeclarationScenarioMatrix(matrix = {}) {
  const playerCount = Number(matrix.playerCount);
  const factionIds = matrix.factionIds || [];
  const focalSeats = matrix.focalSeats || [];
  const backends = matrix.backends || [];
  const opponentRotations = Number(matrix.opponentRotations || 1);
  const profileId = matrix.profileId || "agi_candidate";
  if (
    !Number.isInteger(playerCount) ||
    playerCount < 3 ||
    playerCount > 5 ||
    factionIds.length < playerCount ||
    new Set(factionIds).size !== factionIds.length ||
    focalSeats.length < 1 ||
    backends.length < 1 ||
    !Number.isInteger(opponentRotations) ||
    opponentRotations < 1
  ) {
    throw new TypeError("AGI scenarioMatrix is incomplete.");
  }
  for (const focalSeat of focalSeats) {
    if (
      !Number.isInteger(focalSeat) ||
      focalSeat < 0 ||
      focalSeat >= playerCount
    ) {
      throw new RangeError("AGI scenarioMatrix has an invalid focal seat.");
    }
  }
  for (const backend of backends) {
    if (!DETERMINISTIC_BACKENDS.has(backend)) {
      throw new TypeError(
        "AGI declaration scenario matrix accepts deterministic backends only."
      );
    }
  }

  const place = (focalSeat, focal, opponents) => {
    const values = [];
    let opponentIndex = 0;
    for (let seat = 0; seat < playerCount; seat += 1) {
      values.push(seat === focalSeat ? focal : opponents[opponentIndex++]);
    }
    return values;
  };

  return factionIds.flatMap((focalFactionId) => {
    const opponents = factionIds.filter((id) => id !== focalFactionId);
    return focalSeats.flatMap((focalSeat) =>
      backends.flatMap((backend) =>
        Array.from({ length: opponentRotations }, (_, rotation) => {
          const start = (rotation * (playerCount - 1)) % opponents.length;
          const opponentFactionIds = Array.from(
            { length: playerCount - 1 },
            (_, index) => opponents[(start + index) % opponents.length]
          );
          const roster = place(focalSeat, focalFactionId, opponentFactionIds);
          return {
            id: [
              focalFactionId,
              `seat_${focalSeat}`,
              backend,
              `roster_${rotation}`
            ].join("_"),
            seedGroup: [
              focalFactionId,
              `seat:${focalSeat}`,
              `backend:${backend}`,
              `roster:${rotation}`
            ].join(":"),
            question:
              "What is the paired outcome effect of a legal AGI declaration " +
              "window versus an otherwise identical one-marker-short state?",
            focalSeat,
            focalFactionId,
            backend,
            opponentRotation: rotation,
            profileIds: Array(playerCount).fill(profileId),
            backends: Array(playerCount).fill(backend),
            leftFactionIds: roster,
            rightFactionIds: roster,
            leftScenario: {
              id: "agi_declaration_window_v1",
              arm: "eligible",
              focalSeat
            },
            rightScenario: {
              id: "agi_declaration_window_v1",
              arm: "blocked_grid_ready",
              focalSeat
            }
          };
        })
      )
    );
  });
}

function workerCount(value, fallback) {
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 64) {
    throw new RangeError("workers must be an integer from 1 to 64.");
  }
  return parsed;
}

function taskUsesLlm(task) {
  return (task.options.backends || []).some((backend) =>
    !DETERMINISTIC_BACKENDS.has(backend)
  );
}

function workersForTasks(value, tasks, llmConcurrency) {
  const hasLlm = tasks.some(taskUsesLlm);
  const fallback = hasLlm
    ? Math.min(4, llmConcurrency)
    : Math.min(64, Math.max(1, availableParallelism() - 1));
  return workerCount(value, fallback);
}

async function runInline(tasks, { signal, onProgress, totalGames }) {
  const reports = [];
  let completed = 0;
  for (const task of tasks) {
    if (signal?.aborted) throw signal.reason;
    reports[task.taskIndex] = await createSimulation({
      ...task.options,
      launchIdentity: task.launchIdentity,
      signal
    });
    completed += task.options.runs;
    onProgress?.({ completed, total: totalGames });
  }
  return reports;
}

async function runInWorkers(tasks, {
  workers,
  broker,
  studyGeneration,
  signal,
  onProgress,
  totalGames,
  archiveCompletedLlmMatch
}) {
  if (signal?.aborted) throw signal.reason;
  const count = Math.min(workers, tasks.length);
  const reports = Array(tasks.length);
  const failures = Array(tasks.length);
  const archives = Array(tasks.length);
  const pool = Array.from({ length: count }, () => new Worker(workerUrl));
  const workerState = new Map(pool.map((worker) => [worker, null]));
  let nextTask = 0;
  let completedTasks = 0;
  let completedGames = 0;
  let settled = false;

  return new Promise((resolve, reject) => {
    const terminate = () => Promise.allSettled(pool.map((worker) => worker.terminate()));
    const finishWithError = async (error) => {
      if (settled) return;
      settled = true;
      signal?.removeEventListener("abort", abort);
      broker?.cancel(error);
      broker?.close();
      await terminate();
      reject(error);
    };
    const abort = () => finishWithError(
      signal.reason || new Error("Parallel faction swap was cancelled.")
    );
    const assign = (worker) => {
      if (settled || nextTask >= tasks.length) return;
      const task = tasks[nextTask];
      const taskGeneration = `${studyGeneration}:${task.taskIndex}`;
      workerState.set(worker, {
        taskIndex: task.taskIndex,
        taskGeneration
      });
      worker.postMessage({
        kind: "simulation_task",
        ...task,
        studyGeneration,
        taskGeneration,
        brokeredLlm: taskUsesLlm(task)
      });
      nextTask += 1;
    };
    const accept = async (worker, message) => {
      if (settled) return;
      const state = workerState.get(worker);
      if (message.kind === "llm_abort") {
        broker?.cancelRequest(message.requestToken, restoreError(message.reason));
        return;
      }
      if (message.kind === "llm_request") {
        if (
          !broker ||
          !state ||
          message.taskIndex !== state.taskIndex ||
          message.taskGeneration !== state.taskGeneration
        ) {
          worker.postMessage({
            kind: "llm_response",
            requestToken: message.requestToken,
            error: serializeError(new Error("Stale worker LLM request rejected."))
          });
          return;
        }
        broker.request(message).then(
          (result) => {
            const current = workerState.get(worker);
            if (
              settled ||
              !current ||
              current.taskGeneration !== message.taskGeneration
            ) return;
            worker.postMessage({
              kind: "llm_response",
              requestToken: message.requestToken,
              result
            });
          },
          (error) => {
            const current = workerState.get(worker);
            if (
              settled ||
              !current ||
              current.taskGeneration !== message.taskGeneration
            ) return;
            worker.postMessage({
              kind: "llm_response",
              requestToken: message.requestToken,
              error: serializeError(error)
            });
          }
        );
        return;
      }
      if (
        message.kind !== "task_result" ||
        !state ||
        message.taskIndex !== state.taskIndex ||
        message.taskGeneration !== state.taskGeneration
      ) {
        await finishWithError(new Error("Parallel faction swap returned a stale task result."));
        return;
      }
      const task = tasks[message.taskIndex];
      if (message.error) {
        if (!taskUsesLlm(task)) {
          await finishWithError(restoreError(message.error));
          return;
        }
        failures[message.taskIndex] = message.error;
      } else {
        if (!task || reports[message.taskIndex]) {
          await finishWithError(new Error(
            `Parallel faction swap returned an invalid task index: ${message.taskIndex}.`
          ));
          return;
        }
        if (taskUsesLlm(task)) {
          archives[task.taskIndex] = await archiveCompletedLlmMatch(task, message.report);
        }
        reports[message.taskIndex] = message.report;
      }
      workerState.set(worker, null);
      completedTasks += 1;
      completedGames += task.options.runs;
      onProgress?.({ completed: completedGames, total: totalGames });
      if (completedTasks === tasks.length) {
        settled = true;
        signal?.removeEventListener("abort", abort);
        broker?.close();
        await terminate();
        resolve({ reports, failures, archives });
        return;
      }
      assign(worker);
    };

    signal?.addEventListener("abort", abort, { once: true });
    for (const worker of pool) {
      worker.on("message", (message) => {
        accept(worker, message).catch(finishWithError);
      });
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

function summarizePair(left, right, focalSeat, matchIndexes) {
  if (left.observations.length !== right.observations.length) {
    throw new Error("Paired faction arms produced different observation counts.");
  }
  const rows = left.observations.map((leftObservation, index) => {
    const rightObservation = right.observations[index];
    const leftStanding = standingAt(leftObservation, focalSeat);
    const rightStanding = standingAt(rightObservation, focalSeat);
    const leftScenario = scenarioOutcome(leftObservation, focalSeat);
    const rightScenario = scenarioOutcome(rightObservation, focalSeat);
    return {
      matchIndex: matchIndexes?.[index] ?? index,
      scoreDelta: leftStanding.score - rightStanding.score,
      rankAdvantage: rightStanding.rank - leftStanding.rank,
      winCreditDelta:
        winCredit(leftObservation, focalSeat) -
        winCredit(rightObservation, focalSeat),
      leftLegalDeclaration: leftScenario.legalDeclaration,
      rightLegalDeclaration: rightScenario.legalDeclaration,
      leftDeclared: leftScenario.declared,
      rightDeclared: rightScenario.declared
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
    leftLegalDeclarationRate: mean(rows.map((row) =>
      Number(row.leftLegalDeclaration)
    )),
    rightLegalDeclarationRate: mean(rows.map((row) =>
      Number(row.rightLegalDeclaration)
    )),
    leftDeclarationRate: mean(rows.map((row) => Number(row.leftDeclared))),
    rightDeclarationRate: mean(rows.map((row) => Number(row.rightDeclared))),
    rows
  };
}

function sumNumericValues(left = {}, right = {}) {
  const result = structuredClone(left);
  for (const [key, value] of Object.entries(right || {})) {
    if (typeof value === "number") {
      result[key] = (Number(result[key]) || 0) + value;
    } else if (value && typeof value === "object" && !Array.isArray(value)) {
      result[key] = sumNumericValues(result[key], value);
    } else if (!(key in result)) {
      result[key] = structuredClone(value);
    }
  }
  return result;
}

function abilityValues(reports, factionId) {
  return reports.reduce((totals, report) =>
    sumNumericValues(
      totals,
      report.matchMetrics?.factionAbilityValues?.[factionId] || {}
    ), {});
}

function failureEvidence(value) {
  if (!value) return null;
  return {
    outcome: value.evidenceOutcome || "quarantined",
    name: value.name || "Error",
    message: value.message || "Unknown LLM match failure.",
    providerReceipt: value.providerReceipt || null
  };
}

function orderedReceipts(report) {
  const observation = report.observations?.[0];
  if (!observation) return [];
  return [...observation.standings]
    .sort((left, right) => left.seat - right.seat)
    .flatMap((standing) => (standing.policyReceipts || []).map((receipt, receiptIndex) => ({
      seat: standing.seat,
      receiptIndex,
      ...structuredClone(receipt)
    })));
}

function llmExecutionProfiles(prepared) {
  const profiles = [];
  for (const { common } of prepared) {
    for (const [seat, backend] of (common.backends || []).entries()) {
      if (DETERMINISTIC_BACKENDS.has(backend)) continue;
      const entry = {
        backend,
        provider: backend.includes("claude") ? "claude" : "codex",
        model: common.models?.[seat] || common.model || null,
        reasoningEffort:
          common.reasoningEfforts?.[seat] || common.reasoningEffort || null
      };
      if (!profiles.some((candidate) =>
        JSON.stringify(candidate) === JSON.stringify(entry)
      )) profiles.push(entry);
    }
  }
  return profiles;
}

function studyIdentityBasis(identity) {
  return {
    game: identity.game,
    engine: identity.engine,
    contracts: identity.contracts,
    rng: identity.rng,
    provenance: identity.provenance
  };
}

async function captureTaskLaunchIdentities(tasks) {
  let expectedBasis = null;
  for (const task of tasks) {
    const launchIdentity = await captureSimulationLaunchIdentity(task.options);
    const basis = studyIdentityBasis(launchIdentity);
    const fingerprint = fingerprintObject(basis);
    if (expectedBasis && expectedBasis.fingerprint !== fingerprint) {
      const error = new Error(
        "Faction-swap source identity changed while task launch identities were captured."
      );
      error.code = "study_launch_identity_mismatch";
      throw error;
    }
    expectedBasis ||= { ...basis, fingerprint };
    task.launchIdentity = launchIdentity;
  }
  return expectedBasis;
}

export async function runFactionSwapDiagnostic(options = {}, onProgress) {
  const comparisons = options.comparisons ||
    (options.comparisonMatrix
      ? expandFactionIsolationMatrix(options.comparisonMatrix)
      : options.scenarioMatrix
        ? expandAgiDeclarationScenarioMatrix(options.scenarioMatrix)
        : []);
  if (!comparisons.length) throw new RangeError("At least one faction comparison is required.");
  const playerCount = Number(options.playerCount || 4);
  if (
    options.comparisonMatrix?.playerCount !== undefined &&
    Number(options.comparisonMatrix.playerCount) !== playerCount
  ) {
    throw new RangeError("comparisonMatrix playerCount must match the study playerCount.");
  }
  const runsPerArm = Number(options.runsPerArm || 100);
  if (!Number.isInteger(runsPerArm) || runsPerArm < 1 || runsPerArm > 10000) {
    throw new RangeError("runsPerArm must be an integer from 1 to 10000.");
  }
  const rootSeed = String(options.seed || "m3t4-faction-swap");
  const sampleReplays = Number(options.sampleReplays || 0);
  if (!Number.isInteger(sampleReplays) || sampleReplays < 0 || sampleReplays > 10) {
    throw new RangeError("sampleReplays must be an integer from 0 to 10.");
  }
  const prepared = comparisons.map((comparison) => {
    const focalSeat = validateComparison(comparison, playerCount);
    const common = {
      runs: runsPerArm,
      playerCount,
      seed: `${rootSeed}:${comparison.seedGroup || comparison.id}`,
      sampleReplays,
      profileIds: comparison.profileIds || options.profileIds,
      backends: comparison.backends || options.backends,
      models: comparison.models || options.models,
      model: comparison.model || options.model,
      reasoningEfforts: comparison.reasoningEfforts || options.reasoningEfforts,
      reasoningEffort: comparison.reasoningEffort || options.reasoningEffort,
      rotateProfiles: false,
      rotateFactions: false,
      mandateMode: options.mandateMode || "variable",
      rulesVariant: options.rulesVariant || {},
      simulateNegotiation: true,
      includeObservations: true,
      experimentKind: options.experimentKind || "balance_audit",
      allowLlm: Boolean(options.allowLlm),
      maxLlmDecisions: options.maxLlmDecisions,
      maxLlmDecisionsPerSeatCycle: options.maxLlmDecisionsPerSeatCycle,
      timeoutMs: options.timeoutMs,
      llmCallerOptions: options.llmCallerOptions,
      llmCacheMode: options.llmCacheMode,
      llmCacheDirectory: options.llmCacheDirectory
    };
    return { comparison, focalSeat, common };
  });
  const hasLlm = prepared.some(({ common }) =>
    (common.backends || []).some((backend) => !DETERMINISTIC_BACKENDS.has(backend))
  );
  if (hasLlm && !options.allowLlm) {
    throw new Error("LLM-backed faction diagnostics require explicit allowLlm authorization.");
  }
  const resolvedLlmConcurrency = hasLlm
    ? boundedConcurrency(
      options.llmConcurrency,
      DEFAULT_LLM_CONCURRENCY,
      MAX_LLM_CONCURRENCY,
      "llmConcurrency"
    )
    : 0;
  const tasks = [];
  for (const [comparisonIndex, { comparison, common }] of prepared.entries()) {
    const llmArm = (common.backends || []).some((backend) =>
      !DETERMINISTIC_BACKENDS.has(backend)
    );
    for (const arm of ["left", "right"]) {
      const factionIds = comparison[`${arm}FactionIds`];
      const promptAddenda = resolvePromptAddenda(
        comparison,
        arm,
        options,
        playerCount
      );
      const scenario = comparison[`${arm}Scenario`] || null;
      if (!llmArm) {
        tasks.push({
          comparisonIndex,
          arm,
          matchIndex: null,
          options: { ...common, factionIds, promptAddenda, scenario }
        });
        continue;
      }
      for (let matchIndex = 0; matchIndex < runsPerArm; matchIndex += 1) {
        tasks.push({
          comparisonIndex,
          arm,
          matchIndex,
          options: {
            ...common,
            runs: 1,
            runOffset: matchIndex,
            sampleReplays: matchIndex < sampleReplays ? 1 : 0,
            factionIds,
            promptAddenda,
            scenario,
            requireLlm: true,
            strictLlmEvidence: true
          }
        });
      }
    }
  }
  tasks.forEach((task, taskIndex) => {
    task.taskIndex = taskIndex;
  });
  const studyLaunchIdentity = await captureTaskLaunchIdentities(tasks);
  const requestedWorkers = workersForTasks(
    options.workers,
    tasks,
    resolvedLlmConcurrency
  );
  const totalGames = tasks.reduce((total, task) => total + task.options.runs, 0);
  const actualWorkers = Math.min(requestedWorkers, tasks.length);
  const studyGeneration = randomUUID();
  const broker = hasLlm
    ? new LlmConcurrencyBroker({
      concurrency: resolvedLlmConcurrency,
      providerConcurrency: options.providerConcurrency,
      retries: options.llmRetries,
      signal: options.signal,
      generation: studyGeneration,
      callerFactory: options.llmCallerFactory
    })
    : null;
  const archiveCompletedLlmMatch = async (task, report) => {
    if (!taskUsesLlm(task) || options.archiveLlmMatches === false) return null;
    return archiveSimulationReport(report, {
      projectRoot: options.archiveProjectRoot || projectRoot,
      directory: options.archiveDirectory || "evidence/studies/simulation",
      jobId: [
        "faction-swap-match",
        task.comparisonIndex,
        task.arm,
        task.matchIndex
      ].join("-"),
      canPublish: () => !options.signal?.aborted
    });
  };
  const executionResult = !hasLlm && requestedWorkers === 1
    ? {
      reports: await runInline(tasks, {
        signal: options.signal,
        onProgress,
        totalGames
      }),
      failures: [],
      archives: []
    }
    : await runInWorkers(tasks, {
      workers: requestedWorkers,
      broker,
      studyGeneration,
      signal: options.signal,
      onProgress,
      totalGames,
      archiveCompletedLlmMatch
    });
  const armReports = executionResult.reports;
  const failures = executionResult.failures;
  for (const task of tasks) {
    if (!taskUsesLlm(task) && !armReports[task.taskIndex]) {
      throw new Error("Parallel faction swap did not return every deterministic arm.");
    }
  }
  const identityReport = armReports.find(Boolean);
  if (!identityReport) {
    const error = new Error("Every LLM-backed faction match was quarantined.");
    error.evidenceOutcome = "quarantined";
    error.failures = failures.filter(Boolean).map(failureEvidence);
    throw error;
  }
  const quarantines = [];
  const llmEvidenceMatches = [];
  const results = prepared.map(({ comparison, focalSeat }, comparisonIndex) => {
    const comparisonTasks = tasks.filter((task) =>
      task.comparisonIndex === comparisonIndex
    );
    const llmComparison = comparisonTasks.some(taskUsesLlm);
    let leftReports;
    let rightReports;
    let paired;
    if (llmComparison) {
      leftReports = [];
      rightReports = [];
      const matchIndexes = [];
      for (let matchIndex = 0; matchIndex < runsPerArm; matchIndex += 1) {
        const leftTask = comparisonTasks.find((task) =>
          task.arm === "left" && task.matchIndex === matchIndex
        );
        const rightTask = comparisonTasks.find((task) =>
          task.arm === "right" && task.matchIndex === matchIndex
        );
        const leftFailure = failures[leftTask.taskIndex];
        const rightFailure = failures[rightTask.taskIndex];
        if (leftFailure || rightFailure) {
          quarantines.push({
            comparisonId: comparison.id,
            matchIndex,
            outcome: "quarantined",
            left: failureEvidence(leftFailure),
            right: failureEvidence(rightFailure)
          });
          continue;
        }
        const leftReport = armReports[leftTask.taskIndex];
        const rightReport = armReports[rightTask.taskIndex];
        leftReports.push(leftReport);
        rightReports.push(rightReport);
        matchIndexes.push(matchIndex);
        llmEvidenceMatches.push({
          comparisonId: comparison.id,
          matchIndex,
          left: {
            experimentFingerprint: leftReport.experiment.fingerprint,
            receipts: orderedReceipts(leftReport),
            replay: leftReport.samples?.[0] || null
          },
          right: {
            experimentFingerprint: rightReport.experiment.fingerprint,
            receipts: orderedReceipts(rightReport),
            replay: rightReport.samples?.[0] || null
          }
        });
      }
      paired = summarizePair(
        { observations: leftReports.map((report) => report.observations[0]) },
        { observations: rightReports.map((report) => report.observations[0]) },
        focalSeat,
        matchIndexes
      );
      paired.scheduledPairs = runsPerArm;
      paired.quarantinedPairs = runsPerArm - paired.pairs;
    } else {
      const leftTask = comparisonTasks.find((task) => task.arm === "left");
      const rightTask = comparisonTasks.find((task) => task.arm === "right");
      leftReports = [armReports[leftTask.taskIndex]];
      rightReports = [armReports[rightTask.taskIndex]];
      paired = summarizePair(leftReports[0], rightReports[0], focalSeat);
      paired.scheduledPairs = runsPerArm;
      paired.quarantinedPairs = 0;
    }
    const leftIdentity = leftReports[0] || identityReport;
    const rightIdentity = rightReports[0] || identityReport;
    return {
      id: comparison.id,
      seedGroup: comparison.seedGroup || comparison.id,
      promptTreatmentId: comparison.promptTreatmentId || null,
      question: comparison.question || null,
      focalSeat,
      left: {
        factionId: comparison.leftFactionIds[focalSeat],
        factionIds: comparison.leftFactionIds,
        scenario: comparison.leftScenario || null,
        strategiesFingerprint: leftIdentity.strategies.fingerprint,
        abilityValues: abilityValues(
          leftReports,
          comparison.leftFactionIds[focalSeat]
        )
      },
      right: {
        factionId: comparison.rightFactionIds[focalSeat],
        factionIds: comparison.rightFactionIds,
        scenario: comparison.rightScenario || null,
        strategiesFingerprint: rightIdentity.strategies.fingerprint,
        abilityValues: abilityValues(
          rightReports,
          comparison.rightFactionIds[focalSeat]
        )
      },
      paired
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
    promptAddenda: options.promptAddenda,
    promptLibrary: options.promptLibrary,
    comparisonMatrix: options.comparisonMatrix,
    scenarioMatrix: options.scenarioMatrix,
    backends: options.backends,
    models: options.models,
    model: options.model,
    reasoningEfforts: options.reasoningEfforts,
    reasoningEffort: options.reasoningEffort,
    comparisons
  };
  preRegistration.fingerprint = fingerprintObject(preRegistration);
  const completedRuns = tasks.reduce((total, task) =>
    total + (armReports[task.taskIndex] ? task.options.runs : 0), 0);
  const pairedEvidenceRuns = results.reduce(
    (total, comparison) => total + comparison.paired.pairs * 2,
    0
  );
  const brokerSummary = broker?.summary() || null;
  const executionProfiles = llmExecutionProfiles(prepared);
  const completedLlmArchives = tasks
    .filter(taskUsesLlm)
    .flatMap((task) => {
      const archive = executionResult.archives?.[task.taskIndex];
      return archive ? [{
        taskIndex: task.taskIndex,
        comparisonId: comparisons[task.comparisonIndex].id,
        arm: task.arm,
        matchIndex: task.matchIndex,
        ...archive
      }] : [];
    });
  return {
    schemaVersion: 6,
    reportSchemaVersion: 6,
    replaySchemaVersion: 2,
    decisionSchemaVersion: 2,
    reportType: "balance_audit",
    diagnosticKind: options.diagnosticKind || "paired_faction_swap",
    evidenceLabel: "simulation",
    evidenceType: "simulation",
    generatedAt: new Date().toISOString(),
    launchIdentity: {
      schemaVersion: 1,
      study: studyLaunchIdentity,
      taskOrder: "comparison_then_arm_then_match",
      tasks: tasks.map((task) => ({
        taskIndex: task.taskIndex,
        comparisonIndex: task.comparisonIndex,
        arm: task.arm,
        matchIndex: task.matchIndex,
        identity: structuredClone(task.launchIdentity)
      }))
    },
    execution: {
      scheduler: hasLlm || actualWorkers > 1 ? "worker_threads" : "inline",
      taskUnit: hasLlm ? "simulation_match" : "simulation_arm",
      requestedWorkers: options.workers === undefined
        ? null
        : Number(options.workers),
      configuredWorkers: requestedWorkers,
      workers: actualWorkers,
      deterministicResultOrder: "comparison_then_arm_then_match",
      requestedLlmConcurrency: options.llmConcurrency === undefined
        ? null
        : Number(options.llmConcurrency),
      llmConcurrency: hasLlm ? resolvedLlmConcurrency : 0,
      llm: brokerSummary
        ? {
          ...brokerSummary,
          requestedProviderConcurrency:
            options.providerConcurrency || null,
          profiles: executionProfiles,
          configuredRetries: retryCount(options.llmRetries)
        }
        : null,
      quarantinedMatches: quarantines.length,
      completedLlmArchives
    },
    seed: rootSeed,
    runs: completedRuns,
    scheduledRuns: comparisons.length * runsPerArm * 2,
    pairedEvidenceRuns,
    runsPerArm,
    playerCount,
    scope: identityReport.scope,
    game: identityReport.game,
    engine: identityReport.engine,
    variant: identityReport.variant,
    strategies: {
      ...identityReport.strategies,
      configurations: comparisons.map((comparison) => ({
        id: comparison.id,
        profileIds: comparison.profileIds || options.profileIds,
        leftPromptAddenda: resolvePromptAddenda(
          comparison,
          "left",
          options,
          playerCount
        ),
        rightPromptAddenda: resolvePromptAddenda(
          comparison,
          "right",
          options,
          playerCount
        ),
        backends: comparison.backends || options.backends,
        models: comparison.models || options.models,
        model: comparison.model || options.model,
        reasoningEfforts: comparison.reasoningEfforts || options.reasoningEfforts,
        reasoningEffort: comparison.reasoningEffort || options.reasoningEffort,
        leftScenario: comparison.leftScenario || null,
        rightScenario: comparison.rightScenario || null
      })),
      fingerprint: fingerprintObject(comparisons.map((comparison) => ({
        id: comparison.id,
        profileIds: comparison.profileIds || options.profileIds,
        leftPromptAddenda: resolvePromptAddenda(
          comparison,
          "left",
          options,
          playerCount
        ),
        rightPromptAddenda: resolvePromptAddenda(
          comparison,
          "right",
          options,
          playerCount
        ),
        backends: comparison.backends || options.backends,
        models: comparison.models || options.models,
        model: comparison.model || options.model,
        reasoningEfforts: comparison.reasoningEfforts || options.reasoningEfforts,
        reasoningEffort: comparison.reasoningEffort || options.reasoningEffort,
        leftScenario: comparison.leftScenario || null,
        rightScenario: comparison.rightScenario || null
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
          options.diagnosticKind === "paired_agi_declaration_scenario"
            ? "Paired AGI declaration scenarios qualify a route endpoint but do not promote a physical rule."
            : "Paired faction swaps locate main effects but do not promote a physical rule."
        ]
      }
    },
    preRegistration,
    quarantine: {
      policy: hasLlm ? "strict_llm_pair" : "not_applicable",
      matches: quarantines
    },
    ...(hasLlm ? {
      llmEvidence: {
        mode: "strict_no_fallback",
        ordering: "comparison_then_match_then_arm_receipt_order",
        matches: llmEvidenceMatches
      }
    } : {}),
    comparisons: results
  };
}
