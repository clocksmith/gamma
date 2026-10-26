'use strict';

// 1154. Day of the Year (Easy).
// Specification: https://leetcode.com/problems/day-of-the-year/description/
// O(1) time and space for fixed-format dates; sum earlier Gregorian month lengths.
function solve(date) {
  const year = Number(date.slice(0, 4));
  const month = Number(date.slice(5, 7));
  const day = Number(date.slice(8, 10));
  const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year % 400 === 0 || (year % 4 === 0 && year % 100 !== 0)) days[1] = 29;
  let result = day;
  for (let index = 0; index < month - 1; index++) result += days[index];
  return result;
}

const dayOfYear = solve;
class Solution {
  dayOfYear(date) { return solve(date); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dayOfYear };
