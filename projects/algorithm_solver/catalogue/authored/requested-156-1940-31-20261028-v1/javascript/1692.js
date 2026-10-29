"use strict";

const MOD = 1000000007n;

function solve(n, k) {
  const dp = new BigInt64Array(k + 1);
  dp[0] = 1n;
  for (let i = 1; i <= n; i++) {
    for (let j = k; j >= 1; j--) {
      dp[j] = (dp[j] * BigInt(j) + dp[j - 1]) % MOD;
    }
    dp[0] = 0n;
  }
  return Number(dp[k]);
}

function waysToDistribute(n, k) {
  return solve(n, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.waysToDistribute = waysToDistribute;
