'use strict';

// 2708. Maximum Strength of a Group: track both extremal products of a nonempty subsequence.
// O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums) {
  let smallest = nums[0];
  let largest = nums[0];
  for (let index = 1; index < nums.length; index += 1) {
    const value = nums[index];
    const fromSmallest = smallest * value;
    const fromLargest = largest * value;
    smallest = Math.min(smallest, value, fromSmallest, fromLargest);
    largest = Math.max(largest, value, fromSmallest, fromLargest);
  }
  return largest;
}

const maxStrength = solve;
class Solution {
  maxStrength(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxStrength };
