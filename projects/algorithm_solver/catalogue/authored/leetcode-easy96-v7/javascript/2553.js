'use strict';

// 2553. Separate the Digits in an Array (Easy).
// Specification: https://leetcode.com/problems/separate-the-digits-in-an-array/description/
// O(total digits) time and result space; preserve number order and digit order; preserve nums.
function solve(nums) {
  const result = [];
  for (const value of nums) {
    for (const character of String(value)) result.push(character.charCodeAt(0) - 48);
  }
  return result;
}

const separateDigits = solve;
class Solution {
  separateDigits(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, separateDigits };
