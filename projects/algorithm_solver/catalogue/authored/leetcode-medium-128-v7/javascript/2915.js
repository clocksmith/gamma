'use strict';

// 2915. Length of the Longest Subsequence That Sums to Target: maximize the element count for each exact sum with descending knapsack updates.
// O(n * target) time and O(target) auxiliary space; inputs are read-only.
function solve(nums, target) {
  const longest = new Int32Array(target + 1).fill(-1);
  longest[0] = 0;
  for (const value of nums) {
    for (let total = target; total >= value; total -= 1) {
      if (longest[total - value] !== -1) {
        longest[total] = Math.max(longest[total], longest[total - value] + 1);
      }
    }
  }
  return longest[target];
}

const lengthOfLongestSubsequence = solve;
class Solution {
  lengthOfLongestSubsequence(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthOfLongestSubsequence };
