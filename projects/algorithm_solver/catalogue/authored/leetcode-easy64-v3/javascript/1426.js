'use strict';

// 1426. Counting Elements (Easy).
// Specification: https://leetcode.com/problems/counting-elements/description/
// O(n) expected time, O(n) space; count occurrences and preserve arr.
function solve(arr) {
  const present = new Set(arr);
  let result = 0;
  for (const value of arr) {
    if (present.has(value + 1)) result++;
  }
  return result;
}

const countElements = solve;
class Solution {
  countElements(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countElements };
