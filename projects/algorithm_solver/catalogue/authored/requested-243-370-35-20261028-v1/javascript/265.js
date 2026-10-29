"use strict";

function solve(costs) {
  const k = costs[0].length;
  let dp = costs[0].slice();
  for (let i = 1; i < costs.length; i++) {
    const row = costs[i];
    let min1 = Infinity, min2 = Infinity, idx1 = -1;
    for (let j = 0; j < k; j++) {
      const v = dp[j];
      if (v < min1) {
        min2 = min1;
        min1 = v;
        idx1 = j;
      } else if (v < min2) {
        min2 = v;
      }
    }
    const ndp = new Array(k);
    for (let j = 0; j < k; j++) {
      ndp[j] = row[j] + (j === idx1 ? min2 : min1);
    }
    dp = ndp;
  }
  let best = dp[0];
  for (let j = 1; j < k; j++) if (dp[j] < best) best = dp[j];
  return best;
}

function minCostII(costs) {
  return solve(costs);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minCostII = minCostII;
