'use strict';

// 560. Subarray Sum Equals K (Medium).
// Specification: https://leetcode.com/problems/subarray-sum-equals-k/description/
function solve(nums, k) {
  const counts = new Map([[0, 1]]);
  let prefix = 0; let result = 0;
  for (const value of nums) {
    prefix += value;
    result += counts.get(prefix - k) || 0;
    counts.set(prefix, (counts.get(prefix) || 0) + 1);
  }
  return result;
}
const subarraySum = solve;
class Solution { subarraySum(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarraySum };
