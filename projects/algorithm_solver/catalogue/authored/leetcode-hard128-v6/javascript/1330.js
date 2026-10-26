'use strict';

// 1330. Reverse Subarray To Maximize Array Value.
// Separate boundary reversals from the best internal boundary exchange; O(n) time and O(1) space. Inputs are preserved.

function solve(nums) {
  let total = 0, gain = 0;
  let largestLower = -Infinity, smallestUpper = Infinity;
  for (let index = 1; index < nums.length; index += 1) {
    const first = nums[index - 1], second = nums[index];
    const difference = Math.abs(first - second);
    total += difference;
    gain = Math.max(gain, Math.abs(nums[0] - second) - difference, Math.abs(nums[nums.length - 1] - first) - difference);
    largestLower = Math.max(largestLower, Math.min(first, second));
    smallestUpper = Math.min(smallestUpper, Math.max(first, second));
  }
  if (nums.length > 1) gain = Math.max(gain, 2 * (largestLower - smallestUpper));
  return total + gain;
}

const maxValueAfterReverse = solve;
class Solution {
  maxValueAfterReverse(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValueAfterReverse };
