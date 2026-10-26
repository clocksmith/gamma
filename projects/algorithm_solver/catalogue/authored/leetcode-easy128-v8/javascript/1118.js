'use strict';

// 1118. Number of Days in a Month (Easy).
// Specification: https://leetcode.com/problems/number-of-days-in-a-month/description/
// O(1) time and space; Gregorian leap years include centuries only when divisible by 400.
function solve(year, month) {
  const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const leapYear = year % 400 === 0 || (year % 4 === 0 && year % 100 !== 0);
  return days[month - 1] + (month === 2 && leapYear ? 1 : 0);
}

const numberOfDays = solve;
class Solution {
  numberOfDays(year, month) { return solve(year, month); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfDays };
