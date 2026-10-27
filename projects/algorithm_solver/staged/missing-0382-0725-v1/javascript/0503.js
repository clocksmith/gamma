'use strict';

// 503. Next Greater Element II.

function solve(nums) {
  const n = nums.length, answer = Array(n).fill(-1), stack = [];
  for (let i = 0; i < 2 * n; i += 1) {
    const index = i % n;
    while (stack.length > 0 && nums[stack[stack.length - 1]] < nums[index]) answer[stack.pop()] = nums[index];
    if (i < n) stack.push(index);
  }
  return answer;
}

const nextGreaterElements = solve;
class Solution {
  nextGreaterElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreaterElements };
