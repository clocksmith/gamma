'use strict';

// 1063. Number of Valid Subarrays (Medium).
// Specification: https://leetcode.com/problems/number-of-valid-subarrays/description/
function solve(nums) {
  const stack = [];
  let total = 0;
  for (let i = nums.length - 1; i >= 0; i--) {
    while (stack.length > 0 && nums[stack[stack.length - 1]] >= nums[i]) stack.pop();
    const nextSmaller = stack.length === 0 ? nums.length : stack[stack.length - 1];
    total += nextSmaller - i;
    stack.push(i);
  }
  return total;
}
const validSubarrays = solve;
class Solution { validSubarrays(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSubarrays };
