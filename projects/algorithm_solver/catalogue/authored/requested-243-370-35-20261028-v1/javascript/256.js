"use strict";

function solve(costs) {
  let r = 0, b = 0, g = 0;
  for (let i = 0; i < costs.length; i++) {
    const [c0, c1, c2] = costs[i];
    const nr = c0 + (b < g ? b : g);
    const nb = c1 + (r < g ? r : g);
    const ng = c2 + (r < b ? r : b);
    r = nr; b = nb; g = ng;
  }
  return Math.min(r, b, g);
}

function minCost(costs) {
  return solve(costs);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minCost = minCost;
