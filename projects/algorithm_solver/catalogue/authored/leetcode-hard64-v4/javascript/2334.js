'use strict';

// 2334. Subarray With Elements Greater Than Varying Threshold. Monotonic stack of minimum spans; O(n) time and O(n) space. Inputs are preserved.

function solve(nums, threshold) {
  const stack = [];
  for (let right = 0; right <= nums.length; right += 1) {
    while (stack.length > 0 && (right === nums.length || nums[stack[stack.length - 1]] >= nums[right])) {
      const minimum = nums[stack.pop()];
      const left = stack.length > 0 ? stack[stack.length - 1] : -1;
      const length = right - left - 1;
      if (minimum * length > threshold) return length;
    }
    if (right < nums.length) stack.push(right);
  }
  return -1;
}

const validSubarraySize = solve;
class Solution {
  validSubarraySize(nums, threshold) { return solve(nums, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSubarraySize };
