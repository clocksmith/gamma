'use strict';

// 1619. Mean of Array After Removing Some Elements (Easy).
// Specification: https://leetcode.com/problems/mean-of-array-after-removing-some-elements/description/
// O(n log n) time, O(n) space; sort a copy; n is a positive multiple of 20.
function solve(arr) {
  const values = arr.slice().sort((a, b) => a - b);
  const trim = values.length / 20;
  let total = 0;
  for (let index = trim; index < values.length - trim; index++) total += values[index];
  return total / (values.length - 2 * trim);
}

const trimMean = solve;
class Solution {
  trimMean(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, trimMean };
