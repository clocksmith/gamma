"use strict";

function solve(target, words, costs) {
  const n = target.length;
  const best = new Map();
  for (let i = 0; i < words.length; i++) {
    const w = words[i], c = costs[i];
    if (!best.has(w) || c < best.get(w)) best.set(w, c);
  }
  const entries = Array.from(best.entries());
  const INF = 1e15;
  const dp = new Float64Array(n + 1).fill(INF);
  dp[0] = 0;
  for (let i = 0; i < n; i++) {
    if (dp[i] === INF) continue;
    for (let j = 0; j < entries.length; j++) {
      const [w, c] = entries[j];
      const L = w.length;
      if (i + L <= n && target.startsWith(w, i)) {
        if (dp[i] + c < dp[i + L]) dp[i + L] = dp[i] + c;
      }
    }
  }
  return dp[n] === INF ? -1 : dp[n];
}

function minimumCost(target, words, costs) {
  return solve(target, words, costs);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minimumCost = minimumCost;
