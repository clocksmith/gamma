// Shared admission interface, not an optimizer or experiment result.
export function observationWindow({ objectiveId, theta, previous = null, loss, limit = 8 }) {
  if (typeof objectiveId !== 'string' || !objectiveId || !Array.isArray(theta)
      || !theta.length || !theta.every(Number.isFinite) || typeof loss !== 'function'
      || !Number.isInteger(limit) || limit < 1) throw new Error('Invalid observation window');
  if (previous && (previous.objectiveId !== objectiveId || previous.dimension !== theta.length)) {
    throw new Error('History objective or dimension mismatch');
  }
  let calls = 0;
  const history = previous ? structuredClone(previous) : null;
  return {
    objectiveId, dimension: theta.length, history,
    query(point) {
      if (!Array.isArray(point) || point.length !== theta.length || !point.every(Number.isFinite)) {
        throw new Error('Invalid query point');
      }
      if (calls >= limit) throw new Error('Scalar query budget exhausted');
      calls += 1; // Failed oracle calls consume budget too.
      const value = loss([...point]);
      if (!Number.isFinite(value)) throw new Error('Invalid scalar loss');
      return value;
    },
    receipt() { return { objectiveId, dimension: theta.length, scalarQueries: calls, limit }; },
  };
}
