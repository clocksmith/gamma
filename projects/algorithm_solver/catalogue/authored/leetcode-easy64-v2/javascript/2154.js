'use strict';

// 2154. Keep Multiplying Found Values by Two (Easy).
// Specification: https://leetcode.com/problems/keep-multiplying-found-values-by-two/description/
// O(n + log(M + 1)) expected time, O(n) space; M=max(nums), positive inputs.
function solve(nums, original) {
  const values = new Set(nums);
  let result = original;
  while (values.has(result)) result *= 2;
  return result;
}

const findFinalValue = solve;
class Solution {
  findFinalValue(nums, original) { return solve(nums, original); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findFinalValue };
