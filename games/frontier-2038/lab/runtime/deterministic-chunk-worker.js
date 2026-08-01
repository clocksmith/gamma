import { parentPort } from "node:worker_threads";
import { createSimulation } from "./create-simulation.js";

function serializeError(error) {
  return {
    name: error?.name || "Error",
    message: error?.message || "Deterministic simulation chunk failed.",
    stack: error?.stack || null
  };
}

parentPort.on("message", async (message) => {
  if (message.kind !== "deterministic_chunk") return;
  try {
    const result = await createSimulation({
      ...message.options,
      workers: 1,
      returnOutcomes: true,
      sampleReplaysGlobal: true,
      launchIdentity: message.launchIdentity
    });
    parentPort.postMessage({
      kind: "chunk_result",
      chunkIndex: message.chunkIndex,
      outcomes: result.outcomes
    });
  } catch (error) {
    parentPort.postMessage({
      kind: "chunk_result",
      chunkIndex: message.chunkIndex,
      error: serializeError(error)
    });
  }
});
