"use strict";
// Hack2Hire 6a1a10e2c81f779dc6a23794 (Factory Network Cost Minimization, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(costs) {
  let total = 0;
  for (const row of costs) { let best = row[0]; for (const c of row) if (c < best) best = c; total += best; }
  return total;
}

function minimumCost(costs) { return solve(costs); }

module.exports = solve;
module.exports.minimumCost = minimumCost;
