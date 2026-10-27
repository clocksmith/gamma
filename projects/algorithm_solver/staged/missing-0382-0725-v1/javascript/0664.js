'use strict';

// 664. Strange Printer. Compress equal runs, then merge matching-character printing turns in interval DP.

function solve(s) {
  const text = [];
  for (const char of s) if (text.length === 0 || text[text.length - 1] !== char) text.push(char);
  const n = text.length;
  if (n === 0) return 0;
  const dp = Array.from({length: n}, () => Array(n).fill(0));
  for (let left = n - 1; left >= 0; left -= 1) {
    dp[left][left] = 1;
    for (let right = left + 1; right < n; right += 1) {
      let best = 1 + dp[left + 1][right];
      for (let match = left + 1; match <= right; match += 1) {
        if (text[match] === text[left]) best = Math.min(best, (match > left + 1 ? dp[left + 1][match - 1] : 0) + dp[match][right]);
      }
      dp[left][right] = best;
    }
  }
  return dp[0][n - 1];
}

const strangePrinter = solve;
class Solution {
  strangePrinter(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, strangePrinter };
