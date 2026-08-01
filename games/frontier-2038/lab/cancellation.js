export function cancellationError(message = "Simulation job cancelled.") {
  const error = new Error(message);
  error.name = "AbortError";
  error.evidenceOutcome = "cancelled";
  return error;
}

export function throwIfAborted(signal) {
  if (!signal?.aborted) return;
  const reason = signal.reason;
  if (reason instanceof Error) throw reason;
  throw cancellationError();
}
