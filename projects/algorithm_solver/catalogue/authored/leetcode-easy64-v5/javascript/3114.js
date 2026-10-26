'use strict';

// 3114. Latest Time You Can Obtain After Replacing Characters (Easy).
// Specification: https://leetcode.com/problems/latest-time-you-can-obtain-after-replacing-characters/description/
// O(1) time and space; the hour range is 00 through 11, not 00 through 23.
function solve(s) {
  const time = s.split('');
  if (time[0] === '?') time[0] = time[1] === '?' || time[1] <= '1' ? '1' : '0';
  if (time[1] === '?') time[1] = time[0] === '1' ? '1' : '9';
  if (time[3] === '?') time[3] = '5';
  if (time[4] === '?') time[4] = '9';
  return time.join('');
}

const findLatestTime = solve;
class Solution {
  findLatestTime(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLatestTime };
