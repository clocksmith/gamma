'use strict';

// 66. Plus One (Easy).
// Specification: https://leetcode.com/problems/plus-one/description/
// O(n) time and space; propagate the carry through a fresh copy.
function solve(digits) {
  const result = digits.slice();
  for (let index = result.length - 1; index >= 0; index--) {
    if (result[index] < 9) {
      result[index]++;
      return result;
    }
    result[index] = 0;
  }
  return [1, ...result];
}

const plusOne = solve;
class Solution {
  plusOne(digits) { return solve(digits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, plusOne };
