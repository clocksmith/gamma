'use strict';

// 613. Shortest Distance in a Line. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. point: x (unique). Output: shortest; no pair yields NULL.

function solve(point) {
  const values = point.map(row => row.x).sort((a, b) => a - b);
  let best = Infinity;
  for (let i = 1; i < values.length; i += 1) best = Math.min(best, values[i] - values[i - 1]);
  return [{shortest: Number.isFinite(best) ? best : null}];
}

const shortestDistance = solve;
class Solution {
  shortestDistance(point) { return solve(point); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistance };
