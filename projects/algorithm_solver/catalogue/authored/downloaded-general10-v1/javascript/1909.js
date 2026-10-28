'use strict';

// 1909. Remove One Element to Make the Array Strictly Increasing (Easy).
// Specification: https://leetcode.com/problems/remove-one-element-to-make-the-array-strictly-increasing/description/
function solve(nums) {
  let removed = false;
  for (let i = 1; i < nums.length; i++) {
    if (nums[i] <= nums[i - 1]) {
      if (removed) return false;
      removed = true;
      if (i > 1 && i + 1 < nums.length && nums[i] <= nums[i - 2] && nums[i + 1] <= nums[i - 1]) return false;
    }
  }
  return true;
}
const canBeIncreasing = solve;
class Solution { canBeIncreasing(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canBeIncreasing };
