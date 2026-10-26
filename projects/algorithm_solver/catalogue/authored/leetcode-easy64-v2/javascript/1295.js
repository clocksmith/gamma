'use strict';

// 1295. Find Numbers with Even Number of Digits (Easy).
// Specification: https://leetcode.com/problems/find-numbers-with-even-number-of-digits/description/
// O(n * d) time, O(d) temporary space; preserve nums. d is the digit bound.
function solve(nums) {
  let result = 0;
  for (const value of nums) {
    if (String(value).length % 2 === 0) result++;
  }
  return result;
}

const findNumbers = solve;
class Solution {
  findNumbers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findNumbers };
