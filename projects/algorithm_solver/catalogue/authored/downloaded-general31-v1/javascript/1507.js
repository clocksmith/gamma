'use strict';

// 1507. Reformat Date (Easy).
// Specification: https://leetcode.com/problems/reformat-date/description/
const MONTHS = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };
function pad(value) { return value < 10 ? '0' + value : String(value); }
function solve(date) {
  const parts = date.split(' ');
  const day = parseInt(parts[0], 10);
  const month = MONTHS[parts[1]];
  const year = parts[2];
  return year + '-' + pad(month) + '-' + pad(day);
}
const reformatDate = solve;
class Solution { reformatDate(date) { return solve(date); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reformatDate };
