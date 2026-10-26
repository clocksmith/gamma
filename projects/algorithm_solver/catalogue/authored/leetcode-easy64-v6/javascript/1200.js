'use strict';

// 1200. Minimum Absolute Difference (Easy).
// Specification: https://leetcode.com/problems/minimum-absolute-difference/description/
// O(n log n) time, O(n) space; sort a copy and return fresh pairs.
function solve(arr) {
  const values = arr.slice().sort((a, b) => a - b);
  let smallest = values[1] - values[0];
  let result = [];
  for (let index = 1; index < values.length; index++) {
    const difference = values[index] - values[index - 1];
    if (difference < smallest) {
      smallest = difference;
      result = [];
    }
    if (difference === smallest) result.push([values[index - 1], values[index]]);
  }
  return result;
}

const minimumAbsDifference = solve;
class Solution {
  minimumAbsDifference(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumAbsDifference };
