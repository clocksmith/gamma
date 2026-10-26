'use strict';

// 3280. Convert Date to Binary (Easy).
// Specification: https://leetcode.com/problems/convert-date-to-binary/description/
// O(1) time and space for the bounded date format; omit binary leading zeros.
function solve(date) {
  const parts = date.split('-');
  return parts.map(part => Number(part).toString(2)).join('-');
}

const convertDateToBinary = solve;
class Solution {
  convertDateToBinary(date) { return solve(date); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertDateToBinary };
