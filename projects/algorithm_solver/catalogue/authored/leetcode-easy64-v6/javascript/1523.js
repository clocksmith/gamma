'use strict';

// 1523. Count Odd Numbers in an Interval Range (Easy).
// Specification: https://leetcode.com/problems/count-odd-numbers-in-an-interval-range/description/
// O(1) time and space; both bounds are inclusive.
function solve(low, high) {
  return Math.floor((high + 1) / 2) - Math.floor(low / 2);
}

const countOdds = solve;
class Solution {
  countOdds(low, high) { return solve(low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOdds };
