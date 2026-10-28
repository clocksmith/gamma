'use strict';

// 1185. Day of the Week (Easy).
// Specification: https://leetcode.com/problems/day-of-the-week/description/
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
function isLeap(year) { return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0; }
function solve(day, month, year) {
  let days = 0;
  for (let y = 1971; y < year; y++) days += isLeap(y) ? 366 : 365;
  for (let m = 1; m < month; m++) days += MONTH_DAYS[m - 1] + (m === 2 && isLeap(year) ? 1 : 0);
  days += day - 1;
  return DAYS[(days + 5) % 7];
}
const dayOfTheWeek = solve;
class Solution { dayOfTheWeek(day, month, year) { return solve(day, month, year); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, dayOfTheWeek };
