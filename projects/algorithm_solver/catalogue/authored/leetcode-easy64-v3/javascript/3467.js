'use strict';

// 3467. Transform Array by Parity (Easy).
// Specification: https://leetcode.com/problems/transform-array-by-parity/description/
// O(n) time and output space; count even values and return a fresh sorted array.
function solve(nums) {
  let evens = 0;
  for (const value of nums) {
    if (value % 2 === 0) evens++;
  }
  const result = new Array(nums.length).fill(1);
  for (let index = 0; index < evens; index++) result[index] = 0;
  return result;
}

const transformArray = solve;
class Solution {
  transformArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, transformArray };
