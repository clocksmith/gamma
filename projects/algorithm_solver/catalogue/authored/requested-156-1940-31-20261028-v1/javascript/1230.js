"use strict";

function solve(prob, target) {
  const dp = new Float64Array(target + 1);
  dp[0] = 1.0;
  for (let i = 0; i < prob.length; i++) {
    const p = prob[i];
    for (let j = target; j >= 1; j--) {
      dp[j] = dp[j] * (1.0 - p) + dp[j - 1] * p;
    }
    dp[0] *= 1.0 - p;
  }
  return Math.round(dp[target] * 1e10) / 1e10;
}

function probabilityOfHeads(prob, target) {
  return solve(prob, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.probabilityOfHeads = probabilityOfHeads;
