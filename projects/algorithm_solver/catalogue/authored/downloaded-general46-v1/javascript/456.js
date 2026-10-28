'use strict';

// 456. 132 Pattern (Medium).
// Specification: https://leetcode.com/problems/132-pattern/description/
function solve(nums) {
  const stack = [];
  let third = -Infinity;
  for (let i = nums.length - 1; i >= 0; i--) {
    if (nums[i] < third) return true;
    while (stack.length > 0 && stack[stack.length - 1] < nums[i]) third = stack.pop();
    stack.push(nums[i]);
  }
  return false;
}
const find132pattern = solve;
class Solution { find132pattern(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, find132pattern };
