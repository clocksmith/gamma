'use strict';

// 1323. Maximum 69 Number (Easy).
// Specification: https://leetcode.com/problems/maximum-69-number/description/
// O(d) time and space; d is the number of decimal digits.
function solve(num) {
  return Number(String(num).replace('6', '9'));
}

const maximum69Number = solve;
class Solution {
  maximum69Number(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximum69Number };
