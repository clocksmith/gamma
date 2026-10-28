'use strict';

// 581. Shortest Unsorted Continuous Subarray (Medium).
// Specification: https://leetcode.com/problems/shortest-unsorted-continuous-subarray/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  let left = nums.length; let right = -1;
  for (let i = 0; i < nums.length; i++) { if (nums[i] !== sorted[i]) { left = Math.min(left, i); right = Math.max(right, i); } }
  return right === -1 ? 0 : right - left + 1;
}
const findUnsortedSubarray = solve;
class Solution { findUnsortedSubarray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findUnsortedSubarray };
