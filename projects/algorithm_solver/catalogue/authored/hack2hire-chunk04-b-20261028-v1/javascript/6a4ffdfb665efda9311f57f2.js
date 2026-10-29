"use strict";
// Hack2Hire 6a4ffdfb665efda9311f57f2 (Coins and Energy) over an INFERRED spec; qualification unknown.

function solve(initialEnergy, energy, coins) {
  const n = energy.length, cap = n;
  let dp = new Array(cap + 1).fill(-1);
  dp[Math.min(initialEnergy, cap)] = 0;
  let best = 0;
  for (let i = 0; i < n; i++) {
    const after = new Array(cap + 1).fill(-1);
    const gain = energy[i], coin = coins[i];
    for (let e = 0; e <= cap; e++) {
      const have = dp[e];
      if (have < 0) continue;
      const up = Math.min(e + gain, cap);
      if (have > after[up]) after[up] = have;
      if (have + coin > after[e]) after[e] = have + coin;
    }
    for (const v of after) if (v > best) best = v;
    dp = after.slice(1);
    dp.push(-1);
  }
  return best;
}

function maxCoins(initialEnergy, energy, coins) { return solve(initialEnergy, energy, coins); }

module.exports = solve;
module.exports.maxCoins = maxCoins;
