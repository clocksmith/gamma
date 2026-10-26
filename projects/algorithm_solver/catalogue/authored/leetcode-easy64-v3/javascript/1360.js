'use strict';

// 1360. Number of Days Between Two Dates (Easy).
// Specification: https://leetcode.com/problems/number-of-days-between-two-dates/description/
// O(1) time and space for fixed-format Gregorian dates; no timezone conversion.
function solve(date1, date2) {
  function ordinal(date) {
    const [year, month, day] = date.split('-').map(Number);
    const previousYear = year - 1;
    let days = 365 * previousYear + Math.floor(previousYear / 4)
      - Math.floor(previousYear / 100) + Math.floor(previousYear / 400) + day;
    const monthLengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    for (let index = 0; index < month - 1; index++) days += monthLengths[index];
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    if (month > 2 && leap) days++;
    return days;
  }
  return Math.abs(ordinal(date1) - ordinal(date2));
}

const daysBetweenDates = solve;
class Solution {
  daysBetweenDates(date1, date2) { return solve(date1, date2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, daysBetweenDates };
