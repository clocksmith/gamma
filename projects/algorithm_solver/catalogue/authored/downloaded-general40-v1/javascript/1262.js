'use strict';

// 1262. Greatest Sum Divisible by Three (Medium).
// Specification: https://leetcode.com/problems/greatest-sum-divisible-by-three/description/
function solve(nums) {
  const dp = [0, -Infinity, -Infinity];
  for (const value of nums) {
    const next = dp.slice();
    for (let remainder = 0; remainder < 3; remainder++) {
      const newRemainder = (remainder + value) % 3;
      next[newRemainder] = Math.max(next[newRemainder], dp[remainder] + value);
    }
    for (let remainder = 0; remainder < 3; remainder++) dp[remainder] = next[remainder];
  }
  return dp[0];
}
const maxSumDivThree = solve;
class Solution { maxSumDivThree(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumDivThree };
