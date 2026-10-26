'use strict';

// 1929. Concatenation of Array (Easy).
// Specification: https://leetcode.com/problems/concatenation-of-array/description/
// O(n) time and result space; preserve nums and return a fresh array.
function solve(nums) {
  return nums.concat(nums);
}

const getConcatenation = solve;
class Solution {
  getConcatenation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getConcatenation };
