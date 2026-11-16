// Strict first-order loss-and-gradient observation window shared identically across
// learned proposers, neural regeneration, and conventional optimizers (SGD, Adam, L-BFGS).
// Charges every evaluation attempt BEFORE execution so failed / non-finite calls consume budget.

export function counter() {
  return {
    oracleCalls: 0,
    failedAttempts: 0,
    updates: 0,
    clamps: 0,
    skippedCurvature: 0,
    regenerationCalls: 0,
    regenerationFlops: 0,
    reconstructionBytes: 0,
    peakStateBytes: 0,
  };
}

export function addBudget(target, delta) {
  target.oracleCalls += delta.oracleCalls;
  target.failedAttempts += delta.failedAttempts;
  target.updates += delta.updates;
  target.clamps += delta.clamps;
  target.skippedCurvature += delta.skippedCurvature;
  target.regenerationCalls += delta.regenerationCalls;
  target.regenerationFlops += delta.regenerationFlops;
  target.reconstructionBytes += delta.reconstructionBytes;
  target.peakStateBytes = Math.max(target.peakStateBytes, delta.peakStateBytes);
  return target;
}

export function gradientWindow({ objectiveId, theta, previous = null, lossAndGrad, limit = 1 }) {
  if (typeof objectiveId !== 'string' || !objectiveId
      || !Array.isArray(theta) || theta.length === 0 || !theta.every(Number.isFinite)
      || typeof lossAndGrad !== 'function' || !Number.isInteger(limit) || limit < 1) {
    throw new Error('Invalid gradient observation window specification');
  }
  if (previous !== null) {
    if (typeof previous !== 'object'
        || previous.objectiveId !== objectiveId
        || previous.dimension !== theta.length) {
      throw new Error('Episode state objective or dimension mismatch');
    }
  }
  let calls = 0;
  let failed = 0;
  const history = previous ? structuredClone(previous) : null;
  const baseTheta = [...theta];

  return {
    objectiveId,
    dimension: baseTheta.length,
    history,
    evaluate(point) {
      if (!Array.isArray(point) || point.length !== baseTheta.length || !point.every(Number.isFinite)) {
        calls += 1;
        failed += 1;
        throw new Error('Invalid or non-finite query point');
      }
      if (calls >= limit) {
        throw new Error('Oracle query budget exhausted');
      }
      calls += 1; // Charged before evaluation so thrown or non-finite evaluations still cost budget.
      let res;
      try {
        res = lossAndGrad([...point]);
      } catch (err) {
        failed += 1;
        throw err;
      }
      if (!res || !Number.isFinite(res.loss)
          || !Array.isArray(res.grad) || res.grad.length !== baseTheta.length
          || !res.grad.every(Number.isFinite)) {
        failed += 1;
        throw new Error('Non-finite loss or gradient observation');
      }
      return { loss: res.loss, grad: [...res.grad] };
    },
    receipt() {
      return {
        objectiveId,
        dimension: baseTheta.length,
        oracleCalls: calls,
        failedAttempts: failed,
        limit,
      };
    },
  };
}
