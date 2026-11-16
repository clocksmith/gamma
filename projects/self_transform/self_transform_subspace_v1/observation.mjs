// Strict black-box scalar oracle window shared identically by learned and conventional updaters.
// Zero analytic gradients, Hessians, target identities, or free line-search retries.

export function observationWindow({ objectiveId, theta, previous = null, loss, limit = 8 }) {
  if (typeof objectiveId !== 'string' || !objectiveId
      || !Array.isArray(theta) || theta.length === 0 || !theta.every(Number.isFinite)
      || typeof loss !== 'function' || !Number.isInteger(limit) || limit < 1) {
    throw new Error('Invalid observation window specification');
  }
  if (previous !== null) {
    if (typeof previous !== 'object'
        || previous.objectiveId !== objectiveId
        || previous.dimension !== theta.length) {
      throw new Error('Episode state objective or dimension mismatch');
    }
  }
  let calls = 0;
  const history = previous ? structuredClone(previous) : null;
  const baseTheta = [...theta];
  return {
    objectiveId,
    dimension: baseTheta.length,
    history,
    query(point) {
      if (!Array.isArray(point) || point.length !== baseTheta.length || !point.every(Number.isFinite)) {
        throw new Error('Invalid query point');
      }
      if (calls >= limit) {
        throw new Error('Scalar query budget exhausted');
      }
      calls += 1; // Charged before evaluation so failed calls still consume budget.
      const value = loss([...point]);
      if (!Number.isFinite(value)) {
        throw new Error('Non-finite scalar loss observation');
      }
      return value;
    },
    receipt() {
      return { objectiveId, dimension: baseTheta.length, scalarQueries: calls, limit };
    },
  };
}
