'use strict';

// 1155. Number of Dice Rolls With Target Sum (Medium).
// Specification: https://leetcode.com/problems/number-of-dice-rolls-with-target-sum/description/
const MOD = 1000000007;
function solve(n, k, target) {
  let dp = new Array(target + 1).fill(0);
  dp[0] = 1;
  for (let die = 0; die < n; die++) {
    const next = new Array(target + 1).fill(0);
    for (let total = 0; total <= target; total++) {
      if (dp[total] === 0) continue;
      for (let face = 1; face <= k && total + face <= target; face++) next[total + face] = (next[total + face] + dp[total]) % MOD;
    }
    dp = next;
  }
  return dp[target];
}
const numRollsToTarget = solve;
class Solution { numRollsToTarget(n, k, target) { return solve(n, k, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numRollsToTarget };
