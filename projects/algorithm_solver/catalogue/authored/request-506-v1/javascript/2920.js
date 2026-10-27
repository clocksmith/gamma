// Original candidate implementation. Contract: https://leetcode.com/problems/maximum-points-after-collecting-coins-from-all-nodes/
"use strict";

function solve(edges, coins, k) {
  const n = coins.length;
  const adjacency = Array.from({ length: n }, () => []);
  for (const [u, v] of edges) {
    adjacency[u].push(v);
    adjacency[v].push(u);
  }
  const parent = Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index++) {
    const u = order[index];
    for (const v of adjacency[u]) {
      if (v !== parent[u]) {
        parent[v] = u;
        order.push(v);
      }
    }
  }
  let maximum = 0;
  for (const value of coins) maximum = Math.max(maximum, value);
  const levels = Math.floor(Math.log2(maximum || 1)) + 2;
  const dp = Array.from({ length: n }, () => Array(levels + 1).fill(0));
  // Iterative postorder avoids a call-stack limit on chain-shaped trees.
  for (let index = n - 1; index >= 0; index--) {
    const u = order[index];
    for (let shift = levels - 1; shift >= 0; shift--) {
      let keep = (coins[u] >> shift) - k;
      let halve = coins[u] >> (shift + 1);
      for (const v of adjacency[u]) {
        if (parent[v] === u) {
          keep += dp[v][shift];
          halve += dp[v][shift + 1];
        }
      }
      dp[u][shift] = Math.max(keep, halve);
    }
  }
  return dp[0][0];
}

module.exports = solve;
