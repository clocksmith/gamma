'use strict';

// 1690. Stone Game VII (Medium).
// Specification: https://leetcode.com/problems/stone-game-vii/description/
function solve(stones) {
  const n = stones.length;
  const prefix = [0];
  for (const value of stones) prefix.push(prefix[prefix.length - 1] + value);
  const total = (l, r) => prefix[r + 1] - prefix[l];
  const dp = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let len = 2; len <= n; len++) {
    for (let l = 0; l + len - 1 < n; l++) {
      const r = l + len - 1;
      dp[l][r] = Math.max(total(l + 1, r) - dp[l + 1][r], total(l, r - 1) - dp[l][r - 1]);
    }
  }
  return dp[0][n - 1];
}
const stoneGameVII = solve;
class Solution { stoneGameVII(stones) { return solve(stones); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameVII };
