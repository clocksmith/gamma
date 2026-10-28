'use strict';

// 1074. Number of Dice Rolls With Target Sum (Medium).
// Specification: https://leetcode.com/problems/number-of-dice-rolls-with-target-sum/description/
function solve(n, k, target) {
  const modulus = 1000000007;
  let dp = new Array(target + 1).fill(0);
  dp[0] = 1;
  for (let die = 0; die < n; die++) {
    const next = new Array(target + 1).fill(0);
    for (let total = 0; total <= target; total++) {
      if (dp[total] === 0) continue;
      for (let face = 1; face <= k; face++) {
        if (total + face <= target) next[total + face] = (next[total + face] + dp[total]) % modulus;
      }
    }
    dp = next;
  }
  return dp[target];
}
const numRollsToTarget = solve;
class Solution { numRollsToTarget(n, k, target) { return solve(n, k, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numRollsToTarget };
