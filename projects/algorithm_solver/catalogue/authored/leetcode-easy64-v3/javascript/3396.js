'use strict';

// 3396. Minimum Number of Operations to Make Elements in Array Distinct (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-operations-to-make-elements-in-array-distinct/description/
// O(n) expected time, O(n) space; find the longest distinct suffix without mutation.
function solve(nums) {
  const seen = new Set();
  for (let index = nums.length - 1; index >= 0; index--) {
    if (seen.has(nums[index])) return Math.floor(index / 3) + 1;
    seen.add(nums[index]);
  }
  return 0;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
