'use strict';

// 2460. Apply Operations to an Array (Easy).
// Specification: https://leetcode.com/problems/apply-operations-to-an-array/description/
// O(n) time, O(n) space; apply operations left to right on a copy of nums.
function solve(nums) {
  const result = nums.slice();
  for (let index = 0; index < result.length - 1; index++) {
    if (result[index] === result[index + 1]) {
      result[index] *= 2;
      result[index + 1] = 0;
    }
  }
  let write = 0;
  for (let index = 0; index < result.length; index++) {
    if (result[index] !== 0) result[write++] = result[index];
  }
  while (write < result.length) result[write++] = 0;
  return result;
}

const applyOperations = solve;
class Solution {
  applyOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, applyOperations };
