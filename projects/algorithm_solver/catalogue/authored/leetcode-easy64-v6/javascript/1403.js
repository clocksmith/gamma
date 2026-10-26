'use strict';

// 1403. Minimum Subsequence in Non-Increasing Order (Easy).
// Specification: https://leetcode.com/problems/minimum-subsequence-in-non-increasing-order/description/
// O(n log n) time, O(n) space; sort a copy and require a strictly larger sum.
function solve(nums) {
  const values = nums.slice().sort((a, b) => b - a);
  let total = 0;
  for (const value of values) total += value;
  let selected = 0;
  const result = [];
  for (const value of values) {
    result.push(value);
    selected += value;
    if (selected > total - selected) break;
  }
  return result;
}

const minSubsequence = solve;
class Solution {
  minSubsequence(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSubsequence };
