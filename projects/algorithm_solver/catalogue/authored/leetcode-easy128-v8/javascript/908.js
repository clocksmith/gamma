'use strict';

// 908. Smallest Range I (Easy).
// Specification: https://leetcode.com/problems/smallest-range-i/description/
// O(n) time, O(1) space; both extremes can move inward by at most k.
function solve(nums, k) {
  let smallest = nums[0];
  let largest = nums[0];
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    largest = Math.max(largest, value);
  }
  return Math.max(0, largest - smallest - 2 * k);
}

const smallestRangeI = solve;
class Solution {
  smallestRangeI(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestRangeI };
