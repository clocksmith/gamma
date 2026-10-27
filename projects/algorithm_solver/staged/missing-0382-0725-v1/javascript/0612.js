'use strict';

// 612. Shortest Distance in a Plane. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. point2d: x, y (unique integer-coordinate pairs). Output: shortest, rounded to two decimal places; no pair yields NULL.

function solve(point2d) {
  let best = Infinity;
  for (let i = 0; i < point2d.length; i += 1) {
    for (let j = i + 1; j < point2d.length; j += 1) {
      const dx = point2d[i].x - point2d[j].x;
      const dy = point2d[i].y - point2d[j].y;
      best = Math.min(best, dx * dx + dy * dy);
    }
  }
  return [{shortest: Number.isFinite(best) ? Math.round(Math.sqrt(best) * 100) / 100 : null}];
}

const shortestDistance = solve;
class Solution {
  shortestDistance(point2d) { return solve(point2d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistance };
