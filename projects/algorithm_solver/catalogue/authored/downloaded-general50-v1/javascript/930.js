'use strict';

// 930. Binary Subarrays With Sum (Medium).
// Specification: https://leetcode.com/problems/binary-subarrays-with-sum/description/
function solve(nums, goal) {
  const counts = new Map([[0, 1]]);
  let prefix = 0; let total = 0;
  for (const v of nums) {
    prefix += v;
    total += counts.get(prefix - goal) || 0;
    counts.set(prefix, (counts.get(prefix) || 0) + 1);
  }
  return total;
}
const numSubarraysWithSum = solve;
class Solution { numSubarraysWithSum(nums, goal) { return solve(nums, goal); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubarraysWithSum };
