'use strict';

// 368. Largest Divisible Subset (Medium).
// Specification: https://leetcode.com/problems/largest-divisible-subset/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const dp = new Array(sorted.length).fill(1);
  const previous = new Array(sorted.length).fill(-1);
  let bestIndex = 0;
  for (let i = 0; i < sorted.length; i++) {
    for (let j = 0; j < i; j++) {
      if (sorted[i] % sorted[j] === 0 && dp[j] + 1 > dp[i]) { dp[i] = dp[j] + 1; previous[i] = j; }
    }
    if (dp[i] > dp[bestIndex]) bestIndex = i;
  }
  const result = [];
  for (let index = bestIndex; index !== -1; index = previous[index]) result.push(sorted[index]);
  return result.reverse();
}
const largestDivisibleSubset = solve;
class Solution { largestDivisibleSubset(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestDivisibleSubset };
