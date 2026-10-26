'use strict';

// 3289. The Two Sneaky Numbers of Digitville (Easy).
// Specification: https://leetcode.com/problems/the-two-sneaky-numbers-of-digitville/description/
// O(n) time and space; return repeated values in ascending order without mutation.
function solve(nums) {
  const counts = new Array(nums.length - 2).fill(0);
  for (const value of nums) counts[value]++;
  const result = [];
  for (let value = 0; value < counts.length; value++) {
    if (counts[value] === 2) result.push(value);
  }
  return result;
}

const getSneakyNumbers = solve;
class Solution {
  getSneakyNumbers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSneakyNumbers };
