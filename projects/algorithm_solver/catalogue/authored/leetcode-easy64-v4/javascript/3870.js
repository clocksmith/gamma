'use strict';

// 3870. Count Commas in Range (Easy).
// Specification: https://leetcode.com/problems/count-commas-in-range/description/
// O(1) time and space; the declared bound n <= 100000 permits at most one comma per number.
function solve(n) {
  return Math.max(0, n - 999);
}

const countCommas = solve;
class Solution {
  countCommas(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCommas };
