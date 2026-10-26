'use strict';

// 1331. Rank Transform of an Array (Easy).
// Specification: https://leetcode.com/problems/rank-transform-of-an-array/description/
// O(n log n) time, O(n) space; preserve arr and return a fresh array.
function solve(arr) {
  const values = Array.from(new Set(arr)).sort((a, b) => a - b);
  const ranks = new Map();
  for (let index = 0; index < values.length; index++) ranks.set(values[index], index + 1);
  return arr.map(value => ranks.get(value));
}

const arrayRankTransform = solve;
class Solution {
  arrayRankTransform(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayRankTransform };
