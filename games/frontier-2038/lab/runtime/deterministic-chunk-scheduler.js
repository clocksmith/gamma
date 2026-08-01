import { availableParallelism } from "node:os";
import { Worker } from "node:worker_threads";
import { runMonteCarlo } from "../runner/monte-carlo-runner.js";

const workerUrl = new URL("./deterministic-chunk-worker.js", import.meta.url);

function workerCount(value) {
  const fallback = Math.min(64, Math.max(1, availableParallelism() - 1));
  const parsed = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 64) {
    throw new RangeError("workers must be an integer from 1 to 64.");
  }
  return parsed;
}

function chunkLength(value) {
  const parsed = value === undefined ? 5 : Number(value);
  if (!Number.isInteger(parsed) || parsed < 5 || parsed > 10) {
    throw new RangeError("chunkSize must be an integer from 5 to 10.");
  }
  return parsed;
}

function restoreError(value) {
  const error = new Error(value?.message || "Deterministic simulation chunk failed.");
  error.name = value?.name || "Error";
  error.stack = value?.stack || error.stack;
  return error;
}

export async function runDeterministicChunks({
  options,
  launchIdentity,
  onProgress
}) {
  const runs = Number(options.runs);
  const size = chunkLength(options.chunkSize);
  const tasks = Array.from({ length: Math.ceil(runs / size) }, (_, chunkIndex) => {
    const runOffset = chunkIndex * size;
    return {
      chunkIndex,
      runs: Math.min(size, runs - runOffset),
      runOffset
    };
  });
  const requestedWorkers = workerCount(options.workers);
  if (tasks.length === 1 || requestedWorkers === 1) return null;

  const workers = Math.min(requestedWorkers, tasks.length);
  const pool = Array.from({ length: workers }, () => new Worker(workerUrl, {
    // `--input-type` is valid for a parent launched from stdin, but Node rejects
    // it when it is inherited by a file-backed worker module.
    execArgv: process.execArgv.filter((argument) => !argument.startsWith("--input-type"))
  }));
  const outcomes = Array(tasks.length);
  const workerTask = new Map(pool.map((worker) => [worker, null]));
  const { signal, callerFactory, onProgress: ignoredProgress, ...workerOptions } = options;
  let next = 0;
  let completedTasks = 0;
  let completedRuns = 0;
  let settled = false;

  const result = await new Promise((resolve, reject) => {
    const terminate = () => Promise.allSettled(pool.map((worker) => worker.terminate()));
    const finish = async (error, value) => {
      if (settled) return;
      settled = true;
      signal?.removeEventListener("abort", abort);
      await terminate();
      if (error) reject(error);
      else resolve(value);
    };
    const abort = () => finish(
      signal?.reason || new DOMException("Deterministic batch was cancelled.", "AbortError")
    );
    const assign = (worker) => {
      if (settled || next >= tasks.length) return;
      const task = tasks[next++];
      workerTask.set(worker, task);
      worker.postMessage({
        kind: "deterministic_chunk",
        chunkIndex: task.chunkIndex,
        launchIdentity,
        options: {
          ...workerOptions,
          runs: task.runs,
          runOffset: task.runOffset
        }
      });
    };
    const receive = async (worker, message) => {
      const task = workerTask.get(worker);
      if (
        settled ||
        message.kind !== "chunk_result" ||
        !task ||
        message.chunkIndex !== task.chunkIndex
      ) {
        if (!settled) await finish(new Error("Deterministic batch returned a stale chunk result."));
        return;
      }
      if (message.error) {
        await finish(restoreError(message.error));
        return;
      }
      outcomes[task.chunkIndex] = message.outcomes;
      workerTask.set(worker, null);
      completedTasks += 1;
      completedRuns += task.runs;
      onProgress?.({ completed: completedRuns, runs });
      if (completedTasks === tasks.length) {
        await finish(null, outcomes.flat());
        return;
      }
      assign(worker);
    };
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) {
      abort();
      return;
    }
    for (const worker of pool) {
      worker.on("message", (message) => receive(worker, message));
      worker.on("error", (error) => finish(error));
      worker.on("exit", (code) => {
        if (!settled && workerTask.get(worker)) {
          finish(new Error(`Deterministic batch worker exited early (code ${code}).`));
        }
      });
      assign(worker);
    }
  });

  const report = await runMonteCarlo({
    runs,
    seed: String(options.seed || "frontier-monte-carlo"),
    precomputedOutcomes: result,
    sampleReplays: options.sampleReplays || 0,
    includeObservations: Boolean(options.includeObservations),
    projection: options.projection
  });
  return {
    report,
    execution: {
      scheduler: "worker_threads",
      requestedWorkers,
      workers,
      chunkSize: size,
      chunks: tasks.length
    }
  };
}
