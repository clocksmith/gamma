import { parentPort } from "node:worker_threads";
import { performance } from "node:perf_hooks";
import { createSimulation } from "../runtime/create-simulation.js";

function serializeError(error) {
  return {
    name: error?.name || "Error",
    message: error?.message || "Unified-matrix cell failed.",
    stack: error?.stack || null,
    code: error?.code || null
  };
}

parentPort.on("message", async (message) => {
  if (message.kind !== "unified_matrix_cell") return;
  try {
    const started = performance.now();
    const report = await createSimulation({
      ...message.options,
      workers: 1,
      launchIdentity: message.launchIdentity
    });
    parentPort.postMessage({
      kind: "cell_result",
      taskIndex: message.taskIndex,
      report,
      elapsedMs: Math.round(performance.now() - started)
    });
  } catch (error) {
    parentPort.postMessage({
      kind: "cell_result",
      taskIndex: message.taskIndex,
      error: serializeError(error)
    });
  }
});
