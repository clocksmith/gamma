'use strict';

// 3774. Absolute Difference Between Maximum and Minimum K Elements (Easy).
// Specification: https://leetcode.com/problems/absolute-difference-between-maximum-and-minimum-k-elements/description/
// O(n log n) time, O(n) space; sort a copy and preserve nums.
function solve(nums, k) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let difference = 0;
  for (let index = 0; index < k; index++) {
    difference += ordered[ordered.length - 1 - index] - ordered[index];
  }
  return difference;
}

const absDifference = solve;
class Solution {
  absDifference(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, absDifference };
