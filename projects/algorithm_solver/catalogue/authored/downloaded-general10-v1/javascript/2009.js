'use strict';

// 2009. Minimum Number of Operations to Make Array Continuous (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-operations-to-make-array-continuous/description/
function solve(nums) {
  const uniq = [...new Set(nums)].sort((a, b) => a - b);
  const n = nums.length; let best = 0; let right = 0;
  for (let left = 0; left < uniq.length; left++) {
    while (right < uniq.length && uniq[right] - uniq[left] < n) right++;
    if (right - left > best) best = right - left;
  }
  return n - best;
}
const minOperations = solve;
class Solution { minOperations(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
