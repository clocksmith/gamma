'use strict';

// 456. 132 Pattern.

function solve(nums) {
  const stack = [];
  let third = -Infinity;
  for (let i = nums.length - 1; i >= 0; i -= 1) {
    const value = nums[i];
    if (value < third) return true;
    while (stack.length > 0 && value > stack[stack.length - 1]) third = stack.pop();
    stack.push(value);
  }
  return false;
}

const find132pattern = solve;
class Solution {
  find132pattern(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, find132pattern };
