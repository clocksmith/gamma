'use strict';

// 258. Add Digits (Easy).
// Specification: https://leetcode.com/problems/add-digits/description/
// O(1) time and space; the digital root of a nonnegative integer.
function solve(num) {
  return num === 0 ? 0 : 1 + (num - 1) % 9;
}

const addDigits = solve;
class Solution {
  addDigits(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addDigits };
