'use strict';

// 1546. Maximum Number of Non-Overlapping Subarrays With Sum Equals Target (Medium).
// Specification: https://leetcode.com/problems/maximum-number-of-non-overlapping-subarrays-with-sum-equals-target/description/
function solve(nums, target) {
  const seen = new Set([0]);
  let prefix = 0; let count = 0;
  for (const value of nums) {
    prefix += value;
    if (seen.has(prefix - target)) { count++; seen.clear(); seen.add(prefix); }
    else seen.add(prefix);
  }
  return count;
}
const maxNonOverlapping = solve;
class Solution { maxNonOverlapping(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNonOverlapping };
