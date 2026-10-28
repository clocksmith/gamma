'use strict';

// 962. Maximum Width Ramp (Medium).
// Specification: https://leetcode.com/problems/maximum-width-ramp/description/
function solve(nums) {
  const stack = [];
  for (let i = 0; i < nums.length; i++) { if (stack.length === 0 || nums[stack[stack.length - 1]] > nums[i]) stack.push(i); }
  let best = 0;
  for (let j = nums.length - 1; j >= 0; j--) {
    while (stack.length > 0 && nums[stack[stack.length - 1]] <= nums[j]) { best = Math.max(best, j - stack.pop()); }
  }
  return best;
}
const maxWidthRamp = solve;
class Solution { maxWidthRamp(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxWidthRamp };
