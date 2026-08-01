import { mkdir, rename, writeFile } from "node:fs/promises";
import { relative, resolve } from "node:path";

function slug(value, fallback = "simulation") {
  const normalized = String(value || fallback)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 96);
  return normalized || fallback;
}

function timestamp() {
  return new Date().toISOString();
}

// Persists a small, atomic status receipt separate from the immutable final report.
// A monitor must never decide whether a simulation result is valid or publish it.
export function createSimulationRunMonitor({
  projectRoot,
  jobId,
  totalGames,
  directory = "evidence/studies/simulation/live"
} = {}) {
  if (!projectRoot) throw new TypeError("Simulation run monitor requires projectRoot.");
  if (!jobId) throw new TypeError("Simulation run monitor requires jobId.");
  const total = Number(totalGames);
  if (!Number.isInteger(total) || total < 1) {
    throw new RangeError("Simulation run monitor requires a positive totalGames value.");
  }
  const destination = resolve(projectRoot, directory, `${slug(jobId)}.json`);
  const temporary = `${destination}.tmp`;
  const state = {
    schemaVersion: 1,
    evidenceLabel: "simulation_run_status",
    jobId,
    status: "starting",
    startedAt: null,
    updatedAt: null,
    finishedAt: null,
    progress: {
      completedGames: 0,
      totalGames: total,
      completedTasks: 0,
      totalTasks: null,
      activeTaskIndices: []
    },
    execution: null,
    archive: null,
    error: null
  };
  let writes = Promise.resolve();

  const persist = () => {
    state.updatedAt = timestamp();
    const snapshot = `${JSON.stringify(state, null, 2)}\n`;
    writes = writes.then(async () => {
      await mkdir(resolve(destination, ".."), { recursive: true });
      await writeFile(temporary, snapshot, "utf8");
      await rename(temporary, destination);
    });
    return writes;
  };

  return {
    relativePath: relative(projectRoot, destination),
    async start({ execution = null, configuration = null } = {}) {
      state.status = "running";
      state.startedAt = timestamp();
      state.execution = execution;
      state.configuration = configuration;
      await persist();
    },
    update({ completed, total: nextTotal, completedTasks, totalTasks, activeTaskIndices } = {}) {
      if (completed !== undefined) state.progress.completedGames = completed;
      if (nextTotal !== undefined) state.progress.totalGames = nextTotal;
      if (completedTasks !== undefined) state.progress.completedTasks = completedTasks;
      if (totalTasks !== undefined) state.progress.totalTasks = totalTasks;
      if (activeTaskIndices !== undefined) {
        state.progress.activeTaskIndices = [...activeTaskIndices].sort((left, right) => left - right);
      }
      return persist();
    },
    async complete({ archive = null } = {}) {
      await writes;
      state.status = "completed";
      state.finishedAt = timestamp();
      state.archive = archive;
      state.progress.activeTaskIndices = [];
      state.progress.completedGames = state.progress.totalGames;
      if (state.progress.totalTasks !== null) state.progress.completedTasks = state.progress.totalTasks;
      await persist();
    },
    async fail(error) {
      await writes;
      state.status = error?.name === "AbortError" ? "cancelled" : "failed";
      state.finishedAt = timestamp();
      state.error = {
        name: error?.name || "Error",
        message: error?.message || String(error)
      };
      await persist();
    },
    flush() {
      return writes;
    }
  };
}
