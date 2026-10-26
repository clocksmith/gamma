'use strict';

// 1848. Minimum Distance to the Target Element (Easy).
// Specification: https://leetcode.com/problems/minimum-distance-to-the-target-element/description/
// O(n) time, O(1) space; the contract guarantees at least one target occurrence.
function solve(nums, target, start) {
  let closest = nums.length;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] === target) closest = Math.min(closest, Math.abs(index - start));
  }
  return closest;
}

const getMinDistance = solve;
class Solution {
  getMinDistance(nums, target, start) { return solve(nums, target, start); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMinDistance };
