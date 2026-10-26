'use strict';

// 896. Monotonic Array (Easy).
// Specification: https://leetcode.com/problems/monotonic-array/description/
// O(n) time, O(1) space; equal neighbors do not determine the direction.
function solve(nums) {
  let increasing = false;
  let decreasing = false;
  for (let index = 1; index < nums.length; index++) {
    if (nums[index] > nums[index - 1]) increasing = true;
    if (nums[index] < nums[index - 1]) decreasing = true;
    if (increasing && decreasing) return false;
  }
  return true;
}

const isMonotonic = solve;
class Solution {
  isMonotonic(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isMonotonic };
