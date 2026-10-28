'use strict';

// 764. Largest Plus Sign (Medium).
// Specification: https://leetcode.com/problems/largest-plus-sign/description/
function solve(n, mines) {
  const isMine = new Set(mines.map(([r, c]) => r * n + c));
  const dp = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let r = 0; r < n; r++) {
    let count = 0;
    for (let c = 0; c < n; c++) { count = isMine.has(r * n + c) ? 0 : count + 1; dp[r][c] = count; }
    count = 0;
    for (let c = n - 1; c >= 0; c--) { count = isMine.has(r * n + c) ? 0 : count + 1; dp[r][c] = Math.min(dp[r][c], count); }
  }
  let best = 0;
  for (let c = 0; c < n; c++) {
    let count = 0;
    for (let r = 0; r < n; r++) { count = isMine.has(r * n + c) ? 0 : count + 1; dp[r][c] = Math.min(dp[r][c], count); }
    count = 0;
    for (let r = n - 1; r >= 0; r--) { count = isMine.has(r * n + c) ? 0 : count + 1; dp[r][c] = Math.min(dp[r][c], count); best = Math.max(best, dp[r][c]); }
  }
  return best;
}
const orderOfLargestPlusSign = solve;
class Solution { orderOfLargestPlusSign(n, mines) { return solve(n, mines); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, orderOfLargestPlusSign };
