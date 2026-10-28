'use strict';

// 2119. A Number After a Double Reversal (Easy).
// Specification: https://leetcode.com/problems/a-number-after-a-double-reversal/description/
function reverseNumber(num) {
  return Number(String(num).split('').reverse().join(''));
}
function solve(num) {
  return reverseNumber(reverseNumber(num)) === num;
}
const isSameAfterReversals = solve;
class Solution { isSameAfterReversals(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSameAfterReversals };
