'use strict';

// 2235. Add Two Integers (Easy).
// Specification: https://leetcode.com/problems/add-two-integers/description/
// O(1) time and space; exact integer addition over the declared input range.
function solve(num1, num2) {
  return num1 + num2;
}

const sum = solve;
class Solution {
  sum(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sum };
