'use strict';

// 3314. Construct the Minimum Bitwise Array I (Easy).
// Specification: https://leetcode.com/problems/construct-the-minimum-bitwise-array-i/description/
// O(n log M) time, O(n) result space; M <= 1000; clear the highest trailing one.
function solve(nums) {
  const result = [];
  for (const value of nums) {
    if (value % 2 === 0) {
      result.push(-1);
      continue;
    }
    let bit = 1;
    while ((value & bit) !== 0) bit *= 2;
    result.push(value - bit / 2);
  }
  return result;
}

const minBitwiseArray = solve;
class Solution {
  minBitwiseArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minBitwiseArray };
