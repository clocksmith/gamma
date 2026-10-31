"use strict";

function solve(source, pattern, targetIndices) {
  const n = source.length, m = pattern.length;
  const isTarget = new Uint8Array(n);
  for (let i = 0; i < targetIndices.length; i++) isTarget[targetIndices[i]] = 1;
  const NEG = -1000000000;
  const dp = new Int32Array(m + 1).fill(NEG);
  dp[0] = 0;
  for (let i = 0; i < n; i++) {
    const ch = source.charCodeAt(i);
    const inT = isTarget[i];
    for (let j = m; j >= 1; j--) {
      if (dp[j] !== NEG) dp[j] += inT;
      if (ch === pattern.charCodeAt(j - 1) && dp[j - 1] !== NEG && dp[j - 1] > dp[j]) {
        dp[j] = dp[j - 1];
      }
    }
    dp[0] += inT;
  }
  return dp[m];
}

function maxRemovals(source, pattern, targetIndices) {
  return solve(source, pattern, targetIndices);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxRemovals = maxRemovals;
