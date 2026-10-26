'use strict';

// 3095. Shortest Subarray With OR at Least K I (Easy).
// Specification: https://leetcode.com/problems/shortest-subarray-with-or-at-least-k-i/description/
// O(n^2) time, O(1) space; declared values fit six bits, so bitwise OR is exact.
function solve(nums, k) {
  let shortest = nums.length + 1;
  for (let left = 0; left < nums.length; left++) {
    let combined = 0;
    for (let right = left; right < nums.length; right++) {
      combined |= nums[right];
      if (combined >= k) {
        shortest = Math.min(shortest, right - left + 1);
        break;
      }
    }
  }
  return shortest <= nums.length ? shortest : -1;
}

const minimumSubarrayLength = solve;
class Solution {
  minimumSubarrayLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSubarrayLength };
