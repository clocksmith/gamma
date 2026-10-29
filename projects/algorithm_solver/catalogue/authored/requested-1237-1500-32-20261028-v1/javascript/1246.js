"use strict";

function solve(arr) {
  const n = arr.length;
  const dp = Array.from({ length: n }, () => new Int32Array(n));
  for (let i = 0; i < n; i++) dp[i][i] = 1;
  for (let len = 2; len <= n; len++) {
    for (let i = 0; i <= n - len; i++) {
      const j = i + len - 1;
      let best = 1 + dp[i + 1][j];
      if (arr[i] === arr[i + 1]) {
        const cand = 1 + (i + 2 <= j ? dp[i + 2][j] : 0);
        if (cand < best) best = cand;
      }
      const ai = arr[i];
      for (let k = i + 2; k <= j; k++) {
        if (ai === arr[k]) {
          const cand = dp[i + 1][k - 1] + (k + 1 <= j ? dp[k + 1][j] : 0);
          if (cand < best) best = cand;
        }
      }
      dp[i][j] = best;
    }
  }
  return dp[0][n - 1];
}

function minimumMoves(arr) {
  return solve(arr);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minimumMoves = minimumMoves;
