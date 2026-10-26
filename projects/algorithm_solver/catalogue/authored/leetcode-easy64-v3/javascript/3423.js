'use strict';

// 3423. Maximum Difference Between Adjacent Elements in a Circular Array (Easy).
// Specification: https://leetcode.com/problems/maximum-difference-between-adjacent-elements-in-a-circular-array/description/
// O(n) time, O(1) space; include the last-to-first edge.
function solve(nums) {
  let largest = Math.abs(nums[0] - nums[nums.length - 1]);
  for (let index = 1; index < nums.length; index++) {
    largest = Math.max(largest, Math.abs(nums[index] - nums[index - 1]));
  }
  return largest;
}

const maxAdjacentDistance = solve;
class Solution {
  maxAdjacentDistance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAdjacentDistance };
