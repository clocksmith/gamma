"use strict";

function solve(s, k) {
  const n = s.length;
  const cost = Array.from({ length: n }, () => new Int32Array(n));
  for (let len = 2; len <= n; len++) {
    for (let i = 0; i <= n - len; i++) {
      const j = i + len - 1;
      cost[i][j] = cost[i + 1][j - 1] + (s[i] === s[j] ? 0 : 1);
    }
  }
  let dp = new Int32Array(n);
  for (let i = 0; i < n; i++) dp[i] = cost[0][i];
  for (let parts = 2; parts <= k; parts++) {
    const nxt = new Int32Array(n).fill(n);
    for (let i = parts - 1; i < n; i++) {
      let best = n;
      for (let p = parts - 2; p < i; p++) {
        const v = dp[p] + cost[p + 1][i];
        if (v < best) best = v;
      }
      nxt[i] = best;
    }
    dp = nxt;
  }
  return dp[n - 1];
}

function palindromePartition(s, k) {
  return solve(s, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.palindromePartition = palindromePartition;
