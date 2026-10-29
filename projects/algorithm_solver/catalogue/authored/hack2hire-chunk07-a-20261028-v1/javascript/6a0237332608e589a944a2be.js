"use strict";
// Hack2Hire 6a0237332608e589a944a2be (Longest Common Subsequence-Substring) over an INFERRED spec; qualification unknown.

function solve(x, y) {
  const m = y.length;
  let prev = new Int32Array(m + 1), cur = new Int32Array(m + 1);
  for (let i = 0; i < x.length; i++) {
    const ch = x[i];
    for (let j = 0; j < m; j++) cur[j + 1] = y[j] === ch ? prev[j] + 1 : prev[j + 1];
    const t = prev; prev = cur; cur = t;
  }
  let best = 0;
  for (let j = 0; j <= m; j++) if (prev[j] > best) best = prev[j];
  return best;
}

function longestSubsequenceSubstring(x, y) { return solve(x, y); }

module.exports = solve;
module.exports.longestSubsequenceSubstring = longestSubsequenceSubstring;
