'use strict';

// 3173. Bitwise OR of Adjacent Elements (Easy).
// Specification: https://leetcode.com/problems/bitwise-or-of-adjacent-elements/description/
// O(n) time, O(n) result space; values are in [0, 100], so bitwise arithmetic is exact.
function solve(nums) {
  const result = [];
  for (let index = 0; index + 1 < nums.length; index++) {
    result.push(nums[index] | nums[index + 1]);
  }
  return result;
}

const orArray = solve;
class Solution {
  orArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, orArray };
