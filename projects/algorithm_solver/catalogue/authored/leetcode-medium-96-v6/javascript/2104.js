'use strict';

// 2104. Sum of Subarray Ranges: count each value as a subarray maximum and minimum with monotonic boundaries.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  function contribution(maximum) {
    const stack = [];
    let total = 0;
    for (let right = 0; right <= nums.length; right += 1) {
      while (stack.length && (right === nums.length ||
        (maximum ? nums[stack[stack.length - 1]] < nums[right] : nums[stack[stack.length - 1]] > nums[right]))) {
        const index = stack.pop();
        const left = stack.length ? stack[stack.length - 1] : -1;
        total += nums[index] * (index - left) * (right - index);
      }
      if (right < nums.length) stack.push(right);
    }
    return total;
  }
  return contribution(true) - contribution(false);
}

const subArrayRanges = solve;
class Solution {
  subArrayRanges(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subArrayRanges };
