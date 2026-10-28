'use strict';

// 790. Domino and Tromino Tiling (Medium).
// Specification: https://leetcode.com/problems/domino-and-tromino-tiling/description/
function solve(n) {
  const MOD = 1000000007;
  if (n === 1) return 1;
  if (n === 2) return 2;
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1; dp[1] = 1; dp[2] = 2;
  for (let i = 3; i <= n; i++) dp[i] = (2 * dp[i - 1] + dp[i - 3]) % MOD;
  return dp[n];
}
const numTilings = solve;
class Solution { numTilings(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTilings };
