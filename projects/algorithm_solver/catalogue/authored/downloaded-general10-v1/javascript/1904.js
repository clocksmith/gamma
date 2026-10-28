'use strict';

// 1904. The Number of Full Rounds You Have Played (Easy).
// Specification: https://leetcode.com/problems/the-number-of-full-rounds-you-have-played/description/
function toMinutes(t) {
  const parts = t.split(':');
  return Number(parts[0]) * 60 + Number(parts[1]);
}
function solve(loginTime, logoutTime) {
  let start = toMinutes(loginTime); let end = toMinutes(logoutTime);
  if (end <= start) end += 24 * 60;
  return Math.floor(end / 15) - Math.ceil(start / 15);
}
const numberOfRounds = solve;
class Solution { numberOfRounds(loginTime, logoutTime) { return solve(loginTime, logoutTime); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfRounds };
