'use strict';

// 2437. Number of Valid Clock Times (Easy).
// Specification: https://leetcode.com/problems/number-of-valid-clock-times/description/
// O(1) time and space; independently count matching hours and minutes in the fixed clock domain.
function solve(time) {
  let hours = 0;
  let minutes = 0;
  for (let hour = 0; hour < 24; hour++) {
    const text = String(hour).padStart(2, '0');
    if ((time[0] === '?' || time[0] === text[0]) &&
        (time[1] === '?' || time[1] === text[1])) hours++;
  }
  for (let minute = 0; minute < 60; minute++) {
    const text = String(minute).padStart(2, '0');
    if ((time[3] === '?' || time[3] === text[0]) &&
        (time[4] === '?' || time[4] === text[1])) minutes++;
  }
  return hours * minutes;
}

const countTime = solve;
class Solution {
  countTime(time) { return solve(time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTime };
