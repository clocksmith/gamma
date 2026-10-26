'use strict';

// 2357. Make Array Zero by Subtracting Equal Amounts (Easy).
// Specification: https://leetcode.com/problems/make-array-zero-by-subtracting-equal-amounts/description/
// O(n) expected time, O(u) space; each distinct positive level requires one subtraction.
function solve(nums) {
  const positive = new Set();
  for (const value of nums) {
    if (value > 0) positive.add(value);
  }
  return positive.size;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
